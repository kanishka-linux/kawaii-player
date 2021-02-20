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
import sqlite3
import shutil
import hashlib
import subprocess
import base64
import urllib.parse
from urllib.parse import urlparse
import json
import uuid
import platform
from collections import OrderedDict
from functools import partial
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui, QtWidgets
from player_functions import write_files, open_files, send_notification
from thread_modules import DiscoverServer

class BrowserData:

    def __init__(self, data):
        self.html = bytes(data, "utf-8")
        self.direct_link = True

class PlaylistWidget(QtWidgets.QListWidget):

    def __init__(self, parent, uiwidget=None, home_var=None, tmp=None, logr=None):
        super(PlaylistWidget, self).__init__(parent)
        global MainWindow, home, TMPDIR, logger, ui
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.downloadWget = []
        self.downloadWget_cnt = 0
        MainWindow = parent
        ui = uiwidget
        self.ui = uiwidget
        TMPDIR = tmp
        home = home_var
        logger = logr
        self.upcount = 0
        self.downcount = 0
        self.count_limit = 1
        self.pc_to_pc_dict = {}
        self.verify_slave_ssl = True
        self.discover_slave_thread = None
        
    def mouseMoveEvent(self, event): 
        if self.ui.auto_hide_dock and not self.ui.dockWidget_3.isHidden() and platform.system().lower() != "darwin":
            self.ui.dockWidget_3.hide()
        if self.ui.tab_5.arrow_timer.isActive():
            self.ui.tab_5.arrow_timer.stop()
        if self.ui.player_val != 'mplayer' or self.ui.mpvplayer_val.processId() == 0:
            self.setFocus()

    def init_offline_mode(self):
        print(self.currentRow(), '--init--offline--')
        param_dict = self.ui.get_parameters_value(s='site', n='name',
                                             sn='siteName', m='mirrorNo')
        site = param_dict['site']
        name = param_dict['name']
        siteName = param_dict['siteName']
        mirrorNo = param_dict['mirrorNo']
        for item in self.selectedItems():
            r = self.row(item)
            if '\t' in self.ui.epn_arr_list[r]:
                eptxt = self.ui.epn_arr_list[r].split('	')[0].replace('_', ' ')
                epfinal = self.ui.epn_arr_list[r].split('	')[1]
            else:
                eptxt = epfinal = self.ui.epn_arr_list[r]
            if eptxt.startswith('#'):
                eptxt = eptxt.replace('#', '', 1)
            aitem = (name, epfinal, mirrorNo, self.ui.quality_val, r, site, siteName, eptxt)
            if site not in ['Music', 'Video']:
                if self.ui.wget.processId() == 0 and not self.ui.epn_wait_thread.isRunning():
                    self.ui.download_video = 1
                    self.ui.queue_item = aitem
                    self.ui.start_offline_mode(r, aitem)
                else:
                    if not self.ui.queue_url_list:
                        self.ui.list6.clear()
                    self.ui.queue_url_list.append(aitem)
                    self.ui.list6.addItem(eptxt)
    
    def open_in_file_manager(self, row):
        param_dict = self.ui.get_parameters_value(s='site', sn='siteName', o='opt')
        site = param_dict['site']
        siteName = param_dict['siteName']
        opt = param_dict['opt']
        path_dir = ''
        if (site.lower() == 'video' or site.lower() == 'music' or 
                site.lower() == 'playlists' or site.lower() == 'none'):
            path = self.ui.epn_arr_list[row].split('\t')[1]
            if path.startswith('abs_path='):
                path = path.split('abs_path=', 1)[1]
                path = str(base64.b64decode(path).decode('utf-8'))
            if path.startswith('"'):
                path = path[1:]
            if path.endswith('"'):
                path = path[:-1]
            if os.path.exists(path):
                path_dir, path_file = os.path.split(path)
            if site.lower() == "playlists" and path.startswith('http'):
                file_1, file_2 = self.ui.get_file_name(row, self)
                if file_1:
                    path_dir, path_file = os.path.split(file_1)
                elif file_2:
                    path_dir, path_file = os.path.split(file_2)
        elif opt.lower() == 'history':
            if self.ui.list1.currentItem():
                itemlist = self.ui.list1.currentItem()
                if  itemlist:
                    new_row = self.ui.list1.currentRow()
                    item_value = self.ui.original_path_name[new_row]
                    if '\t' in item_value:
                        old_name = item_value.split('\t')[0]
                    else:
                        old_name = item_value
                    if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                        history_txt = os.path.join(home, 'History', site, siteName, 'history.txt')
                        path_dir = os.path.join(home, 'History', site, siteName, old_name)
                    else:
                        history_txt = os.path.join(home, 'History', site, 'history.txt')
                        path_dir = os.path.join(home, 'History', site, old_name)
        if os.path.exists(path_dir):
            if os.name == 'posix':
                if platform.system().lower() == "linux":
                    subprocess.Popen(['xdg-open', path_dir])
                else:
                    subprocess.Popen(['open', path_dir])
            elif os.name == 'nt':
                subprocess.Popen(['start', path_dir], shell=True)
        else:
            msg = 'local file path does not exists: {0}'.format(path)
            send_notification(msg)
            
    def queue_item(self):
        site = self.ui.get_parameters_value(s='site')['site']
        for item in self.selectedItems():
            r = self.row(item)
            if site in ["Music", "Video", "PlayLists", "None"]:
                file_queue = os.path.join(home, 'Playlists', 'Queue')
                if not os.path.exists(file_queue):
                    f = open(file_queue, 'w')
                    f.close()
                if not self.ui.queue_url_list:
                    self.ui.list6.clear()
                if site.lower() == "playlists":
                    file_1, file_2 = self.ui.get_file_name(r, self)
                    if os.path.exists(file_1):
                        file_local = file_1
                    elif os.path.exists(file_2):
                        file_local = file_2
                    else:
                        file_local = None
                    txt_queue = self.ui.epn_arr_list[r]
                    if '\t' in txt_queue and file_local:
                        txt_queue_split = txt_queue.split('\t')
                        txt_queue_split[1] = file_local.replace('"', "")
                        txt_queue = '\t'.join(txt_queue_split)
                    elif file_local:
                        txt_queue = file_local
                else:
                    txt_queue = self.ui.epn_arr_list[r]
                self.ui.queue_url_list.append(txt_queue)
                if '\t' in txt_queue:
                    txt_load = txt_queue.split('\t')[0]
                else:
                    txt_load = txt_queue
                if txt_load.startswith('#'):
                    txt_load = txt_load.replace('#', '', 1)
                self.ui.list6.addItem(txt_load)
                logger.info(self.ui.queue_url_list)
                write_files(file_queue, txt_queue, line_by_line=True)
            elif self.ui.video_local_stream:
                if self.ui.list6.count() > 0:
                    txt = self.ui.list6.item(0).text()
                    if txt.startswith('Queue Empty:'):
                        self.ui.list6.clear()
                self.ui.list6.addItem(item.text()+':'+str(r))
            else:
                if not self.ui.queue_url_list:
                    self.ui.list6.clear()
                self.ui.queue_url_list.append(self.ui.epn_arr_list[r])
                self.ui.list6.addItem(self.ui.epn_arr_list[r].split('	')[0])
                
    def edit_name_list2(self, row):
        site = self.ui.get_parameters_value(s='site')['site']
        if '	' in self.ui.epn_arr_list[row]:
            default_text = self.ui.epn_arr_list[row].split('	')[0]
            default_path_name = self.ui.epn_arr_list[row].split('	')[1]
            default_basename = os.path.basename(default_path_name)
            default_display = 'Enter Episode Name Manually\nFile Name:\n{0}'.format(default_basename)
        else:
            default_text = self.ui.epn_arr_list[row]
            default_display = 'Enter Episode Name Manually\nDefault Name:\n{0}'.format(default_text)
        item, ok = QtWidgets.QInputDialog.getText(
            MainWindow, 'Input Dialog', default_display, 
            QtWidgets.QLineEdit.Normal, default_text)
            
        if ok and item:
            if '::' in item:
                nm = item.split('::')[0]
                artist = item.split('::')[1]
            else:
                nm = item
                artist = None
            logger.debug('{0}::{1}'.format(nm, artist))
            t = self.ui.epn_arr_list[row]
            logger.info("4282--{0}-{1}-{2}".format(nm, row, t))
            
            if site == 'PlayLists' or self.ui.music_playlist:
                if artist is None:
                    tmp = self.ui.epn_arr_list[row]
                    tmp = re.sub('[^	]*', nm, tmp, 1)
                else:
                    tmp_arr = self.ui.epn_arr_list[row].split('\t')
                    tmp = nm + '\t' + tmp_arr[1] + '\t' + artist
                    logger.debug(tmp_arr)
                    logger.debug(tmp)
                logger.debug(tmp)
                self.ui.epn_arr_list[row] = tmp
                if self.ui.list1.currentItem():
                    pls_n = os.path.join(
                        home, 'Playlists', self.ui.list1.currentItem().text())
                    self.ui.update_playlist_original(pls_n)
                    self.setCurrentRow(row)
                listitem = self.item(row)
                if listitem:
                    listitem.setText(item)
            elif site == "Video":
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                conn = sqlite3.connect(video_db)
                cur = conn.cursor()
                txt = self.ui.epn_arr_list[row].split('	')[1]
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (item, txt))
                conn.commit()
                conn.close()
                tmp = self.ui.epn_arr_list[row]
                tmp = re.sub('[^	]*', item, tmp, 1)
                self.ui.epn_arr_list[row] = tmp
                dir_path, file_path = os.path.split(txt)
                if dir_path in self.ui.video_dict:
                    del self.ui.video_dict[dir_path]
                listitem = self.item(row)
                if listitem:
                    listitem.setText(item)
            elif site == 'Music' or site == 'NONE':
                pass
            else:
                file_path = ''
                param_dict = self.ui.get_parameters_value(s='siteName', n='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site.lower() == "subbedanime" or site == "dubbedanime":
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                else:
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.isfile(file_path):
                    old_value = self.ui.epn_arr_list[row]
                    if '\t' in old_value:
                        path = old_value.split('\t')[1]
                    else:
                        path = old_value
                    
                    if '\t' in old_value:
                        tmp = re.sub('[^	]*', nm, old_value, 1)
                    else:
                        tmp = nm + '\t' + old_value
                    self.ui.epn_arr_list[row] = tmp
                    listitem = self.item(row)
                    if listitem:
                        listitem.setText(nm)
                write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
            
    def get_default_name(self, row, mode=None):
        site = self.ui.get_parameters_value(s='site')['site']
        if site == "Video" and mode == 'default':
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            txt = self.ui.epn_arr_list[row].split('	')[1]
            item = os.path.basename(txt)
            item = item.replace('_', ' ')
            qr = 'Update Video Set EP_NAME=? Where Path=?'
            cur.execute(qr, (item, txt))
            conn.commit()
            conn.close()
            tmp = self.ui.epn_arr_list[row]
            tmp = re.sub('[^	]*', item, tmp, 1)
            self.ui.epn_arr_list[row] = tmp
            dir_path, file_path = os.path.split(txt)
            if dir_path in self.ui.video_dict:
                del self.ui.video_dict[dir_path]
            listitem = self.item(row)
            if listitem:
                listitem.setText(item)
        elif site == "Video" and mode == 'default_all':
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for row, row_item in enumerate(self.ui.epn_arr_list):
                txt = row_item.split('	')[1]
                item = os.path.basename(txt)
                item = item.replace('_', ' ')
                qr = 'Update Video Set EP_NAME=? Where Path=?'
                cur.execute(qr, (item, txt))
                tmp = row_item
                tmp = re.sub('[^	]*', item, tmp, 1)
                self.ui.epn_arr_list[row] = tmp
            conn.commit()
            conn.close()
            dir_path, file_path = os.path.split(txt)
            if dir_path in self.ui.video_dict:
                del self.ui.video_dict[dir_path]
            self.ui.update_list2()
        elif site == "Video" and mode == 'from_summary':
            video_db = os.path.join(home, 'VideoDB', 'Video.db')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            path = None
            thumbnail_dir = os.path.join(self.ui.home_folder, 'thumbnails', 'thumbnail_server')
            for row, row_item in enumerate(self.ui.epn_arr_list):
                path = row_item.split('	')[1]
                path_bytes = bytes(path, 'utf-8')
                h = hashlib.sha256(path_bytes)
                thumb_name = h.hexdigest()
                txt_path = os.path.join(thumbnail_dir, thumb_name+'.txt')
                if os.path.isfile(txt_path):
                    sumry = open_files(txt_path, False)
                    epname = re.search('Episode Name: [^\n]*', sumry)
                    if epname:
                        epname = epname.group()
                        epname = re.sub('Episode Name: ', '', epname)
                        epname = epname.strip()
                        if epname:
                            qr = 'Update Video Set EP_NAME=? Where Path=?'
                            cur.execute(qr, (epname, path))
                            tmp = row_item
                            tmp = re.sub('[^	]*', epname, tmp, 1)
                            self.ui.epn_arr_list[row] = tmp
            conn.commit()
            conn.close()
            if path is not None:
                if os.path.exists(path):
                    dir_path, file_path = os.path.split(path)
                    if dir_path in self.ui.video_dict:
                        del self.ui.video_dict[dir_path]
                        self.ui.update_list2()
        elif site == 'Music' or site == 'PlayLists' or site == 'NONE':
            pass
        else:
            file_path = ''
            param_dict = self.ui.get_parameters_value(s='siteName', n='name')
            siteName = param_dict['siteName']
            name = param_dict['name']
            if site.lower() == "subbedanime" or site == "dubbedanime":
                file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            if os.path.isfile(file_path):
                if mode == 'default':
                    old_value = self.ui.epn_arr_list[row]
                    if '\t' in old_value:
                        new_name = old_name = old_value.split('\t')[1]
                        if '::' in new_name:
                            new_name = new_name.split('::')[0]
                        if new_name.startswith('http'):
                            new_name = new_name.rsplit('/')[-1]
                            new_name = urllib.parse.unquote(new_name)
                        new_value = new_name + '\t' + old_name
                        self.ui.epn_arr_list[row] = new_value
                        listitem = self.item(row)
                        if listitem:
                            listitem.setText(new_name)
                        write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
                elif mode == 'default_all':
                    for row, val in enumerate(self.ui.epn_arr_list):
                        old_value = val
                        if '\t' in old_value:
                            new_name = old_name = old_value.split('\t')[1]
                            if '::' in new_name:
                                new_name = new_name.split('::')[0]
                            if new_name.startswith('http'):
                                new_name = new_name.rsplit('/')[-1]
                                new_name = urllib.parse.unquote(new_name)
                            new_value = new_name + '\t' + old_name
                            self.ui.epn_arr_list[row] = new_value
                            listitem = self.item(row)
                            if listitem:
                                listitem.setText(new_name)
                    write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
    
    def edit_name_in_group(self, row):
        site = self.ui.get_parameters_value(s='site')['site']
        start_point = row
        end_point = len(self.ui.epn_arr_list)
        default_text = 'Episode-{'+str(row)+'-'+str(end_point-1)+'}'
        item, ok = QtWidgets.QInputDialog.getText(
            MainWindow, 'Input Dialog', 'Enter Naming pattern', 
            QtWidgets.QLineEdit.Normal, default_text)
        if item and ok:
            try:
                nmval = re.search('[^\{]*', item).group()
                nmval2 = re.search('\}[^"]*', item).group()
                nmval2 = re.sub('\}', '', nmval2, 1)
                range_val = re.search('\{[^}]*', item).group()
                range_val = re.sub('\{', '', range_val)
                range_start, range_end = range_val.split('-')
                range_start = int(range_start.strip())
                range_end = int(range_end.strip())
                if range_end > 100:
                    size = 3
                else:
                    size = 2
                error_in_processing = False
            except Exception as err:
                print(err, '--141---')
                error_in_processing = True
            
            if error_in_processing:
                msg = 'Bad Input Data Entered. Enter in format: NewName{start-end}'
                send_notification(msg)
            elif site.lower() == 'video':
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                conn = sqlite3.connect(video_db)
                cur = conn.cursor()
                end_point = len(self.ui.epn_arr_list)
                new_row = range_start
                for row in range(start_point, end_point):
                    old_value = self.ui.epn_arr_list[row]
                    path = old_value.split('	')[1]
                    if size == 2:
                        if new_row < 10:
                            new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                        else:
                            new_name = nmval + str(new_row) + nmval2
                    elif size == 3:
                        if new_row < 10:
                            new_name = '{0}00{1}{2}'.format(nmval, new_row, nmval2)
                        elif new_row >= 10 and new_row < 100:
                            new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                        else:
                            new_name = nmval + str(new_row) + nmval2
                    qr = 'Update Video Set EP_NAME=? Where Path=?'
                    cur.execute(qr, (new_name, path))
                    tmp = re.sub('[^	]*', new_name, old_value, 1)
                    self.ui.epn_arr_list[row] = tmp
                    listitem = self.item(row)
                    if listitem:
                        listitem.setText(new_name)
                    new_row = new_row + 1
                    if new_row > range_end:
                        break
                conn.commit()
                conn.close()
                old_value = self.ui.epn_arr_list[start_point]
                path = old_value.split('	')[1]
                dir_path, file_path = os.path.split(path)
                if dir_path in self.ui.video_dict:
                    del self.ui.video_dict[dir_path]
            elif (site.lower() == 'playlists' or site.lower() == 'music' 
                    or site.lower() == 'none'):
                msg = 'Batch Renaming not allowed in Music and Playlist section'
                send_notification(msg)
            else:
                file_path = ''
                param_dict = self.ui.get_parameters_value(s='siteName', n='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site.lower() == "subbedanime" or site.lower() == "dubbedanime":
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                else:
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.isfile(file_path):
                    end_point = len(self.ui.epn_arr_list)
                    new_row = range_start
                    for row in range(start_point, end_point):
                        old_value = self.ui.epn_arr_list[row]
                        if '\t' in old_value:
                            path = old_value.split('\t')[1]
                        else:
                            path = old_value
                        if size == 2:
                            if new_row < 10:
                                new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                            else:
                                new_name = nmval + str(new_row) + nmval2
                        elif size == 3:
                            if new_row < 10:
                                new_name = '{0}00{1}{2}'.format(nmval, new_row, nmval2)
                            elif new_row >= 10 and new_row < 100:
                                new_name = '{0}0{1}{2}'.format(nmval, new_row, nmval2)
                            else:
                                new_name = nmval + str(new_row) + nmval2
                        if '\t' in old_value:
                            tmp = re.sub('[^	]*', new_name, old_value, 1)
                        else:
                            tmp = new_name + '\t' + old_value
                        self.ui.epn_arr_list[row] = tmp
                        listitem = self.item(row)
                        if listitem:
                            listitem.setText(new_name)
                        new_row = new_row + 1
                        if new_row > range_end:
                            break
                    write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
    
    def move_playlist_items(self, src_row, dest_row, action=None):
        row = src_row
        nrow = dest_row
        param_dict = self.ui.get_parameters_value(s='site', o='opt', b='bookmark')
        site = param_dict['site']
        opt = param_dict['opt']
        bookmark = param_dict['bookmark']
        update_pls = False
        item = None
        logger.debug('{}::{}::{}'.format(opt, row, site))
        if ((site == "PlayLists" or self.ui.music_playlist or opt == 'History')
                and site != "Video" and row in range(0, self.count())):
            file_path = ""
            param_dict = self.ui.get_parameters_value(sn='siteName', nm='name')
            siteName = param_dict['siteName']
            name = param_dict['name']
            if site == "SubbedAnime" or site == "DubbedAnime":
                if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            elif site == "PlayLists" or self.ui.music_playlist:
                pls = ''
                if self.ui.list1.currentItem():
                    pls = self.ui.list1.currentItem().text()
                if pls:
                    file_path = os.path.join(home, 'Playlists', pls)
            else:
                if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            if os.path.exists(file_path):
                lines = open_files(file_path, True)
                length = len(lines)
                if ((row > 0 and action == 'pgup') or (row < length -1 and action == 'pgdown')):
                    if row == length - 1:
                        t = lines[row].replace('\n', '')+'\n'
                        lines[row] = lines[nrow].replace('\n', '')
                        lines[nrow] = t
                    else:
                        t = lines[row]
                        lines[row] = lines[nrow]
                        lines[nrow] = t
                elif row == 0 and action == 'pgup':
                    rowitem = lines[0].strip()
                    del lines[0]
                    lines.append(rowitem)
                else:
                    rowitem = lines.pop().strip()
                    lines.insert(0, rowitem)
                self.ui.epn_arr_list = [i.strip() for i in lines if i.strip()]
                write_files(file_path, lines, line_by_line=True)
                update_pls = True
                item = self.item(row)
            if self.ui.gapless_playback:
                self.ui.use_playlist_method()
        elif site == "Video":
            item = self.item(row)
            bookmark = self.ui.get_parameters_value(b='bookmark')['bookmark']
            if item:
                if not bookmark:
                    video_db = os.path.join(home, 'VideoDB', 'Video.db')
                    conn = sqlite3.connect(video_db)
                    cur = conn.cursor()
                    if ((row > 0 and action == 'pgup') or (row < len(self.ui.epn_arr_list) - 1
                            and action == 'pgdown')):
                        txt = self.ui.epn_arr_list[row].split('	')[1]
                        cur.execute('Select EPN FROM Video Where Path=?', (txt, ))
                        rows = cur.fetchall()
                        num1 = int(rows[0][0])
                        txt1 = self.ui.epn_arr_list[nrow].split('	')[1]
                        self.ui.epn_arr_list[row], self.ui.epn_arr_list[nrow] = self.ui.epn_arr_list[nrow], self.ui.epn_arr_list[row]
                        cur.execute('Select EPN FROM Video Where Path=?', (txt1, ))
                        rows = cur.fetchall()
                        num2 = int(rows[0][0])
                        logger.debug('num2={}'.format(num2))
                        qr = 'Update Video Set EPN=? Where Path=?'
                        cur.execute(qr, (num2, txt))
                        qr = 'Update Video Set EPN=? Where Path=?'
                        cur.execute(qr, (num1, txt1))
                        update_pls = True
                        conn.commit()
                        conn.close()
                    elif row == 0 and action == 'pgup':
                        txt = self.ui.epn_arr_list[-1].split('	')[1]
                        length = len(self.ui.epn_arr_list)
                        for rowint, row_item in enumerate(self.ui.epn_arr_list):
                            txt = row_item.split('\t')[1]
                            num = rowint - 1
                            if num < 0:
                                num = num % length
                            print(num, '---num2')
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num, txt))
                        first_txt = self.ui.epn_arr_list[0]
                        del self.ui.epn_arr_list[0]
                        self.ui.epn_arr_list.append(first_txt)
                        conn.commit()
                        conn.close()
                        update_pls = True
                    else:
                        length = len(self.ui.epn_arr_list)
                        txt = self.ui.epn_arr_list[0].split('\t')[1]
                        for rowint, row_item in enumerate(self.ui.epn_arr_list):
                            txt = row_item.split('\t')[1]
                            num = rowint + 1
                            if num >= length:
                                num = num % length
                            logger.debug('num2={}'.format(num))
                            qr = 'Update Video Set EPN=? Where Path=?'
                            cur.execute(qr, (num, txt))
                        last_txt = self.ui.epn_arr_list[-1]
                        del self.ui.epn_arr_list[-1]
                        self.ui.epn_arr_list.insert(0, last_txt)
                        update_pls = True
                        conn.commit()
                        conn.close()
                    dir_path, file_path = os.path.split(txt)
                    if dir_path in self.ui.video_dict:
                        del self.ui.video_dict[dir_path]
                    if self.ui.gapless_playback:
                        self.ui.use_playlist_method()
        if update_pls and item:
            row_n = None
            if ((row > 0 and action == 'pgup') or (row < len(self.ui.epn_arr_list) - 1
                    and action == 'pgdown')):
                self.takeItem(row)
                self.insertItem(nrow, item)
                row_n = nrow
            elif row == 0 and action == 'pgup':
                self.takeItem(row)
                self.addItem(item)
                row_n = len(self.ui.epn_arr_list) - 1
            else:
                self.takeItem(row)
                self.insertItem(0, item)
                row_n = 0
            if row_n is not None:
                self.setCurrentRow(row_n)
                
    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Left):
            self.ui.tab_5.setFocus()
        elif (event.key() == QtCore.Qt.Key_F2):
            if self.ui.epn_arr_list:
                print('F2 Pressed')
                if self.currentItem():
                    self.edit_name_list2(self.currentRow())
        elif (event.key() == QtCore.Qt.Key_F3):
            if self.ui.epn_arr_list:
                print('F3 Pressed')
                if self.currentItem():
                    self.edit_name_in_group(self.currentRow())
        elif (event.key() == QtCore.Qt.Key_F4):
            if self.ui.epn_arr_list:
                print('Default Name')
                for item in self.selectedItems():
                    r = self.row(item)
                    self.get_default_name(r, mode='default')
        elif (event.key() == QtCore.Qt.Key_F5):
            if self.ui.epn_arr_list:
                print('Batch Renaming in database')
                if self.currentItem():
                    self.get_default_name(self.currentRow(), mode='default_all')
        elif (event.key() == QtCore.Qt.Key_F6):
            if self.ui.list1.currentItem():
                row = self.ui.list1.currentRow()
            else:
                row = 0
            if self.currentItem():
                self.set_search_backend(row)
        elif (event.key() == QtCore.Qt.Key_F7):
            if self.ui.list1.currentItem():
                row = self.ui.list1.currentRow()
            else:
                row = 0
            if self.currentItem():
                self.set_search_backend(row, use_search='ddg')
        elif (event.key() == QtCore.Qt.Key_F8):
            if self.ui.list1.currentItem():
                row = self.ui.list1.currentRow()
            else:
                row = 0
            if self.currentItem():
                self.set_search_backend(row, use_search='g')
        elif event.key() == QtCore.Qt.Key_F9:
            self.get_default_name(0, mode='from_summary')
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Up):
            self.setCurrentRow(0)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Down):
            self.setCurrentRow(self.count()-1)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_D):
            item, ok = QtWidgets.QInputDialog.getText(
                MainWindow, 'Input Dialog', 'Enter Upload Speed in KB\n0 means unlimited', 
                QtWidgets.QLineEdit.Normal, str(self.ui.setuploadspeed))
            if item and ok:
                if item.isnumeric():
                    self.ui.setuploadspeed = int(item)
                else:
                    send_notification('wrong values')
        elif event.key() == QtCore.Qt.Key_Return:
            self.ui.epnClicked(dock_check=True)
        elif event.key() == QtCore.Qt.Key_Backspace:
            if self.ui.list1.isHidden() and self.ui.list1.count() > 0:
                self.hide()
                self.ui.goto_epn.hide()
                self.ui.list1.show()
                self.ui.list1.setFocus()
                show_hide_playlist = 0
                show_hide_titlelist = 1
                self.ui.set_parameters_value(show_hide_pl=show_hide_playlist,
                                        show_hide_tl=show_hide_titlelist)
        elif event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                self.downcount += 1
                if self.downcount > self.count_limit:
                    self.setCurrentRow(0)
                    self.downcount = 0
            else:
                self.downcount = 0
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if prev_r == -1:
                self.upcount += 1
                if self.upcount > self.count_limit:
                    self.setCurrentRow(self.count()-1)
                    self.upcount = 0
            else:
                self.upcount = 0
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_W:
            self.ui.watchToggle()
        elif (event.modifiers() == QtCore.Qt.ControlModifier and 
                event.key() == QtCore.Qt.Key_Q):
            if self.ui.player_val == "libmpv":
                self.ui.gui_signals.queue_item("keyboard_shortcut")
            else:
                self.queue_item()
        elif event.key() == QtCore.Qt.Key_Delete:
            param_dict = self.ui.get_parameters_value(s='site', b='bookmark', o='opt')
            site = param_dict['site']
            bookmark = param_dict['bookmark']
            opt = param_dict['opt']
            row_val = self.currentRow()
            if site == 'None':
                print("Nothing To Delete")
            elif site == "Video":
                r = self.currentRow()
                item = self.item(r)
                if item:
                    if not bookmark:
                        video_db = os.path.join(home, 'VideoDB', 'Video.db')
                        conn = sqlite3.connect(video_db)
                        cur = conn.cursor()
                        txt = self.ui.epn_arr_list[r].split('	')[1]
                        cur.execute('Delete FROM Video Where Path=?', (txt, ))
                        logger.info('Deleting Directory From Database : '+txt)
                        del self.ui.epn_arr_list[r]
                        
                        if r < len(self.ui.epn_arr_list):
                            for index in range(r, len(self.ui.epn_arr_list)):
                                path_update = self.ui.epn_arr_list[index].split('	')[1]
                                qr = 'Update Video Set EPN=? Where Path=?'
                                cur.execute(qr, (index, path_update))
                        
                        conn.commit()
                        conn.close()
                        self.takeItem(r)
                        del item
                        dir_path, file_path = os.path.split(txt)
                        if dir_path in self.ui.video_dict:
                            del self.ui.video_dict[dir_path]
                        if self.ui.gapless_playback:
                            self.ui.use_playlist_method()
            elif (site != "PlayLists" and site != "Video" and site != "Music" 
                    and opt == "History"):
                row = self.currentRow()
                file_path = ""
                param_dict = self.ui.get_parameters_value(sn='siteName', nm='name')
                siteName = param_dict['siteName']
                name = param_dict['name']
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
                else:
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if file_path and self.ui.epn_arr_list:
                    item = self.item(row)
                    self.takeItem(row)
                    del self.ui.epn_arr_list[row]
                    del item
                    write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
                    self.ui.update_list2()
                else:
                    pass
            elif site == "PlayLists" or self.ui.music_playlist:
                pls = ''
                if site == "Music":
                    r = self.ui.list1.currentRow()
                    if self.ui.list1.item(r):
                        pls = str(self.ui.list1.item(r).text())
                else:
                    if self.ui.list1.currentItem():
                        pls = self.ui.list1.currentItem().text()
                if pls:
                    file_path = os.path.join(home, 'Playlists', pls)
                    row = self.currentRow()
                    item = self.item(row)
                    if item and os.path.exists(file_path):
                        self.takeItem(row)
                        del item
                        del self.ui.epn_arr_list[row]
                        write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
                        if self.ui.gapless_playback:
                            self.ui.use_playlist_method()
            if row_val < self.count():
                self.setCurrentRow(row_val)
        elif event.key() == QtCore.Qt.Key_PageUp:
            row = self.currentRow()
            nrow = row - 1
            self.move_playlist_items(row, nrow, action='pgup')
        elif event.key() == QtCore.Qt.Key_PageDown:
            row = self.currentRow()
            nrow = row + 1
            self.move_playlist_items(row, nrow, action='pgdown')
        elif event.key() == QtCore.Qt.Key_Left:
            if self.ui.float_window.isHidden():
                if not self.ui.list1.isHidden():
                    self.ui.list1.setFocus()
                elif not self.ui.list_poster.isHidden():
                    self.ui.list_poster.setFocus()
                else:
                    self.ui.list1.keyPressEvent(event)
            else:
                prev_r = self.currentRow() - 1
                if self.currentRow() == 0:
                    self.setCurrentRow(0)
                else:
                    self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_Right:
            if self.ui.float_window.isHidden():
                pass
            else:
                nextr = self.currentRow() + 1
                if nextr == self.count():
                    self.setCurrentRow(self.count()-1)
                else:
                    self.setCurrentRow(nextr)
            if self.ui.auto_hide_dock:
                self.ui.dockWidget_3.hide()
        elif (event.modifiers() == QtCore.Qt.ControlModifier and 
                event.key() == QtCore.Qt.Key_O):
            self.init_offline_mode()
        elif event.key() == QtCore.Qt.Key_2: 
            mirrorNo = 2
            msg = "Mirror No. 2 Selected"
            self.ui.set_parameters_value(mir=mirrorNo)
            send_notification(msg)
        elif event.key() == QtCore.Qt.Key_4: 
            mirrorNo = 4
            msg = "Mirror No. 4 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_5: 
            mirrorNo = 5
            msg = "Mirror No. 5 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_3: 
            mirrorNo = 3
            msg = "Mirror No. 3 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_1: 
            mirrorNo = 1
            msg = "Mirror No. 1 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_6: 
            mirrorNo = 6
            msg = "Mirror No. 6 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_7: 
            mirrorNo = 7
            msg = "Mirror No. 7 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_8: 
            mirrorNo = 8
            msg = "Mirror No. 8 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_9: 
            mirrorNo = 9
            msg = "Mirror No. 9 Selected"
            send_notification(msg)
            self.ui.set_parameters_value(mir=mirrorNo)
        elif event.key() == QtCore.Qt.Key_F and self.ui.mpvplayer_val.processId() > 0:
            if not MainWindow.isHidden():
                param_dict = self.ui.get_parameters_value(t='total_till')
                total_till = param_dict['total_till']
                if not MainWindow.isFullScreen():
                    self.ui.gridLayout.setSpacing(0)
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                    self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                    self.ui.text.hide()
                    self.ui.label.hide()
                    self.ui.frame1.hide()
                    self.ui.tab_6.hide()
                    self.ui.goto_epn.hide()
                    #self.ui.btn20.hide()
                    if self.ui.wget.processId() > 0 or self.ui.video_local_stream:
                        self.ui.progress.hide()
                        if not self.ui.torrent_frame.isHidden():
                            self.ui.torrent_frame.hide()
                    self.hide()
                    self.ui.list6.hide()
                    self.ui.list1.hide()
                    self.ui.frame.hide()
                    self.ui.tab_5.show()
                    self.ui.tab_5.setFocus()
                    if (self.ui.player_val == "mplayer" or self.ui.player_val == "mpv"):
                        MainWindow.setCursor(QtGself.ui.QCursor(QtCore.Qt.BlankCursor))
                    MainWindow.showFullScreen()
                else:
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    self.show()
                    self.ui.btn20.show()
                    if self.ui.wget.processId() > 0:
                        self.ui.goto_epn.hide()
                        self.ui.progress.show()

                    self.ui.frame1.show()
                    if self.ui.player_val == "mplayer" or self.ui.player_val == "mpv":
                        MainWindow.setCursor(QtGself.ui.QCursor(QtCore.Qt.ArrowCursor))
                    MainWindow.showNormal()
                    MainWindow.showMaximized()
                    if total_till != 0:
                        self.ui.tab_6.show()
                        self.hide()
                        self.ui.goto_epn.hide()
            else:
                if not self.ui.float_window.isHidden():
                    if not self.ui.float_window.isFullScreen():
                        self.ui.float_window.showFullScreen()
                    else:
                        self.ui.float_window.showNormal()
        elif event.text().isalnum():
            self.ui.focus_widget = self
            if self.ui.search_on_type_btn.isHidden():
                g = self.geometry()
                txt = event.text()
                self.ui.search_on_type_btn.setGeometry(g.x(), g.y(), self.width(), 32)
                self.ui.search_on_type_btn.show()
                self.ui.search_on_type_btn.clear()
                self.ui.search_on_type_btn.setText(txt)
            else:
                self.ui.search_on_type_btn.setFocus()
                txt = self.ui.search_on_type_btn.text()
                new_txt = txt+event.text()
                self.ui.search_on_type_btn.setText(new_txt)
        else:
            super(PlaylistWidget, self).keyPressEvent(event)

    def triggerPlaylist(self, value):
        print('Menu Clicked')
        print(value)
        file_path = os.path.join(home, 'Playlists', str(value))
        logger.info(file_path)
        site = self.ui.get_parameters_value(s='site')['site']
        if (site == "Music" or site == "Video" or site == "Local" 
                or site == "None" or site == 'PlayLists' or site == 'MyServer'):
            if os.path.exists(file_path):
                new_name = ''
                for item in self.selectedItems():
                    i = self.row(item)
                    sumr = self.ui.epn_arr_list[i].split('	')[0]
                    try:
                        rfr_url = self.ui.epn_arr_list[i].split('	')[2]
                    except:
                        rfr_url = "NONE"
                    sumry = self.ui.epn_arr_list[i].split('	')[1]
                    sumry = sumry.replace('"', '')
                    sumry = '"'+sumry+'"'
                    t = sumr+'	'+sumry+'	'+rfr_url
                    if new_name:
                        new_name = new_name + '\n' + t
                    else:
                        new_name = t
                if new_name:
                    write_files(file_path, new_name, line_by_line=True)
        else:
            param_dict = self.ui.get_parameters_value(f='finalUrlFound', r='refererNeeded')
            finalUrlFound = param_dict['finalUrlFound']
            refererNeeded = param_dict['refererNeeded']
            finalUrl = self.ui.epn_return(self.currentRow())
            t = ''
            sumr = self.item(self.currentRow()).text().replace('#', '', 1)
            sumr = sumr.replace(self.ui.check_symbol, '')
            if os.path.exists(file_path):
                if isinstance(finalUrl, list):
                    if finalUrlFound and refererNeeded:
                        rfr_url = finalUrl[1]
                        sumry = str(finalUrl[0])
                        t = sumr+'	'+sumry+'	'+rfr_url
                    else:
                        rfr_url = "NONE"
                        j = 1
                        t = ''
                        for i in finalUrl:
                            p = "-Part-"+str(j)
                            sumry = str(i)
                            if j == 1:
                                t = sumr+p+'	'+sumry+'	'+rfr_url
                            else:
                                t = t + '\n' + sumr+p+'	'+sumry+'	'+rfr_url
                            j = j+1
                else:
                    rfr_url = "NONE"
                    sumry = str(finalUrl)
                    t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)

    def fix_order(self):
        param_dict = self.ui.get_parameters_value(o='opt', s='site', b='bookmark',
                                             n='name')
        opt = param_dict['opt']
        site = param_dict['site']
        bookmark = param_dict['bookmark']
        name = param_dict['name']
        row = self.currentRow()
        item = self.item(row)
        if item:
            if site == "Video":
                txt = None
                if not bookmark:
                    video_db = os.path.join(home, 'VideoDB', 'Video.db')
                    conn = sqlite3.connect(video_db)
                    cur = conn.cursor()
                    for num in range(len(self.ui.epn_arr_list)):
                        txt = self.ui.epn_arr_list[num].split('	')[1]
                        qr = 'Update Video Set EPN=? Where Path=?'
                        cur.execute(qr, (num, txt))
                    conn.commit()
                    conn.close()
                    if txt:
                        dir_path, file_path = os.path.split(txt)
                        if dir_path in self.ui.video_dict:
                            del self.ui.video_dict[dir_path]
            elif site == "Music" and self.ui.list3.currentItem():
                go_next = True
                if self.ui.list3.currentItem().text() == "Playlist":
                    go_next = True
                else:
                    go_next = False
                if go_next:
                    pls = ''
                    file_path = ''
                    if self.ui.list1.currentItem():
                        pls = self.ui.list1.currentItem().text()
                    if pls:
                        file_path = os.path.join(home, 'Playlists', pls)
                    if os.path.exists(file_path):
                        write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
            elif (opt == "History" or site == "PlayLists") and row > 0 and site != "Video":
                file_path = ""
                if site == "PlayLists":
                    if self.ui.list1.currentItem():
                        pls = self.ui.list1.currentItem().text()
                        file_path = os.path.join(home, 'Playlists', pls)
                elif site == "Local":
                    if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                        file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
                if os.path.exists(file_path):
                    abs_path = os.path.join(TMPDIR, 'tmp.txt')
                    logger.info('--file-path--{0}'.format(file_path))
                    writing_failed = False
                    if os.path.exists(file_path):
                        write_files(file_path, self.ui.epn_arr_list, line_by_line=True)
    
    def show_web_menu(self):
        ip = self.ui.slave_address
        request_url = 'stream_continue.htm'
        addr = None
        if '127.0.0.1' in ip:
            send_notification('You have not setup slave address properly')
        elif not ip.startswith('http') and not ip.startswith('https'):
            addr = 'http://{}/{}'.format(ip, request_url)
        elif ip.endswith('/'):
            addr = '{}{}'.format(ip, request_url)
        else:
            addr = '{}/{}'.format(ip, request_url)
        print(addr, ip, request_url)
        if addr:
            self.ui.btnWebReviews_search.setText(addr)
            self.ui.webHide()
            self.ui.reviewsWeb(action='return_pressed')
    
    def clear_slave_session(self):
        ip = self.ui.slave_address
        request_url = 'logout'
        addr = None
        if '127.0.0.1' in ip:
            send_notification('You have not setup slave address properly')
        elif not ip.startswith('http') and not ip.startswith('https'):
            addr = 'http://{}/{}'.format(ip, request_url)
        elif ip.endswith('/'):
            addr = '{}{}'.format(ip, request_url)
        else:
            addr = '{}/{}'.format(ip, request_url)
        n = urlparse(addr)
        netloc = n.netloc
        val = self.ui.vnt.cookie_session.get(netloc)
        verify = self.verify_slave_ssl
        print(addr, ip, request_url, netloc, val, verify)
        logger.debug('url={} verify={}'.format(addr, verify))
        if val:
            self.ui.vnt.get(addr, session=True, verify=verify, timeout=60)
            del self.ui.vnt.cookie_session[netloc]
        else:
            self.ui.vnt.get(addr, timeout=60, verify=verify)
    
    def setup_slave_address(self, ipaddr=None):
        file_path = os.path.join(self.ui.home_folder, 'slave.txt')
        if ipaddr:
            item = ipaddr
            ok = True
        else:
            item = '127.0.0.1:9001'
            if os.path.isfile(file_path):
                ip_addr = open_files(file_path, False)
            else:
                ip_addr = ''
            item, ok = QtWidgets.QInputDialog.getText(
                MainWindow, 'Input Dialog', 'Enter IP Address of Slave\nExample: http://192.168.2.3:9001',
                QtWidgets.QLineEdit.Normal, ip_addr
                )
        if ok and item:
            n = urlparse(item)
            scheme = n.scheme
            netloc = n.netloc
            if not scheme:
                scheme = 'http'
            if not netloc:
                netloc = n.path
            item = scheme + '://' + netloc
            with open(file_path, 'w') as f:
                f.write(item)
            msg = ('Address of Slave is set to {}, now start media server\
                    and cast single item or playlist'.format(item))
            msg = re.sub(' +', ' ', msg)
            send_notification(msg)
            logger.info(msg)
        self.ui.slave_address = item.strip()
        return item
    
    def check_local_subtitle(self, path, external=None):
        result = None
        ext = ['.srt', '.ass', '.en.srt', '.en.ass', '.en.vtt']
        extension = None
        if os.path.exists(path) or external:
            if '.' in path:
                nm = path.rsplit('.', 1)[0]
                for i in ext:
                    sub_name = nm + i
                    if os.path.exists(sub_name):
                        result = sub_name
                        extension = i
                        break
        return (result, extension)
    
    def send_subtitle_method(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames(
                MainWindow, 'Select One or More Files', self.ui.last_dir)
        sub_dict = {}
        if fname:
            logger.info(fname)
            if fname[0]:
                for i in fname[0]:
                    self.ui.last_dir, file_choose = os.path.split(i)
                    if '.' in i:
                        ext = i.rsplit('.', 1)[1]
                    else:
                        ext = None
                    check_local_sub = i
                    if ext in ['srt', 'ass', 'vtt']:
                        if os.name == 'nt':
                            try:
                                content = open(check_local_sub, mode='r', encoding='utf-8-sig').read()
                            except Exception as err:
                                logger.error(err)
                                content = open_files(check_local_sub, False)
                        else:
                            content = open_files(check_local_sub, False)
                        sub_dict.update({ext:content})
                    logger.debug('{}::{}'.format(i, file_choose))
                    sub_json = os.path.join(self.ui.tmp_download_folder, 'sub.json')
                    if sub_dict:
                        file_path = os.path.join(self.ui.home_folder, 'slave.txt')
                        if os.path.isfile(file_path):
                            item = open_files(file_path, False)
                            item = item.strip()
                            with open(sub_json, 'w') as f:
                                json.dump(sub_dict, f)
                            if not item.startswith('http') and not item.startswith('https'):
                                item = 'http://{}/sending_subtitle'.format(item)
                            elif item.endswith('/'):
                                item = '{}sending_subtitle'.format(item)
                            else:
                                item = '{}/sending_subtitle'.format(item)
                            n = urlparse(item)
                            netloc = n.netloc
                            val = self.ui.vnt.cookie_session.get(netloc)
                            verify = self.verify_slave_ssl
                            logger.debug('url={} verify={}'.format(item, verify))
                            if val:
                                self.ui.vnt.post(item, session=True, verify=verify,
                                            files=sub_json, timeout=60)
                            else:
                                self.ui.vnt.post(item, files=sub_json, timeout=60, verify=verify)
                        else:
                            send_notification('Slave IP Address not set')
                       
                            
    def start_pc_to_pc_casting(self, mode, row, browser_data=None, direct_link=None):
        cur_row = str(row)
        file_path = os.path.join(self.ui.home_folder, 'slave.txt')
        if not os.path.isfile(file_path):
            item = self.setup_slave_address()
        else:
            item = open_files(file_path, False)
            self.ui.slave_address = item
        item = item.strip()
        ipval = item
        http_val = "http"
        if self.ui.https_media_server:
            http_val = "https"
        if mode == "play quick":
            if not item.startswith('http') and not item.startswith('https'):
                item = 'http://{}/{}'.format(item, direct_link)
            elif item.endswith('/'):
                item = '{}{}'.format(item, direct_link)
            else:
                item = '{}/{}'.format(item, direct_link)
            logger.debug(item)
            self.ui.vnt.get(item, binary=True, timeout=60, verify=False) 
        elif browser_data:
            self.process_pc_to_pc_casting(mode, row, item, browser_data)
        elif mode == 'direct index':
            self.process_pc_to_pc_casting(mode, row, item, [])
        else:
            ip = '{}://{}:{}/stream_continue.m3u'.format(http_val, str(self.ui.local_ip_stream), str(self.ui.local_port_stream))
            self.ui.vnt.get(ip, binary=True, timeout=60, verify=False,
                            onfinished=partial(self.process_pc_to_pc_casting, mode, row, item))

    def process_browser_based_url(self, title, url, mode):
        pls_txt = '#EXTM3U\n'
        if title:
            title = title.split("\n")[0]
        else:
            title = "Title not Available"
        pls_txt = pls_txt+'#EXTINF:0, {0}\n{1}\n'.format(title, url)
        browser_data = BrowserData(pls_txt)
        self.start_pc_to_pc_casting(mode, 0, browser_data)
        
    def process_pc_to_pc_casting(self, mode, cur_row, item, *args):
        item = item.strip()
        direct_link = False
        if args and hasattr(args[-1], "html"):
            content = args[-1].html
        elif mode == "direct index":
            content = b"Not required"
        else:
            content = None
        if isinstance(args[-1], BrowserData):
            direct_link = args[-1].direct_link
        if content:
            self.ui.slave_live_status = True
            self.ui.gui_signals.first_time = True
            content = content.decode('utf-8')
            lines = content.split('\n')
            new_dict = OrderedDict()
            new_lines = []
            direct_url_link = None
            if mode == "direct url":
                line1 = "#EXTINF:0, {}".format(self.ui.epn_name_in_list)
                line2 = self.ui.final_playing_url
                if line2.startswith("http"):
                    new_lines = [line1, line2]
                    direct_url_link = line2
                else:
                    mode = "single"
            if mode in ['single', 'playlist', 'queue', 'direct url'] and item:
                if mode in ['single', 'queue']:
                    line1 = lines[2*cur_row+1]
                    line2 = lines[2*cur_row+2]
                    new_lines = [line1, line2]
                elif mode == "direct url":
                    pass
                else:
                    lines = lines[1:]
                    new_lines = [i.strip() for i in lines if i.strip()]
                i = 0
                uid = str(uuid.uuid4())
                if len(self.ui.master_access_tokens) > 100:
                    self.ui.master_access_tokens.pop()
                self.ui.master_access_tokens.add(uid)
                for row in range(0, len(new_lines), 2):
                    master_token = True
                    title = new_lines[row]
                    title = title.split(',', 1)[-1].strip()
                    url = new_lines[row+1]
                    if direct_link or mode == "direct index":
                        master_token = False
                    else:
                        try:
                            nurl = self.ui.if_path_is_rel(urllib.parse.urlparse(url).path[1:].rsplit('/', 1)[0],
                                                          abs_path=True, from_master=True)
                            nurl_netloc = urllib.parse.urlparse(nurl).netloc
                            if 'youtube.com' in nurl_netloc:
                                url = nurl
                                master_token = False
                            elif mode == "direct url" and direct_url_link:
                                url = direct_url_link
                                master_token = False
                        except Exception as err:
                            logger.error(err)
                    url = url.replace('abs_path=', 'master_abs_path=', 1)
                    if 'relative_path=' in url:
                        url = url.replace('relative_path=', 'master_relative_path=', 1)
                    if master_token:
                        if url.endswith('/'):
                            url = '{}&master_token={}&'.format(url, uid)
                        else:
                            url = '{}/&master_token={}&'.format(url, uid)
                    local_path = None
                    sub = 'none'
                    ext = 'none'
                    if ui.epn_arr_list and '\t' in self.ui.epn_arr_list[i]:
                        local_path = self.ui.epn_arr_list[i].split('\t')[1]
                    if local_path:
                        local_path = local_path.replace('"', '')
                        if os.path.isfile(local_path):
                            sub, ext = self.check_local_subtitle(local_path)
                            if sub:
                                sub = url + '.original.subtitle'
                            else:
                                sub = 'none'
                    new_dict.update(
                            {
                                str(row):{
                                    'url':url, 'title':title,
                                    'artist': 'None', 'play_now':cur_row,
                                    'sub':sub, 'sub-ext':ext
                                    }
                            }
                        )
                    i += 1
                pls_file = os.path.join(self.ui.tmp_download_folder, 'playlist.json')
                with open(pls_file, 'w') as f:
                    json.dump(new_dict, f)
                if mode == 'queue':
                    request_url = 'sending_queueitem'
                else:
                    request_url = 'sending_playlist'
                if not item.startswith('http') and not item.startswith('https'):
                    item = 'http://{}/{}'.format(item, request_url)
                elif item.endswith('/'):
                    item = '{}{}'.format(item, request_url)
                else:
                    item = '{}/{}'.format(item, request_url)
                n = urlparse(item)
                netloc = n.netloc
                val = self.ui.vnt.cookie_session.get(netloc)
                verify = self.verify_slave_ssl
                logger.debug('url={} verify={}'.format(item, verify))
                if val:
                    logger.debug('using old session')
                    self.ui.vnt.post(item, timeout=60, files=pls_file, session=True, verify=verify,
                                onfinished=partial(self.final_pc_to_pc_process, pls_file, verify))
                else:
                    self.ui.vnt.post(item, files=pls_file, timeout=60, verify=verify,
                                onfinished=partial(self.final_pc_to_pc_process, pls_file, verify))
            elif mode == "direct index":
                request_url = "playlist_{}".format(cur_row)
                if not item.startswith('http') and not item.startswith('https'):
                    item = 'http://{}/{}'.format(item, request_url)
                elif item.endswith('/'):
                    item = '{}{}'.format(item, request_url)
                else:
                    item = '{}/{}'.format(item, request_url)
                n = urlparse(item)
                netloc = n.netloc
                val = self.ui.vnt.cookie_session.get(netloc)
                verify = self.verify_slave_ssl
                pls_file = ""
                logger.debug('url={} verify={}'.format(item, verify))
                if val:
                    logger.debug('using old session')
                    self.ui.vnt.get(item, timeout=60, session=True, verify=verify, onfinished=partial(self.final_pc_to_pc_process, pls_file, verify))
                else:
                    self.ui.vnt.get(item, timeout=60, verify=verify, onfinished=partial(self.final_pc_to_pc_process, pls_file, verify))
        else:
            msg = 'Most Probably Media Server not started on Master.'
            logger.error(msg)
            logger.error(args[-1].error)
            send_notification(msg)
    
    def final_pc_to_pc_process(self, pls_file, verify, *args):
        r = args[-1]
        content = r.html
        if not content:
            err = r.error
            url = args[-2]
            logger.debug(err)
            if 'http error 401' in err.lower():
                self.ui.gui_signals.login_required(url, pls_file, verify)
            elif 'certificate verify failed' in err.lower():
                self.ui.vnt.post(url, files=pls_file, timeout=60, verify=False,
                            onfinished=partial(self.final_pc_to_pc_process, pls_file, False))
                self.verify_slave_ssl = False
            elif 'errno 113' in err.lower():
                msg = ('Slave is unreachable. Wrong IP address of slave!')
                logger.error(msg)
                send_notification(msg)
            elif 'errno 104' in err.lower():
                msg = ('Connection reset. Most Probably wrong http/https prefix to slave address')
                logger.error(msg)
                send_notification(msg)
            else:
                msg = ('Most Probably slave ip address is wrong or slave server\
                        is not running or misconfigured, or wrong http/https prefix to slave address')
                msg = re.sub('  +', ' ', msg)
                logger.error(msg)
                send_notification(msg)
        else:
            self.start_remote_status(args[-2])
            
    def start_remote_status(self, url):
        n = urlparse(url)
        nurl = n.scheme + '://' + n.netloc + '/get_remote_control_status'
        val = self.ui.vnt.cookie_session.get(n.netloc)
        verify = self.verify_slave_ssl
        if val:
            self.ui.vnt.get(nurl, session=True, verify=verify, timeout=60, onfinished=self.get_remote_status)
        else:
            self.ui.vnt.get(nurl, timeout=60, verify=verify, onfinished=self.get_remote_status)
    
    def get_remote_status(self, *args):
        r = args[-1]
        content = r.html
        url = args[-2]
        if content and self.ui.slave_live_status:
            self.ui.slave_status_string = content
            if self.ui.extra_toolbar_control == 'slave' and self.ui.mpvplayer_val.processId() == 0:
                self.ui.gui_signals.slave_status(content)
            n = urlparse(url)
            val = self.ui.vnt.cookie_session.get(n.netloc)
            verify = self.verify_slave_ssl
            if val:
                self.ui.vnt.get(url, session=True, verify=verify, wait=0.8, timeout=60, onfinished=self.get_remote_status)
            else:
                self.ui.vnt.get(url, timeout=60, verify=verify, wait=0.8, onfinished=self.get_remote_status)
    
    def post_pc_processing(self, *args):
        r = args[0]
        html = r.html
        url = args[3]
        err = r.error
        if not html:
            if 'http error 401' in err.lower():
                msg = 'wrong credentials try again'
                logger.error(msg)
                send_notification(msg)
        elif 'You are not authorized to access the content' in html:
            msg = 'Wrong Credentials! Try Again'
            logger.error(msg)
            send_notification(msg)
        else:
            logger.debug("PC To PC Casting Auth Error: {}".format(err))
            self.start_remote_status(url)
            
    def remove_thumbnails(self, row, row_item, remove_summary=None):
        dest = self.ui.get_thumbnail_image_path(row, row_item, only_name=True)
        if os.path.exists(dest) and remove_summary is None:
            os.remove(dest)
            small_nm_1, new_title = os.path.split(dest)
            small_nm_2 = '128px.'+new_title
            small_nm_3 = '480px.'+new_title
            small_nm_4 = 'label.'+new_title
            small_nm_5 = '256px.'+new_title
            new_small_thumb = os.path.join(small_nm_1, small_nm_2)
            small_thumb = os.path.join(small_nm_1, small_nm_3)
            small_label = os.path.join(small_nm_1, small_nm_4)
            wall_thumb = os.path.join(small_nm_1, small_nm_5)
            logger.info(new_small_thumb)
            if os.path.exists(new_small_thumb):
                os.remove(new_small_thumb)
            if os.path.exists(small_thumb):
                os.remove(small_thumb)
            if os.path.exists(small_label):
                os.remove(small_label)
            if os.path.exists(wall_thumb):
                os.remove(wall_thumb)
        elif remove_summary:
            path_thumb, new_title = os.path.split(dest)
            txt_file = new_title.replace('.jpg', '.txt', 1)
            txt_path = os.path.join(path_thumb, txt_file)
            if os.path.isfile(txt_path):
                os.remove(txt_path)
    
    def edit_selected_summary(self, row, row_item, help_needed=None):
        dest = self.ui.get_thumbnail_image_path(row, row_item, only_name=True)
        path_thumb, new_title = os.path.split(dest)
        txt_file = new_title.replace('.jpg', '.txt', 1)
        txt_path = os.path.join(path_thumb, txt_file)
        txt = ''
        if not help_needed:
            if os.path.isfile(txt_path):
                txt = open_files(txt_path, False)
            else:
                if row < len(self.ui.epn_arr_list):
                    self.ui.text.clear()
                    ep_name = self.ui.epn_arr_list[row]
                    if '\t' in ep_name:
                        ep_name = ep_name.split('\t')[0]
                    if ep_name.startswith('#'):
                        ep_name = ep_name.replace('#', '', 1)
                    txt = 'Air Date:\n\nEpisode Name:{0}\n\nOverview: Start Here'.format(ep_name)
                    
        else:
            txt = ("Air Date:\n\nDo Not Remove - Air Date: - text from top corner,\
                   while editing episode summary in this box\
                   otherwise edited summary will be saved as series summary. \
                   After Editing press ctrl+a to save changes"
                   '\n\nFor fetching Episode Summary from TVDB, first focus either \
                   TitleList or PlayList Column, and then press either F6 or F7 or F8. \
                   \nF6: Get Episode Summary and Thumbnails from TVDB directly \
                   \nF7: Get Episode Summary and Thumbnails from TVDB using duckduckgo as \
                   search engine backend. F8 will search using google as search engine backend.\n\
                   \n\nEpisode Naming patterns for better automatic fetching \
                   \nEpisode Naming Patterns with seasons: S01EP02, S01E02 \
                   \nEpisode Naming Patterns without seasons: EP01, Episode01, Episode-01, Ep-01 \
                   \nFor Specials: S00EP01\
                   \nEpisode can be renamed using F2(single entry) or F3(Batch Rename).\
                   \nBatch renaming pattern is NameStart{start-end}NameEnd. \
                   eg. S01EP{01-20}, Episode-{05-25} \
                   \nOriginal names can be restored using F4(single entry) or F5(All).\
                   When restoring original names using keys F2, F3, F4 and F5 playlist \
                   needs to be focussed')
            txt = re.sub('  +', ' ', txt)
        self.ui.text.setText(txt)
        self.ui.text.setFocus()
        if self.ui.text.isHidden():
            self.ui.text.show()
    
    def set_search_backend(self, row, use_search=None):
        if use_search is None:
            use_search = False
        try:
            site = self.ui.get_parameters_value(s='site')['site']
            nm = self.ui.get_title_name(row)
            video_dir = None
            if site.lower() == 'video':
                video_dir = self.ui.original_path_name[row].split('\t')[-1]
            elif site.lower() == 'playlists' or site.lower() == 'none' or site.lower() == 'music':
                pass
            else:
                video_dir = self.ui.original_path_name[row]
            self.ui.posterfound_new(
                name=nm, site=site, url=False, copy_poster=False, copy_fanart=False, 
                copy_summary=False, direct_url=False, use_search=use_search,
                video_dir=video_dir, get_sum=True)
        except Exception as e:
            print(e)
    
    def contextMenuEvent(self, event):
        param_dict = self.ui.get_parameters_value(s='site', n='name')
        site = param_dict['site']
        name = param_dict['name']
        if site == "Music":
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Add To Playlist")
            menu.addMenu(submenuR)
            view_menu = QtWidgets.QMenu(menu)
            view_menu.setTitle("View Mode")
            menu.addMenu(view_menu)
            view_list = view_menu.addAction("List Mode (Default)")
            view_list_thumbnail = view_menu.addAction("List With Thumbnail")
            thumb_wall = view_menu.addAction("Thumbnail Wall Mode (F1)")
            thumb = view_menu.addAction("Thumbnail Grid Mode (Shift+Z)")
            if self.ui.pc_to_pc_casting == 'master':
                cast_menu = QtWidgets.QMenu(menu)
                cast_menu.setTitle("PC To PC Casting")
                cast_menu_file = cast_menu.addAction("Cast this Item")
                cast_menu_playlist = cast_menu.addAction("Cast this Playlist")
                cast_menu_queue = cast_menu.addAction("Queue this Item")
                cast_menu_direct_url = cast_menu.addAction("Cast Current URL")
                cast_menu.addSeparator()
                cast_menu_web = cast_menu.addAction("Show More Controls")
                cast_menu.addSeparator()
                set_cast_slave = cast_menu.addAction("Set Slave IP Address")
                clear_session = cast_menu.addAction("Logout and Clear Session")
                if self.ui.discover_slaves:
                    dis_slave = cast_menu.addAction("Stop Discovering")
                else:
                    dis_slave = cast_menu.addAction("Discover Slaves")
                slave_actions = []
                if self.ui.pc_to_pc_casting_slave_list:
                    cast_menu.addSeparator()
                    for ip in self.ui.pc_to_pc_casting_slave_list:
                        slave_actions.append(cast_menu.addAction(ip))
                menu.addMenu(cast_menu)
            save_pls = menu.addAction('Save Current Playlist')
            go_to = menu.addAction("Go To Last.fm")
            qitem = menu.addAction("Queue Item (Ctrl+Q)")
            fix_ord = menu.addAction("Lock Order (Playlist Only)")
            pls = os.listdir(os.path.join(home, 'Playlists'))
            home_n = os.path.join(home, 'Playlists')
            pls = sorted(
                pls, key=lambda x: os.path.getmtime(os.path.join(home_n, x)), 
                reverse=True)
            j = 0
            item_m = []
            for i in pls:
                item_m.append(submenuR.addAction(i))
            submenuR.addSeparator()
            new_pls = submenuR.addAction("Create New Playlist")
            file_manager = menu.addAction("Open in File Manager")
            default = menu.addAction("Set Default Background")
            delPosters = menu.addAction("Delete Poster")
            delInfo = menu.addAction("Delete Info")
            thumb_menu = QtWidgets.QMenu(menu)
            thumb_menu.setTitle("Remove Thumbnails")
            menu.addMenu(thumb_menu)
            remove_all = thumb_menu.addAction("Remove All")
            remove_selected = thumb_menu.addAction("Remove Selected")
            
            action = menu.exec_(self.mapToGlobal(event.pos()))
            for i in range(len(item_m)):
                if action == item_m[i]:
                    self.triggerPlaylist(pls[i])
            if self.ui.pc_to_pc_casting == 'master':
                if action == cast_menu_file:
                    self.start_pc_to_pc_casting('single', self.currentRow())
                elif action == cast_menu_playlist:
                    self.start_pc_to_pc_casting('playlist', self.currentRow())
                elif action == cast_menu_queue:
                    self.start_pc_to_pc_casting('queue', self.currentRow())
                elif action == cast_menu_direct_url:
                    self.start_pc_to_pc_casting('direct url', self.currentRow())
                elif action == set_cast_slave:
                    self.setup_slave_address()
                elif action == clear_session:
                    self.clear_slave_session()
                elif action == cast_menu_web:
                    self.show_web_menu()
                elif action == dis_slave:
                    self.discover_slave_ips(action.text())
                elif action in slave_actions:
                    self.setup_slave_address(ipaddr=action.text())
            if action == new_pls:
                print("creating")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Playlists', item)
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == save_pls:
                    print("creating")
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter New Playlist Name')
                    if ok and item:
                        file_path = os.path.join(home, 'Playlists', item)
                        write_files(file_path, self.ui.epn_arr_list, True)
            elif action == qitem:
                if self.ui.player_val == "libmpv":
                    self.ui.gui_signals.queue_item("context_menu")
                else:
                    self.queue_item()
            elif action == view_list:
                self.ui.widget_style.change_list2_style(mode=False)
                if not self.ui.float_window.isHidden():
                    if self.ui.new_tray_widget.cover_mode.text() == self.ui.player_buttons['down']: 
                        self.setMaximumHeight(30)
                    else:
                        self.setMaximumHeight(16777215)
                self.ui.update_list2()
            elif action == view_list_thumbnail:
                self.ui.widget_style.change_list2_style(mode=True)
                if not self.ui.float_window.isHidden():
                    self.setMaximumHeight(16777215)
                self.ui.update_list2()
            elif action == thumb_wall:
                if self.ui.list1.currentRow():
                    title_index = self.ui.list1.currentRow()
                else:
                    title_index = -1
                self.ui.experiment_list({"mode":"pls", "epi": self.currentRow(), "title_index": title_index})
            elif action == thumb:
                if self.currentItem() and self.ui.float_window.isHidden():
                    self.ui.IconViewEpn(mode=3)
                    self.ui.scrollArea1.setFocus()
            elif action == file_manager:
                if self.ui.epn_arr_list:
                    if self.currentItem():
                        self.open_in_file_manager(self.currentRow())
            elif action == go_to:
                if self.ui.list3.currentItem():
                    nam1 = ''
                    if str(self.ui.list3.currentItem().text()) == "Artist":
                        nam1 = str(self.ui.list1.currentItem().text())
                    else:
                        r = self.currentRow()
                        try:
                            nam1 = self.ui.epn_arr_list[r].split('	')[2]
                        except:
                            nam1 = ''
                    logger.info(nam1)
                    self.ui.reviewsWeb(srch_txt=nam1, review_site='last.fm', 
                                  action='search_by_name')
            elif action == fix_ord:
                self.fix_order()
            elif action == remove_all:
                for i, j in enumerate(self.ui.epn_arr_list):
                    self.remove_thumbnails(i ,j)
            elif action == remove_selected:
                r = self.currentRow()
                self.remove_thumbnails(r ,self.ui.epn_arr_list[r])
            elif action == delInfo or action == delPosters or action == default:
                if (self.ui.list3.currentItem()):
                    if str(self.ui.list3.currentItem().text()) == "Artist":
                        if '/' in name:
                            nam = name.replace('/', '-')
                        else:
                            nam = name
                    else:
                        try:
                            r = self.currentRow()
                            nam = self.ui.epn_arr_list[r].split('	')[2]
                        except:
                            nam = ""
                        if '/' in nam:
                            nam = nam.replace('/', '-')
                        else:
                            nam = nam
                    if nam:
                        picn = os.path.join(home, 'Music', 'Artist', nam, 'poster.jpg')
                        fanart = os.path.join(home, 'Music', 'Artist', nam, 'fanart.jpg')
                        default_wall = os.path.join(home, 'default.jpg')
                        sumr = os.path.join(home, 'Music', 'Artist', nam, 'bio.txt')
                        dir_n = os.path.join(home, 'Music', 'Artist', nam)
                        if os.path.exists(dir_n):
                            if action == delInfo:
                                m = os.listdir(dir_n)
                                for i in m:
                                    if i.endswith('.txt'):
                                        f = open(os.path.join(dir_n, 'bio.txt'), 'w')
                                        f.write('No Information Available')
                                        f.close()
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('.txt'):
                                        t = os.path.join(TMPDIR, i)
                                        os.remove(t)
                            elif action == delPosters:
                                m = os.listdir(dir_n)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('256px') or i.endswith('128px'):
                                        os.remove(os.path.join(dir_n, i))
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('.txt'):
                                        os.remove(os.path.join(TMPDIR, i)) 
                            elif action == default:
                                shutil.copy(default_wall, picn)
                                shutil.copy(default_wall, fanart)
                                self.ui.videoImage(
                                    picn, os.path.join(home, 'Music', 'Artist', 
                                    nam, 'thumbnail.jpg'), fanart, '')
        else:
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Add To Playlist")
            menu.addMenu(submenuR)
            view_menu = QtWidgets.QMenu(menu)
            view_menu.setTitle("View Mode")
            menu.addMenu(view_menu)
            if self.ui.pc_to_pc_casting == 'master':
                cast_menu = QtWidgets.QMenu(menu)
                cast_menu.setTitle("PC To PC Casting")
                cast_menu_file = cast_menu.addAction("Cast this Item")
                cast_menu_playlist = cast_menu.addAction("Cast this Playlist")
                cast_menu_queue = cast_menu.addAction("Queue this Item")
                cast_menu_direct_url = cast_menu.addAction("Cast Current URL")
                cast_menu_play_file_at_index = cast_menu.addAction("Play this index")
                cast_menu_subtitle = cast_menu.addAction("Send Subtitle File")
                cast_menu.addSeparator()
                cast_menu_web = cast_menu.addAction("Show More Controls")
                cast_menu.addSeparator()
                set_cast_slave = cast_menu.addAction("Set Slave IP Address")
                clear_session = cast_menu.addAction("Logout and Clear Session")
                if self.ui.discover_slaves:
                    dis_slave = cast_menu.addAction("Stop Discovering")
                else:
                    dis_slave = cast_menu.addAction("Discover Slaves")
                slave_actions = []
                if self.ui.pc_to_pc_casting_slave_list:
                    cast_menu.addSeparator()
                    for ip in self.ui.pc_to_pc_casting_slave_list:
                        slave_actions.append(cast_menu.addAction(ip))
                menu.addMenu(cast_menu)
            view_list = view_menu.addAction("List Mode (Default)")
            view_list_thumbnail = view_menu.addAction("List With Thumbnail")
            thumb_wall = view_menu.addAction("Thumbnail Wall Mode (F1)")
            thumb = view_menu.addAction("Thumbnail Grid Mode (Shift+Z)")
            pls = os.listdir(os.path.join(home, 'Playlists'))
            home_n = os.path.join(home, 'Playlists')

            pls = sorted(
                pls, key=lambda x: os.path.getmtime(os.path.join(home_n, x)), 
                reverse=True)

            item_m = []
            for i in pls:
                item_m.append(submenuR.addAction(i))
            submenuR.addSeparator()
            new_pls = submenuR.addAction("Create New Playlist")
            r = self.currentRow()
            goto_web_mode = False
            offline_mode = False
            if self.ui.epn_arr_list and self.currentItem():
                epn_arr = self.ui.epn_arr_list[r].split('	')
                if len(epn_arr) > 2:
                    url_web = self.ui.epn_arr_list[r].split('	')[1]
                    if url_web.startswith('abs_path='):
                        url_web = self.ui.if_path_is_rel(url_web)
                    if url_web.startswith('ytdl:'):
                        url_web = url_web.replace('ytdl:', '', 1)
                else:
                    url_web = 'none'
            else:
                url_web = 'none'
            save_pls_entry = None
            if 'youtube.com' in url_web:
                goto_web = menu.addAction('Open in Youtube Browser')
                goto_web_mode = True
            if (site.lower() == 'video' or site.lower() == 'local' 
                    or site.lower() == 'none' 
                    or site.lower().startswith('playlist')):
                save_pls = menu.addAction('Save Current Playlist')
                save_pls_entry = True
            if (site.lower() != 'video' and site.lower() != 'music' 
                    and site.lower() != 'local'):
                if (self.ui.btn1.currentText().lower() == 'addons' 
                        or url_web.startswith('http') 
                        or url_web.startswith('"http')):
                    start_offline = menu.addAction('Start In Offline Mode')
                    offline_mode = True
                    
            qitem = menu.addAction("Queue Item (Ctrl+Q)")
            fix_ord = menu.addAction("Lock Order")
            submenu = QtWidgets.QMenu(menu)
            submenu.setTitle('TVDB options')
            eplist_info = False
           
            if site.lower().startswith('playlist') or site.lower() == 'none':
                eplist_info = False
            else:
                eplist = submenu.addAction("Thumbnails and Summary (F6)")
                eplist_ddg = submenu.addAction("Thumbnails and Summary (ddg) (F7)")
                eplist_g = submenu.addAction("Thumbnails and Summary (g) (F8)")
                eplist_info = True
            
            eplistM = QtWidgets.QAction("Go To TVDB", self)
            if site.lower() != 'playlists' and site.lower() != 'none':
                submenu.addAction(eplistM)
                menu.addMenu(submenu)
            file_manager = menu.addAction("Open in File Manager")
            rm_menu = QtWidgets.QMenu(menu)
            rm_menu.setTitle("Rename Options")
            editN = rm_menu.addAction("Rename Single Entry (F2)")
            group_rename = rm_menu.addAction("Rename in Group (F3)")
            default_name = rm_menu.addAction("Set Default Name (F4)")
            default_name_all = rm_menu.addAction("Set Default Name For All (F5)")
            menu.addMenu(rm_menu)
            thumb_menu = QtWidgets.QMenu(menu)
            thumb_menu.setTitle("Remove Thumbnails")
            menu.addMenu(thumb_menu)
            remove_selected = thumb_menu.addAction("Remove Selected")
            remove_all = thumb_menu.addAction("Remove All")
            
            summary_menu = QtWidgets.QMenu(menu)
            summary_menu.setTitle("Episode Summary")
            menu.addMenu(summary_menu)
            edit_summary = summary_menu.addAction("Edit Selected")
            remove_summary_selected = summary_menu.addAction("Remove Selected")
            remove_summary_all = summary_menu.addAction("Remove All")
            edit_summary_help = summary_menu.addAction("Help Editing Summary")
            
            upspeed = menu.addAction("Set Upload Speed (Ctrl+D)")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            
            if self.currentItem():
                for i in range(len(item_m)):
                    if action == item_m[i]:
                        self.triggerPlaylist(pls[i])
            if offline_mode:
                if action == start_offline:
                    self.init_offline_mode()
            if goto_web_mode:
                if action == goto_web:
                    self.ui.reviewsWeb(srch_txt=url_web, review_site='YouTube', action='open')
            if self.ui.pc_to_pc_casting == 'master':
                if action == cast_menu_file:
                    self.start_pc_to_pc_casting('single', self.currentRow())
                elif action == cast_menu_playlist:
                    self.start_pc_to_pc_casting('playlist', self.currentRow())
                elif action == cast_menu_queue:
                    self.start_pc_to_pc_casting('queue', self.currentRow())
                elif action == cast_menu_direct_url:
                    self.start_pc_to_pc_casting('direct url', self.currentRow())
                elif action == cast_menu_play_file_at_index:
                    self.start_pc_to_pc_casting('direct index', self.currentRow())
                elif action == set_cast_slave:
                    self.setup_slave_address()
                elif action == cast_menu_subtitle:
                    self.send_subtitle_method()
                elif action == clear_session:
                    self.clear_slave_session()
                elif action == cast_menu_web:
                    self.show_web_menu()
                elif action == dis_slave:
                    self.discover_slave_ips(action.text())
                elif action in slave_actions:
                    self.setup_slave_address(ipaddr=action.text())
            if save_pls_entry:
                if action == save_pls:
                    print("creating")
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Playlist Name')
                    if ok and item:
                        file_path = os.path.join(home, 'Playlists', item)
                        write_files(file_path, self.ui.epn_arr_list, True)
            if eplist_info:
                if action == eplist:
                    if self.ui.list1.currentItem():
                        row = self.ui.list1.currentRow()
                    else:
                        row = 0
                    if self.currentItem():
                        self.set_search_backend(row)
                elif action == eplist_ddg:
                    if self.ui.list1.currentItem():
                        row = self.ui.list1.currentRow()
                    else:
                        row = 0
                    if self.currentItem():
                        self.set_search_backend(row, use_search='ddg')
                elif action == eplist_g:
                    if self.ui.list1.currentItem():
                        row = self.ui.list1.currentRow()
                    else:
                        row = 0
                    if self.currentItem():
                        self.set_search_backend(row, use_search='g')
            if action == new_pls:
                print("creating")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Playlists', item)
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == qitem:
                if self.ui.player_val == "libmpv":
                    self.ui.gui_signals.queue_item("context_menu")
                else:
                    self.queue_item()
            elif action == upspeed:
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Upload Speed in KB\n0 means unlimited', 
                    QtWidgets.QLineEdit.Normal, str(self.ui.setuploadspeed))
                if item and ok:
                    if item.isnumeric():
                        self.ui.setuploadspeed = int(item)
                    else:
                        send_notification('wrong values')
            elif action == view_list:
                self.ui.widget_style.change_list2_style(mode=False)
                if not self.ui.float_window.isHidden():
                    if self.ui.new_tray_widget.cover_mode.text() == self.ui.player_buttons['down']: 
                        self.setMaximumHeight(30)
                    else:
                        self.setMaximumHeight(16777215)
                self.ui.update_list2()
            elif action == view_list_thumbnail:
                self.ui.widget_style.change_list2_style(mode=True)
                if not self.ui.float_window.isHidden():
                    self.setMaximumHeight(16777215)
                self.ui.update_list2()
            elif action == thumb_wall:
                if self.ui.list1.currentRow():
                    title_index = self.ui.list1.currentRow()
                else:
                    title_index = -1
                self.ui.experiment_list({"mode":"pls", "epi": self.currentRow(), "title_index": title_index})
            elif action == remove_all:
                for i, j in enumerate(self.ui.epn_arr_list):
                    self.remove_thumbnails(i ,j)
            elif action == remove_selected:
                for item in self.selectedItems():
                    r = self.row(item)
                    self.remove_thumbnails(r ,self.ui.epn_arr_list[r])
            elif action == remove_summary_all:
                for i, j in enumerate(self.ui.epn_arr_list):
                    self.remove_thumbnails(i ,j, remove_summary=True)
            elif action == edit_summary:
                self.edit_selected_summary(r ,self.ui.epn_arr_list[r])
            elif action == edit_summary_help:
                self.edit_selected_summary(r ,self.ui.epn_arr_list[r], help_needed=True)
            elif action == remove_summary_selected:
                for item in self.selectedItems():
                    r = self.row(item)
                    self.remove_thumbnails(r ,self.ui.epn_arr_list[r], remove_summary=True)
            elif action == editN and not self.ui.list1.isHidden():
                if self.ui.epn_arr_list:
                    print('Editing Name')
                    if self.currentItem():
                        self.edit_name_list2(self.currentRow())
            elif action == group_rename and not self.ui.list1.isHidden():
                if self.ui.epn_arr_list:
                    print('Batch Renaming in database')
                    if self.currentItem():
                        self.edit_name_in_group(self.currentRow())
            elif action == default_name and not self.ui.list1.isHidden():
                if self.ui.epn_arr_list:
                    print('Default Name')
                    for item in self.selectedItems():
                        r = self.row(item)
                        self.get_default_name(r, mode='default')
            elif action == default_name_all and not self.ui.list1.isHidden():
                if self.ui.epn_arr_list:
                    print('Batch Renaming in database')
                    if self.currentItem():
                        self.get_default_name(self.currentRow(), mode='default_all')
            elif action == file_manager:
                if self.ui.epn_arr_list:
                    if self.currentItem():
                        self.open_in_file_manager(self.currentRow())
            elif action == eplistM:
                if self.ui.list1.currentItem():
                    name1 = (self.ui.list1.currentItem().text())
                    self.ui.reviewsWeb(
                        srch_txt=name1, review_site='tvdb', action='search_by_name')
            elif action == thumb:
                if self.currentItem() and self.ui.float_window.isHidden():
                    self.ui.IconViewEpn(mode=3)
                    self.ui.scrollArea1.setFocus()
            elif action == fix_ord:
                if self.currentItem():
                    self.fix_order()

    def discover_slave_ips(self, text):
        if text.lower() == 'discover slaves':
            self.ui.discover_slaves = True
            logger.debug('starting...')
            if not self.discover_slave_thread:
                self.discover_slave_thread = DiscoverServer(ui)
                self.discover_slave_thread.start()
            elif isinstance(self.discover_slave_thread, DiscoverServer):
                if not self.discover_slave_thread.isRunning():
                    self.discover_slave_thread = DiscoverServer(ui)
                    self.discover_slave_thread.start()
        elif text.lower() == 'stop discovering':
            self.ui.discover_slaves = False
            logger.debug('stopping...')
