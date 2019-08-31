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

import re
import os
import urllib.parse
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtWebKitWidgets
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import ccurl, send_notification, write_files, wget_string
from hls_webkit.netmon_webkit import NetManager


class BrowserPage(QWebPage):
      
    def __init__(self):
        super(BrowserPage, self).__init__()

    def acceptNavigationRequest(self, frame, req, nav_type):
        return super(BrowserPage, self).acceptNavigationRequest(frame, req, nav_type)

    def userAgentForUrl(self, url):
        if 'youtube' in url.toString():
            return 'Mozilla/5.0 (Linux; Android 4.4.4; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'
        else:
            return 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:63.0) Gecko/20100101 Firefox/63.0'


class Browser(QtWebKitWidgets.QWebView):

    gotHtmlSignal = pyqtSignal(str, str, str)

    def __init__(self, ui, home, screen_width, quality, site, epnArrList):
        super(Browser, self).__init__()
        self.ui = ui
        self.web = BrowserPage()
        self.web.settings().setAttribute(QWebSettings.LocalStorageEnabled, True)
        cache_path = os.path.join(self.ui.tmp_download_folder, 'CacheBrowser')
        self.web.settings().enablePersistentStorage(cache_path)
        self.setPage(self.web)
        self.nam = NetManager(default_block=True)
        self.web.setNetworkAccessManager(self.nam)
        self.hdr = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:63.0) Gecko/20100101 Firefox/63.0'
        self.img_url = ''
        self.quality = quality
        self.site = site
        self.home = home
        self.epnArrList = epnArrList
        self.wait_player = False
        self.urlChanged.connect(self.url_changed)
        self.hoveredLink = ''
        self.media_url = ''
        self.epn_name_in_list = ''
        self.titleChanged.connect(self.title_changed)
        self.loadProgress.connect(self.load_progress)
        self.current_link = ''
        self.title_page = ''
        self.ui.tab_2.setMaximumWidth(screen_width)
        self.url_arr = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.player_wait)
        self.timer.setSingleShot(True)
        self.hit_link = ''
        self.playlist_dict = {}
        self.get_playlist = False
        self.playlist_name = ''
        self.gotHtmlSignal.connect(self.got_curl_html)
        self.yt_sub_folder = os.path.join(home, 'External-Subtitle')
        if not os.path.exists(self.yt_sub_folder):
            os.makedirs(self.yt_sub_folder)

    def link_clicked(self, link):
        self.current_link = link.toString()
        m = []
        if '/watch?' in link.toString():
            a = link.toString().split('?')[-1]
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
            try:
                self.current_link = 'https://m.youtube.com/watch?v='+d['v']
            except Exception as err:
                self.ui.logger.error(err)
        if ((self.current_link.startswith("https://m.youtube.com/watch?v=") 
                or self.current_link.startswith("https://www.youtube.com/watch?v=")) 
                and not self.wait_player):
            self.page().mainFrame().evaluateJavaScript(
                "var element = document.getElementById('player');element.parentNode.removeChild(element);")
            self.wait_player = True
            self.clicked_link(self.current_link)
            self.timer.start(1000)

    def player_wait(self):
        self.wait_player = False
        self.page().mainFrame().evaluateJavaScript("location.reload();")

    def get_html(self, var):
        if 'youtube.com' in self.url().toString():
            self.playlist_dict = {}
            x = urllib.parse.unquote(var)
            x = x.replace('\\\\u0026', '&')
            l = re.findall('url=https[^"]*', x)
            for i in l:
                if self.ui.quality_val == 'sd': 
                    if 'itag=18' in i:
                        final_url = re.sub('url=', '', i)
            soup = BeautifulSoup(var, 'lxml')
            m = soup.find('div', {'id':'player'})
            if m:
                print('removing')
                self.page().mainFrame().evaluateJavaScript(
                    "var element = document.getElementById('player');element.innerHtml='';")
            title = soup.find('title')
            if title:
                if (self.current_link.startswith("https://m.youtube.com/watch?v=") 
                        or self.current_link.startswith("https://www.youtube.com/watch?v=")):
                    self.epn_name_in_list = title.text
                    self.ui.epn_name_in_list = title.text
                    print(title.text, self.url().toString(), '--changed-title--')

            if ('list=' in self.url().toString() 
                    and 'www.youtube.com' in self.url().toString()):
                ut_c = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit currently-playing"})
                ut = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit "})
                if ut_c:
                    ut = ut_c + ut
                arr = []
                for i in ut:
                    try:
                        j1 = i['data-video-id']+'#'+i['data-video-title']
                        j = i['data-video-id']
                        k = i['data-video-title']
                        l = (j, k)
                        arr.append(l)
                    except Exception as err:
                        self.ui.logger.error(err)
                d = dict(arr)
                if d:
                    self.playlist_dict = d
            elif 'list=' in self.url().toString():
                o = soup.find('div', {'id':'content-container'})
                if  o:
                    m = o.findAll('img')
                else:
                    m = []
                n = []
                d = {}
                for i in m:
                    try:
                        g = i.find_next('h4')
                        yt_id = i['src'].split('/')[-2]
                        n.append((yt_id, g.text))
                    except Exception as err:
                        self.ui.logger.error(err)
                if n:
                    d = dict(n)
                if d:
                    self.playlist_dict = d

    def load_progress(self, var):
        if var == 100 and 'youtube.com' in self.url().toString():
            frame = self.page().mainFrame().toHtml()
            self.get_html(frame)
            try:
                if 'youtube.com/watch?v=' in self.url().toString():
                    self.ui.progressEpn.setValue(0)
                    self.ui.progressEpn.setFormat(('Wait...'))
            except Exception as err:
                self.ui.logger.error(err)

    def title_changed(self, title):
        self.ui.epn_name_in_list = title

    def url_changed(self, link):
        if not self.url_arr:
            self.url_arr.append(link.url())
            prev_url = ''
        else:
            prev_url = self.url_arr[-1]
            self.url_arr.append(link.url())
            
        if prev_url != link.url() and 'youtube' in link.url():
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
                try:
                    self.current_link = 'https://m.youtube.com/watch?v='+d['v']
                except Exception as err:
                    self.ui.logger.error(err)
            if ((self.current_link.startswith("https://m.youtube.com/watch?v=") 
                    or self.current_link.startswith("https://www.youtube.com/watch?v=")) 
                    and not self.wait_player):
                self.wait_player = True
                self.clicked_link(self.current_link)
                self.timer.start(1000)

    def clicked_link(self, link):
        final_url = ''
        url = link
        self.epn_name_in_list = self.title()
        if 'youtube.com/watch?v=' in url:
            if self.ui.mpvplayer_val.processId() > 0:
                self.ui.mpvplayer_val.kill()
                self.ui.mpvplayer_started = False
            self.ui.get_final_link(
                url, self.ui.quality_val, self.ui.ytdl_path, self.ui.logger, 
                '', self.hdr
                )

    def custom_links(self, q_url):
        url = q_url
        self.hoveredLink = url

    def keyPressEvent(self, event):
        if event.modifiers() == QtCore.Qt.AltModifier and event.key() == QtCore.Qt.Key_Left:
            self.back()
        elif event.modifiers() == QtCore.Qt.AltModifier and event.key() == QtCore.Qt.Key_Right:
            self.forward()
        else:
            super(Browser, self).keyPressEvent(event)

    @pyqtSlot(str, str, str)
    def got_curl_html(self, title, url, value):
        file_path = os.path.join(self.home, 'Playlists', str(value))
        if '/' in title:
            title = title.replace('/', '-')
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
            n_url = 'https://m.youtube.com/watch?v='+yt_id
            w = title+'	'+n_url+'	'+'NONE'
            new_arr.append(w)
            j = j+1
        write_files(file_path, new_arr, line_by_line=True)
        self.get_playlist = False

    def triggerPlaylist(self, value, url, title):
        self.ui.logger.debug(value)
        file_path = os.path.join(self.home, 'Playlists', str(value))
        if 'ytimg.com' in url:
            try:
                print(self.playlist_dict)
                yt_id = url.split('/')[-2]
                url = 'https://m.youtube.com/watch?v='+yt_id
                title = self.playlist_dict[yt_id]
            except Exception as err:
                self.ui.logger.error(err)
        if '/' in title:
            title = title.replace('/', '-')
        if '#' in title:
            title = title.replace('#', '')
        if title.startswith('.'):
            title = title[1:]
        if 'list=' in url:
            title = title + '-Playlist'
        title = title.replace('\\', ' - ')
        img_u = ''
        if self.img_url:
            img_u = self.img_url.toString() 
        if 'playlist?list=' in url and img_u:
            try:
                yt_id = img_u.split('/')[-2]
                o_url = r'https://m.youtube.com/playlist?list='
                n_url = 'https://m.youtube.com/watch?v='+yt_id+'&index=1&list='
                url = url.replace(o_url, n_url)
                print(url, o_url, n_url)
            except Exception as err:
                self.ui.logger.error(err)
        self.ui.logger.debug('{}-{}-{}'.format(title, url, file_path))
        t = title + '	'+url+'	'+'NONE'
        write_files(file_path, t, line_by_line=True)
        #self.ui.update_playlist(file_path)

    def contextMenuEvent(self, event):
        self.img_url = ''
        menu = self.page().createStandardContextMenu()
        hit = self.page().currentFrame().hitTestContent(event.pos())
        hit_m = self.page().mainFrame()
        hit_n = hit_m.hitTestContent(event.pos())
        url = hit.linkUrl()
        arr = ['Download As Fanart', 'Download As Cover']
        arr_extra_tvdb = ['Series Link', 'Season Episode Link']
        arr_extra_tmdb = ['Series/Movie Link']
        arr_last = ['Artist Link']
        action = []
        self.img_url = hit.imageUrl()
        self.title_page = hit.linkText()
        yt = False
        title_found = False
        self.ui.logger.info('elm: {}; text:{};'.format(hit.element(), hit.element().toPlainText()))
        try:
            if self.title_page:
                if 'youtube.com' in self.url().toString(): 
                    self.title_page = hit_n.linkElement().toPlainText()
                    self.ui.logger.info(self.title_page)
                if not self.title_page:
                    self.title_page = hit.linkText()
                self.title_page = self.title_page.strip()
                self.title_page = self.title_page.replace('\n', ' - ')
                self.ui.logger.info(self.title_page)
            elif hit.element():
                self.title_page = hit.element().toPlainText()
                self.ui.logger.info(self.title_page)
                title_found = True
            else:
                self.title_page = hit.title()
        except Exception as err:
            self.ui.logger.error(err)
            self.title_page = hit.title()

        if (url.isEmpty() or not url.toString().startswith('http')) and self.img_url:
            url = self.img_url
        if url.isEmpty():
            url = self.url()
            if not title_found:
                self.title_page = hit_m.title()
            if 'reload' in self.url().toString():
                url = self.url().toString()
                n_url = re.sub('\?reload[^\/]*\/|&mode=NORMAL|&params[^&]*', '', url)
                url = QUrl(n_url)
        if not url.isEmpty() or self.img_url:
            if 'tvdb' in url.toString():
                arr = arr + arr_extra_tvdb
            elif 'themoviedb' in url.toString():
                arr = arr_extra_tmdb
            elif 'last.fm' in url.toString():
                arr = arr + arr_last
            elif 'youtube.com' in url.toString() or 'ytimg.com' in url.toString() or url.toString().startswith('http'):
                yt = True
                arr.append('Play with Kawaii-Player')
                arr.append('Queue Item')
                arr.append('Download')
                if self.ui.pc_to_pc_casting == "master":
                    arr.append("Cast This Item")
                    arr.append("Cast Queue")
                if 'ytimg.com' in url.toString():
                    yt_id = url.toString().split('/')[-2]
                    url = QUrl('https://m.youtube.com/watch?v='+yt_id)
                    try:
                        self.title_page = self.playlist_dict[yt_id]
                    except Exception as err:
                        self.ui.logger.error(err)
                        self.title_page = ''
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

            for nmenu in arr:
                action.append(menu.addAction(nmenu))

            act = menu.exec_(event.globalPos())
            for i, acts in enumerate(action):
                if act == acts:
                    self.download(url, arr[i])
            if yt:
                for i, acts in enumerate(item_m):
                    if act == acts:
                        if 'views' in self.title_page:
                            self.title_page = re.sub('[0-9][^ ]* ', '', self.title_page, 1)
                            self.title_page = re.sub('[0-9][^ ]* views', '', self.title_page, 1)
                            self.title_page = self.title_page.replace('/', '-')
                        if not self.title_page:
                            content = ccurl(url.toString())
                            soup = BeautifulSoup(content, 'lxml')
                            self.title_page = soup.title.text.strip().replace('/', '-')
                        self.triggerPlaylist(pls[i], url.toString(), self.title_page)

                if act == new_pls:
                    MainWindow = QtWidgets.QWidget()
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Playlist Name')
                    if ok and item:
                        file_path = os.path.join(self.home, 'Playlists', item)
                        if not os.path.exists(file_path):
                            f = open(file_path, 'w')
                            f.close()
        super(Browser, self).contextMenuEvent(event)

    def download(self, url, option):
        if option.lower() == 'play with kawaii-player':
            final_url = ''
            self.ui.epn_name_in_list = self.title_page
            self.ui.logger.debug(self.ui.epn_name_in_list)
            if self.ui.mpvplayer_val.processId() > 0:
                self.ui.mpvplayer_val.kill()
                self.ui.mpvplayer_started = False
            if 'youtube.com' in url.toString() or 'ytimg.com' in url.toString():
                final_url = url.toString()
            else:
                final_url = 'ytdl:'+url.toString()
            self.ui.get_final_link(
                final_url, self.ui.quality_val, self.ui.ytdl_path, self.ui.logger, 
                self.ui.epn_name_in_list, self.hdr)
        elif option.lower() in ["cast this item", "cast queue"]:
            if option.lower() == "cast queue":
                self.ui.list2.process_browser_based_url(self.title_page, url, "queue")
            else:
                self.ui.list2.process_browser_based_url(self.title_page, url, "single")
        elif option.lower() == 'add as local playlist':
            self.get_playlist = True
            if self.playlist_dict:
                self.add_playlist(self.playlist_name)
        elif option.lower() == 'download':
            if self.ui.quality_val == 'sd480p':
                txt = "Video can't be saved in 480p, Saving in either HD or SD"
                send_notification(txt)
                quality = 'hd'
            else:
                quality = self.ui.quality_val
            finalUrl = self.ui.yt.get_yt_url(url.toString(), quality,
                                             self.ui.ytdl_path, self.ui.logger,
                                             mode='offline')
            finalUrl = finalUrl.replace('\n', '')
            title = self.title_page+'.mp4'
            title = title.replace('"', '')
            title = title.replace('/', '-')
            if os.path.exists(self.ui.default_download_location):
                title = os.path.join(self.ui.default_download_location, title)
            else:
                title = os.path.join(self.ui.tmp_download_folder, title)
            command = wget_string(finalUrl, title, self.ui.get_fetch_library)
            self.ui.infoWget(command, 0)
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
            r = title + '	'+url.toString()+'	'+'NONE'
            self.ui.queue_url_list.append(r)
            self.ui.list6.addItem(title)
            write_files(file_path, r, line_by_line=True)
        elif option.lower() == 'season episode link':
            if self.site != "Music" and self.site != "PlayLists":
                my_copy = self.ui.epn_arr_list.copy()
                r = self.ui.list1.currentRow()
                nm = self.ui.get_title_name(r)
                video_dir = None
                if self.site.lower() == 'video':
                    video_dir = self.ui.original_path_name[r].split('\t')[-1]
                elif self.site.lower() in ['playlists', 'none', 'music']:
                    pass
                else:
                    video_dir = self.ui.original_path_name[r]
                self.ui.posterfound_new(
                    name=nm, site=self.site, url=url.toString(), direct_url=True, 
                    copy_summary=False, copy_poster=False, copy_fanart=False,
                    get_sum=True, video_dir=video_dir
                )
        elif (option.lower() == 'artist link' or option.lower() == 'series link' 
                or option.lower() == 'series/movie link'):
            url = url.toString()
            r = self.ui.list1.currentRow()
            nm = self.ui.get_title_name(r)
            self.ui.posterfound_new(
                name=nm, site=self.site, url=url, direct_url=True, 
                copy_summary=True, copy_poster=True, copy_fanart=True
                )
        else:
            url = url.toString()
            if url:
                t_content = ccurl(url, curl_opt='-I')
                if 'image/jpeg' in t_content and not 'Location:' in t_content:
                    pass
                elif 'image/jpeg' in t_content and 'Location:' in t_content:
                    m = re.findall('Location: [^\n]*', t_content)
                    found = re.sub('Location: |\r', '', m[0])
                    url = found
                elif not self.img_url.isEmpty():
                    url = self.img_url.toString()
                else:
                    return 0
                if '#' in url:
                    url = url.split('#')[0]
                if option.lower() == "download as fanart":
                    r = self.ui.list1.currentRow()
                    nm = self.ui.get_title_name(r)
                    self.ui.posterfound_new(
                        name=nm, site=self.site, url=url, direct_url=True, 
                        copy_summary=False, copy_poster=False, copy_fanart=True
                        )
                elif option.lower() == "download as cover":
                    r = self.ui.list1.currentRow()
                    nm = self.ui.get_title_name(r)
                    self.ui.posterfound_new(
                        name=nm, site=self.site, url=url, direct_url=True, 
                        copy_summary=False, copy_poster=True, copy_fanart=False
                        )
