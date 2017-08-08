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
from PyQt5 import QtCore, QtWidgets
from player_functions import write_files, open_files, send_notification

class TitleListWidget(QtWidgets.QListWidget):
    
    def __init__(self, parent, uiwidget=None, home_var=None, tmp=None, logr=None):
        super(TitleListWidget, self).__init__(parent)
        global MainWindow, home, TMPDIR, logger, ui
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        MainWindow = parent
        ui = uiwidget
        TMPDIR = tmp
        home = home_var
        logger = logr

    def mouseMoveEvent(self, event): 
        if ui.auto_hide_dock and not ui.dockWidget_3.isHidden():
            ui.dockWidget_3.hide()
        self.setFocus()
    """
    def dropEvent(self, event):
        if (event.source() == self 
                and (event.dropAction() == QtCore.Qt.MoveAction 
                or self.dragDropMode() == QtWidgets.QAbstractItemView.InternalMove)):
            i = self.currentItem()
            item = i.text()
            itemR = self.currentRow()
            print("Mouse Release")
            print(item)
            p = self.itemAt(event.pos())
            m = p.text()
            n = self.row(p)
            print(n)
            print(itemR)
            if itemR != n:
                self.takeItem(itemR)
                del i
                self.insertItem(n, item)
                param_dict = ui.get_parameters_value(b='bookmark', o='opt', s='status')
                bookmark = param_dict['bookmark']
                opt = param_dict['opt']
                status = param_dict['status']
                if bookmark or opt == "History":
                    file_path = ""
                    if bookmark:
                        if os.path.exists(os.path.join(home, 'Bookmark', status+'.txt')):
                            file_path = os.path.join(home, 'Bookmark', status+'.txt')
                            l = open_files(file_path, True)
                            lines = []
                            for i in l:
                                i = re.sub('\n', '', i)
                                lines.append(i)
                                
                            if n > itemR:
                                t = lines[itemR]
                                i = itemR
                                while(i < n):
                                    lines[i] = lines[i+1]
                                    i = i+1
                                lines[n] = t
                            else:
                                i = itemR
                                t = lines[itemR]
                                while(i > n):
                                    lines[i] = lines[i-1]
                                    i = i -1
                                lines[n]=t
                            j = 0
                            length = len(lines)
                            write_files(file_path, lines, line_by_line=True)
                            self.clear()
                            for i in lines:
                                j = i.split(':')
                                self.addItem(j[-1])
                            self.setCurrentRow(n)
                    else:
                        param_dict = ui.get_parameters_value(s='site', sn='siteName')
                        site = param_dict['site']
                        siteName = param_dict['siteName']
                        if site == "SubbedAnime" or site == "DubbedAnime":
                            if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                                file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                        else:
                            if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                                file_path = os.path.join(home, 'History', site, 'history.txt')
                        write_files(file_path, ui.original_path_name, line_by_line=True)
                        self.setCurrentRow(n)
        else:
            QtWidgets.QListWidget.dropEvent(event)
    """
    
    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Right):
            try:
                site = ui.get_parameters_value(s='site')['site']
                nm = ui.get_title_name(self.currentRow())
                ui.posterfound_new(
                    name=nm, site=site, url=False, copy_poster=True, copy_fanart=True, 
                    copy_summary=True, direct_url=False)
            except Exception as e:
                print(e)
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_C):
            ui.copyFanart()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_C):
            ui.copyFanart()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Delete):
            row = self.currentRow()
            file_path = ""
            param_dict = ui.get_parameters_value(s='site', sn='siteName')
            site = param_dict['site']
            siteName = param_dict['siteName']
            if site == "SubbedAnime" or site == "DubbedAnime":
                if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, 'history.txt')
            if os.path.exists(file_path):
                row = self.currentRow()
                item = self.item(row)
                if item:
                    self.takeItem(row)
                    del item
                    del ui.original_path_name[row]
                    length = self.count()-1
                    write_files(file_path, ui.original_path_name, line_by_line=True)
        elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_C):
            ui.copySummary()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_B):
            param_dict = ui.get_parameters_value(b='bookmark', o='opt')
            bookmark = param_dict['bookmark']
            opt = param_dict['opt']
            if not bookmark:
                if opt != "History":
                    ui.listfound()
                param_dict = ui.get_parameters_value(
                    s='site', sn='siteName', bu='base_url', e='embed',
                    n='name', r='refererNeeded', f='finalUrlFound')
                site = param_dict['site']
                siteName = param_dict['siteName']
                base_url = param_dict['base_url']
                embed = param_dict['embed']
                name = param_dict['name']
                refererNeeded = param_dict['refererNeeded']
                finalUrlFound = param_dict['finalUrlFound']
                tmp = site+':'+"History"+':'+siteName+':'+str(base_url)+':'+str(embed)+':'+name+':'+finalUrlFound+':'+refererNeeded
                file_path = os.path.join(home, 'Bookmark', 'bookmark.txt')
                write_files(file_path, tmp, line_by_line=True)
                note = name + " is Bookmarked"
                send_notification(note)
        elif event.key() == QtCore.Qt.Key_PageUp:
            param_dict = ui.get_parameters_value(
                b='bookmark', s='site', o='opt', st='status', sn='siteName')
            bookmark = param_dict['bookmark']
            status = param_dict['status']
            opt = param_dict['opt']
            site= param_dict['site']
            siteName = param_dict['siteName']
            if bookmark:
                file_path = os.path.join(home, 'Bookmark', status+'.txt')
                if os.path.exists(file_path):
                    lins = open_files(file_path, True)
                    lines = []
                    for i in lins:
                        i = re.sub('\n', '', i)
                        lines.append(i)
                    r = self.currentRow()
                    length = self.count()
                    if r == 0:
                        p = length - 1
                    else:
                        p = r - 1
                    if length > 1:
                        t = lines[r]
                        lines[r] = lines[p]
                        lines[p] = t
                        write_files(file_path, lines, line_by_line=True)
                        self.clear()
                        ui.original_path_name[:] = []
                        for i in lines:
                            i = i.strip()
                            j = i.split(':')
                            if j[5].startswith('@'):
                                self.addItem(j[5].split('@')[-1])
                            elif '	' in j[5]:
                                k = j[5].split('	')[0]
                                self.addItem(k)	
                            else:
                                self.addItem(j[5])
                            ui.original_path_name.append(j[5])
                        self.setCurrentRow(p)
            elif opt == "History" and site!= "Music":
                file_path = ''
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                else:
                    if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                        file_path = os.path.join(home, 'History', site, 'history.txt')
                row = self.currentRow()
                if row == 0:
                    prev_row = self.count()-1
                else:
                    prev_row = row - 1
                ui.original_path_name[row], ui.original_path_name[prev_row] = ui.original_path_name[prev_row], ui.original_path_name[row]
                if os.path.exists(file_path):
                    write_files(file_path, ui.original_path_name, line_by_line=True)
                self.clear()
                for i in ui.original_path_name:
                    if '	' in i:
                        i = i.split('	')[0]
                    self.addItem(i)
                self.setCurrentRow(prev_row)
        elif event.key() == QtCore.Qt.Key_PageDown:
            param_dict = ui.get_parameters_value(
                b='bookmark', s='site', o='opt', st='status', sn='siteName')
            bookmark = param_dict['bookmark']
            status = param_dict['status']
            opt = param_dict['opt']
            site= param_dict['site']
            siteName = param_dict['siteName']
            if bookmark:
                file_path = os.path.join(home, 'Bookmark', status+'.txt')
                if os.path.exists(file_path):
                    lins = open_files(file_path, True)
                    lines = []
                    for i in lins:
                        i = re.sub('\n', '', i)
                        lines.append(i)
                    r = self.currentRow()
                    length = self.count()
                    if r == length -1:
                        p = 0
                    else:
                        p = r + 1
                    if length > 1:
                        t = lines[r]
                        lines[r] = lines[p]
                        lines[p] = t
                        write_files(file_path, lines, line_by_line=True)
                        self.clear()
                        ui.original_path_name[:] = []
                        for i in lines:
                            i = re.sub('\n', '', i)
                            j = i.split(':')
                            if j[5].startswith('@'):
                                self.addItem(j[5].split('@')[-1])
                            elif '	' in j[5]:
                                k = j[5].split('	')[0]
                                self.addItem(k)
                            else:
                                self.addItem(j[5])
                            ui.original_path_name.append(j[5])
                        self.setCurrentRow(p)
            elif opt =="History" and site!= "Music":
                if site == "SubbedAnime" or site == "DubbedAnime":
                    if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                        file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                else:
                    if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                        file_path = os.path.join(home, 'History', site, 'history.txt')
                row = self.currentRow()
                if row == (self.count() - 1):
                    next_row = 0
                else:
                    next_row = row+1
                ui.original_path_name[row], ui.original_path_name[next_row] = ui.original_path_name[next_row], ui.original_path_name[row]
                if os.path.exists(file_path):
                    write_files(file_path, ui.original_path_name, line_by_line=True)
                self.clear()
                for i in ui.original_path_name:
                    if '	' in i:
                        i = i.split('	')[0]
                    self.addItem(i)
                self.setCurrentRow(next_row)
        elif event.key() == QtCore.Qt.Key_Delete:
            param_dict = ui.get_parameters_value(b='bookmark', s='site')
            bookmark = param_dict['bookmark']
            site= param_dict['site']
            r = self.currentRow()
            item = self.item(r)
            if item:
                if site == "PlayLists":
                    index = self.currentRow()
                    item_r  = self.item(index)
                    if item_r:
                        item = str(self.currentItem().text())
                        if item != "Default":
                            file_pls = os.path.join(home, 'Playlists', item)
                            if os.path.exists(file_pls):
                                os.remove(file_pls)
                            self.takeItem(index)
                            del item_r
                            ui.list2.clear()
                elif site == "Video" and not bookmark:
                    video_db = os.path.join(home, 'VideoDB', 'Video.db')
                    conn = sqlite3.connect(video_db)
                    cur = conn.cursor()
                    txt = ui.original_path_name[r].split('	')[1]
                    cur.execute('Delete FROM Video Where Directory=?', (txt, ))
                    logger.info('Deleting Directory From Database : '+txt)
                    del ui.original_path_name[r]
                    conn.commit()
                    conn.close()
                    self.takeItem(r)
                    del item
                    if txt in ui.video_dict:
                        del ui.video_dict[txt]
                elif site == "Music":
                    list3n = (ui.list3.currentItem().text())
                    if (list3n == "Fav-Artist" or list3n == "Fav-Album" 
                            or list3n=="Fav-Directory"):
                        conn = sqlite3.connect(os.path.join(home, 'Music', 'Music.db'))
                        cur = conn.cursor()
                        qVal = str(self.currentItem().text())
                        logger.info('{0}--qval'.format(qVal))
                        tmp = str(ui.list3.currentItem().text())
                        if tmp == "Fav-Artist":
                            qr = 'Update Music Set Favourite="no" Where Artist=?'
                            cur.execute(qr, (qVal, ))
                        elif tmp == "Fav-Album":
                            qr = 'Update Music Set Favourite="no" Where Album=?'
                            cur.execute(qr, (qVal, ))
                        elif tmp == "Fav-Directory":
                            qr = 'Update Music Set Favourite="no" Where Directory=?'
                            cur.execute(qr, (qVal, ))
                        logger.info("Number of rows updated: %d" % cur.rowcount)
                        conn.commit()
                        conn.close()
                        ui.options_clicked()
                        self.setCurrentRow(r)
                elif site == 'None':
                    print("Nothing to delete")
                else:
                    ui.deleteHistory()
        elif event.key() == QtCore.Qt.Key_H:
            ui.setPreOpt()
        elif event.key() == QtCore.Qt.Key_D:
            ui.deleteArtwork()
        elif event.key() == QtCore.Qt.Key_M:
            pass
        elif event.key() == QtCore.Qt.Key_I:
            ui.showImage()
        elif event.key() == QtCore.Qt.Key_R:
            ui.shuffleList()
        elif event.key() == QtCore.Qt.Key_T:
            ui.sortList()
        elif event.key() == QtCore.Qt.Key_Y:
            ui.getList()
        elif event.key() == QtCore.Qt.Key_C:
            ui.copyImg()
        elif event.key() == QtCore.Qt.Key_Return:
            ui.list1_double_clicked()
        elif event.key() == QtCore.Qt.Key_Right:
            ui.list2.setFocus()
        elif event.key() == QtCore.Qt.Key_Left:
            if ui.tab_5.isHidden() and ui.mpvplayer_val.processId() == 0:
                ui.btn1.setFocus()
                ui.dockWidget_3.show()
            else:
                ui.tab_5.setFocus()
        elif event.key() == QtCore.Qt.Key_Period:
            if site == "Music":
                ui.mpvNextEpnList()
            else:
                ui.nextp(ui.list3.currentRow())
        elif event.key() == QtCore.Qt.Key_Comma:
            if site == "Music":
                ui.mpvPrevEpnList()
            else:
                ui.backp(ui.list3.currentRow())
        elif event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if self.currentRow() == 0:
                self.setCurrentRow(self.count()-1)
            else:
                self.setCurrentRow(prev_r)
        #super(List1, self).keyPressEvent(event)

    def addBookmarkList(self):
        try:
            new_path = ui.original_path_name[self.currentRow()].split('	')[-1]
        except Exception as e:
            print(e)
            new_path = 'NONE'
        param_dict = ui.get_parameters_value(b='bookmark', o='opt')
        bookmark = param_dict['bookmark']
        opt = param_dict['opt']
        if not bookmark:
            if opt != "History":
                ui.listfound()
            param_dict = ui.get_parameters_value(
                s='site', sn='siteName', bu='base_url', e='embed', v='video_local_stream',
                n='name', r='refererNeeded', f='finalUrlFound')
            site = param_dict['site']
            siteName = param_dict['siteName']
            base_url = param_dict['base_url']
            embed = param_dict['embed']
            name = param_dict['name']
            refererNeeded = param_dict['refererNeeded']
            finalUrlFound = param_dict['finalUrlFound']
            video_local_stream = param_dict['video_local_stream']
            if site == "Music" or site == "Video":
                if ui.list3.currentItem():
                    music_opt = str(ui.list3.currentItem().text())
                    tmp = site+':'+(music_opt)+':'+siteName+':'+str(base_url)+':'+str(embed)+':'+name+':'+str(finalUrlFound)+':'+str(refererNeeded)+':'+str(video_local_stream)+':'+str(new_path)
                else:
                    return 0
            else:
                tmp = site+':'+"History"+':'+siteName+':'+str(base_url)+':'+str(embed)+':'+name+':'+str(finalUrlFound)+':'+str(refererNeeded)+':'+str(video_local_stream)+':'+str(new_path)
            file_path = os.path.join(home, 'Bookmark', 'bookmark.txt')
            write_files(file_path, tmp, line_by_line=True)
            note = name + " is Bookmarked"

    def triggerBookmark(self, val):
        try:
            new_path = ui.original_path_name[self.currentRow()].split('	')[-1]
        except Exception as e:
            print(e)
            new_path = 'NONE'
        param_dict = ui.get_parameters_value(b='bookmark', o='opt')
        bookmark = param_dict['bookmark']
        opt = param_dict['opt']
        if not bookmark:
            self.addBookmarkList()
        param_dict = ui.get_parameters_value(
            s='site', sn='siteName', bu='base_url', e='embed', v='video_local_stream',
            n='name', r='refererNeeded', f='finalUrlFound')
        site = param_dict['site']
        siteName = param_dict['siteName']
        base_url = param_dict['base_url']
        embed = param_dict['embed']
        name = param_dict['name']
        refererNeeded = param_dict['refererNeeded']
        finalUrlFound = param_dict['finalUrlFound']
        video_local_stream = param_dict['video_local_stream']
        if site == "Music" or site == "Video":
            if ui.list3.currentItem():
                music_opt = str(ui.list3.currentItem().text())
                tmp = site+':'+(music_opt)+':'+siteName+':'+str(base_url)+':'+str(embed)+':'+name+':'+str(finalUrlFound)+':'+str(refererNeeded)+':'+str(video_local_stream)+':'+str(new_path)
            else:
                return 0
        else:
            if ui.list1.currentItem():
                tmp = site+':'+"History"+':'+siteName+':'+str(base_url)+':'+str(embed)+':'+name+':'+str(finalUrlFound)+':'+str(refererNeeded)+':'+str(video_local_stream)+':'+str(new_path)
            else:
                return 0
        file_path = os.path.join(home, 'Bookmark', val+'.txt')
        write_files(file_path, tmp, line_by_line=True)
        note = name + " is Added to "+val+" Category"
        send_notification(note)

    def triggerPlaylist(self, value):
        print('Menu Clicked')
        print(value)
        file_path = os.path.join(home, 'Playlists', str(value))
        for i in range(len(ui.epn_arr_list)):
            if os.path.exists(file_path):
                sumr=str(ui.epn_arr_list[i].split('	')[0])
                try:
                    rfr_url=str(ui.epn_arr_list[i].split('	')[2])
                except:
                    rfr_url = "NONE"
                sumry = str(ui.epn_arr_list[i].split('	')[1])
                sumry = sumry.replace('"', '')
                sumry = '"'+sumry+'"'
                t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)

    def contextMenuEvent(self, event):
        if self.currentItem():
            name = str(ui.list1.currentItem().text())
        else:
            name = ''
        ui.set_parameters_value(name_val=name)
        site = ui.get_parameters_value(s='site')['site']
        if site == "Music":
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Add To PlayList")
            menu.addMenu(submenuR)
            fav = menu.addAction("Add To Favourite")
            r = ui.list3.currentRow()
            itm = ui.list3.item(r)
            if itm:
                music_opt = str(itm.text())
            else:
                music_opt = ""
            pls = os.listdir(os.path.join(home, 'Playlists'))
            item_m = []
            for i in pls:
                i = i.replace('.txt', '')
                item_m.append(submenuR.addAction(i))
            submenuR.addSeparator()
            new_pls = submenuR.addAction("Create New Playlist")
            profile = menu.addAction("Find Last.fm Profile(manually)")
            default = menu.addAction("Set Default Background")
            delPosters = menu.addAction("Delete Poster")
            delFanart = menu.addAction("Delete Fanart")
            delThumb = menu.addAction("Delete Playlist Thumbnails")
            delInfo = menu.addAction("Delete Info")
            thumbnail = menu.addAction("Show Thumbnail View (Ctrl+Z)")
            cache = menu.addAction("Clear Cache")
            action = menu.exec_(self.mapToGlobal(event.pos()))

            for i in range(len(item_m)):
                if action == item_m[i]:
                    self.triggerPlaylist(pls[i].replace('.txt', ''))

            if action == fav:
                r = self.currentRow()
                item = self.item(r)
                if (item and music_opt!="Playlist" 
                        and music_opt!= "Fav-Artist" 
                        and music_opt!= "Fav-Album" 
                        and music_opt!= "Fav-Directory"):
                    txt = str(item.text())
                    ui.media_data.update_music_count('fav', txt)
                else:
                    print("Not Permitted")
            elif action == cache:
                    m = os.listdir(TMPDIR)
                    for i in m:
                        if '.txt' in i or '.jpg' in i:
                            t = os.path.join(TMPDIR, i)
                            os.remove(t)
            elif action == new_pls:
                print("creating")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Playlists', item)
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == profile:
                if '/' in name:
                    nam = name.replace('/', '-')
                else:
                    nam = name
                ui.reviewsWeb(srch_txt=nam, review_site='last.fm', 
                              action='search_by_name')
            elif action == thumbnail:
                param_dict = ui.get_parameters_value(b='bookmark', o='opt')
                opt = param_dict['opt']
                bookmark = param_dict['bookmark']
                if (site == "Local" or bookmark 
                        or opt == "History" or site == "Video" 
                        or site == "Music"):
                    if ui.list3.currentItem():
                        if (ui.list3.currentItem().text())=="Artist":
                            ui.scrollArea.setFocus()
                            ui.lock_process = True
                            ui.IconView()
                            ui.lock_process = False
            elif (action == delInfo or action == delPosters 
                    or action == default or action == delThumb 
                    or action == delFanart):
                if (ui.list3.currentItem()):
                    if str(ui.list3.currentItem().text()) == "Artist":
                        if '/' in name:
                            nam = name.replace('/', '-')
                        else:
                            nam = name
                    else:
                        try:
                            r = ui.list2.currentRow()
                            nam = ui.epn_arr_list[r].split('	')[2]
                        except:
                            nam = ""
                        if '/' in nam:
                            nam = nam.replace('/', '-')
                        else:
                            nam = nam
                    if nam:
                        picn = os.path.join(home, 'Music', 'Artist', nam, 
                                            'poster.jpg')
                        fanart = os.path.join(home, 'Music', 'Artist', nam, 
                                              'fanart.jpg')
                        default_wall = os.path.join(home, 'default.jpg')
                        sumr = os.path.join(home, 'Music', 'Artist', nam, 
                                            'bio.txt')
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
                                    if i.endswith('.jpg'):
                                        os.remove(os.path.join(dir_n, i))
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.endswith('.jpg') or i.endswith('.txt'):
                                        t = os.path.join(TMPDIR, i)
                                        os.remove(t) 
                            elif action == delThumb:
                                m = os.listdir(dir_n)
                                for i in m:
                                    logger.info(i)
                                    if i.startswith('256px') or i.startswith('128px'):
                                        os.remove(os.path.join(dir_n, i))
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.startswith('256x') or i.startswith('128x'):
                                        t = os.path.join(TMPDIR, i)
                                        os.remove(t) 
                            elif action == delFanart:
                                m = os.listdir(dir_n)
                                for i in m:
                                    if (i.startswith('fanart') or i.startswith('original-fanart')):
                                        os.remove(os.path.join(dir_n, i))
                                m = os.listdir(TMPDIR)
                                for i in m:
                                    if i.startswith('fanart') or i.startswith('original-fanart'):
                                        t = os.path.join(TMPDIR, i)
                                        os.remove(t)
                            elif action == default:
                                shutil.copy(default_wall, picn)
                                shutil.copy(default_wall, fanart)
                                ui.videoImage(
                                    picn, os.path.join(home, 'Music', 'Artist',
                                    nam, 'thumbnail.jpg'), fanart, '')
        else:
            menu = QtWidgets.QMenu(self)
            submenuR = QtWidgets.QMenu(menu)
            submenuR.setTitle("Find Information")
            menu.addMenu(submenuR)
            submenu = QtWidgets.QMenu(menu)
            submenu.setTitle("Bookmark Options")
            menu.addMenu(submenu)
            if 'AnimeWatch' in home or ui.anime_review_site:
                submenu_arr_dict = {
                    'mal':'MyAnimeList', 'ap':'Anime-Planet', 
                    'ans':'Anime-Source', 'tvdb':'TVDB', 
                    'ann':'ANN', 'anidb':'AniDB', 'g':'Google', 
                    'yt':'Youtube', 'ddg':'DuckDuckGo', 
                    'last.fm':'last.fm', 'zerochan':'Zerochan'
                    }
            elif 'kawaii-player' in home:
                submenu_arr_dict = {
                    'tvdb':'TVDB', 'g':'Google', 
                    'yt':'Youtube', 'ddg':'DuckDuckGo', 
                    'last.fm':'last.fm'
                    }
            reviews = []
            for i in submenu_arr_dict:
                reviews.append(submenuR.addAction(submenu_arr_dict[i]))
            addBookmark = submenu.addAction("Add Bookmark")
            bookmark_array = ['bookmark']
            pls = os.listdir(os.path.join(home, 'Bookmark'))
            item_m = []
            for i in pls:
                i = i.replace('.txt', '')
                if i not in bookmark_array:
                    item_m.append(submenu.addAction(i))
            submenu.addSeparator()
            new_pls = submenu.addAction("Create New Bookmark Category")
            sideBar = menu.addAction("Show Side Bar")
            thumbnail = menu.addAction("Show Thumbnail View (Ctrl+Z)")
            history = menu.addAction("History")
            #rmPoster = menu.addAction("Remove Poster")
            tvdb	= menu.addAction("Find Poster(TVDB) (Ctrl+Right)")
            tvdbM	= menu.addAction("Find Poster(TVDB Manually)")
            cache = menu.addAction("Clear Cache")
            del_history = menu.addAction("Delete (Only For History)")
            rem_fanart = menu.addAction("Remove Fanart")
            rem_poster = menu.addAction("Remove poster")
            refresh_poster = menu.addAction("Refresh posters")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            
            for i in range(len(item_m)):
                if action == item_m[i]:
                    item_name = item_m[i].text()
                    self.triggerBookmark(item_name)
                    
            for i in range(len(reviews)):
                if action == reviews[i]:
                    new_review = reviews[i].text()
                    if new_review.startswith('&'):
                        new_review = new_review[1:]
                    try:
                        st = list(submenu_arr_dict.keys())[list(submenu_arr_dict.values()).index(new_review)]
                        logger.info('review-site: {0}'.format(st))
                    except ValueError as e:
                        print(e, '--key--not--found--')
                        st = 'ddg'
                    ui.reviewsWeb(srch_txt=name, review_site=st, action='context_menu')
                    
            if action == new_pls:
                print("creating new bookmark category")
                item, ok = QtWidgets.QInputDialog.getText(
                    MainWindow, 'Input Dialog', 'Enter Playlist Name')
                if ok and item:
                    file_path = os.path.join(home, 'Bookmark', item+'.txt')
                    if not os.path.exists(file_path):
                        f = open(file_path, 'w')
                        f.close()
            elif action == sideBar:
                if ui.dockWidget_3.isHidden():
                    ui.dockWidget_3.show()
                    ui.btn1.setFocus()
                else:
                    ui.dockWidget_3.hide()
                    ui.list1.setFocus()
            elif action == del_history:
                ui.deleteHistory()
            elif action == addBookmark:
                self.addBookmarkList()
            elif action == thumbnail:
                param_dict = ui.get_parameters_value(b='bookmark', o='opt',
                                                     s='site')
                opt = param_dict['opt']
                bookmark = param_dict['bookmark']
                site = param_dict['site']
                if ((site == "Local" or site == 'PlayLists') 
                        or bookmark or opt == "History" 
                        or site == "Video"):
                    ui.scrollArea.setFocus()
                    ui.lock_process = True
                    ui.IconView()
                    ui.lock_process = False
            elif action == cache:
                m = os.listdir(TMPDIR)
                for i in m:
                    file_name = os.path.join(TMPDIR, i)
                    if os.path.isfile(file_name):
                        os.remove(file_name)
                    if os.path.isdir(file_name):
                        shutil.rmtree(file_name)
            elif action == tvdb:
                site = ui.get_parameters_value(s='site')['site']
                if self.currentItem():
                    nm = ui.get_title_name(self.currentRow())
                    ui.posterfound_new(
                        name=nm, site=site, url=False, copy_poster=True, 
                        copy_fanart=True, copy_summary=True, direct_url=False)
            elif action == history:
                ui.setPreOpt()
            elif action == tvdbM:
                ui.reviewsWeb(
                    srch_txt=name, review_site='tvdb', action='context_menu')
            elif action == rem_fanart:
                path = ui.get_current_directory()
                fanart = os.path.join(path, 'fanart.jpg')
                fanart_original = os.path.join(path, 'original-fanart.jpg')
                if os.path.exists(fanart):
                    os.remove(fanart)
                if os.path.exists(fanart_original):
                    os.remove(fanart_original)
            elif action == rem_poster:
                path = ui.get_current_directory()
                fanart = os.path.join(path, 'poster.jpg')
                fanart_original = os.path.join(path, 'thumbnail.jpg')
                if os.path.exists(fanart):
                    os.remove(fanart)
                if os.path.exists(fanart_original):
                    os.remove(fanart_original)
            elif action == refresh_poster:
                path = ui.get_current_directory()
                fanart_original = os.path.join(path, 'thumbnail.jpg')
                if os.path.exists(fanart_original):
                    os.remove(fanart_original)
