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
import base64
import ssl
import ipaddress
import shutil
import time
from datetime import datetime
import uuid
import hashlib
import json
import ssl
import random
import socket
import importlib as imp
import subprocess
import urllib.parse
import urllib.request
import sqlite3
from urllib.parse import urlparse
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn, TCPServer
from bs4 import BeautifulSoup
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import send_notification, write_files, open_files
from player_functions import get_lan_ip, ccurl, naturallysorted, change_opt_file
from settings_widget import LoginAuth
from serverlib import ServerLib
from typing import Dict, Any, List, Tuple

try:
    from stream import get_torrent_download_location, torrent_session_status
except Exception as e:
    print(e)
    notify_txt = 'python3 bindings for libtorrent are broken\nTorrent Streaming feature will be disabled'
    send_notification(notify_txt, display='posix')

class DoGETSignal(QtCore.QObject):
    new_signal_gui = pyqtSignal(str)
    stop_signal_torrent = pyqtSignal(str)
    control_signal_player = pyqtSignal(int, str)
    nav_remote_player = pyqtSignal(str)
    delete_torrent_signal_remote = pyqtSignal(str)
    update_signal_db = pyqtSignal(str)
    total_navigation_signal = pyqtSignal(str, str, str, bool)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.new_signal_gui.connect(goto_ui_jump)
        self.stop_signal_torrent.connect(stop_torrent_from_client)
        self.control_signal_player.connect(start_player_remotely)
        self.nav_remote_player.connect(navigate_player_remotely)
        self.delete_torrent_signal_remote.connect(delete_torrent_history)
        self.update_signal_db.connect(update_databse_signal)
        self.total_navigation_signal.connect(total_ui_navigation)

    def total_navigation(self, st, st_o, opt, shuffle):
        self.total_navigation_signal.emit(st, st_o, opt, shuffle)

    def new_signal(self, val):
        self.new_signal_gui.emit(val)

    def stop_signal(self, val):
        self.stop_signal_torrent.emit(val)

    def control_signal(self, index, val):
        self.control_signal_player.emit(index, val)

    def nav_remote(self, val):
        self.nav_remote_player.emit(val)

    def delete_torrent_signal(self, val):
        self.delete_torrent_signal_remote.emit(val)

    def update_signal(self, val):
        self.update_signal_db.emit(val)
    
@pyqtSlot(str)
def goto_ui_jump(nm):
    global getdb
    url = getdb.epn_return_from_bookmark(nm, from_client=True)


@pyqtSlot(str)
def stop_torrent_from_client(nm):
    #ui.stop_torrent(from_client=True)
    ui.label_torrent_stop.clicked_emit()

"""
@pyqtSlot(str)
def get_my_ip_regularly(nm):
    new_thread = getIpThread(interval=ui.get_ip_interval, ip_file=ui.cloud_ip_file)
    new_thread.start()
"""

@pyqtSlot(int, str)
def start_player_remotely(nm, mode):
    global ui, MainWindow
    if mode == 'normal' and ui.list2.count():
        if nm < ui.list2.count() and nm >= 0:
            ui.cur_row = nm
        else:
            ui.cur_row = (nm%ui.list2.count())
        ui.list2.setCurrentRow(ui.cur_row)
        item = ui.list2.item(ui.cur_row)
        if item and ui.web_control == 'master':
            if ui.mpvplayer_val.processId() > 0 and ui.player_val in ["vlc", "cvlc"] and ui.playback_mode == "playlist":
                ui.mpvplayer_val.write(bytes("goto {}".format(ui.cur_row+1), "utf-8"))

            else:
                ui.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
        elif item and ui.web_control == 'slave':
            if ui.playlist_updated:
                ui.gui_signals.playlist_command('playlist', ui.cur_row)
                ui.playlist_updated = False
            else:
                ui.gui_signals.playlist_command('direct index', ui.cur_row)
    elif mode == 'queue':
        nm = nm - 1
        ui.queue_item_external = nm
        if ui.web_control == 'master':
            ui.set_queue_item_btn.clicked_emit()
        else:
            ui.gui_signals.playlist_command('queue', nm)
    elif mode == 'queue_remove':
        ui.queue_item_external_remove = nm
        ui.remove_queue_item_btn.clicked_emit()
    elif mode == 'playpause':
        if ui.web_control == 'master':
            ui.player_play_pause.clicked_emit()
        else:
            ui.settings_box.play_pause.clicked_emit()
    elif mode == 'playpause_play':
        ui.player_play_pause_play.clicked_emit()
    elif mode == 'playpause_pause':
        ui.player_play_pause_pause.clicked_emit()
    elif mode == 'show_player':
        ui.player_show_btn.clicked_emit()
    elif mode == 'hide_player':
        ui.player_hide_btn.clicked_emit()
    elif (ui.mpvplayer_val.processId() > 0 or ui.player_val in ["libmpv", "libvlc"]) or ui.web_control == 'slave':
        if mode == 'stop':
            ui.update_video_playlist_status("row")
            ui.stop_from_client = True
            if ui.web_control == 'master':
                #if MainWindow.isFullScreen():
                #    ui.player_fullscreen.clicked_emit()
                ui.player_stop.clicked_emit()
            else:
                ui.settings_box.playerstop.clicked_emit()
        elif mode == 'loop':
            if ui.web_control == 'master':
                ui.player_loop_file.clicked_emit()
            else:
                ui.settings_box.play_loop.clicked_emit()
        elif mode == 'next':
            if ui.web_control == 'master':
                if ui.player_val in ["vlc", "cvlc"] and ui.playback_mode == "playlist":
                    if ui.cur_row < ui.list2.count()-1 and ui.cur_row >= 0:
                        ui.cur_row = ui.cur_row + 1
                    else:
                        ui.cur_row = ((ui.cur_row+1)%ui.list2.count())
                    ui.list2.setCurrentRow(ui.cur_row)
                    ui.mpvplayer_val.write(bytes("next", "utf-8"))
                else:
                    ui.player_next.clicked_emit()
            else:
                if ui.cur_row < ui.list2.count()-1 and ui.cur_row >= 0:
                    ui.cur_row = ui.cur_row + 1
                else:
                    ui.cur_row = ((ui.cur_row+1)%ui.list2.count())
                ui.list2.setCurrentRow(ui.cur_row)
                ui.settings_box.playernext.clicked_emit()
        elif mode == 'prev':
            if ui.web_control == 'master':
                if ui.player_val in ["vlc", "cvlc"] and ui.playback_mode == "playlist":
                    if ui.cur_row > 0:
                        ui.cur_row = ui.cur_row - 1
                    else:
                        ui.cur_row = ui.list2.count() - 1
                    ui.list2.setCurrentRow(ui.cur_row)
                    ui.mpvplayer_val.write(bytes("prev", "utf-8"))
                else:
                    ui.player_prev.clicked_emit()
            else:
                if ui.cur_row > 0:
                    ui.cur_row = ui.cur_row - 1
                else:
                    ui.cur_row = ui.list2.count() - 1
                ui.list2.setCurrentRow(ui.cur_row)
                ui.settings_box.playerprev.clicked_emit()
        elif mode == 'seek':
            if nm == 10:
                if ui.web_control == 'master':
                    ui.player_seek_10.clicked_emit()
                else:
                    ui.settings_box.playerseek10.clicked_emit()
            elif nm == -10:
                if ui.web_control == 'master':
                    ui.player_seek_10_.clicked_emit()
                else:
                    ui.settings_box.playerseek_10.clicked_emit()
            elif nm == 60:
                if ui.web_control == 'master':
                    ui.player_seek_60.clicked_emit()
                else:
                    ui.settings_box.playerseek60.clicked_emit()
            elif nm == -60:
                if ui.web_control == 'master':
                    ui.player_seek_60_.clicked_emit()
                else:
                    ui.settings_box.playerseek_60.clicked_emit()
            elif nm == 300:
                if ui.web_control == 'master':
                    ui.player_seek_5m.clicked_emit()
                else:
                    ui.settings_box.playerseek5m.clicked_emit()
            elif nm == -300:
                if ui.web_control == 'master':
                    ui.player_seek_5m_.clicked_emit()
                else:
                    ui.settings_box.playerseek_5m.clicked_emit()
            else:
                ui.client_seek_val = nm
                if ui.web_control == 'master':
                    ui.player_seek_all.clicked_emit()
                else:
                    ui.settings_box.playerseekabs.clicked_emit()
        elif mode == 'volume':
            if nm == 5:
                if ui.web_control == 'master':
                    ui.player_vol_5.clicked_emit()
                else:
                    ui.settings_box.playervol5.clicked_emit()
            elif nm == -5:
                if ui.web_control == 'master':
                    ui.player_vol_5_.clicked_emit()
                else:
                    ui.settings_box.playervol_5.clicked_emit()
        elif mode == 'fullscreen':
            if ui.web_control == 'master':
                ui.player_fullscreen.clicked_emit()
            else:
                ui.settings_box.toggle_fs.clicked_emit()
        elif mode == 'toggle_subtitle':
            if ui.web_control == 'master':
                ui.subtitle_track.clicked_emit()
            else:
                ui.settings_box.toggle_sub.clicked_emit()
        elif mode == 'toggle_audio':
            if ui.web_control == 'master':
                ui.audio_track.clicked_emit()
            else:
                ui.settings_box.toggle_aud.clicked_emit()
        elif mode == 'add_subtitle':
            ui.add_external_subtitle.clicked_emit()

def find_and_set_index(st, st_o, srch):
    index = None
    mode = -1
    if srch.endswith('.hash'):
        srch = srch.rsplit('.', 1)[0]
    if st.lower() == 'video':
        mode = 0
    elif st.lower() == 'music':
        if st_o.lower().startswith('playlist'):
            mode = 2
        else:
            mode = 1
        
    for i, val in enumerate(ui.original_path_name):
        val = val.strip()
        if mode == 0 and '\t' in val:
            new_val = val.split('\t')[1]
        elif mode == 2:
            new_val = val
        else:
            new_val = val
        hash_val = bytes(new_val, 'utf-8')
        h = hashlib.sha256(hash_val)
        hash_dir = h.hexdigest()
        if hash_dir == srch:
            index = i
            break
    if index is not None:
        if index < ui.list1.count():
            ui.list1.setFocus()
            ui.list1.setCurrentRow(index)
            item = ui.list1.item(index)
            if item:
                ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)

@pyqtSlot(str, str, str, bool)
def total_ui_navigation(st, st_o, srch, shuffle):
    global ui
    logger.debug('\n{0}::{1}::{2}::{3}\n'.format(st, st_o, srch, shuffle))
    if shuffle:
       ui.player_btn_update_list2.clicked_emit() 
    elif st:
        if st.lower() == 'video':
            index = ui.btn1.findText('Video')
            site = 'Video'
            ui.set_parameters_value(siteval=site)
            if index >= 0 and ui.btn1.currentText().lower() != 'video':
                ui.btn1.setCurrentIndex(0)
                ui.btn1.setCurrentIndex(index)
            time.sleep(0.5)
            list3_index = 0
            if st_o.lower() != 'update' and st_o.lower() != 'updateall':
                for i in range(0, ui.list3.count()):
                    item = ui.list3.item(i)
                    txt = item.text()
                    if txt.lower() == st_o.lower():
                        if not ui.list3.currentItem():
                            ui.list3.setFocus()
                            ui.list3.setCurrentRow(0)
                        if ui.list3.currentItem().text().lower() != txt.lower():
                            ui.set_parameters_value(op=txt)
                            ui.list3.setCurrentRow(i)
                            ui.list3.itemDoubleClicked['QListWidgetItem*'].emit(item)
                            #time.sleep(0.5)
                            break
                find_and_set_index(st, st_o, srch)
        elif st.lower() == 'music':
            index = ui.btn1.findText('Music')
            site = 'Music'
            ui.set_parameters_value(siteval=site)
            if index >= 0 and ui.btn1.currentText().lower() != 'music':
                ui.btn1.setCurrentIndex(0)
                ui.btn1.setCurrentIndex(index)
            time.sleep(0.5)
            list3_index = 0
            if (st_o.lower() == 'artist' or st_o.lower() == 'album'
                    or st_o.lower() == 'directory' or st_o.lower() == 'playlist'):
                for i in range(0, ui.list3.count()):
                    item = ui.list3.item(i)
                    txt = item.text()
                    if txt.lower() == st_o.lower():
                        if not ui.list3.currentItem():
                            ui.list3.setFocus()
                            ui.list3.setCurrentRow(0)
                        if ui.list3.currentItem().text().lower() != txt.lower():
                            ui.set_parameters_value(op=txt)
                            ui.list3.setCurrentRow(i)
                            ui.list3.itemDoubleClicked['QListWidgetItem*'].emit(item)
                            time.sleep(0.5)
                            break
                find_and_set_index(st, st_o, srch)
        elif st.lower() == 'playlists':
            index = ui.btn1.findText('PlayLists')
            site = 'PlayLists'
            ui.set_parameters_value(siteval=site)
            if index >= 0 and ui.btn1.currentText().lower() != 'playlists':
                ui.btn1.setCurrentIndex(0)
                ui.btn1.setCurrentIndex(index)
            time.sleep(0.5)
            ui.list3.setFocus()
            ui.list3.setCurrentRow(0)
            item = ui.list3.item(0)
            if srch:
                list_item = ui.list1.findItems(srch, QtCore.Qt.MatchExactly)
                logger.debug('::::::::{0}'.format(srch))
                if len(list_item) > 0:
                    for i in list_item:
                        row = ui.list1.row(i)
                        ui.list1.setFocus()
                        ui.list1.setCurrentRow(row)
                        item = ui.list1.item(row)
                        logger.debug(':::::row:::{0}::::::::'.format(row))
                        if item:
                            ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)
                            ui.gui_signals.click_title_list('playlist_click_from_client')
                            time.sleep(0.5)
                            if ui.instant_cast_play in range(0, ui.list2.count()) and srch.lower() == 'tmp_playlist':
                                ui.list2.setCurrentRow(ui.instant_cast_play)
                                item = ui.list2.item(ui.instant_cast_play)
                                if item:
                                    ui.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
                                    ui.instant_cast_play = -1
        elif st.lower() == 'bookmark':
            index = ui.btn1.findText('Bookmark')
            if index >= 0 and ui.btn1.currentText().lower() != 'bookmark':
                ui.btn1.setCurrentIndex(0)
                ui.btn1.setCurrentIndex(index)
            time.sleep(0.5)
            ui.list3.setFocus()
            if st_o:
                if st_o.lower() == 'bookmark':
                    st_o = 'all'
                for i in range(0, ui.list3.count()):
                    item = ui.list3.item(i)
                    txt = item.text()
                    if txt.lower() == st_o.lower():
                        ui.list3.setCurrentRow(i)
                        time.sleep(0.5)
                        break
                logger.debug('::::::::{0}'.format(srch))
                list_item = ui.list1.findItems(srch, QtCore.Qt.MatchExactly)
                if len(list_item) > 0:
                    for i in list_item:
                        row = ui.list1.row(i)
                        ui.list1.setFocus()
                        ui.list1.setCurrentRow(row)
                        item = ui.list1.item(row)
                        logger.debug(':::::row:::{0}::::::::'.format(row))
                        if item:
                            ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)
        elif st:
            index = ui.btn1.findText('Addons')
            if index >= 0 and ui.btn1.currentText().lower() != 'addons':
                ui.btn1.setCurrentIndex(0)
                ui.btn1.setCurrentIndex(index)
            time.sleep(0.5)
            index_val = ''
            for i,j in enumerate(ui.addons_option_arr):
                if j.lower() == st.lower():
                    index_val = j
                    break
            if index_val:
                site = index_val
                ui.set_parameters_value(siteval=site)
                index = ui.btnAddon.findText(index_val)
                if index >= 0 and ui.btnAddon.currentText().lower() != site.lower():
                    ui.btnAddon.setCurrentIndex(0)
                    ui.btnAddon.setCurrentIndex(index)
                time.sleep(0.5)
                list_item = ui.list3.findItems('History', QtCore.Qt.MatchExactly)
                if not ui.list3.currentItem():
                    ui.list3.setFocus()
                    ui.list3.setCurrentRow(0)
                if len(list_item) > 0 and ui.list3.currentItem().text().lower() != 'history':
                    for i in list_item:
                        row = ui.list3.row(i)
                        ui.list3.setFocus()
                        ui.list3.setCurrentRow(row)
                        item = ui.list3.item(row)
                        if item:
                            ui.list3.itemDoubleClicked['QListWidgetItem*'].emit(item)
                time.sleep(0.5)
                list_item = ui.list1.findItems(srch, QtCore.Qt.MatchExactly)
                if len(list_item) > 0:
                    for i in list_item:
                        row = ui.list1.row(i)
                        ui.list1.setFocus()
                        ui.list1.setCurrentRow(row)
                        item = ui.list1.item(row)
                        if item:
                            ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)
                    

@pyqtSlot(str)
def navigate_player_remotely(nm):
    global ui
    index = ui.btn1.findText('PlayLists')
    site = 'PlayLists'
    ui.set_parameters_value(siteval=site)
    if index >= 0:
        ui.btn1.setCurrentIndex(0)
        ui.btn1.setCurrentIndex(index)
    time.sleep(0.5)
    ui.list3.setFocus()
    ui.list3.setCurrentRow(0)
    list_item = ui.list1.findItems(nm, QtCore.Qt.MatchExactly)
    if len(list_item) > 0:
        for i in list_item:
            row = ui.list1.row(i)
            ui.list1.setFocus()
            ui.list1.setCurrentRow(row)
            item = ui.list1.item(row)
            if item:
                ui.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)
            
    

@pyqtSlot(str)
def update_databse_signal(mode):
    global ui
    if mode == 'video':
        video_dir = os.path.join(home, 'VideoDB')
        if not os.path.exists(video_dir):
            os.makedirs(video_dir)
        video_db = os.path.join(video_dir, 'Video.db')
        video_file = os.path.join(video_dir, 'Video.txt')
        video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
        
        if not os.path.exists(video_db):
            ui.media_data.create_update_video_db(video_db, video_file, video_file_bak, update_progress_show=False)
        else:
            ui.media_data.update_on_start_video_db(video_db, video_file, video_file_bak, 'Update', update_progress_show=False)
    elif mode == 'music':
        music_dir = os.path.join(home, 'Music')
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)
        music_db = os.path.join(home, 'Music', 'Music.db')
        music_file = os.path.join(home, 'Music', 'Music.txt')
        music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
        if not os.path.exists(music_db):
            ui.media_data.create_update_music_db(music_db, music_file, music_file_bak, update_progress_show=False)
        else:
            ui.media_data.update_on_start_music_db(music_db, music_file, music_file_bak, update_progress_show=False)


@pyqtSlot(str)
def delete_torrent_history(nm):
    global home, ui
    if ui.stream_session:
        t_list = ui.stream_session.get_torrents()
        for i in t_list:
            chk_name = i.name()
            if chk_name == nm:
                ui.stream_session.remove_torrent(i)
                logger.info('removing--torrent--{0}'.format(chk_name))
    if nm:
        #ui.stop_torrent(from_client=True)
        hist_folder = os.path.join(home, 'History', 'Torrent')
        hist_txt = os.path.join(hist_folder, 'history.txt')
        hist_torrent = os.path.join(hist_folder, nm+'.torrent')
        hist_torrent_folder = os.path.join(hist_folder, nm)
        down_location = os.path.join(ui.torrent_download_folder, nm)
        if os.path.exists(hist_txt):
            lines = open_files(hist_txt, lines_read=True)
            new_lines = [i.strip() for i in lines]
            try:
                indx = new_lines.index(nm)
            except ValueError as e:
                print(e)
                indx = -1
            if indx != -1 and indx >= 0:
                del new_lines[indx]
                
            write_files(hist_txt, new_lines, line_by_line=True)
            if os.path.isdir(hist_torrent_folder):
                shutil.rmtree(hist_torrent_folder)
                logger.info('removed-folder:-{0}'.format(hist_torrent_folder))
                if os.path.isfile(hist_torrent):
                    os.remove(hist_torrent)
                    logger.info('removed-torrent:-{0}'.format(hist_torrent))
                if os.path.exists(down_location):
                    if os.path.isdir(down_location):
                        shutil.rmtree(down_location)
                    elif os.path.isfile(down_location):
                        os.remove(down_location)
                    logger.info('removed-torrent files:-{0}'.format(down_location))
            else:
                logger.info('nothing to delete: wrong file name')

class HTTPServer_RequestHandler(BaseHTTPRequestHandler):

    protocol_version = 'HTTP/1.1'
    proc_req = True
    client_auth_dict = {}
    playlist_auth_dict = {}
    playlist_m3u_dict = {}
    playlist_shuffle_list = []
    nav_signals = DoGETSignal()
    old_path = []
    last_view = []
    
    def process_HEAD(self):
        global ui, logger, getdb

        epnArrList = ui.epn_arr_list

        try:
            get_bytes = int(self.headers['Range'].split('=')[1].replace('-', ''))
        except Exception as e:
            get_bytes = 0
        #print(get_bytes, '--head--')
        #print(self.headers, '--head--')

        logger.info(self.path)
        path = self.path.replace('/', '', 1)
        if '/' in path:
            path = path.split('/')[0]
        path = urllib.parse.unquote(path)
        #print(os.getcwd())
        _head_found = False
        nm = ''
        user_agent = self.headers['User-Agent']
        if path.endswith('_playlist'):
            row, pl = path.split('_', 1)
            row_num = int(row)
            nm = ui.epn_return(row_num)
        elif path.lower() == 'play' or not path:
            self.row = ui.list2.currentRow()
            if self.row < 0:
                self.row = 0
            if ui.btn1.currentText().lower() == 'youtube':
                nm = ui.final_playing_url
            else:
                nm = ui.epn_return(self.row)
        elif path.startswith('abs_path='):
            try:
                path = path.split('abs_path=', 1)[1]
                nm = path
                nm = str(base64.b64decode(nm).decode('utf-8'))
                logger.info(nm)
                if 'youtube.com' in nm:
                    nm = ui.yt.get_yt_url(nm, ui.quality_val, ui.ytdl_path, logger)
            except Exception as e:
                print(e)
        elif path.startswith('relative_path='):
            try:
                path = path.split('relative_path=', 1)[1]
                nm = path
                nm = str(base64.b64decode(nm).decode('utf-8'))
                if nm.split('&')[4] == 'True':
                    old_nm = nm
                    if ui.https_media_server:
                        https_val = 'https'
                    else:
                        https_val = 'http'
                    nm = https_val+"://"+ui.local_ip+':'+str(ui.local_port)+'/'
                    self.nav_signals.new_signal(old_nm)
                else:
                    nm = getdb.epn_return_from_bookmark(nm, from_client=True)
            except Exception as e:
                print(e)
        elif path.startswith('site=') or path.startswith('stream_'):
            nm = 'txt_html'
        if nm:
            if nm.startswith('http'):
                self.send_response(303)
                self.send_header('Location', nm)
                self.end_headers()
            elif nm == 'txt_html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(1024))
                self.send_header('Accept-Ranges', 'bytes')
                #self.send_header('Content-Range', 'bytes ' +str('0-')+str(size)+'/'+str(size))
                self.send_header('Connection', 'close')
                self.end_headers()
            else:
                nm = nm.replace('"', '')
                self.send_response(200)
                #if user_agent:
                #if 'firefox' in user_agent.lower() or 'chrome' in user_agent.lower():
                #	self.send_header('Content-type', 'video/webm')
                #else:
                #self.send_header('Content-type', 'video/mp4')
                #else:
                self.send_header('Content-type', 'video/mp4')
                size = os.stat(nm).st_size
                self.send_header('Content-Length', str(size))
                self.send_header('Accept-Ranges', 'bytes')
                if get_bytes:
                    self.send_header('Content-Range', 'bytes ' +str(get_bytes)+'-'+str(size)+'/'+str(size))
                self.send_header('Connection', 'close')
                self.end_headers()
                    #print(size)
        else:
            self.send_response(404)
            self.end_headers()

    def process_playlist_object(self, new_dict):
        global logger
        arr = []
        new_title = ''
        new_artist = ''
        link = ''
        sort_key_arr = [int(i) for i in new_dict]
        sort_key_arr.sort()
        logger.info(sort_key_arr)
        for i in sort_key_arr:
            logger.info(i)
            j = new_dict[str(i)]
            for k in j:
                logger.info('title={0}, data={1}'.format(k, j[k]))
                if (k == 'title'):
                    j[k] = j[k].strip()
                    title_arr = j[k].split(' - ', 1)
                    if len(title_arr) >= 2:
                        new_title = title_arr[1].strip()
                        new_artist = title_arr[0].strip()
                    else:
                        new_title = new_artist = j[k]
                elif k == 'data':
                    m = re.search('abs_path=[^"]*|relative_path=[^"]*', j[k])
                    if m:
                        link = m.group()
                        if '&pl_id=' in link:
                            link, pl_id = link.rsplit('&pl_id=', 1)
                        elif '/' in link:
                            link = link.rsplit('/', 1)[0]
                if new_title and new_artist and link:
                    new_line = new_title+'	'+link+'	'+new_artist
                    arr.append(new_line)
                    new_title = ''
                    new_artist = ''
                    link = ''
        return arr

    def process_POST(self):
        global home, logger
        if self.path.startswith('/save_playlist='):
            new_var = self.path.replace('/save_playlist=', '', 1)
            logger.info(new_var)
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            logger.info(content)
            new_dict = json.loads(content)
            arr = self.process_playlist_object(new_dict)
            logger.info(arr)
            logger.info(new_var)
            created = False
            pls_append = False
            if new_var and arr:
                new_var = urllib.parse.unquote(new_var)
                file_path = os.path.join(home, 'Playlists', new_var)
                if not os.path.exists(file_path):
                    write_files(file_path, arr, line_by_line=True)
                    created = True
                elif os.path.isfile(file_path):
                    lines = open_files(file_path, lines_read=True)
                    new_lines = [i.strip() for i in lines]
                    new_lines = new_lines + arr
                    write_files(file_path, new_lines, line_by_line=True)
                    created = True
                    pls_append = True
            if created:
                if pls_append:
                    msg = 'Appended to Playlist: {0}'.format(new_var)
                else:
                    msg = 'New Playlist: {0} created'.format(new_var)
            else:
                msg = 'Playlist creation failed'
            self.final_message(bytes(msg, 'utf-8'))
        elif self.path.startswith('/get_playlist_in_m3u'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            logger.info(content)
            new_dict = json.loads(content)
            sort_key_arr = [int(i) for i in new_dict]
            sort_key_arr.sort()
            pls_txt = '#EXTM3U\n'
            for i in sort_key_arr:
                pls_txt = pls_txt+'#EXTINF:0, {0}\n{1}\n'.format(
                    new_dict[str(i)]['title'], new_dict[str(i)]['data']
                    )
            logger.debug(pls_txt)
            dict_pls_len = str(len(self.playlist_m3u_dict) + 1)
            if dict_pls_len in self.playlist_m3u_dict:
                del self.playlist_m3u_dict[dict_pls_len]
            self.playlist_m3u_dict.update({str(dict_pls_len):pls_txt})
            url_response = 'm3u_playlist_{0}.m3u'.format(dict_pls_len)
            self.final_message(bytes(url_response, 'utf-8'))
        elif ((self.path.startswith('/sending_playlist')
                or self.path.startswith('/sending_queueitem'))
                and ui.pc_to_pc_casting == 'slave'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
                if 'Content-Type' in content:
                    content = re.search('\{[^\n]*', content).group()
                    content = content.strip()
            new_dict = json.loads(content)
            sort_key_arr = [int(i) for i in new_dict]
            sort_key_arr.sort()
            lines = []
            odict = OrderedDict()
            #ui.master_casting_subdict.clear()
            for i in sort_key_arr:
                odict.update({str(i):new_dict.get(str(i))})
            play_row = -1
            sample_url = None
            val = None
            fanart_url = None
            for i in odict:
                val = odict[i]
                lines.append('{}\t{}\t{}'.format(val['title'], val['url'], val['artist']))
                play_row = val['play_now']
                if val['sub'] != 'none':
                    ui.master_casting_subdict.update({val['url']:val['sub']})
            if isinstance(val, dict):
                sample_url = val.get('url')
                if sample_url:
                    n = urlparse(sample_url)
                    fanart_url = n.scheme + '://' + n.netloc + '/' + 'get_current_background'
            if self.path.startswith('/sending_playlist'):
                file_name = os.path.join(ui.home_folder, 'Playlists', 'TMP_PLAYLIST')
                f = open(file_name, 'w').close()
                write_files(file_name, lines, line_by_line=True)
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.kill()
                    ui.mpvplayer_started = False
                ui.instant_cast_play = int(play_row)
                if ui.instant_cast_play >= len(lines) or ui.instant_cast_play < 0:
                    ui.instant_cast_play = 0
                self.nav_signals.total_navigation('PlayLists', 'PlayLists', 'TMP_PLAYLIST', False)
            else:
                ui.queue_url_list = ui.queue_url_list + lines
                ui.queue_item_external = -100
                ui.set_queue_item_btn.clicked_emit()
            if ui.remote_control_field:
                ui.remote_control = True
            self.final_message(bytes('OK', 'utf-8'))
            if fanart_url:
                out_file = os.path.join(ui.tmp_download_folder, 'master_fanart.jpg')
                ui.vnt.get(fanart_url, out=out_file, onfinished=self.got_master_fanart)
        elif self.path.startswith('/sending_subtitle') and ui.pc_to_pc_casting == 'slave':
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
                if 'Content-Type' in content:
                    content = re.search('\{[^\n]*', content).group()
                    content = content.strip()
            sub_dict = json.loads(content)
            sub_name_bytes = bytes(ui.final_playing_url, 'utf-8')
            h = hashlib.sha256(sub_name_bytes)
            sub_name = h.hexdigest()
            sub_name_path = os.path.join(ui.yt_sub_folder, sub_name)
            for i in sub_dict:
                val = sub_dict[i]
                subtitle_path = sub_name_path + '.' + i
                write_files(subtitle_path, val, line_by_line=False)
                if os.name == 'nt':
                    subtitle_path = 'file:///{}'.format(subtitle_path.replace('\\', '/'))
                if ui.mpvplayer_val.processId() > 0 or ui.player_val in ["libmpv", "libvlc"]:
                    ui.master_casting_subdict.update({ui.final_playing_url:subtitle_path})
                    self.nav_signals.control_signal(-1000, 'add_subtitle')
            self.final_message(bytes('Subtitle Recieved', 'utf-8'))
        elif self.path.startswith('/sending_command') and ui.pc_to_pc_casting == 'slave':
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            param, value = content.split('&')
            if param and not param.startswith('param='):
                param, value = value, param
            self.final_message(bytes('Command Recieved', 'utf-8'))
            ui.gui_signals.player_command(param.replace('+', ' '), value.replace('+', ' '))
        elif self.path.startswith('/sending_web_command'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            param = "param={}".format(content.get("param"))
            value = "widget={}".format(content.get("widget"))
            self.final_message(bytes('Command Recieved', 'utf-8'))
            ui.gui_signals.player_command(param.replace('+', ' '), value.replace('+', ' '))
        elif self.path.startswith('/fetch-posters'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            title = content.get("title")
            url = content.get("url")
            mode = content.get("mode")
            site_option = content.get("site_option")
            if mode == "poster" and title is not None and url is not None and url.startswith("http"):
                ui.remove_fanart(site_option, title, "remove_poster")
                ui.fetch_fanart(site_option, url, title, "poster")
            elif mode == "fanart" and title is not None and url is not None and url.startswith("http"):
                ui.remove_fanart(site_option, title, "remove_fanart")
                ui.fetch_fanart(site_option, url, title, "fanart")
            self.final_message(bytes('Command Recieved', 'utf-8'))
        elif self.path.startswith('/modify_category'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            category = content.get("category")
            paths = []
            if category in ui.category_array:
                playlist = content.get("playlist")
                for i in playlist:
                    path = i.split('abs_path=', 1)[1].rsplit("/", 1)[0]
                    abs_path = str(base64.b64decode(path).decode('utf-8'))
                    if os.path.exists(abs_path):
                        paths.append(abs_path)

                if paths:
                    conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                    cur = conn.cursor()
                    query_params = [category] + paths
                    if len(paths) == 1:
                        qr = 'Update Video Set Category=? Where Path=?'
                    else: 
                        s = ", ".join(['?']*len(paths))
                        qr = 'Update Video Set Category=? Where Path in ({})'.format(s)
                    cur.execute(qr, tuple(query_params))
                    logger.debug(qr)
                    conn.commit()
                    conn.close()
                    msg = "playlist added to category {}".format(category)
                else:
                    msg = "invalid video paths"
            else:
                msg = "category does not exists"
            self.final_message(bytes(msg, 'utf-8'))
        elif self.path.startswith('/rename_title'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            title = content.get("title")
            db_title = content.get("db_title", "")
            paths = []
            if title and len(title) < 100:
                playlist = content.get("playlist")
                for i in playlist:
                    path = i.split('abs_path=', 1)[1].rsplit("/", 1)[0]
                    abs_path = str(base64.b64decode(path).decode('utf-8'))
                    if os.path.exists(abs_path):
                        paths.append(abs_path)

                if paths:
                    conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                    cur = conn.cursor()
                    query_params = [title] + paths
                    if len(paths) == 1:
                        qr = 'Update Video Set Title=? Where Path=?'
                    else: 
                        s = ", ".join(['?']*len(paths))
                        qr = 'Update Video Set Title=? Where Path in ({})'.format(s)
                    cur.execute(qr, tuple(query_params))
                    rows_changed = cur.rowcount
                    if rows_changed > 0:
                        # update series info
                        qr = 'update series_info set db_title = ? where db_title = ?'
                        cur.execute(qr, (title, db_title))
                        rows_updated = cur.rowcount
                        if rows_updated  > 0:
                            print(f"series_info table updated {rows_updated}: {db_title} => {title}")
                    logger.debug(qr)
                    conn.commit()
                    conn.close()
                    if rows_changed > 0:
                        msg = "Title Changed to {}, rows affected = {}".format(title, rows_changed)
                    else:
                        msg = "0 rows affected, Title not changed"

                else:
                    msg = "invalid video paths"
            else:
                msg = "no title"
            self.final_message(bytes(msg, 'utf-8'))
        elif self.path.startswith('/series_metadata'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            title = content.get("title")
            media_type = content.get("media_type")
            category = content.get("category")
            paths = []
            error_response = {
                "success": False,
                "data": None
            }
            response_data = {}
            if title and media_type and len(title) < 100:
                if media_type.lower() == "video":
                    response_data = ui.media_data.fetch_series_metadata(title)
                elif media_type.lower() == "music":
                    response_data = ui.media_data.fetch_music_metadata(title, category)

                if response_data:
                    self.send_json_response(response_data)
                else:
                    self.send_json_response(error_response, status_code=422)
            else:
                self.send_json_response(error_response, status_code=422)
        elif self.path.startswith('/fetch_series_metadata'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            db_title = content.get("db_title")
            suggested_title = content.get("suggested_title")
            series_type = content.get("series_type")
            media_type = content.get("media_type")
            from_cache = content.get("from_cache")
            paths = []
            if media_type and media_type.lower() == "video":
                media_type == "video"

            if suggested_title and len(suggested_title) < 100 and media_type ==  "video":
                if series_type == "anime":
                    if from_cache == "yes":
                        result = ui.anime_info_fetcher.get_anime_info(suggested_title, True)
                    else:
                        result = ui.anime_info_fetcher.get_anime_info(suggested_title, False)
                else:
                    if from_cache == "yes":
                        result = ui.tvshow_info_fetcher.get_series_info(suggested_title, True)
                    else:
                        result = ui.tvshow_info_fetcher.get_series_info(suggested_title, False)

                ui.media_data.insert_series_data(db_title, result, series_type)

                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))

                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                qr = """
                    select * from series_info where db_title = ?
                    """
                cur.execute(qr, (db_title, ))
                rows = [row for row in cur.fetchall()]
                if rows:
                    data = dict(rows[0])
                    response_data = {
                        "success": True,
                        "data": data
                    }

                conn.commit()
                conn.close()
                self.send_json_response(response_data)
            else:
                error_response = {
                    "success": False,
                    "data": None
                }
                self.send_json_response(error_response, status_code=422)
        elif self.path.startswith('/fetch_image_poster'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            db_title = content.get("db_title")
            img_url = content.get("img_url")
            media_type = content.get("media_type")
            if media_type and media_type.lower() == "video":
                media_type == "video"
            paths = []
            if db_title and media_type == "video" and len(db_title) < 100:

                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                qr = """
                    select * from series_info where db_title = ?
                    """
                cur.execute(qr, (db_title, ))
                rows = [row for row in cur.fetchall()]
                img_path = ""
                if rows:
                    data = dict(rows[0])
                    image_poster_large = data.get("image_poster_large", "")

                    if image_poster_large:
                        img_name = image_poster_large.rsplit("/", 1)[-1]
                        img_path = os.path.join(ui.anime_info_fetcher.thumbnail_dir, img_name)
                    response_data = {
                        "success": True
                    }

                conn.commit()
                conn.close()
                if img_path:
                    ui.vnt.get(img_url, out=img_path)
                self.send_json_response(response_data)
            else:
                error_response = {
                    "success": False,
                    "data": None
                }
                self.send_json_response(error_response, status_code=422)
        elif self.path.startswith('/reset_series_metadata'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            db_title = content.get("db_title")
            media_type = content.get("media_type")
            if media_type and media_type.lower() == "video":
                media_type = "video"
            paths = []
            if db_title and len(db_title) < 100 and media_type == "video":
                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                qr = """
                    select * from series_info where db_title = ?
                """

                cur.execute(qr, (db_title, ))
                select_result = [row for row in cur.fetchall()]
                if select_result:
                    select_result_dict = dict(select_result[0])
                    image_poster_large = select_result_dict.get("image_poster_large", "")
                    img_name = image_poster_large.rsplit("/", 1)[-1]
                    img_path = os.path.join(ui.anime_info_fetcher.thumbnail_dir, img_name)
                    if os.path.isfile(img_path) and img_path.endswith(".jpg"):
                        os.remove(img_path)

                qr = """
                    delete from series_info where db_title = ?
                    """
                cur.execute(qr, (db_title, ))
                if cur.rowcount:
                    response_data = {
                        "success": True
                    }
                    conn.commit()
                    conn.close()
                    self.send_json_response(response_data)
                else:
                    response_data = {
                        "success": False
                    }
                    conn.commit()
                    conn.close()
                    self.send_json_response(response_data, status_code=422)
            else:
                error_response = {
                    "success": False,
                    "data": None
                }
                self.send_json_response(error_response, status_code=422)
        else:
            self.final_message(bytes('Nothing Available', 'utf-8'))

    def send_json_response(self, data, status_code=200):
        """Send a JSON response with proper headers"""
        try:
            # Convert data to JSON string
            json_string = json.dumps(data, ensure_ascii=False, indent=2)
            json_bytes = json_string.encode('utf-8')

            # Send response
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(json_bytes)))
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS if needed
            self.end_headers()
            self.wfile.write(json_bytes)

        except Exception as e:
            # Fallback error response
            error_msg = f'{{"success": false, "message": "JSON encoding error: {str(e)}"}}'
            error_bytes = error_msg.encode('utf-8')

            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(error_bytes)))
            self.end_headers()
            self.wfile.write(error_bytes)

    def do_init_function(self, type_request=None):
        global ui, logger
        path = self.path.replace('/', '', 1)
        if '/' in path:
            if not path.startswith('site=') and'&s=' not in path:
                path = path.rsplit('/', 1)[0]
        if path.startswith('relative_path=') or path.startswith('abs_path='):
            if ".played" in path:
                path = path.rsplit(".played", 1)[0]
            elif ".image" not in self.path and path not in self.old_path:
                self.old_path.append(path)
            if len(self.old_path) > 100:
                self.old_path.clear()
        else:
            path = urllib.parse.unquote(path)
        #logger.info(self.requestline)
        print(f"Total in Direct Playlist: {len(self.old_path)}")
        playlist_id = None
        try:
            get_bytes = int(self.headers['Range'].split('=')[1].replace('-', ''))
        except Exception as e:
            get_bytes = 0
        #print(self.headers)
        cookie_verified = False
        cookie_set = False
        cookie_val = self.headers['Cookie']
        if cookie_val:
            try:
                uid_c = cookie_val.split('=')[1]
                uid_val = (self.client_auth_dict[uid_c])
                old_time, playlist_id = uid_val.split('&pl_id=')
                #logger.info('old-time={0}:pl_id={1}'.format(old_time, playlist_id))
                old_time = int(old_time)
                cur_time = int(time.time())
                #logger.info(self.client_auth_dict)
                #logger.info('Time Elapsed: {0}'.format(cur_time-old_time))
                if (cur_time - old_time) > ui.cookie_expiry_limit*3600:
                    cookie_verified = False
                    del self.client_auth_dict[uid_c]
                    logger.debug('deleting client cookie due to timeout')
                else:
                    cookie_verified = True
                if '&pl_id=' in path:
                    path, pl_id = path.rsplit('&pl_id=', 1)
            except Exception as err_val:
                print(err_val)
        else:
            #if '/' in path:
            #	path = path.split('/')[0]
            if '&pl_id=' in path:
                path, pl_id = path.rsplit('&pl_id=', 1)
                del_uid = False
                found_uid = False
                try:
                    if pl_id in self.playlist_auth_dict:
                        #print(pl_id, self.playlist_auth_dict[pl_id], '--playlist--id--')
                        old_time = self.playlist_auth_dict[pl_id]
                        found_uid = True
                        time_diff = int(time.time()) - int(old_time)
                        #print(time_diff, '--time--diff--')
                        if (time_diff) > ui.cookie_playlist_expiry_limit*3600:
                            del self.playlist_auth_dict[pl_id]
                            try:
                                del ui.playlist_auth_dict_ui[pl_id]
                            except Exception as e:
                                print(e, '--488--')
                            del_uid = True
                except Exception as err_val:
                    print(err_val, '--316--')

                if found_uid and not del_uid:
                    cookie_verified = True
                elif found_uid and del_uid:
                    print('--timeout--')

        if ui.media_server_key and not ui.media_server_cookie:
            new_key = ui.media_server_key 
            cli_key = self.headers['Authorization']
            if cli_key: 
                #print(cli_key)
                cli_key_byte = bytes(str(cli_key), 'utf-8')
                hash_obj = hashlib.sha256(cli_key_byte)
                cli_key = hash_obj.hexdigest()
                #print(cli_key, new_key)
            client_addr = str(self.client_address[0])
            logger.info('--cli--addr-no-cookie-{0}'.format(client_addr))
            logger.info('--auth-no-cookie-{0}'.format(ui.client_auth_arr))
            if not cli_key and (not client_addr in ui.client_auth_arr):
                if ipaddress.ip_address(client_addr).is_private:
                    self.auth_header()
                else:
                    self.final_message(b'Access from outside not allowed')
            elif (cli_key == new_key) or (client_addr in ui.client_auth_arr):
                first_time = False
                if client_addr not in ui.client_auth_arr:
                    if ipaddress.ip_address(client_addr).is_private:
                        ui.client_auth_arr.append(client_addr)
                if ipaddress.ip_address(client_addr).is_private:
                    if type_request == 'get':
                        self.get_the_content(path, get_bytes)
                    elif type_request == 'head':
                        self.process_HEAD()
                    elif type_request == 'post':
                        self.process_POST()
                else:
                    self.final_message(b'Access from outside not allowed')
            else:
                txt = b'You are not authorized to access the content'
                self.final_message(txt, auth_failed=True)
        elif ui.media_server_cookie and ui.media_server_key:
            new_key = ui.media_server_key 
            cli_key = self.headers['Authorization']
            if cli_key: 
                #print(cli_key)
                cli_key_byte = bytes(str(cli_key), 'utf-8')
                hash_obj = hashlib.sha256(cli_key_byte)
                cli_key = hash_obj.hexdigest()
                #print(cli_key, new_key)
            client_addr = str(self.client_address[0])
            #logger.info('--cli-with-cookie-{0}'.format(client_addr))
            #logger.info('--auth-with-cookie-{0}'.format(ui.client_auth_arr))
            #logger.info('--auth-local-cookie-{0}'.format(ui.local_auth_arr))
            if client_addr in ui.local_auth_arr:
               cookie_set = True 
            elif not cli_key and not cookie_verified:
                self.auth_header()
            elif (cli_key == new_key) and not cookie_verified:
                if client_addr not in ui.client_auth_arr:
                    ui.client_auth_arr.append(client_addr)
                uid = str(uuid.uuid4())
                while uid in self.client_auth_dict:
                    logger.debug("no unique ID, Generating again")
                    uid = str(uuid.uuid4())
                    time.sleep(0.1)
                uid_pl = str(uuid.uuid4())
                uid_pl = uid_pl.replace('-', '')
                while uid_pl in self.playlist_auth_dict:
                    logger.debug("no unique playlist ID, Generating again")
                    uid_pl = str(uuid.uuid4())
                    uid_pl = uid_pl.replace('-', '')
                    time.sleep(0.1)
                cur_time = str(int(time.time()))
                new_id = cur_time+'&pl_id='+uid_pl
                self.playlist_auth_dict.update({uid_pl:cur_time})
                ui.playlist_auth_dict_ui.update({uid_pl:cur_time})
                self.client_auth_dict.update({uid:new_id})
                set_cookie_id = "id="+uid
                self.final_message(b'Session Established, Now reload page again', set_cookie_id)
                cookie_set = True
                
            if cookie_set or cookie_verified:
                if ipaddress.ip_address(client_addr).is_private:
                    if type_request == 'get':
                        self.get_the_content(path, get_bytes, play_id=playlist_id)
                    elif type_request == 'head':
                        self.process_HEAD()
                    elif type_request == 'post':
                        self.process_POST()
                elif ui.access_from_outside_network:
                    if not ui.my_public_ip:
                        try:
                            logger.debug('trying to get external public ip')
                            my_ip = str(ccurl('https://diagnostic.opendns.com/myip'))
                            try:
                                new_ip_object = ipaddress.ip_address(my_ip)
                            except Exception as e:
                                print(e)
                                my_ip = None
                        except Exception as e:
                            print(e)
                            my_ip = None
                    else:
                        my_ip = ui.my_public_ip
                    if my_ip:
                        if type_request == 'get':
                            self.get_the_content(path, get_bytes, my_ip_addr=my_ip, play_id=playlist_id)
                        elif type_request == 'head':
                            self.process_HEAD()
                        elif type_request == 'post':
                            self.process_POST()
                    else:
                        self.final_message(b'Could not find your Public IP')
                else:
                    txt = b'Access Not Allowed, Authentication Failed. Clear cache, ACTIVE LOGINS and try again or restart browser.'
                    self.final_message(txt, auth_failed=True)
            else:
                txt = b'Access Not Allowed, Authentication Failed. Clear cache, ACTIVE LOGINS and try again or restart browser.'
                self.final_message(txt, auth_failed=True)
        else:
            client_addr = str(self.client_address[0])
            if client_addr not in ui.client_auth_arr:
                ui.client_auth_arr.append(client_addr)
            if ipaddress.ip_address(client_addr).is_private:
                if type_request == 'get':
                    self.get_the_content(path, get_bytes)
                elif type_request == 'head':
                    self.process_HEAD()
                elif type_request == 'post':
                    self.process_POST()
            else:
                txt = b'Access From Outside Network Not Allowed'
                self.final_message(txt)
                
    def got_master_fanart(self, *args):
        result = args[-1]
        url = args[-2]
        if result.error is None:
            if result.content_type in ['image/jpeg', 'image/png']:
                ui.gui_signals.fanart_changed(result.out_file, ui.player_theme)
            
    def do_HEAD(self):
        self.do_init_function(type_request='head')

    def do_GET(self):
        if (ui.remote_control and ui.remote_control_field
                and self.path.startswith('/youtube_quick=')):
            logger.debug('using quick mode')
            path = self.path.replace('/', '', 1)
            self.get_the_content(path, 0)
        elif (self.path.startswith('/master_abs_path=')
                or self.path.startswith('/master_relative_path=')
                or self.path.startswith('/get_current_background')):
            if ui.pc_to_pc_casting == 'master':
                path = self.path.replace('/', '', 1)
                master_token = None
                allow_access = False
                if '&master_token=' in path:
                    _, master_token = path.rsplit('&master_token=', 1)
                    master_token = master_token.split('&')[0]
                    if master_token and master_token in ui.master_access_tokens:
                        allow_access = True
                if path == "get_current_background":
                    allow_access = True
                path = re.sub(r'/&master_token=(.?)*&', '', path)
                self.path = re.sub(r'/&master_token=(.?)*&', '', self.path)
                if '/' in path:
                    path = path.rsplit('/', 1)[0]
                try:
                    get_bytes = int(self.headers['Range'].split('=')[1].replace('-', ''))
                except Exception as e:
                    get_bytes = 0
                if allow_access:
                    self.get_the_content(path, get_bytes)
                else:
                    self.final_message(b'Access Denied: invalid access token')
            else:
                self.final_message(b'Not Allowed')
        elif self.path.startswith('/browse.html')  or self.path.startswith('/browse?'):
            # Handle browse requests
            self.handle_browse_request()
        elif self.path.startswith('/admin.html') or self.path == '/admin':
            self.handle_admin_request()
        elif self.path == '/admin-data':
            self.handle_admin_data_request()
        elif self.path.startswith('/series/'):
            # Handle browse requests
            self.handle_browse_series_request()
            nm = '/stream_continue.htm'
            self.send_response(303)
            self.send_header('Location', nm)
            self.send_header('Connection', 'close')
            self.end_headers()
        else:
            self.do_init_function(type_request='get')

    def handle_browse_series_request(self):
        global logger, home
        series_id = self.path.split("/")[-1]
        """Get all available genres from series_info table"""
        try:
            query = """
            SELECT db_title 
            FROM series_info 
            WHERE id = ?
            """
            
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cursor = conn.execute(query, (series_id,))
            result = [row[0] for row in cursor.fetchall()]
            if result:
                db_title = result[0]
            
                cur = conn.execute('SELECT Directory from Video Where Title=?', (db_title, ))
                res = cur.fetchone()
                if res:
                    directory = bytes(res[0], 'utf-8')

                    st = 'video'
                    st_o = 'available'
                    h = hashlib.sha256(directory)
                    hash_val = h.hexdigest()
                    srch = f"{hash_val}.hash"
                    st_arr = [st, st_o, srch]
                    st_arr_str  = ",".join(st_arr)

                    last_view_file = os.path.join(home, 'History', 'last_viewed.txt')
                    self.last_view.append(st_arr_str)
                    with open(last_view_file, "w") as f:
                        f.write(st_arr_str)

        except Exception as e:
            logger.error(f"Error getting available genres: {e}")
        return []

    def parse_query_params(self, query_string: str) -> Dict[str, Any]:
        global ui, logger

        """Parse query parameters from URL"""
        if not query_string:
            return {}
        
        try:
            parsed = urllib.parse.parse_qs(query_string, keep_blank_values=False)
            filters = {}
            
            for key, values in parsed.items():
                if values and values[0]:
                    if key == 'genres' and len(values) > 1:
                        # Handle multiple genre selections from multiselect
                        filters[key] = values
                    else:
                        filters[key] = values[0]
            
            return filters
        except Exception as e:
            logger.error(f"Error parsing query params: {e}")
            return {}

    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize filter parameters"""
        validated = {}
        
        # Search
        if filters.get('search'):
            search = filters['search'].strip()[:100]
            if len(search) >= 1:
                validated['search'] = search
        
        # Genres - handle multiple selections from js-multiselect
        if filters.get('genres'):
            genres = filters['genres']
            if isinstance(genres, list):
                # Multiple selections from multiselect
                genre_list = [g.strip() for g in genres if g.strip()][:10]  # Allow up to 10 genres
                if genre_list:
                    validated['genres'] = ','.join(genre_list)
            elif isinstance(genres, str):
                # Single string or comma-separated
                genres = genres.strip()
                if genres:
                    genre_list = [g.strip() for g in genres.split(',')][:10]
                    validated['genres'] = ','.join(genre_list)
        
        # Year range
        current_year = datetime.now().year
        
        if filters.get('year_from'):
            try:
                year_from = int(filters['year_from'])
                if 1900 <= year_from <= current_year + 5:
                    validated['year_from'] = year_from
            except (ValueError, TypeError):
                pass
        
        if filters.get('year_to'):
            try:
                year_to = int(filters['year_to'])
                if 1900 <= year_to <= current_year + 5:
                    validated['year_to'] = year_to
            except (ValueError, TypeError):
                pass
        
        # Type
        if filters.get('type'):
            validated['type'] = filters['type'].strip()
        
        # Sort
        valid_sorts = ['title', 'year', 'score', 'popularity', 'rank']
        sort_field = filters.get('sort', 'title')
        validated['sort'] = sort_field if sort_field in valid_sorts else 'title'
        
        # Order
        order = filters.get('order', 'asc').lower()
        validated['order'] = 'asc' if order == 'asc' else 'desc'

        if filters.get('category'):
            validated['category'] = filters['category'].strip()

        
        return validated

    def get_available_genres(self) -> List[str]:
        global logger, home
        """Get all available genres from series_info table"""
        try:
            query = """
            SELECT DISTINCT genres 
            FROM series_info 
            WHERE genres IS NOT NULL AND genres != ''
            """
            
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # Parse and flatten genres
            all_genres = set()
            for row in rows:
                if row[0]:
                    # Split comma-separated genres and clean them
                    genres = [g.strip() for g in row[0].split(',') if g.strip()]
                    all_genres.update(genres)
            
            # Return sorted list
            return sorted(list(all_genres))
            
        except Exception as e:
            logger.error(f"Error getting available genres: {e}")
            return []

    def get_available_types(self) -> List[str]:
        global home, logger
        """Get all available types from series_info table"""
        try:
            query = """
            SELECT DISTINCT type 
            FROM series_info 
            WHERE type IS NOT NULL AND type != ''
            """
            
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            return sorted([row[0] for row in rows if row[0]])
            
        except Exception as e:
            logger.error(f"Error getting available types: {e}")
            return []

    def get_year_range(self) -> Tuple[int, int]:
        global logger, home
        """Get min and max years from series_info table"""
        try:
            query = """
            SELECT MIN(year), MAX(year) 
            FROM series_info 
            WHERE year IS NOT NULL AND year > 0
            """
            
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cursor = conn.execute(query)
            row = cursor.fetchone()
            
            if row and row[0] and row[1]:
                return int(row[0]), int(row[1])
            else:
                return 1900, 2025  # Default range
                
        except Exception as e:
            logger.error(f"Error getting year range: {e}")
            return 1900, 2025

    def generate_filter_options(self, selected_filters: Dict[str, Any]) -> Dict[str, str]:
        global logger, ui
        """Generate HTML options for filter dropdowns with preselected values"""
        options = {}
        
        try:
            # Get available data from database
            genres = self.get_available_genres()
            types = self.get_available_types()
            min_year, max_year = self.get_year_range()
            
            # Get selected genres list
            selected_genres = []
            if selected_filters.get('genres'):
                selected_genres = selected_filters['genres'].split(',')
            
            # Generate genre options for js-multiselect
            genre_options = []
            for genre in genres:
                selected = 'selected' if genre in selected_genres else ''
                genre_options.append(f'<option value="{genre}" {selected}>{genre}</option>')
            options['genre_options'] = '\n                                    '.join(genre_options)
            
            # Generate empty category options (not used but template expects it)

            category_type = selected_filters.get('category', '')
            categories = ["Available", "History", "Recent"] + ui.category_array.copy()

            category_options = []

            for category in categories:
                selected = 'selected' if category.lower() in category_type else ''
                category_options.append(f'<option value="{category.lower()}" {selected}>{category}</option>')
            options['category_options'] = '\n                                    '.join(category_options)

            # Type options
            selected_type = selected_filters.get('type', '')
            type_options = []
            for type_val in types:
                selected = 'selected' if type_val == selected_type else ''
                type_options.append(f'<option value="{type_val}" {selected}>{type_val.title()}</option>')
            options['type_options'] = '\n                                    '.join(type_options)
            
            # Generate year options
            selected_year_from = selected_filters.get('year_from', '')
            selected_year_to = selected_filters.get('year_to', '')
            
            year_from_options = []
            year_to_options = []
            
            if min_year and max_year:
                for year in range(min_year, max_year + 1):
                    from_selected = 'selected' if str(year) == str(selected_year_from) else ''
                    to_selected = 'selected' if str(year) == str(selected_year_to) else ''
                    
                    year_from_options.append(f'<option value="{year}" {from_selected}>{year}</option>')
                    year_to_options.append(f'<option value="{year}" {to_selected}>{year}</option>')
            
            options['year_from_options'] = '\n                                        '.join(year_from_options)
            options['year_to_options'] = '\n                                        '.join(year_to_options)
            
            return options
            
        except Exception as e:
            logger.error(f"Error generating filter options: {e}")
            return {
                'genre_options': '',
                'category_options': '',
                'type_options': '',
                'year_from_options': '',
                'year_to_options': ''
            }

    def generate_selected_attributes(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """Generate selected attributes for sort/order dropdowns"""
        attrs = {}
        
        # Sort selection
        sort_value = filters.get('sort', 'title')
        attrs['title_selected'] = 'selected' if sort_value == 'title' else ''
        attrs['year_selected'] = 'selected' if sort_value == 'year' else ''
        attrs['score_selected'] = 'selected' if sort_value == 'score' else ''
        attrs['popularity_selected'] = 'selected' if sort_value == 'popularity' else ''
        attrs['rank_selected'] = 'selected' if sort_value == 'rank' else ''
        
        # Order selection
        order_value = filters.get('order', 'asc')
        attrs['asc_selected'] = 'selected' if order_value == 'asc' else ''
        attrs['desc_selected'] = 'selected' if order_value == 'desc' else ''
        
        return attrs

    
    def get_series_count(self, filters: Dict[str, Any]) -> int:
        global logger, home, ui
        """Get total count of series matching filters"""
        try:
            media_data = {}
            
            if filters.get('category'):
                cat = filters.get('category')
                if cat == 'recent':
                    data = ui.media_data.fetch_recently_added()
                    media_data = dict(data)
                elif cat == 'history':
                    data = ui.media_data.fetch_recently_accessed()
                    media_data = dict(data)
                elif cat == 'available':
                    data = ui.media_data.fetch_all_available()
                    media_data = dict(data)
                else:
                    # For database categories, we'll count using EXISTS subquery
                    pass

            # Handle recent, history, and available categories
            if media_data:
                # For these categories, we need to count items that match both media_data and filters
                if not filters.get('search') and not filters.get('type') and not filters.get('genres') and not filters.get('year_from') and not filters.get('year_to'):
                    # No additional filters, just return media_data count
                    return len(media_data)
                else:
                    # Need to apply filters to media_data items
                    db_titles = list(media_data.keys())
                    if not db_titles:
                        return 0
                    
                    placeholders = ','.join(['?' for _ in db_titles])
                    query = f"SELECT COUNT(*) FROM series_info WHERE db_title IN ({placeholders})"
                    params = db_titles[:]
                    
                    # Add other filter conditions
                    if filters.get('search'):
                        query += " AND (title LIKE ? OR english_title LIKE ?)"
                        search_term = f"%{filters['search']}%"
                        params.extend([search_term, search_term])
                    
                    if filters.get('type'):
                        query += " AND type = ?"
                        params.append(filters['type'])
                    
                    if filters.get('genres'):
                        genres = filters['genres'].split(',')
                        genre_conditions = []
                        for genre in genres:
                            genre_conditions.append("genres LIKE ?")
                            params.append(f"%{genre.strip()}%")
                        if genre_conditions:
                            query += " AND (" + " OR ".join(genre_conditions) + ")"
                    
                    if filters.get('year_from'):
                        query += " AND year >= ?"
                        params.append(filters['year_from'])
                    
                    if filters.get('year_to'):
                        query += " AND year <= ?"
                        params.append(filters['year_to'])
                    
                    conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                    cursor = conn.execute(query, params)
                    count = cursor.fetchone()[0]
                    conn.close()
                    return count
            else:
                # Handle database categories (not recent, history, available)
                need_category_filter = (filters.get('category') and 
                                       filters['category'] not in ['recent', 'history', 'available'])
                
                query = "SELECT COUNT(*) FROM series_info WHERE 1=1"
                params = []
                
                # Add category filter using EXISTS subquery
                if need_category_filter:
                    query += " AND EXISTS (SELECT 1 FROM Video v WHERE v.Title = series_info.db_title AND lower(v.Category) = ?)"
                    params.append(filters['category'])
                
                # Add other filter conditions
                if filters.get('search'):
                    query += " AND (title LIKE ? OR english_title LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
                
                if filters.get('type'):
                    query += " AND type = ?"
                    params.append(filters['type'])
                
                if filters.get('genres'):
                    genres = filters['genres'].split(',')
                    genre_conditions = []
                    for genre in genres:
                        genre_conditions.append("genres LIKE ?")
                        params.append(f"%{genre.strip()}%")
                    if genre_conditions:
                        query += " AND (" + " OR ".join(genre_conditions) + ")"
                
                if filters.get('year_from'):
                    query += " AND year >= ?"
                    params.append(filters['year_from'])
                
                if filters.get('year_to'):
                    query += " AND year <= ?"
                    params.append(filters['year_to'])
                
                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                cursor = conn.execute(query, params)
                count = cursor.fetchone()[0]
                conn.close()
                return count
                
        except Exception as e:
            logger.error(f"Error getting series count: {e}")
            return 0

    def get_series_list(self, filters: Dict[str, Any], page: int, limit: int) -> List[Dict[str, Any]]:
        """Get paginated list of series matching filters"""
        global home, logger, ui
        try:
            media_data = {}
            skip_sorting = False  # Flag to determine if we should skip sorting
            preserve_media_order = False  # Flag to preserve media_data order
            
            if filters.get('category'):
                cat = filters.get('category')
                if cat == 'recent':
                    data = ui.media_data.fetch_recently_added()
                    media_data = dict(data)
                    skip_sorting = True  # Don't sort recent items
                    preserve_media_order = True  # Preserve media_data order
                elif cat == 'history':
                    data = ui.media_data.fetch_recently_accessed()
                    media_data = dict(data)
                    skip_sorting = True  # Don't sort history items
                    preserve_media_order = True  # Preserve media_data order
                elif cat == 'available':
                    data = ui.media_data.fetch_all_available()
                    media_data = dict(data)
                else:
                    # For other categories, we'll filter using the Video table
                    # Don't fetch media_data for database categories
                    pass

            # Handle recent and history with preserved order
            if preserve_media_order and media_data:
                # Get the ordered list of db_titles from media_data
                ordered_db_titles = list(media_data.keys())
                
                # Apply pagination to the ordered list
                offset = (page - 1) * limit
                paginated_db_titles = ordered_db_titles[offset:offset + limit]
                
                if not paginated_db_titles:
                    return []
                
                # Build query to fetch only the paginated items in the correct order
                placeholders = ','.join(['?' for _ in paginated_db_titles])
                query = f"""
                SELECT id, title, english_title, year, episodes, score, summary, 
                       image_poster_large, genres, type, popularity, rank, db_title
                FROM series_info 
                WHERE db_title IN ({placeholders})
                """
                
                params = paginated_db_titles[:]
                
                # Add other filter conditions (except category since we're already filtering by media_data)
                if filters.get('search'):
                    query += " AND (title LIKE ? OR english_title LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
                
                if filters.get('type'):
                    query += " AND type = ?"
                    params.append(filters['type'])
                
                if filters.get('genres'):
                    genres = filters['genres'].split(',')
                    genre_conditions = []
                    for genre in genres:
                        genre_conditions.append("genres LIKE ?")
                        params.append(f"%{genre.strip()}%")
                    if genre_conditions:
                        query += " AND (" + " OR ".join(genre_conditions) + ")"
                
                if filters.get('year_from'):
                    query += " AND year >= ?"
                    params.append(filters['year_from'])
                
                if filters.get('year_to'):
                    query += " AND year <= ?"
                    params.append(filters['year_to'])
                
                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Create a dictionary for quick lookup
                series_dict = {}
                for row in rows:
                    db_title = row[12] or ''
                    series_dict[db_title] = {
                        'id': row[0],
                        'title': row[1] or '',
                        'english_title': row[2] or '',
                        'year': row[3] or '',
                        'episodes': row[4] or '',
                        'score': float(row[5]) if row[5] else 0,
                        'summary': row[6] or '',
                        'image_poster_large': row[7] or '',
                        'genres': row[8] or '',
                        'type': row[9] or '',
                        'popularity': row[10] or '',
                        'rank': row[11] or ''
                    }
                    
                    # Parse genres into list
                    if series_dict[db_title]['genres']:
                        series_dict[db_title]['genres_list'] = [g.strip() for g in series_dict[db_title]['genres'].split(',')]
                    else:
                        series_dict[db_title]['genres_list'] = []
                
                # Build the final list in the correct order
                series_list = []
                for db_title in paginated_db_titles:
                    if db_title in series_dict:
                        series_list.append(series_dict[db_title])
                
                conn.close()
                return series_list
                
            else:
                # Original logic for other categories
                offset = (page - 1) * limit
                
                # Determine if we need to filter by Video table category
                need_category_filter = (filters.get('category') and 
                                       filters['category'] not in ['recent', 'history', 'available'])
                
                # Base query - always from series_info only
                query = """
                SELECT id, title, english_title, year, episodes, score, summary, 
                       image_poster_large, genres, type, popularity, rank, db_title
                FROM series_info WHERE 1=1
                """
                
                params = []
                
                # Add category filter using EXISTS subquery - note the capital 'Category'
                if need_category_filter:
                    query += " AND EXISTS (SELECT 1 FROM Video v WHERE v.Title = series_info.db_title AND lower(v.Category) = ?)"
                    params.append(filters['category'])
                
                # Add other filter conditions
                if filters.get('search'):
                    query += " AND (title LIKE ? OR english_title LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
                
                if filters.get('type'):
                    query += " AND type = ?"
                    params.append(filters['type'])
                
                if filters.get('genres'):
                    genres = filters['genres'].split(',')
                    genre_conditions = []
                    for genre in genres:
                        genre_conditions.append("genres LIKE ?")
                        params.append(f"%{genre.strip()}%")
                    if genre_conditions:
                        query += " AND (" + " OR ".join(genre_conditions) + ")"
                
                if filters.get('year_from'):
                    query += " AND year >= ?"
                    params.append(filters['year_from'])
                
                if filters.get('year_to'):
                    query += " AND year <= ?"
                    params.append(filters['year_to'])
                
                # Add sorting only if not skipping (i.e., not recent or history)
                if not skip_sorting:
                    sort_field = filters.get('sort', 'title')
                    order = filters.get('order', 'asc').upper()
                    
                    # Map sort fields to database columns
                    sort_mapping = {
                        'title': 'title',
                        'year': 'year',
                        'score': 'score',
                        'popularity': 'popularity',
                        'rank': 'rank'
                    }
                    
                    db_sort_field = sort_mapping.get(sort_field, 'title')
                    query += f" ORDER BY {db_sort_field} {order}"
                
                # Add pagination
                query += " LIMIT ? OFFSET ?"
                params.extend([str(limit), str(offset)])
                
                conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                series_list = []
                for row in rows:
                    series = {
                        'id': row[0],
                        'title': row[1] or '',
                        'english_title': row[2] or '',
                        'year': row[3] or '',
                        'episodes': row[4] or '',
                        'score': float(row[5]) if row[5] else 0,
                        'summary': row[6] or '',
                        'image_poster_large': row[7] or '',
                        'genres': row[8] or '',
                        'type': row[9] or '',
                        'popularity': row[10] or '',
                        'rank': row[11] or ''
                    }
                    
                    db_title = row[12] or ''
                    # Parse genres into list
                    if series['genres']:
                        series['genres_list'] = [g.strip() for g in series['genres'].split(',')]
                    else:
                        series['genres_list'] = []
                    
                    # Apply media_data filtering for special categories
                    if media_data and media_data.get(db_title):
                        series_list.append(series)
                    elif media_data:
                        pass  # Skip if not in media_data
                    else:
                        # For database category filtering, add all results
                        series_list.append(series)
                
                conn.close()
                return series_list
                
        except Exception as e:
            logger.error(f"Error getting series list: {e}")
            return []

    def generate_series_cards_html(self, series_list: List[Dict[str, Any]]) -> str:
        """Generate HTML for series cards matching your template structure"""
        if not series_list:
            return '''
                        <div class="empty-state">
                            <h3>No series found</h3>
                            <p>Try adjusting your filters or search terms to find more results.</p>
                            <button type="button" class="btn btn-secondary js-clear-filters">
                                <span class="btn-icon">✖️</span>
                                Clear All Filters
                            </button>
                        </div>'''
        
        cards_html = []
        
        for series in series_list:
            series_id = series.get('id', '')
            title = series.get('title', 'Unknown Title')
            english_title = series.get('english_title', '')
            year = series.get('year', '')
            episodes = series.get('episodes', '')
            score = series.get('score', 0)
            summary = series.get('summary', '')
            poster_url = series.get('image_poster_large', '')
            genres_list = series.get('genres_list', [])
            series_type = series.get('type', '')
            
            # Format score
            score_display = f"{score:.1f}" if score and score > 0 else "N/A"
            
            # Format meta info
            meta_parts = []
            if year:
                meta_parts.append(str(year))
            if episodes:
                meta_parts.append(f"{episodes} episodes")
            if series_type:
                meta_parts.append(series_type.title())
            meta_text = " • ".join(meta_parts)
            
            # Generate genre tags
            genre_tags = ""
            if genres_list:
                displayed_genres = genres_list[:4]
                for genre in displayed_genres:
                    genre_tags += f'<span class="genre-tag">{genre}</span>'
                if len(genres_list) > 4:
                    remaining = len(genres_list) - 4
                    genre_tags += f'<span class="genre-tag">+{remaining} more</span>'
            
            # Truncate summary
            # summary_display = summary[:150] + "..." if len(summary) > 150 else summary
            summary_display = summary
            # Poster image with proper error handling
            if poster_url:
                poster_html = f'''<img src="{poster_url}" alt="{title} poster" loading="lazy" 
                                      onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                 <div class="no-image" style="display:none;">No Image</div>'''
            else:
                poster_html = '<div class="no-image">No Image</div>'
            
            # Generate card HTML matching your CSS structure
            card_html = f'''
                        <div class="series-card" data-series-id="{series_id}" tabindex="0">
                            <div class="series-poster">
                                {poster_html}
                                <div class="series-score">{score_display}</div>
                            </div>
                            <div class="series-info">
                                <h3 class="series-title">{title}</h3>
                                {f'<div class="series-english">{english_title}</div>' if english_title else ''}
                                {f'<div class="series-meta">{meta_text}</div>' if meta_text else ''}
                                <div class="series-genres">{genre_tags}</div>
                                {f'<div class="series-summary">{summary_display}</div>' if summary_display else ''}
                            </div>
                        </div>'''
            
            cards_html.append(card_html)
        
        return '\n'.join(cards_html)

    def generate_pagination_html(self, current_page: int, total_pages: int, base_url: str) -> str:
        """Generate pagination HTML matching your template structure"""
        if total_pages <= 1:
            return ""
        
        html_parts = []
        
        # Previous button
        if current_page > 1:
            prev_url = f"{base_url}&page={current_page - 1}"
            html_parts.append(f'<a href="{prev_url}" class="pagination-link">← Previous</a>')
        else:
            html_parts.append('<span class="pagination-link disabled">← Previous</span>')
        
        # Page numbers
        start_page = max(1, current_page - 2)
        end_page = min(total_pages, current_page + 2)
        
        if start_page > 1:
            html_parts.append(f'<a href="{base_url}&page=1" class="pagination-link">1</a>')
            if start_page > 2:
                html_parts.append('<span class="pagination-ellipsis">...</span>')
        
        for page_num in range(start_page, end_page + 1):
            if page_num == current_page:
                html_parts.append(f'<span class="pagination-link current">{page_num}</span>')
            else:
                page_url = f"{base_url}&page={page_num}"
                html_parts.append(f'<a href="{page_url}" class="pagination-link">{page_num}</a>')
        
        if end_page < total_pages:
            if end_page < total_pages - 1:
                html_parts.append('<span class="pagination-ellipsis">...</span>')
            html_parts.append(f'<a href="{base_url}&page={total_pages}" class="pagination-link">{total_pages}</a>')
        
        # Next button
        if current_page < total_pages:
            next_url = f"{base_url}&page={current_page + 1}"
            html_parts.append(f'<a href="{next_url}" class="pagination-link">Next →</a>')
        else:
            html_parts.append('<span class="pagination-link disabled">Next →</span>')
        
        return '\n                    '.join(html_parts)

    def build_base_url(self, filters: Dict[str, Any]) -> str:
        """Build base URL for pagination"""
        params = []
        
        for key, value in filters.items():
            if key != 'page' and value:
                if key == 'genres':
                    # Handle multiple genres for URL
                    for genre in value.split(','):
                        params.append(f"genres={urllib.parse.quote(genre.strip())}")
                else:
                    params.append(f"{key}={urllib.parse.quote(str(value))}")
        
        base_url = "/browse"
        if params:
            base_url += "?" + "&".join(params)
        else:
            base_url += "?"
        
        return base_url

    def handle_admin_request(self):
        """Serve the admin HTML page"""
        try:
            # Read HTML template
            html_path = os.path.join(BASEDIR, 'web', 'admin.html')
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "Admin interface not found")

    
    def handle_admin_data_request(self):
        global home
        """Serve lightweight admin data as JSON - titles and counts only"""
        
        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get title data with episode counts - lightweight query
            cur.execute("""
                SELECT 
                    v.Title,
                    v.Directory,
                    COUNT(*) as episode_count
                FROM Video v
                WHERE v.Title IS NOT NULL AND v.Directory IS NOT NULL
                GROUP BY v.Title, v.Directory
                ORDER BY v.Title
            """)
            title_rows = cur.fetchall()
            
            # Get all series info in one query
            cur.execute("""
                SELECT db_title
                FROM series_info
                WHERE db_title IS NOT NULL
            """)
            series_rows = cur.fetchall()
            series_titles = {row['db_title'] for row in series_rows}
            
            cur.execute("""
                select distinct category
                from series_info
                where category is not null
                and category != ""
            """)
            categories = [row[0].strip() for row in cur.fetchall()]
            cur.execute("""
                select distinct labels
                from series_info
                where labels is not null
                and labels != ""
            """)
            labels_nested_list = [row[0].split(",") for row in cur.fetchall()]
            labels = [
                    label.strip() for label_list in labels_nested_list for label in label_list
                    ]
            conn.close()

            print(labels, categories)
            
            # Filter valid directories and get modification times
            valid_titles = []
            for row in title_rows:
                title = row['Title']
                directory = row['Directory']
                
                # Skip if directory doesn't exist
                if not os.path.exists(directory):
                    continue
                
                try:
                    mtime = os.path.getmtime(directory)
                except (OSError, FileNotFoundError):
                    mtime = 0

                valid_titles.append({
                    'title': title,
                    'directory_hash': self.calc_dir_hash(directory, title),
                    'episode_count': row['episode_count'],
                    'has_series_info': title in series_titles,
                    'mtime': mtime
                })
            
            # Sort by modification time (recent first)
            valid_titles.sort(key=lambda x: x['mtime'], reverse=True)
            
            valid_response = {
                        "available_categories": categories,
                        "available_labels": labels,
                        "titles": valid_titles
                    }
            response = json.dumps(valid_response, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Admin data error: {str(e)}")
            self.send_error(500, f"Database error: {str(e)}")

    def calc_dir_hash(self, directory, title):
        directory_h = bytes(f"{directory}-{title}", 'utf-8')
        h = hashlib.sha256(directory_h)
        hash_val = h.hexdigest()
        return hash_val
        
    def handle_title_details_request(self, title, directory_hash):
        global home
        """Serve detailed episode data for a specific title"""
        
        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get episodes for this title
            cur.execute("""
                SELECT 
                    EP_NAME,
                    Path,
                    EPN,
                    Directory
                FROM Video 
                WHERE Title = ?
                ORDER BY EPN
            """, (title,))
            episode_rows = [
                    row for row in cur.fetchall() if self.calc_dir_hash(row['Directory'], title) == directory_hash
                    ]
            
            # Get series info for this title
            cur.execute("""
                SELECT 
                    db_title,
                    title,
                    english_title,
                    year,
                    episodes,
                    score,
                    rank,
                    popularity,
                    type,
                    duration,
                    genres,
                    external_id,
                    image_poster_large,
                    summary,
                    labels,
                    category,
                    multi_audio,
                    multi_subtitle,
                    ignore,
                    collection_name
                FROM series_info
                WHERE db_title = ?
            """, (title,))
            series_row = cur.fetchone()
            
            conn.close()
            
            # Build episode list
            episodes = []
            for row in episode_rows:
                episodes.append({
                    'name': row['EP_NAME'] or f"Episode {row['EPN']}",
                    'path': row['Path']
                })
            
            # Build response
            response_data = {
                'title': title,
                'episodes': episodes,
                'series_info': dict(series_row) if series_row else None
            }
            
            response = json.dumps(response_data, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Title details error: {str(e)}")
            self.send_error(500, f"Database error: {str(e)}")

    def handle_admin_data_request_legacy(self):
        global home
        """Serve admin data as JSON"""
        
        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Get unique titles with episode counts
            cur.execute("""
                SELECT 
                    v.Title,
                    v.Directory,
                    COUNT(v.Path) as episode_count
                FROM Video v
                GROUP BY v.Title, v.Directory
                ORDER BY v.Title
            """)

            rows  = [(row[0], row[1], row[2]) for row in cur.fetchall() if os.path.exists(row[1])]

            # Sort by when directory was last modified
            # with recent first
            sorted_rows = sorted(
                    rows, key=lambda x: os.path.getmtime(x[1]),
                    reverse=True)
            
            titles_data = []
            for row in sorted_rows:
                title = row[0]
                episode_count = row[2]
                
                # Get episodes for this title
                # Need to fix this, very in-efficient
                # To fetch data in 1 go
                cur.execute("""
                    SELECT EP_NAME, Path, EPN 
                    FROM Video 
                    WHERE Title = ? 
                    ORDER BY EPN
                """, (title,))
                
                episodes = []
                for ep_row in cur.fetchall():
                    episodes.append({
                        'name': ep_row['EP_NAME'] or f"Episode {ep_row['EPN']}",
                        'path': ep_row['Path']
                    })
                
                # Check if series info exists
                cur.execute("SELECT * FROM series_info WHERE db_title = ?", (title,))
                series_row = cur.fetchone()
                
                title_data = {
                    'title': title,
                    'episode_count': episode_count,
                    'has_series_info': series_row is not None,
                    'episodes': episodes,
                    'series_info': dict(series_row) if series_row else None
                }
                
                titles_data.append(title_data)
            
            conn.close()
            
            response = json.dumps(titles_data, indent=2)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Database error: {str(e)}")

    def handle_browse_request(self):
        """Handle /browse GET request without category filter"""
        try:
            # Parse query parameters
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            raw_filters = self.parse_query_params(query_string)
            
            # Validate filters
            filters = self.validate_filters(raw_filters)
            
            # Get page number
            try:
                page = int(raw_filters.get('page', 1))
                page = max(1, page)
            except (ValueError, TypeError):
                page = 1
            
            limit = 20  # Items per page
            
            # Get series data from database
            total_count = self.get_series_count(filters)
            series_list = self.get_series_list(filters, page, limit)
            
            # Calculate pagination
            total_pages = (total_count + limit - 1) // limit
            results_start = (page - 1) * limit + 1
            results_end = min(page * limit, total_count)
            
            # Generate HTML components
            series_cards_html = self.generate_series_cards_html(series_list)
            filter_options = self.generate_filter_options(filters)
            selected_attrs = self.generate_selected_attributes(filters)
            base_url = self.build_base_url(filters)
            pagination_html = self.generate_pagination_html(page, total_pages, base_url)
            
            # Read HTML template
            html_path = os.path.join(BASEDIR, 'web', 'browse.html')
            with open(html_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # Replace all template placeholders
            replacements = {
                '$search': filters.get('search', ''),
                '$category_options': filter_options['category_options'],  # Empty string
                '$genre_options': filter_options['genre_options'],
                '$type_options': filter_options['type_options'],
                '$year_from_options': filter_options['year_from_options'],
                '$year_to_options': filter_options['year_to_options'],
                '$results_start': str(results_start),
                '$results_end': str(results_end),
                '$total_count': str(total_count),
                '$series_cards': series_cards_html,
                '$pagination_html': pagination_html
            }
            
            # Add sort/order selected attributes
            replacements.update({f'${k}': v for k, v in selected_attrs.items()})
            
            # Replace all placeholders in template
            html_content = html_template
            for placeholder, value in replacements.items():
                html_content = html_content.replace(placeholder, value)
            
            # Send response
            html_bytes = html_content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_bytes)))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(html_bytes)
            
        except FileNotFoundError:
            logger.error("browse.html template not found")
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Template not found')
            
        except Exception as e:
            logger.error(f"Error handling browse request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal server error')

    def do_POST(self):
        if self.path == '/series-update':
            self.handle_series_update()
        elif self.path.startswith('/title-details'):
            content = self.rfile.read(int(self.headers['Content-Length']))
            if isinstance(content, bytes):
                content = str(content, 'utf-8')
            content = json.loads(content)
            title = content.get("title")
            directory_hash = content.get("directory_hash")
            if title and directory_hash:
                self.handle_title_details_request(title, directory_hash)
            else:
                self.send_error(400, "Title parameter required")
        else:
            self.do_init_function(type_request='post')

    def handle_series_update(self):
        """Handle admin update requests - JSON only"""
        try:
            # Get content length and read the data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data only
            data = json.loads(post_data.decode('utf-8'))
            print("JSON data:", data)
            
            action = data.get('action', '')
            print("Action:", action)
            print("Data:", data)
            
            if action == 'update_title':
                result = self.update_single_title(data)
            elif action == 'update_single_path':
                result = self.update_single_path(data)
            elif action == 'update_multiple_paths':
                result = self.update_multiple_paths(data)
            elif action == 'bulk_update':
                result = self.bulk_update_titles(data.get('updates', []))
            else:
                result = {'success': False, 'error': 'Invalid action'}
            
            # Send response
            response = json.dumps(result)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            print(f"Error in handle_admin_update: {e}")
            import traceback
            traceback.print_exc()
            
            error_response = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_response.encode('utf-8'))

    def bulk_update_titles(self, bulk_data):
        global ui, logger
        results = []
        for data in bulk_data:
            results.append(self.do_bulk_update_titles(data))
        
        for res in results:
            out_image = res.get('out_image')
            if out_image and out_image.startswith('/'):
                poster_name = res.get('out_image').rsplit('/', 1)[-1]
                img_path = os.path.join(ui.anime_info_fetcher.thumbnail_dir, poster_name)
                img_url = res.get('input_image_poster_large')
                if img_url and img_url.startswith('http'):
                    logger.info(f"fetching: {img_url} -> saving to: {img_path}")
                    ui.vnt.get(img_url, out=img_path)

        success_count = sum(1 for r in results if r.get('success'))
        
        return {
            'success': success_count == len(bulk_data),
            'message': f'{success_count}/{len(bulk_data)} titles updated successfully',
            'results': results
        }

    def do_bulk_update_titles(self, data):
        """Update a single title with bulk update fields and insert series info if not exists"""
        global home, logger

        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            title = data.get('title', '').strip()
            directory_hash = data.get('directory_hash', '').strip()
            
            if not title or not directory_hash:
                return {'success': False, 'error': 'Title and directory_hash are required'}
            
            updates_made = []
            
            # Verify the title exists in Video table with matching directory hash
            cur.execute("""
                SELECT DISTINCT Title, Directory
                FROM Video 
                WHERE Title = ?
            """, (title,))
            
            video_rows = cur.fetchall()
            print(video_rows)
            title_exists = False
            
            directory_list = [
                    row['Directory'] for row in video_rows if self.calc_dir_hash(row['Directory'], row['Title']) == directory_hash
                    ]
            
            if not directory_list:
                return {'success': False, 'error': f'Title "{title}" with matching directory hash not found'}

            if len(directory_list) > 1:
                print(directory_list)
                return {'success': False, 'error': f'Title "{title}" has  inconsistent number of directories'}
            

            # Prepare series_info updates
            series_fields = {}
            
            # Process bulk update fields directly
            category = data.get('category', '').strip()
            if category and len(category) < 50:
                series_fields['category'] = category.lower()
            
            collection_name = data.get('collection_name', '').strip()
            if collection_name:
                series_fields['collection_name'] = collection_name
            
            labels = data.get('labels', '').strip()
            if labels and len(labels) < 100:
                series_fields['labels'] = labels.lower()
            
            input_image_poster_large = ""
            image_poster_large = data.get('image_poster_large', '').strip()
            if image_poster_large:
                series_fields['image_poster_large'] = image_poster_large
                input_image_poster_large = image_poster_large
            
            # Handle ignore field
            ignore_value = data.get('ignore')
            if ignore_value in ['yes', 'no']:
                series_fields['ignore'] = ignore_value
            
            # Only proceed if we have fields to update
            if not series_fields:
                return {'success': True, 'message': 'No valid fields to update'}
            series_fields["directory"] = directory_list[0]
            
            logger.info(f"Bulk updating series info for: '{title}'")
            logger.info(f"Series updates: {series_fields}")
            
            # Check if series_info exists
            cur.execute("SELECT id, image_poster_large FROM series_info WHERE db_title = ?", (title,))
            result = cur.fetchone()
            series_id = ""
            out_image = ""
            if result:
                # Update existing record
                series_id = result[0]
                image_poster_large = result[1]
                input_image_url = series_fields.get("image_poster_large")
                if input_image_url and input_image_url.startswith('http'):
                    img_name = f"poster-{series_id}.jpg"
                    series_fields["image_poster_large"] = f"/images/{img_name}"
                    out_image= series_fields["image_poster_large"]
                    if image_poster_large and image_poster_large.startswith('/images/poster-'):
                        img_name = image_poster_large.rsplit('/', 1)[-1]
                        poster_path = os.path.join(ui.anime_info_fetcher.thumbnail_dir, img_name)
                        if os.path.exists(poster_path):
                            os.remove(poster_path)
                set_clause = ', '.join([f"{k} = ?" for k in series_fields.keys()])
                values = list(series_fields.values()) + [title]
                cur.execute(f"UPDATE series_info SET {set_clause} WHERE db_title = ?", values)
                affected_rows = cur.rowcount
                if affected_rows > 0:
                    updates_made.append(f"Updated series information for '{title}'")
                else:
                    updates_made.append(f"No changes made to '{title}' (values may be identical)")
            else:
                # Insert new record with db_title and provided fields
                series_fields['db_title'] = title
                series_fields['title'] = title
                series_id = str(uuid.uuid4())
                series_fields['id'] = series_id 

                if series_fields.get("image_poster_large"):
                    img_name = f"poster-{series_id}.jpg"
                    series_fields["image_poster_large"] = f"/images/{img_name}"
                    out_image= series_fields["image_poster_large"]

                
                columns = ', '.join(series_fields.keys())
                placeholders = ', '.join(['?' for _ in series_fields])
                values = list(series_fields.values())
                
                cur.execute(f"INSERT INTO series_info ({columns}) VALUES ({placeholders})", values)
                updates_made.append(f"Created new series information for '{title}'")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '; '.join(updates_made) if updates_made else 'No changes made',
                'title': title,
                'out_image': out_image,
                'input_image_poster_large': input_image_poster_large
            }
            
        except Exception as e:
            print(f"Error in update_single_title_bulk: {e}")
            import traceback
            traceback.print_exc()
            
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {
                'success': False, 
                'error': str(e),
                'title': data.get('title', 'Unknown')
            }

    def update_single_title(self, data):
        """Update a single title and its episodes"""
        global home, logger

        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            original_title = data.get('original_title', '').strip()
            new_title = data.get('new_title', '').strip()
            directory_hash = data.get('directory_hash', '').strip()
            
            updates_made = []
            update_path_count = 0
            
            # Update Video table if new title is provided
            if new_title and len(new_title) > 3 and new_title != original_title:
                # Get episodes for this title
                cur.execute("""
                    SELECT 
                        EP_NAME,
                        Path,
                        EPN,
                        Directory
                    FROM Video 
                    WHERE Title = ?
                    ORDER BY EPN
                """, (original_title,))
                episode_rows = [
                        row['Path'] for row in cur.fetchall() if self.calc_dir_hash(row['Directory'], original_title) == directory_hash
                        ]

                for path in episode_rows:
                    query = "update video set Title = ? where Path = ?"
                    cur.execute(query, (new_title, path))

                    affected_rows = cur.rowcount
                    if affected_rows > 0:
                        update_path_count = update_path_count + 1

            if update_path_count > 0:
                updates_made.append(f"Updated title from '{original_title}' to '{new_title}' for {update_path_count} episodes")
                try:
                    cur.execute("""
                        update series_info
                        set db_title = ?
                        where db_title = ?
                    """, (new_title, original_title))
                except sqlite3.IntegrityError as e:
                    # Check if it's a unique constraint error on db_title
                    if "UNIQUE constraint failed" in str(e) and "db_title" in str(e):
                        logger.error(f"Error: {str(e)}, db_title = {new_title} already exists")
            else:
                updates_made.append(f"No update for {original_title}")

            
            # Update series_info
            series_fields = {
                'title': data.get('display_title', '').strip(),
                'english_title': data.get('english_title', '').strip(),
                'year': data.get('year', '').strip(),
                'episodes': data.get('episodes', '').strip(),
                'score': data.get('score', '').strip(),
                'rank': data.get('rank', '').strip(),
                'popularity': data.get('popularity', '').strip(),
                'type': data.get('type', '').strip(),
                'duration': data.get('duration', '').strip(),
                'genres': data.get('genres', '').strip(),
                'external_id': data.get('external_id', '').strip(),
                'image_poster_large': data.get('image_poster', '').strip(),
                'summary': data.get('summary', '').strip(),
                'collection_name': data.get('collection_name', '').strip(),
                'labels': data.get('labels', '').strip(),
                'category': data.get('category', '').strip()
            }

            ignore_series = data.get('multi_audio')
            if ignore_series in ['yes', 'no']:
                series_fields['ignore'] = ignore_series

            multi_sub = data.get("multi_subtitle")
            if multi_sub in ['yes', 'no']:
                series_fields["multi_subtitle"] = multi_sub

            multi_aud = data.get("multi_audio")
            if multi_aud in ['yes', 'no']:
                series_fields["multi_audio"] = multi_aud

            labels = data.get("labels")
            if labels and len(labels) < 100:
                series_fields["labels"] = labels.strip().lower()

            category = data.get("category")
            if category and len(category) < 10:
                series_fields["category"] = category.strip().lower()
            
            # Filter out empty fields
            series_updates = {k: v for k, v in series_fields.items() if v}
            
            if series_updates:
                # Use the new title if provided, otherwise use original
                target_title = new_title if new_title else original_title
                
                print(f"Updating series info for: '{target_title}'")
                print(f"Series updates: {series_updates}")
                
                # Check if series_info exists
                cur.execute("SELECT COUNT(*) FROM series_info WHERE db_title = ?", (target_title,))
                exists = cur.fetchone()[0] > 0
                
                if exists:
                    # Update existing record
                    set_clause = ', '.join([f"{k} = ?" for k in series_updates.keys()])
                    values = list(series_updates.values()) + [target_title]
                    cur.execute(f"UPDATE series_info SET {set_clause} WHERE db_title = ?", values)
                    affected_rows = cur.rowcount
                    if affected_rows > 0:
                        updates_made.append("Updated existing series information")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': '; '.join(updates_made) if updates_made else 'No changes made'
            }
            
        except Exception as e:
            print(f"Error in update_single_title: {e}")
            import traceback
            traceback.print_exc()
            
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {'success': False, 'error': str(e)}

    def update_single_path(self, data):
        """Update title for a single video path"""
        global home

        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cur = conn.cursor()
            
            video_path = data.get('video_path', '').strip()
            new_title = data.get('new_title', '').strip()
            
            print(f"Updating single path: '{video_path}' -> '{new_title}'")
            
            if not video_path or not new_title:
                return {'success': False, 'error': 'Video path and new title are required'}
            
            # Update the specific video file
            cur.execute("UPDATE Video SET Title = ? WHERE Path = ?", (new_title, video_path))
            
            if cur.rowcount == 0:
                return {'success': False, 'error': 'Video file not found'}
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f"Successfully updated episode title to '{new_title}'"
            }
            
        except Exception as e:
            print(f"Error in update_single_path: {e}")
            import traceback
            traceback.print_exc()
            
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {'success': False, 'error': f"Database error: {str(e)}"}

    def update_multiple_paths(self, data):
        """Update title for multiple video paths"""
        global home

        try:
            conn = sqlite3.connect(os.path.join(home, 'VideoDB', 'Video.db'))
            cur = conn.cursor()
            
            # Handle video_paths - now expecting array directly
            video_paths = data.get('video_paths', [])
            
            # Ensure it's a list
            if not isinstance(video_paths, list):
                print(f"Warning: video_paths is not a list: {type(video_paths)} - {repr(video_paths)}")
                video_paths = []
                
            new_title = data.get('new_title', '').strip()
            
            print(f"Updating multiple paths: {len(video_paths)} files -> '{new_title}'")
            print(f"Video paths: {video_paths}")
            
            if not video_paths or not new_title:
                return {'success': False, 'error': 'Video paths and new title are required'}
            
            # Update all selected video files
            placeholders = ','.join(['?' for _ in video_paths])
            cur.execute(f"UPDATE Video SET Title = ? WHERE Path IN ({placeholders})", 
                       [new_title] + video_paths)
            
            updated_count = cur.rowcount
            
            if updated_count == 0:
                return {'success': False, 'error': 'No video files were updated'}
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f"Successfully updated {updated_count} episodes to '{new_title}'"
            }
            
        except Exception as e:
            print(f"Error in update_multiple_paths: {e}")
            import traceback
            traceback.print_exc()
            
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return {'success': False, 'error': f"Database error: {str(e)}"}

    def process_url(self, nm, get_bytes, status=None):
        global ui, logger
        user_agent = self.headers['User-Agent']
        range_hdr = self.headers['Range']
        upper_range = None
        lower_range = None
        try:
            if range_hdr:
                if range_hdr.startswith('bytes='):
                    range_hdr = range_hdr.replace('bytes=', '', 1)
                if '-' in range_hdr:
                    if not range_hdr.endswith('-'):
                        low, up = range_hdr.split('-')
                        lower_range = int(low)
                        upper_range = int(up)
                        print(lower_range, upper_range)
                    else:
                        lower_range = int(range_hdr.replace('-', ''))
                else:
                    lower_range = int(range_hdr)
        except Exception as err_val:
            print(err_val, '--495--')

        if lower_range is not None:
            get_bytes = lower_range
        allow_chunks = False
        logger.info('Range: {0}-{1}'.format(get_bytes, upper_range))
        content_range = True
        if user_agent:
            user_agent = user_agent.lower()
            user_agent = user_agent.strip()
        else:
            user_agent = 'mpv'
        print('user_agent=', user_agent)
        if user_agent.startswith('mpv'):
            allow_chunks = True
            logger.info('allow-chunks={0}'.format(allow_chunks))
        if nm.startswith('http'):
            netloc = urlparse(nm).netloc
            torrent_stream_ip = ui.local_ip + ':' + str(ui.local_port)
            if netloc == torrent_stream_ip:
                uid = str(uuid.uuid4())
                if nm.endswith('/'):
                    nm = '{}&auth_token={}'.format(nm, uid)
                else:
                    nm = '{}/&auth_token={}'.format(nm, uid)
                if len(ui.allowed_access_tokens) > 10:
                    del ui.allowed_access_tokens[0]
                ui.allowed_access_tokens.append(uid)
            self.send_response(303)
            self.send_header('Location', nm)
            self.send_header('Connection', 'close')
            self.end_headers()
            logger.debug('\nRedirecting...{0}\n'.format(nm))
        else:
            if '.' in nm:
                nm_ext = nm.rsplit('.', 1)[1]
            else:
                nm_ext = 'nothing'
            self.proc_req = False
            if get_bytes:
                self.send_response(206)
            else:
                self.send_response(200)
                    
            if nm_ext == 'mp3':
                self.send_header('Content-type', 'audio/mpeg') 
            else:
                self.send_header('Content-type', 'video/mp4')
            size = os.stat(nm).st_size

            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(size))
            if get_bytes or upper_range is not None:
                if upper_range is None:
                    upper_range = size - 1
                logger.info('...sending range...{0}-{1}/{2}'.format(get_bytes, upper_range, size))
                self.send_header(
                    'Content-Range', 'bytes ' +str(get_bytes)+'-'+str(upper_range)+'/'+str(size))
            if get_bytes and 'firefox' in user_agent:
                self.send_header('Connection', 'keep-alive')
            else:
                self.send_header('Connection', 'close')
            self.end_headers()
            
            print(get_bytes, '--get--bytes--', nm_ext)
            upspeed = 1024
            upload_gap = 0
            if ui.setuploadspeed:
                upspeed = ui.setuploadspeed
                upload_gap = 1

            t = 0
            end_read = False
            content = None
            content_count = 0
            with open(nm, 'rb') as f:
                if get_bytes and t == 0:
                        f.seek(get_bytes)
                        t = 1
                        print('seeking')
                        if upper_range is not None:
                            if upper_range != size - 1:
                                content = f.read(upper_range-get_bytes+1)
                                self.wfile.write(content)
                                self.wfile.flush()
                                end_read = True
                if not end_read:
                    content = f.read(1024*upspeed)
                    content_count += 1024*upspeed
                while(content) and not end_read:
                    try:
                        self.wfile.write(content)
                        self.wfile.flush()
                    except Exception as e:
                        if 'Errno 104' in str(e):
                            logger.info(e)
                            break
                    content = f.read(1024*upspeed)
                    content_count += 1024*upspeed
                    if upload_gap:
                        time.sleep(upload_gap)
            print('data sent')
            self.proc_req = True

    def triggerBookmark(self, row):
        global ui

        arg_dict = ui.get_parameters_value(
            s='site', o='opt', sn='siteName', n='name'
            )
        site = arg_dict['site']
        opt = arg_dict['opt']
        siteName = arg_dict['siteName']
        name = arg_dict['name']
        video_local_stream = ui.video_local_stream

        tmp = ''
        if row:
            tmp = site+'&'+opt+'&'+siteName+'&'+name+'&'+str(video_local_stream)
        else:
            tmp = ''+'&'+''+'&'+''+'&'+''+'&'+str(video_local_stream)
        return tmp

    def create_option_playlist(self, site, site_option, original_path_name):
        k = ''
        for i in original_path_name:
            dir_hash = None
            i = i.strip()
            old_i = i
            if '	' in i:
                i = i.split('	')[0]
            if site.lower() == 'music': 
                if site_option.lower() == 'directory':
                    dir_m, i = os.path.split(i)
                elif site_option.lower().startswith('playlist'):
                    old_i = old_i.split('\t')[1]
                else:
                    i = old_i
                dir_byte = bytes(old_i, 'utf-8')
                h = hashlib.sha256(dir_byte)
                dir_hash = h.hexdigest()
            elif site.lower() == 'video':
                dir_byte = bytes(old_i.split('\t')[1], 'utf-8')
                h = hashlib.sha256(dir_byte)
                dir_hash = h.hexdigest()
            if dir_hash:
                i = i+'::::'+dir_hash+'\n'
            else:
                i = i+'\n'
            k = k+i
        return k

    def write_to_tmp_playlist(self, epnArrList, _new_epnArrList=None):
        pass

    def create_playlist(
            self, site, site_option, name, epnArrList, new_video_local_stream, 
            siteName, my_ipaddress, shuffle_list, play_id):
        global logger, html_default_arr, getdb
        old_name = []
        _new_epnArrList = []
        self.playlist_shuffle_list[:] = []
        n_url_name = 'unknown'
        if self.path.endswith('.pls'):
            pls_txt = '[playlist]'
        elif self.path.endswith('.htm') or self.path.endswith('.html'):
            pls_txt = '<ol id="playlist">'
        else:
            pls_txt = '#EXTM3U\n'
        #pls_txt = '#EXTM3U\n'
        new_index = 0
        if shuffle_list:
            epnArrList = random.sample(epnArrList, len(epnArrList))
            if ui.remote_control and ui.remote_control_field:
                self.playlist_shuffle_list = epnArrList.copy()
        site_pls = False
        if (site.lower().startswith('playlist') or (site.lower().startswith('music')
                and site_option.lower().startswith('playlist'))):
            site_pls = True
        for  i in range(len(epnArrList)):
            try:
                k = epnArrList[i]
                n_art = k.split('	')[-1]
                if n_art.startswith('http') or n_art.startswith('"http') or n_art.lower() == 'none':
                    n_art = 'NONE'
                book_mark = site+'&'+site_option+'&'+siteName+'&'+n_art+'&'+str(new_video_local_stream)
                if not old_name:
                    old_name.append(n_art)
                    new_index = 0
                else:
                    old_old_name = old_name.pop()
                    if old_old_name == n_art:
                        new_index = new_index + 1
                    else:
                        new_index = 0
                    old_name.append(n_art)
                if site_pls:
                    new_k = k.split('	')[-1]
                    if '##' in k:
                        name = new_k.rsplit('##', 1)[-1]
                        n_art = ""
                n_url_file = getdb.get_file_name_from_bookmark(site, site_option, name, i, epnArrList)
                logger.info(name)
                if (site.lower() == 'video' or site.lower() == 'music' or 
                        site.lower() == 'local' or site.lower().startswith('playlist') 
                        or site.lower() == 'none'):
                    if '	' in k:
                        n_out = k.split('	')[0]
                        if site.lower() == "video" and n_out.startswith("#"):
                            n_out = n_out.replace('#', '✅', 1)
                        elif n_out.startswith('#'):
                            n_out = n_out.replace('#', '', 1)
                        if n_url_file:
                            n_url = n_url_file.replace('"', '')
                        else:
                            n_url = k.split('	')[1].replace('"', '')
                    n_url_name = os.path.basename(n_url)
                    n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
                    n_url = str(n_url_new, 'utf-8')
                    j = 'abs_path='+n_url
                    if site_pls:
                        new_j = k.split('	')[1]
                        if new_j.startswith('abs_path') or new_j.startswith('relative_path'):
                            j = new_j
                            n_url_name = k.split('	')[0]
                else:
                    if '	' in k:
                        n_out = k.split('	')[0]
                        if n_out.startswith('#'):
                            n_out = n_out.replace('#', '', 1)
                        new_name = k.split('	')[1].replace('"', '')
                        if new_name.startswith('#'):
                            new_name = new_name[1:]
                        if n_url_file:
                            n_url = n_url_file.replace('"', '')
                        else:
                            n_url = book_mark+'&'+str(new_index)+'&'+new_name
                    if '&' in n_url:
                        n_url_name = n_url.split('&')[-1]
                    else:
                        n_url_name = os.path.basename(n_url)
                    n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
                    n_url = str(n_url_new, 'utf-8')
                    if n_url_file:
                        j = 'abs_path='+n_url
                    else:
                        j = 'relative_path='+n_url
                #n_out = n_out.replace(' ', '_')

                logger.info('create-playlist----{0}'.format(j))
                n_url = n_url.replace('"', '')
                n_art = n_art.replace('"', '')
                http_val = "http"
                if '_' in n_art:
                    n_art = n_art.replace('_', ' ')
                if '_' in n_out:
                    n_out = n_out.replace('_', ' ')
                if n_art.lower() == 'none':
                    n_art = ''
                if ui.https_media_server:
                    http_val = "https" 
                if play_id:
                    out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'&pl_id='+play_id+'/'+urllib.parse.quote(n_url_name.replace('/', '-'))
                else:
                    out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'/'+urllib.parse.quote(n_url_name.replace('/', '-'))
                if self.path.endswith('.pls'):
                    pls_txt = pls_txt+'\nFile{0}={1}\nTitle{0}={2}-{3}\n'.format(str(i), out, n_art, n_out)
                elif self.path.endswith('.htm') or self.path.endswith('.html'):
                    if site.lower() == 'video':
                        pls_txt = pls_txt+'<li data-mp3="{2}" data-num="{3}"><img src="{4}" width="128">{1}</li>'.format(n_art, n_out, out, str(i+1), out+'.image')
                    else:
                        pls_txt = pls_txt+'<li data-mp3="{2}" data-num="{3}"><img src="{4}" width="128">{0} - {1}</li>'.format(n_art, n_out, out, str(i+1), out+'.image')
                else:
                    if site.lower() == 'video':
                        pls_txt = pls_txt+'#EXTINF:0, {0}\n{1}\n'.format(n_out, out)
                    else:
                        pls_txt = pls_txt+'#EXTINF:0, {0} - {1}\n{2}\n'.format(n_art, n_out, out)
                _new_epnArrList.append(n_out+'	'+j+'	'+n_art)
            except Exception as e:
                print(e)
        if self.path.endswith('.pls'):
            footer = '\nNumberOfEntries='+str(len(epnArrList))+'\n'
            pls_txt = pls_txt+footer
        elif self.path.endswith('.htm') or self.path.endswith('.html'):
            pls_txt = pls_txt+'</ol>'
            playlist_htm = os.path.join(BASEDIR, 'web', 'playlist.html')
            if os.path.exists(playlist_htm):
                play_htm = open_files(playlist_htm, False)
                #print(play_htm)
                pls_txt = re.sub('<ol id="playlist"></ol>', pls_txt, play_htm)
                new_field = ''
                for i in html_default_arr:
                    new_field = new_field+'<option value="{0}">{1}</option>'.format(i.lower(), i)
                new_field = '<select id="site" onchange="siteChange()">{0}</select>'.format(new_field)
                logger.info(new_field)
                pls_txt = pls_txt.replace('<select id="site" onchange="siteChange()"></select>', new_field)
                extra_fields = self.get_extra_fields()
                logger.info(extra_fields)
                pls_txt = re.sub('<div id="site_option" hidden></div>', extra_fields, pls_txt)

        if ui.remote_control and ui.remote_control_field:
            self.write_to_tmp_playlist(epnArrList, _new_epnArrList)

        return pls_txt

    def get_extra_fields(self):
        global html_default_arr, home, ui, logger
        #extra_fields = ''

        extra_fields = 'RemoteField:{0};RemoteControl:{1};Thumbnails:{2};WebControl:{3};categories:{4};'.format(
            ui.remote_control_field, ui.remote_control, ui.show_client_thumbnails, ui.web_control, ",".join(ui.category_array)
            )
        for i in html_default_arr:
            if i.lower() == 'video':
                category_list = ''
                for arr_cat in ui.category_array:
                    category_list = category_list+'Video:'+arr_cat+';'
                extra_fields = extra_fields+'Video:Available;Video:History;Video:Recent;'+category_list
            elif i.lower() == 'music':
                extra_fields = extra_fields+'Music:Artist;Music:Album;Music:Directory;Music:Playlist;'
            elif i.lower().startswith('playlist'):
                home_n = os.path.join(home, 'Playlists')
                criteria = os.listdir(os.path.join(home, 'Playlists'))
                criteria = naturallysorted(criteria)
                for j in criteria:
                    if '.' in j:
                        j = j.rsplit('.', 1)[0]
                    extra_fields = extra_fields+'{0}:{1};'.format(i, j)
            elif i.lower() == 'bookmark':
                home_n = os.path.join(home, 'Bookmark')
                criteria = os.listdir(home_n)
                criteria = naturallysorted(criteria)
                for j in criteria:
                    if '.' in j:
                        j = j.rsplit('.', 1)[0]
                    extra_fields = extra_fields+'{0}:{1};'.format(i, j)
            elif i.lower() == 'subbedanime' or i.lower() == 'dubbedanime':
                plugin_path = os.path.join(home, 'src', 'Plugins', i+'.py')
                if os.path.exists(plugin_path):
                    module = imp.import_module(i, plugin_path)
                    site_var = getattr(module, i)(TMPDIR)
                    if site_var:
                        criteria = site_var.getOptions() 
                        for j in criteria:
                            extra_fields = extra_fields+'{0}:{1};'.format(i, j)
            else:
                extra_fields = extra_fields+'{0}:History;'.format(i)

        last_view_file = os.path.join(home, 'History', 'last_viewed.txt')
        if self.last_view:
            extra_fields = extra_fields+'LastView:{0};'.format(self.last_view[-1])
        elif os.path.exists(last_view_file):
            last_viewed = open(last_view_file).read()
            extra_fields = extra_fields+'LastView:{0};'.format(last_viewed)

        extra_fields = '<div id="site_option" hidden>{0}</div>'.format(extra_fields)
        return extra_fields

    def build_url_from_file_path(self, file_path, file_type):
        file_name = os.path.basename(file_path)
        file_name_saitized = urllib.parse.quote(file_name.replace("/", "-"))
        encoded_path = str(base64.b64encode(bytes(file_path, 'utf-8')), 'utf-8')
        url = f"/abs_path={encoded_path}/{file_name_saitized}"
        if  file_type == "image":
            url = f"{url}.image"
        return url

    def get_the_content(self, path, get_bytes, my_ip_addr=None, play_id=None):
        global ui, home, html_default_arr, logger, getdb
        global site

        if self.path.startswith("/images/"):
            local_image = self.path.rsplit("/", 1)[-1]
            poster_path = os.path.join(ui.anime_info_fetcher.thumbnail_dir, local_image)
            if os.path.exists(poster_path):
                content = open(poster_path, 'rb').read()
            else:
                default_file = os.path.join(ui.home_folder, '480px.default.jpg')
                content = open(default_file, 'rb').read()
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-Length', len(content))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(content)
            except Exception as e:
                print(e)

        arg_dict = ui.get_parameters_value(s='site')
        epnArrList = ui.epn_arr_list.copy()
        site = arg_dict['site']
        self.playlist_shuffle_list[:] = []
        if not my_ip_addr:
            my_ipaddress = ui.local_ip_stream
        else:
            my_ipaddress = my_ip_addr
        if play_id:
            pl_id_val = '&pl_id='+play_id
            if path.endswith(pl_id_val):
                path = path.replace(pl_id_val, '', 1)
        if (path.lower().startswith('stream_continue') 
                or path.lower().startswith('stream_shuffle') 
                or path.lower().startswith('channel.') 
                or path.lower().startswith('channel_sync.')):
            new_arr = []
            n_out = ''
            n_art = ''
            n_url = ''
            n_url_name = 'unknown'
            shuffle_list = False
            if ui.list1.currentItem():
                list1_row = ui.list1.currentRow()
            else:
                list1_row = None

            #book_mark = self.triggerBookmark(list1_row)
            new_epnArrList = [i for i in epnArrList]

            new_arr = [i for i in range(len(epnArrList))]

            if path.startswith('channel'):
                new_arr = new_arr[ui.cur_row:]
                new_epnArrList = new_epnArrList[ui.cur_row:]
                logger.info('{0}++++++++++++++++++{1}'.format(new_arr, new_epnArrList))
            if path.lower().startswith('stream_continue_from_'):
                row_digit = 0
                try:
                    row_digit = int(path.lower().rsplit('_', 1)[1])
                except Exception as err_val:
                    print(err_val, '--bad--request--')
                if row_digit:
                    if len(new_arr) > row_digit:
                        new_arr = new_arr[row_digit:]
                #print(row_digit)
                #print(new_arr)
            if path.lower().startswith('stream_shuffle'):
                shuffle_list = True
                new_arr = random.sample(new_arr, len(new_arr))
                if ui.remote_control and ui.remote_control_field:
                    self.playlist_shuffle_list = [epnArrList[i] for i in new_arr]
            #print(new_arr)
            #print(self.client_address)
            if path.endswith('.html') or path.endswith('.htm'):
                pls_txt = '<ol id="playlist">'
            elif path.endswith('.pls'):
                pls_txt = '[playlist]'
            else:
                pls_txt = '#EXTM3U\n'
            for  i in range(len(new_arr)):
                try:
                    k = new_arr[i]
                    n_url_file = ui.if_file_path_exists_then_play(k, ui.list2, play_now=False)
                    if (site.lower() == 'video' or site.lower() == 'music' or 
                            site.lower() == 'local' or site.lower() == 'playlists' 
                            or site.lower() == 'none' or site.lower() == 'myserver'):
                        if '	' in epnArrList[k]:
                            n_out = epnArrList[k].split('	')[0]
                            if n_out.startswith('#'):
                                n_out = n_out.replace('#', '', 1)
                            if n_url_file:
                                n_url = n_url_file.replace('"', '')
                            else:
                                n_url = epnArrList[k].split('	')[1].replace('"', '')
                            try:
                                n_art_arr = epnArrList[k].split('	')
                                if len(n_art_arr) > 2:
                                    n_art = n_art_arr[2]
                                else:
                                    if ui.list1.currentItem():
                                        n_art = ui.list1.currentItem().text()
                                    else:
                                        n_art = 'NONE'
                            except Exception as e:
                                print(e, '--960--')
                                if ui.list1.currentItem():
                                    n_art = ui.list1.currentItem().text()
                                else:
                                    n_art = 'NONE'
                            if n_art.startswith('http') or n_art.startswith('"http') or n_art.lower() == 'none':
                                if ui.list1.currentItem():
                                    n_art = ui.list1.currentItem().text()
                                else:
                                    n_art = 'NONE'
                        else:
                            n_out = epnArrList[k]
                            if n_out.startswith('#'):
                                n_out = n_out.replace('#', '', 1)
                            if n_url_file:
                                n_url = n_url_file.replace('"', '')
                            else:
                                n_url = epnArrList[k].replace('"', '')
                            try:
                                n_art = ui.list1.currentItem().text()
                            except Exception as e:
                                print(e, '--981--')
                                n_art = 'NONE'
                        n_url_name = os.path.basename(n_url)
                        n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
                        n_url = str(n_url_new, 'utf-8')
                        j = 'abs_path='+n_url
                        if site.lower() == 'playlists':
                            new_j = epnArrList[k].split('	')[1]
                            if new_j.startswith('abs_path') or new_j.startswith('relative_path'):
                                j = new_j
                                n_url_name = epnArrList[k].split('	')[0]
                    else:
                        book_mark = self.triggerBookmark(k+1)
                        if '	' in epnArrList[k]:
                            n_out = epnArrList[k].split('	')[0]
                            if n_out.startswith('#'):
                                n_out = n_out.replace('#', '', 1)
                            new_name = epnArrList[k].split('	')[1].replace('"', '')
                            if new_name.startswith('#'):
                                new_name = new_name[1:]
                            if n_url_file:
                                n_url = n_url_file.replace('"', '')
                            else:
                                n_url = book_mark+'&'+str(k)+'&'+new_name
                            try:
                                n_art = epnArrList[k].split('	')[2]
                            except Exception as e:
                                print(e, '--1003--')
                                if ui.list1.currentItem():
                                    n_art = ui.list1.currentItem().text()
                                else:
                                    n_art = 'NONE'
                            if n_art.startswith('http') or n_art.startswith('"http') or n_art.lower() == 'none':
                                if ui.list1.currentItem():
                                    n_art = ui.list1.currentItem().text()
                                else:
                                    n_art = 'NONE'
                        else:
                            n_out = epnArrList[k]
                            if n_out.startswith('#'):
                                n_out = n_out.replace('#', '', 1)
                            n_out = n_out.replace('"', '')
                            new_name = n_out
                            if new_name.startswith('#'):
                                new_name = new_name[1:]
                            if n_url_file:
                                n_url = n_url_file.replace('"', '')
                            else:
                                n_url = book_mark+'&'+str(k)+'&'+new_name
                            try:
                                n_art = ui.list1.currentItem().text()
                            except Exception as e:
                                print(e, '--1029--')
                                n_art = 'NONE'
                        if '&' in n_url:
                            n_url_name = n_url.split('&')[-1]
                        else:
                            n_url_name = os.path.basename(n_url)
                        logger.info('--n_url_name___::{0}'.format(n_url))
                        n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
                        n_url = str(n_url_new, 'utf-8')
                        if n_url_file:
                            j = 'abs_path='+n_url
                        else:
                            j = 'relative_path='+n_url
                    logger.info('--875---{0}'.format(j))
                    #n_out = n_out.replace(' ', '_')
                    #n_url = n_url.replace('"', '')
                    n_art = n_art.replace('"', '')
                    http_val = "http"
                    if ui.https_media_server:
                        http_val = "https" 
                    if path.startswith('channel'):
                        if path.startswith('channel.'):
                            n_url_name = str(k)
                        else:
                            n_url_name = 'now_playing'
                        n_url = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)
                        n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
                        n_url = str(n_url_new, 'utf-8')
                        j = 'abs_path='+n_url
                    if '_' in n_art:
                        n_art = n_art.replace('_', ' ')
                    if n_art.lower() == 'none':
                        n_art = ''
                    if '_' in n_out:
                        n_out = n_out.replace('_', ' ')
                    if play_id:
                        out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'&pl_id='+play_id+'/'+urllib.parse.quote(n_url_name.replace('/', '-'))
                    else:
                        out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'/'+urllib.parse.quote(n_url_name.replace('/', '-'))
                    if path.endswith('.pls'):
                        pls_txt = pls_txt+'\nFile{0}={1}\nTitle{0}={2}-{3}\n'.format(str(i), out, n_art, n_out)
                    elif path.endswith('.htm') or path.endswith('.html'):
                        if site.lower() == 'video':
                            pls_txt = pls_txt+'<li data-mp3="{2}" data-num="{3}" draggable="true" ondragstart="drag_start(event)" ondragend="drag_end(event)" ondragover="drag_over(event)" ondragleave="drag_leave(event)" ondragenter="drag_enter(event)" ondrop="on_drop(event)" title="{1}">{1}</li>'.format(n_art, n_out, out, str(i+1))
                        else:
                            pls_txt = pls_txt+'<li data-mp3="{2}" data-num="{3}" draggable="true" ondragstart="drag_start(event)" ondragend="drag_end(event)" ondragover="drag_over(event)" ondragleave="drag_leave(event)" ondragenter="drag_enter(event)" ondrop="on_drop(event)" title="{0} - {1}">{0} - {1}</li>'.format(n_art, n_out, out, str(i+1))
                    else:
                        if site.lower() == 'video':
                            pls_txt = pls_txt+'#EXTINF:0, {0}\n{1}\n'.format(n_out, out)
                        else:
                            pls_txt = pls_txt+'#EXTINF:0, {0} - {1}\n{2}\n'.format(n_art, n_out, out)
                    if k == len(epnArrList) - 1:
                        if path.startswith('channel'):
                            n_art = 'Server'
                            n_out = "What I'm playing now"
                            out = out.rsplit('/', 1)[0]
                            out = out + '/server' 
                            if path.endswith('.pls'):
                                pls_txt = pls_txt+'\nFile{0}={1}\nTitle{0}={2}-{3}\n'.format(str(i), out, n_art, n_out)
                            elif path.endswith('.htm') or path.endswith('.html'):
                                pls_txt = pls_txt+'<li data-mp3="{2}">{0} - {1}</li>'.format(n_art, n_out, out)
                            else:
                                pls_txt = pls_txt+'#EXTINF:0, {0} - {1}\n{2}\n'.format(n_art, n_out, out)
                except Exception as e:
                    print(e, '--1081--')
            playlist_file_name = n_art + '.m3u'
            if path.endswith('.pls'):
                footer = '\nNumberOfEntries='+str(len(new_arr))+'\n'
                pls_txt = pls_txt+footer
                playlist_file_name = n_art + '.pls'
            elif path.endswith('.htm') or path.endswith('.html'):
                pls_txt = pls_txt+'</ol>'
                playlist_htm = os.path.join(BASEDIR, 'web', 'playlist.html')
                if os.path.exists(playlist_htm):
                    play_htm = open_files(playlist_htm, False)
                    pls_txt = re.sub('<ol id="playlist"></ol>', pls_txt, play_htm)
                    new_field = ''
                    for i in html_default_arr:
                        new_field = new_field+'<option value="{0}">{1}</option>'.format(i.lower(), i)
                    copy_new_field = new_field
                    new_field = '<select id="site" onchange="siteChange()">{0}</select>'.format(new_field)
                    logger.info(new_field)
                    
                    new_field_select = '<select id="first_select" onchange="siteChangeTop()">{0}</select>'.format(copy_new_field)
                    
                    pls_txt = pls_txt.replace('<select id="site" onchange="siteChange()"></select>', new_field, 1)
                    pls_txt = pls_txt.replace('<select id="first_select" onchange="siteChangeTop()"></select>', new_field_select, 1)
                    
                    extra_fields = self.get_extra_fields()
                    logger.info(extra_fields)
                    pls_txt = re.sub('<div id="site_option" hidden></div>', extra_fields, pls_txt)
            pls_txt = bytes(pls_txt, 'utf-8')
            self.send_response(200)
            #self.send_header('Set-Cookie', 'A=Bcdfgh')
            if path.endswith('.htm') or path.endswith('.html'):
                self.send_header('Content-type', 'text/html; charset=utf-8')
            else:
                self.send_header('Content-type', 'audio/mpegurl')
                self.send_header('Content-Disposition', 'attachment; filename={}'.format(playlist_file_name.encode("utf-8")))
            size = len(pls_txt)
            #size = size - get_bytes
            self.send_header('Content-Length', str(size))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(pls_txt)
            except Exception as e:
                print(e)
            if ui.remote_control and ui.remote_control_field:
                self.write_to_tmp_playlist(epnArrList)
                if self.playlist_shuffle_list and shuffle_list:
                    ui.epn_arr_list = self.playlist_shuffle_list.copy()
                    self.nav_signals.total_navigation('', '', '', shuffle_list)
        elif (path.lower().startswith('channel_sync.')):
            if path.endswith('.html') or path.endswith('.htm'):
                pls_txt = '<ol id="playlist">'
            elif path.endswith('.pls'):
                pls_txt = '[playlist]'
            else:
                pls_txt = '#EXTM3U\n'
            http_val = 'http'
            if ui.https_media_server:
                http_val = "https" 
            n_url = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)
            n_url_name = 'now_playing'
            n_url_new = base64.b64encode(bytes(n_url, 'utf-8'))
            n_url = str(n_url_new, 'utf-8')
            j = 'abs_path='+n_url
            if play_id:
                out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'&pl_id='+play_id+'/'+urllib.parse.quote(n_url_name)
            else:
                out = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)+'/'+j+'/'+urllib.parse.quote(n_url_name)
            n_art = ''
            n_out = ''
            if ui.list1.currentItem():
                n_art = ui.list1.currentItem().text()
                n_out = "Server"
            if epnArrList:
                if '	' in epnArrList[ui.cur_row]:
                    epn_arr = epnArrList[ui.cur_row].strip()
                    length = len(epn_arr.split('	'))
                    if length == 3:
                        n_out, __, n_art = epn_arr.split('	')
                    elif length == 2:
                        n_out, __ = epn_arr.split('	')
                    else:
                        n_out = epn_arr
                else:
                    n_out = epnArrList[ui.cur_row].strip()
                    if not n_art:
                        n_art = 'Not Available'

            if path.endswith('.pls'):
                pls_txt = pls_txt+'\nTitle{0}={1}\nFile{0}={2}\n'.format(str(1), n_art, out)
            elif path.endswith('.htm') or path.endswith('.html'):
                pls_txt = pls_txt+'<li data-mp3="{2}">{0} - {1}</li>'.format(n_art, n_out, out)
            else:
                pls_txt = pls_txt+'#EXTINF:0, {0} - {1}\n{2}\n'.format(n_art, n_out, out)

            if path.endswith('.pls'):
                footer = '\nNumberOfEntries='+str(1)+'\n'
                pls_txt = pls_txt+footer
            elif path.endswith('.htm') or path.endswith('.html'):
                pls_txt = pls_txt+'</ol>'
                playlist_htm = os.path.join(BASEDIR, 'web', 'playlist.html')
                if os.path.exists(playlist_htm):
                    play_htm = open_files(playlist_htm, False)
                    pls_txt = re.sub('<ol id="playlist"></ol>', pls_txt, play_htm)
                    new_field = ''
                    for i in html_default_arr:
                        new_field = new_field+'<option value="{0}">{1}</option>'.format(i.lower(), i)
                    new_field = '<select id="site" onchange="siteChange()">{0}</select>'.format(new_field)
                    logger.info(new_field)
                    pls_txt = pls_txt.replace('<select id="site" onchange="siteChange()"></select>', new_field)
                    extra_fields = self.get_extra_fields()
                    logger.info(extra_fields)
                    pls_txt = re.sub('<div id="site_option" hidden></div>', extra_fields, pls_txt)
            logger.info('pls_txt_channel: '.format(pls_txt))
            pls_txt = bytes(pls_txt, 'utf-8')
            self.send_response(200)
            if path.endswith('.htm') or path.endswith('.html'):
                self.send_header('Content-type', 'text/html; charset=utf-8')
            else:
                self.send_header('Content-type', 'audio/mpegurl')
            size = len(pls_txt)
            self.send_header('Content-Length', str(size))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(pls_txt)
            except Exception as e:
                print(e)
        elif (path.lower().startswith('site=') or path.startswith('get_previous_playlist')
                or path.startswith('get_next_playlist') or path.startswith('get_last_playlist')
                or path.startswith('get_first_playlist')):
            ret_val = None
            get_pls = False
            if path.startswith("site="):
                logger.debug(path)
            elif path.startswith('get_next_playlist'):
                ret_val = ui.navigate_playlist_history.get_next()
                get_pls = True
            elif path.startswith('get_previous_playlist'):
                ret_val = ui.navigate_playlist_history.get_prev()
                get_pls = True
            elif path.startswith('get_last_playlist'):
                ret_val = ui.navigate_playlist_history.get_item()
                get_pls = True
            elif path.startswith('get_first_playlist'):
                ret_val = ui.navigate_playlist_history.get_item(index=0)
                get_pls = True
                
            logger.debug(ret_val)
            if get_pls:
                if ret_val is not None:
                    path = ret_val
                    logger.debug('total={0}::ptr={1}'.format(
                        ui.navigate_playlist_history.get_total, ui.navigate_playlist_history.get_ptr
                        ))
                    logger.debug(ui.navigate_playlist_history.get_list())
                else:
                    path = 'stream_continue.htm'
                
            new_arr = path.split('&')
            logger.info(new_arr)
            st = ''
            st_o = ''
            srch = ''
            srch_exact = False
            shuffle_list = False
            pls_cache = False
            pls_txt = ''
            url_format = 'htm'
            for i in new_arr:
                logger.info(i)
                if i.startswith('site='):
                    st = i.split('=')[-1]
                elif i.startswith('opt='):
                    st_o = i.split('=')[-1]
                elif i.startswith('s='):
                    #srch = i.split('=')[-1]
                    srch = re.search('&s=[^"]*', path).group()
                    srch = srch.replace('&s=', '', 1)
                    if '&exact' in srch:
                        srch = srch.replace('&exact', '')
                    if '&shuffle' in srch:
                        srch = srch.replace('&shuffle', '')
                    if (srch.endswith('.pls') or srch.endswith('.m3u') 
                            or srch.endswith('.htm') or srch.endswith('.html')):
                        if srch.endswith('.m3u'):
                            url_format = 'm3u'
                        elif srch.endswith('.pls'):
                            url_format = 'pls'
                        srch = srch.rsplit('.', 1)[0]
                    srch = srch.replace('+', ' ')
                elif i.startswith('exact'):
                    srch_exact = True
                elif i.startswith('shuffle'):
                    shuffle_list = True
            record_last_playlist = False
            if st and st_o and srch:
                record_last_playlist = True
            if not st_o:
                st_o = 'NONE'
            if st:
                if st.startswith('playlist'):
                    if st_o and not srch:
                        srch = st_o

            if len(self.last_view) > 10:
                self.last_view.clear()

            st_arr = [st, st_o, srch]
            st_arr_str  = ",".join(st_arr)

            last_view_file = os.path.join(home, 'History', 'last_viewed.txt')
            if record_last_playlist:
                self.last_view.append(st_arr_str)
                with open(last_view_file, "w") as f:
                    f.write(st_arr_str)

            epn_arr = []
            if st and st_o and srch and not pls_cache:
                epn_arr, st, st_o, new_str, st_nm = getdb.options_from_bookmark(
                    st, st_o, srch, search_exact=srch_exact)
                pls_txt = ''
                if epn_arr:
                    pls_txt = self.create_playlist(
                        st, st_o, srch, epn_arr, new_str, st_nm, my_ipaddress, 
                        shuffle_list, play_id)
                    if ret_val is None:
                        ui.navigate_playlist_history.add_item(path)
            elif st and st_o and not pls_cache:
                original_path_name = getdb.options_from_bookmark(
                    st, st_o, srch, search_exact=srch_exact)
                pls_txt = ''
                if original_path_name:
                    pls_txt = self.create_option_playlist(
                        st, st_o, original_path_name)
            self.send_response(200)
            if path.endswith('.htm') or path.endswith('.html'):
                self.send_header('Content-type', 'text/html; charset=utf-8')
            else:
                self.send_header('Content-type', 'audio/mpegurl')
                self.send_header('Content-Disposition', 'attachment; filename={}'.format(srch))
            if not pls_cache:
                pls_txt = bytes(pls_txt, 'utf-8')
            size = len(pls_txt)
            self.send_header('Content-Length', str(size))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(pls_txt)
            except Exception as e:
                print(e)
            if ui.remote_control and ui.remote_control_field:
                srch = st_arr[-1]
                if epn_arr and srch and not srch.endswith(".hash") and not shuffle_list:
                    shuffle_list = True
                    self.playlist_shuffle_list = epn_arr.copy()
                if self.playlist_shuffle_list and shuffle_list:
                    ui.epn_arr_list = self.playlist_shuffle_list.copy()
                self.nav_signals.total_navigation(st_arr[0], st_arr[1],
                                                 st_arr[2], shuffle_list)
        elif path.lower() in ["vlc", "mpv"] or not path:
            self.send_response(303)
            if len(self.old_path) > 0:
                self.send_header('Location', self.old_path[-1] + ".played")
            self.send_header('Connection', 'close')
            self.end_headers()
        elif path.lower() == 'play':
            self.row = ui.list2.currentRow()
            if self.row < 0:
                self.row = 0
            if ui.btn1.currentText().lower() == 'youtube':
                nm = ui.final_playing_url
                if not nm:
                    return 0
            else:
                nm = ui.epn_return(self.row)
            if nm.startswith('"'):
                nm = nm.replace('"', '')
            self.process_url(nm, get_bytes)
        elif path.startswith('playlist_') or path.startswith('queueitem_') or path.startswith('queue_remove_item_') or path.startswith("play_last_item_"):
            try:
                pl, row = path.rsplit('_', 1)
                if row.isnumeric():
                    row_num = int(row)
                else:
                    row_num = -1000
                if ui.remote_control and ui.remote_control_field:
                    b = b'Playing file'
                    if path.startswith('playlist_'):
                        self.nav_signals.control_signal(row_num, 'normal')
                    elif path.startswith("play_last_item_"):
                        row_num = ui.read_from_video_playlist_status("row")
                        self.nav_signals.control_signal(row_num, 'normal')
                    elif path.startswith('queueitem_'):
                        b = b'queued'
                        self.nav_signals.control_signal(row_num, 'queue')
                    elif path.startswith('queue_remove_item_'):
                        b = b'queued item removed'
                        self.nav_signals.control_signal(row_num, 'queue_remove')
                    self.final_message(b)
                else:
                    b = b'Remote Control Not Allowed'
                    self.final_message(b)
            except Exception as e:
                print(e)
        elif path.lower() == 'lock':
            if ui.remote_control and ui.remote_control_field:
                b = b'locking file'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'loop')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playpause':
            if ui.remote_control and ui.remote_control_field:
                b = 'playpause:{0}'.format(ui.cur_row)
                self.final_message(bytes(b, 'utf-8'))
                self.nav_signals.control_signal(-1000, 'playpause')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playpause_pause':
            if ui.remote_control and ui.remote_control_field:
                b = 'playpause_pause:{0}'.format(ui.cur_row)
                self.final_message(bytes(b, 'utf-8'))
                self.nav_signals.control_signal(-1000, 'playpause_pause')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playpause_play':
            if ui.remote_control and ui.remote_control_field:
                b = 'playpause_play:{0}'.format(ui.cur_row)
                self.final_message(bytes(b, 'utf-8'))
                self.nav_signals.control_signal(-1000, 'playpause_play')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'seek10':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek +10s'
                self.final_message(b)
                self.nav_signals.control_signal(10, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'seek_10':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek -10s'
                self.final_message(b)
                self.nav_signals.control_signal(-10, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'seek60':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek 60s'
                self.final_message(b)
                self.nav_signals.control_signal(60, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'seek_60':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek -60s'
                self.final_message(b)
                self.nav_signals.control_signal(-60, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'seek5m':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek 300s'
                self.final_message(b)
                self.nav_signals.control_signal(300, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'toggle_master_slave':
            if ui.remote_control and ui.remote_control_field:
                if ui.web_control == 'master':
                    ui.web_control = 'slave'
                else:
                    ui.web_control = 'master'
                self.final_message(bytes(ui.web_control, 'utf-8'))
                ui.frame_extra_toolbar.master_slave_tab_btn.clicked_emit()
                if not ui.settings_box.tabs_present:
                    ui.gui_signals.box_settings('hide')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'get_current_background':
            content = None
            if os.path.isfile(ui.current_background):
                with open(ui.current_background, 'rb') as f:
                    content = f.read()
            if content:
                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-Length', len(content))
                self.send_header('Connection', 'close')
                self.end_headers()
                try:
                    self.wfile.write(content)
                except Exception as err:
                    self.final_message(b'No Content')
            else:
                self.final_message(b'No Content')
        elif path.lower() == 'seek_5m':
            if ui.remote_control and ui.remote_control_field:
                b = b'seek -300s'
                self.final_message(b)
                self.nav_signals.control_signal(-300, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower().startswith('seek_abs_'):
            seek_val = 0
            if ui.remote_control and ui.remote_control_field:
                val = path.replace('seek_abs_', '', 1)
                seek_val = 0
                try:
                    seek_val_float = float(val)
                    if ui.web_control == 'master':
                        seek_val = int(ui.mplayerLength*(seek_val_float/100))
                        if ui.player_val == 'mplayer':
                            seek_val = seek_val/1000
                    else:
                        seek_val = round(float(val))
                except Exception as err:
                    print(err, '--1358--seek-abs--')
                seek_str = 'seek {0}/{1}'.format(seek_val, ui.mplayerLength)
                self.final_message(bytes(seek_str, 'utf-8'))
                self.nav_signals.control_signal(seek_val, 'seek')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'volume5':
            if ui.remote_control and ui.remote_control_field:
                b = b'volume +5'
                self.final_message(b)
                self.nav_signals.control_signal(5, 'volume')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'volume_5':
            if ui.remote_control and ui.remote_control_field:
                b = b'volume -5'
                self.final_message(b)
                self.nav_signals.control_signal(-5, 'volume')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playerstop':
            if ui.remote_control and ui.remote_control_field:
                b = b'stop playing'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'stop')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playnext':
            if ui.remote_control and ui.remote_control_field:
                b = 'Next:{0}'.format(str((ui.cur_row+1)%ui.list2.count()))
                self.final_message(bytes(b, 'utf-8'))
                self.nav_signals.control_signal(-1000, 'next')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'playprev':
            if ui.remote_control and ui.remote_control_field:
                b = 'Prev:{0}'.format(str((ui.cur_row-1)%ui.list2.count()))
                self.final_message(bytes(b, 'utf-8'))
                self.nav_signals.control_signal(-1000, 'prev')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'fullscreen':
            if ui.remote_control and ui.remote_control_field:
                b = b'Toggle Fullscreen'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'fullscreen')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'show_player_window':
            if ui.remote_control and ui.remote_control_field:
                b = b'show_player'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'show_player')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'hide_player_window':
            if ui.remote_control and ui.remote_control_field:
                b = b'hide_player'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'hide_player')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'toggle_subtitle':
            if ui.remote_control and ui.remote_control_field:
                b = b'toggle_subtitle'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'toggle_subtitle')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'toggle_audio':
            if ui.remote_control and ui.remote_control_field:
                b = b'toggle_audio'
                self.final_message(b)
                self.nav_signals.control_signal(-1000, 'toggle_audio')
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.lower() == 'get_remote_control_status':
            try:
                if ui.remote_control and ui.remote_control_field:
                    if ui.web_control == 'master':
                        media_length = ui.mplayerLength
                        if ui.mpvplayer_val.processId() > 0 and ui.player_val in ["vlc", "cvlc"]:
                            data = ui.mpvplayer_val.get_vlc_output("get_time")
                            if data and data.isnumeric():
                                ui.progress_counter = int(data)
                        progress_counter = ui.progress_counter

                        if ui.player_val == 'mplayer':
                            media_length = media_length/1000
                            progress_counter = progress_counter/1000
                        msg = str(media_length)+'::'+str(progress_counter)+'::'+str(ui.list2.currentRow()+1)+'::'+str(len(ui.queue_url_list))+'::'+str(ui.epn_name_in_list)+'::'+str(ui.player_val)+'::'+str(ui.queue_changed)
                    else:
                        msg = ui.slave_status_string
                    self.final_message(bytes(msg, 'utf-8'))
                    if ui.queue_changed:
                        ui.queue_changed = False
                else:
                    b = b'Remote Control Not Allowed'
                    self.final_message(b)
            except Exception as err:
                print(err, '--1488--')
                self.final_message(b'error')
        elif path.startswith('abs_path=') or path.startswith('master_abs_path='):
            try:
                process_url = False
                if path.startswith('abs_path='):
                    path = path.split('abs_path=', 1)[1]
                else:
                    path = path.split('master_abs_path=', 1)[1]
                nm = path
                nm = str(base64.b64decode(nm).decode('utf-8'))
                logger.info(nm)
                num_row = None
                old_nm = nm
                if nm.startswith('http') or nm.startswith('ytdl:'):
                    http_val = 'http'
                    if ui.https_media_server:
                        http_val = "https" 
                    n_url = http_val+'://'+str(my_ipaddress)+':'+str(ui.local_port_stream)
                    logger.info('abs_path_playing={0}'.format(n_url))
                    if nm.startswith(n_url):
                        try:
                            num_row = self.path.rsplit('/', 1)[-1]
                            if num_row == 'server' or num_row == 'now_playing':
                                row = ui.cur_row
                            else:
                                row = int(num_row)
                        except Exception as err_val:
                            print(err_val, '--1112--')
                            row = 0
                        if row < 0:
                            row = 0
                        nm = ui.epn_return(row)
                        if nm.startswith('"'):
                            nm = nm.replace('"', '')
                    elif (('youtube.com' in nm or nm.startswith('ytdl:')) and not self.path.endswith('.subtitle') 
                            and not self.path.endswith('.getsub') and not self.path.endswith('.image')):
                        nm = ui.yt.get_yt_url(
                                nm, ui.client_quality_val, ui.ytdl_path, logger,
                                mode=ui.client_yt_mode, reqfrom='client'
                                )
                        nm = nm.strip()
                        if '::' in nm:
                            nm_arr = nm.split('::')
                            vid = nm_arr[0]
                            aud = nm_arr[1]
                            if ui.client_yt_mode == 'music' and not aud.endswith('.vtt'):
                                nm = aud
                            elif aud.endswith('.vtt'):
                                nm = vid
                            if "youtube-dl" in vid:
                                nm = aud.replace('"', "")
                if self.path.endswith('.subtitle'):
                    new_path = self.path.rsplit('.', 1)[0]
                    if new_path.endswith('.reload'):
                        self.process_subtitle_url(nm, status='reload')
                    elif new_path.endswith('.original'):
                        self.process_subtitle_url(nm, status='original')
                    else:
                        self.process_subtitle_url(nm)
                elif self.path.endswith('.getsub'):
                    self.process_subtitle_url(nm, status='getsub')
                elif self.path.endswith('.image'):
                    self.process_image_url(nm)
                elif ".image_next_" in self.path:
                    inter  = int(self.path.rsplit("_", 1)[-1])
                    self.generate_image_url_next(nm, inter)
                elif ".toggle_watch_status" in self.path:
                    r = ui.media_data.toggle_watch_status(nm)
                    b = bytes(r, "utf-8")
                    self.final_message(b)
                elif self.path.endswith('.download'):
                    if 'youtube.com' in old_nm:
                        captions = self.check_yt_captions(old_nm)
                        info_args = urllib.parse.unquote(self.path.rsplit('&&')[-1])
                        info_arr = info_args.split('&')
                        if len(info_arr) >= 2:
                            try:
                                pls_name = info_arr[0]
                                new_name = info_arr[1].split('=')[-1].rsplit('.')[0]
                                logger.info(new_name)
                                self.process_offline_mode(
                                    nm, pls_name, new_name, 
                                    msg=True, captions=captions, url=old_nm)
                            except Exception as e:
                                print(e)
                                self.final_message(b'Error in processing url')
                        else:
                            self.final_message(b'Wrong parameters')
                    else:
                        self.final_message(b'Wrong parameters')
                else:
                    if os.path.exists(nm):
                        ui.media_data.mark_episode_as_watched(nm)
                    self.process_url(nm, get_bytes, status=num_row)
                    process_url = True
                #print(ui.remote_control, ui.remote_control_field, path, '--1440--')
                if ui.remote_control and ui.remote_control_field:
                    if 'playlist_index=' in self.path:
                        row_num_val = self.path.rsplit('playlist_index=', 1)[1]
                        row_num = -1000
                        mode = 'normal'
                        if row_num_val.isnumeric():
                            row_num = int(row_num_val)
                        else:
                            mode = row_num_val
                        #print(row_num, '--row--num--playlist--', mode)
                        self.nav_signals.control_signal(row_num, mode)
                    else:
                        if not process_url:
                            b = b'Remote Control Not Allowed'
                            self.final_message(b)
            except Exception as e:
                print(e)
                self.final_message(b'Wrong parameters --1626--')
        elif path.startswith('relative_path=') or path.startswith('master_relative_path='):
            try:
                #if '/' in path:
                #	path = path.rsplit('/', 1)[0]
                process_url = False
                logger.info('--------path---{0}'.format(path))
                if path.startswith('relative_path='):
                    path = path.split('relative_path=', 1)[1]
                else:
                    path = path.split('master_relative_path=', 1)[1]
                nm = path
                nm = str(base64.b64decode(nm).decode('utf-8'))
                logger.info('\n<------------------>{0}\n'.format(nm))
                
                tmp_arr = nm.split('&')
                torrent_stream = False
                if len(tmp_arr) == 7:
                    if tmp_arr[4] == 'False':
                        torrent_stream = False
                    else:
                        torrent_stream = True
                elif len(tmp_arr) > 7:
                    new_tmp_arr = tmp_arr[3:]
                    row_index = -1
                    local_stream_index = -1
                    for i, j in enumerate(new_tmp_arr):
                        if j.lower() == 'true' or j.lower() == 'false':
                            if j.lower() == 'false':
                                torrent_stream = False
                            else:
                                torrent_stream = True
                
                if torrent_stream:
                    old_nm = nm
                    if ui.https_media_server:
                        https_val = 'https'
                    else:
                        https_val = 'http'
                    if not my_ip_addr:
                        nm = https_val+"://"+str(ui.local_ip)+':'+str(ui.local_port)+'/'
                    else:
                        nm = https_val+"://"+str(my_ip_addr)+':'+str(ui.local_port)+'/'
                    if ui.remote_control and ui.remote_control_field:
                        if 'playlist_index=' in self.path:
                            row_num_val = self.path.rsplit('playlist_index=', 1)[1]
                            row_num = -1000
                            mode = 'normal'
                            if row_num_val.isnumeric():
                                row_num = int(row_num_val)
                            else:
                                mode = row_num_val
                            logger.info('{0}--row--num--playlist--{1}'.format(row_num, mode))
                            self.nav_signals.control_signal_external(row_num, mode)
                            b = b'OK'
                            self.final_message(b)
                        elif "master_relative_path=" in self.path:
                            self.nav_signals.new_signal(old_nm)
                            logger.info('--nm---{0}'.format(nm))
                            self.process_url(nm, get_bytes)
                        else:
                            b = b'Remote Control Not Allowed'
                            self.final_message(b)
                    else:
                        pl_id_c = None
                        
                        if '&pl_id=' in self.path:
                            pl_id_c = re.search('&pl_id=[^/]*', self.path).group()
                            nm = nm + pl_id_c
                            logger.debug('\nplaylist--id--{0}\n'.format(nm))
                        if self.path.endswith('.subtitle'):
                            loc = get_torrent_download_location(old_nm, home, ui.torrent_download_folder)
                            new_path = self.path.rsplit('.', 1)[0]
                            if new_path.endswith('.reload'):
                                self.process_subtitle_url(loc, status='reload')
                            else:
                                self.process_subtitle_url(loc)
                        elif self.path.endswith('.image'):
                            loc = get_torrent_download_location(old_nm, home, ui.torrent_download_folder)
                            self.process_image_url(loc)
                        else:
                            self.nav_signals.new_signal(old_nm)
                            logger.info('--nm---{0}'.format(nm))
                            self.process_url(nm, get_bytes)
                else:
                    #print(ui.remote_control, ui.remote_control_field, path)
                    if ui.remote_control and ui.remote_control_field:
                        if 'playlist_index=' in self.path:
                            row_num_val = self.path.rsplit('playlist_index=', 1)[1]
                            row_num = -1000
                            mode = 'normal'
                            if row_num_val.isnumeric():
                                row_num = int(row_num_val)
                            else:
                                mode = row_num_val
                            logger.info('{0}--row--num--playlist--{1}'.format(row_num, mode))
                            self.nav_signals.control_signal_external(row_num, mode)
                            b = b'OK'
                            self.final_message(b)
                        else:
                            b = b'Remote Control Not Allowed'
                            self.final_message(b)
                    else:
                        if self.path.endswith('.image'):
                            self.process_image_url(nm)
                        else:
                            nm = getdb.epn_return_from_bookmark(nm, from_client=True)
                            self.process_url(nm, get_bytes)
            except Exception as e:
                print(e)
        elif path.startswith('stop_torrent'):
            try:
                self.nav_signals.stop_signal('from client')
                msg = 'Torrent Stopped'
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
            except Exception as e:
                print(e)
        elif path.startswith('get_torrent_info'):
            try:
                if ui.torrent_handle:
                    msg = torrent_session_status(ui.torrent_handle)
                else:
                    msg = 'no torrent handle, wait for torrent to start'
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
            except Exception as e:
                print(e)
        elif path.startswith('torrent_pause'):
            try:
                if ui.torrent_handle:
                    ui.torrent_handle.pause()
                    msg = 'Current Torrent Paused'
                else:
                    msg = 'no torrent handle, first start torrent before pausing'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = str(e)
            self.final_message(msg)
        elif path.startswith('torrent_all_pause'):
            try:
                if ui.stream_session:
                    ui.stream_session.pause()
                    msg = 'Current session paused'
                else:
                    msg = 'no torrent handle, first start torrent before pausing'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = str(e)
            self.final_message(msg)
        elif path.startswith('torrent_resume'):
            try:
                if ui.torrent_handle:
                    ui.torrent_handle.resume()
                    msg = 'Current Torrent resumed'
                else:
                    msg = 'no torrent handle, first start torrent before starting'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = str(e)
            self.final_message(msg)
        elif path.startswith('torrent_remove'):
            try:
                if ui.torrent_handle:
                    t_list = ui.stream_session.get_torrents()
                    for i in t_list:
                        if i == ui.torrent_handle:
                            ui.stream_session.remove_torrent(i)
                    msg = 'Current Torrent Removed from session'
                else:
                    msg = 'no torrent handle, first start torrent session before removing'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = str(e)
            self.final_message(msg)
        elif path.startswith('torrent_all_resume'):
            try:
                if ui.stream_session:
                    ui.stream_session.resume()
                    msg = 'Current session resumed'
                else:
                    msg = 'no torrent handle, first start torrent before resuming'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = str(e)
            self.final_message(msg)
        elif path.startswith('get_all_torrent_info'):
            try:
                if ui.stream_session:
                    msg = ''
                    t_list = ui.stream_session.get_torrents()
                    for i in t_list:
                        msg_t = i.name() +':'+torrent_session_status(i) +'<br>'
                        if i == ui.torrent_handle:
                            msg_t = ui.check_symbol+msg_t
                        msg = msg + msg_t
                else:
                    msg = 'no torrent handle, session not started wait for torrent session to start'
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
            except Exception as e:
                print(e)
        elif path.startswith('set_torrent_speed'):
            d = ''
            u = ''
            try:
                val = path.replace('set_torrent_speed=', '', 1)
                if val:
                    if val.startswith('d=') or val.startswith('u='):
                        if '&' in val:
                            if val.startswith('d='):
                                d1, u1 = val.split('&')
                            else:
                                u1, d1 = val.split('&')
                            if d1:
                                d = d1.replace('d=', '', 1)
                            if u1:
                                u = u1.replace('u=', '', 1)
                        else:
                            if val.startswith('d='):
                                d = val.replace('d=', '', 1)
                            else:
                                u = val.replace('u=', '', 1)
                        if d.isnumeric():
                            ui.torrent_download_limit = int(d) * 1024
                        if u.isnumeric():
                            ui.torrent_upload_limit = int(u) * 1024
                            
                down_speed = str(int((ui.torrent_download_limit)/1024)) + 'KB'
                up_speed = str(int((ui.torrent_upload_limit)/1024)) + 'KB'
                if ui.torrent_handle:
                    ui.torrent_handle.set_download_limit(ui.torrent_download_limit)
                    ui.torrent_handle.set_upload_limit(ui.torrent_upload_limit)
                msg = 'Download Speed Limit:{0}, Upload Speed Limit:{1} SET'.format(down_speed, up_speed)
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
            except Exception as e:
                print(e)
                msg = b'Some wrong parameters provided, Nothing changed'
                self.final_message(msg)
        elif path.startswith('clear_client_list'):
            try:
                arr = b'<html>Clearing Visited Client list</html>'
                #size = sys.getsizeof(arr)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(arr))
                self.send_header('Connection', 'close')
                self.end_headers()
                try:
                    self.wfile.write(arr)
                except Exception as e:
                    print(e)
                ui.client_auth_arr[:] = []
                ui.client_auth_arr = ['127.0.0.1', '0.0.0.0']
                if ui.local_ip not in ui.client_auth_arr:
                    ui.client_auth_arr.append(ui.local_ip)
                if ui.local_ip_stream not in ui.client_auth_arr:
                    ui.client_auth_arr.append(ui.local_ip_stream)
            except Exception as e:
                print(e)
        elif path.startswith('logout'):
            try:
                client_addr = str(self.client_address[0])
                if client_addr in ui.client_auth_arr:
                    index = ui.client_auth_arr.index(client_addr)
                    del ui.client_auth_arr[index]
                if ui.remote_control_field:
                    ui.remote_control = False
                cookie_val = self.headers['Cookie']
                #print(cookie_val, '--cookie--')
                if cookie_val:
                    try:
                        uid_c = cookie_val.split('=')[1]
                        if uid_c in self.client_auth_dict:
                            del self.client_auth_dict[uid_c]
                            #print('deleting client cookie')
                    except Exception as err_val:
                        print(err_val)
                logger.debug(self.client_auth_dict)
                logger.debug(self.playlist_auth_dict)
                logger.debug("client: {0} logged out".format(client_addr))
                txt = "Logged out. Now Clear Browser Cookies, Cache, ACTIVE LOGINS to avoid auto-login. In desktop browsers these options can be found by pressing shift+ctrl+del. If auto-login still persists, try restarting the browser."
                txt_b = bytes(txt, 'utf-8')
                self.final_message(txt_b)
            except Exception as e:
                print(e)
        elif path.startswith('index.htm'):
            nm = 'stream_continue.htm'
            self.send_response(303)
            self.send_header('Location', nm)
            self.send_header('Connection', 'close')
            self.end_headers()
        elif path.startswith('remote_'):
            if path.endswith('_on.htm'):
                if ui.remote_control_field:
                    ui.remote_control = True
            elif path.endswith('_off.htm'):
                if ui.remote_control_field:
                    ui.remote_control = False
            msg = 'Remote Control Set {0}'.format(ui.remote_control)
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('show_thumbnails'):
            ui.show_client_thumbnails = True
            msg = 'Thumbnails Set To {0}'.format(ui.show_client_thumbnails)
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('hide_thumbnails'):
            ui.show_client_thumbnails = False
            msg = 'Thumbnails Set To {0}'.format(ui.show_client_thumbnails)
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('get_torrent='):
            nm = self.path.replace('/get_torrent=', '', 1)
            new_url = str(base64.b64decode(nm).decode('utf-8'))
            logger.info(nm)
            logger.info(new_url)
            if new_url.startswith('http') or new_url.startswith('magnet'):
                msg = 'Empty Response'
                ret_val = ''
                hist_folder = os.path.join(home, 'History', 'Torrent')
                try:
                    ret_val = getdb.record_torrent(new_url, hist_folder)
                    if ret_val:
                        msg = 'OK:{0}'.format(ret_val)
                    else:
                        msg = 'Failed'
                except Exception as e:
                    print(e)
                    msg = 'Fetching Torrent Failed'
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
                if ui.remote_control and ui.remote_control_field and ret_val:
                    ui.btn1.setCurrentIndex(0)
                    ui.btnAddon.setCurrentIndex(0)
                    self.nav_signals.total_navigation('Torrent', 'History', ret_val, False)
            elif new_url.startswith('delete'):
                var_name = new_url.replace('delete&', '', 1)
                if var_name:
                    msg = 'Deleting Torrent: {}, Refresh history'.format(var_name)
                    msg = bytes(msg, 'utf-8')
                    self.final_message(msg)
                    self.nav_signals.delete_torrent_signal(var_name)
                else:
                    msg = "Wrong Parameters: Don't do that again without selecting Torrent from the list".format(var_name)
                    msg = bytes(msg, 'utf-8')
                    self.final_message(msg)
            else:
                msg = 'Wrong Parameters, Try Again'
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
        elif path.startswith('add_to_playlist='):
            ui.media_server_cache_playlist.clear()
            n_path = path.replace('add_to_playlist=', '', 1)
            arr = n_path.split('&')
            pls_name = arr[0]
            entry_info = arr[1]
            entry_info = entry_info.strip()
            if entry_info.startswith('- '):
                entry_info = entry_info.replace('- ', 'NONE - ', 1)
            
            if '-' in entry_info:
                artist = entry_info.split(' - ')[0]
            else:
                artist = ''
            artist = artist.strip()
            if not artist:
                artist = 'NONE'
            if '-' in entry_info:
                title = entry_info.split(' - ')[1]
            else:
                title = entry_info
            data_link = re.search('abs_path=[^"]*|relative_path=[^"]*', n_path).group()
            txt = 'artist={3}:\npls-name={0}:\ntitle={1}:\nlink={2}'.format(pls_name, title, data_link, artist)
            logger.info(txt)
            txt = '{0} added to {1}'.format(entry_info, pls_name)
            msg = bytes(txt, 'utf-8')
            self.final_message(msg)
            new_line = title+'	'+data_link+'	'+artist
            file_path = os.path.join(home, 'Playlists', pls_name)
            write_files(file_path, new_line, line_by_line=True)
        elif path.startswith('remove_from_playlist='):
            ui.media_server_cache_playlist.clear()
            n_path = path.replace('remove_from_playlist=', '', 1)
            arr = n_path.split('&')
            pls_name = arr[0]
            pls_num = arr[1]
            msg = 'Deleting Number {0} Entry from playlist: {1}'.format(pls_num, pls_name)
            if pls_num.isnumeric():
                pls_number = int(pls_num) - 1
                file_path = os.path.join(home, 'Playlists', pls_name)
                if os.path.isfile(file_path):
                    lines = open_files(file_path, lines_read=True)
                    new_lines = [i.strip() for i in lines if i.strip()]
                    if pls_number < len(new_lines):
                        del new_lines[pls_number]
                        write_files(file_path, new_lines, line_by_line=True)
            else:
                msg = 'Nothing Changed: Wrong Parameters'
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('create_playlist='):
            ui.media_server_cache_playlist.clear()
            n_path = path.replace('create_playlist=', '', 1)
            n_path = n_path.strip()
            msg = 'creating playlist: {0}\nrefresh browser'.format(n_path)
            if n_path:
                file_path = os.path.join(home, 'Playlists', n_path)
                if not os.path.exists(file_path):
                    f = open(file_path, 'w').close()
                    msg = '1:OK'
                else:
                    msg = '2:WRONG'
            else:
                msg = '3:FALSE'
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('delete_playlist='):
            ui.media_server_cache_playlist.clear()
            n_path = path.replace('delete_playlist=', '', 1)
            n_path = n_path.strip()
            msg = 'Nothing deleted: Wrong Parameters'
            if n_path:
                file_path = os.path.join(home, 'Playlists', n_path)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    msg = 'deleted playlist: {0}\n. Refresh browser'.format(n_path)
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('get_all_playlist'):
            dir_path = os.path.join(home, 'Playlists')
            m = os.listdir(dir_path)
            pls_txt = ''
            j = 0
            for i in m:
                if j == len(m) - 1:
                    pls_txt = pls_txt + i
                else:
                    pls_txt = pls_txt + i + '\n'
                j = j + 1
            pls_txt = bytes(pls_txt, 'utf-8')
            self.final_message(pls_txt)
        elif path.startswith('get_all_category'):
            pls_txt = self.get_extra_fields()
            pls_txt = bytes(pls_txt, 'utf-8')
            self.final_message(pls_txt)
        elif path.startswith('update_video') or path.startswith('update_music'):
            try:
                if path.startswith('update_video'):
                    val = 'video'
                    ui.media_server_cache_video.clear()
                else:
                    val = 'music'
                    ui.media_server_cache_music.clear()
                self.nav_signals.update_signal(val)
                msg = '{0} section updated successfully: refresh browser'.format(val)
                msg = bytes(msg, 'utf-8')
                self.final_message(msg)
            except Exception as e:
                print(e)
                msg = bytes('Error in updating', 'utf-8')
                self.final_message(msg)
        elif path.startswith('youtube_url='):
            ui.media_server_cache_playlist.clear()
            try:
                msg = 'Something wrong in parameters'
                logger.info('{0}---1903--'.format(path))
                new_path = self.path.replace('/youtube_url=', '', 1)
                url = pls = None
                if '&&' in new_path:
                    url, pls = new_path.split('&&')
                    #url = str(base64.b64decode(url).decode('utf-8'))
                else:
                    msg = 'wrong parameters'
                mode = None
                if pls.endswith('.download'):
                    pls = pls.rsplit('.', 1)[0]
                    mode = 'offline'
                if url and pls:
                    pls = urllib.parse.unquote(pls)
                    if url.startswith('http'):
                        val = self.process_yt_playlist(url, pls, mode=mode)
                        logger.info('---1914---val={0}--url={1}--pls={2}'.format(val, url, pls))
                        if val:
                            msg = 'playlist :{0} updated successfully'.format(pls)
                        else:
                            msg = 'playlist creation failed'
                    else:
                        if url == 'audio':
                            ui.client_yt_mode = 'music'
                            msg = 'only audio will be played'
                        elif url == 'audiovideo':
                            ui.client_yt_mode = 'offline'
                            msg = 'regular video will be played'
                        else:
                            msg = 'wrong parameters'
                    
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = bytes('Error in updating', 'utf-8')
            self.final_message(msg)
        elif path.lower().startswith('youtube_quick='):
            if ui.remote_control and ui.remote_control_field:
                b = b'Youtube Quick Command Received by Server. Trying To Play Video Directly'
                self.final_message(b)
                logger.debug(path)
                url = self.path.replace('/youtube_quick=', '', 1)
                logger.debug(url)
                if url.startswith('http') or url.startswith('magnet:'):
                    if ui.web_control == "slave":
                        new_url_1 = '{}/remote_on.htm'.format(ui.slave_address.strip())
                        ui.vnt.get(new_url_1)
                        ui.list2.start_pc_to_pc_casting("play quick", 0, None, path)
                    else:
                        ui.media_server_cache_playlist.clear()
                        ui.navigate_playlist_history.clear()
                        ui.quick_url_play = url
                        logger.debug(ui.quick_url_play)
                        ui.quick_url_play_btn.clicked_emit()
                    self.process_yt_playlist(url, "CAST_PLAYLIST", mode=None)
            else:
                b = b'Remote Control Not Allowed'
                self.final_message(b)
        elif path.startswith('quality='):
            try:
                qual = path.replace('quality=', '', 1)
                if qual in ui.quality_dict:
                    ui.client_quality_val = qual
                    if ui.remote_control and ui.remote_control_field:
                        ui.quality_val = qual
                        ui.set_quality_server_btn.clicked_emit()
                    msg = 'quality set to: {0}'.format(ui.client_quality_val)
                else:
                    msg = 'wrong parameters'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = bytes('Error in setting quality', 'utf-8')
            self.final_message(msg)
        elif path.startswith('playbackengine='):
            try:
                playbackengine = path.replace('playbackengine=', '', 1)
                if "&" in playbackengine:
                    (pl_engine, mode) = playbackengine.split("&")
                    mode_val = mode.split("=")[1].lower()
                else:
                    pl_engine = playbackengine
                    mode_val = "master"
                if pl_engine in ui.playback_engine and mode_val == "master":
                    if ui.remote_control and ui.remote_control_field:
                        ui.player_val = pl_engine
                        ui.restart_application = True
                        ui.btn_quit.clicked_emit()
                    msg = 'Playback Engine Changed For master to {}'.format(pl_engine)
                elif pl_engine in ui.playback_engine and mode_val == "slave":

                    new_url_1 = '{}/remote_on.htm'.format(ui.slave_address.strip())
                    new_url_2 = '{}/playbackengine={}'.format(ui.slave_address.strip(), pl_engine)

                    ui.vnt.get(new_url_1)
                    ui.vnt.get(new_url_2)
                    msg = 'Playback Engine Changed For slave to {}'.format(pl_engine)
                else:
                    msg = 'wrong parameters'
                msg = bytes(msg, 'utf-8')
            except Exception as e:
                print(e)
                msg = bytes('Error in setting quality', 'utf-8')
            self.final_message(msg)
        elif path.startswith('change_playlist_order='):
            ui.media_server_cache_playlist.clear()
            n_path = path.replace('change_playlist_order=', '', 1)
            n_path = n_path.strip()
            arr = n_path.split('&')
            modified = False
            logger.info(arr)
            if len(arr) >= 3:
                pls = arr[0]
                try:
                    src = int(arr[1]) - 1
                    dest = int(arr[2]) - 1
                except Exception as e:
                    print(e, '--1736--')
                    src = -1
                    dest = -1
                if pls and src >= 0 and dest >= 0:
                    file_path = os.path.join(home, 'Playlists', pls)
                    lines = open_files(file_path, lines_read=True)
                    new_lines = [i.strip() for i in lines if i.strip()]
                    if ((src >= dest and src < len(new_lines)) or 
                            (src < dest and dest <= len(new_lines))):
                        src_val = new_lines[src]
                        del new_lines[src]
                        if dest < len(new_lines):
                            new_lines.insert(dest, src_val)
                            modified = True
                        elif dest == len(new_lines):
                            new_lines.append(src_val) 
                            modified = True
                        if modified:
                            write_files(file_path, new_lines, line_by_line=True)

            if modified:
                msg = 'Playlist Modified Successfully'
            else:
                if pls:
                    msg = 'Playlist sync failed'
                else:
                    msg = "No Playlist was selected, hence can't sync arrangement"
            msg = bytes(msg, 'utf-8')
            self.final_message(msg)
        elif path.startswith('m3u_playlist_'):
            try:
                pls_num = (path.split('_')[2]).replace('.m3u', '')
                if pls_num.isnumeric():
                    pls_txt = self.playlist_m3u_dict.get(pls_num)
                    if not pls_txt:
                        pls_txt = '#EXTM3U\n'
                    else:
                        del self.playlist_m3u_dict[pls_num]
                    pls_txt = bytes(pls_txt, 'utf-8')
                    self.send_response(200)
                    self.send_header('Content-type', 'audio/mpegurl')
                    self.send_header('Content-Disposition', 'attachment; filename={}'.format(path))
                    size = len(pls_txt)
                    self.send_header('Content-Length', str(size))
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    try:
                        self.wfile.write(pls_txt)
                    except Exception as e:
                        print(e)
            except Exception as err:
                print(err, '--2091--')
        elif path.startswith('clear_playlist_history'):
            ui.media_server_cache_playlist.clear()
            ui.navigate_playlist_history.clear()
            msg = bytes('playlist navigation history cleared', 'utf-8')
            self.final_message(msg)
        elif path.startswith('clear_all_cache'):
            ui.media_server_cache_playlist.clear()
            ui.media_server_cache_music.clear()
            ui.media_server_cache_video.clear()
            ui.navigate_playlist_history.clear()
            msg = bytes('cache and playlist navigation history cleared', 'utf-8')
            self.final_message(msg)
        elif path.startswith('default.jpg'):
            default_jpg = os.path.join(home, 'default.jpg')
            content = open(default_jpg, 'rb').read()
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-Length', len(content))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(content)
            except Exception as e:
                print(e)
        elif path.endswith('.css') or path.endswith('.js'):
            if path.endswith('.css') and path in ['style.css', 'browse.css', 'admin.css']:
                default_file = os.path.join(BASEDIR, 'web', path)
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
            elif path.endswith('.js') and path in ['myscript.js', 'browse.js', 'admin.js']:
                default_file = os.path.join(BASEDIR, 'web', path)
                self.send_response(200)
                self.send_header('Content-type', 'text/javascript')
            content = open(default_file, 'rb').read()
            self.send_header('Content-Length', len(content))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(content)
            except Exception as e:
                print(e)
        else:
            nm = 'stream_continue.htm'
            self.send_response(303)
            self.send_header('Location', nm)
            self.send_header('Connection', 'close')
            self.end_headers()

    def check_yt_captions(self, url):
        try:
            req = urllib.request.Request(
                url, data=None, headers={'User-Agent': 'Mozilla/5.0'})
            f = urllib.request.urlopen(req)
            content = f.read().decode('utf-8')
            caption = '"caption_translation_languages":""'
            if caption in content:
                sub_title = False
            else:
                sub_title = True
        except Exception as e:
            print(e, '---2279---')
            sub_title = False
        return sub_title

    def process_offline_mode(self, nm, pls, title, msg=None, captions=None, url=None):
        global ui, home, logger
        loc_dir = os.path.join(ui.default_download_location, pls)
        if not os.path.exists(loc_dir):
            os.makedirs(loc_dir)
        title = title.replace('"', '')
        title = title.replace('/', '-')
        if title.startswith('.'):
            title = title[1:]
        loc = os.path.join(loc_dir, title+'.mp4')
        ok_val = False
        if captions and url:
            sub_name_bytes = bytes(loc, 'utf-8')
            h = hashlib.sha256(sub_name_bytes)
            sub_name = h.hexdigest()
            #get_yt_sub_(
            #    url, sub_name, ui.yt_sub_folder, TMPDIR, ui.ytdl_path, logger)
        try:
            ccurl(nm+'#'+'-o'+'#'+loc)
            ok_val = True
        except Exception as e:
            print(e)
            ok_val = False
        if ok_val:
            pls_home = os.path.join(home, 'Playlists', pls)
            content = '{0} - offline	{1}	{2}'.format(title, loc, 'YouTube')
            if os.path.exists(pls_home):
                write_files(pls_home, content, line_by_line=True)
        if msg:
            self.final_message(b'Got it!. update video section or refresh playlist')
        logger.info('captions={0}-{1}-{2}'.format(captions, url, ok_val))

    def generate_image_url_next(self, path, inter):
        global ui, home, logger
        thumbnail_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)
        thumb_name_bytes = bytes(path, 'utf-8')
        h = hashlib.sha256(thumb_name_bytes)
        thumb_name = h.hexdigest()
        thumb_path = os.path.join(thumbnail_dir, thumb_name+'.jpg')
        new_thumb_path = os.path.join(thumbnail_dir, '480px.'+thumb_name+'.jpg')
        new_thumb_path_128px = os.path.join(thumbnail_dir, '128px.'+thumb_name+'.jpg')
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        if os.path.exists(new_thumb_path):
            os.remove(new_thumb_path)
        if os.path.exists(new_thumb_path_128px):
            os.remove(new_thumb_path_128px)
        logger.debug(thumb_path)

        ui.generate_thumbnail_method(thumb_path, inter, path, from_client=True)
        if os.path.exists(thumb_path) and os.stat(thumb_path).st_size:
            ui.create_new_image_pixel(thumb_path, 480)
            ui.create_new_image_pixel(thumb_path, 128)
            thumb_path = new_thumb_path

        if os.path.exists(thumb_path) and os.stat(thumb_path).st_size:
            content = open(thumb_path, 'rb').read()
        else:
            new_file = os.path.join(home, '480px.default.jpg')
            default_jpg = os.path.join(home, 'default.jpg')
            if not os.path.exists(new_file):
                ui.create_new_image_pixel(default_jpg, 480)
            content = open(new_file, 'rb').read()
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.send_header('Content-Length', len(content))
        self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(content)
        except Exception as e:
            print(e)

    def process_image_url(self, path):
        global ui, home, logger
        thumbnail_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)
        thumb_name_bytes = bytes(path, 'utf-8')
        h = hashlib.sha256(thumb_name_bytes)
        thumb_name = h.hexdigest()
        thumb_path = os.path.join(thumbnail_dir, thumb_name+'.jpg')
        new_thumb_path = os.path.join(thumbnail_dir, '480px.'+thumb_name+'.jpg')
        logger.debug(thumb_path)
        got_http_image = False
        if 'youtube.com' in path:
            if path.startswith('ytdl:'):
                path = path.replace('ytdl:', '', 1)
            img_url = ui.create_img_url(path)
            logger.debug(img_url)
            if not os.path.exists(thumb_path) and img_url:
                ccurl(img_url, curl_opt='-o', out_file=thumb_path)
                got_http_image = True
        elif path.startswith('http') and 'abs_path=' in path:
            img_url = path
            if not path.endswith('.image'):
                img_url = path + '.image'
            if not os.path.exists(thumb_path) and img_url:
                ccurl(img_url, curl_opt='-o', out_file=thumb_path)
                got_http_image = True
        logger.debug("path:--thumbnail--{0}".format(path))
        if ((not os.path.exists(thumb_path) and not path.startswith('http') 
                and not path.startswith('relative_path=')) or got_http_image):
            if not got_http_image:
                start_counter = 0
                while ui.mpv_thumbnail_lock.locked():
                    time.sleep(0.5)
                    start_counter += 1
                    if start_counter > 120:
                        break
                ui.generate_thumbnail_method(thumb_path, 10, path, from_client=True)
            if not os.path.exists(new_thumb_path): 
                if os.path.exists(thumb_path) and os.stat(thumb_path).st_size:
                    ui.create_new_image_pixel(thumb_path, 480)
                    thumb_path = new_thumb_path
            else:
                thumb_path = new_thumb_path
        elif os.path.exists(new_thumb_path): 
            if os.stat(new_thumb_path).st_size:
                thumb_path = new_thumb_path
            
                    
        if os.path.exists(thumb_path) and os.stat(thumb_path).st_size:
            content = open(thumb_path, 'rb').read()
        else:
            new_file = os.path.join(home, '480px.default.jpg')
            default_jpg = os.path.join(home, 'default.jpg')
            if not os.path.exists(new_file):
                ui.create_new_image_pixel(default_jpg, 480)
            content = open(new_file, 'rb').read()
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.send_header('Content-Length', len(content))
        self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(content)
        except Exception as e:
            print(e)
        
    def check_local_subtitle(self, path, external=None):
        result = None
        ext = ['.srt', '.ass', '.en.srt', '.en.ass', '.en.vtt']
        if os.path.exists(path) or external:
            if '.' in path:
                nm = path.rsplit('.', 1)[0]
                for i in ext:
                    sub_name = nm + i
                    if os.path.exists(sub_name):
                        result = sub_name
                        break
        return result

    def process_subtitle_url(self, path, status=None):
        global home, ui, logger
        folder_sub = False
        sub_name_bytes = bytes(path, 'utf-8')
        h = hashlib.sha256(sub_name_bytes)
        sub_name = h.hexdigest()
        sub_name_path = os.path.join(ui.yt_sub_folder, sub_name)

        sub_name_vtt = sub_name_path + '.vtt'
        sub_name_srt = sub_name_path + '.srt'
        sub_name_ass = sub_name_path + '.ass'

        if status == 'reload':
            if os.path.isfile(sub_name_vtt):
                os.remove(sub_name_vtt)
            if os.path.isfile(sub_name_srt):
                os.remove(sub_name_srt)
            if os.path.isfile(sub_name_ass):
                os.remove(sub_name_ass)

        sub_path = sub_name_vtt

        logger.info('path={0}:sub={1}'.format(path, sub_path))
        check_local_sub = self.check_local_subtitle(path)
        logger.debug('{}::{}'.format(check_local_sub, status))
        if status == 'original':
            if check_local_sub:
                if os.name == 'nt':
                    try:
                        content = open(check_local_sub, mode='r', encoding='utf-8-sig').read()
                    except Exception as err:
                        logger.error(err)
                        content = open_files(check_local_sub, False)
                else:
                    content = open_files(check_local_sub, False)
            else:
                content = 'Not Found'
            c = bytes(content, 'utf-8')
            self.send_response(200)
            if check_local_sub.endswith('ass'):
                self.send_header('Content-type', 'text/ass')
            elif check_local_sub.endswith('srt'):
                self.send_header('Content-type', 'text/srt')
            else:
                self.send_header('Content-type', 'text/vtt')
            self.send_header('Content-Length', len(c))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(c)
            except Exception as e:
                print(e)
        else:
            sub_srt = False
            sub_ass = False
            got_sub = False

            if check_local_sub is None:
                check_local_sub = self.check_local_subtitle(sub_name_path+'.mkv', external=True)

            if path.startswith('http') and 'youtube.com' in path:
                if status == 'getsub':
                    #get_yt_sub_(path, sub_name, ui.yt_sub_folder, TMPDIR, ui.ytdl_path, logger)
                    check_local_sub = self.check_local_subtitle(sub_name_path+'.mkv', external=True)

                if check_local_sub is not None and not os.path.exists(sub_path):
                    try:
                        if OSNAME == 'posix':
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', check_local_sub, sub_path
                                ])
                        else:
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', check_local_sub, sub_path
                                ], shell=True)
                        got_sub = True
                    except Exception as e:
                        print(e)
                        got_sub = False

                if status == 'getsub' and got_sub:
                    self.final_message(b'Got Subtitle')
                    return 0
                elif status == 'getsub' and not got_sub:
                    self.final_message(b'No Subtitle')
                    return 0
            elif os.path.exists(path) and not os.path.exists(sub_path):
                if check_local_sub is not None and status != 'original':
                    try:
                        if OSNAME == 'posix':
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', check_local_sub, sub_path])
                        else:
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', check_local_sub, sub_path
                                ], shell=True)
                        got_sub = True
                    except Exception as e:
                        logger.error(e)
                        got_sub = False
                elif status == 'original' and check_local_sub:
                    sub_path = check_local_sub
                    got_sub = True
                if not got_sub:
                    try:
                        if OSNAME == 'posix':
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', path, '-map', '0:s:0', '-c',
                                'copy', sub_name_srt])
                        else:
                            out = subprocess.check_output([
                                'ffmpeg', '-y', '-i', path, '-map', '0:s:0', '-c',
                                'copy', sub_name_srt], shell=True)
                        sub_srt = True
                    except Exception as e:
                        logger.error(e)
                        sub_srt = False
                        if os.path.isfile(sub_name_srt):
                            os.remove(sub_name_srt)
                        try:
                            if OSNAME == 'posix':
                                out = subprocess.check_output([
                                    'ffmpeg', '-y', '-i', path, '-map', '0:s:0',
                                    '-c', 'copy', sub_name_ass])
                            else:
                                out = subprocess.check_output([
                                    'ffmpeg', '-y', '-i', path, '-map', '0:s:0',
                                    '-c', 'copy', sub_name_ass], shell=True)
                            sub_ass = True
                        except Exception as e:
                            logger.error(e)
                            sub_ass = False
                            if os.path.isfile(sub_name_ass):
                                os.remove(sub_name_ass)
                    if sub_srt or sub_ass:
                        if sub_srt:
                            ip_file = sub_name_srt
                        else:
                            ip_file = sub_name_ass
                        try:
                            if OSNAME == 'posix':
                                out = subprocess.check_output([
                                    'ffmpeg', '-y', '-i', ip_file, sub_path])
                            else:
                                out = subprocess.check_output([
                                    'ffmpeg', '-y', '-i', ip_file, sub_path
                                    ], shell=True)
                            got_sub = True
                        except Exception as e:
                            logger.error(e)
                            got_sub = False

            if os.path.exists(sub_path):
                content = open(sub_path, 'r').read()
                c = bytes(content, 'utf-8')
            else:
                logger.info('--2287---No--Subtitles--')
                c = bytes('WEBVTT', 'utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/vtt')
            self.send_header('Content-Length', len(c))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(c)
            except Exception as e:
                logger.error(e)

    def process_yt_playlist(self, url, pls, mode=None):
        global home, logger
        op_success = False
        logger.info('----------------2146-----------')
        logger.info('{0}:{1}--1975--'.format(url, pls))
        if url and pls:
            if 'list=' in url:
                yt_playlist = True
            else:
                yt_playlist = False
            if url.startswith('http') and 'youtube.com' in url:
                try:
                    req = urllib.request.Request(
                        url, data=None, headers={'User-Agent': 'Mozilla/5.0'}
                        )
                    f = urllib.request.urlopen(req)
                    content = f.read().decode('utf-8')
                except Exception as e:
                    print(e, '---2279---')
                    return op_success
                caption = '"caption_translation_languages":""'
                
                if caption in content:
                    sub_title = False
                else:
                    sub_title = True
                soup = BeautifulSoup(content, 'lxml')
                #print(soup.prettify())
                title = soup.title.text.replace(' - YouTube', '').strip()
                logger.info(title)
                pls_path = os.path.join(home, 'Playlists', pls)
                logger.info(pls_path)
                if not yt_playlist and pls_path:
                    new_line = title + '	'+url+ '	'+ 'NONE'
                    logger.info(new_line)
                    if not os.path.exists(pls_path):
                        open(pls_path, 'wb').close()
                    if os.path.exists(pls_path):
                        write_files(pls_path, new_line, line_by_line=True)
                        op_success = True
                elif pls_path and yt_playlist:
                    ut_c = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit vve-check currently-playing"})
                    ut = soup.findAll('li', {'class':"yt-uix-scroller-scroll-unit vve-check"})
                    if ut_c:
                        ut = ut_c + ut
                    arr = []
                    for i in ut:
                        try:
                            j = 'https://www.youtube.com/watch?v='+i['data-video-id']
                            k = i['data-video-title']
                            l = k+'	'+j+'	'+'NONE'
                            arr.append(l)
                        except Exception as e:
                            print(e, '--2004--')
                    if arr:
                        if os.path.exists(pls_path):
                            lines = open_files(pls_path, lines_read=True)
                            lines = lines + arr
                            write_files(pls_path, lines, line_by_line=True)
                            op_success = True
                if mode == 'offline':
                    nm = ui.yt.get_yt_url(
                            url, ui.client_quality_val, ui.ytdl_path,
                            logger, mode=ui.client_yt_mode, reqfrom='client'
                            )
                    nm = nm.strip()
                    if '::' in nm:
                        nm_arr = nm.split('::')
                        vid = nm_arr[0]
                        aud = nm_arr[1]
                        if ui.client_yt_mode == 'music' and not aud.endswith('.vtt'):
                            nm = aud
                        elif aud.endswith('.vtt'):
                            nm = vid
                    self.process_offline_mode(nm, pls, title, msg=False, captions=sub_title, url=url)
            else:
                content = None
                try:
                    req = urllib.request.Request(
                        url, data=None, headers={'User-Agent': 'Mozilla/5.0'}
                        )
                    resp = urllib.request.urlopen(req)
                    info = resp.info()
                    content_type = info.get_content_type() 
                    if content_type == "text/html":
                        content = resp.read().decode('utf-8')
                except Exception as e:
                    print(e, '---2279---')
                    return op_success
                if content:
                    soup = BeautifulSoup(content, 'lxml')
                    title = soup.title.text.strip()
                    logger.info(title)
                    url = 'ytdl:'+url
                else:
                    title = url.rsplit("/", 1)[-1]
                    title = urllib.parse.unquote(title)
                new_line = title + '\t' + url + '\t' + 'NONE'
                pls_path = os.path.join(home, 'Playlists', pls)
                if not os.path.exists(pls_path):
                    open(pls_path, 'wb').close()
                if os.path.exists(pls_path):
                    write_files(pls_path, new_line, line_by_line=True)
                    op_success = True
        return op_success

    def final_message(self, txt, cookie=None, auth_failed=None):
        if cookie:
            self.send_response(303)
            self.send_header('Set-Cookie', cookie)
            if self.path.startswith('/get_all_category'):
                nm = 'get_all_category.htm'
            else:
                nm = 'stream_continue.htm'
            self.send_header('Location', nm)
            self.send_header('Connection', 'close')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(txt))
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(txt)
            except Exception as e:
                print(e)
            
    def auth_header(self):
        print('authenticating...')
        txt = 'Nothing'
        print("send header")
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Auth"')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(txt))
        self.end_headers()
        try:
            self.wfile.write(b'Nothing')
        except Exception as e:
            print(e)





class ThreadedHTTPServerLocal(ThreadingMixIn, HTTPServer):
    pass


class MyTCPServer(TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)


class ThreadServerLocal(QtCore.QThread):

    cert_signal = pyqtSignal(str)
    media_server_start = pyqtSignal(str)

    def __init__(self, ip, port, ui_widget=None, hm=None, logr=None, window=None):
        global ui, MainWindow, home, logger, html_default_arr, getdb
        global BASEDIR, TMPDIR, OSNAME
        QtCore.QThread.__init__(self)
        self.ip = ip
        self.port = int(port)
        self.cert_signal.connect(generate_ssl_cert)
        self.media_server_start.connect(media_server_started)
        self.httpd = None
        logger = logr
        ui = ui_widget
        home = hm
        MainWindow = window
        arg_dict = ui.get_parameters_value(
            r='html_default_arr', b='BASEDIR', t='TMPDIR')
        #logger.info(arg_dict)
        html_default_arr = arg_dict['html_default_arr']
        BASEDIR = arg_dict['BASEDIR']
        TMPDIR = arg_dict['TMPDIR']
        OSNAME = os.name
        if ui.getdb is None:
            getdb = ServerLib(ui, home, BASEDIR, TMPDIR, logger)
        elif isinstance(ui.getdb, ServerLib):
            logger.info('--server--initiated---2477--')
            getdb = ui.getdb

    def __del__(self):
        self.wait()                        

    def get_httpd(self):
        return self.httpd
    
    def set_local_ip_val(self):
        try:
            self.ip = get_lan_ip()
        except Exception as err:
            self.ip = ''
        if self.ip:
            if ui.local_ip_stream != self.ip:
                try:
                    change_config_file(self.ip, ui.local_port_stream)
                    print('ip changed: updated config files')
                except Exception as err:
                    print(err)
            ui.local_ip_stream = self.ip
            ui.local_ip = self.ip
    
    def run(self):
        logger.info('starting server...')
        try:
            cert = os.path.join(home, 'cert.pem')
            if ui.https_media_server:
                if not os.path.exists(cert):
                    self.cert_signal.emit(cert)
            if not ui.https_media_server:
                server_address = ('', self.port)
                self.httpd = ThreadedHTTPServerLocal(server_address, HTTPServer_RequestHandler)
                if ui.auto_set_ip_address_on_start:
                    self.set_local_ip_val()
                self.media_server_start.emit('http')
            elif ui.https_media_server and os.path.exists(cert):
                server_address = ('', self.port)
                self.httpd = ThreadedHTTPServerLocal(server_address, HTTPServer_RequestHandler)
                self.httpd.socket = ssl.wrap_socket(self.httpd.socket, certfile=cert, ssl_version=ssl.PROTOCOL_TLSv1_2)
                if ui.auto_set_ip_address_on_start:
                    self.set_local_ip_val()
                self.media_server_start.emit('https')
        except OSError as e:
            e_str = str(e)
            logger.info(e_str)
            if 'errno 99' in e_str.lower():
                txt = 'Your local IP changed..or port is blocked.\n..Trying to find new IP'
                send_notification(txt)
                self.ip = get_lan_ip()
                txt = 'Your New Address is '+self.ip+':'+str(self.port) + '\n Please restart the application'
                send_notification(txt)
                change_config_file(self.ip, self.port)
                server_address = (self.ip, self.port)
                ui.local_ip_stream = self.ip
            else:
                pass
        if self.httpd:
            logger.info('running server...at..'+self.ip+':'+str(self.port))
            #httpd.allow_reuse_address = True
            self.httpd.serve_forever()
            logger.info('quitting http server')
        else:
            logger.info('server not started')


def change_config_file(ip, port):
    global home, ui
    config_file = os.path.join(home, 'other_options.txt')
    new_ip = 'LOCAL_STREAM_IP='+ip+':'+str(port)
    change_opt_file(config_file, 'LOCAL_STREAM_IP=', new_ip)
    ui.local_ip_stream = str(ip)
    ui.local_ip = str(ip)
    config_file_torrent = os.path.join(home, 'torrent_config.txt')
    torrent_ip = 'TORRENT_STREAM_IP='+ip+':'+str(ui.local_port)
    change_opt_file(config_file_torrent, 'TORRENT_STREAM_IP=', torrent_ip)

@pyqtSlot(str)
def generate_ssl_cert(cert):
    global ui, MainWindow, TMPDIR
    if not os.path.exists(cert):
        ui.action_player_menu[7].setText("Start Media Server")
        new_ssl = LoginAuth(parent=MainWindow, ssl_cert=cert, ui=ui, tmp=TMPDIR)
        new_ssl.show()
        send_notification("1.Generating SSL as you've chosen HTTPS.\n2.Enter Atleast 8-character Passphrase in the dialog box.\n")
        

@pyqtSlot(str)
def media_server_started(val):
    global ui
    if val == 'http':
        msg = 'Media Server Started.\nWeb interface is available at\nhttp://{0}:{1}/stream_continue.htm'.format(ui.local_ip_stream, str(ui.local_port_stream))
        send_notification(msg)
    elif val == 'https':
        msg = 'Media Server Started with SSL support.\nWeb interface available at \nhttps://{0}:{1}/stream_continue.htm'.format(ui.local_ip_stream, str(ui.local_port_stream))
        send_notification(msg)

