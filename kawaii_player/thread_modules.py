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
import importlib as imp
import time
import socket
import urllib.request
import hashlib
from bs4 import BeautifulSoup
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import pyqtSlot, pyqtSignal
from player_functions import write_files, send_notification


def observe_prop(ui, logr, mp, y=0):
    print(ui, logr, mp, y)
    while True:
        x = mp.time_pos
        if x is None:
            print(x)
            #ui.slider.setValue(y)
        else:
            pass
            #ui.slider.setValue(int(y))
        time.sleep(0.5)
        y += 1
        print(y, ui, logr, mp, ui.progress_counter)
        #ui.slider.setValue(int(y))


class Observe(QtCore.QThread):
    gotlink = pyqtSignal(float)
    def __init__(self, ui_widget, logr):
        QtCore.QThread.__init__(self)
        global ui, logger
        

    def __del__(self):
        self.wait()                        

    def run(self):
        while True:
            
            time.sleep(0.5)
            
@pyqtSlot(float)
def start_player_directly_observe(time_pos):
    global ui
    print(time_pos)
    #ui.tab_5.paintGL()
    ui.tab_5.update()
    ui.slider.setValue(int(time_pos))
    ui.tab_5.update()
    #ui.slider.valueChanged(int(time_pos))

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
            final_url = ui.yt.get_yt_url(self.url, self.quality, self.path,
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

class GetSubThread(QtCore.QThread):

    sub_signal = pyqtSignal(str)
    
    def __init__(self, ui_widget, url, wait_time=None):
        QtCore.QThread.__init__(self)
        global ui
        ui = ui_widget
        self.url = url
        self.sub_signal.connect(load_external_sub_signal)
        if wait_time:
            if isinstance(wait_time, int):
                self.wait_time = wait_time
            else:
                self.wait_time = 0
        else:
            self.wait_time = 2
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        sub_name_bytes = bytes(self.url, 'utf-8')
        h = hashlib.sha256(sub_name_bytes)
        sub_name = h.hexdigest()
        sub_name_path = os.path.join(ui.yt_sub_folder, sub_name)
        try:
            req = urllib.request.Request(self.url)
            response = urllib.request.urlopen(req)
            content = response.read().decode('utf-8')
            content_type = response.info()['content-type']
            if 'text/ass' in content_type:
                ext = '.ass'
            elif 'text/srt' in content_type:
                ext = '.srt'
            else:
                ext = '.vtt'
            subtitle_path = sub_name_path + ext
            write_files(subtitle_path, content, line_by_line=False)
        except Exception as err:
            ui.logger.error(err)
            ext = '.vtt'
            subtitle_path = sub_name_path + ext
            content = ui.vnt_sync.get(self.url, out=subtitle_path)
        if os.name == 'nt':
            subtitle_path = 'file:///' + subtitle_path.replace('\\', '/')
        time.sleep(self.wait_time)
        if ui.player_val.lower() == 'mplayer':
            command = 'sub_load "{}"'.format(subtitle_path)
        else:
            command = 'sub-add "{}" select'.format(subtitle_path)
        self.sub_signal.emit(command)


@pyqtSlot(str)
def load_external_sub_signal(command):
    global ui
    ui.mpv_execute_command(command, ui.cur_row)

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
                            module = imp.import_module(self.site, plugin_path)
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
            if hasattr(self, "final"):
                self.final = self.final.replace('"', "")
            if hasattr(self, "mode"):
                logger.debug('type={}, mode={}'.format(self.epn_type, self.mode))
            if self.epn_type == 'yt':
                finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                            logger, mode='a+v')
            elif self.epn_type == 'yt_music':
                finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                            logger, mode='music')
            elif self.epn_type == 'yt_prefetch_av':
                if ui.use_single_network_stream:
                    ytmode = 'offline'
                else:
                    ytmode = 'a+v'
                if self.final.startswith("http"):
                    finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                                logger, mode=ytmode)
                else:
                    finalUrl = self.final
            elif self.epn_type == 'yt_prefetch_a':
                if self.final.startswith("http"):
                    finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                                logger, mode='music')
                else:
                    finalUrl = self.final
            elif self.epn_type == 'yt_title':
                finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                            logger, mode='TITLE')
            elif self.epn_type == 'yt+title':
                finalUrl = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
                                            logger, mode='a+v')
                
                self.get_epn_signal.emit(finalUrl, '-1')
                title = ui.yt.get_yt_url(self.final, self.quality, self.yt_path,
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
                logger.debug(finalUrl)
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
                    if ui.player_val == "libmpv":
                        logger.debug(finalUrl)
                        ui.tab_5.prefetch_url = (finalUrl, self.row, self.epn_type)
                    else:
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
    if ui.list1.currentItem():
        pls_name = ui.list1.currentItem().text()
    else:
        pls_name = 'TMP_PLAYLIST'
    file_name = os.path.join(ui.home_folder, 'Playlists', pls_name)
    if not os.path.exists(file_name):
        pls_name = 'TMP_PLAYLIST'
        file_name = os.path.join(ui.home_folder, 'Playlists', pls_name)
        if not os.path.exists(file_name):
            f = open(file_name, 'w').close()
    write_files(file_name, file_entry, True)
    list_item = ui.list1.findItems(pls_name, QtCore.Qt.MatchFlag.MatchExactly)
    item = None
    if len(list_item) > 0:
        for i in list_item:
            row = ui.list1.row(i)
            ui.list1.setFocus()
            ui.list1.setCurrentRow(row)
            item = ui.list1.item(row)
    else:
        item = ui.list1.item(0)
    if item:
        ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)

class ThreadingThumbnail(QtCore.QThread):

    def __init__(self, ui_widget, logr, path, picn, inter, size):
        QtCore.QThread.__init__(self)
        global ui, logger
        ui = ui_widget
        logger = logr
        self.path = path
        self.picn = picn
        self.inter = inter
        self.interval = 1
        self.size = size

    def __del__(self):
        self.wait()                        

    def run(self):
        logger.info(self.path)
        if not os.path.exists(self.picn) and self.path:
            try:
                if (self.path.startswith('http') and 
                        (self.path.endswith('.jpg') or self.path.endswith('.png')
                         or self.path.endswith('.image'))):
                    ui.vnt_sync.get(self.path, out=self.picn)
                    ui.image_fit_option(self.picn, self.picn, fit_size=6, widget=ui.label)
                else:
                    ui.generate_thumbnail_method(self.picn, self.inter, self.path, width_allowed=self.size)
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
            if ui.view_mode == "thumbnail_light":
                size = 256
            else:
                size = 128
            icon_new_pixel = ui.create_new_image_pixel(icon_name, size)
            if os.path.exists(icon_new_pixel):
                scaled_pixel = ui.scaled_icon(icon_new_pixel, size)
                ui.list2.item(k).setIcon(QtGui.QIcon(scaled_pixel))
                if ui.view_mode == "thumbnail_light" and ui.list_poster.title_clicked:
                    ui.list_poster.item(k).setIcon(QtGui.QIcon(scaled_pixel))
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
        msg = 'this is kawaii-player At: port={} https={} pc_to_pc_casting={} msg={}'.format(
            port, ui.https_media_server, ui.pc_to_pc_casting, ui.broadcast_message)
        msg = bytes(msg , 'utf-8')
        if ui.https_media_server:
            https_val = 'https'
        else:
            https_val = 'http'
        subnet_mask = ui.local_ip_stream.rsplit('.', 1)[0] + '.255'
        notify_msg = '{0}://{1}:{2}, Role={3} started broadcasting. Now Clients can Discover it'.format(
            https_val, ui.local_ip_stream, ui.local_port_stream, ui.pc_to_pc_casting)
        send_notification(notify_msg)
        print(subnet_mask)
        while ui.broadcast_server:
            try:
                s.sendto(msg, (subnet_mask,12345))
            except Exception as err:
                print(err)
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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 12345))

        s.settimeout(60)
        port_val = ''
        https_val = ''
        msg_val = ''
        if ui.discover_slaves:
            notifymsg = ('Started Process of Discovering. Make sure that\
                          Slave is broadcasting itself')
        else:
            notifymsg = 'Started Process of Discovering'
        notifymsg = re.sub(' +', ' ', notifymsg)
        send_notification(notifymsg)
        if ui.discover_server:
            self.clear_list.emit('start')
        while ui.discover_server or ui.discover_slaves:
            try:
                m = s.recvfrom(1024)
                val = str(m[0], 'utf-8')
                server = str(m[1][0])
                casting_mode = None
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
                        elif i.startswith('pc_to_pc_casting='):
                            casting_mode = i.split('=')[1]
                    if casting_mode == 'slave':
                        slave_address = '{}://{}:{}'.format(https_val, server, port_val)
                        slave_address_without_prefix = '{}:{}'.format(server, port_val)
                        if slave_address not in ui.pc_to_pc_casting_slave_list:
                            ui.pc_to_pc_casting_slave_list.append(slave_address)
                            if ui.auto_set_ip_address_on_start and ui.slave_address != slave_address_without_prefix:
                                ui.slave_address = '{}:{}'.format(server, port_val)
                                config_file = os.path.join(ui.home_folder, 'slave.txt')
                                with open(config_file, "w") as f:
                                    f.write(slave_address)

                                print("slave address updated to: {}".format(slave_address))

                    msg_val = re.search('msg=[^"]*', val_string).group()
                    msg_val = msg_val.replace('msg=', '', 1)
                    server_val = '{0}://{1}:{2}/\t{3}'.format(
                        https_val, server, port_val, casting_mode)
                    if server_val not in ui.broadcast_server_list and ui.discover_server:
                        ui.broadcast_server_list.append(server_val)
                        self.discover_signal.emit(server_val)
                time.sleep(1)
            except Exception as e:
                print('timeout', e)
                break
        if not ui.broadcast_server_list and ui.discover_server:
            send_notification('No Server Found')
            self.clear_list.emit('no server')
        elif not ui.pc_to_pc_casting_slave_list and ui.discover_slaves:
            send_notification('No Slave Found')
        elif ui.broadcast_server_list:
            send_notification('Stopped Discovering: found {} servers'.format(len(ui.broadcast_server_list)))
        elif ui.pc_to_pc_casting_slave_list:
            send_notification('Stopped Discovering: found {} slaves'.format(len(ui.pc_to_pc_casting_slave_list)))
            
@pyqtSlot(str)
def remember_server(val):
    ui.text.setText('Found..')
    ui.original_path_name.append(val)
    ui.list1.addItem(val)
    
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
