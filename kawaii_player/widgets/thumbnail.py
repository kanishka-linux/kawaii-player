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
import shutil
import re
import subprocess
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from player_functions import write_files

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class ThumbnailWidget(QtWidgets.QLabel):

    def __init(self, parent):
        super(ThumbnailWidget, self).__init__(parent)
        global MainWindow
        MainWindow = parent
    
    def setup_globals(
            self, parent, uiwidget=None, hm=None, tmp=None, logr=None,
            scw=None, sch=None):
        global ui, TMPDIR, home, logger, MainWindow, screen_width
        global screen_height
        ui = uiwidget
        TMPDIR = tmp
        home = hm
        logger = logr
        MainWindow = parent
        screen_width = scw
        screen_height = sch
        ui.total_seek = 0
        
        self.arrow_timer = QtCore.QTimer()
        self.arrow_timer.timeout.connect(self.arrow_hide)
        self.arrow_timer.setSingleShot(True)

        self.mplayer_OsdTimer = QtCore.QTimer()
        self.mplayer_OsdTimer.timeout.connect(self.osd_hide)
        self.mplayer_OsdTimer.setSingleShot(True)

        self.seek_timer = QtCore.QTimer()
        self.seek_timer.timeout.connect(self.seek_mplayer)
        self.seek_timer.setSingleShot(True)
        
        self.fs_timer = QtCore.QTimer()
        self.fs_timer.timeout.connect(self.thumbnail_fs)
        self.fs_timer.setSingleShot(True)
        
        self.fs_timer_focus = QtCore.QTimer()
        self.fs_timer_focus.timeout.connect(self.thumbnail_fs_focus)
        self.fs_timer_focus.setSingleShot(True)
    
    def thumbnail_fs(self):
        self.player_thumbnail_fs(mode='fs_now')
        self.fs_timer_focus.start(2000)
        
    def thumbnail_fs_focus(self):
        #for i in range(0, 4):
        #p = "ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setFocus()"
        #exec(p)
        self.setFocus()
        self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
        ui.frame1.hide()
        
    def seek_mplayer(self):
        if ui.player_val == "mplayer":
            t = bytes('\n'+"seek " + str(ui.total_seek)+'\n', 'utf-8')
            ui.mpvplayer_val.write(t)
            ui.total_seek = 0

    def osd_hide(self):
        ui.mpvplayer_val.write(b'\n osd 0 \n')

    def arrow_hide(self):
        if ui.player_val == "mplayer" or ui.player_val == "mpv":
            self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
        print("arrow hide")

    def frameShowHide(self):
        if MainWindow.isFullScreen() and ui.tab_6.isHidden():
            if ui.frame1.isHidden():
                ui.gridLayout.setSpacing(0)
                ui.frame1.show()
                ui.frame_timer.start(2000)
            else:
                ui.frame_timer.stop()
                ui.frame_timer.start(2000)

    def keyPressEvent(self, event):
        if ui.player_val == 'mplayer':
            site = ui.get_parameters_value(s='site')['site']
            if site == "Local" or site == "None" or site == "PlayLists":
                pass
            else:
                try:
                    if self.seek_timer.isActive():
                        logger.info('--seek-timer-available--')
                except Exception as e:
                    print(e, '--2309--')
                    logger.info('seek timer variable not available, creating new seek timer')
                    self.seek_timer = QtCore.QTimer()
                    self.seek_timer.timeout.connect(self.seek_mplayer)
                    self.seek_timer.setSingleShot(True)
                    
        if ui.mpvplayer_val.processId() > 0:
            param_dict = ui.get_parameters_value(t='tab_6_size_indicator')
            tab_6_size_indicator = param_dict['tab_6_size_indicator']
            if tab_6_size_indicator:
                tab_6_size_indicator.pop()
            tab_6_size_indicator.append(ui.tab_6.width())
            ui.set_parameters_value(tab_6=tab_6_size_indicator)
            if event.key() == QtCore.Qt.Key_Equal:
                param_dict = ui.get_parameters_value(
                    i='iconv_r', ir='iconv_r_indicator', c='curR')
                iconv_r = param_dict['iconv_r']
                iconv_r_indicator = param_dict['iconv_r_indicator']
                curR = param_dict['curR']
                if iconv_r > 1:
                    iconv_r = iconv_r-1
                    if iconv_r_indicator:
                        iconv_r_indicator.pop()
                    iconv_r_indicator.append(iconv_r)
                ui.set_parameters_value(iconv=iconv_r, iconvr=iconv_r_indicator)
                if not ui.scrollArea.isHidden():
                    ui.next_page('not_deleted')
                elif not ui.scrollArea1.isHidden():
                    ui.thumbnail_label_update_epn()
                if iconv_r > 1:
                    w = float((ui.tab_6.width()-60)/iconv_r)
                    h = int(w/ui.image_aspect_allowed)
                    width=str(int(w))
                    height=str(int(h))
                    ui.scrollArea1.verticalScrollBar().setValue((((curR+1)/iconv_r)-1)*h+((curR+1)/iconv_r)*10)
            elif event.key() == QtCore.Qt.Key_Minus:
                param_dict = ui.get_parameters_value(
                    i='iconv_r', ir='iconv_r_indicator', c='curR')
                iconv_r = param_dict['iconv_r']
                iconv_r_indicator = param_dict['iconv_r_indicator']
                curR = param_dict['curR']
                iconv_r = iconv_r+1
                if iconv_r_indicator:
                    iconv_r_indicator.pop()
                iconv_r_indicator.append(iconv_r)
                ui.set_parameters_value(iconv=iconv_r, iconvr=iconv_r_indicator)
                if not ui.scrollArea.isHidden():
                    ui.next_page('not_deleted')
                elif not ui.scrollArea1.isHidden():
                    ui.thumbnail_label_update_epn()
                if iconv_r > 1:
                    w = float((ui.tab_6.width()-60)/iconv_r)
                    h = int(w/ui.image_aspect_allowed)
                    width=str(int(w))
                    height=str(int(h))
                    ui.scrollArea1.verticalScrollBar().setValue((((curR+1)/iconv_r)-1)*h+((curR+1)/iconv_r)*10)
            elif event.key() == QtCore.Qt.Key_Right:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists":
                        ui.mpvplayer_val.write(b'\n seek +10 \n')
                    else:
                        ui.total_seek = ui.total_seek + 10
                        r = "Seeking "+str(ui.total_seek)+'s'
                        logger.info(r)
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                    self.frameShowHide()
                else:
                    txt = '\n set osd-level 1 \n'
                    ui.mpvplayer_val.write(bytes(txt, 'utf-8'))
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek +10 \n')
            elif event.key() == QtCore.Qt.Key_1:
                ui.mpvplayer_val.write(b'\n add chapter -1 \n')
            elif event.key() == QtCore.Qt.Key_2:
                ui.mpvplayer_val.write(b'\n add chapter 1 \n')
            elif event.key() == QtCore.Qt.Key_3:
                ui.mpvplayer_val.write(b'\n cycle ass-style-override \n')
            elif event.modifiers() == QtCore.Qt.ShiftModifier and event.key() == QtCore.Qt.Key_V:
                ui.mpvplayer_val.write(b'\n cycle ass-vsfilter-aspect-compat \n')
            elif event.key() == QtCore.Qt.Key_Left:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists":
                        ui.mpvplayer_val.write(b'\n seek -10 \n')
                    else:
                        ui.total_seek = ui.total_seek - 10
                        r = "Seeking "+str(ui.total_seek)+'s'
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                    self.frameShowHide()
                else:
                    txt = '\n set osd-level 1 \n'
                    ui.mpvplayer_val.write(bytes(txt, 'utf-8'))
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek -10 \n')
            elif event.key() == QtCore.Qt.Key_BracketRight:
                if ui.player_val == "mplayer":
                        ui.mpvplayer_val.write(b'\n seek +90 \n')
                else:
                        ui.mpvplayer_val.write(b'\n osd-msg-bar seek +90 \n')
            elif event.key() == QtCore.Qt.Key_BracketLeft:
                if ui.player_val == "mplayer":
                        ui.mpvplayer_val.write(b'\n seek -5 \n')
                else:
                        ui.mpvplayer_val.write(b'\n osd-msg-bar seek -5 \n')
            elif event.key() == QtCore.Qt.Key_0:
                if ui.player_val == "mplayer":
                        ui.mpvplayer_val.write(b'\n volume +5 \n')
                else:
                        ui.mpvplayer_val.write(b'\n add ao-volume +5 \n')
            elif event.key() == QtCore.Qt.Key_9:
                if ui.player_val == "mplayer":
                        ui.mpvplayer_val.write(b'\n volume -5 \n')
                else:
                        ui.mpvplayer_val.write(b'\n add ao-volume -5 \n')
            elif event.key() == QtCore.Qt.Key_A:
                ui.mpvplayer_val.write(b'\n cycle_values video-aspect "16:9" "4:3" "2.35:1" "-1" \n')
            elif event.key() == QtCore.Qt.Key_N:
                ui.mpvplayer_val.write(b'\n playlist_next \n')
            elif event.key() == QtCore.Qt.Key_L:
                ui.tab_5.setFocus()
            elif event.key() == QtCore.Qt.Key_End:
                if ui.player_val == "mplayer":
                    ui.mpvplayer_val.write(b'\n seek 99 1 \n')
                else:
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek 100 absolute-percent \n')
            elif event.key() == QtCore.Qt.Key_P:
                if ui.frame1.isHidden():
                    ui.gridLayout.setSpacing(0)
                    ui.frame1.show()
                else:
                    ui.gridLayout.setSpacing(5)
                    ui.frame1.hide()
            elif event.key() == QtCore.Qt.Key_Space:
                buffering_mplayer = "no"
                ui.set_parameters_value(bufm=buffering_mplayer)
                if ui.frame_timer.isActive:
                    ui.frame_timer.stop()
                if ui.mplayer_timer.isActive():
                    ui.mplayer_timer.stop()
                if ui.player_val == "mplayer":
                    if MainWindow.isFullScreen():
                        site = ui.get_parameters_value(s='site')['site']
                        if site != "Music" and ui.tab_6.isHidden() and ui.list2.isHidden():
                            ui.frame1.hide()
                    ui.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
                else:
                    param_dict = ui.get_parameters_value(
                        s='pause_indicator', m='mpv_indicator', st='site')
                    pause_indicator = param_dict['pause_indicator']
                    mpv_indicator = param_dict['mpv_indicator']
                    site = param_dict['site']
                    if not pause_indicator:
                        ui.mpvplayer_val.write(b'\n set pause yes \n')
                        if MainWindow.isFullScreen():
                            ui.frame1.show()
                            ui.gridLayout.setSpacing(0)
                        pause_indicator.append("Pause")
                        ui.set_parameters_value(pause_i=pause_indicator)
                    else:
                        ui.mpvplayer_val.write(b'\n set pause no \n')
                        if MainWindow.isFullScreen():
                            if site != "Music" and ui.tab_6.isHidden() and ui.list2.isHidden():
                                ui.gridLayout.setSpacing(0)
                                ui.frame1.hide()
                        pause_indicator.pop()
                        if mpv_indicator:
                            mpv_indicator.pop()
                            cache_empty = 'no'
                            ui.set_parameters_value(
                                cache_val=cache_empty, mpv_i=mpv_indicator)
            elif event.key() == QtCore.Qt.Key_Up:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists":
                        ui.mpvplayer_val.write(b'\n seek +60 \n')
                    else:
                        ui.total_seek = ui.total_seek + 60
                        r = "Seeking "+str(ui.total_seek)+'s'
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                else:
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek +60 \n')
                self.frameShowHide()
            elif event.key() == QtCore.Qt.Key_Down:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists": 
                        ui.mpvplayer_val.write(b'\n seek -60 \n')
                    else:
                        ui.total_seek = ui.total_seek - 60
                        r = "Seeking "+str(ui.total_seek)+'s'
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                else:
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek -60 \n')
                self.frameShowHide()
            elif event.key() == QtCore.Qt.Key_PageUp:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists":
                        ui.mpvplayer_val.write(b'\n seek +300 \n')
                    else:
                        ui.total_seek = ui.total_seek + 300
                        r = "Seeking "+str(ui.total_seek)+'s'
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                else:
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek +300 \n')
                self.frameShowHide()
            elif event.key() == QtCore.Qt.Key_PageDown:
                if ui.player_val == "mplayer":
                    site = ui.get_parameters_value(s='site')['site']
                    if site == "Local" or site == "None" or site == "PlayLists":
                        ui.mpvplayer_val.write(b'\n seek -300 \n')
                    else:
                        ui.total_seek = ui.total_seek - 300
                        r = "Seeking "+str(ui.total_seek)+'s'
                        ui.progressEpn.setFormat(r)
                        if self.seek_timer.isActive():
                            self.seek_timer.stop()
                        self.seek_timer.start(500)
                else:
                    ui.mpvplayer_val.write(b'\n osd-msg-bar seek -300 \n')
                self.frameShowHide()
            elif event.key() == QtCore.Qt.Key_O:
                if ui.player_val == 'mplayer':
                    ui.mpvplayer_val.write(b'\n osd \n')
                else:
                    ui.mpvplayer_val.write(b'\n cycle osd-level \n')
            elif event.key() == QtCore.Qt.Key_M:
                if ui.player_val == "mplayer":
                    ui.mpvplayer_val.write(b'\n osd_show_property_text ${filename} \n')
                else:
                    ui.mpvplayer_val.write(b'\n show-text "${filename}" \n')
            elif event.key() == QtCore.Qt.Key_I:
                ui.mpvplayer_val.write(b'\n show_text ${file-size} \n')
            elif event.key() == QtCore.Qt.Key_E:
                if ui.mpvplayer_val.processId() > 0:
                    w=self.width()
                    w = w + (0.05*w)
                    h = self.height()
                    h = h + (0.05*h)
                    self.setMaximumSize(w, h)
                    self.setMinimumSize(w, h)
            elif event.key() == QtCore.Qt.Key_W:
                if ui.mpvplayer_val.processId() > 0:
                    w=self.width()
                    w = w - (0.05*w)
                    h = self.height()
                    h = h - (0.05*h)
                    self.setMaximumSize(w, h)
                    self.setMinimumSize(w, h)
            elif event.key() == QtCore.Qt.Key_R:
                if ui.player_val == "mplayer":
                    ui.mpvplayer_val.write(b'\n sub_pos -1 \n')
                else:
                    ui.mpvplayer_val.write(b'\n add sub-pos -1 \n')
            elif event.key() == QtCore.Qt.Key_T:
                if ui.player_val == "mplayer":
                    ui.mpvplayer_val.write(b'\n sub_pos +1 \n')
                else:
                    ui.mpvplayer_val.write(b'\n add sub-pos +1 \n')
            elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_J):
                #self.ui.load_external_sub()
                ui.tab_5.load_external_sub()
            elif event.key() == QtCore.Qt.Key_J:
                if ui.player_val == "mplayer":
                    if not self.mplayer_OsdTimer.isActive():
                        ui.mpvplayer_val.write(b'\n osd 1 \n')
                    else:
                        self.mplayer_OsdTimer.stop()
                    ui.mpvplayer_val.write(b'\n sub_select \n')
                    ui.mpvplayer_val.write(b'\n get_property sub \n')
                    self.mplayer_OsdTimer.start(5000)
                else:
                    ui.mpvplayer_val.write(b'\n cycle sub \n')
                    ui.mpvplayer_val.write(b'\n print-text "SUB_ID=${sid}" \n')
                    ui.mpvplayer_val.write(b'\n show-text "${sid}" \n')
            elif event.key() == QtCore.Qt.Key_K:
                if ui.player_val == "mplayer":
                    if not self.mplayer_OsdTimer.isActive():
                        ui.mpvplayer_val.write(b'\n osd 1 \n')
                    else:
                        self.mplayer_OsdTimer.stop()
        
                    ui.mpvplayer_val.write(b'\n switch_audio \n')
                    self.mplayer_OsdTimer.start(5000)
                else:
                    ui.mpvplayer_val.write(b'\n cycle audio \n')
                    ui.mpvplayer_val.write(b'\n print-text "Audio_ID=${aid}" \n')
                    ui.mpvplayer_val.write(b'\n show-text "${aid}" \n')
            elif event.key() == QtCore.Qt.Key_Period:
                ui.mpvNextEpnList()
            elif event.key() == QtCore.Qt.Key_Comma:
                ui.mpvPrevEpnList()
            elif (event.modifiers() == QtCore.Qt.ControlModifier
                and event.key() == QtCore.Qt.Key_Q):
                quitReally = "yes"
                ui.set_parameters_value(quit_r=quitReally)
                msg = '"Stop After current file"'
                msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
                ui.mpvplayer_val.write(msg_byt)
            elif (event.modifiers() == QtCore.Qt.ShiftModifier
                and event.key() == QtCore.Qt.Key_Q):
                quitReally = "yes"
                ui.set_parameters_value(quit_r=quitReally)
                ui.playerStop(msg='remember quit')
            elif event.key() == QtCore.Qt.Key_Q:
                ui.player_stop.clicked.emit()
            elif event.key() == QtCore.Qt.Key_F:
                mode = None
                if ui.video_mode_index == 1:
                    self.player_thumbnail_fs()
                elif ui.video_mode_index in range(3, 6):
                    num = ui.thumbnail_label_number[0]
                    p1 = "ui.label_epn_{0}.width()".format(num)
                    p2 = "ui.label_epn_{0}.height()".format(num)
                    wd = eval(p1)
                    ht = eval(p2)
                    fs = False
                    logger.debug('{0}, {1}::original {2}, {3}'.format(wd, ht, screen_width, screen_height))
                    if wd == screen_width and ht == screen_height:
                        fs = True
                    if not fs:
                        self.player_thumbnail_fs(mode='fs_now')
                    else:
                        self.player_thumbnail_fs()
                    if self.fs_timer_focus.isActive():
                        self.fs_timer_focus.stop()
                    self.fs_timer_focus.start(1000)
        super(ThumbnailWidget, self).keyPressEvent(event)

    def player_thumbnail_fs(self, mode=None):
        param_dict = ui.get_parameters_value(
            wgt='wget', icn='iconv_r_indicator', i='iconv_r', fl='fullscr')
        wget = param_dict['wget']
        iconv_r_indicator = param_dict['iconv_r_indicator']
        iconv_r = param_dict['iconv_r']
        fullscr = param_dict['fullscr']
        if not MainWindow.isHidden():
            if ui.video_mode_index == 6:
                pass
            else:
                if iconv_r_indicator:
                    iconv_r = iconv_r_indicator[0]
                fullscr = 1 - fullscr
                ui.set_parameters_value(iconv=iconv_r, fullsc=fullscr)
                widget = "ui.label_epn_"+str(ui.thumbnail_label_number[0])
                col = (ui.thumbnail_label_number[0]%iconv_r)
                row = 2*int(ui.thumbnail_label_number[0]/iconv_r)
                new_pos = (row, col)
                print(new_pos)
                if not MainWindow.isFullScreen() or mode == 'fs' or mode == 'fs_now':
                    if mode != 'fs':
                        p1 = "ui.gridLayout2.indexOf(ui.label_epn_{0})".format(ui.thumbnail_label_number[0])
                        index = eval(p1)
                        print(index, '--index--')
                        ui.current_thumbnail_position = ui.gridLayout2.getItemPosition(index)
                        ui.tab_6.hide()
                        p1 = "ui.gridLayout.addWidget({0}, 0, 1, 1, 1)".format(widget)
                        exec(p1)
                        p2= "ui.label_epn_{0}.setMaximumSize(QtCore.QSize({1}, {2}))".format(ui.thumbnail_label_number[0], screen_width, screen_height)
                        exec (p2)
                        ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                        ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        ui.gridLayout1.setContentsMargins(0, 0, 0, 0)
                        ui.gridLayout2.setContentsMargins(0, 0, 0, 0)
                        ui.gridLayout.setSpacing(0)
                        ui.gridLayout1.setSpacing(0)
                        ui.gridLayout2.setSpacing(0)
                        ui.superGridLayout.setSpacing(0)
                    MainWindow.showFullScreen()
                else:
                    w = float((ui.tab_6.width()-60)/iconv_r)
                    h = int(w/ui.image_aspect_allowed)
                    width=str(int(w))
                    height=str(int(h))
                    r = ui.current_thumbnail_position[0]
                    c = ui.current_thumbnail_position[1]
                    p6="ui.gridLayout2.addWidget(ui.label_epn_"+str(ui.thumbnail_label_number[0])+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
                    exec(p6)
                    QtWidgets.QApplication.processEvents()
                    if not ui.force_fs:
                        MainWindow.showNormal()
                        MainWindow.showMaximized()

                    p1="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".y()"
                    yy=eval(p1)
                    ui.scrollArea1.verticalScrollBar().setValue(yy)
                    QtWidgets.QApplication.processEvents()
                    ui.frame1.show()
                    ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                    ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    ui.gridLayout1.setContentsMargins(5, 5, 5, 5)
                    ui.gridLayout2.setContentsMargins(5, 5, 5, 5)
                    ui.gridLayout.setSpacing(5)
                    ui.gridLayout1.setSpacing(5)
                    ui.gridLayout2.setSpacing(5)
                    ui.superGridLayout.setSpacing(5)
                    ui.tab_6.show()
                    QtWidgets.QApplication.processEvents()
                    p1="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setFocus()"
                    exec(p1)
                    QtCore.QTimer.singleShot(1000, ui.update_thumbnail_position)
        else:
            if not ui.float_window.isHidden():
                if not ui.float_window.isFullScreen():
                    p1 = "ui.gridLayout2.indexOf(ui.label_epn_{0})".format(ui.thumbnail_label_number[0])
                    index = eval(p1)
                    print(index, '--index--')
                    ui.current_thumbnail_position = ui.gridLayout2.getItemPosition(index)
                    ui.float_window.showFullScreen()
                else:
                    ui.float_window.showNormal()
                    
    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        self.setFocus()
        pos = event.pos()
        if not ui.float_window.isHidden() and ui.new_tray_widget.remove_toolbar:
            if ui.float_timer.isActive():
                ui.float_timer.stop()
            if ui.new_tray_widget.cover_mode.text() == ui.player_buttons['up']:
                wid_height = int(ui.float_window.height()/3)
            else:
                wid_height = int(ui.float_window.height())
            ui.new_tray_widget.setMaximumHeight(wid_height)
            ui.new_tray_widget.show()
            ui.float_timer.start(1000)

        if ui.player_val == "mplayer" or ui.player_val=="mpv":
            try:
                idw = ui.get_parameters_value(i='idw')['idw']
                if str(idw) == str(int(self.winId())):
                    if self.arrow_timer.isActive():
                        self.arrow_timer.stop()
                    self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    if ui.mpvplayer_val.processId() > 0:
                        self.arrow_timer.start(2000)
            except Exception as e:
                logger.error(e)
                self.arrow_timer = QtCore.QTimer()
                self.arrow_timer.timeout.connect(self.arrow_hide)
                self.arrow_timer.setSingleShot(True)

        if MainWindow.isFullScreen():
            ht = self.height()
            if not ui.tab_6.isHidden() or not ui.list2.isHidden() or not ui.list1.isHidden() or not ui.tab_2.isHidden():
                if ui.frame1.isHidden():
                    ui.frame1.show()
            else:
                if pos.y() <= ht and pos.y()> ht - 5 and ui.frame1.isHidden():
                    ui.gridLayout.setSpacing(0)
                    ui.frame1.show()
                    ui.frame1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                elif pos.y() <= ht-32 and not ui.frame1.isHidden() :
                    ui.frame1.hide()
                    ui.gridLayout.setSpacing(5)


    def change_video_mode(self, var_mode, c_row, restart=None):
        """
        Mode 1: Show video within thumbnail and fullscreen by default
        Mode 2: Default mode
        Mode 3: Show video within thumbnail
        Mode 4: Show video within thumbnail but with enlarged size of thumbnail
                widget
        Mode 5: Show video within thumbnail but in a list form
        
        Mode 6: Show video in thumbnail/poster label widget
        """
        param_dict = ui.get_parameters_value(
            s='site', tab6='tab_6_size_indicator',
            serv='server', tab_pl='tab_6_player',
            iconv_r='iconv_r', iconv_r_indicator='iconv_r_indicator')
        site = param_dict['site']
        tab_6_size_indicator = param_dict['tab_6_size_indicator']
        server = param_dict['server']
        tab_6_player = param_dict['tab_6_player']
        iconv_r = param_dict['iconv_r']
        iconv_r_indicator = param_dict['iconv_r_indicator']
        finalUrl = ''
        curR = c_row
        ui.set_parameters_value(curRow=curR)
        if var_mode == 2:
            ui.label_search.clear()
            ui.labelFrame2.hide()
            tab_6_player = "False"
            if tab_6_size_indicator:
                tab_6_size_indicator.pop()
            if ui.tab_6.width()>500:
                tab_6_size_indicator.append(ui.tab_6.width())
            ui.set_parameters_value(tab_6=tab_6_size_indicator)
            ui.gridLayout.setSpacing(0)
            if (site == "Local" or site == "PlayLists" or site == "Music" or 
                site == "Video" or site == "None"):
                num = curR
                ui.gridLayout.addWidget(ui.tab_6, 0, 2, 1, 1)
                if '	' in ui.epn_arr_list[num]:
                    new_epn = (ui.epn_arr_list[num]).split('	')[0]
                else:
                    new_epn = os.path.basename(ui.epn_arr_list[num])
                if new_epn.startswith('#'):
                    new_epn = new_epn.replace('#', '', 1)
                ui.epn_name_in_list = new_epn
                finalUrl = ui.epn_return(num)
                if finalUrl.startswith('"'):
                    finalUrl = finalUrl.replace('"', '')
                elif finalUrl.startswith("'"):
                    finalUrl = finalUrl.replace("'", '')
                if num < ui.list2.count():
                    ui.list2.setCurrentRow(num)
                    idw = str(int(ui.tab_5.winId()))
                    ui.set_parameters_value(idw_val=idw)
                    ui.gridLayout.addWidget(ui.tab_5, 0, 1, 1, 1)
                    ui.tab_5.show()
                    ui.tab_5.setFocus()
                    ui.frame1.show()
                    if iconv_r_indicator and iconv_r != 1:
                        iconv_r_indicator.pop()
                    if iconv_r != 1:
                        iconv_r_indicator.append(iconv_r)
                    iconv_r = 1
                    ui.set_parameters_value(iconv=iconv_r)
                    ui.thumbnail_label_update_epn()
                    QtWidgets.QApplication.processEvents()
                    p1 = "ui.label_epn_"+str(num)+".y()"
                    ht = eval(p1)
                    print(ht, '--ht--', ui.scrollArea1.height())
                    ui.scrollArea1.verticalScrollBar().setValue(ht - 5)
                    ui.play_file_now(finalUrl)
                    if site == "Music":
                        logger.info(finalUrl)
                        ui.text.show()
                        ui.label.show()
                        try:
                            artist_name_mplayer = ui.epn_arr_list[num].split('	')[2]
                            if artist_name_mplayer == "None":
                                artist_name_mplayer = ""
                        except:
                            artist_name_mplayer = ""
                        ui.set_parameters_value(amp=artist_name_mplayer)
                        ui.media_data.update_music_count('count', finalUrl)
                    
                    elif site == "Video":
                        ui.media_data.update_video_count('mark', finalUrl)
                    current_playing_file_path = finalUrl
                    ui.set_parameters_value(cur_ply=current_playing_file_path)
            else:
                    num = curR
                    if '	' in ui.epn_arr_list[num]:
                        new_epn = (ui.epn_arr_list[num]).split('	')[0]
                    else:
                        new_epn = os.path.basename(ui.epn_arr_list[num])
                    if new_epn.startswith('#'):
                        new_epn = new_epn.replace('#', '', 1)
                    ui.epn_name_in_list = new_epn
                    ui.list2.setCurrentRow(num)
                    finalUrl = ui.epn_return(num)
                    if finalUrl.startswith('"'):
                        finalUrl = finalUrl.replace('"', '')
                    elif finalUrl.startswith("'"):
                        finalUrl = finalUrl.replace("'", '')
                    if num < ui.list2.count():
                        ui.gridLayout.addWidget(ui.tab_5, 0, 1, 1, 1)
                        ui.gridLayout.addWidget(ui.tab_6, 0, 2, 1, 1)
                        print(ui.tab_5.width())
                        ui.tab_5.show()
                        ui.tab_5.setFocus()
                        ui.frame1.show()
                        i = 0
                        ui.play_file_now(finalUrl)
                        iconv_r = 1
                        ui.set_parameters_value(iconv=iconv_r, thumb_indicator='empty')
                        ui.thumbnail_label_update_epn()
                        QtWidgets.QApplication.processEvents()
                        p1 = "ui.label_epn_"+str(num)+".y()"
                        ht = eval(p1)
                        print(ht, '--ht--', ui.scrollArea1.height())
                        ui.scrollArea1.verticalScrollBar().setValue(ht)

            title_num = num + ui.list2.count()
            if ui.epn_name_in_list.startswith(ui.check_symbol):
                newTitle = ui.epn_name_in_list
            else:
                newTitle = ui.check_symbol+ui.epn_name_in_list	
            sumry = "<html><h1>"+ui.epn_name_in_list+"</h1></html>"
            newTitle = newTitle.replace('_', ' ')
            q3="ui.label_epn_"+str(title_num)+".setText((newTitle))"
            exec (q3)
            q3="ui.label_epn_"+str(title_num)+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(q3)
            t= ui.epn_name_in_list[:20]
            ui.labelFrame2.setText(newTitle)
            QtWidgets.QApplication.processEvents()
            if site == "Music":
                self.setFocus()
                r = ui.list2.currentRow()
                ui.musicBackground(r, 'Search')
            try:
                server._emitMeta("Play", site, ui.epn_arr_list)
            except Exception as e:
                print(e, '--681--thumbnail.py')
            # Default Mode Ends Here#
        elif var_mode == 1 or var_mode == 3 or var_mode == 4:
            if ui.mpvplayer_val.processId()>0:
                ui.mpvplayer_val.kill()
                ui.mpvplayer_started = False
                ui.tab_5.hide()
                ui.tab_6.setMaximumSize(16777215, 16777215)
            tab_6_player = "True"
            ui.set_parameters_value(t6_ply=tab_6_player)
            num = curR
            self.setFocus()
            ui.gridLayout2.setAlignment(QtCore.Qt.AlignCenter)
            if var_mode == 4:
                w = float(ui.thumbnail_video_width)
                #h = float((9*w)/16)
                h = int(w/ui.image_aspect_allowed)
                width=str(int(w))
                height=str(int(h))

                p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                exec (p2)
                exec (p3)
                QtWidgets.QApplication.processEvents()
                QtWidgets.QApplication.processEvents()
                p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".y()"
                p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".x()"
                yy= eval(p2)
                xy= eval(p3)
                p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".width()"
                p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".height()"
                wdt=eval(p2)
                hgt=eval(p3)

                ui.scrollArea1.horizontalScrollBar().setValue(xy-10)
                ui.scrollArea1.verticalScrollBar().setValue(yy-10)

            quitReally = "no"
            ui.set_parameters_value(quit_r=quitReally)
            ui.list2.setCurrentRow(num)
            p4="ui.label_epn_"+str(num)+".setMouseTracking(True)"
            exec (p4)
            ui.gridLayout.addWidget(ui.tab_6, 0, 1, 1, 1)
            if '	' in ui.epn_arr_list[num]:
                finalUrl = '"'+(ui.epn_arr_list[num]).split('	')[1]+'"'
                new_epn = (ui.epn_arr_list[num]).split('	')[0]
            else:
                finalUrl = '"'+ui.epn_arr_list[num]+'"'
                new_epn = os.path.basename(ui.epn_arr_list[num])

            if new_epn.startswith('#'):
                new_epn = new_epn.replace('#', ui.check_symbol, 1)
            new_epn = new_epn.replace('_', ' ')
            ui.epn_name_in_list = new_epn
            
            finalUrl = ui.epn_return(num)
            if finalUrl.startswith('"'):
                finalUrl = finalUrl.replace('"', '')
            elif finalUrl.startswith("'"):
                finalUrl = finalUrl.replace("'", '')
            if finalUrl.startswith('abs_path=') or finalUrl.startswith('relative_path='):
                finalUrl = ui.if_path_is_rel(finalUrl)
            if num < ui.list2.count():
                ui.list2.setCurrentRow(num)
                p1 = "ui.label_epn_"+str(num)+".winId()"
                mn=int(eval(p1))
                idw = str(mn)
                ui.set_parameters_value(idw_val=idw)
                ui.frame1.show()
                finalUrl = str(finalUrl)
                if ui.player_val == "mplayer":
                    command = ui.mplayermpv_command(idw, finalUrl, 'mplayer')
                    logger.info(command)
                    ui.infoPlay(command)
                elif ui.player_val == "mpv":
                    command = ui.mplayermpv_command(idw, finalUrl, 'mpv')
                    logger.info(command)
                    ui.infoPlay(command)	
            ui.labelFrame2.setText(ui.epn_name_in_list)
            #Mode 2, 3 Ends Here#
            if var_mode == 1:
                if self.fs_timer.isActive():
                    self.fs_timer.stop()
                self.fs_timer.start(1000)
        elif var_mode == 5:
            if ui.mpvplayer_val.processId()>0:
                ui.mpvplayer_val.kill()
                ui.mpvplayer_started = False
                ui.tab_5.hide()
                ui.tab_6.setMaximumSize(16777215, 16777215)
            if iconv_r_indicator and iconv_r != 1:
                iconv_r_indicator.pop()
            if iconv_r != 1:
                iconv_r_indicator.append(iconv_r)
            iconv_r = 1
            ui.set_parameters_value(iconv=iconv_r)
            ui.tab_6.setMaximumSize(ui.width_allowed, 16777215) # (400, 1000) earlier

            ui.thumbnail_label_update()
            tab_6_player = "True"
            
            ui.set_parameters_value(t6_ply=tab_6_player)

            num = curR
            self.setFocus()
            ui.gridLayout2.setAlignment(QtCore.Qt.AlignCenter)
            w = float(ui.thumbnail_video_width)
            h = int(w/ui.image_aspect_allowed)
            width=str(int(w))
            height=str(int(h))
            dim = (width, height)

            p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
            p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
            exec (p2)
            exec (p3)
            QtWidgets.QApplication.processEvents()
            QtWidgets.QApplication.processEvents()
            p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".y()"
            p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".x()"
            yy=eval(p2)
            xy=eval(p3)
            print(dim, '--dim--', 'y=', yy, 'x=', xy)
            p2="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".width()"
            p3="ui.label_epn_"+str(ui.thumbnail_label_number[0])+".height()"
            wdt=eval(p2)
            hgt=eval(p3)

            ui.scrollArea1.horizontalScrollBar().setValue(xy-10)
            ui.scrollArea1.verticalScrollBar().setValue(yy-10)

            quitReally = "no"
            ui.set_parameters_value(quit_r=quitReally)
            ui.list2.setCurrentRow(num)
            p4="ui.label_epn_"+str(num)+".setMouseTracking(True)"
            exec(p4)
            #ui.gridLayout.addWidget(ui.tab_5, 0, 0, 1, 1)
            ui.gridLayout.addWidget(ui.tab_6, 0, 1, 1, 1)
            if '	' in ui.epn_arr_list[num]:
                finalUrl = '"'+(ui.epn_arr_list[num]).split('	')[1]+'"'
                new_epn = (ui.epn_arr_list[num]).split('	')[0]
            else:
                finalUrl = '"'+ui.epn_arr_list[num]+'"'
                new_epn = os.path.basename(ui.epn_arr_list[num])

            if new_epn.startswith('#'):
                    new_epn = new_epn.replace('#', '', 1)
            ui.epn_name_in_list = new_epn

            finalUrl = ui.epn_return(num)
            if finalUrl.startswith('"'):
                finalUrl = finalUrl.replace('"', '')
            elif finalUrl.startswith("'"):
                finalUrl = finalUrl.replace("'", '')
            if finalUrl.startswith('abs_path=') or finalUrl.startswith('relative_path='):
                finalUrl = ui.if_path_is_rel(finalUrl)
            if num < ui.list2.count():
                ui.list2.setCurrentRow(num)
                p1 = "ui.label_epn_"+str(num)+".winId()"
                mn=int(eval(p1))
                idw = str(mn)
                ui.set_parameters_value(idw_val=idw)
                ui.frame1.show()
                finalUrl = str(finalUrl)
                if ui.player_val == "mplayer":
                    command = ui.mplayermpv_command(idw, finalUrl, 'mplayer')
                    logger.info(command)
                    ui.infoPlay(command)
                elif ui.player_val == "mpv":
                    command = ui.mplayermpv_command(idw, finalUrl, 'mpv')
                    logger.info(command)
                    ui.infoPlay(command)	
            ui.labelFrame2.setText(ui.epn_name_in_list)
        elif var_mode == 6 or var_mode == 7:
            tab_6_player = "True"

            num = curR
            self.setFocus()
            quitReally = "no"
            ui.set_parameters_value(quit_r=quitReally, t6_ply=tab_6_player)
            ui.list2.setCurrentRow(num)
            p4="ui.label.setMouseTracking(True)"
            exec(p4)

            if '	' in ui.epn_arr_list[num]:
                finalUrl = '"'+(ui.epn_arr_list[num]).split('	')[1]+'"'
                new_epn = (ui.epn_arr_list[num]).split('	')[0]
                ui.epn_name_in_list = new_epn
            else:
                finalUrl = '"'+ui.epn_arr_list[num]+'"'
                new_epn = os.path.basename(ui.epn_arr_list[num])
                ui.epn_name_in_list = new_epn
            finalUrl = ui.epn_return(num)
            if finalUrl.startswith('"'):
                finalUrl = finalUrl.replace('"', '')
            elif finalUrl.startswith("'"):
                finalUrl = finalUrl.replace("'", '')
            if finalUrl.startswith('abs_path=') or finalUrl.startswith('relative_path='):
                finalUrl = ui.if_path_is_rel(finalUrl)
            if var_mode == 6:
                tmp_idw = str(int(ui.label.winId()))
            else:
                tmp_idw = str(int(ui.label_new.winId()))
            idw = ui.get_parameters_value(i='idw')['idw']
            if tmp_idw != idw:
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.kill()
                    ui.mpvplayer_started = False
                    ui.tab_5.hide()
                    ui.tab_6.setMaximumSize(10000, 10000)

            if ui.mpvplayer_val.processId() > 0:
                ui.play_file_now(finalUrl)
            else:
                if num < ui.list2.count():
                    ui.list2.setCurrentRow(num)
                    if var_mode == 6:
                        p1 = "ui.label.winId()"
                    else:
                        p1 = "ui.label_new.winId()"
                    mn = int(eval(p1))
                    idw = str(mn)
                    ui.set_parameters_value(idw_val=idw)
                    #ui.tab_5.setFocus()
                    ui.frame1.show()
                    finalUrl = str(finalUrl)
                    if ui.player_val == "mplayer":
                        command = ui.mplayermpv_command(idw, finalUrl, 'mplayer')
                        logger.info(command)
                        ui.infoPlay(command)
                    elif ui.player_val == "mpv":
                        command = ui.mplayermpv_command(idw, finalUrl, 'mpv')
                        logger.info(command)
                        ui.infoPlay(command)
            #Mode 2 Ends Here#

        current_playing_file_path = finalUrl
        ui.set_parameters_value(cur_ply=current_playing_file_path)
        try:
            server._emitMeta("Play", site, ui.epn_arr_list)
        except Exception as e:
            print(e, '--934--thumbnail.py')
        try:
            if site.lower() == "music":
                    try:
                        artist_name_mplayer = ui.epn_arr_list[row].split('	')[2]
                        if artist_name_mplayer.lower() == "none":
                            artist_name_mplayer = ""
                    except:
                        artist_name_mplayer = ""
                    ui.set_parameters_value(amp=artist_name_mplayer)
                    ui.media_data.update_music_count('count', finalUrl)
                    r = curR
                    ui.musicBackground(r, 'Search')
            elif site.lower() == 'video' or site.lower() == 'local' or site.lower() == 'playlists':
                try:
                    row = curR
                    if (site.lower() == 'playlists'):
                        if ui.is_artist_exists(row):
                            ui.musicBackground(row, 'get now')
                            ui.media_data.update_music_count('count', finalUrl)
                        else:
                            try:
                                thumb_path = ui.get_thumbnail_image_path(row, ui.epn_arr_list[row])
                                logger.info("thumbnail path = {0}".format(thumb_path))
                                if os.path.exists(thumb_path):
                                    ui.videoImage(thumb_path, thumb_path, thumb_path, '')
                            except Exception as e:
                                logger.info('Error in getting Thumbnail: {0}'.format(e))
                    elif site.lower() == "video":
                        ui.media_data.update_video_count('mark', finalUrl)
                        thumb_path = ui.get_thumbnail_image_path(row, ui.epn_arr_list[row])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            ui.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    logger.info('Error in getting Thumbnail--1620-- - localvideogetinlist: {0}'.format(e))
        except Exception as e:
            print(e, '--1622--')
        
        try:
            new_cnt = curR + ui.list2.count()
            p1 = "ui.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(new_cnt)
            exec (p1)
            p1 = "ui.label_epn_{0}.toPlainText()".format(new_cnt)
            txt = eval(p1)
            try:
                p1 = "ui.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                exec(p1)
            except Exception as e:
                print(e, '--line--4597--')
                try:
                    p1 = 'ui.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                    exec(p1)
                except Exception as e:
                    print(e)
            p1="ui.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
            exec(p1)
        except Exception as e:
            print(e)
        try:
            if var_mode == 1 or var_mode == 2 or var_mode == 3 or var_mode == 4 or var_mode == 5:
                if site.lower() == 'music' or site.lower() == 'none' or site.lower() == 'local':
                    pass
                elif site.lower() == 'video':
                    ui.mark_video_list('mark', curR)
                elif site.lower() == 'playlists':
                    ui.mark_playlist('mark', curR)
                else:
                    ui.mark_addons_history_list('mark', curR)
        except Exception as e:
            print(e)
    
    def mouseDoubleClickEvent(self, event):
        if ui.video_mode_index == 1:
            pass
        else:
            msg = 'In this mode Fullscreen allowed using Key F. Use keys W or E to decrease/increase size'
            ui.labelFrame2.setText(msg)
    
    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.setFocus()
            quitReally = "no"
            ui.set_parameters_value(quit_r=quitReally)
            label_name = str(self.objectName())
            label_watch = False
            if label_name in ['label', 'label_new']:
                num = ui.list2.currentRow()
                curR = num
                ui.set_parameters_value(curRow=curR)
                if label_name == 'label':
                    ui.video_mode_index = 6
                    p1 = "ui.label.winId()"
                else:
                    ui.video_mode_index = 7
                    p1 = "ui.label_new.winId()"
                if ui.player_theme == 'default':
                    ui.label_new.setMinimumHeight(2.5*ui.height_allowed)
                    ui.video_mode_index = 7
                    p1 = "ui.label_new.winId()"
                mn = int(eval(p1))
                tmp_idw = str(mn)
                label_watch = True
            else:
                label_num = re.sub('label_epn_', '', label_name)
                num = int(label_num)
                curR = num
                ui.set_parameters_value(curRow=curR)
                p1 = "ui.label_epn_"+str(num)+".winId()"
                mn = int(eval(p1))
                tmp_idw = str(mn)
                if ui.video_mode_index == 6:
                    ui.video_mode_index = 1
                    ui.comboBoxMode.setCurrentIndex(0)
            idw = ui.get_parameters_value(i='idw')['idw']
            if tmp_idw == idw:
                if ui.mpvplayer_val.processId() > 0:
                    ui.playerPlayPause()
                else:
                    if not label_watch:
                        self.remember_thumbnail_position(num)
                    self.change_video_mode(ui.video_mode_index, num)
            else:
                if label_name not in ['label', 'label_new']:
                    self.remember_thumbnail_position(num)
                self.change_video_mode(ui.video_mode_index, num)
                
    def remember_thumbnail_position(self, num):
        p1 = "ui.gridLayout2.indexOf(ui.label_epn_{0})".format(num)
        index = eval(p1)
        print(index, '--index--')
        ui.current_thumbnail_position = ui.gridLayout2.getItemPosition(index)
        txt_count = num + ui.list2.count()
        p1 = "ui.label_epn_{0}.toPlainText()".format(txt_count)
        txt = eval(p1)
        ui.thumbnail_label_number[:] = []
        ui.thumbnail_label_number = [num, txt]
    
    def play_within_poster(self):
        quitReally = "no"
        ui.set_parameters_value(quit_r=quitReally)
        num = ui.list2.currentRow()
        if num >= 0:
            curR = num
            ui.set_parameters_value(curRow=curR)
            ui.video_mode_index = 5
            p1 = "ui.label.winId()"
            mn=int(eval(p1))
            tmp_idw = str(mn)
            self.change_video_mode(ui.video_mode_index, num)
                
    def triggerPlaylist(self, val):
        print('Menu Clicked')
        print(val.text())
        value = str(val.text())
        t=str(self.objectName())
        t = re.sub('label_epn_', '', t)
        num = int(t)
        param_dict = ui.get_parameters_value(s='site', r='refererNeeded')
        site = param_dict['site']
        refererNeeded = param_dict['refererNeeded']
        file_path = os.path.join(home, 'Playlists', str(value))
        if (site == "Music" or site == "Video" or site == "Local" or 
            site == "None" or site == "PlayLists"):
            if os.path.exists(file_path):
                #i = ui.list2.currentRow()
                i = num
                sumr = ui.epn_arr_list[i].split('	')[0]
                try:
                    rfr_url = ui.epn_arr_list[i].split('	')[2]
                except:
                    rfr_url = "NONE"
                sumry = ui.epn_arr_list[i].split('	')[1]
                sumry = sumry.replace('"', '')
                if not sumry.startswith('http'):
                    sumry = '"'+sumry+'"'
                t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)
        else:
            path_final_Url = ui.epn_return(num)
            ui.set_parameters_value(path_final=path_final_Url)
            t = ''
            try:
                if '	' in ui.epn_arr_list[num]:
                    sumr = ui.epn_arr_list[num].split('	')[0]
                else:
                    sumr = ui.epn_arr_list[num]
            except Exception as e:
                print(e)
                sumr = 'NONE'
            if os.path.exists(file_path):
                if isinstance(path_final_Url, list):
                    if refererNeeded == True:
                        rfr_url = path_final_Url[1]
                        sumry = path_final_Url[0]
                        t = sumr+'	'+sumry+'	'+rfr_url
                    else:
                        rfr_url = "NONE"
                        j = 1
                        t = ''
                        for i in path_final_Url:
                            p = "-Part-"+str(j)
                            sumry = i
                            if j == 1:
                                t = sumr+p+'	'+sumry+'	'+rfr_url
                            else:
                                t = t + '\n' + sumr+p+'	'+sumry+'	'+rfr_url
                            j = j+1
                else:
                    rfr_url = "NONE"
                    sumry = path_final_Url
                    t = sumr+'	'+sumry+'	'+rfr_url
                write_files(file_path, t, line_by_line=True)
                
    def contextMenuEvent(self, event):
        param_dict = ui.get_parameters_value(
            m='memory_num_arr', f='finalUrlFound',
            r='refererNeeded', i='interval', s='site', n='name')
        memory_num_arr = param_dict['memory_num_arr']
        finalUrlFound = param_dict['finalUrlFound']
        refererNeeded = param_dict['refererNeeded']
        interval = param_dict['interval']
        name = param_dict['name']
        site = param_dict['site']
        ui.total_seek = 0
        t=str(self.objectName())
        thumbnail_grid = True
        if t == 'label':
            num = ui.list2.currentRow()
            thumbnail_grid = False
        else:
            t = re.sub('label_epn_', '', t)
            num = int(t)
        menu = QtWidgets.QMenu(self)
        submenuR = QtWidgets.QMenu(menu)
        submenuR.setTitle("Add To Playlist")
        menu.addMenu(submenuR)
        queue_item = menu.addAction("Queue Item")
        thumb = menu.addAction("Show other Thumbnails")
        removeThumb = menu.addAction("Remove Thumbnail")
        list_mode = menu.addAction("Go To List Mode")
        group = QtWidgets.QActionGroup(submenuR)
        pls = os.listdir(os.path.join(home, 'Playlists'))
        for i in pls:
            item = submenuR.addAction(i)
            item.setData(i)
            item.setActionGroup(group)
        group.triggered.connect(self.triggerPlaylist)
        submenuR.addSeparator()
        new_pls = submenuR.addAction("Create New Playlist")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        self.setFocus()
        if action == queue_item:
            if (site == "Music" or site == "Video" or site == "Local" 
                    or site == "PlayLists" or site == "None" or site == "MyServer"):
                file_path = os.path.join(home, 'Playlists', 'Queue')
                if not os.path.exists(file_path):
                    f = open(file_path, 'w')
                    f.close()
                if not ui.queue_url_list:
                    ui.list6.clear()
                r = num
                item = ui.list2.item(r)
                if item:
                    ui.queue_url_list.append(ui.epn_arr_list[r])
                    ui.list6.addItem(ui.epn_arr_list[r].split('	')[0])
                    logger.info(ui.queue_url_list)
                    write_files(file_path, ui.epn_arr_list[r], line_by_line=True)
        elif action == new_pls:
            print("creating")
            item, ok = QtWidgets.QInputDialog.getText(
                MainWindow, 'Input Dialog', 'Enter Playlist Name')
            if ok and item:
                file_path = os.path.join(home, 'Playlists', item)
                if not os.path.exists(file_path):
                    f = open(file_path, 'w')
                    f.close()
        elif action == list_mode:
            ui.thumbnailHide('none')
        elif action == removeThumb:
            if ui.list1.currentItem():
                nm = ui.list1.currentItem().text()
            else:
                nm = ''
            picn = ui.get_thumbnail_image_path(num, ui.epn_arr_list[num], only_name=True)
            if os.path.exists(picn):
                os.remove(picn)
                small_nm_1, new_title = os.path.split(picn)
                small_nm_2 = '128px.'+new_title
                small_nm_3 = '480px.'+new_title
                small_nm_4 = 'label.'+new_title
                new_small_thumb = os.path.join(small_nm_1, small_nm_2)
                small_thumb = os.path.join(small_nm_1, small_nm_3)
                label_thumb = os.path.join(small_nm_1, small_nm_4)
                logger.info(new_small_thumb)
                if os.path.exists(new_small_thumb):
                    os.remove(new_small_thumb)
                if os.path.exists(small_thumb):
                    os.remove(small_thumb)
                if os.path.exists(label_thumb):
                    os.remove(label_thumb)
                if thumbnail_grid:
                    q1="ui.label_epn_"+str(num)+".clear()"
                else:
                    q1="ui.label.clear()"
                exec(q1)
            interval = 0
            ui.set_parameters_value(inter=interval)
        elif action == thumb:
            width = self.width()
            height = self.height()
            if (site == "Local" or finalUrlFound == True or site=="None" 
                    or site =="PlayLists" or site == "Video" or site == "Music"
                    or site == "MyServer"):
                ui.list2.setCurrentRow(num)
                if memory_num_arr:
                    t_num = memory_num_arr.pop()
                else:
                    t_num = -1
                
                if t_num != num:
                    if site != "PlayLists":
                        path_final_Url = ui.epn_return(num)
                    interval = 10
                memory_num_arr.append(num)
                ui.set_parameters_value(inter=interval, memory_num=memory_num_arr)
                if '	' in ui.epn_arr_list[num]:
                    path = (ui.epn_arr_list[num]).split('	')[1]
                else:	
                    path = ui.epn_arr_list[num]
                if path.startswith('#'):
                    path = path.replace('#', '', 1)
                if path.startswith('"'):
                    path = path.replace('"', '', 1)
                picn = picn_new = ui.get_thumbnail_image_path(num, ui.epn_arr_list[num], only_name=True)
                if os.path.exists(picn_new):
                    small_nm_1, new_title = os.path.split(picn_new)
                    small_nm_2 = '128px.'+new_title
                    small_nm_3 = '480px.'+new_title
                    small_nm_4 = 'label.'+new_title
                    new_small_thumb = os.path.join(small_nm_1, small_nm_2)
                    small_thumb = os.path.join(small_nm_1, small_nm_3)
                    label_thumb = os.path.join(small_nm_1, small_nm_4)
                    logger.info(new_small_thumb)
                    if os.path.exists(new_small_thumb):
                        os.remove(new_small_thumb)
                    if os.path.exists(picn_new):
                        os.remove(picn_new)
                    if os.path.exists(small_thumb):
                        os.remove(small_thumb)
                    if os.path.exists(label_thumb):
                        os.remove(label_thumb)
                        
                interval = (interval + 10)
                ui.set_parameters_value(inter=interval)
                inter = str(interval)+'s'
                path = str(path)
                
                if site == "PlayLists":
                    rfr_url = str((ui.epn_arr_list[num]).split('	')[2])
                    rfr_url1 = rfr_url.replace('"', '')
                    rfr_url1 = rfr_url1.replace("'", '')
                    logger.info(rfr_url1)
                    if rfr_url1.lower().startswith('http'):
                        rfr = "--referrer="+rfr_url
                        logger.info(rfr)
                        subprocess.call([
                            "mpv", rfr, "--vo=image", "--no-sub", "--ytdl=no", "--quiet", "--no-audio", 
                            "--vo-image-outdir="+TMPDIR, "-sid=no", "-aid=no", 
                            "--start="+str(interval)+"%", "--frames=1", 
                            path])
                        tmp_img = os.path.join(TMPDIR, '00000001.jpg')
                        if os.path.exists(tmp_img):
                            shutil.copy(tmp_img, picn)
                            os.remove(tmp_img)
                    else:
                        path1 = path.replace('"', '')
                        if path1.startswith('http'):
                            subprocess.call([
                                "mpv", "--vo=image", "--no-sub", "--ytdl=yes", "--quiet", "--no-audio", 
                                "--vo-image-outdir="+TMPDIR, "-sid=no", "-aid=no", 
                                "--start="+str(interval)+"%", "--frames=1", 
                                path])
                            tmp_img = os.path.join(TMPDIR, '00000001.jpg')
                            if os.path.exists(tmp_img):
                                tmp_new_img = ui.change_aspect_only(tmp_img)
                                shutil.copy(tmp_new_img, picn)
                                os.remove(tmp_img)
                        else:
                            ui.generate_thumbnail_method(picn, inter, path)
                else:
                    ui.generate_thumbnail_method(picn, inter, path)
                picn = ui.image_fit_option(picn, '', fit_size=6, widget_size=(int(width), int(height)))
                img = QtGui.QPixmap(picn, "1")			
                if thumbnail_grid:
                    q1="ui.label_epn_"+str(num)+".setPixmap(img)"
                else:
                    q1="ui.label.setPixmap(img)"
                exec (q1)
                if interval == 100:
                    interval = 10
                    ui.set_parameters_value(inter=interval)
                
            else:
                width = ui.label.width()
                height = ui.label.height()
                print("num="+str(num))
                ui.list2.setCurrentRow(num)
                print(memory_num_arr)
                if memory_num_arr:
                    t_num = memory_num_arr.pop()
                else:
                    t_num = -1
            
                if t_num != num:
                    #ui.epnfound_return()
                    path_final_Url = ui.epn_return(num)
                    interval = 10
                else:
                    path_final_Url = ui.get_parameters_value(path_final='path_final_Url')['path_final_Url']
                memory_num_arr.append(num)
                ui.set_parameters_value(inter=interval, path_final=path_final_Url,
                                        memory_num=memory_num_arr)
                if '	' in ui.epn_arr_list[num]:
                    a = (((ui.epn_arr_list[num])).split('	')[0])
                else:			
                    a = ((ui.epn_arr_list[num]))
                a = a.replace('#', '', 1)
                if a.startswith(ui.check_symbol):
                    a = a[1:]
                a = a.strip()
                if os.name != 'posix':
                    a = ui.replace_special_characters(a)
                if site.lower() == 'myserver':
                    picnD = os.path.join(home, 'thumbnails', 'MyServer', name)
                else:
                    picnD = os.path.join(home, 'thumbnails', name)
                if not os.path.exists(picnD):
                    os.makedirs(picnD)
                picn = picn_new = os.path.join(picnD, a+'.jpg')
                if os.path.exists(picn_new):
                    small_nm_1, new_title = os.path.split(picn_new)
                    small_nm_2 = '128px.'+new_title
                    small_nm_3 = '480px.'+new_title
                    new_small_thumb = os.path.join(small_nm_1, small_nm_2)
                    small_thumb = os.path.join(small_nm_1, small_nm_3)
                    logger.info(new_small_thumb)
                    if os.path.exists(new_small_thumb):
                        os.remove(new_small_thumb)
                    if os.path.exists(picn_new):
                        os.remove(picn_new)
                    if os.path.exists(small_thumb):
                        os.remove(small_thumb)
                interval = (interval + 10)
                ui.set_parameters_value(inter=interval)
                inter = str(interval)+'s'
                path_final_Url = str(path_final_Url)
                path_final_Url = path_final_Url.replace('"', '')
                ui.set_parameters_value(path_final=path_final_Url)
                if not path_final_Url.startswith('http'):
                    path_final_Url = '"'+path_final_Url+'"'
                subprocess.call(
                    ["mpv", "--vo=image", "--no-sub", "--ytdl=no", "--quiet", "--no-audio", 
                    "--vo-image-outdir="+TMPDIR, "-aid=no", "-sid=no", 
                    "--start="+str(interval)+"%", "--frames=1", 
                    path_final_Url])
                tmp_img = os.path.join(TMPDIR, '00000001.jpg')
                if os.path.exists(tmp_img):
                    tmp_new_img = ui.change_aspect_only(tmp_img)
                    shutil.copy(tmp_new_img, picn)
                    os.remove(tmp_img)
                print(width, height)
                img = QtGui.QPixmap(picn, "1")
                if thumbnail_grid:
                    q1="ui.label_epn_"+str(num)+".setPixmap(img)"
                else:
                    q1="ui.label.setPixmap(img)"
                exec (q1)
                if interval == 100:
                    interval = 10
                    ui.set_parameters_value(inter=interval)


class TitleThumbnailWidget(QtWidgets.QLabel):

    def __init(self, parent):
        QLabel.__init__(self, parent)

    def setup_globals(self, uiwidget, home_dir, tmp, logr):
        global ui, home, TMPDIR, logger
        ui = uiwidget
        home = home_dir
        TMPDIR = tmp
        logger = logr

    def mouseReleaseEvent(self, ev):
        t=str(self.objectName())
        t = re.sub('label_', '', t)
        count = len(ui.original_path_name)
        #num = (int(t) % count) + 1
        num = int(t)
        ui.label_search.clear()
        logger.info('\nnum={0}:t={1}\n'.format(num, t))
        if '\t' in ui.original_path_name[num]:
            name = ui.original_path_name[num].split('\t')[0]
        else:
            name = ui.original_path_name[num]
        logger.info(name)
        ui.list1.setCurrentRow(num)
        ui.labelFrame2.setText(ui.list1.currentItem().text())
        ui.btn10.clear()
        ui.btn10.addItem(_fromUtf8(""))
        ui.btn10.setItemText(0, _translate("MainWindow", name, None))
        ui.listfound()
        ui.list2.setCurrentRow(0)
        curR = 0
        ui.set_parameters_value(curRow=curR)
        time.sleep(0.01)
        if not ui.lock_process:
            ui.gridLayout.addWidget(ui.tab_6, 0, 1, 1, 1)
            #ui.thumbnailHide('ExtendedQLabel')
            ui.IconViewEpn()
            if not ui.scrollArea1.isHidden():
                ui.scrollArea1.setFocus()

    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        self.setFocus()
    """
    def contextMenuEvent(self, event):
        global name, tmp_name, opt, list1_items, curR, nxtImg_cnt

        t=str(self.objectName())
        t = re.sub('label_', '', t)
        num = int(t)
        try:
            name = tmp_name[num]
        except:
            name = tmp_name[num%len(tmp_name)]
        logger.info(name)
        menu = QtWidgets.QMenu(self)
        rmPoster = menu.addAction("Remove Poster")
        adPoster = menu.addAction("Find Image")
        rset = menu.addAction("Reset Counter")
        adImage = menu.addAction("Replace Image")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == rmPoster:
            t=str(self.objectName())
            p1 = "ui."+t+".clear()"
            exec (p1)
        elif action == adPoster:
            if site == "SubbedAnime" and base_url == 15:
                nam = re.sub('[0-9]*', '', name)
            else:
                nam = name
            url = "https://www.google.co.in/search?q="+nam+"anime&tbm=isch"
            logger.info(url)
            content = ccurl(url)
            n = re.findall('imgurl=[^"]*.jpg', content)
            src= re.sub('imgurl=', '', n[nxtImg_cnt])
            picn = os.path.join(TMPDIR, name+'.jpg')
            if os.path.isfile(picn):
                os.remove(picn)
            subprocess.call(["curl", "-A", hdr, '--max-filesize', "-L", "-o", picn, src])
            t=str(self.objectName())
            img = QtGui.QPixmap(picn, "1")
            q1="ui."+t+".setPixmap(img)"
            t=str(self.objectName())
            exec (q1)
            nxtImg_cnt = nxtImg_cnt+1
        elif action == rset:
            nxtImg_cnt = 0
        elif action == adImage:
            ui.copyImg()
    """
