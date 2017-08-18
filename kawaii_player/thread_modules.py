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
import urllib.request
from bs4 import BeautifulSoup
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import ccurl, write_files, open_files
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
        nam = re.sub('-|_| ', '+', name)
        nam = nam.lower()
        nam = re.sub('\[[^\]]*\]|\([^\)]*\)', '', nam)
        nam = re.sub(
            '\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4|\+season[^"]*|\+special[^"]*', '', nam)
        nam = nam.strip()
        return nam

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
                        ccurl(url+'#'+'-o'+'#'+thumb)
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
                        ccurl(final+'#'+'-o'+'#'+thumb)
                except Exception as e:
                    print(e)
        else:
            nam = self.name_adjust(name)
            if self.use_search:
                m = []
                new_url = 'https://duckduckgo.com/html/?q='+nam+'+tvdb'
                content = ccurl(new_url)
                soup = BeautifulSoup(content, 'lxml')
                div_val = soup.findAll('h2', {'class':'result__title'})
                logger.info(div_val)
                for div_l in div_val:
                    new_url = div_l.find('a')
                    if 'href' in str(new_url):
                        new_link = new_url['href']
                        final_link = re.search('http[^"]*', new_link).group()
                        if ('tvdb.com' in final_link and 'tab=episode' not in final_link 
                                and 'tab=seasonall' not in final_link):
                            m.append(final_link)
                            break
            else:
                if direct_url and url:
                    if (".jpg" in url or ".png" in url or url.endswith('.webp')) and "http" in url:
                        if self.copy_poster:
                            ccurl(url+'#'+'-o'+'#'+thumb)
                        elif self.copy_fanart:
                            ccurl(url+'#'+'-o'+'#'+fanart)
                    elif 'tvdb' in url:
                        final_link = url
                        logger.info(final_link)
                        m.append(final_link)
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

            if m:
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
            final_url = get_yt_url(self.url, self.quality, self.path, self.loger)
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
        ui.watchDirectly(final_url, nm, 'no')

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
                    (self.path.endswith('.jpg') or self.path.endswith('.png'))):
                    ccurl(self.path+'#'+'-o'+'#'+self.picn)
                    ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
                else:
                    ui.generate_thumbnail_method(self.picn, self.inter, self.path)
            except Exception as e:
                logger.info("Thumbnail Generation Exception: {0}".format(e))
                print(e,'--548--')


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
