"""

    Opengl related Code adapted from https://gist.github.com/cosven/b313de2acce1b7e15afda263779c0afc
    
"""
import os
import platform
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import QOpenGLWidget, QApplication
from PyQt5.QtOpenGL import QGLContext

from OpenGL import GL

from mpv import MPV, _mpv_get_sub_api, _mpv_opengl_cb_set_update_callback, \
        _mpv_opengl_cb_init_gl, OpenGlCbGetProcAddrFn, _mpv_opengl_cb_draw, \
        _mpv_opengl_cb_report_flip, MpvSubApi, OpenGlCbUpdateFn, _mpv_opengl_cb_uninit_gl

from player import PlayerWidget, KeyBoardShortcuts

def get_proc_addr(_, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    addr = int(glctx.getProcAddress(name.decode('utf-8')))
    return addr

class QProcessExtra(QtCore.QProcess):
    
    def __init__(self, parent=None, ui=None, logr=None, tmp=None):
        super(QProcessExtra, self).__init__(parent)
        self.ui = ui
        
    def write(self, cmd):
        if self.ui.player_val == "libmpv":
            print(cmd)
            cmd = str(cmd, "utf-8").strip()
            cmd_arr = cmd.split()
            print(cmd_arr)
            if cmd_arr[0] == "show-text":
                cmd_tail = cmd.split(" ", 1)[-1]
                if cmd_tail.startswith('"') or cmd_tail.startswith("'"):
                   cmd = cmd[:-1]
                   cmd = cmd[1:] 
                if "filename" in cmd_tail:
                    filename = self.ui.tab_5.mpv.filename
                    cmd_tail = "filename: {}".format(filename)
                elif "chapter" in cmd_tail:
                    chapter = self.ui.tab_5.mpv.chapter
                    total = self.ui.tab_5.mpv.chapters
                    meta = self.ui.tab_5.mpv.chapter_metadata
                    print(meta)
                    cmd_tail = "Chapter: {} / {} {}".format(chapter, total, meta)
                elif "${aid}" in cmd_tail:
                    aid = self.ui.tab_5.mpv.aid
                    cmd_tail = "Audio: {}".format(aid)
                elif "${sid}" in cmd_tail:
                    sid = self.ui.tab_5.mpv.sid
                    cmd_tail = "Sub: {}".format(sid)
                self.ui.tab_5.mpv.command("show-text", cmd_tail)
                print(self.ui.tab_5.mpv.property_list)
                print(self.ui.tab_5.mpv.chapter_list)
                #print(self.ui.tab_5.mpv.track_list)
            else:
                try:
                    
                    if "sub-font-size" in cmd_arr:
                        font_size = cmd_arr[-1]
                        self.ui.tab_5.mpv.sub_font_size = font_size
                        print(font_size)
                    elif "sub-font" in cmd_arr:
                        sub_font = cmd_arr[-1]
                        self.ui.tab_5.mpv.sub_font = sub_font.replace('"', "")
                        print(sub_font)
                    elif "sub-color" in cmd_arr:
                        sub_color = cmd_arr[-1]
                        self.ui.tab_5.mpv.sub_color = sub_color.replace('"', "")
                    elif "sub-border-color" in cmd_arr:
                        sub_border_color = cmd_arr[-1]
                        self.ui.tab_5.mpv.sub_border_color = sub_border_color.replace('"', "")
                    elif "sub-shadow-color" in cmd_arr:
                        sub_shadow_color = cmd_arr[-1]
                        self.ui.tab_5.mpv.sub_shadow_color = sub_shadow_color.replace('"', "")
                    else:
                        self.ui.tab_5.mpv.command(*cmd_arr)
                    #self.ui.tab_5.mpv.command("show-text", "{}".format(cmd))
                except Exception as e:
                    print(e)
                    self.ui.tab_5.mpv.command("show-text", "not found: {}, {}".format(cmd, e), 5000)
            
        else:
            super(QProcessExtra, self).write(cmd)

class MpvOpenglWidget(QOpenGLWidget):
    
    mpv = MPV(vo='libmpv', ytdl=True,
              keep_open=True, idle=True)
    if platform.system().lower() == "darwin":
        mpv.ao = "coreaudio"
    elif os.name == "posix":
        mpv.ao = "pulse"
    elif os.name == "nt":
        mpv.ao = "wasapi"
    def __init__(self, parent=None, ui=None, logr=None, tmp=None):
        global gui, MainWindow, screen_width, screen_height, logger
        print(ui, logr, tmp, "--")
        super().__init__(parent)
        gui = ui
        self.ui = ui
        MainWindow = parent
        logger = logr
        self.mpv_gl = _mpv_get_sub_api(self.mpv.handle, MpvSubApi.MPV_SUB_API_OPENGL_CB)
        self.on_update_c = OpenGlCbUpdateFn(self.on_update)
        self.on_update_fake_c = OpenGlCbUpdateFn(self.on_update_fake)
        self.get_proc_addr_c = OpenGlCbGetProcAddrFn(get_proc_addr)
        _mpv_opengl_cb_set_update_callback(self.mpv_gl, self.on_update_c, None)
        self.frameSwapped.connect(self.swapped, Qt.DirectConnection)
        self.arrow_timer = QtCore.QTimer()
        self.arrow_timer.timeout.connect(self.arrow_hide)
        self.arrow_timer.setSingleShot(True)

        self.pause_timer = QtCore.QTimer()
        self.pause_timer.timeout.connect(self.pause_unpause)
        self.pause_timer.setSingleShot(True)

        self.fs_timer = QtCore.QTimer()
        self.fs_timer.timeout.connect(self.toggle_fullscreen_mode)
        self.fs_timer.setSingleShot(True)
        
        self.player_val = "libmpv"
        screen_width = gui.screen_size[0]
        screen_height = gui.screen_size[1]
        self.custom_keys = {}
        self.event_dict = {'ctrl':False, 'alt':False, 'shift':False}
        self.key_map = KeyBoardShortcuts(gui, self)
        self.mpv_default = self.key_map.get_default_keys()
        self.mpv_custom, self.input_conf_list = self.key_map.get_custom_keys(gui.mpv_input_conf)
        self.custom_keys, _ = self.key_map.get_custom_keys(gui.custom_key_file)
        self.function_map = self.key_map.function_map()
        self.non_alphanumeric_keys = self.key_map.non_alphanumeric_keys()
        self.alphanumeric_keys = self.key_map.alphanumeric_keys()
        if self.custom_keys:
            self.mpv_default = self.custom_keys.copy()
        self.shift_keys = [
            '?', '>', '<', '"', ':', '}', '{', '|', '+', '_', 'sharp',
            ')', '(', '*', '&', '^', '%', '$', '#', '#', '@', '!', '~'
            ]
        self.aboutToResize.connect(self.resized)
        self.aboutToCompose.connect(self.compose)

    def set_mpvplayer(self, player=None, mpvplayer=None):
        if mpvplayer:
            self.mpvplayer = mpvplayer
        else:
            self.mpvplayer = self.ui.mpvplayer_val
        if player:
            self.player_val = player
        else:
            self.player_val = self.ui.player_val

    def pause_unpause(self, status=None):
        if status == "pause":
            self.mpv.command("set", "pause", "yes")
        else:
            self.mpv.command("set", "pause", "no")
            
    def compose(self):
        pass

    def resized(self):
        self.setFocus()
        self.update()
        
    def arrow_hide(self):
        if gui.player_val in ['mpv', 'mplayer', 'libmpv']:
            if self.hasFocus():
                self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                logger.debug('player has focus')
            else:
                logger.debug('player not focussed')
    
    @mpv.property_observer('time-pos')
    def time_observer(_name, value):
        if value is not None:
            z = 'duration is {:.2f}s'.format(value)
            gui.progress_counter = value
            gui.slider.setValue(value)
    
    @mpv.property_observer('eof-reached')
    def eof_observer(_name, value):
        print("eof.. value", value, _name)
        gui.cur_row = gui.tab_5.mpv.playlist_pos
        if gui.cur_row is not None:
            gui.list2.setCurrentRow(gui.cur_row)
        else:
            gui.cur_row = gui.list2.currentRow()
            
    @mpv.property_observer('duration')
    def time_duration(_name, value):
        if value is not None:
            z = 'duration is {:.2f}s'.format(value)
            gui.progressEpn.setFormat((z))
            gui.mplayerLength = int(value)
            gui.slider.setRange(0, int(gui.mplayerLength))
        
    def initializeGL(self):
        _mpv_opengl_cb_init_gl(self.mpv_gl, None, self.get_proc_addr_c, None)

    def paintGL(self):
        ratio = self.windowHandle().devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        _mpv_opengl_cb_draw(self.mpv_gl, self.defaultFramebufferObject(), w, -h)
        
    def resizeGL(self, width, height):
        ratio = self.windowHandle().devicePixelRatio()
        w = int(width * ratio)
        h = int(height * ratio)
        _mpv_opengl_cb_draw(self.mpv_gl, self.defaultFramebufferObject(), w, -h)
        
    @pyqtSlot()
    def maybe_update(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped()
            self.doneCurrent()
        else:
            self.update()

    def on_update(self, ctx=None):
        QMetaObject.invokeMethod(self, 'maybe_update')
        
    def on_update_fake(self, ctx=None):
        pass

    def swapped(self):
        _mpv_opengl_cb_report_flip(self.mpv_gl, 0)
        
    def closeEvent(self, _):
        self.makeCurrent()
        if self.mpv_gl:
            _mpv_opengl_cb_set_update_callback(self.mpv_gl, self.on_update_fake_c, None)
        _mpv_opengl_cb_uninit_gl(self.mpv_gl)
        self.mpv.terminate()
    
    def keyPressEvent(self, event):
        PlayerWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        PlayerWidget.keyReleaseEvent(self, event)
        
    def mouseDoubleClickEvent(self, event):
        self.toggle_fullscreen_mode()
        for i in self.event_dict:
            self.event_dict[i] = False
            
    def mouseMoveEvent(self, event):
        self.setFocus()
        PlayerWidget.mouseMoveEvent(self, event)

    def change_aspect_ratio(self):
        pass

    def start_player_loop(self):
        pass

    def show_hide_status_frame(self):
        pass

    def toggle_play_pause(self):
        self.ui.tab_5.mpv.command("cycle", "pause")

    def load_subtitle_from_file(self):
        pass

    def load_subtitle_from_network(self):
        pass

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
                self.ui.mpvplayer_val.write(command_string)

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
                self.ui.mpvplayer_val.write(bytes(new_command, 'utf-8'))
            msg = bytes(msg, 'utf-8')
            self.ui.mpvplayer_val.write(msg)
            
    def toggle_fullscreen_mode(self):
        wd = self.width()
        ht = self.height()
        val = self.mpv.fullscreen
        print(val, "-->>>>>>>>>fs--\n\n\n")
        if val is False or val is None:
            self.mpv.fullscreen = True
            self.player_fs(mode='fs')
        else:
            self.mpv.fullscreen = False
            self.player_fs(mode='nofs')
                

    def get_next(self):
        pls_count = self.mpv.playlist_count
        pls_pos = self.mpv.playlist_pos
        print(pls_count, pls_pos)
        if pls_count is not None and pls_pos is not None and pls_count == pls_pos + 1:
            self.mpv.playlist_pos = 0
        else:
            self.mpv.command("playlist-next")

    def get_previous(self):
        pls_count = self.mpv.playlist_count
        pls_pos = self.mpv.playlist_pos
        print(pls_count, pls_pos)
        if pls_count is not None and pls_pos is not None and pls_pos == 0:
            self.mpv.playlist_pos = pls_count - 1
        else:
            self.mpv.command("playlist-prev")

    def quit_player(self, msg=None):
        MainWindow.show()
        MainWindow.showMaximized()
        self.setParent(MainWindow)
        self.ui.gridLayout.addWidget(self, 0, 1, 1, 1)
        self.ui.superGridLayout.addWidget(self.ui.frame1, 1, 1, 1, 1)
        self.setMouseTracking(True)
        self.showNormal()
        self.setFocus()
        self.mpv.command("stop")
        self.ui.playerStop()
        
    def remember_and_quit(self):
        pass

    def cycle_player_subtitle(self):
        self.ui.mpvplayer_val.write(b'\n cycle sub \n')
        self.ui.mpvplayer_val.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
        self.ui.mpvplayer_val.write(b'\n show-text "${sid}" \n')
                
    def cycle_player_audio(self):
        self.ui.mpvplayer_val.write(b'\n cycle audio \n')
        self.ui.mpvplayer_val.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
        self.ui.mpvplayer_val.write(b'\n show-text "${aid}" \n')
                
    def stop_after_current_file(self):
        self.ui.quit_really = "yes"
        msg = '"Stop After current file"'
        msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
        self.mpvplayer.write(msg_byt)

    def player_fs(self, mode=None):
        self.mpv.command("set", "pause", "yes")
        if not self.ui.idw or self.ui.idw == str(int(self.winId())):
            if self.player_val == "libmpv":
                if mode == 'fs':
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
                        self.ui.superGridLayout.setSpacing(0)
                        self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                        
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
                        if self.player_val in self.ui.playback_engine:
                            MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                        MainWindow.showFullScreen()
                        #MainWindow.hide()
                        
                        #self.setParent(None)
                         
                        self.ui.fullscreen_video = True
                        #self.showFullScreen()
                        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
                        #self.setWindowState(QtCore.Qt.WindowFullScreen)
                        self.showFullScreen()
                        #MainWindow.showFullScreen()
                        #self.update()
                        self.ui.tab_5_layout.insertWidget(1, self.ui.frame1)
                        self.setFocus()
                        self.setMouseTracking(True)
                        QtWidgets.QApplication.processEvents()
                        self.makeCurrent()
                        #self.paintGL()
                        #self.update()

                        #self.context().swapBuffers(self.context().surface())
                        #self.swapped()
                        #self.update()
                elif mode == "nofs":
                    self.mpv.command("set", "pause", "yes")
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(5)
                    self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.list2.show()
                    self.ui.btn20.show()
                    if self.ui.wget.processId() > 0 or self.ui.video_local_stream:
                        self.ui.progress.show()
                    self.ui.frame1.show()
                    if self.player_val in self.ui.playback_engine:
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    if not self.ui.force_fs:
                        #MainWindow.showNormal()
                        MainWindow.show()
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
                    #self.setParent(MainWindow)
                    
                    #self.setParent(MainWindow)
                    self.ui.gridLayout.addWidget(self, 0, 1, 1, 1)
                    self.ui.superGridLayout.addWidget(self.ui.frame1, 1, 1, 1, 1)
                    self.setMouseTracking(True)
                    self.showNormal()
                    self.setFocus()
                    MainWindow.show() 
                    MainWindow.showMaximized()
                    #MainWindow.show()
                    self.makeCurrent()
                    #self.paintGL()
                    #self.update()
                    #self.doneCurrent()
                    #self.update()
                    #QtWidgets.QApplication.processEvents()
            else:
                if self.ui.detach_fullscreen:
                    self.ui.detach_fullscreen = False
                    self.ui.float_window.showNormal()
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
            param_dict = self.ui.get_parameters_value(icn='iconv_r_indicator', i='iconv_r')
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
        if not self.pause_timer.isActive():
            self.pause_timer.start(1000)
                        

    
