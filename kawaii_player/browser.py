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
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from yt import get_yt_url, get_yt_sub
from player_functions import write_files, ccurl, send_notification, wget_string
from hls_webengine.netmon import NetManager


class MyPage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self):
        super(MyPage, self).__init__()

    def acceptNavigationRequest(self, url, nav_type, frame):
        if nav_type == 0:
            print('clicked')
        return super(MyPage, self).acceptNavigationRequest(url, nav_type, frame)


class Browser(QtWebEngineWidgets.QWebEngineView):

    urlSignal = pyqtSignal(str)
    gotHtmlSignal = pyqtSignal(str, str, str)
    playlist_obtained_signal = pyqtSignal(str)
    #yt_sub_signal = pyqtSignal(str, str, str)

    def __init__(self, ui, home, screen_width, quality, site, epnArrList):
        super(Browser, self).__init__()
        self.epn_name_in_list = ''
        self.wait_player = False
        #self.action_arr = []
        #self.threadPool = []
        self.home = home
        self.ui = ui
        self.quality = quality
        self.site = site
        self.epnArrList = epnArrList
        self.pg = MyPage()
        self.setPage(self.pg)
        yt_url = False
        try:
            row = ui.list2.currentRow()
            url_name = self.epnArrList[row].split('	')[1]
            if 'youtube.com' in url_name or self.ui.review_site_code == 'yt':
                yt_url = True
        except:
            pass
        if self.ui.btnWebReviews.currentText().lower() == 'youtube' or yt_url:
            self.hdr = 'Mozilla/5.0 (Linux; Android 4.4.4; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'
        else:
            self.hdr = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'
        self.page().profile().setHttpUserAgent(self.hdr)
        p = NetManager(parent=self.pg, default_block=True)
        self.page().profile().setRequestInterceptor(p)
        #self.profile().clearHttpCache()
        cache_path = os.path.join(self.ui.tmp_download_folder, 'CacheBrowser')
        print(cache_path, '--cache--path--')
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        self.page().profile().setCachePath(cache_path)
        self.page().profile().setPersistentStoragePath(cache_path)
        self.page().linkHovered.connect(self.custom_links)
        self.urlChanged.connect(self.url_changed)
        self.hoveredLink = ''
        self.media_url = ''
        self.titleChanged.connect(self.title_changed)
        self.loadProgress.connect(self.load_progress)
        self.current_link = ''
        self.title_page = ''
        #ui.tab_2.showMaximized()
        self.ui.tab_2.setMaximumWidth(screen_width)
        self.url_arr = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.player_wait)
        self.timer.setSingleShot(True)
        self.urlSignal.connect(self.final_found)
        self.gotHtmlSignal.connect(self.got_curl_html)
        self.playlist_obtained_signal.connect(self.got_playlist_html)
        self.playlist_dict = {}
        self.get_playlist = False
        self.playlist_name = ''
        self.sub_url = ''
        self.yt_sub_folder = os.path.join(home, 'External-Subtitle')
        #self.yt_sub_signal.connect(get_yt_sub_thread)
        if not os.path.exists(self.yt_sub_folder):
            os.makedirs(self.yt_sub_folder)
        self.yt_process = QtCore.QProcess()
        self.yt_process.started.connect(self.yt_process_started)
        self.yt_process.finished.connect(self.yt_process_finished)

    @pyqtSlot(str)
    def final_found(self, final_url):
        print(final_url, 'clicked')
        if final_url:
            print(final_url, '--youtube--')
            self.ui.watchDirectly(final_url, self.epn_name_in_list, 'no')
            self.ui.tab_5.show()
            self.ui.frame1.show()
            self.ui.tab_2.setMaximumWidth(self.ui.width_allowed+50)

    @pyqtSlot(str)
    def got_playlist_html(self, final_url):
        pass

    def player_wait(self):
        self.wait_player = False
        self.page().runJavaScript("location.reload();", self.var_remove)

    def get_html(self, var):
        print('--got--html--')
        if 'youtube.com' in self.url().url():
            self.sub_url = ''
            self.playlist_dict = {}
            soup = BeautifulSoup(var, 'lxml')
            m = soup.find('div', {'id':'player'})

            if m:
                print('removing')
                self.page().runJavaScript(
                    "var element = document.getElementById('player');element.innerHtml='';",
                    self.var_remove)
            title = soup.find('title')
            if title:
                if (self.current_link.startswith("https://m.youtube.com/watch?v=") 
                        or self.current_link.startswith("https://www.youtube.com/watch?v=")):
                    self.epn_name_in_list = title.text
                    self.ui.epn_name_in_list = title.text

            if 'list=' in self.url().url() and 'www.youtube.com' in self.url().url():
                ut_c = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit currently-playing"})
                ut = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit "})
                if ut_c:
                    ut = ut_c + ut
                print(ut)
                arr = []
                for i in ut:
                    try:
                        j1 = i['data-video-id']+'#'+i['data-video-title']
                        print(j1)
                        j = i['data-video-id']
                        k = i['data-video-title']
                        l = (j, k)
                        arr.append(l)
                    except:
                        pass
                d = dict(arr)
                print(d)
                print(arr)
                if d:
                    self.playlist_dict = d
            elif 'list=' in self.url().url():
                o = soup.find('div', {'id':'content-container'})
                m = o.findAll('img')
                n = []
                d = {}
                for i in m:
                    try:
                        g = i.find_next('h4')
                        yt_id = i['src'].split('/')[-2]
                        n.append((yt_id, g.text))
                    except:
                        pass
                if n:
                    d = dict(n)
                print(d)
                if d:
                    self.playlist_dict = d

    def var_remove(self, var):
        print(var, '--js--')

    def load_progress(self, var):
        if var == 100 and 'youtube.com' in self.url().url():
            self.page().toHtml(self.get_html)
            try:
                if 'youtube.com/watch?v=' in self.url().toString():
                    self.ui.progressEpn.setValue(0)
                    self.ui.progressEpn.setFormat(('Wait...'))
            except Exception as err:
                print(err, '--222--')

    def title_changed(self, title):
        pass

    def url_changed(self, link):
        if not self.url_arr:
            self.url_arr.append(link.url())
            prev_url = ''
        else:
            prev_url = self.url_arr[-1]
            self.url_arr.append(link.url())

        if prev_url != link.url() and 'youtube.com' in link.url():
            self.current_link = link.url()
            m = []
            if '/watch?' in link.url():
                a = link.url().split('?')[-1]
                b = a.split('&')
                if b:
                    for i in b:
                        j = i.split('=')
                        k = (j[0], j[1])
                        m.append(k)
                else:
                    j = a.split('=')
                    k = (j[0], j[1])
                    m.append(k)
                d = dict(m)
                print(d, '----dict--arguments---generated---')
                try:
                    self.current_link = 'https://m.youtube.com/watch?v='+d['v']
                except:
                    pass
            if ((self.current_link.startswith("https://m.youtube.com/watch?v=") 
                    or self.current_link.startswith("https://www.youtube.com/watch?v=")) 
                    and not self.wait_player):
                self.wait_player = True
                self.clicked_link(self.current_link)
                self.timer.start(1000)

    def yt_process_started(self):
        print('yt_process_started')

    def yt_process_finished(self):
        print('yt_process_started')

    def clicked_link(self, link):
        final_url = ''
        url = link
        self.epn_name_in_list = self.title()
        self.ui.logger.info('--clicked--link: {0}--{1}'.format(url, self.epn_name_in_list))
        if 'youtube.com/watch?v=' in url:
            if self.ui.mpvplayer_val.processId() > 0:
                self.ui.mpvplayer_val.kill()
                self.ui.mpvplayer_started = False
            self.ui.get_final_link(
                url, self.ui.quality_val, self.ui.ytdl_path, self.ui.logger, 
                '', self.hdr)

    def custom_links(self, q_url):
        url = q_url
        self.hoveredLink = url

    def urlHeaders(self, url):
        m = []
        o = []
        content = ccurl(url, curl_opt='-I')
        n = content.split('\n')
        #print(n)
        k = 0
        for i in n:
            i = re.sub('\r', '', i)
            if i and ':' in i:
                p = i.split(': ', 1)
                if p:
                    t = (p[0], p[1])
                else:
                    t = (i, "None")
                m.append(t)
                #print(m, '-----')
                k = k+1
                #print(k)
            else:
                t = (i, '')
                m.append(t)
        d = dict(m)
        print(d)
        return d

    @pyqtSlot(str, str, str)
    def got_curl_html(self, title, url, file_path):
        t = title + '	'+url+'	'+'NONE'
        write_files(file_path, t, line_by_line=True)
        self.ui.update_playlist(file_path)

    def add_playlist(self, value):
        value = value.replace('/', '-')
        value = value.replace('#', '')
        if value.startswith('.'):
            value = value[1:]
        file_path = os.path.join(self.home, 'Playlists', str(value))
        new_pl = False
        j = 0
        new_arr = []
        for i in self.playlist_dict:
            yt_id = i
            title = self.playlist_dict[yt_id]
            title = title.replace('/', '-')
            title = title.replace('#', '')
            if title.startswith('.'):
                title = title[1:]
            if os.name != 'posix':
                title = title.replace(':', '-')
                title = title.replace('|', '-')
            n_url = 'https://m.youtube.com/watch?v='+yt_id
            w = title+'	'+n_url+'	'+'NONE'
            new_arr.append(w)
            j = j+1
        write_files(file_path, new_arr, line_by_line=True)
        self.get_playlist = False

    def triggerPlaylist(self, value, url, title):
        print('Menu Clicked')
        print(value)
        file_path = os.path.join(self.home, 'Playlists', str(value))
        if '/' in title:
            title = title.replace('/', '-')
        if '#' in title:
            title = title.replace('#', '')
        if title.startswith('.'):
            title = title[1:]
        if os.name != 'posix':
            title = title.replace(':', '-')
            title = title.replace('|', '-')
        #print(title, url, file_path)
        if 'list=' in url:
            title = title + '-Playlist'
        img_u = ''
        if self.media_url:
            if 'ytimg.com' in self.media_url:
                img_u = self.media_url 
        if 'playlist?list=' in url and img_u:
            yt_id = img_u.split('/')[-2]
            o_url = r'https://m.youtube.com/playlist?list='
            n_url = 'https://m.youtube.com/watch?v='+yt_id+'&index=1&list='
            url = url.replace(o_url, n_url)
            print(url, o_url, n_url)
        t = title + '	'+url+'	'+'NONE'

        write_files(file_path, t, line_by_line=True)
        self.ui.update_playlist(file_path)

    def contextMenuEvent(self, event):
        self.media_url = ''
        self.selected_text = ''
        menu = self.page().createStandardContextMenu()
        try:
            data = self.page().contextMenuData()
            url = data.linkUrl().url()
            self.title_page = data.linkText()
            self.selected_text = data.selectedText()
            self.ui.logger.info(self.selected_text)
            #print(data.selectedText(), '--selected-text--')
            try:
                #self.title_page = self.title_page.strip()
                tmp = self.title_page.replace('\n', '#')
                #print(tmp)
                tmp1 = tmp.split('#')[0]
                if tmp1:
                    self.title_page = tmp.split('#')[1]
                else:
                    self.title_page = tmp.split('#')[1]+'-'+tmp.split('#')[2]
                #tmp = re.search('[#][^#]*', tmp)
                #print(tmp)
                #self.title_page = tmp.group()
                self.title_page = self.title_page.replace('#', '')
            except:
                pass
            self.epn_name_in_list = self.title_page
            if data.mediaType() == 1:
                self.media_url = data.mediaUrl().url()
                if not self.media_url.startswith('http'):
                    self.media_url = ''
                    print('--no--image-url--')
                #print(data.mediaUrl().url(), '--media-url--image--')
        except:
            url = self.hoveredLink
            pass

        self.ui.logger.info(url)
        if not url.startswith('http'):
            url = self.media_url
            self.ui.logger.info(url)

        arr = ['Download As Fanart', 'Download As Cover', 'Copy Summary']
        arr_extra_tvdb = ['Series Link', 'Season Episode Link']
        arr_extra_tmdb = ['Series/Movie Link']
        arr_last = ['Artist Link']
        action = []
        yt = False
        if url or self.media_url:
            if url:
                if 'tvdb' in url:
                    arr = arr + arr_extra_tvdb
                elif 'themoviedb' in url:
                    arr = arr_extra_tmdb
                elif 'last.fm' in url:
                    arr = arr + arr_last
                elif 'youtube.com' in url or 'ytimg.com' in url or url.startswith('http'):
                    yt = True
                    #arr[:] = []
                    arr.append('Play with Kawaii-Player')
                    arr.append('Queue Item')
                    arr.append('Download')
                    arr.append('Get Subtitle (If Available)')
                    if 'ytimg.com' in url:
                        #print(self.playlist_dict)
                        yt_id = url.split('/')[-2]
                        url = 'https://m.youtube.com/watch?v='+yt_id
                        print('url=', url)
                        try:
                            self.title_page = self.playlist_dict[yt_id]
                        except:
                            self.title_page = ''
                        #print('url=', url, 'Title=', self.title_page)
                        self.epn_name_in_list = self.title_page
                        arr.append('Add as Local Playlist')
                        self.playlist_name = self.epn_name_in_list

                    menu.addSeparator()
                    submenuR = QtWidgets.QMenu(menu)
                    submenuR.setTitle("Add To Playlist")
                    menu.addMenu(submenuR)
                    pls = os.listdir(os.path.join(self.home, 'Playlists'))
                    home1 = os.path.join(self.home, 'Playlists')
                    pls = sorted(pls, 
                                 key=lambda x: os.path.getmtime(os.path.join(home1, x)), 
                                 reverse=True)
                    item_m = []
                    for i in pls:
                        item_m.append(submenuR.addAction(i))
                    
                    submenuR.addSeparator()
                    new_pls = submenuR.addAction("Create New Playlist")

            for i in range(len(arr)):
                action.append(menu.addAction(arr[i]))

            act = menu.exec_(event.globalPos())

            for i in range(len(action)):
                if act == action[i]:
                    self.download(url, arr[i], copy_summary=self.selected_text)
            if yt:
                for i in range(len(item_m)):
                    if act == item_m[i]:
                        if not self.title_page:
                            content = ccurl(url)
                            soup = BeautifulSoup(content, 'lxml')
                            self.title_page = soup.title.text.strip().replace('/', '-')
                            self.epn_name_in_list = self.title_page
                        self.triggerPlaylist(pls[i], url, self.epn_name_in_list)

                if act == new_pls:
                    print("creating")
                    MainWindow = QtWidgets.QWidget()
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Playlist Name')
                    if ok and item:
                        file_path = os.path.join(self.home, 'Playlists', item)
                        if not os.path.exists(file_path):
                            f = open(file_path, 'w')
                            f.close()
            #menu.exec_(event.globalPos())
        else:
            if 'youtube.com/watch?v=' in self.url().url() or self.url().url().startswith('http'):
                self.title_page = self.title()
                arr = ['Play with Kawaii-Player', 'Download', 
                       'Get Subtitle (If Available)']
                if 'tvdb' in self.url().url():
                    arr = arr + arr_extra_tvdb
                elif 'themoviedb' in self.url().url():
                    arr = arr_extra_tmdb
                elif 'last.fm' in self.url().url():
                    arr = arr + arr_last
                elif self.selected_text:
                    arr[:] = []
                    arr.append('Copy Summary')
                action = []
                menu.addSeparator()

                submenuR = QtWidgets.QMenu(menu)
                submenuR.setTitle("Add To Playlist")
                menu.addMenu(submenuR)
                pls = os.listdir(os.path.join(self.home, 'Playlists'))
                home1 = os.path.join(self.home, 'Playlists')
                pls = sorted(pls, 
                             key=lambda x: os.path.getmtime(os.path.join(home1, x)), 
                             reverse=True)
                item_m = []
                for i in pls:
                    item_m.append(submenuR.addAction(i))

                submenuR.addSeparator()
                new_pls = submenuR.addAction("Create New Playlist")

                for i in range(len(arr)):
                    action.append(menu.addAction(arr[i]))

                act = menu.exec_(event.globalPos())

                for i in range(len(action)):
                    if act == action[i]:
                        self.download(self.url().url(), arr[i])

                for i in range(len(item_m)):
                    if act == item_m[i]:
                        self.triggerPlaylist(pls[i], self.url().url(), 
                                             self.title_page)

                if act == new_pls:
                    print("creating")
                    MainWindow = QtWidgets.QWidget()
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Playlist Name')
                    if ok and item:
                        file_path = os.path.join(self.home, 'Playlists', item)
                        if not os.path.exists(file_path):
                            f = open(file_path, 'w')
                            f.close()
            elif('tvdb' in self.url().url() or 'last.fm' in self.url().url() 
                    or 'themoviedb' in self.url().url() or self.selected_text):
                self.ui.logger.info(self.url().url())
                if 'tvdb' in self.url().url():
                    arr = arr + arr_extra_tvdb
                elif 'themoviedb' in self.url().url():
                    arr = arr_extra_tmdb
                elif 'last.fm' in self.url().url():
                    arr = arr + arr_last
                elif self.selected_text:
                    arr[:] = []
                    arr.append('Copy Summary')
                for i in range(len(arr)):
                    action.append(menu.addAction(arr[i]))

                act = menu.exec_(event.globalPos())

                for i in range(len(action)):
                    if act == action[i]:
                        self.download(self.url().url(), arr[i], 
                                      copy_summary=self.selected_text)
            else:
                super(Browser, self).contextMenuEvent(event)
                
    def download(self, url, option, copy_summary=None):
        if option.lower() == 'play with kawaii-player':
            final_url = ''
            self.ui.epn_name_in_list = self.title_page
            self.ui.logger.info(self.ui.epn_name_in_list)
            if self.ui.mpvplayer_val.processId() > 0:
                self.ui.mpvplayer_val.kill()
                self.ui.mpvplayer_started = False
            if 'youtube.com' in url or 'ytimg.com' in url:
                pass
            else:
                url = 'ytdl:'+url
            self.ui.get_final_link(
                url, self.ui.quality_val, self.ui.ytdl_path, self.ui.logger, 
                self.ui.epn_name_in_list, self.hdr)
        elif option.lower() == 'add as local playlist':
            self.get_playlist = True
            if self.playlist_dict:
                self.ui.logger.info(self.get_playlist, '=get_playlist')
                self.add_playlist(self.playlist_name)
        elif option.lower() == 'download':
            if self.ui.quality_val == 'sd480p':
                txt = "Video can't be saved in 480p, Saving in either HD or SD"
                send_notification(txt)
                quality = 'hd'
            else:
                quality = self.ui.quality_val
            finalUrl = get_yt_url(url, quality, self.ui.ytdl_path, self.ui.logger, mode='offline')
            finalUrl = finalUrl.replace('\n', '')
            title = self.title_page+'.mp4'
            title = title.replace('"', '')
            title = title.replace('/', '-')
            if os.path.exists(self.ui.default_download_location):
                title = os.path.join(self.ui.default_download_location, title)
            else:
                title = os.path.join(self.ui.tmp_download_folder, title)
            command = wget_string(finalUrl, title, self.ui.get_fetch_library)
            print(command)	
            self.ui.infoWget(command, 0)
        elif option.lower() == 'get subtitle (if available)':
            self.ui.epn_name_in_list = self.title_page
            self.ui.logger.info(self.ui.epn_name_in_list)
            get_yt_sub(
                url, self.ui.epn_name_in_list, self.yt_sub_folder, 
                self.ui.tmp_download_folder, self.ui.ytdl_path, self.ui.logger)
        elif option.lower() == 'queue item':
            file_path = os.path.join(self.home, 'Playlists', 'Queue')
            if not os.path.exists(file_path):
                f = open(file_path, 'w')
                f.close()
            if not self.ui.queue_url_list:
                self.ui.list6.clear()
            title = self.title_page.replace('/', '-')
            if title.startswith('.'):
                title = title[1:]
            r = title + '	'+url+'	'+'NONE'
            self.ui.queue_url_list.append(r)
            self.ui.list6.addItem(title)
            print(self.ui.queue_url_list)
            write_files(file_path, r, line_by_line=True)
        elif option.lower() == 'season episode link':
            if self.site != "Music" and self.site != "PlayLists":
                my_copy = self.ui.epn_arr_list.copy()
                r = self.ui.list1.currentRow()
                nm = self.ui.get_title_name(r)
                self.ui.metaengine.getTvdbEpnInfo(url, site=self.site,
                                       epn_arr=my_copy, name=nm, row=r)
        elif (option.lower() == 'artist link' or option.lower() == 'series link' 
                or option.lower() == 'series/movie link'):
            r = self.ui.list1.currentRow()
            nm = self.ui.get_title_name(r)
            self.ui.posterfound_new(
                name=nm, site=self.site, url=url, direct_url=True, 
                copy_summary=True, copy_poster=True, copy_fanart=True)
        elif option.lower() == 'copy summary':
            self.ui.copySummary(copy_sum=copy_summary)
        else:
            if not url:
                url = self.media_url
            print(url, self.media_url, '--media--url--')
            if url:
                t_content = ccurl(url, curl_opt='-I')
                if 'image/jpeg' in t_content and not 'Location:' in t_content:
                    pass
                elif 'image/jpeg' in t_content and 'Location:' in t_content:
                    m = re.findall('Location: [^\n]*', t_content)
                    found = re.sub('Location: |\r', '', m[0])
                    url = found
                elif self.media_url:
                    url = self.media_url
                else:
                    return 0

                if option.lower() == "download as fanart":
                    r = self.ui.list1.currentRow()
                    nm = self.ui.get_title_name(r)
                    print(option, '----')
                    self.ui.posterfound_new(
                        name=nm, site=self.site, url=url, direct_url=True, 
                        copy_summary=False, copy_poster=False, copy_fanart=True)
                elif option.lower() == "download as cover":
                    r = self.ui.list1.currentRow()
                    nm = self.ui.get_title_name(r)
                    self.ui.posterfound_new(
                        name=nm, site=self.site, url=url, direct_url=True, 
                        copy_summary=False, copy_poster=True, copy_fanart=False)
