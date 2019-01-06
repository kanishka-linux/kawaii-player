import os
import re
import time
import sqlite3
import hashlib
import urllib.parse
from functools import partial
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import ccurl, write_files, open_files
from thread_modules import DownloadThread



class MetaEngine:
    
    def __init__(self, ui_widget, logr, tmp, hm):
        global ui, logger, TMPDIR, home
        ui = ui_widget
        logger = logr
        TMPDIR = tmp
        home = hm
        self.thread_info = []
        self.epn_list = []
        self.image_dict_list = {}
        self.dest_dir = ''
        self.site = ''
        
    def name_adjust(self, name):
        nam = re.sub('-|_| |\.', '+', name)
        nam = nam.lower()
        nam = re.sub('\[[^\]]*\]|\([^\)]*\)', '', nam)
        nam = re.sub('\+sub|\+dub|subbed|dubbed|online|720p|1080p|480p|.mkv|.mp4', '', nam)
        nam = re.sub('\+season[^"]*|\+special[^"]*|xvid|bdrip|brrip|ac3|hdtv|dvdrip', '', nam)
        nam = nam.strip()
        dt = re.search("[1-2][0-9]{3}|[0-9]{2}[\']?s", name)
        if dt:
            nam = re.sub(dt.group(), '', nam)
            nam = nam.strip()
            nam = '{}+({})'.format(nam, dt.group())
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
        if src in ['tvdb', 'tvdb+ddg']:
            new_url = 'https://duckduckgo.com/html/?q='+nam+'+tvdb'
        elif src in ['tmdb', 'tmdb+ddg']:
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
                if src in ['tvdb', 'tvdb+ddg']:
                    if ('tvdb.com' in final_link and 'tab=episode' not in final_link 
                            and 'tab=seasonall' not in final_link):
                        m.append(final_link)
                elif src in ['tmdb', 'tmdb+ddg']:
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
    
    def find_info_thread(self, mode, row, epn_arr):
        info_thr = DownloadInfoThread(ui, self, mode, row, epn_arr)
        self.thread_info.append(info_thr)
        length = len(self.thread_info)
        self.thread_info[length-1].finished.connect(information_update)
        self.thread_info[length-1].start()
    
    def find_info(self, mode, row, thread=None, local_arr=None):
        name = ui.get_title_name(row)
        nam = self.name_adjust(name)
        nam1 = nam
        logger.info(nam)
        index = ""
        final_link_found = False
        final_link_arr = []
        if mode == 0:
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
                    if not m:
                        final_link_found = False
                    else:
                        final_link_found = True
                        final_link_arr = m
                else:
                    final_link_found = True
                    final_link_arr = m
            else:
                final_link_found = True
                final_link_arr = m
        elif mode == 1:
            final_link_arr = self.get_ddglinks(nam, src='tvdb')
            if final_link_arr:
                final_link_found = True
        elif mode == 2:
            final_link_arr = self.get_glinks(nam, src='tvdb')
            if final_link_arr:
                final_link_found = True
                
        logger.info(final_link_arr)
        if final_link_found and final_link_arr:
            n = re.sub('amp;', '', final_link_arr[0])
            elist = re.sub('tab=series', 'tab=seasonall', n)
            if not n.startswith('http'):
                url = "http://thetvdb.com" + n
                elist_url = "http://thetvdb.com" + elist
            else:
                url = n
                elist_url = elist
            site = ui.get_parameters_value(s='site')['site']
            self.getTvdbEpnInfo(elist_url, epn_arr=local_arr,
                              site=site, name=name, row=row, thread=thread)
    
    def get_epn_arr_list(self, site, name, video_dir):
        epn_arr = []
        if site.lower() == 'video' and video_dir:
             video_db = os.path.join(ui.home_folder, 'VideoDB', 'Video.db')
             if os.path.exists(video_db):
                epn_arr_tmp = ui.media_data.get_video_db(video_db, "Directory", video_dir)
                for i in epn_arr_tmp:
                    epn_name = i[0]+'	'+i[1]
                    logger.debug(epn_name)
                    epn_arr.append(epn_name)
        elif video_dir:
            new_name_with_info = video_dir.strip()
            extra_info = ''
            if '	' in new_name_with_info:
                name_title = new_name_with_info.split('	')[0]
                extra_info = new_name_with_info.split('	')[1]
            else:
                name_title = new_name_with_info
            
            if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                siteName = ui.get_parameters_value(s='siteName')['siteName']
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
        return epn_arr
    
    def map_episodes(self, tvdb_dict=None, epn_arr=None, name=None,
                       site=None, row=None, video_dir=None):
        epn_arr_list = epn_arr.copy()
        ep_dict = tvdb_dict.copy()
        sr_dict = {}
        ep_list = []
        sp = 0
        for key, value in ep_dict.items():
            if value and not key.startswith('0x'):
                ep_list.append(value)
            elif key.startswith('0x'):
                sp += 1
        for i, j in enumerate(ep_list):
            key = j[0] - sp + 1
            sr_dict.update({key:j})
        if site.lower() == 'video':
            dest_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
        else:
            dest_dir = os.path.join(home, "thumbnails", name)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        new_arr = []
        for i, val in enumerate(epn_arr_list):
            if '\t' in val:
                name_val, extra = val.split('\t', 1)
            else:
                name_val = val
                extra = ''
            watched = False
            if name_val.startswith('#'):
                name_val = name_val.replace('#', '', 1)
                watched = True
            lower_case = name_val.lower()
            key_found = False
            ep_val = None
            ep_patn = self.find_episode_key_val(lower_case, index=i)
            print(ep_patn, lower_case)
            if ep_patn:
                e = -1
                if ep_patn.startswith('s') or ep_patn.startswith('e'):
                    if ep_patn.startswith('s'):
                        ep_patn = ep_patn[1:]
                    s, e = ep_patn.split('e')
                    if s:
                        s = int(s)
                    else:
                        s = 1
                    e = int(e)
                    ep_patn = str(s) + 'x' + str(e)
                print(ep_patn, 'final...')
                ep_val = ep_dict.get(ep_patn)
                if not ep_val and e != -1:
                    ep_val = sr_dict.get(e)
                if ep_val:
                    key_found = True
            if key_found:
                if ep_val[3] is None:
                    ep_val[3] = "None"
                new_name = ep_val[1]+ ' ' + ep_val[3].replace('/', ' - ')
                summary = 'Air Date: {}\n\n{}: {}\n\n{}'.format(ep_val[-3], ep_val[1], ep_val[3], ep_val[-1])
                img_url = ep_val[-2]
                if extra:
                    new_val = new_name + '\t' + extra
                else:
                    new_val = new_name+ '\t' + name_val
                if watched:
                    new_val = '#' + new_val
                if site.lower() == 'video':
                    if '\t' in extra:
                        path = extra.split('\t')[0]
                    else:
                        path = extra
                    path = path.replace('"', '')
                    thumb_name_bytes = bytes(path, 'utf-8')
                    h = hashlib.sha256(thumb_name_bytes)
                    thumb_name = h.hexdigest()
                    dest_txt = os.path.join(dest_dir, thumb_name+'.txt')
                    dest_picn = os.path.join(dest_dir, thumb_name+'.jpg')
                else:
                    dest_txt = os.path.join(dest_dir, new_name+'.txt')
                    dest_picn = os.path.join(dest_dir, new_name+'.jpg')
                write_files(dest_txt, summary, line_by_line=False)
                self.remove_extra_thumbnails(dest_picn)
                if img_url and img_url.startswith('http'):
                    ui.vnt.get(
                            img_url, wait=0.1, out=dest_picn,
                            onfinished=partial(self.finished_thumbnails, i, new_name, summary, dest_picn)
                        )
            else:
                new_val = val
            new_arr.append(new_val)
        if new_arr:
            epn_arr_list = self.epn_list = new_arr.copy()
            
        if site == "Video":
            video_db = os.path.join(ui.home_folder, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for r, val in enumerate(epn_arr_list):
                txt = val.split('	')[1]
                ep_name = val.split('	')[0]
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (ep_name, txt))
            conn.commit()
            conn.close()
            try:
                txt = None
                if row is None:
                    if video_dir:
                        txt = video_dir
                else:
                    txt = ui.original_path_name[row].split('	')[1]
                if txt in ui.video_dict:
                    del ui.video_dict[txt]
            except Exception as err:
                print(err, '--4240---')
        elif site == 'Music' or site == 'PlayLists' or site == 'NONE':
            pass
        else: 
            if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                siteName = ui.get_parameters_value(s='siteName')['siteName']
                file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            
            if os.path.exists(file_path):
                write_files(file_path, epn_arr_list, line_by_line=True)
            logger.debug('<<<<<<<{0}>>>>>>>>'.format(file_path))
    
    def finished_thumbnails(self, *args):
        ui.gui_signals.ep_changed(args[0], args[1], args[2], args[3])
        
    def remove_extra_thumbnails(self, dest):
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
                
    def find_episode_key_val(self, lower_case, index=None, season=None):
        lower_case = re.sub('\[[^\]]*\]|\([^\)]*\)', '', lower_case)
        name_srch = re.search(r's[0-9]+ep?[0-9]+|[0-9]+x[0-9]+ ', lower_case)
        name_srch_val = None
        ep_name = ''
        
        if not name_srch:
            name_srch = re.search('e(p)?(isode)?[0-9]+', lower_case)
            if not name_srch:
                name_srch = re.search('-[^"]*[0-9][0-9]+', lower_case)
                if not name_srch:
                    name_srch = re.search('[0-9][0-9]+', lower_case)
                    if not name_srch:
                        if isinstance(index, int):
                            oped = re.search('op[0-9]*|ed[0-9]*', lower_case)
                            if not oped:
                                name_srch_val = 'ep'+str(index+1)
                    else:
                        oped = re.search('op[0-9]*|ed[0-9]*', lower_case)
                        if not oped:
                            name_srch_val = 'ep' + name_srch.group()
                else:
                    ssn_final = ''
                    ssn_val = re.search('s[0-9]+[^"]*\-', lower_case)
                    if ssn_val:
                        ssn_str_srch = re.search('s[0-9]+', ssn_val.group())
                        if ssn_str_srch:
                            ssn_final = ssn_str_srch.group()
                    if ssn_final:
                        name_srch_val = ssn_final + 'ep'+re.sub('-[^0-9]*', '', name_srch.group())
                    else:
                        oped = re.search('op[0-9]*|ed[0-9]*', lower_case)
                        if not oped:
                            name_srch_val = 'ep' + re.sub('-[^0-9]*', '', name_srch.group())
                            print(name_srch_val, lower_case)
            else:
                name_srch_val = name_srch.group()
        else:
            name_srch_val = name_srch.group()
        sn = -1
        en = -1
        if name_srch_val:
            epval = name_srch_val.lower()
            s = re.search('s[0-9]+|[0-9]+x', epval)
            e = re.search('e[0-9]+|ep[0-9]+|x[0-9]+ ', epval)
            if not e:
                e = re.search('episode[^"]*[0-9]+|ep[^"]+[0-9]+', epval)
            
            if s:
                ss = re.search('[0-9][0-9]*', s.group())
                if ss:
                    sn = int(ss.group())
            if e:
                ee = re.search('[0-9][0-9]*', e.group())
                if ee:
                    en = int(ee.group())
            if sn >= 0 and en >=0:
                ep_name = 's'+str(sn)+'e'+str(en)
            elif sn < 0 and en >=0:
                ep_name = 'e'+str(en)
            else:
                ep_name = ''
            logger.debug('{0}::{1}'.format(ep_name, sn))
        if season:
            return (ep_name, sn)
        else:
            return ep_name
            
    def getTvdbEpnInfo(self, url, epn_arr=None, name=None,
                       site=None, row=None, thread=None, video_dir=None):
        epn_arr_list = epn_arr.copy()
        content = ccurl(url)
        soup = BeautifulSoup(content, 'lxml')
        m=[]
        link1 = soup.find('div', {'class':'section'})
        if not link1:
            return 0
        link = link1.findAll('td')
        n = []
        """ep_dict = {epn_key:[sr, name, img_url, date, ep_url]}"""
        ep_dict = {}
        special_count = 0
        ep_count = 0
        image_dict = {}
        index_count = 0
        length_link = len(link)
        for i in range(4, len(link), 4):
            j = k = l = p = epurl = ''
            jj = link[i].find('a')
            if jj:
                j = jj.text
                if 'href' in str(jj):
                    epurl = jj['href']
                    if not epurl.startswith('http'):
                        if epurl.startswith('/'):
                            epurl = 'https://thetvdb.com' + epurl
                        else:
                            epurl = 'https://thetvdb.com/' + epurl
            if i+1 < length_link:
                kk = link[i+1].find('a')
                if kk:
                    k = kk.text
                else:
                    k = ''
            if i+2 < length_link:
                l = link[i+2].text
            if i+3 < length_link:
                p = link[i+3].find('img')
            if p:
                img_lnk = link[i].find('a')['href']
                lnk = img_lnk.split('&')
                series_id = lnk[1].split('=')[-1]
                poster_id = lnk[3].split('=')[-1]
                q = "http://thetvdb.com/banners/episodes/"+series_id+'/'+poster_id+'.jpg'
            else:
                q = "NONE"
            j = j.replace(' ', '')
            if j == '1x0':
                continue
            k = k.replace('/', '-')
            k = k.replace(':', '-')
            t = j+' '+k+':'+q
            if j:
                j = j.lower().strip()
                key = None
                s = e = ''
                if 'x' in j:
                    s, e = j.split('x', 1)
                    ep_count += 1
                elif j == 'special':
                    special_count += 1
                    s = '0'
                    e = str(special_count)
                else:
                    e = j
                    ni = ''
                    if index_count < len(epn_arr_list):
                        if '\t' in epn_arr_list[index_count]:
                            ni = epn_arr_list[index_count].split('\t')[0]
                        else:
                            ni = epn_arr_list[index_count]
                        if ni.startswith('#'):
                            ni = ni.replace('#', '', 1)
                    if ni:
                        epn_value, sn = self.find_episode_key_val(
                            ni, index=index_count, season=True
                            )
                        if sn >= 0:
                            s = str(sn)
                            j = s + 'x' + j 
                    ep_count += 1
                if s and e:
                    s = s.strip()
                    e = e.strip()
                    key = 's'+s+'e'+e
                if key:
                    ep_dict.update({key:[j, k, q, l, epurl]})
                if j == 'special':
                    n.append(t)
                else:
                    m.append(t)
                    key = 'e'+str(ep_count)
                    ep_dict.update({key:[j, k, q, l, epurl]})
                index_count += 1
        for i in ep_dict:
            logger.debug('\nkey:{0} value:{1}\n'.format(i, ep_dict[i]))
        new_arr = []
        for i, val in enumerate(epn_arr_list):
            if '\t' in val:
                name_val, extra = val.split('\t', 1)
            else:
                name_val = val
                extra = ''
            watched = False
            if name_val.startswith('#'):
                name_val = name_val.replace('#', '', 1)
                watched = True
            lower_case = name_val.lower()
            key_found = False
            ep_val = None
            ep_patn = self.find_episode_key_val(lower_case, index=i)
            if ep_patn:
                ep_val = ep_dict.get(ep_patn)
                if ep_val:
                    key_found = True
            if key_found:
                new_name = ep_val[0]+ ' ' + ep_val[1]
                """image_dict={sr:[img_url, date, ep_url, local_path, site]}"""
                image_dict.update({new_name:[ep_val[2], ep_val[3], ep_val[4], extra, site]})
                if extra:
                    new_val = new_name + '\t' + extra
                else:
                    new_val = new_name+ '\t' + name_val
                if watched:
                    new_val = '#' + new_val
            else:
                new_val = val
            new_arr.append(new_val)
        if new_arr:
            epn_arr_list = self.epn_list = new_arr.copy()
            
        if site=="Video":
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for r, val in enumerate(epn_arr_list):
                txt = val.split('	')[1]
                ep_name = val.split('	')[0]
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (ep_name, txt))
            conn.commit()
            conn.close()
            try:
                txt = None
                if row is None:
                    if video_dir:
                        txt = video_dir
                else:
                    txt = ui.original_path_name[row].split('	')[1]
                if txt in ui.video_dict:
                    del ui.video_dict[txt]
            except Exception as err:
                print(err, '--4240---')
        elif site == 'Music' or site == 'PlayLists' or site == 'NONE':
            pass
        else: 
            if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                siteName = ui.get_parameters_value(s='siteName')['siteName']
                file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            
            if os.path.exists(file_path):
                write_files(file_path, epn_arr_list, line_by_line=True)
            logger.debug('<<<<<<<{0}>>>>>>>>'.format(file_path))
        if thread is None:
            ui.update_list2(epn_arr=epn_arr_list)
        
        if thread:
            thread.image_dict_list = image_dict.copy()
            if site.lower() == 'video':
                thread.dest_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
            else:
                thread.dest_dir = os.path.join(home, "thumbnails", name)
            thread.site = site
        else:
            if site.lower() == 'video':
                dest_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
            else:
                dest_dir = os.path.join(home, "thumbnails", name)
        
        if thread is None:        
            update_image_list_method(image_dict, dest_dir, site)


class DownloadInfoThread(QtCore.QThread):
    
    mysignal = pyqtSignal(list)
    imagesignal = pyqtSignal(dict, str, str)
    
    def __init__(self, ui_widget, meta, mode, row, epn_arr):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        self.ui = ui_widget
        self.meta = meta
        self.mode = mode
        self.row = row
        self.image_dict_list = {}
        self.dest_dir = ''
        self.site = ''
        self.epn_arr = ''
        self.local_arr = epn_arr.copy()
        self.mysignal.connect(update_playlist_widget)
        self.imagesignal.connect(update_image_list)
        
    def __del__(self):
        self.wait()                        

    def run(self):
        self.meta.find_info(self.mode, self.row, self, self.local_arr)
        self.epn_arr = self.meta.epn_list.copy()
        image_dict = self.image_dict_list.copy()
        dest_dir = self.dest_dir
        site = self.site
        self.mysignal.emit(self.epn_arr)
        self.imagesignal.emit(image_dict, dest_dir, site)
        
@pyqtSlot(list)
def update_playlist_widget(epn_arr):
    ui.update_list2(epn_arr)

def information_update():
    print('completed')

@pyqtSlot(dict, str, str)
def update_image_list(image_dict, dest_dir, site):
    if dest_dir:
        update_image_list_method(image_dict, dest_dir, site)

def update_image_list_method(image_dict, dest_dir, site):
    if site not in ['Music', 'PlayLists', 'NONE', 'MyServer']:
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
