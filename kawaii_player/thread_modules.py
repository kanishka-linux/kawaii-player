"""
Copyright (C) 2017 kanishka-linux kanishka.linux@gmail.com

This file is part of kawaii-player.

kawaii-player is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

kawaii-player is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with kawaii-player.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import re
import time
import ipaddress
import random
import socket
import urllib.request
from bs4 import BeautifulSoup
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import ccurl, write_files, open_files, send_notification
from yt import get_yt_url

class FindPosterThread(QtCore.QThread):

    summary_signal = pyqtSignal(str, str, str)

    def __init__(
            self, ui_widget, logr, tmp, name, url=None, direct_url=None,
            copy_fanart=None, copy_poster=None, copy_summary=None, use_search=None):
        QtCore.QThread.__init__(self)
        global ui, logger, TMPDIR, site
        ui = ui_widget
        logger = logr
        TMPDIR = tmp
        self.name = name
        self.url = url
        self.direct_url = direct_url
        self.copy_fanart = copy_fanart
        self.copy_poster = copy_poster
        self.copy_summary = copy_summary
        self.use_search = use_search
        self.summary_signal.connect(copy_information)
        site = ui.get_parameters_value(s='site')['site']
        
    def __del__(self):
        self.wait()                        

    def name_adjust(self, name):
        nam = re.sub('-|_| |\.', '+', name)
        nam = nam.lower()
        nam = re.sub('\[[^\]]*\]|\([^\)]*\)', '', nam)
        nam = re.sub(
            '\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4|\+season[^"]*|\+special[^"]*|xvid|bdrip|brrip|ac3|hdtv|dvdrip', '', nam)
        nam = nam.strip()
        return nam
    
    def ddg_search(self, nam, src, direct_search=None):
        m = []
        final_link = ''
        if direct_search:
            if src == 'tmdb':
                new_url = 'https://www.themoviedb.org/search?query='+nam
                content = ccurl(new_url)
                soup = BeautifulSoup(content, 'lxml')
                div_link = soup.find('div', {'class':'item poster card'})
                if div_link:
                    alink = div_link.find('a')
                    if 'href' in str(alink):
                        link = alink['href']
                        if link.startswith('/'):
                            final_link = 'https://www.themoviedb.org'+link
                        elif link.startswith('http'):
                            final_link = link
                        else:
                            final_link = 'https://www.themoviedb.org/'+link
                        m.append(final_link)
            elif src == 'tvdb+g' or src == 'tmdb+g':
                m = self.get_glinks(nam, src)
            elif src == 'tvdb+ddg' or src == 'tmdb+ddg':
                m = self.get_ddglinks(nam, src)
        else:
            m = self.get_ddglinks(nam, src)
        if m:
            final_link = m[0]
        logger.info('\n{0}---{1}\n'.format(final_link, m))
        return (final_link, m)
    
    def get_ddglinks(self, nam, src=None):
        m = []
        if src == 'tvdb' or src == 'tvdb+ddg':
            new_url = 'https://duckduckgo.com/html/?q='+nam+'+tvdb'
        elif src == 'tmdb' or src == 'tmdb+ddg':
            new_url = 'https://duckduckgo.com/html/?q='+nam+'+themoviedb'
        content = ccurl(new_url)
        soup = BeautifulSoup(content, 'lxml')
        div_val = soup.findAll('h2', {'class':'result__title'})
        logger.info(div_val)
        for div_l in div_val:
            new_url = div_l.find('a')
            if 'href' in str(new_url):
                new_link = new_url['href']
                final_link = re.search('http[^"]*', new_link).group()
                if src == 'tvdb' or src == 'tvdb+ddg':
                    if ('tvdb.com' in final_link and 'tab=episode' not in final_link 
                            and 'tab=seasonall' not in final_link):
                        m.append(final_link)
                elif src == 'tmdb' or src == 'tmdb+ddg':
                    if 'themoviedb.org' in final_link:
                        m.append(final_link)
                if m:
                    break
        return m
        
    def get_glinks(self, nam, src=None):
        if src == 'tmdb+g':
            url = "https://www.google.co.in/search?q="+nam+"+themoviedb"
        else:
            url = "https://www.google.co.in/search?q="+nam+"+tvdb"
        content = ccurl(url)
        soup = BeautifulSoup(content, 'lxml')
        m = soup.findAll('a')
        links = []
        for i in m:
            if 'href' in str(i):
                x = urllib.parse.unquote(i['href'])
                y = ''
                src = 'tvdb'
                if 'thetvdb.com' in x:
                    y = re.search('thetvdb.com[^"]*tab=series[^"]*', x)
                    src = 'tvdb'
                elif 'themoviedb.org' in x:
                    y = re.search('www.themoviedb.org[^"]*', x)
                    src = 'tmdb'
                if y:
                    y = y.group()
                    if src == 'tvdb':
                        y = 'http://'+y
                    else:
                        y = 'https://'+y
                    y = urllib.parse.unquote(y)
                    y = y.replace(' ', '%20')
                    y = re.sub('\&sa[^"]*', '', y)
                    links.append(y)
        return links
    
    def run(self):
        name = self.name
        url = self.url
        direct_url = self.direct_url
        #print(name, url, direct_url, '--poster--thread--')
        fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
        thumb = os.path.join(TMPDIR, name+'.jpg')
        fan_text = os.path.join(TMPDIR, name+'-fanart.txt')
        post_text = os.path.join(TMPDIR, name+'-poster.txt')
        logger.info(fanart)
        logger.info(thumb)
        final_link = ""
        m = []

        if site == 'Music':
            final = ''
            if (self.copy_fanart and self.copy_poster and self.copy_summary):
                if not direct_url and not url:
                    nam = self.name_adjust(name)
                    url = "http://www.last.fm/search?q="+nam
                    logger.info(url)
                wiki = ""
                content = ccurl(url)
                soup = BeautifulSoup(content, 'lxml')
                link = soup.findAll('div', {'class':'row clearfix'})
                name3 = ""
                for i in link:
                    j = i.findAll('a')
                    for k in j:
                        try:
                            url = k['href']
                            if '?q=' not in url:
                                logger.info(url)
                                break
                        except Exception as err:
                            print(err, '--108--')
                logger.info(url)
                if url.startswith('http'):
                    url = url
                else:
                    url = "http://www.last.fm" + url
                logger.info(url)
                img_url = url+'/+images'
                wiki_url = url + '/+wiki'
                logger.info(wiki_url)
                content = ccurl(wiki_url)
                soup = BeautifulSoup(content, 'lxml')
                link = soup.find('div', {'class':'wiki-content'})
                if link:
                    wiki = link.text
                    self.summary_signal.emit(name, wiki, 'summary')
                content = ccurl(img_url)
                soup = BeautifulSoup(content, 'lxml')
                link = soup.findAll('ul', {'class':'image-list'})
                img = []
                for i in link:
                    j = i.findAll('img')
                    for k in j:
                        l = k['src']
                        u1 = l.rsplit('/', 2)[0]
                        u2 = l.split('/')[-1]
                        u = u1 + '/770x0/'+u2
                        img.append(u)
                img = list(set(img))
                logger.info(len(img))
                thumb = os.path.join(TMPDIR, name+'.jpg')
                if img:
                    url = img[0]
                    try:
                        ccurl(url, curl_opt='-o', out_file=thumb)
                    except Exception as err:
                        print(err, '--151--')
            elif (self.copy_poster or self.copy_fanart) and url and direct_url:
                if 'last.fm' in url:
                    logger.info('--artist-link---{0}'.format(url))
                    content = ccurl(url)
                    soup = BeautifulSoup(content, 'lxml')
                    link = soup.findAll('img')
                    url1Code = url.split('/')[-1]
                    found = None
                    for i in link:
                        if 'src' in str(i):
                            j = i['src']
                            k = j.split('/')[-1]
                            if url1Code == k:
                                found = j
                                break
                    logger.info(str(found))
                    if found:
                        u1 = found.rsplit('/', 2)[0]
                        u2 = found.split('/')[-1]
                        final = u1 + '/770x0/'+u2
                        logger.info(final)
                elif (".jpg" in url or ".png" in url) and url.startswith('http'):
                    final = url
                else:
                    final = ''
                try:
                    if final.startswith('http'):
                        ccurl(final, curl_opt='-o', out_file=thumb)
                except Exception as e:
                    print(e)
        else:
            nam = self.name_adjust(name)
            src_site = 'tvdb'
            if self.use_search:
                if isinstance(self.use_search, bool):
                    final_link, m = self.ddg_search(nam, 'tvdb') 
                    if not m:
                        final_link, m = self.ddg_search(nam, 'tmdb')
                        if m:
                            src_site = 'tmdb' 
                else:
                    final_link, m = self.ddg_search(nam, self.use_search, direct_search=True)
                    src_site = self.use_search
            else:
                if direct_url and url:
                    if (".jpg" in url or ".png" in url or url.endswith('.webp')) and "http" in url:
                        if self.copy_poster:
                            ccurl(url+'#'+'-o'+'#'+thumb)
                        elif self.copy_fanart:
                            ccurl(url+'#'+'-o'+'#'+fanart)
                    elif 'tvdb' in url or 'themoviedb' in url:
                        final_link = url
                        logger.info(final_link)
                        m.append(final_link)
                        if 'themoviedb' in url:
                            src_site = 'tmdb'
                else:
                    link = "http://thetvdb.com/index.php?seriesname="+nam+"&fieldlocation=1&language=7&genre=Animation&year=&network=&zap2it_id=&tvcom_id=&imdb_id=&order=translation&addedBy=&searching=Search&tab=advancedsearch"
                    logger.info(link)
                    content = ccurl(link)
                    m = re.findall('/index.php[^"]tab=[^"]*', content)
                    if not m:
                        link = "http://thetvdb.com/index.php?seriesname="+nam+"&fieldlocation=2&language=7&genre=Animation&year=&network=&zap2it_id=&tvcom_id=&imdb_id=&order=translation&addedBy=&searching=Search&tab=advancedsearch"
                        content = ccurl(link)
                        m = re.findall('/index.php[^"]tab=[^"]*', content)
                        if not m:
                            link = "http://thetvdb.com/?string="+nam+"&searchseriesid=&tab=listseries&function=Search"
                            content = ccurl(link)
                            m = re.findall('/[^"]tab=series[^"]*lid=7', content)

            if m and (src_site == 'tvdb' or src_site == 'tvdb+g' or src_site == 'tvdb+ddg'):
                if not final_link:
                    n = re.sub('amp;', '', m[0])
                    elist = re.sub('tab=series', 'tab=seasonall', n)
                    url = "http://thetvdb.com" + n
                    logger.info(url)
                    elist_url = "http://thetvdb.com" + elist
                else:
                    url = final_link
                content = ccurl(url)
                soup = BeautifulSoup(content, 'lxml')
                sumry = soup.find('div', {'id':'content'})
                linkLabels = soup.findAll('div', {'id':'content'})
                logger.info(sumry)
                t_sum = re.sub('</h1>', '</h1><p>', str(sumry))
                t_sum = re.sub('</div>', '</p></div>', str(t_sum))
                soup = BeautifulSoup(t_sum, 'lxml')
                try:
                    title = (soup.find('h1')).text
                except Exception as err_val:
                    print(err_val)
                    title = 'Title Not Available'
                title = re.sub('&amp;', '&', title)
                try:
                    sumr = (soup.find('p')).text
                except Exception as e:
                    print(e, '--233--')
                    sumr = "Not Available"
                
                try:
                    link1 = linkLabels[1].findAll('td', {'id':'labels'})
                    logger.info(link1)
                    labelId = ""
                    for i in link1:
                        j = i.text 
                        if "Genre" in j:
                            k = str(i.findNext('td'))
                            l = re.findall('>[^<]*', k)
                            q = ""
                            for p in l:
                                q = q + " "+p.replace('>', '')
                            k = q 
                        else:
                            k = i.findNext('td').text
                            k = re.sub('\n|\t', '', k)
                        labelId = labelId + j +" "+k + '\n'
                except:
                    labelId = ""

                summary = title+'\n\n'+labelId+ sumr
                summary = re.sub('\t', '', summary)
                fan_all = post_all = []
                if self.copy_summary:
                    self.summary_signal.emit(name, summary, 'summary')
                fan_all = re.findall('/[^"]tab=seriesfanart[^"]*', content)
                logger.info(fan_all)
                content1 = ""
                content2 = ""
                post_all = re.findall('/[^"]tab=seriesposters[^"]*', content)
                logger.info(post_all)
                direct_jpg = False
                
                if not fan_all and not post_all:
                    fan_all = re.findall('banners/seasons/[^"]*.jpg', content)
                    post_all = fan_all
                    direct_jpg = True
                if fan_all:
                    url_fan_all = "http://thetvdb.com" + fan_all[0]
                    logger.info(url_fan_all)
                    if not direct_jpg:
                        content1 = ccurl(url_fan_all)
                        m = re.findall('banners/fanart/[^"]*jpg', content1)
                    else:
                        m = fan_all
                    m = list(set(m))
                    #m.sort()
                    m = random.sample(m, len(m))
                    length = len(m) - 1
                    logger.info(m)
                    fanart_text = os.path.join(TMPDIR, name+'-fanart.txt')
                    if not os.path.isfile(fanart_text):
                        f = open(fanart_text, 'w')
                        f.write(m[0])
                        i = 1
                        while(i <= length):
                            if not "vignette" in m[i]:
                                f.write('\n'+m[i])
                            i = i + 1
                        f.close()
                else:
                    m = re.findall('banners/fanart/[^"]*.jpg', content)
                    m = list(set(m))
                    #m.sort()
                    m = random.sample(m, len(m))
                    length = len(m) - 1
                    logger.info(m)
                    fanart_text = os.path.join(TMPDIR, name+'-fanart.txt')
                    if not os.path.isfile(fanart_text) and m:
                        f = open(fanart_text, 'w')
                        f.write(m[0])
                        i = 1
                        while(i <= length):
                            if not "vignette" in m[i]:
                                f.write('\n'+m[i])
                            i = i + 1
                        f.close()

                if post_all:
                    url_post_all = "http://thetvdb.com" + post_all[0]
                    logger.info(url_post_all)
                    if not direct_jpg:
                        content2 = ccurl(url_post_all)
                        r = re.findall('banners/posters/[^"]*jpg', content2)
                    else:
                        r = post_all
                    r = list(set(r))
                    #r.sort()
                    r = random.sample(r, len(r))
                    logger.info(r)
                    length = len(r) - 1
                    
                    poster_text = os.path.join(TMPDIR, name+'-poster.txt')
                    
                    if not os.path.isfile(poster_text):
                        f = open(poster_text, 'w')
                        f.write(r[0])
                        i = 1
                        while(i <= length):
                            f.write('\n'+r[i])
                            i = i + 1
                        f.close()
                else:
                    r = re.findall('banners/posters/[^"]*.jpg', content)
                    r = list(set(r))
                    #r.sort()
                    r = random.sample(r, len(r))
                    logger.info(r)
                    length = len(r) - 1
                    poster_text = os.path.join(TMPDIR, name+'-poster.txt')
                    if (r) and (not os.path.isfile(poster_text)):
                        f = open(poster_text, 'w')
                        f.write(r[0])
                        i = 1
                        while(i <= length):
                            f.write('\n'+r[i])
                            i = i + 1
                        f.close()

                poster_text = os.path.join(TMPDIR, name+'-poster.txt')
                fanart_text = os.path.join(TMPDIR, name+'-fanart.txt')

                if os.path.isfile(poster_text) and os.stat(poster_text).st_size:
                    lines = open_files(poster_text, True)
                    logger.info(lines)
                    url1 = re.sub('\n|#', '', lines[0])
                    url = "http://thetvdb.com/" + url1
                    ccurl(url+'#'+'-o'+'#'+thumb)
                if os.path.isfile(fanart_text) and os.stat(fanart_text).st_size:
                    lines = open_files(fanart_text, True)
                    logger.info(lines)
                    url1 = re.sub('\n|#', '', lines[0])
                    url = "http://thetvdb.com/" + url1
                    ccurl(url+'#'+'-o'+'#'+fanart)
                if os.path.exists(fanart_text):
                    os.remove(fanart_text)
                if os.path.exists(poster_text):
                    os.remove(poster_text)
            elif m and (src_site == 'tmdb' or src_site == 'tmdb+g' or src_site == 'tmdb+ddg'):
                url = final_link
                url_ext = ['discuss', 'reviews', 'posters', 'changes', 'videos', '#']
                url_end = url.rsplit('/', 1)[1]
                if url_end in url_ext:
                    url = url.rsplit('/', 1)[0]
                if '?' in url:
                    url = url.split('?')[0]
                content = ccurl(url)
                soup = BeautifulSoup(content, 'lxml')
                #logger.info(soup.prettify())
                title_div = soup.find('div', {'class':'title'})
                if title_div:
                    title = title_div.text
                else:
                    title = name
                summ = soup.find('div', {'class':'overview'})
                if summ:
                    summary = summ.text.strip()
                else:
                    summary = 'Not Available'
                cer_t = soup.find('div', {'class':'certification'})
                if cer_t:
                    cert = cer_t.text
                else:
                    cert = 'None'
                genre = soup.find("section", {"class":"genres right_column"})
                if genre:
                    genres = genre.text.strip()
                    genres = genres.replace('\n', ' ')
                    genres = genres.replace('Genres', 'Genres:')
                else:
                    genres = 'No Genres'
                new_summary = title.strip()+'\n\n'+cert.strip()+'\n'+genres.strip()+'\n\n'+summary.strip()
                if self.copy_summary:
                    self.summary_signal.emit(name, new_summary, 'summary')
                url = url + '/images/posters'
                content = ccurl(url)
                posters_link = re.findall('https://image.tmdb.org/[^"]*original[^"]*.jpg', content)
                if posters_link:
                    posters_link = random.sample(posters_link, len(posters_link))
                    if len(posters_link) == 1:
                        url = posters_link[0]
                        ccurl(url+'#'+'-o'+'#'+thumb)
                    elif len(posters_link) >= 2:
                        ccurl(posters_link[0]+'#'+'-o'+'#'+thumb)
                        ccurl(posters_link[1]+'#'+'-o'+'#'+fanart)
                

@pyqtSlot(str, str, str)
def copy_information(nm, txt, val):
    global ui
    if val == 'summary':
        ui.copySummary(new_name=nm, copy_sum=txt)
        new_copy_sum = 'Wait..Downloading Poster and Fanart..\n\n'+txt
        ui.text.setText(new_copy_sum)
    elif val == 'poster':
        ui.copyImg(new_name=nm)
    elif val == 'fanart':
        ui.copyFanart(new_name=nm)


class YTdlThread(QtCore.QThread):
    gotlink = pyqtSignal(str, str)
    def __init__(self, ui_widget, logr, url, quality, path, loger, nm, hdr):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.url = url
        self.quality = quality
        self.path = path
        self.loger = loger
        self.nm = nm
        self.hdr = hdr
        self.gotlink.connect(start_player_directly)

    def __del__(self):
        self.wait()                        

    def run(self):
        final_url = ''
        try:
            final_url = get_yt_url(self.url, self.quality, self.path,
                                   self.loger, mode='a+v')
            self.gotlink.emit(final_url, self.nm)
            try:
                if not self.nm:
                    req = urllib.request.Request(
                        self.url, data=None, headers={'User-Agent': 'Mozilla/5.0'})
                    f = urllib.request.urlopen(req)
                    content = f.read().decode('utf-8')
                    soup = BeautifulSoup(content, 'lxml')
                    title = soup.title.text.replace(' - YouTube', '').strip()
                    logger.info(title)
                    ui.epn_name_in_list = title
            except Exception as e:
                print(e, '---2877---')
        except Exception as e:
            print(e, '--2865--')


@pyqtSlot(str)
def start_player_directly(final_url, nm):
    global ui
    if final_url:
        print(final_url, '--youtube--')
        ui.epn_name_in_list = nm
        #ui.watchDirectly(final_url, nm, 'no')
        ui.epnfound_now_start_player(final_url, nm)

class DownloadThread(QtCore.QThread):

    def __init__(self, ui_widget, url):
        QtCore.QThread.__init__(self)
        global ui
        self.url = url
        self.interval = 1
        self.picn = 'picn'
        ui = ui_widget

    def __del__(self):
        self.wait()                        

    def run(self):
        ccurl(self.url)
        try:
            self.picn = self.url.split('#')[2]
            ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
        except Exception as e:
            print(e)


class PlayerWaitThread(QtCore.QThread):

    wait_signal = pyqtSignal(str)
    
    def __init__(self, ui_widget, command):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        self.command = command
        self.wait_signal.connect(start_new_player_instance)

    def __del__(self):
        self.wait()                        
    
    def run(self):
        print('{0}: Running'.format(ui.player_val))
        while ui.mpvplayer_val.processId() > 0:
            time.sleep(0.5)
            print('{0} Player still alive'.format(ui.player_val))
        self.wait_signal.emit(self.command)


@pyqtSlot(str)
def start_new_player_instance(command):
    global ui
    ui.infoPlay(command)

class PlayerGetEpn(QtCore.QThread):

    get_epn_signal = pyqtSignal(str, str)
    get_offline_signal = pyqtSignal(str, int)
    get_epn_signal_list = pyqtSignal(list, str)
    get_offline_signal_list = pyqtSignal(list, int)
    get_listfound_signal = pyqtSignal(list)
    
    def __init__(self, ui_widget, logr, epn_type, *args):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.epn_type = epn_type
        if self.epn_type == 'yt':
            self.final = args[0]
            self.quality = args[1]
            self.yt_path = args[2]
            self.row = args[3]
        elif (self.epn_type == 'addons' or self.epn_type == 'type_one' 
                or self.epn_type == 'type_two'):
            self.name = args[0]
            self.epn = args[1]
            self.mirrorNo = args[2]
            self.quality = args[3]
            self.row = args[4]
            if self.epn_type == 'type_two' or self.epn_type == 'type_one':
                self.siteName = args[5]
                if self.epn_type == 'type_one':
                    self.category = args[6]
        elif self.epn_type == 'offline':
            self.row = args[0]
            self.mode = args[1]
        elif self.epn_type == 'list':
            self.name = args[0]
            self.opt = args[1]
            self.depth_list = args[2]
            self.extra_info = args[3]
            self.siteName = args[4]
            self.category = args[5]
            self.row = args[6]
        else:
            pass
        #self.command = command
        logger.info(args)
        self.get_epn_signal.connect(connect_to_epn_generator)
        self.get_offline_signal.connect(connect_to_offline_mode)
        self.get_epn_signal_list.connect(connect_to_epn_generator_list)
        self.get_offline_signal_list.connect(connect_to_offline_mode_list)
        self.get_listfound_signal.connect(connect_to_listfound_signal)
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        finalUrl = ""
        try:
            if self.epn_type == 'yt':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='a+v')
            elif self.epn_type == 'addons':
                finalUrl = ui.site_var.getFinalUrl(self.name, self.epn,
                                                   self.mirrorNo, self.quality)
            elif self.epn_type == 'type_one':
                finalUrl = ui.site_var.getFinalUrl(self.siteName, self.name, self.epn,
                                                   self.mirrorNo, self.category,
                                                   self.quality)
            elif self.epn_type == 'type_two':
                finalUrl = ui.site_var.getFinalUrl(self.siteName, self.name, self.epn,
                                                   self.mirrorNo, self.quality)
            elif self.epn_type == 'offline':
                finalUrl = ui.epn_return(self.row, mode=self.mode)
            elif self.epn_type == 'list':
                mytuple = ui.site_var.getEpnList(self.name, self.opt,
                                                 self.depth_list, self.extra_info,
                                                 self.siteName, self.category)
                mylist = []
                for i in mytuple:
                    mylist.append(i)
                mylist.append(self.name)
                mylist.append(self.extra_info)
                mylist.append(self.siteName)
                mylist.append(self.opt)
                mylist.append(self.row)
        except Exception as err:
            print(err, '--707--')
        if self.epn_type != 'list':
            ui.epnfound_final_link = finalUrl
        if not isinstance(finalUrl, list):
            if self.epn_type == 'offline':
                self.get_offline_signal.emit(finalUrl, self.row)
            elif self.epn_type == 'list':
                self.get_listfound_signal.emit(mylist)
            else:
                self.get_epn_signal.emit(finalUrl, str(self.row))
        else:
            if self.epn_type == 'offline':
                self.get_offline_signal_list.emit(finalUrl, self.row)
            else:
                self.get_epn_signal_list.emit(finalUrl, str(self.row))
        
@pyqtSlot(str, str)
def connect_to_epn_generator(url, row):
    global ui
    ui.epnfound_now_start_player(url, row)
    
@pyqtSlot(str, int)
def connect_to_offline_mode(url, row):
    global ui
    ui.start_offline_mode_post(url, row)
    
@pyqtSlot(list, str)
def connect_to_epn_generator_list(url, row):
    global ui
    print('<<<<<<<<<<<<<\n\n{0}\n\n>>>>>>>>>'.format(url))
    ui.epnfound_now_start_player(url, row)
    
@pyqtSlot(list, int)
def connect_to_offline_mode_list(url, row):
    global ui
    ui.start_offline_mode_post(url, row)
    
@pyqtSlot(list)
def connect_to_listfound_signal(mylist):
    global ui
    ui.listfound(send_list=mylist)

class GetIpThread(QtCore.QThread):
    
    got_ip_signal = pyqtSignal(str)
    
    def __init__(self, ui_widget, interval=None, ip_file=None):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        if not interval:
            self.interval = (3600)
        else:
            self.interval = interval * (3600)
        self.got_ip_signal.connect(set_my_ip_function)
        self.ip_file = ip_file

    def __del__(self):
        self.wait()                        
    
    def run(self):
        while True:
            try:
                my_ip = str(ccurl('https://diagnostic.opendns.com/myip'))
                try:
                    ip_obj = ipaddress.ip_address(my_ip)
                except Exception as e:
                    print(e)
                    my_ip = 'none'
            except Exception as e:
                print(e)
                my_ip = 'none'
            self.got_ip_signal.emit(my_ip)
            print(my_ip, '--from-GetIpThread--', self.interval)
            time.sleep(self.interval)


@pyqtSlot(str)
def set_my_ip_function(my_ip):
    global ui
    if my_ip.lower() != 'none':
        ui.my_public_ip = my_ip
        print(ui.cloud_ip_file)
        if ui.cloud_ip_file:
            if os.path.exists(ui.cloud_ip_file):
                f = open(ui.cloud_ip_file, 'w')
                f.write(my_ip)
                f.close()
            else:
                print('cloud ip file is not available')
        else:
            print('Cloud File Does not exists')


class ThreadingThumbnail(QtCore.QThread):

    def __init__(self, ui_widget, logr, path, picn, inter):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.path = path
        self.picn = picn
        self.inter = inter
        self.interval = 1

    def __del__(self):
        self.wait()                        

    def run(self):
        logger.info(self.path)
        if not os.path.exists(self.picn) and self.path:
            try:
                if (self.path.startswith('http') and 
                    (self.path.endswith('.jpg') or self.path.endswith('.png') or self.path.endswith('.image'))):
                    ccurl(self.path+'#'+'-o'+'#'+self.picn)
                    ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
                else:
                    ui.generate_thumbnail_method(self.picn, self.inter, self.path)
            except Exception as e:
                logger.info("Thumbnail Generation Exception: {0}".format(e))
                print(e,'--548--')

class GetServerEpisodeInfo(QtCore.QThread):

    def __init__(
            self, ui_widget, logr, site, opt, siteName, video_local_stream,
            name, ei, category, from_cache):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.site = site
        self.opt = opt
        self.siteName = siteName
        self.video_local_stream = video_local_stream
        self.name = name
        self.ei = ei
        self.category = category
        self.from_cache = from_cache
        
    def __del__(self):
        self.wait()                        

    def run(self):
        print(self.name)
        ui.newlistfound(
            self.site, self.opt, self.siteName, self.video_local_stream,
            self.name, self.ei, self.category, from_cache=self.from_cache)
        print('End')

class ThreadingExample(QtCore.QThread):
    
    def __init__(self, name, logr, tmp):
        QtCore.QThread.__init__(self)
        global logger, TMPDIR
        self.name1 = name
        self.interval = 1
        logger = logr
        TMPDIR = tmp
        
    def __del__(self):
        self.wait()

    def run(self):
        name = self.name1
        name2 = name.replace(' ', '+')
        if name2 != 'NONE':
            url = "https://www.last.fm/search?q="+name2
            logger.info(url)
            wiki = ""
            content = ccurl(url)
            soup = BeautifulSoup(content, 'lxml')
            link = soup.findAll('div', {'class':'row clearfix'})
            logger.info('{0}-{1}'.format(link, 253))
            name3 = ""
            for i in link:
                j = i.findAll('a')
                for k in j:
                    try:
                        url = k['href']
                        if '?q=' not in url:
                            logger.info(url)
                            break
                    except:
                        pass
            logger.info(url)
            if url.startswith('http'):
                url = url
            else:
                url = "https://www.last.fm" + url
            logger.info(url)
            img_url = url+'/+images'
            wiki_url = url + '/+wiki'
            logger.info(wiki_url)
            content = ccurl(wiki_url)
            soup = BeautifulSoup(content, 'lxml')
            link = soup.find('div', {'class':'wiki-content'})
            if link:
                wiki = link.text
            content = ccurl(img_url)
            soup = BeautifulSoup(content, 'lxml')
            link = soup.findAll('ul', {'class':'image-list'})
            img = []
            for i in link:
                j = i.findAll('img')
                for k in j:
                    l = k['src']
                    u1 = l.rsplit('/', 2)[0]
                    u2 = l.split('/')[-1]
                    u = u1 + '/770x0/'+u2
                    img.append(u)
            img = list(set(img))
            logger.info(len(img))
            tmp_bio = os.path.join(TMPDIR, name+'-bio.txt')
            write_files(tmp_bio, wiki, line_by_line=False)
            thumb = os.path.join(TMPDIR, name+'.jpg')
            if img:
                url = img[0]
                try:
                    ccurl(url+'#'+'-o'+'#'+thumb)
                except Exception as err:
                    print(err, '--623--')
            tmp_n = os.path.join(TMPDIR, name+'.txt')
            write_files(tmp_n, img, line_by_line=True)

class BroadcastServer(QtCore.QThread):

    broadcast_signal = pyqtSignal(str)
    
    def __init__(self, ui_widget, broadcast=None):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        if broadcast:
            ui.broadcast_server = True
        self.broadcast_signal.connect(broadcast_server_signal)

    def __del__(self):
        self.wait()                        
    
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        port = str(ui.local_port_stream)
        print(ui.local_ip_stream, '-----ip--', ui.local_port_stream)
        msg = 'this is kawaii-player At: port={} https={} msg={}'.format(
            port, ui.https_media_server, ui.broadcast_message)
        msg = bytes(msg , 'utf-8')
        if ui.https_media_server:
            https_val = 'https'
        else:
            https_val = 'http'
        subnet_mask = ui.local_ip_stream.rsplit('.', 1)[0] + '.255'
        notify_msg = '{0}://{1}:{2} started broadcasting. Now Clients can Discover it'.format(
            https_val, ui.local_ip_stream, ui.local_port_stream)
        send_notification(notify_msg)
        print(subnet_mask)
        while ui.broadcast_server:
            s.sendto(msg, (subnet_mask,12345))
            time.sleep(1)
        send_notification('Broadcasting Stopped')

@pyqtSlot(str)
def broadcast_server_signal(val):
    send_notification(val)

class DiscoverServer(QtCore.QThread):

    discover_signal = pyqtSignal(str)
    clear_list = pyqtSignal(str)
    def __init__(self, ui_widget, start_discovery=None):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        if start_discovery:
            ui.discover_server = True
        self.discover_signal.connect(remember_server)
        self.clear_list.connect(clear_server_list)
    def __del__(self):
        self.wait()                        
    
    def run(self):
        print('hello world---server discovery')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 12345))
        s.settimeout(60)
        port_val = ''
        https_val = ''
        msg_val = ''
        send_notification('Started Process of Discovering')
        self.clear_list.emit('start')
        while ui.discover_server:
            try:
                m = s.recvfrom(1024)
                val = str(m[0], 'utf-8')
                server = str(m[1][0])
                if val.lower().startswith('this is kawaii-player at:'):
                    val_string = (val.split(':')[1]).strip()
                    val_arr = val_string.split(' ')
                    for i in val_arr:
                        if i.startswith('port='):
                            port_val = i.split('=')[1]
                        elif i.startswith('https='):
                            https_status = i.split('=')[1]
                            if https_status == 'True':
                                https_val = 'https'
                            else:
                                https_val = 'http'
                    msg_val = re.search('msg=[^"]*', val_string).group()
                    msg_val = msg_val.replace('msg=', '', 1)
                    server_val = '{0}://{1}:{2}/\t{3}'.format(
                        https_val, server, port_val, msg_val)
                    if server_val not in ui.broadcast_server_list:
                        ui.broadcast_server_list.append(server_val)
                        self.discover_signal.emit(server_val)
                time.sleep(1)
            except Exception as e:
                print('timeout', e)
                break
        if not ui.broadcast_server_list:
            send_notification('No Server Found')
            self.clear_list.emit('no server')
        else:
            send_notification('Stopped Discovering: found {} servers'.format(len(ui.broadcast_server_list)))

@pyqtSlot(str)
def remember_server(val):
    ui.text.setText('Found..')
    ui.original_path_name.append(val)
    ui.list1.addItem(val.split('\t')[0])
    
@pyqtSlot(str)
def clear_server_list(val):
    if val == 'start':
        ui.text.setText('Waiting...(wait time = 60s)')
    elif val == 'no server':
        ui.text.setText('Nothing found. Try Manual Login')
    ui.broadcast_server_list.clear()
    ui.list1.clear()
    ui.original_path_name.clear()

@pyqtSlot(str)
def start_new_player_instance(command):
    global ui
    ui.infoPlay(command)
