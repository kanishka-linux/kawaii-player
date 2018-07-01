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
import urllib.parse
from functools import partial
from PyQt5 import QtCore, QtGui
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
        
    @pyqtSlot(str)
    def start_settings_box(self, val):
        ui.settings_box.start(mode=val)

    @pyqtSlot(str)
    def apply_new_text(self, val):
        ui.text.setText(val)

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
                widget.clicked.emit()
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
