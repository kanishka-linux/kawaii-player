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
import datetime
import platform
import urllib.parse
from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from settings_widget import LoginPCToPC

class GUISignals(QtCore.QObject):
    
    textsignal = pyqtSignal(str)
    fanartsignal = pyqtSignal(str, str)
    epsum_signal = pyqtSignal(int, str, str, str)
    login_box = pyqtSignal(str, str, bool)
    command_signal = pyqtSignal(str, str)
    poster_signal = pyqtSignal(bool, str, str)
    sub_signal = pyqtSignal(list)
    sub_apply = pyqtSignal(str, str)
    play_signal = pyqtSignal(str, int)
    start_settings = pyqtSignal(str)
    title_signal = pyqtSignal(str)
    slave_status_signal = pyqtSignal(str)
    torrent_status_signal = pyqtSignal(str)
    observe_signal = pyqtSignal(float)
    opengl_signal = pyqtSignal(str)
    preview_signal = pyqtSignal(str, str, bool, int, int, int, int, str)
    queue_signal = pyqtSignal(str)
    queue_delete = pyqtSignal(int)
    display_signal = pyqtSignal(str)
    mouse_move_signal = pyqtSignal(tuple)
    adjust_mainwindow_signal = pyqtSignal(tuple)
    initial_view_signal = pyqtSignal(str)
    cursor_signal = pyqtSignal(tuple)
    
    def __init__(self, uiwidget, mw):
        QtCore.QObject.__init__(self)
        global ui, MainWindow
        self.text = ''
        ui = uiwidget
        MainWindow = mw
        self.textsignal.connect(self.apply_new_text)
        self.fanartsignal.connect(self.apply_fanart_widget)
        self.epsum_signal.connect(self.apply_episode_metadata)
        self.login_box.connect(self.show_login_box)
        self.command_signal.connect(self.control_slave_playback)
        self.poster_signal.connect(self.apply_dropped_fanart_poster)
        self.sub_signal.connect(self.grab_subtitle)
        self.sub_apply.connect(self.apply_player_subtitle)
        self.play_signal.connect(self.receive_playlist_command)
        self.start_settings.connect(self.start_settings_box)
        self.title_signal.connect(self.title_clicked)
        self.slave_status_signal.connect(self.track_slave_status)
        self.torrent_status_signal.connect(self.update_torrent_status_window)
        self.observe_signal.connect(self.mpv_observe_signal)
        self.opengl_signal.connect(self.update_opengl_widget)
        self.preview_signal.connect(self.preview_generated_new)
        self.queue_signal.connect(self.queue_signal_generated)
        self.queue_delete.connect(self.queue_delete_signal)
        self.display_signal.connect(self.display_signal_string)
        self.first_time = True
        self.mouse_move_signal.connect(self.mouse_move_function)
        self.adjust_mainwindow_signal.connect(self.adjust_mainwindow_function)
        self.initial_view_signal.connect(self.initial_view_signal_function)
        self.cursor_signal.connect(self.cursor_function)

    def generate_preview(self, picn, length, change_aspect, tsec, counter, x, y, source_val):
        self.preview_signal.emit(picn, length, change_aspect, tsec, counter, x, y, source_val)
    
    def set_text(self, text):
        self.text = text
    
    def set_fanart(self, fanart, theme):
        self.fanart = fanart
        self.theme = theme
        
    def text_changed(self, txt):
        self.textsignal.emit(txt)
        
    def fanart_changed(self, fanart, theme):
        self.fanartsignal.emit(fanart, theme)
        
    def ep_changed(self, num, ep, sumr, path):
        self.epsum_signal.emit(num, ep, sumr, path)
        
    def login_required(self, url, pls, verify):
        self.login_box.emit(url, pls, verify)
        
    def player_command(self, param, val):
        self.command_signal.emit(param, val)
        
    def poster_drop(self, param, picn, nm):
        self.poster_signal.emit(param, picn, nm)
        
    def subtitle_fetch(self, arr):
        self.sub_signal.emit(arr)
        
    def subtitle_apply(self, url, title):
        self.sub_apply.emit(url, title)
        
    def playlist_command(self, mode, row):
        self.play_signal.emit(mode, row)
        
    def box_settings(self, mode):
        self.start_settings.emit(mode)
        
    def click_title_list(self, mode):
        self.title_signal.emit(mode)
        
    def slave_status(self, val):
        self.slave_status_signal.emit(val)
        
    def update_torrent_status(self, val):
        self.torrent_status_signal.emit(val)

    def update_observe(self, val):
        self.observe_signal.emit(val)

    def update_opengl(self, val):
        self.opengl_signal.emit(val)

    def queue_item(self, val):
        self.queue_signal.emit(val)

    def delete_queue_item(self, val):
        self.queue_delete.emit(val)

    def display_string(self, val):
        self.display_signal.emit(val)

    def mouse_move_method(self, event):
        self.mouse_move_signal.emit(event)
        
    def adjust_mainwindow(self, val):
        self.adjust_mainwindow_signal.emit(val)
        
    def initial_view(self, val):
        self.initial_view_signal.emit(val)
        
    def cursor_method(self, val):
        self.cursor_signal.emit(val)
        
    @staticmethod
    def update_opengl_widget(val):
        if ui.tab_5.window().isMinimized():
            ui.tab_5.makeCurrent()
            ui.tab_5.self.paintGL()
            ui.tab_5.context().swapBuffers(ui.tab_5.context().surface())
            ui.tab_5.swapped()
            ui.tab_5.doneCurrent()
        else:
            ui.tab_5.update()
            
    @staticmethod
    def mpv_observe_signal(val):
        ui.slider.setValue(int(val))
    
    @staticmethod
    def update_torrent_status_window(value):
        text = ui.label_torrent_status.toPlainText()
        if text and text.startswith('+'):
            ui.torrent_status_command = 'map'
            text = text[1:]
            ui.label_torrent_status.setText(text)
        elif text and text.startswith('-'):
            ui.torrent_status_command = 'default'
            text = text[1:]
            ui.label_torrent_status.setText(text)
        elif text and text.startswith('*'):
            ui.torrent_status_command = 'all'
            text = text[1:]
            ui.label_torrent_status.setText(text)
        else:
            vscroll = ui.label_torrent_status.verticalScrollBar().value()
            ui.label_torrent_status.setText(value)
            ui.label_torrent_status.verticalScrollBar().setValue(vscroll)
    
    @staticmethod
    def check_master_mode(value):
        def real_deco(func):
            def wrapper(*args, **kargs):
                gui = args[0]
                if (gui.extra_toolbar_control == 'slave'
                        and gui.pc_to_pc_casting == 'master'
                        and gui.mpvplayer_val.processId() == 0):
                    if value == 'stop':
                        gui.settings_box.playerstop.clicked_emit()
                    elif value == 'playpause':
                        gui.settings_box.play_pause.clicked_emit()
                    elif value == 'toggle_sub':
                        gui.settings_box.toggle_sub.clicked_emit()
                    elif value == 'toggle_aud':
                        gui.settings_box.toggle_aud.clicked_emit()
                    elif value == 'next':
                        gui.settings_box.playernext.clicked_emit()
                    elif value == 'prev':
                        gui.settings_box.playerprev.clicked_emit()
                    elif value == 'loop':
                        gui.settings_box.play_loop.clicked_emit()
                else:
                    func(*args, **kargs)
            return wrapper
        return real_deco
        
    @staticmethod
    def check_master_mode_playlist(value):
        def real_deco(func):
            def wrapper(*args, **kargs):
                gui = args[0]
                if (gui.extra_toolbar_control == 'slave'
                        and gui.pc_to_pc_casting == 'master'
                        and ui.slave_live_status):
                    if ui.list2.currentItem():
                        ui.list2.start_pc_to_pc_casting("playlist", ui.list2.currentRow())
                    else:
                        func(*args, **kargs)
                else:
                    func(*args, **kargs)
            return wrapper
        return real_deco

    @pyqtSlot(str, str, bool, int, int, int, int, str)
    def preview_generated_new(self, picn, length, change_aspect, tsec, counter, x, y, source_val):
        ui.slider.preview_generated(picn, length, change_aspect, tsec, counter, x, y, source_val)

    @pyqtSlot(tuple)
    def mouse_move_function(self, event_tuple):
        widget, event = event_tuple
        QtWidgets.QApplication.postEvent(widget, event)
        
    @pyqtSlot(str)
    def queue_signal_generated(self, val):
        ui.list2.queue_item()

    @pyqtSlot(str)
    def display_signal_string(self, val):
        ui.progressEpn.setFormat((val))
        
    @pyqtSlot(tuple)
    def cursor_function(self, val):
        widget, opt = val
        if opt == "show":
            widget.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        else:
            if platform.system().lower() == "darwin" and widget == ui.tab_5:
                widget.arrow_timer.start(1000)
            else:
                widget.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
            
    @pyqtSlot(int)
    def queue_delete_signal(self, val):
        ui.delete_queue_item(val)
        
    @pyqtSlot(str)
    def initial_view_signal_function(self, val):
        ui.restore_initial_view(val)
        
    @pyqtSlot(str)
    def track_slave_status(self, val):
        #print(val, "from-slave")
        float_check =  lambda x: int(x) if x.isnumeric() else int(float(x))
        val_arr = val.split('::')
        if len(val_arr) > 3 and ui.mpvplayer_val.processId() == 0:
            length = float_check(val_arr[0])
            counter = float_check(val_arr[1])
            row = float_check(val_arr[2]) - 1
            que = float_check(val_arr[3])
            if len(val_arr) > 4 :
                epn = val_arr[4]
            else:
                epn = None
            nlen = str(datetime.timedelta(seconds=int(length)))
            tme = str(datetime.timedelta(seconds=int(counter)))
            if (counter in range(0, 5) and row != ui.list2.currentRow()) or self.first_time:
                #ui.list2.setCurrentRow(row)
                self.first_time = False
            slider_max = ui.slider.maximum()
            if length != slider_max:
                ui.slider.setRange(0, length)
            item = ui.list2.item(row)
            if item:
                title = item.text()
            else:
                title = 'Not Available'
            if epn not in [None, ""]:
                title = epn
            if title and isinstance(title, str):
                MainWindow.windowTitleChanged.emit(title)
            ui.slider.setValue(counter)
            ui.progressEpn.setValue(0)
            ui.progressEpn.setFormat((''))
            ui.progressEpn.setFormat(('{} / {}'.format(tme, nlen)))
            if hasattr(ui.tab_5, "send_fake_event") and counter % 10 == 0:
                ui.tab_5.send_fake_event("mouse_release")
            
    @pyqtSlot(str)
    def title_clicked(self, val):
        #if ui.display_device == "rpitv":
        #    if ui.list1.currentRow():
        #        title_index = ui.list1.currentRow()
        #    else:
        #        title_index = -1
        #    ui.experiment_list({"mode":"pls", "epi": ui.list2.currentRow(), "title_index": title_index})
        #    ui.listfound(show_ep_thumbnail=True)
        #else:
        ui.listfound()
        ui.update_list2(show_thumb=True)
    
    @pyqtSlot(str)
    def start_settings_box(self, val):
        ui.settings_box.start(mode=val)

    @pyqtSlot(str)
    def apply_new_text(self, val):
        ui.text.setText(val)
        
    @pyqtSlot(tuple)
    def adjust_mainwindow_function(self, val):
        ui.adjust_widget_size(val)
        
    @pyqtSlot(str, str)
    def apply_player_subtitle(self, url, title):
        ui.tab_5.load_external_sub(mode='load', subtitle=url, title=title)
    
    @pyqtSlot(str, int)
    def receive_playlist_command(self, mode, row):
        ui.list2.start_pc_to_pc_casting(mode, row)
        
    @pyqtSlot(list)
    def grab_subtitle(self, arr):
        for entry in arr:
            url, sub_name, title = entry
            if not os.path.isfile(sub_name):
                ui.vnt.get(
                    url, out=sub_name,
                    onfinished=partial(ui.yt.post_subtitle_fetch, title)
                    )
            else:
                ui.tab_5.load_external_sub(mode='auto', subtitle=sub_name, title=title)

    @pyqtSlot(bool, str, str)
    def apply_dropped_fanart_poster(self, poster_drop, url, nm):
        site = ui.get_parameters_value(s='site')['site']
        if url.startswith('http'):
            ui.watch_external_video('{}'.format(url), start_now=True)
        elif poster_drop:
            if site == 'Music':
                ui.copy_poster_image(url, find_name=True)
            else:
                ui.copyImg(new_name=nm)
        else:
            if site == 'Music':
                ui.copy_fanart_image(url, find_name=True)
            else:
                ui.copyFanart(new_name=nm)

    @pyqtSlot(str, str)
    def apply_fanart_widget(self, fanart, theme):
        QtCore.QTimer.singleShot(100, partial(ui.set_mainwindow_palette, fanart, theme=theme))
        
    @pyqtSlot(str, str)
    def control_slave_playback(self, param, val):
        _, param_type = param.split('=')
        if param_type == 'gsbc':
            slider_name, slider_val = val.split('=')
            slider_list = [
                'zoom', 'speed', 'brightness',
                'gamma', 'saturation', 'hue', 'contrast'
                ]
            if slider_name in slider_list:
                slider = eval('ui.frame_extra_toolbar.{}_slider'.format(slider_name))
                slider.setValue(int(slider_val))
        elif param_type == 'volume':
            slider_name, slider_val = val.split('=')
            if slider_name == 'volume':
                ui.frame_extra_toolbar.slider_volume.setValue(int(slider_val))
        elif param_type == 'subtitle':
            subslider_list = [
                'text', 'border', 'shadow', 'blur',
                'xmargin', 'ymargin', 'xymargin', 'space'
            ]
            slider_name, slider_val = val.split('=')
            if slider_name == 'subscale':
                ui.frame_extra_toolbar.subscale_slider.setValue(int(slider_val))
            elif slider_name in subslider_list:
                slider = eval('ui.frame_extra_toolbar.subtitle_{}_slider'.format(slider_name))
                slider.setValue(int(slider_val))
        elif param_type == 'click':
            widget_list = [
                'btn_aspect_original', 'btn_aspect_disable', 'btn_aspect_4_3',
                'btn_aspect_16_9', 'btn_aspect_235', 'btn_scr_1',
                'btn_scr_2', 'btn_scr_3', 'btn_sub_minus', 'btn_sub_plus',
                'btn_aud_minus', 'btn_aud_plus', 'btn_chapter_minus',
                'btn_chapter_plus', 'btn_show_stat', 'btn_fs_window',
                'btn_fs_video'
                ]
            widget_name, widget_val = val.split('=')
            widget_name = urllib.parse.unquote(widget_name)
            widget_val = urllib.parse.unquote(widget_val)
            if widget_name == 'widget' and widget_val in widget_list:
                widget = eval('ui.frame_extra_toolbar.{}'.format(widget_val))
                widget.clicked_emit()
            elif widget_name in ['font_color_value', 'border_color_value', 'shadow_color_value']:
                ui.frame_extra_toolbar.apply_slave_subtitile_effects(widget_name, widget_val)
            elif widget_name in ['checkbox_bold', 'checkbox_italic', 'checkbox_gray', 'checkbox_dont']:
                widget = eval('ui.frame_extra_toolbar.{}'.format(widget_name))
                if widget_val.lower() == 'true':
                    widget.setChecked(True)
                else:
                    widget.setChecked(False)
            elif widget_name == 'font_value':
                widget = eval('ui.frame_extra_toolbar.{}'.format(widget_name))
                widget.setText(widget_val)
                ui.frame_extra_toolbar.change_sub_font(widget, widget_name)
            elif widget_name in ['subtitle_horiz_align', 'subtitle_vertical_align', 'ass_override_value']:
                widget = eval('ui.frame_extra_toolbar.{}'.format(widget_name))
                if widget_name == 'subtitle_vertical_align' and widget_val == 'center':
                        widget_val = 'Middle'
                widget_val = widget_val.title()
                index = widget.findText(widget_val)
                widget.setCurrentIndex(index)
                
    @pyqtSlot(str, str, bool)
    def show_login_box(self, url, pls, verify):
        LoginPCToPC(MainWindow, url, ui, pls, verify, onfinished=ui.list2.post_pc_processing)
        
    @pyqtSlot(int, str, str, str)
    def apply_episode_metadata(self, num, ep, sumr, path):
        if num < ui.list2.count():
            ui.list2.item(num).setText(ep)
            ui.list2.item(num).setIcon(QtGui.QIcon(path))
            ui.text.setText(sumr)
