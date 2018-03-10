import os
import re
from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets
from player_functions import ccurl, open_files

class PlayerWidget(QtWidgets.QWidget):

    def __init__(self, parent, ui=None, logr=None, tmp=None):
        super(PlayerWidget, self).__init__(parent)
        global MainWindow, logger, TMPDIR, screen_width, screen_height
        self.cycle_pause = 0
        self.ui = ui
        MainWindow = parent
        logger = logr
        TMPDIR = tmp
        self.mpvplayer = None
        self.player_val = None
        self.ui.total_seek = 0
        self.dblclk = False
        self.setAcceptDrops(True)
        self.arrow_timer = QtCore.QTimer()
        self.arrow_timer.timeout.connect(self.arrow_hide)
        self.arrow_timer.setSingleShot(True)

        self.mplayer_OsdTimer = QtCore.QTimer()
        self.mplayer_OsdTimer.timeout.connect(self.osd_hide)
        self.mplayer_OsdTimer.setSingleShot(True)

        self.seek_timer = QtCore.QTimer()
        self.seek_timer.timeout.connect(self.seek_mplayer)
        self.seek_timer.setSingleShot(True)
        self.mplayer_aspect_msg = False
        
        screen_width = self.ui.screen_size[0]
        screen_height = self.ui.screen_size[1]
        self.custom_keys = {}
        self.event_dict = {'ctrl':False, 'alt':False, 'shift':False}
        self.key_map = KeyBoardShortcuts(ui, self)
        self.mpv_default = self.key_map.get_default_keys()
        self.mpv_custom, self.input_conf_list = self.key_map.get_custom_keys(self.ui.mpv_input_conf)
        self.custom_keys, _ = self.key_map.get_custom_keys(self.ui.custom_key_file)
        self.function_map = self.key_map.function_map()
        self.non_alphanumeric_keys = self.key_map.non_alphanumeric_keys()
        self.alphanumeric_keys = self.key_map.alphanumeric_keys()
        if self.custom_keys:
            self.mpv_default = self.custom_keys.copy()
        self.shift_keys = [
            '?', '>', '<', '"', ':', '}', '{', '|', '+', '_', 'sharp',
            ')', '(', '*', '&', '^', '%', '$', '#', '#', '@', '!', '~'
            ]
    
    def dragEnterEvent(self, event):
        data = event.mimeData()
        if data.hasUrls():
            event.accept()
        else:
            event.ignore()
        
        
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for i in urls:
            i = i.toString()
            logger.debug(i)
            ext = None
            if '.' in i:
                ext = i.split('.')[-1]
            ok = False
            if ext:
                ext = ext.lower()
                if ext in ['srt', 'ass', 'vtt']:
                    self.load_external_sub(mode='drop', subtitle=i)
                    logger.debug(i)
                    ok = True
            if not ok:
                logger.debug(i)
                if i.startswith('file:///') or i.startswith('http') or i.startswith('magnet:'):
                    if os.name == 'posix':
                        i = i.replace('file://', '', 1)
                    else:
                        i = i.replace('file:///', '', 1)
                    self.ui.watch_external_video('{}'.format(i), start_now=True)
    
    def set_mpvplayer(self, player=None, mpvplayer=None):
        if mpvplayer:
            self.mpvplayer = mpvplayer
        else:
            self.mpvplayer = self.ui.mpvplayer_val
        if player:
            self.player_val = player
        else:
            self.player_val = self.ui.player_val
        
    def seek_mplayer(self):
        if self.player_val == "mplayer":
            t = bytes('\n'+"seek " + str(self.ui.total_seek)+'\n', 'utf-8')
            self.mpvplayer.write(t)
            self.ui.total_seek = 0

    def osd_hide(self):
        pass
        """
        if self.player_val == 'mplayer':
            self.mpvplayer.write(b'\n osd 0 \n')
        else:
            self.mpvplayer.write(b'\n set osd-level 0 \n')
        """
        
    def arrow_hide(self):
        if self.player_val == "mplayer" or self.player_val == "mpv":
            if self.ui.frame_extra_toolbar.isHidden() and self.ui.list2.isHidden():
                self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                self.setFocus()
                logger.debug("arrow hide")
            elif self.hasFocus():
                self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                logger.debug('player has focus')
            else:
                logger.debug('player not focussed')

    def frameShowHide(self):
        if MainWindow.isFullScreen() and self.ui.tab_6.isHidden():
            if self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
                self.ui.frame_timer.start(2000)
            else:
                self.ui.frame_timer.stop()
                self.ui.frame_timer.start(2000)
    
    def check_double_click(self):
        if not self.dblclk:
            if self.mpvplayer.processId() > 0:
                self.ui.playerPlayPause()
        self.dblclk = False
                
    def mouseReleaseEvent(self, event):
        if not self.dblclk:
            self.dblclk = False
            QtCore.QTimer.singleShot(500, self.check_double_click)
        for i in self.event_dict:
            self.event_dict[i] = False
        """
        if event.button() == QtCore.Qt.LeftButton and not self.dblclk:
            if self.mpvplayer.processId() > 0:
                logger.debug('{0}:{1}'.format(event.type(), 'left-click'))
                if self.player_val == 'mplayer':
                    self.mpvplayer.write(b'\n pausing_toggle osd_show_progression \n')
                elif self.player_val == 'mpv':
                    self.mpvplayer.write(b'\n cycle pause \n')
        """
        
    def mouseDoubleClickEvent(self, event):
        self.dblclk = True
        if not self.ui.force_fs:
            self.player_fs()
        else:
            wd = self.width()
            ht = self.height()
            if wd == screen_width and ht == screen_height:
                self.player_fs()
            else:
                self.player_fs(mode='fs')
        for i in self.event_dict:
            self.event_dict[i] = False
        
    def mouseMoveEvent(self, event):
        self.setFocus()
        pos = event.pos()
        if self.ui.auto_hide_dock and not self.ui.dockWidget_3.isHidden():
            self.ui.dockWidget_3.hide()
        if not self.ui.float_window.isHidden() and self.ui.new_tray_widget.remove_toolbar:
            if self.ui.float_timer.isActive():
                self.ui.float_timer.stop()
            if self.ui.new_tray_widget.cover_mode.text() == self.ui.player_buttons['up']:
                wid_height = int(self.ui.float_window.height()/3)
            else:
                wid_height = int(self.ui.float_window.height())
            self.ui.new_tray_widget.setMaximumHeight(wid_height)
            self.ui.new_tray_widget.show()
            self.ui.float_timer.start(1000)
        if (self.player_val == "mplayer" or self.player_val == "mpv"):
            if self.arrow_timer.isActive():
                self.arrow_timer.stop()
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            self.arrow_timer.start(2000)
        if MainWindow.isFullScreen():
            ht = self.height()
            if pos.y() <= ht and pos.y() > ht - 5 and self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
                self.ui.frame1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            elif pos.y() <= ht-32 and not self.ui.frame1.isHidden():
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site != "Music" and self.ui.tab_6.isHidden()
                        and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                    self.ui.frame1.hide()
                    self.ui.gridLayout.setSpacing(5)

    def ccurl_head(self, url, rfr_url):
        if rfr_url:
            content = ccurl(url+'#'+'-Ie'+'#'+rfr_url)
        else:
            content = ccurl(url+'#'+'-I')
        return content

    def url_resolve_size(self, url, rfr_url):
        m = []
        content = self.ccurl_head(url, rfr_url)
        n = content.split('\n')
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
                k = k+1
            else:
                t = (i, '')
                m.append(t)
        d = dict(m)
        print(d)
        result = int(int(d['Content-Length'])/(1024*1024))
        return result

    def set_slider_val(self, val):
        t = self.ui.slider.value()
        t = t+val
        self.ui.slider.setValue(t)
    
    def player_fs(self, mode=None):
        if not self.ui.idw or self.ui.idw == str(int(self.winId())):
            if not MainWindow.isHidden():
                if not MainWindow.isFullScreen() or mode == 'fs':
                    if os.name == 'nt' and self.ui.web_review_browser_started:
                        self.ui.detach_fullscreen = True
                        MainWindow.hide()
                        self.ui.tray_widget.right_menu._detach_video()
                        if not self.ui.float_window.isFullScreen():
                            self.ui.float_window.showFullScreen()
                            self.ui.tab_5.setFocus()
                    else:
                        if not self.ui.tab_6.isHidden():
                            self.ui.fullscreen_mode = 1
                        elif not self.ui.float_window.isHidden():
                            self.ui.fullscreen_mode = 2
                        else: 
                            self.ui.fullscreen_mode = 0
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.superGridLayout.setSpacing(0)
                        self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.text.hide()
                        self.ui.label.hide()
                        self.ui.frame1.hide()
                        self.ui.tab_6.hide()
                        self.ui.goto_epn.hide()
                        if self.ui.wget.processId() > 0 or self.ui.video_local_stream:
                            self.ui.progress.hide()
                            if not self.ui.torrent_frame.isHidden():
                                self.ui.torrent_frame.hide()
                        self.ui.list2.hide()
                        self.ui.frame_extra_toolbar.hide()
                        self.ui.frame_extra_toolbar.playlist_hide = False
                        self.ui.list6.hide()
                        self.ui.list1.hide()
                        self.ui.frame.hide()
                        self.ui.dockWidget_3.hide()
                        if self.ui.orientation_dock == 'right':
                            self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 1, 1, 1)
                        self.show()
                        self.setFocus()
                        if not self.ui.tab_2.isHidden():
                            self.ui.tab_2.hide()
                        if (self.player_val == "mplayer" or self.player_val == "mpv"):
                            MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                        MainWindow.showFullScreen()
                        self.ui.fullscreen_video = True
                else:
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.list2.show()
                    self.ui.btn20.show()
                    if self.ui.wget.processId() > 0 or self.ui.video_local_stream:
                        self.ui.progress.show()
                    self.ui.frame1.show()
                    if self.player_val == "mplayer" or self.player_val == "mpv":
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    if not self.ui.force_fs:
                        MainWindow.showNormal()
                        MainWindow.showMaximized()
                    param_dict = self.ui.get_parameters_value(tl='total_till')
                    total_till = param_dict['total_till']
                    if total_till != 0 or self.ui.fullscreen_mode == 1:
                        self.ui.tab_6.show()
                        self.ui.list2.hide()
                        self.ui.frame_extra_toolbar.hide()
                        self.ui.frame_extra_toolbar.playlist_hide = False
                        self.ui.goto_epn.hide()
                    if self.ui.btn1.currentText().lower() == 'youtube':
                        self.ui.list2.hide()
                        self.ui.frame_extra_toolbar.hide()
                        self.ui.frame_extra_toolbar.playlist_hide = False
                        self.ui.goto_epn.hide()
                        self.ui.tab_2.show()
                    if self.ui.orientation_dock == 'right':
                        self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 5, 2, 1)
                    self.ui.fullscreen_video = False
            else:
                if self.ui.detach_fullscreen:
                    self.ui.detach_fullscreen = False
                    self.ui.tray_widget.right_menu._detach_video()
                    self.ui.tab_5.setFocus()
                else:
                    if not self.ui.float_window.isHidden():
                        if not self.ui.float_window.isFullScreen():
                            self.ui.float_window.showFullScreen()
                        else:
                            self.ui.float_window.showNormal()
        else:
            self.ui.tab_6_size_indicator.append(self.ui.tab_6.width())
            param_dict = self.ui.get_parameters_value(
                icn='iconv_r_indicator', i='iconv_r',
                cl='cur_label_num')
            iconv_r_indicator = param_dict['iconv_r_indicator']
            iconv_r = param_dict['iconv_r']
            cur_label_num = self.ui.cur_row
            if not MainWindow.isHidden():
                if self.ui.video_mode_index in [5,6,7]:
                    pass
                else:
                    if iconv_r_indicator:
                        iconv_r = iconv_r_indicator[0]
                    self.ui.set_parameters_value(iconv=iconv_r)
                    widget = eval("self.ui.label_epn_"+str(cur_label_num))
                    col = (cur_label_num%iconv_r)
                    row = 2*int(cur_label_num/iconv_r)
                    new_pos = (row, col)
                    print(new_pos)
                    if not MainWindow.isFullScreen():
                        cur_label = cur_label_num
                        index = self.ui.gridLayout2.indexOf(widget)
                        logger.debug(index)
                        if index >= 0:
                            self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                            self.ui.tab_6.hide()
                            self.ui.gridLayout.addWidget(widget, 0, 1, 1, 1)
                            widget.setMaximumSize(QtCore.QSize(screen_width, screen_height))
                            self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                            self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout1.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout2.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout.setSpacing(0)
                            self.ui.gridLayout1.setSpacing(0)
                            self.ui.gridLayout2.setSpacing(0)
                            self.ui.superGridLayout.setSpacing(0)
                            if self.ui.orientation_dock == 'right':
                                self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 1, 1, 1)
                            MainWindow.showFullScreen()
                            self.ui.fullscreen_video = True
                    else:
                        w = float((self.ui.tab_6.width()-60)/iconv_r)
                        h = int(w/self.ui.image_aspect_allowed)
                        width=str(int(w))
                        height=str(int(h))
                        r = self.ui.current_thumbnail_position[0]
                        c = self.ui.current_thumbnail_position[1]
                        cur_label = cur_label_num
                        self.ui.gridLayout2.addWidget(widget, r, c, 1, 1, QtCore.Qt.AlignCenter)
                        QtWidgets.QApplication.processEvents()
                        MainWindow.showNormal()
                        MainWindow.showMaximized()
                        yy = widget.y()
                        self.ui.scrollArea1.verticalScrollBar().setValue(yy)
                        QtWidgets.QApplication.processEvents()
                        self.ui.frame1.show()
                        self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                        self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout1.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout2.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout.setSpacing(5)
                        self.ui.gridLayout1.setSpacing(5)
                        self.ui.gridLayout2.setSpacing(5)
                        self.ui.superGridLayout.setSpacing(5)
                        self.ui.tab_6.show()
                        if self.ui.orientation_dock == 'right':
                            self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 5, 2, 1)
                        QtWidgets.QApplication.processEvents()
                        widget.setFocus()
                        QtCore.QTimer.singleShot(1000, self.ui.update_thumbnail_position)
                        self.ui.fullscreen_video = False
            else:
                if not self.ui.float_window.isHidden():
                    if not self.ui.float_window.isFullScreen():
                        widget = eval("self.ui.label_epn_"+str(cur_label_num))
                        index = self.ui.gridLayout2.indexOf(widget)
                        print(index, '--index--')
                        self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                        self.ui.float_window.showFullScreen()
                    else:
                        self.ui.float_window.showNormal()

    def player_quit(self, msg=None):
        self.ui.player_stop.clicked.emit()
        
    def load_external_sub(self, mode=None, subtitle=None):
        if mode is None:
            fname = QtWidgets.QFileDialog.getOpenFileNames(
                    MainWindow, 'Select Subtitle file', self.ui.last_dir)
            if fname:
                logger.info(fname)
                if fname[0]:
                    self.ui.last_dir, file_choose = os.path.split(fname[0][0])
                    title_sub = fname[0][0]
                    if self.player_val == "mplayer":
                        txt = '\nsub_load '+'"'+title_sub+'"\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer.write(txt_b)
                    else:
                        txt = '\nsub_add '+'"'+title_sub+'" select\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer.write(txt_b)
            self.ui.acquire_subtitle_lock = False
        elif mode == 'network':
            site = self.ui.get_parameters_value(st='site')['site']
            if site.lower() == 'myserver':
                title_sub = self.ui.final_playing_url + '.subtitle'
                if self.player_val == "mplayer":
                    txt = '\nsub_load '+'"'+title_sub+'"\n'
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    self.mpvplayer.write(txt_b)
                else:
                    txt = '\nsub_add '+'"'+title_sub+'" select\n'
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    self.mpvplayer.write(txt_b)
            else:
                logger.warn('Not Allowed')
        elif mode == 'drop':
            title_sub = subtitle
            logger.debug(title_sub)
            if self.player_val == "mplayer":
                txt = '\nsub_load '+'"'+title_sub+'"\n'
                txt_b = bytes(txt, 'utf-8')
                logger.info("{0} - {1}".format(txt_b, txt))
                self.mpvplayer.write(txt_b)
            else:
                txt = '\nsub_add '+'"'+title_sub+'" select\n'
                txt_b = bytes(txt, 'utf-8')
                logger.info("{0} - {1}".format(txt_b, txt))
                self.mpvplayer.write(txt_b)
    
    def keyReleaseEvent(self, event):
        if event.modifiers() == QtCore.Qt.ControlModifier or event.key() == QtCore.Qt.Key_Control:
            self.event_dict['ctrl'] = False
            self.event_dict['alt'] = False
            self.event_dict['shift'] = False
        elif event.modifiers() == QtCore.Qt.AltModifier or event.key() == QtCore.Qt.Key_Alt:
            self.event_dict['alt'] = False
            self.event_dict['shift'] = False
        elif event.modifiers() == QtCore.Qt.ShiftModifier or event.key() == QtCore.Qt.Key_Shift:
            self.event_dict['shift'] = False
        logger.debug('release'.format(event.key()))
        
    def keyPressEvent(self, event):
        if self.player_val.lower() == 'mpv':
            key = None
            modifier = None
            no_modifier = False
            logger.debug('press {}'.format(event.key()))
            event_text = event.text()
            if event.modifiers() == QtCore.Qt.ControlModifier or self.event_dict['ctrl']:
                modifier = 'ctrl+'
                if event.key() == QtCore.Qt.Key_Alt:
                    self.event_dict['alt'] = True
                if event.key() == QtCore.Qt.Key_Shift:
                    self.event_dict['shift'] = True
                if self.event_dict['ctrl'] and self.event_dict['alt']:
                    modifier = 'ctrl+alt+'
                if event.key() in self.alphanumeric_keys:
                    keysym = self.alphanumeric_keys.get(event.key())
                    if self.event_dict['shift']:
                        keysym = keysym.upper()
                    key = modifier + keysym
                elif event.key() in self.non_alphanumeric_keys:
                    key = self.non_alphanumeric_keys.get(event.key())
                    if self.event_dict['shift'] and key not in self.shift_keys:
                        modifier = modifier + 'shift+'
                    key = modifier + key
                else:
                    self.event_dict['ctrl'] = True
            elif event.modifiers() == QtCore.Qt.AltModifier or self.event_dict['alt']:
                self.event_dict['ctrl'] = False
                if event.key() == QtCore.Qt.Key_Shift:
                    self.event_dict['shift'] = True
                if event.key() in self.alphanumeric_keys:
                    keysym = self.alphanumeric_keys.get(event.key())
                    if self.event_dict['shift']:
                        keysym = keysym.upper()
                    key = 'alt+'+ keysym
                elif event.key() in self.non_alphanumeric_keys:
                    key = 'alt+' + self.non_alphanumeric_keys.get(event.key())
                else:
                    self.event_dict['alt'] = True
            elif event.modifiers() == QtCore.Qt.ShiftModifier or self.event_dict['shift']:
                self.event_dict['ctrl'] = False
                self.event_dict['alt'] = False
                if event.text().isalnum():
                    key = event.text().upper()
                elif event.key() in self.non_alphanumeric_keys:
                    key = self.non_alphanumeric_keys.get(event.key())
                    if key not in self.shift_keys:
                        key = 'shift+' + key
                else:
                    self.event_dict['shift'] = True
            elif event.text().isalnum():
                key = event.text()
                no_modifier = True
            else:
                key = self.non_alphanumeric_keys.get(event.key())
                no_modifier = True
            logger.debug('modifier: {} key: {}'.format(modifier, key))
            if key is not None:
                if key == 'esc':
                    if not self.ui.float_window.isHidden():
                        if self.ui.new_tray_widget.isHidden():
                            self.ui.new_tray_widget.show()
                        else:
                            self.ui.new_tray_widget.hide()
                command = self.mpv_default.get(key)
                logger.debug(command)
                if not command:
                    command = self.mpv_custom.get(key)
                logger.debug(command)
                if command:
                    command_list = command.split('::')
                    for part in command_list:
                        if part in self.function_map:
                            myfunction = self.function_map.get(part)
                            myfunction()
                        elif part.startswith('ignore'):
                            pass
                        elif part.startswith('add'):
                            self.add_parameter(part)
                        else:
                            cmd = '\n {} \n'.format(part)
                            command_string = bytes(cmd, 'utf-8')
                            logger.debug(command_string)
                            self.mpvplayer.write(command_string)
            if no_modifier:
                for i in self.event_dict:
                    self.event_dict[i] = False
        elif self.player_val.lower() == 'mplayer':
            self.keyPressEventOld(event)
    
    def add_parameter(self, cmd):
        if ' ' in cmd:
            cmd_list = cmd.split(' ')
            cmd_name = cmd_list[1]
            if cmd_name in ['volume', 'ao-volume']:
                self.change_volume(cmd)
            elif cmd_name in ['brightness', 'contrast', 'saturation', 'hue', 'gamma']:
                cmd_val = cmd_list[-1]
                try:
                    cmd_val_int = int(cmd_val)
                    slider = eval('self.ui.frame_extra_toolbar.{}_slider'.format(cmd_name))
                    slider.setValue(slider.value() + cmd_val_int)
                except Exception as err:
                    logger.error(err)
            else:
                cmd = '\n {} \n'.format(cmd)
                command_string = bytes(cmd, 'utf-8')
                logger.debug(command_string)
                self.mpvplayer.write(command_string)
    
    def change_aspect_ratio(self, key=None):
        if key is None:
            self.ui.mpvplayer_aspect_cycle = (self.ui.mpvplayer_aspect_cycle + 1) % 5
        else:
            self.ui.mpvplayer_aspect_cycle = int(key)
        aspect_val = self.ui.mpvplayer_aspect.get(str(self.ui.mpvplayer_aspect_cycle))
        logger.info('aspect:{0}::value:{1}'.format(self.ui.mpvplayer_aspect_cycle, aspect_val))
        if aspect_val == '-1':
            show_text_val = 'Original Aspect'
        elif aspect_val == '0':
            show_text_val = 'Aspect Ratio Disabled'
        else:
            show_text_val = aspect_val
        if self.player_val == 'mpv':
            msg = '\n set video-aspect "{0}" \n'.format(aspect_val)
            self.mpvplayer.write(bytes(msg, 'utf-8'))
            txt_osd = '\n show-text "{0}" \n'.format(show_text_val)
            self.mpvplayer.write(bytes(txt_osd, 'utf-8'))
            if self.ui.final_playing_url in self.ui.history_dict_obj:
                seek_time, acc_time, sub_id, audio_id, rem_quit, vol, asp = self.ui.history_dict_obj.get(self.ui.final_playing_url)
                asp = aspect_val
                if self.ui.video_parameters:
                    if self.ui.video_parameters[0] == self.ui.final_playing_url:
                        self.ui.video_parameters[-1] = asp
                self.ui.history_dict_obj.update(
                    {self.ui.final_playing_url:[
                        seek_time, acc_time, sub_id, audio_id,
                        rem_quit, vol, asp
                        ]
                    }
                )
    
    def change_volume(self, command):
        vol = None
        volume = False
        msg = None
        new_command = None
        if ' ' in command:
            vol_int = command.split(' ')[-1]
            if vol_int.startswith('-') or vol_int.startswith('+'):
                vol = vol_int[1:]
            else:
                vol = vol_int
            if vol.isnumeric():
                volume = True
        slider = self.ui.frame_extra_toolbar.slider_volume
        if command.startswith('add volume') and volume:
            value = slider.value() + int(vol_int)
            if self.ui.volume_type == 'ao-volume':
                msg = '\n print-text volume-print=${volume} \n'
            if value <= 100:
                slider.setValue(value)
            else:
                new_command = '\n add volume {} \n'.format(vol_int)
                msg = '\n print-text volume-print=${volume} \n'
        elif command.startswith('add ao-volume') and volume:
            slider.setValue(slider.value() + int(vol_int))
            if self.ui.volume_type == 'volume':
                msg = '\n print-text ao-volume-print=${ao-volume} \n'
        if msg:
            if new_command:
                self.mpvplayer.write(bytes(new_command, 'utf-8'))
            msg = bytes(msg, 'utf-8')
            self.mpvplayer.write(msg)
            
    def start_player_loop(self):
        self.ui.playerLoopFile(self.ui.player_loop_file)
    
    def show_hide_status_frame(self):
        if self.ui.frame1.isHidden():
            self.ui.gridLayout.setSpacing(0)
            self.ui.frame1.show()
        else:
            self.ui.gridLayout.setSpacing(5)
            self.ui.frame1.hide()
            
    def toggle_play_pause(self):
        txt = self.ui.player_play_pause.text()
        if txt == self.ui.player_buttons['play']:
            self.ui.player_play_pause.setText(self.ui.player_buttons['pause'])
        elif txt == self.ui.player_buttons['pause']:
            self.ui.player_play_pause.setText(self.ui.player_buttons['play'])
            self.ui.mplayer_pause_buffer = False
            self.ui.mplayer_nop_error_pause = False
            buffering_mplayer = "no"
            self.ui.set_parameters_value(bufm=buffering_mplayer)
        if self.ui.frame_timer.isActive:
            self.ui.frame_timer.stop()
        if self.ui.mplayer_timer.isActive():
            self.ui.mplayer_timer.stop()
        param_dict = self.ui.get_parameters_value(
            ps='pause_indicator', mpv='mpv_indicator', s='site')
        pause_indicator = param_dict['pause_indicator']
        mpv_indicator = param_dict['mpv_indicator']
        site = param_dict['site']
        if not pause_indicator:
            self.mpvplayer.write(b'\n set pause yes \n')
            if MainWindow.isFullScreen() and self.ui.fullscreen_video:
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
            pause_indicator.append("Pause")
        else:
            self.mpvplayer.write(b'\n set pause no \n')
            if MainWindow.isFullScreen():
                if (site != "Music" and self.ui.tab_6.isHidden()
                        and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                    self.ui.frame1.hide()
            pause_indicator.pop()
            if mpv_indicator:
                mpv_indicator.pop()
                cache_empty = 'no'
                self.ui.set_parameters_value(
                    cache_val=cache_empty, mpv_i=mpv_indicator)
                    
    def load_subtitle_from_file(self):
        self.load_external_sub()
    
    def load_subtitle_from_network(self):
        self.load_external_sub(mode='network')
        
    def toggle_fullscreen_mode(self):
        if not self.ui.force_fs:
            self.player_fs()
        else:
            wd = self.width()
            ht = self.height()
            if wd == screen_width and ht == screen_height:
                self.player_fs()
            else:
                self.player_fs(mode='fs')
                
    def get_next(self):
        self.ui.mpvNextEpnList()
        
    def get_previous(self):
        self.ui.mpvPrevEpnList()
        
    def quit_player(self):
        self.player_quit()
    
    def cycle_player_subtitle(self):
        self.mpvplayer.write(b'\n cycle sub \n')
        self.mpvplayer.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
        self.mpvplayer.write(b'\n show-text "${sid}" \n')
                
    def cycle_player_audio(self):
        self.mpvplayer.write(b'\n cycle audio \n')
        self.mpvplayer.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
        self.mpvplayer.write(b'\n show-text "${aid}" \n')
                
    def stop_after_current_file(self):
        self.ui.quit_really = "yes"
        msg = '"Stop After current file"'
        msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
        self.mpvplayer.write(msg_byt)
        
    def remember_and_quit(self):
        self.ui.quit_really = "yes"
        self.ui.playerStop(msg='remember quit')
            
    def keyPressEventOld(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier
                and event.key() == QtCore.Qt.Key_Right):
            self.ui.list2.setFocus()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(10)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +10 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 10
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +10 \n')
            #self.frameShowHide()
        elif event.key() == QtCore.Qt.Key_1:
            self.mpvplayer.write(b'\n add chapter -1 \n')
        elif event.key() == QtCore.Qt.Key_2:
            self.mpvplayer.write(b'\n add chapter 1 \n')
        elif event.key() == QtCore.Qt.Key_3:
            self.mpvplayer.write(b'\n cycle ass-style-override \n')
        elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_V):
            self.mpvplayer.write(b'\n cycle ass-vsfilter-aspect-compat \n')
        elif event.key() == QtCore.Qt.Key_Left:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-10)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek -10 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 10
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -10 \n')
            #self.frameShowHide()
        elif event.key() == QtCore.Qt.Key_BracketRight:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek +90 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek +90 \n')
        elif event.key() == QtCore.Qt.Key_BracketLeft:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek -5 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek -5 \n')
        elif event.key() == QtCore.Qt.Key_0:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n volume +5 \n')
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n add ao-volume +5 \n')
                self.mpvplayer.write(b'\n print-text volume-print=${ao-volume}\n')
        elif event.key() == QtCore.Qt.Key_9:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n volume -5 \n')
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n add ao-volume -5 \n')
                self.mpvplayer.write(b'\n print-text volume-print=${ao-volume}\n')
        elif event.key() == QtCore.Qt.Key_A:
            self.ui.mpvplayer_aspect_cycle = (self.ui.mpvplayer_aspect_cycle + 1) % 5
            aspect_val = self.ui.mpvplayer_aspect.get(str(self.ui.mpvplayer_aspect_cycle))
            logger.info('aspect:{0}::value:{1}'.format(self.ui.mpvplayer_aspect_cycle, aspect_val))
            if aspect_val == '-1':
                show_text_val = 'Original Aspect'
            elif aspect_val == '0':
                show_text_val = 'Aspect Ratio Disabled'
            else:
                show_text_val = aspect_val
            if self.player_val == 'mpv':
                msg = '\n set video-aspect "{0}" \n'.format(aspect_val)
                self.mpvplayer.write(bytes(msg, 'utf-8'))
                txt_osd = '\n show-text "{0}" \n'.format(show_text_val)
                self.mpvplayer.write(bytes(txt_osd, 'utf-8'))
                if self.ui.final_playing_url in self.ui.history_dict_obj:
                    seek_time, acc_time, sub_id, audio_id, rem_quit, vol, asp = self.ui.history_dict_obj.get(self.ui.final_playing_url)
                    asp = aspect_val
                    if self.ui.video_parameters:
                        if self.ui.video_parameters[0] == self.ui.final_playing_url:
                            self.ui.video_parameters[-1] = asp
                    self.ui.history_dict_obj.update(
                        {self.ui.final_playing_url:[
                            seek_time, acc_time, sub_id, audio_id,
                            rem_quit, vol, asp
                            ]
                        }
                    )
            elif self.player_val == 'mplayer':
                self.mplayer_aspect_msg = True
                if self.mpvplayer.processId() > 0:
                    if self.ui.final_playing_url in self.ui.history_dict_obj:
                        seek_time, acc_time, sub_id, audio_id, rem_quit, vol, asp = self.ui.history_dict_obj.get(self.ui.final_playing_url)
                        if self.ui.video_parameters:
                            if self.ui.video_parameters[0] == self.ui.final_playing_url:
                                self.ui.video_parameters[-1] = asp
                        self.ui.history_dict_obj.update(
                            {
                                self.ui.final_playing_url:[
                                    seek_time, acc_time, sub_id, audio_id,
                                    rem_quit, vol, asp
                                    ]
                            }
                        )
                    self.mpvplayer.kill()
        elif event.key() == QtCore.Qt.Key_N:
            self.mpvplayer.write(b'\n playlist_next \n')
        elif event.key() == QtCore.Qt.Key_L:
            #self.ui.tab_5.setFocus()
            self.ui.playerLoopFile(self.ui.player_loop_file)
        elif event.key() == QtCore.Qt.Key_End:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek 99 1 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek 100 absolute-percent \n')
        elif event.key() == QtCore.Qt.Key_P:
            if self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
            else:
                self.ui.gridLayout.setSpacing(5)
                self.ui.frame1.hide()
        elif event.key() == QtCore.Qt.Key_Space:
            txt = self.ui.player_play_pause.text()
            if txt == self.ui.player_buttons['play']:
                self.ui.player_play_pause.setText(self.ui.player_buttons['pause'])
            elif txt == self.ui.player_buttons['pause']:
                self.ui.player_play_pause.setText(self.ui.player_buttons['play'])
                self.ui.mplayer_pause_buffer = False
                self.ui.mplayer_nop_error_pause = False
                buffering_mplayer = "no"
                self.ui.set_parameters_value(bufm=buffering_mplayer)
            if self.ui.frame_timer.isActive:
                self.ui.frame_timer.stop()
            if self.ui.mplayer_timer.isActive():
                self.ui.mplayer_timer.stop()
            if self.player_val == "mplayer":
                if MainWindow.isFullScreen():
                    site = self.ui.get_parameters_value(s='site')['site']
                    if (site != "Music" and self.ui.tab_6.isHidden()
                            and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                        self.ui.frame1.hide()
                self.mpvplayer.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                param_dict = self.ui.get_parameters_value(
                    ps='pause_indicator', mpv='mpv_indicator', s='site')
                pause_indicator = param_dict['pause_indicator']
                mpv_indicator = param_dict['mpv_indicator']
                site = param_dict['site']
                if not pause_indicator:
                    self.mpvplayer.write(b'\n set pause yes \n')
                    if MainWindow.isFullScreen():
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.frame1.show()
                    pause_indicator.append("Pause")
                else:
                    self.mpvplayer.write(b'\n set pause no \n')
                    if MainWindow.isFullScreen():
                        if (site != "Music" and self.ui.tab_6.isHidden()
                                and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                            self.ui.frame1.hide()
                    pause_indicator.pop()
                    if mpv_indicator:
                        mpv_indicator.pop()
                        cache_empty = 'no'
                        self.ui.set_parameters_value(
                            cache_val=cache_empty, mpv_i=mpv_indicator)
        elif event.key() == QtCore.Qt.Key_Up:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(60)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +60 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 60
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +60 \n')
        elif event.key() == QtCore.Qt.Key_Down:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-60)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"): 
                    self.mpvplayer.write(b'\n seek -60 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 60
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -60 \n')
        elif event.key() == QtCore.Qt.Key_PageUp:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(300)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +300 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 300
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +300 \n')
        elif event.key() == QtCore.Qt.Key_PageDown:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-300)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek -300 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 300
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -300 \n')
        elif event.key() == QtCore.Qt.Key_O:
            if self.player_val == 'mplayer':
                self.mpvplayer.write(b'\n osd \n')
            else:
                self.mpvplayer.write(b'\n cycle osd-level \n')
        elif event.key() == QtCore.Qt.Key_M:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n osd_show_property_text ${filename} \n')
            else:
                self.mpvplayer.write(b'\n show-text "${filename}" \n')
        elif event.key() == QtCore.Qt.Key_I:
            if self.player_val == "mpv":
                self.mpvplayer.write(b'\n show_text ${file-size} \n')
            else:
                self.set_slider_val(-300)
                param_dict = self.ui.get_parameters_value(st='rfr_url')
                rfr_url = param_dict['rfr_url']
                logger.info(self.ui.final_playing_url)
                logger.info(rfr_url)
                if self.ui.total_file_size:
                    sz = str(self.ui.total_file_size)+' MB'
                else:
                    if (self.ui.final_playing_url.startswith('http') 
                            and self.ui.final_playing_url.endswith('.mkv')):
                        self.ui.total_file_size = self.url_resolve_size(
                            self.ui.final_playing_url, rfr_url)
                        sz = str(self.ui.total_file_size)+' MB'
                    else:
                        self.ui.total_file_size = 0
                        sz = str(0)
                t = bytes('\n'+'osd_show_text '+'"'+sz+'"'+' 4000'+'\n', 'utf-8')
                logger.info(t)
                self.mpvplayer.write(t)
        elif event.key() == QtCore.Qt.Key_E:
            if self.player_val == "mplayer" and MainWindow.isFullScreen():
                w = self.width()
                w = w + (0.05*w)
                h = self.height()
                h = h + (0.05*h)
                self.setMaximumSize(w, h)
            else:
                self.mpvplayer.write(b'\n add video-zoom +0.01 \n')
        elif event.key() == QtCore.Qt.Key_W:
            if self.player_val == "mplayer" and MainWindow.isFullScreen():
                w = self.width()
                w = w - (0.05*w)
                h = self.height()
                h = h - (0.05*h)
                self.setMaximumSize(w, h)
            else:
                self.mpvplayer.write(b'\n add video-zoom -0.01 \n')
        elif event.key() == QtCore.Qt.Key_R:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n sub_pos -1 \n')
            else:
                self.mpvplayer.write(b'\n add sub-pos -1 \n')
        elif event.key() == QtCore.Qt.Key_T:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n sub_pos +1 \n')
            else:
                self.mpvplayer.write(b'\n add sub-pos +1 \n')
        elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_J):
            #self.ui.load_external_sub()
            self.load_external_sub()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_J):
            #self.ui.load_external_sub()
            self.load_external_sub(mode='network')
        elif event.key() == QtCore.Qt.Key_J:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer.write(b'\n sub_select \n')
                self.mpvplayer.write(b'\n get_property sub \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer.write(b'\n cycle sub \n')
                self.mpvplayer.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
                self.mpvplayer.write(b'\n show-text "${sid}" \n')
        elif event.key() == QtCore.Qt.Key_K:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer.write(b'\n switch_audio \n')
                self.mpvplayer.write(b'\n get_property switch_audio \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer.write(b'\n cycle audio \n')
                self.mpvplayer.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
                self.mpvplayer.write(b'\n show-text "${aid}" \n')
        elif event.key() == QtCore.Qt.Key_F:
            if not self.ui.force_fs:
                self.player_fs()
            else:
                wd = self.width()
                ht = self.height()
                if wd == screen_width and ht == screen_height:
                    self.player_fs()
                else:
                    self.player_fs(mode='fs')
        elif event.key() == QtCore.Qt.Key_Period:
            self.ui.mpvNextEpnList()
        elif event.key() == QtCore.Qt.Key_Comma:
            self.ui.mpvPrevEpnList()
        elif (event.modifiers() == QtCore.Qt.ControlModifier
                and event.key() == QtCore.Qt.Key_Q):
            self.ui.quit_really = "yes"
            msg = '"Stop After current file"'
            msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
            self.mpvplayer.write(msg_byt)
        elif (event.modifiers() == QtCore.Qt.ShiftModifier
                and event.key() == QtCore.Qt.Key_Q):
            self.ui.quit_really = "yes"
            self.ui.playerStop(msg='remember quit')
        elif event.key() == QtCore.Qt.Key_Q:
            self.player_quit()
        #super(PlayerWidget, self).keyPressEvent(event)


class KeyBoardShortcuts:
    
    def __init__(self, uiwidget, parent):
        self.ui = uiwidget
        self.parent = parent
        
    def get_default_keys(self):
        default_key_map = OrderedDict()
        
        default_key_map['f'] = 'cycle fullscreen'
        default_key_map['.'] = 'playlist-next'
        default_key_map[','] = 'playlist-prev'
        default_key_map['q'] = 'quit'
        default_key_map['ctrl+q'] = 'stop-after-current-file'
        default_key_map['Q'] ='quit-watch-later'
        default_key_map['l'] = 'toggle-loop'
        default_key_map['p'] = 'show-hide-status-frame'
        default_key_map['space'] = 'cycle pause'
        default_key_map['a'] = 'cycle-aspect-ratio'
        default_key_map['J'] = 'load-external-subtitle'
        default_key_map['ctrl+j'] ='load-network-subtitle'
        default_key_map['j'] ='cycle sub'
        default_key_map['k'] ='cycle audio'
        
        default_key_map['right'] = 'set osd-level 1::osd-msg-bar seek +10'
        default_key_map['left'] = 'set osd-level 1::osd-msg-bar seek -10'
        default_key_map['up'] = 'set osd-level 1::osd-msg-bar seek +60'
        default_key_map['down'] = 'set osd-level 1::osd-msg-bar seek -60'
        default_key_map['pgup'] = 'set osd-level 1::osd-msg-bar seek +300'
        default_key_map['pgdwn'] = 'set osd-level 1::osd-msg-bar seek -300'
        default_key_map[']'] = 'osd-msg-bar seek +90'
        default_key_map['['] = 'osd-msg-bar seek -5'
        default_key_map['R'] = 'vf add flip'
        
        default_key_map['0'] = 'add ao-volume +5'
        default_key_map['9'] = 'add ao-volume -5'
        default_key_map['$'] = 'cycle ass-style-override'
        default_key_map['V'] ='cycle ass-vsfilter-aspect-compat'
        default_key_map['v'] = 'cycle sub-visibility'
        
        default_key_map['end'] = 'osd-msg-bar seek 100 absolute-percent'
        default_key_map['o'] = 'cycle osd-level'
        default_key_map['i'] = 'show_text ${file-size}'
        default_key_map['e'] = 'add video-zoom +0.01'
        default_key_map['w'] = 'add video-zoom -0.01'
        default_key_map['r'] = 'add sub-pos -1'
        default_key_map['t'] = 'add sub-pos +1'
        default_key_map['M'] = 'osd_show_property_text ${filename}'
        
        default_key_map['shift+right'] = 'no-osd seek  1 exact'
        default_key_map['shift+left'] = 'no-osd seek -1 exact'
        default_key_map['shift+up'] = 'no-osd seek  5 exact'
        default_key_map['shift+down'] = 'no-osd seek -5 exact'
        
        default_key_map['ctrl+left'] = 'no-osd sub-seek -1'
        default_key_map['ctrl+right'] = 'no-osd sub-seek  1'
        default_key_map['{'] = 'multiply speed 0.5'
        default_key_map['}'] = 'multiply speed 2.0'
        default_key_map['bs'] = 'set speed 1.0'
        default_key_map['I'] = 'script-binding stats/display-stats-toggle'
        default_key_map['z'] = 'add sub-delay -0.1'
        default_key_map['x'] = 'add sub-delay +0.1'
        default_key_map['ctrl++'] = 'add audio-delay 0.100'
        default_key_map['ctrl+-'] = 'add audio-delay -0.100'
        default_key_map['m'] = 'cycle mute'
        default_key_map['d'] = 'cycle deinterlace'
        default_key_map['u'] = 'cycle-values sub-ass-override "force" "no"'
        default_key_map['sharp'] = 'cycle audio'
        default_key_map['_'] = 'cycle video'
        default_key_map['T'] = 'cycle ontop'
        default_key_map['s'] = 'async screenshot'
        default_key_map['S'] = 'async screenshot video'
        default_key_map['ctrl+s'] = 'async screenshot window'
        default_key_map['alt+s'] = 'screenshot each-frame'
        default_key_map['!'] = 'add chapter -1'
        default_key_map['@'] = 'add chapter 1'
        default_key_map['1'] = 'add contrast -1'
        default_key_map['2'] = 'add contrast 1'
        default_key_map['3'] = 'add brightness -1'
        default_key_map['4'] = 'add brightness 1'
        default_key_map['5'] = 'add gamma -1'
        default_key_map['6'] = 'add gamma 1'
        default_key_map['7'] = 'add saturation -1'
        default_key_map['8'] = 'add saturation 1'
            
        return default_key_map
        
    def get_custom_keys(self, input_conf):
        custom_key_map = OrderedDict()
        lines_arr = []
        if os.path.isfile(input_conf):
            lines = open_files(input_conf, True)
            for i in lines:
                i = i.strip()
                lines_arr.append(i)
                if i and not i.startswith('#'):
                    if ' ' in i:
                        lst = i.split(' ', 1)
                        key = lst[0]
                        command = lst[1]
                        command = re.sub('#[^\n]*', '', command)
                        command = command.strip()
                        if key.isalnum() and len(key) == 1:
                            custom_key_map.update({key:command})
                        else:
                            custom_key_map.update({key.lower():command})
        return custom_key_map, lines_arr
                    
    def function_map(self):
        func_map = {
            'cycle-aspect-ratio': self.parent.change_aspect_ratio,
            'toggle-loop': self.parent.start_player_loop,
            'show-hide-status-frame':self.parent.show_hide_status_frame,
            'cycle pause':self.parent.toggle_play_pause,
            'load-external-subtitle':self.parent.load_subtitle_from_file,
            'load-network-subtitle':self.parent.load_subtitle_from_network,
            'cycle fullscreen':self.parent.toggle_fullscreen_mode,
            'playlist-next':self.parent.get_next,
            'playlist-prev':self.parent.get_previous,
            'quit':self.parent.quit_player,
            'stop-after-current-file':self.parent.stop_after_current_file,
            'quit-watch-later':self.parent.remember_and_quit,
            'cycle sub':self.parent.cycle_player_subtitle,
            'cycle audio':self.parent.cycle_player_audio
        }
        return func_map
    
    def non_alphanumeric_keys(self):
        non_alphanumeric = {
            QtCore.Qt.Key_BracketLeft : '[',
            QtCore.Qt.Key_BracketRight: ']',
            QtCore.Qt.Key_BraceLeft: '{',
            QtCore.Qt.Key_BraceRight: '}',
            QtCore.Qt.Key_ParenLeft: '(',
            QtCore.Qt.Key_ParenRight: ')',
            QtCore.Qt.Key_Period: '.',
            QtCore.Qt.Key_Comma: ',',
            QtCore.Qt.Key_PageUp: 'pgup',
            QtCore.Qt.Key_PageDown: 'pgdwn',
            QtCore.Qt.Key_Left: 'left',
            QtCore.Qt.Key_Right: 'right',
            QtCore.Qt.Key_Up: 'up',
            QtCore.Qt.Key_Down: 'down',
            QtCore.Qt.Key_End: 'end',
            QtCore.Qt.Key_Return: 'enter',
            QtCore.Qt.Key_Space: 'space',
            QtCore.Qt.Key_Home: 'home',
            QtCore.Qt.Key_Backspace: 'bs',
            QtCore.Qt.Key_Tab: 'tab',
            QtCore.Qt.Key_Backtab: 'backtab',
            QtCore.Qt.Key_Escape: 'esc',
            QtCore.Qt.Key_Delete: 'del',
            QtCore.Qt.Key_Insert: 'ins',
            QtCore.Qt.Key_F1: 'f1',
            QtCore.Qt.Key_F2: 'f2',
            QtCore.Qt.Key_F3: 'f3',
            QtCore.Qt.Key_F4: 'f4',
            QtCore.Qt.Key_F5: 'f5',
            QtCore.Qt.Key_F6: 'f6',
            QtCore.Qt.Key_F7: 'f7',
            QtCore.Qt.Key_F8: 'f8',
            QtCore.Qt.Key_F9: 'f9',
            QtCore.Qt.Key_F10: 'f10',
            QtCore.Qt.Key_F11: 'f11',
            QtCore.Qt.Key_F12: 'f12',
            QtCore.Qt.Key_Exclam: '!',
            QtCore.Qt.Key_QuoteDbl: '""',
            QtCore.Qt.Key_NumberSign: 'sharp',
            QtCore.Qt.Key_Dollar: '$',
            QtCore.Qt.Key_Ampersand: '&',
            QtCore.Qt.Key_Apostrophe: "'",
            QtCore.Qt.Key_Asterisk: '*',
            QtCore.Qt.Key_Minus: '-',
            QtCore.Qt.Key_Plus: '+',
            QtCore.Qt.Key_Slash: '/',
            QtCore.Qt.Key_Colon: ':',
            QtCore.Qt.Key_Semicolon: ';',
            QtCore.Qt.Key_Less: '<',
            QtCore.Qt.Key_Equal: '=',
            QtCore.Qt.Key_Greater: '>',
            QtCore.Qt.Key_Question: '?',
            QtCore.Qt.Key_At: '@',
            QtCore.Qt.Key_Backslash: '\\',
            QtCore.Qt.Key_Underscore: '_',
            QtCore.Qt.Key_QuoteLeft: '`',
            QtCore.Qt.Key_cent: '%',
            QtCore.Qt.Key_Bar: '|'
        }
        return non_alphanumeric
    
    def alphanumeric_keys(self):
        a = ord('a')
        key_dict = {}
        for i in range(a, a+26):
            key = 'QtCore.Qt.Key_{}'.format(chr(i).upper())
            key_dict.update({eval(key):chr(i)})
        
        for i in range(0, 10):
            key = 'QtCore.Qt.Key_{}'.format(i)
            key_dict.update({eval(key):str(i)})
        
        return key_dict
        
