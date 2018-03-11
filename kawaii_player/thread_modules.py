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
import imp
import time
import ipaddress
import random
import socket
import shutil
import urllib.request
import hashlib
from functools import partial
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import ccurl, write_files, open_files, send_notification
from yt import get_yt_url

class FindPosterThread(QtCore.QThread):

    summary_signal = pyqtSignal(str, str, str)
    thumb_signal = pyqtSignal(list)
    imagesignal = pyqtSignal(dict, str, str)
    
    def __init__(
            self, ui_widget, logr, tmp, name, url=None, direct_url=None,
            copy_fanart=None, copy_poster=None, copy_summary=None,
            use_search=None, video_dir=None):
        QtCore.QThread.__init__(self)
        global ui, logger, TMPDIR, site, siteName
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
        self.video_dir = video_dir
        self.image_dict_list = {}
        self.dest_dir = ''
        self.summary_signal.connect(copy_information)
        self.thumb_signal.connect(update_playlist_widget)
        self.imagesignal.connect(update_image_list)
        site = ui.get_parameters_value(s='site')['site']
        siteName = ui.get_parameters_value(s='siteName')['siteName']
        self.site = site
        
    def __del__(self):
        self.wait()
        
    def remove_extra_thumbnails(self, dest):
        if os.path.exists(dest):
            small_nm_1, new_title = os.path.split(dest)
            small_nm_2 = '128px.'+new_title
            small_nm_3 = '480px.'+new_title
            small_nm_4 = 'label.'+new_title
            new_small_thumb = os.path.join(small_nm_1, small_nm_2)
            small_thumb = os.path.join(small_nm_1, small_nm_3)
            small_label = os.path.join(small_nm_1, small_nm_4)
            logger.info(new_small_thumb)
            if os.path.exists(new_small_thumb):
                os.remove(new_small_thumb)
            if os.path.exists(small_thumb):
                os.remove(small_thumb)
            if os.path.exists(small_label):
                os.remove(small_label)
    
    def create_extra_thumbnails(self, picn):
        if os.path.exists(picn) and os.stat(picn).st_size:
            ui.create_new_image_pixel(picn, 128)
            ui.create_new_image_pixel(picn, 480)
            label_name = 'label.'+os.path.basename(picn)
            path_thumb, new_title = os.path.split(picn)
            new_picn = os.path.join(path_thumb, label_name)
            if not os.path.exists(new_picn):
                ui.image_fit_option(picn, new_picn, fit_size=6, widget=ui.label)
    
    def run_curl(self, url=None, get_text=None, img_list=None):
        dest = dest_txt = ep_url = dest_txt = ''
        if img_list and len(img_list) == 7:
            img_url, dt, ep_url, local_path, site, img_key, dest_txt = img_list
            
        if not get_text:
            if url.startswith('http'):
                ccurl(url)
            try:
                if url:
                    picn = url.split('#')[2]
                    ui.image_fit_option(picn, picn, fit_size=6, widget=ui.label)
                    if site.lower() == 'video':
                        self.remove_extra_thumbnails(picn)
                        self.create_extra_thumbnails(picn)
                        
            except Exception as e:
                print(e)
        else:
            txt = 'Air Date: '+ dt + '\n\nEpisode Name: ' + img_key + '\n\nOverview: '
            if ep_url and dest_txt:
                if ep_url.startswith('http'):
                    content = ccurl(ep_url)
                    soup = BeautifulSoup(content, 'lxml')
                    txt_lnk = soup.find('textarea', {'name' : 'Overview_7'})
                    if txt_lnk:
                        txt_val = txt_lnk.text
                        txt_val = txt_val.strip()
                        txt = txt + txt_val
            if dest_txt:
                write_files(dest_txt, txt, False)
    
    
    def update_image_list_method(self, image_dict, dest_dir, site):
        if (site != 'Music' and site != 'PlayLists'
                and site != 'NONE' and site != 'MyServer'):
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            for img_key, img_val in image_dict.items():
                img_url, dt, ep_url, local_path, site_record = img_val
                if site.lower() == 'video':
                    if '\t' in local_path:
                        path = local_path.split('\t')[0]
                    path = local_path.replace('"', '')
                    print(path)
                    thumb_name_bytes = bytes(path, 'utf-8')
                    h = hashlib.sha256(thumb_name_bytes)
                    thumb_name = h.hexdigest()
                    dest_txt = os.path.join(dest_dir, thumb_name+'.txt')
                    dest_picn = os.path.join(dest_dir, thumb_name+'.jpg')
                else:
                    dest_txt = os.path.join(dest_dir, img_key+'.txt')
                    dest_picn = os.path.join(dest_dir, img_key+'.jpg')
                    
                if img_url.startswith('//'):
                    img_url = "http:"+img_url
                
                picn_url = img_url+'#-o#'+dest_picn
                    
                img_val_copy = img_val.copy()
                img_val_copy.append(img_key)
                img_val_copy.append(dest_txt)
                
                self.run_curl(url=picn_url, get_text=False, img_list=img_val_copy)
                self.run_curl(url=picn_url, get_text=True, img_list=img_val_copy)
    
    def parse_tvdb(self, name, url):
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
        fan_arr = []
        post_arr = []
        if not fan_all and not post_all:
            fan_all = re.findall('banners/seasons/[^"]*.jpg', content)
            post_all = fan_all
            direct_jpg = True
        if fan_all:
            url_fan_all = "http://thetvdb.com" + fan_all[0]
            logger.info(url_fan_all)
            if not direct_jpg:
                content1 = ccurl(url_fan_all)
                fan_arr = re.findall('banners/fanart/[^"]*jpg', content1)
            else:
                fan_arr = fan_all
        else:
            fan_arr = re.findall('banners/fanart/[^"]*.jpg', content)
            
        fan_arr = list(set(fan_arr))
        fan_arr = random.sample(fan_arr, len(fan_arr))
        
        if post_all:
            url_post_all = "http://thetvdb.com" + post_all[0]
            logger.info(url_post_all)
            if not direct_jpg:
                content2 = ccurl(url_post_all)
                post_arr = re.findall('banners/posters/[^"]*jpg', content2)
            else:
                post_arr = post_all
        else:
            post_arr = re.findall('banners/posters/[^"]*.jpg', content)
            
        post_arr = list(set(post_arr))
        post_arr = random.sample(post_arr, len(post_arr))
        return (post_arr, fan_arr)
    
    def parse_tmdb(self, name, final_link, thumb, fanart):
        url = final_link
        url_ext = ['discuss', 'reviews', 'posters', 'changes', 'videos', '#']
        url_end = url.rsplit('/', 1)[1]
        if url_end in url_ext:
            url = url.rsplit('/', 1)[0]
        if '?' in url:
            url = url.split('?')[0]
        if url.endswith('/en'):
            url = url.rsplit('/', 1)[0]
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
        if url.endswith('/en'):
            url = url.rsplit('/', 1)[0]
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
    
    def init_search(self, nam, url, direct_url, thumb, fanart, src_site):
        final_link = ""
        m = []
        if self.use_search:
            if isinstance(self.use_search, bool):
                final_link, m = ui.metaengine.ddg_search(nam, 'tvdb') 
                if not m:
                    final_link, m = ui.metaengine.ddg_search(nam, 'tmdb')
                    if m:
                        src_site = 'tmdb' 
            else:
                final_link, m = ui.metaengine.ddg_search(nam, self.use_search, direct_search=True)
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
        return (m, final_link, src_site)
        
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
                    nam = ui.metaengine.name_adjust(name)
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
            nam = ui.metaengine.name_adjust(name)
            src_site = 'tvdb'
            epn_arr = []
            post_val = ''
            fan_val = ''
            logger.debug('\nvideo_dir={0}\n'.format(self.video_dir))
            if site.lower() == 'video' and self.video_dir:
                 video_db = os.path.join(ui.home_folder, 'VideoDB', 'Video.db')
                 if os.path.exists(video_db):
                    epn_arr_tmp = ui.media_data.get_video_db(video_db, "Directory", self.video_dir)
                    for i in epn_arr_tmp:
                        epn_name = i[0]+'	'+i[1]
                        logger.debug(epn_name)
                        epn_arr.append(epn_name)
            elif self.video_dir:
                new_name_with_info = self.video_dir.strip()
                extra_info = ''
                if '	' in new_name_with_info:
                    name_title = new_name_with_info.split('	')[0]
                    extra_info = new_name_with_info.split('	')[1]
                else:
                    name_title = new_name_with_info
                
                if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime' and siteName:
                    hist_site = os.path.join(ui.home_folder, 'History', site, siteName, name_title)
                else:
                    hist_site = os.path.join(ui.home_folder, 'History', site, name_title)
                    
                hist_epn = os.path.join(hist_site, 'Ep.txt')
                logger.info(hist_epn)
                if os.path.exists(hist_epn):
                    lines = open_files(hist_epn, True)
                    for i in lines:
                        i = i.strip()
                        j = i.split('	')
                        if len(j) == 1:
                            epn_arr.append(i+'	'+i+'	'+name)
                        elif len(j) >= 2:
                            epn_arr.append(i+'	'+name)
                            
            if ui.series_info_dict.get(name) and not epn_arr:
                logger.debug('getting values from cache')
                dict_val = ui.series_info_dict.get(name)
                post_arr = dict_val.get('poster')
                fan_arr = dict_val.get('fanart')
                fan_index = dict_val.get('f')
                post_index = dict_val.get('p')
                if fan_index < len(fan_arr):
                    fan_val = fan_arr[fan_index]
                    fan_index = (fan_index + 1) % len(fan_arr)
                    dict_val.update({'f':fan_index})
                if post_index < len(post_arr):
                    post_val = post_arr[post_index]
                    post_index = (post_index + 1) % len(post_arr)
                    dict_val.update({'p':post_index})
                ui.series_info_dict.update({name:dict_val})
                if isinstance(self.use_search, bool):
                    src_site = 'tvdb'
                else:
                    src_site = self.use_search
            else:
                m, final_link, src_site = self.init_search(
                    nam, url, direct_url, thumb, fanart, src_site
                    )
            if (m and src_site in ['tvdb', 'tvdb+g', 'tvdb+ddg']) or post_val or fan_val:
                if post_val or fan_val:
                    if post_val:
                        url = "http://thetvdb.com/" + post_val
                        ccurl(url+'#'+'-o'+'#'+thumb)
                    if fan_val:
                        url = "http://thetvdb.com/" + fan_val
                        ccurl(url+'#'+'-o'+'#'+fanart)
                else:
                    if not final_link:
                        n = re.sub('amp;', '', m[0])
                        elist = re.sub('tab=series', 'tab=seasonall', n)
                        url = "http://thetvdb.com" + n
                        logger.info(url)
                        elist_url = "http://thetvdb.com" + elist
                    else:
                        url = final_link
                    post_arr, fan_arr = self.parse_tvdb(name, url)
                    if post_arr:
                        url = "http://thetvdb.com/" + post_arr[0]
                        ccurl(url+'#'+'-o'+'#'+thumb)
                        logger.info(post_arr)
                    if fan_arr:
                        #if ui.player_theme != 'default':
                        fan_arr = [i for i in fan_arr if 'vignette' not in i]
                        if fan_arr:
                            url = "http://thetvdb.com/" + fan_arr[0]
                            ccurl(url+'#'+'-o'+'#'+fanart)
                        logger.debug(fan_arr)
                    fan_arr.sort()
                    post_arr.sort()
                    ui.series_info_dict.update(
                            {
                            name:{
                                'fanart':fan_arr.copy(), 'poster':post_arr.copy(),
                                'f':0, 'p':0
                                }
                            }
                        )
                    elist_url = re.sub('tab=series', 'tab=seasonall', final_link)
                    if epn_arr:
                        ui.metaengine.getTvdbEpnInfo(
                            elist_url, epn_arr=epn_arr.copy(), site=site,
                            name=name, thread=self, video_dir=self.video_dir
                            )
                        image_dict = self.image_dict_list.copy()
                        dest_dir = self.dest_dir
                        self.imagesignal.emit(image_dict, dest_dir, site)
            elif m and src_site in ['tmdb', 'tmdb+g', 'tmdb+ddg']:
                self.parse_tmdb(name, final_link, thumb, fanart)


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

@pyqtSlot(list)
def update_playlist_widget(epn_arr):
    ui.update_list2(epn_arr)

@pyqtSlot(dict, str, str)
def update_image_list(image_dict, dest_dir, site):
    global ui
    if dest_dir:
        update_image_list_method(image_dict, dest_dir, site)
        

def update_image_list_method(image_dict, dest_dir, site):
    global ui
    if (site != 'Music' and site != 'PlayLists'
            and site != 'NONE' and site != 'MyServer'):
        r = 0
        start_pt = 0
        start_now = True
        length = 0
        txt_count = 0
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        for img_key, img_val in image_dict.items():
            img_url, dt, ep_url, local_path, site_record = img_val
            if site.lower() == 'video':
                if '\t' in local_path:
                    path = local_path.split('\t')[0]
                path = local_path.replace('"', '')
                thumb_name_bytes = bytes(path, 'utf-8')
                h = hashlib.sha256(thumb_name_bytes)
                thumb_name = h.hexdigest()
                dest_txt = os.path.join(dest_dir, thumb_name+'.txt')
                dest_picn = os.path.join(dest_dir, thumb_name+'.jpg')
            else:
                dest_txt = os.path.join(dest_dir, img_key+'.txt')
                dest_picn = os.path.join(dest_dir, img_key+'.jpg')
                
            if img_url.startswith('//'):
                img_url = "http:"+img_url
            
            picn_url = img_url+'#-o#'+dest_picn
                
            img_val_copy = img_val.copy()
            img_val_copy.append(img_key)
            img_val_copy.append(dest_txt)
            
            ui.downloadWget.append(
                DownloadThread(ui, picn_url, img_list=img_val_copy)
                )
            length = len(ui.downloadWget)
            ui.downloadWget[length-1].finished.connect(
                partial(ui.download_thread_finished, dest_picn, r, length-1))
            if not ui.wget_counter_list:
                ui.wget_counter_list = [1 for i in range(len(image_dict))]
                ui.downloadWget[length-1].start()
            r += 1
            
            ui.downloadWgetText.append(
                DownloadThread(ui, picn_url, img_list=img_val_copy,
                get_text=True)
                )
            length_text = len(ui.downloadWgetText)
            ui.downloadWgetText[length_text-1].finished.connect(
                partial(ui.download_thread_text_finished, dest_txt,
                txt_count, length_text-1)
                )
            if not ui.wget_counter_list_text:
                ui.wget_counter_list_text = [1 for i in range(len(image_dict))]
                ui.downloadWgetText[length_text-1].start()
            txt_count += 1


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
        
class UpdateMusicThread(QtCore.QThread):
    
    music_db_update = pyqtSignal(str)
    
    def __init__(self, ui_widget, music_db, music_file, music_file_bak):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        self.music_db = music_db
        self.music_file = music_file
        self.music_file_bak = music_file_bak
        self.music_db_update.connect(update_music_db_onstart)

    def __del__(self):
        self.wait()                        

    def run(self):
        self.music_db_update.emit('start')
        ui.media_data.update_on_start_music_db(self.music_db, self.music_file,
                                               self.music_file_bak)
        self.music_db_update.emit('end')

@pyqtSlot(str)
def update_music_db_onstart(val):
    global ui
    if val == 'start':
        ui.text.setText('Wait..Checking New Files')
    else:
        ui.text.setText('Finished Checking')

class DownloadThread(QtCore.QThread):

    def __init__(self, ui_widget, url, img_list=None, get_text=None):
        QtCore.QThread.__init__(self)
        global ui
        self.url = url
        self.interval = 1
        self.picn = 'picn'
        ui = ui_widget
        if img_list:
            """img_list=[img_url, date, ep_url, local_path, site, img_key, dest_dir]"""
            self.img_list = img_list.copy()
        else:
            self.img_list = []
        if get_text:
            self.get_text = True
        else:
            self.get_text = False

    def __del__(self):
        self.wait()                        
        
    def remove_extra_thumbnails(self, dest):
        if os.path.exists(dest):
            small_nm_1, new_title = os.path.split(dest)
            small_nm_2 = '128px.'+new_title
            small_nm_3 = '480px.'+new_title
            small_nm_4 = 'label.'+new_title
            new_small_thumb = os.path.join(small_nm_1, small_nm_2)
            small_thumb = os.path.join(small_nm_1, small_nm_3)
            small_label = os.path.join(small_nm_1, small_nm_4)
            logger.info(new_small_thumb)
            if os.path.exists(new_small_thumb):
                os.remove(new_small_thumb)
            if os.path.exists(small_thumb):
                os.remove(small_thumb)
            if os.path.exists(small_label):
                os.remove(small_label)
    
    def create_extra_thumbnails(self, picn):
        if os.path.exists(picn) and os.stat(picn).st_size:
            ui.create_new_image_pixel(picn, 128)
            ui.create_new_image_pixel(picn, 480)
            label_name = 'label.'+os.path.basename(picn)
            path_thumb, new_title = os.path.split(picn)
            new_picn = os.path.join(path_thumb, label_name)
            if not os.path.exists(new_picn):
                ui.image_fit_option(picn, new_picn, fit_size=6, widget=ui.label)
    
    def run(self):
        dest = dest_txt = ep_url = dest_txt = ''
        if self.img_list and len(self.img_list) == 7:
            img_url, dt, ep_url, local_path, site, img_key, dest_txt = self.img_list
            
        if not self.get_text:
            if self.url.startswith('http'):
                ccurl(self.url)
            try:
                if self.url:
                    self.picn = self.url.split('#')[2]
                    ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
                    if site.lower() == 'video':
                        self.remove_extra_thumbnails(self.picn)
                        self.create_extra_thumbnails(self.picn)
                        
            except Exception as e:
                print(e)
        else:
            txt = 'Air Date: '+ dt + '\n\nEpisode Name: ' + img_key + '\n\nOverview: '
            if ep_url and dest_txt:
                if ep_url.startswith('http'):
                    content = ccurl(ep_url)
                    soup = BeautifulSoup(content, 'lxml')
                    txt_lnk = soup.find('textarea', {'name' : 'Overview_7'})
                    if txt_lnk:
                        txt_val = txt_lnk.text
                        txt_val = txt_val.strip()
                        txt = txt + txt_val
            if dest_txt:
                write_files(dest_txt, txt, False)


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
    get_title_signal = pyqtSignal(str, str)
    get_offline_signal_type_three = pyqtSignal(str, int, str, str)
    get_offline_signal_list_type_three = pyqtSignal(list, int, str, str)
    final_epn_prefetch_signal = pyqtSignal(str, int, str)
    
    def __init__(self, ui_widget, logr, epn_type, *args):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.epn_type = epn_type
        self.site_var = None
        param_dict = ui.get_parameters_value(s='site')
        self.site_name = param_dict['site']
        if self.epn_type in ['yt', 'yt_title', 'yt+title', 'yt_music',
                             'yt_prefetch_av', 'yt_prefetch_a']:
            self.final = args[0]
            self.quality = args[1]
            self.yt_path = args[2]
            self.row = args[3]
        elif self.epn_type in ['addons', 'type_one', 'type_two', 'type_three']:
            self.name = args[0]
            self.epn = args[1]
            self.mirrorNo = args[2]
            self.quality = args[3]
            self.row = args[4]
            if self.epn_type in ['type_two', 'type_one', 'type_three']:
                if self.epn_type == 'type_three':
                    self.site = args[5]
                    self.siteName = args[6]
                    self.epnname = args[7]
                    if self.site_name != self.site:
                        plugin_path = os.path.join(ui.home_folder, 'src', 'Plugins', self.site+'.py')
                        if os.path.exists(plugin_path):
                            module = imp.load_source(self.site, plugin_path)
                            self.site_var = getattr(module, self.site)(ui.tmp_download_folder)
                else:
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
        self.get_epn_signal_list.connect(connect_to_epn_generator_list)
        
        self.get_offline_signal.connect(connect_to_offline_mode)
        self.get_offline_signal_list.connect(connect_to_offline_mode_list)
        
        self.get_offline_signal_type_three.connect(connect_to_offline_mode_type_three)
        self.get_offline_signal_list_type_three.connect(connect_to_offline_mode_list_type_three)
        
        self.get_listfound_signal.connect(connect_to_listfound_signal)
        self.get_title_signal.connect(connect_post_title)
        self.final_epn_prefetch_signal.connect(connect_prefetch_slot)
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        finalUrl = ""
        nosignal = False
        mylist = []
        try:
            if self.epn_type == 'yt':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='a+v')
            elif self.epn_type == 'yt_music':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='music')
            elif self.epn_type == 'yt_prefetch_av':
                if ui.use_single_network_stream:
                    ytmode = 'offline'
                else:
                    ytmode = 'a+v'
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode=ytmode)
            elif self.epn_type == 'yt_prefetch_a':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='music')
            elif self.epn_type == 'yt_title':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='TITLE')
            elif self.epn_type == 'yt+title':
                finalUrl = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='a+v')
                
                self.get_epn_signal.emit(finalUrl, '-1')
                title = get_yt_url(self.final, self.quality, self.yt_path,
                                      logger, mode='TITLE')
                self.get_title_signal.emit(title, self.final)
                nosignal = True
            elif self.epn_type == 'addons':
                finalUrl = ui.site_var.getFinalUrl(self.name, self.epn,
                                                   self.mirrorNo, self.quality)
            elif self.epn_type == 'type_three':
                if self.site_var:
                    if self.siteName:
                        finalUrl = self.site_var.getFinalUrl(
                            self.name, self.epn, self.mirrorNo,
                            self.quality, sn=self.siteName
                            )
                    else:
                        finalUrl = self.site_var.getFinalUrl(
                            self.name, self.epn, self.mirrorNo, self.quality
                            )
                else:
                    if self.siteName:
                        finalUrl = ui.site_var.getFinalUrl(
                            self.name, self.epn, self.mirrorNo,
                            self.quality, sn=self.siteName
                            )
                    else:
                        finalUrl = ui.site_var.getFinalUrl(
                            self.name, self.epn, self.mirrorNo, self.quality
                            )
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
                for i in mytuple:
                    mylist.append(i)
                mylist.append(self.name)
                mylist.append(self.extra_info)
                mylist.append(self.siteName)
                mylist.append(self.opt)
                mylist.append(self.row)
        except Exception as err:
            logger.error('{0}::--984--'.format(err))
        if nosignal:
            pass
        else:
            if self.epn_type != 'list' and self.epn_type != 'yt_title':
                ui.epnfound_final_link = finalUrl
            if not isinstance(finalUrl, list):
                if self.epn_type == 'offline':
                    self.get_offline_signal.emit(finalUrl, self.row)
                elif self.epn_type == 'type_three':
                    self.get_offline_signal_type_three.emit(
                        finalUrl, self.row, self.name, self.epnname
                        )
                elif self.epn_type == 'list':
                    self.get_listfound_signal.emit(mylist)
                elif self.epn_type == 'yt_title':
                    self.get_title_signal.emit(finalUrl, self.final)
                elif self.epn_type in ['yt_prefetch_av', 'yt_prefetch_a']:
                    self.final_epn_prefetch_signal.emit(finalUrl, self.row, self.epn_type)
                else:
                    self.get_epn_signal.emit(finalUrl, str(self.row))
            else:
                if self.epn_type == 'offline':
                    self.get_offline_signal_list.emit(finalUrl, self.row)
                elif self.epn_type == 'type_three':
                    self.get_offline_signal_list_type_three.emit(
                        finalUrl, self.row, self.name, self.epnname
                        )
                else:
                    self.get_epn_signal_list.emit(finalUrl, str(self.row))
        
@pyqtSlot(str, str)
def connect_to_epn_generator(url, row):
    global ui
    if row == '-1':
        ui.watchDirectly(url, '', 'no')
    else:
        ui.epnfound_now_start_player(url, row)
    
@pyqtSlot(str, int)
def connect_to_offline_mode(url, row):
    global ui
    ui.start_offline_mode_post(url, row)
    
@pyqtSlot(list, int)
def connect_to_offline_mode_list(url, row):
    global ui
    ui.start_offline_mode_post(url, row)

@pyqtSlot(str, int, str, str)
def connect_to_offline_mode_type_three(url, row, name, epn):
    global ui
    ui.start_offline_mode_post(url, row, name, epn)

@pyqtSlot(list, int, str, str)
def connect_to_offline_mode_list_type_three(url, row, name, epn):
    global ui
    ui.start_offline_mode_post(url, row, name, epn)

@pyqtSlot(list, str)
def connect_to_epn_generator_list(url, row):
    global ui
    ui.epnfound_now_start_player(url, row)    

@pyqtSlot(str, int, str)
def connect_prefetch_slot(url, row, mode):
    global ui
    ui.epnfound_now_start_prefetch(url, row, mode)

@pyqtSlot(list)
def connect_to_listfound_signal(mylist):
    global ui
    ui.listfound(send_list=mylist)

@pyqtSlot(str, str)
def connect_post_title(epn_title, tpath):
    global ui
    if epn_title:
        ui.epn_name_in_list = epn_title.strip()
        file_entry = ui.epn_name_in_list+'	'+tpath+'	'+'NONE'
    else:
        ui.epn_name_in_list = 'No Title'
        file_entry = tpath.split('/')[-1]+'	'+tpath+'	'+'NONE'
    file_name = os.path.join(ui.home_folder, 'Playlists', 'TMP_PLAYLIST')
    if not os.path.exists(file_name):
        f = open(file_name, 'w').close()
    write_files(file_name, file_entry, True)
    item = ui.list1.item(0)
    if item:
        ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)

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
                        (self.path.endswith('.jpg') or self.path.endswith('.png')
                         or self.path.endswith('.image'))):
                    ccurl(self.path+'#'+'-o'+'#'+self.picn)
                    ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
                else:
                    ui.generate_thumbnail_method(self.picn, self.inter, self.path)
            except Exception as e:
                logger.info("Thumbnail Generation Exception: {0}".format(e))
                print(e,'--548--')


class SetThumbnail(QtCore.QThread):
    setThumb = pyqtSignal(int, str, str)
    def __init__(self, ui_widget, logr, epn_arr, update_pl, title_list):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.epn_arr = epn_arr.copy()
        self.update_pl = update_pl
        self.title_list = title_list
        self.setThumb.connect(apply_thumbnail_to_playlist)
        
    def __del__(self):
        self.wait()                        

    def run(self):
        generate_thumbnail = False
        if ui.list1.currentItem():
            txt = ui.list1.currentItem().text()
            if txt == self.title_list:
                generate_thumbnail = True
        if generate_thumbnail or ui.show_search_thumbnail:
            for i, k in enumerate(self.epn_arr):
                if ui.list_with_thumbnail and self.update_pl:
                    self.setThumb.emit(i, k, self.title_list)

@pyqtSlot(int, str, str)
def apply_thumbnail_to_playlist(k, i, title):
    try:
        if k < ui.list2.count():
            icon_name = ui.get_thumbnail_image_path(k, i, title_list=title)
            icon_new_pixel = ui.create_new_image_pixel(icon_name, 128)
            if os.path.exists(icon_new_pixel):
                ui.list2.item(k).setIcon(QtGui.QIcon(icon_new_pixel))
    except Exception as e:
        print(e)


class SetThumbnailGrid(QtCore.QThread):
    setThumbGrid = pyqtSignal(int, str, str, int, tuple, int, str)
    def __init__(self, ui_widget, logr, browse_cnt, picn, val, fit_size,
                 widget_size, length, nameEpn, path=None):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.browse_cnt = browse_cnt
        self.picn = picn
        self.val = val
        self.fit_size = fit_size
        self.widget_size = widget_size
        self.length = length
        self.nameEpn = nameEpn
        self.setThumbGrid.connect(apply_to_thumbnail_grid)
        self.path = path
        
    def __del__(self):
        self.wait()                        

    def run(self):
        counter_limit = 10
        if self.path is not None:
            if self.path.startswith('http'):
                counter_limit = 120
        counter = 0
        while True and counter < counter_limit:
            if os.path.isfile(self.picn):
                if os.stat(self.picn).st_size:
                    break
            time.sleep(0.5)
            counter += 1
        if os.path.exists(self.picn):
            self.setThumbGrid.emit(self.browse_cnt, self.picn, self.val,
                                   self.fit_size, self.widget_size, self.length,
                                   self.nameEpn)

@pyqtSlot(int, str, str, int, tuple, int, str)
def apply_to_thumbnail_grid(browse_cnt, picn, val, fit_size, widget_size, length, nameEpn):
    try:
        picn_old = picn
        picn = ui.image_fit_option(picn_old, '', fit_size=fit_size, widget_size=widget_size)
        img = QtGui.QPixmap(picn, "1")
        q1="ui.label_epn_"+str(browse_cnt)+".setPixmap(img)"
        exec (q1)
        #QtWidgets.QApplication.processEvents()
    except Exception as err:
        print(err, '--917--')

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
