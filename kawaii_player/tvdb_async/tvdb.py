"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of tvdb-async.

tvdb-async is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

tvdb-async is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with tvdb-async.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import time
import random
from functools import partial
from vinanti import Vinanti
from bs4 import BeautifulSoup
try:
    from tvdb_async.deco import *
    from tvdb_async.backend import Backend
    from tvdb_async.log import log_function
except ImportError:
    from deco import *
    from backend import Backend
    from log import log_function
logger = log_function(__name__)


class TVDB:
    
    def __init__(self, base_url=None, lang='en', wait=None,
                 episode_summary=False, search_and_grab=True,
                 backend=None, hdrs=None):
        if not base_url:
            self.base_url = 'https://www.thetvdb.com'
        else:
            self.base_url = base_url
        self.language = lang
        if hdrs:
            self.hdrs = hdrs
        else:
            self.hdrs = {'User-Agent':'Mozilla/5.0'}
        if os.name == 'posix':
            verify = True
        else:
            verify = False
        if isinstance(wait, int) or isinstance(wait, float):
            self.vnt = Vinanti(block=False, hdrs=self.hdrs, wait=wait, timeout=10, verify=verify)
        else:
            self.vnt = Vinanti(block=False, hdrs=self.hdrs, timeout=10, verify=verify)
        self.fanart_list = []
        self.poster_list = []
        self.banner_list = []
        self.final_dict = {}
        self.time = time.time()
        self.ep_summary = episode_summary
        self.search_and_grab = search_and_grab
        self.backend = Backend(hdrs)
        self.backend_search = backend
    
    def find_redirected_link(self, *args):
        result = args[-1]
        url = result.url
        logger.debug(args)
        self.getinfo(url, onfinished=args[0], eps=args[2])
        
    def search_with_backend(self, links, *args):
        if links:
            link = links[0]
            if 'tab=series' in link:
                new_args = args[:-3]
                self.vnt.head(link, onfinished=partial(self.find_redirected_link, *new_args))
        
    
    def search(self, srch, backend=None, onfinished=None, episode_summary=None):
        if srch.startswith('http'):
            self.getinfo(srch, onfinished=onfinished, eps=episode_summary)
        else:
            if backend in ['g', 'ddg']:
                self.backend.search(srch, backend, self.search_with_backend, onfinished, srch, episode_summary)
            elif self.backend_search and backend != 'no':
                self.backend.search(srch, self.backend_search, self.search_with_backend, onfinished, srch, episode_summary)
            else:
                base_url = 'https://www.thetvdb.com/search'
                params = {'q':srch}
                logger.info('{}, {}'.format(base_url, params))
                self.vnt.get(base_url, params=params, onfinished=partial(self.process_search, onfinished, srch, episode_summary))
    
    def getinfo(self, url, onfinished=None, eps=None):
        logger.info('{} {}'.format(url, eps))
        self.final_dict.update({url:SeriesObject(url)})
        fanart_url = url + '/artwork/fanart' 
        banner_url = url + '/artwork/banners'
        poster_url = url + '/artwork/poster'
        artwork = [fanart_url, banner_url, poster_url]
        self.vnt.get(url, onfinished=partial(self.process_page, onfinished, url, eps))
        for i in artwork:
            self.vnt.get(i, onfinished=partial(self.process_artwork, onfinished, url))
    
    @process_artwork_onfinished
    def process_artwork(self, *args):
        result = args[-1]
        url = args[-2]
        ourl = args[1]
        soup = BeautifulSoup(result.html, 'html.parser')
        title = url.rsplit('/', 1)[1]
        img_list = []
        for i in soup.findAll('div', {'class':'thumbnail'}):
            j = i.find('img')['src']
            img_list.append(j)
        obj = self.final_dict[ourl]
        if title == 'poster':
            obj.poster = img_list.copy()
        elif title == 'banners':
            obj.banners = img_list.copy()
        elif title == 'fanart':
            obj.fanart = img_list.copy()
        return obj, title
    
    @process_page_onfinished
    def process_page(self, *args):
        ourl = args[1]
        eps = args[2]
        result = args[-1]
        obj = self.final_dict[ourl]
        soup = BeautifulSoup(result.html, 'html.parser')
        title_s = soup.find('h1', {'id':'series_title'})
        if title_s:
            obj.title = title_s.text.strip()
        summary_s = soup.find('div', {'data-language':self.language})
        if summary_s:
            obj.summary = summary_s.text.strip()
        info_soup = soup.find('div', {'id':'series_basic_info'})
        if info_soup:
            for info in soup.findAll('li', {'class':'list-group-item clearfix'}):
                attr = info.find('strong')
                attr_val = attr.findNext('span')
                if attr and attr_val:
                    attr_text = attr.text.lower()
                    attr_val_text = attr_val.text
                    if 'series id' in attr_text:
                        attr_text = 'tvdb-id'
                    elif 'imdb' in attr_text:
                        attr_text = 'imdb-id'
                    if attr_text:
                        obj.info.update({attr_text:attr_val_text})
        series_dict = {}
        for i in soup.findAll('h4', {'class':"list-group-item-heading"}):
            j = i.find('a')
            if j:
                k = self.base_url + j['href']
                l = j.text.strip()
                m = j.findNext('p').text.strip()
                n = (k, l, m)
                series_dict.update({l:[k, m]})
        obj.season_dict = series_dict.copy()
        for i,j in series_dict.items():
            self.vnt.get(j[0], onfinished=partial(self.process_seasons, args[0], i, ourl, eps))
        return obj
    
    @process_seasons_onfinished
    def process_seasons(self, *args):
        season = args[1]
        ourl = args[2]
        eps = args[3]
        obj = self.final_dict[ourl]
        result = args[-1]
        soup = BeautifulSoup(result.html, 'html.parser')
        img_list = []
        for i in soup.findAll('div', {'class':'thumbnail'}):
            j = i.find('img')['src']
            img_list.append(j)
        tables = soup.findAll('table', {'class':'table table-hover'})
        slist = []
        ep_dict = {}
        k = 0
        sid = 1
        if season.lower() in ['specials', 'all seasons']:
            sid = 0
        else:
            ss = season.replace('Season ', '')
            if ss.isnumeric():
                sid = int(ss)
            
        for table in tables:
            for tr in table.findAll('tr'):
                num = None
                link = None
                dt = None
                img_link = None
                title = None
                found = False
                for i, td in enumerate(tr.findAll('td')):
                    if i == 0:
                        ntd = td.find('a')
                        if ntd:
                            num = td.text.strip()
                            link = self.base_url + ntd['href']
                            found = True
                    elif i == 1:
                        ntd = td.find('a')
                        if ntd:
                            nntd = ntd.find('span',{'data-language':self.language})
                            if nntd:
                                title = nntd.text.strip()
                                found = True
                    elif i == 2:
                        dt = td.text.strip()
                        if dt:
                            found = True
                    elif i == 3:
                        ntd = td.find('a')
                        if ntd:
                            img_link = ntd['href']
                            found = True
                if found:
                    if num:
                        nsid = str(sid)+ 'x' + num
                    else:
                        nsid = str(sid)+ 'x' + k
                    slist.append([k, nsid, num, title, link, dt, img_link])
                    k += 1
            if season.lower() != 'all seasons':
                obj.season_episode_dict.update({sid :[slist.copy(), img_list.copy()]})
            sid += 1
        if season.lower() != 'all seasons':
            obj.season_posters.update({season:img_list})
        if season.lower() == 'all seasons' and (self.ep_summary or eps):
            if eps is None or eps is True:
                obj.total = len(slist)
                for i, val in enumerate(slist):
                    logger.debug('{} {}'.format(i, obj.total))
                    k, nsid, num, title, link, dt, img_link = val
                    if link:
                        logger.debug('{} {}-----{} {} {}'.format(i, obj.total, k, nsid, link))
                        self.vnt.get(link, onfinished=partial(self.process_episodes, args[0], ourl, val.copy()))
                    else:
                        obj.total -= 1
        return obj
    
    @process_episodes_onfinished
    def process_episodes(self, *args):
        ourl = args[1]
        result = args[-1]
        if not args[-1]:
            obj = None
        else:
            obj = self.final_dict[ourl]
            soup = BeautifulSoup(result.html, 'html.parser')
            smr = soup.find('div', {'data-language':self.language})
            if smr:
                summary = smr.text.strip()
            else:
                summary = ''
            k, nsid, num, title, link, dt, img_link = args[2]
            newargs = [k, nsid, num, title, link, dt, img_link, summary]
            if not obj.episode_summary.get(nsid):
                obj.episode_summary.update({nsid:newargs})
            else:
                nsid = '-'+nsid + '-' + str(random.randint(0, 100000))
                logger.debug('\nid already exists, creating new one\n')
                obj.episode_summary.update({nsid:newargs})
            logger.debug('{} {}'.format(len(obj.episode_summary), obj.total))
            if len(obj.episode_summary) == obj.total:
                return obj, 'all'
            else:
                return obj, newargs.copy()
    
    @search_onfinished
    def process_search(self, *args):
        search_dict = {}
        result = args[-1]
        srch = args[1]
        eps = args[2]
        exact_found = False
        soup = BeautifulSoup(result.html, 'html.parser')
        info_list = []
        lang = None
        title_text = None
        title_link = None
        tvdb_id = None
        status = None
        original_network = None
        start_date = None
        end_date = None
        min_val = None
        min_dict = {'final':None}
        min_index = 0
        for i, tr in enumerate(soup.findAll('tr')):
            for j, td in enumerate(tr.findAll('td')):
                if j == 0:
                    lang = td.text
                elif j == 1:
                    if 'href' in str(td):
                        txt = td.text
                        if txt.lower() == srch.lower():
                            exact_found = True
                        else:
                            dist = self.levenshtein(txt.lower(), srch.lower())
                            if not min_val:
                                min_val = dist
                                min_index = i
                            else:
                                if min_val > dist:
                                    min_val = dist
                                    min_index = i
                        href = td.find('a')['href']
                        title_text = txt
                        title_link = self.base_url + href
                elif j == 2:
                    tvdb_id = td.text
                elif j == 3:
                    status = td.text
                elif j == 4:
                    original_network = td.text
                elif j == 5:
                    start_date = td.text
                elif j == 6:
                    end_date = td.text
            arg_list = [
                title_text, title_link, tvdb_id, status,
                original_network, start_date, end_date, lang
                ]
            if exact_found:
                search_dict.clear()
                search_dict.update({0:arg_list.copy()})
                break
            elif title_link is None:
                pass
            else:
                search_dict.update({i:arg_list.copy()})
                if min_index == i:
                    min_dict.clear()
                    min_dict = {i:arg_list.copy()}
        if exact_found:
            return search_dict, self.search_and_grab
        else:
            return min_dict, self.search_and_grab
    
    #https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
    
    def levenshtein(self, s1, s2):
        if len(s1) < len(s2):
            return self.levenshtein(s2, s1)

        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

class SeriesObject:
    
    def __init__(self, url):
        self. url = url
        self.poster = []
        self.fanart = []
        self.banners = []
        self.summary = ''
        self.info = {}
        self.season_dict = {}
        self.season_episode_dict = {}
        self.episode_summary = {}
        self.season_posters = {}
        self.total = 0
        self.title = ''

class DummyObject:
    
    def __init__(self, content):
        self.html = content
