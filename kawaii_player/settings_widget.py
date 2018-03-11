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
import sys
import base64
import hashlib
import pickle
import ipaddress
import subprocess
from functools import partial
from PyQt5 import QtWidgets, QtCore, QtGui
from player_functions import ccurl, send_notification, get_lan_ip
from player_functions import open_files, write_files, change_opt_file


class LoginAuth(QtWidgets.QDialog):

    def __init__(
            self, parent=None, url=None, media_server=None, settings=None, 
            ssl_cert=None, ui=None, tmp=None):
        super(LoginAuth, self).__init__(parent)
        self.ui = ui
        self.tmpdir = tmp
        self.parent = parent
        if settings:
            self.setWindowTitle("Kawaii-Player Settings")
            self.grid = QtWidgets.QGridLayout(self)
            self.set_ip = QtWidgets.QLineEdit(self)
            self.set_ip.setText(self.ui.local_ip_stream+':'+str(self.ui.local_port_stream))

            self.set_ip_btn = QtWidgets.QPushButton('Check', self)
            self.set_ip_btn.setToolTip('Check your current IP Address OR\nUser can manually enter the field in the form "ip_address:port_number"')
            self.set_ip_btn.clicked.connect(self._set_local_ip)

            self.set_default_download = QtWidgets.QLineEdit(self)
            self.set_default_download.setText(self.ui.default_download_location)
            self.set_default_download.home(True)
            self.set_default_download.deselect()

            self.default_download_btn = QtWidgets.QPushButton('Set Directory', self)
            self.default_download_btn.setToolTip('Set Default Download Location')
            self.default_download_btn.clicked.connect(self._set_download_location)

            self.backg = QtWidgets.QComboBox(self)
            self.backg.addItem('KEEP_BACKGROUND_CONSTANT=yes')
            self.backg.addItem('KEEP_BACKGROUND_CONSTANT=no')
            self.backg.setToolTip('yes:Keep same default background for all\nno:keep changing the background as per title')
            if self.ui.keep_background_constant:
                self.backg.setCurrentIndex(0)
            else:
                self.backg.setCurrentIndex(1)

            self.img_opt = QtWidgets.QComboBox(self)
            self.img_opt.setToolTip('Use Ctrl+0 to Ctrl+9 keyboard shortcuts to Experiment with various background image modes. \n1:Fit To Screen\n2:Fit To Width\n3:Fit To Height\n4:Fit Upto Playlist\nRestart to see the effect OR if want to see immediate effect, then directly use keyboard shortcuts')
            img_opt_arr = ['IMAGE FIT OPTIONS', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
            for i in img_opt_arr:
                self.img_opt.addItem(i)
            img_val = str(self.ui.image_fit_option_val)
            if img_val == '10':
                img_val = '0'
            index = img_opt_arr.index(img_val)
            try:
                self.img_opt.setCurrentIndex(index)
            except Exception as e:
                print(e)
                self.img_opt.setCurrentIndex(0)
            self.ok_btn = QtWidgets.QPushButton('OK', self)
            self.ok_btn.clicked.connect(self._set_params)

            self.cancel_btn = QtWidgets.QPushButton('Cancel', self)
            self.cancel_btn.clicked.connect(self.hide)

            self.grid.addWidget(self.set_ip, 0, 0, 1, 1)
            self.grid.addWidget(self.set_ip_btn, 0, 1, 1, 1)
            self.grid.addWidget(self.set_default_download, 1, 0, 1, 1)
            self.grid.addWidget(self.default_download_btn, 1, 1, 1, 1)
            self.grid.addWidget(self.backg, 2, 0, 1, 1)
            self.grid.addWidget(self.img_opt, 2, 1, 1, 1)
            self.grid.addWidget(self.ok_btn, 3, 0, 1, 1)
            self.grid.addWidget(self.cancel_btn, 3, 1, 1, 1)
            self.show()
        elif ssl_cert:
            self.ssl_cert = ssl_cert
            self.pass_phrase = QtWidgets.QLineEdit(self)
            self.repeat_phrase = QtWidgets.QLineEdit(self)
            self.pass_phrase.setPlaceholderText('Enter Passphrase: atleast length 8')
            self.repeat_phrase.setPlaceholderText('Repeat Correct Passphrase')
            self.pass_phrase.setEchoMode(QtWidgets.QLineEdit.Password)
            self.repeat_phrase.setEchoMode(QtWidgets.QLineEdit.Password)
            self.btn_create = QtWidgets.QPushButton('Create SSL Certificate', self)
            self.btn_create.clicked.connect(self.handleSsl)
            self.setWindowTitle('SSL')
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.pass_phrase)
            layout.addWidget(self.repeat_phrase)
            layout.addWidget(self.btn_create)
        else:
            self.text_name = QtWidgets.QLineEdit(self)
            self.text_pass = QtWidgets.QLineEdit(self)
            self.text_name.setPlaceholderText('USER')
            self.text_pass.setPlaceholderText('PASSWORD')
            self.text_pass.setEchoMode(QtWidgets.QLineEdit.Password)
            if not media_server:
                self.btn_login = QtWidgets.QPushButton('Login', self)
                self.btn_login.clicked.connect(self.handleLogin)
                self.setWindowTitle('Credentials Required')
            else:
                self.btn_login = QtWidgets.QPushButton('Set', self)
                self.btn_login.clicked.connect(self._set_password)
                self.setWindowTitle('SET User and Password')
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.text_name)
            layout.addWidget(self.text_pass)
            layout.addWidget(self.btn_login)
            self.auth_info = ''
            self.auth_64 = ''
            self.url = url
            self.show()
            self.count = 0
            self.found = True

    def handleSsl(self):
        if self.pass_phrase.text() == self.repeat_phrase.text():
            self.hide()
            pass_word = self.pass_phrase.text()
            if len(pass_word) >= 8:
                my_ip = str(self.ui.local_ip_stream)
                server_key = os.path.join(self.tmpdir, 'server.key')
                server_csr = os.path.join(self.tmpdir, 'server.csr')
                server_crt = os.path.join(self.tmpdir, 'server.crt')
                cn = '/CN='+my_ip
                if self.ui.my_public_ip and self.ui.access_from_outside_network:
                    my_ip = str(self.ui.my_public_ip)	
                try:
                    subprocess.call(['openssl', 'genrsa', '-des3', '-passout',
                                     'pass:'+pass_word, '-out', server_key, '2048'])
                    print('key--generated')
                    subprocess.call(['openssl', 'rsa', '-in', server_key, '-out',
                                     server_key, '-passin', 'pass:'+pass_word])
                    print('next')
                    subprocess.call(['openssl', 'req', '-sha256', '-new', '-key',
                                     server_key, '-out', server_csr, '-subj', cn])
                    print('req')
                    subprocess.call(['openssl', 'x509', '-req', '-sha256', '-days',
                                     '365', '-in', server_csr, '-signkey', server_key,
                                     '-out', server_crt])
                    print('final')
                    f = open(self.ssl_cert, 'w')
                    content1 = open(server_crt).read()
                    content2 = open(server_key).read()
                    f.write(content1+'\n'+content2)
                    f.close()
                    print('ssl generated')
                    send_notification("Certificate Successfully Generated.\nNow Start Media Server Again.")
                except Exception as e:
                    print(e)
                    send_notification("Error in Generating SSL Certificate. Either 'openssl' or 'openssl.cnf' is not available in system path! Create 'cert.pem' manually, and keep it in Kawaii-Player config directory.")
            else:
                self.pass_phrase.clear()
                self.repeat_phrase.clear()
                self.pass_phrase.setPlaceholderText('Length of password less than 8 characters, Make it atleast 8')
                self.show()
        else:
            self.pass_phrase.clear()
            self.repeat_phrase.clear()
            self.pass_phrase.setPlaceholderText('Wrong Values Try again')
            self.show()

    def _set_params(self):
        new_ip_val = None
        new_ip_port = None
        torrent_ip = None
        try:
            if ':' in self.set_ip.text():
                new_ip_val, new_ip_port1 = self.set_ip.text().split(':')
                new_ip_port = int(new_ip_port1)
            if ipaddress.ip_address(new_ip_val):
                ip = 'LOCAL_STREAM_IP='+new_ip_val+':'+str(new_ip_port)
                torrent_ip = 'TORRENT_STREAM_IP='+new_ip_val+':'+str(self.ui.local_port)
        except Exception as err_val:
            print(err_val, '--ip--find--error--')
            ip = 'LOCAL_STREAM_IP='+self.ui.local_ip_stream
            new_ip_val = self.ui.local_ip_stream
            new_ip_port = 9001
        if os.path.exists(self.set_default_download.text()):
            location = 'DEFAULT_DOWNLOAD_LOCATION='+self.set_default_download.text()
            location_val = self.set_default_download.text()
        else:
            location = 'DEFAULT_DOWNLOAD_LOCATION='+self.ui.default_download_location
            location_val = self.ui.default_download_location
        backg = self.backg.currentText()
        img_val = self.img_opt.currentIndex()
        if img_val == 0:
            img_val = 1
        img_opt_str = 'IMAGE_FIT_OPTION='+str(img_val)
        config_file = os.path.join(self.ui.home_folder, 'other_options.txt')
        lines = open_files(config_file, lines_read=True)
        new_lines = []
        for i in lines:
            i = i.strip()
            if i.startswith('LOCAL_STREAM_IP='):
                i = ip
            elif i.startswith('DEFAULT_DOWNLOAD_LOCATION='):
                i = location
            elif i.startswith('KEEP_BACKGROUND_CONSTANT='):
                i = backg
            elif i.startswith('IMAGE_FIT_OPTION='):
                i = img_opt_str
            new_lines.append(i)
        write_files(config_file, new_lines, line_by_line=True)
        self.ui.local_ip_stream = new_ip_val
        self.ui.local_port_stream = new_ip_port
        self.ui.default_download_location = location_val
        self.ui.image_fit_option_val = img_val
        back_g = backg.split('=')[1]
        if back_g == 'no':
            self.ui.keep_background_constant = False
        else:
            self.ui.keep_background_constant = True
        if torrent_ip:
            config_file_torrent = os.path.join(self.ui.home_folder, 'torrent_config.txt')
            change_opt_file(config_file_torrent, 'TORRENT_STREAM_IP=', torrent_ip)
            self.ui.local_ip = new_ip_val
        self.hide()

    def _set_download_location(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent, 'Set Directory', self.ui.last_dir)
        if fname:
            self.set_default_download.setText(fname)
            self.ui.last_dir = fname

    def _set_local_ip(self):
        try:
            ip = get_lan_ip()
            self.set_ip.setText(ip+':'+str(self.ui.local_port_stream))
        except Exception as e:
            print(e)
            self.set_ip.setText(self.ui.local_ip_stream+':'+str(self.ui.local_port_stream))

    def _set_password(self):
        text_val = self.text_name.text()
        pass_val = self.text_pass.text()
        if not text_val:
            text_val = ''
        if not pass_val:
            pass_val = ''
        new_combine = bytes(text_val+':'+pass_val, 'utf-8')
        new_txt = base64.b64encode(new_combine)
        new_txt_str = 'Basic '+str(new_txt, 'utf-8')
        #print(new_txt, new_txt_str)
        new_txt_bytes = bytes(str(new_txt_str), 'utf-8')
        #print(new_txt_bytes)
        h = hashlib.sha256(new_txt_bytes)
        h_digest = h.hexdigest()
        new_pass = 'AUTH='+h_digest
        config_file = os.path.join(self.ui.home_folder, 'other_options.txt')
        content = open_files(config_file, lines_read=False)
        content = re.sub('AUTH=[^\n]*', new_pass, content)
        write_files(config_file, content, line_by_line=False)
        self.hide()
        self.ui.media_server_key = h_digest
        self.ui.client_auth_arr[:] = []
        self.ui.client_auth_arr = ['127.0.0.1', '0.0.0.0']
        if self.ui.local_ip not in self.ui.client_auth_arr:
            self.ui.client_auth_arr.append(self.ui.local_ip)
        if self.ui.local_ip_stream not in self.ui.client_auth_arr:
            self.ui.client_auth_arr.append(self.ui.local_ip_stream)

    def handleLogin(self):
        self.hide()
        text_val = self.text_name.text()
        pass_val = self.text_pass.text()
        self.auth_info = text_val+':'+pass_val
        content = ccurl(self.url+'#'+'-I', user_auth=self.auth_info)
        logger.info('content={0}'.format(content))
        if ((not content or 'www-authenticate' in content.lower() 
                or '401 unauthorized' in content.lower() 
                or 'curl failure' in content.lower()) and self.count < 3):
            self.text_name.clear()
            self.text_pass.clear()
            self.setWindowTitle('Wrong Credential, Try Again')
            self.text_name.setPlaceholderText('USER or PASSWORD Incorrect')
            new_txt = '{0} Attempts Left'.format(str(2-self.count))
            self.text_pass.setPlaceholderText(new_txt)
            self.found = False
            self.count = self.count+1
            self.show()
        elif content:
            self.found = True
        if self.url and self.found:
            self.ui.watch_external_video(self.url)


class OptionsSettings(QtWidgets.QTabWidget):
    
    def __init__(self, parent, uiwidget, tmp):
        super(OptionsSettings, self).__init__(parent)
        global ui, MainWindow, TMPDIR, logger
        ui = uiwidget
        MainWindow = parent
        TMPDIR = tmp
        logger = ui.logger
        self.setWindowTitle("Kawaii-Player Settings")
        #self.tab.setMinimumSize(QtCore.QSize(600, 300))
        self.tab_app = QtWidgets.QWidget(self)
        self.gl1 = QtWidgets.QGridLayout(self.tab_app)
        self.tab_server = QtWidgets.QWidget(self)
        self.gl2 = QtWidgets.QGridLayout(self.tab_server)
        self.tab_torrent = QtWidgets.QWidget(self)
        self.gl3 = QtWidgets.QGridLayout(self.tab_torrent)
        self.tab_meta = QtWidgets.QWidget(self)
        self.gl4 = QtWidgets.QGridLayout(self.tab_meta)
        self.tab_library = QtWidgets.QWidget(self)
        self.gl5 = QtWidgets.QGridLayout(self.tab_library)
        self.tab_close = QtWidgets.QWidget(self)
        self.tab_player = QtWidgets.QWidget(self)
        self.gl6 = QtWidgets.QGridLayout(self.tab_player)
        self.tab_config = QtWidgets.QWidget(self)
        self.gl7 = QtWidgets.QGridLayout(self.tab_config)
        self.tab_shortcuts = QtWidgets.QWidget(self)
        self.gl8 = QtWidgets.QGridLayout(self.tab_shortcuts)
        self.addTab(self.tab_close, 'X')
        self.addTab(self.tab_app, 'Appearance')
        self.addTab(self.tab_library, 'Library')
        self.addTab(self.tab_server, 'Media Server')
        self.addTab(self.tab_torrent, 'Torrent')
        self.addTab(self.tab_player, 'Player')
        self.addTab(self.tab_meta, 'Other')
        self.addTab(self.tab_config, 'Config')
        self.addTab(self.tab_shortcuts, 'Shortcuts')
        
        self.option_file = os.path.join(ui.home_folder, 'other_options.txt')
        self.torrent_config = os.path.join(ui.home_folder, 'torrent_config.txt')
        self.library_file_name = os.path.join(ui.home_folder, 'local.txt')
        self.config_file_name = os.path.join(ui.home_folder, 'src', 'customconfig')
        self.hide_label = False
        self.tabs_present = False
        self.setMouseTracking(True)
        self.font_families = ['default']
        
    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        if ui.search_on_type_btn.isHidden():
            self.setFocus()
    
    def tab_changed(self):
        index = self.currentIndex()
        if self.tabText(index) == 'X':
            self.hide()
            if self.hide_label:
                ui.label.show()
                ui.text.show()
                if ui.player_theme != 'default':
                    ui.label_new.show()
                self.hide_label = False
        else:
            ui.settings_tab_index = index
            logger.debug(ui.settings_tab_index)
        
    def start(self, index=None):
        if self.isHidden():
            logger.debug(ui.settings_tab_index)
            self.setCurrentIndex(ui.settings_tab_index)
            if not self.tabs_present:
                try:
                    self.font_families = [i for i in QtGui.QFontDatabase().families()]
                except Exception as err:
                    logger.error(err)
                ui.apply_new_font()
                self.appeareance()
                self.mediaserver()
                self.torrentsettings()
                self.othersettings()
                self.library()
                self.player_settings()
                self.configsettings()
                self.apply_tab_shortcuts()
                self.tabs_present = True
            if not ui.label.isHidden():
                ui.label_new.hide()
                ui.label.hide()
                ui.text.hide()
                self.hide_label = True
            self.show()
            self.currentChanged.connect(self.tab_changed)
        else:
            self.hide()
            if self.hide_label:
                ui.label.show()
                ui.text.show()
                if ui.player_theme != 'default':
                    ui.label_new.show()
                self.hide_label = False
        if index:
            self.setCurrentIndex(2)
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()    
    
    def appeareance_setdefault(self):
        if ui.player_theme == 'dark':
            fonts = ['noto serif', 'noto sans', 'ubuntu']
            found = None
            for font in fonts:
                for family in self.font_families:
                    if font == family.lower():
                        found = family
                        break
                if found:
                    break
            if found:
                ui.global_font = found
            else:
                self.global_font = QtGui.QFont().defaultFamily()
            ui.global_font_size = 10
            ui.font_bold = False
            ui.thumbnail_text_color = 'lightgray'
            ui.thumbnail_text_color_focus = 'green'
            ui.list_text_color = 'lightgray'
            ui.list_text_color_focus = 'violet'
        elif ui.player_theme == 'default':
            fonts = ['ubuntu', 'noto sans', 'noto serif']
            found = None
            for font in fonts:
                for family in self.font_families:
                    if font == family.lower():
                        found = family
                        break
                if found:
                    break
            if found:
                ui.global_font = found
            else:
                self.global_font = QtGui.QFont().defaultFamily()
            ui.global_font_size = 10
            ui.font_bold = True
            ui.thumbnail_text_color = 'white'
            ui.thumbnail_text_color_focus = 'green'
            ui.list_text_color = 'white'
            ui.list_text_color_focus = 'violet'
        self.line102.setPlaceholderText(ui.global_font)
        self.line103.setPlaceholderText(str(ui.global_font_size))
        index = self.line104.findText(str(ui.font_bold))
        self.line104.setCurrentIndex(index)
        self.line105.setPlaceholderText(ui.thumbnail_text_color)
        self.line106.setPlaceholderText(ui.thumbnail_text_color_focus)
        self.line107.setPlaceholderText(ui.list_text_color)
        self.line108.setPlaceholderText(ui.list_text_color_focus)
        QtCore.QTimer.singleShot(2000, partial(self.apply_changes_to_file, self.option_file))
    
    def apply_changes_to_file(self, file_name):
        lines = open_files(file_name)
        new_lines = []
        for i in lines:
            i = i.strip()
            if i.startswith('THEME='):
                i = 'THEME={}'.format(ui.player_theme.upper())
            elif i.startswith('GLOBAL_FONT='):
                i = 'GLOBAL_FONT={}'.format(ui.global_font)
            elif i.startswith('GLOBAL_FONT_SIZE='):
                i = 'GLOBAL_FONT_SIZE={}'.format(ui.global_font_size)
            elif i.startswith('FONT_BOLD='):
                i = 'FONT_BOLD={}'.format(ui.font_bold)
            elif i.startswith('THUMBNAIL_TEXT_COLOR='):
                i = 'THUMBNAIL_TEXT_COLOR={}'.format(ui.thumbnail_text_color)
            elif i.startswith('THUMBNAIL_TEXT_COLOR_FOCUS='):
                i = 'THUMBNAIL_TEXT_COLOR_FOCUS={}'.format(ui.thumbnail_text_color_focus)
            elif i.startswith('LIST_TEXT_COLOR='):
                i = 'LIST_TEXT_COLOR={}'.format(ui.list_text_color)
            elif i.startswith('LIST_TEXT_COLOR_FOCUS='):
                i = 'LIST_TEXT_COLOR_FOCUS={}'.format(ui.list_text_color_focus)
            new_lines.append(i)
        write_files(file_name, new_lines, line_by_line=True)
    
    def appeareance(self):
        self.param_list = []
        self.line101 = QtWidgets.QComboBox()
        for i in ui.theme_list:
            self.line101.addItem(i)
        index = self.line101.findText(ui.player_theme.title())
        self.line101.setCurrentIndex(index)
        self.text101 = QtWidgets.QLabel()
        self.text101.setText("Theme")
        self.param_list.append('player_theme')
        
        self.line102 = QtWidgets.QLineEdit()
        self.completer = QtWidgets.QCompleter(self.font_families)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.line102.setCompleter(self.completer)
        self.line102.setPlaceholderText(ui.global_font)
        self.text102 = QtWidgets.QLabel()
        self.text102.setText("Global Font")
        self.param_list.append('global_font')
        
        self.line103 = QtWidgets.QLineEdit()
        self.line103.setPlaceholderText(str(ui.global_font_size))
        self.text103 = QtWidgets.QLabel()
        self.text103.setText("Global Font Size")
        self.param_list.append('global_font_size')
        
        self.line104 = QtWidgets.QComboBox()
        self.line104.addItem("True")
        self.line104.addItem("False")
        index = self.line104.findText(str(ui.font_bold))
        self.line104.setCurrentIndex(index)
        self.text104 = QtWidgets.QLabel()
        self.text104.setText("Font Bold")
        self.param_list.append('font_bold')
        
        self.line105 = QtWidgets.QLineEdit()
        self.line105.setPlaceholderText(ui.thumbnail_text_color)
        msg = ("<html>red, green, blue, yellow, gray, white, black, cyan, magenta, darkgray,\
                lightgray, darkred, darkblue, darkyellow, transparent.\
                \nFor Dark Theme, use lightgray, if white color looks bright<\html>")
        self.line105.setToolTip(msg)
        self.text105 = QtWidgets.QLabel()
        self.text105.setText("Thumbnail Text Color")
        self.param_list.append('thumbnail_text_color')
        
        self.line106 = QtWidgets.QLineEdit()
        self.line106.setPlaceholderText(ui.thumbnail_text_color_focus)
        msg1 = ('For focus, use somewhat bright color')
        self.text106 = QtWidgets.QLabel()
        self.text106.setText("Thumbnail Text Color Focus")
        self.param_list.append('thumbnail_text_color_focus')
        
        msg = msg.replace('.', ', violet.')
        
        self.line107 = QtWidgets.QLineEdit()
        self.line107.setPlaceholderText(ui.list_text_color)
        self.line107.setToolTip(msg)
        self.text107 = QtWidgets.QLabel()
        self.text107.setText("List Text Color")
        self.param_list.append('list_text_color')
        
        self.line108 = QtWidgets.QLineEdit()
        self.line108.setPlaceholderText(ui.list_text_color_focus)
        self.text108 = QtWidgets.QLabel()
        self.text108.setText("List Text Color Focus")
        self.param_list.append('list_text_color_focus')
        
        msg2 = ('<html>Use Ctrl+0 to Ctrl+9 keyboard shortcuts to Experiment with\
                various background image modes. These modes are useful only for \
                default theme.\
                \n\n1:Fit To Screen\n2:Fit To Width\n3:Fit To Height\n4:Tiled mode.\n\
                When next backgound image will be downloaded it will automatically\
                follow the mode. If new image does not follow mode then restart application.</html>')
        
        self.line109 = QtWidgets.QComboBox()
        for i in range(0, 10):
            self.line109.addItem(str(i))
        index = self.line109.findText(str(ui.image_fit_option_val))
        self.line109.setCurrentIndex(index)
        self.line109.setToolTip(msg2)
        self.text109 = QtWidgets.QLabel()
        self.text109.setText("Image Fit Option")
        self.param_list.append('image_fit_option_val')
        
        self.line110 = QtWidgets.QComboBox()
        self.line110.addItem("No")
        self.line110.addItem("Yes")
        if ui.keep_background_constant:
            val = 'Yes'
        else:
            val = 'No'
        index = self.line110.findText(val)
        self.line110.setCurrentIndex(index)
        self.text110 = QtWidgets.QLabel()
        self.text110.setText("Keep Background Constant")
        self.param_list.append('keep_background_constant')
        
        self.line111 = QtWidgets.QComboBox()
        self.line111.addItem("True")
        self.line111.addItem("False")
        index = self.line111.findText(str(ui.list_with_thumbnail))
        self.line111.setCurrentIndex(index)
        self.text111 = QtWidgets.QLabel()
        self.text111.setText("List With Thumbnail")
        self.param_list.append('list_with_thumbnail')
        
        self.line112 = QtWidgets.QComboBox()
        self.line112.addItem("True")
        self.line112.addItem("False")
        index = self.line112.findText(str(ui.window_frame.title()))
        self.line112.setCurrentIndex(index)
        self.text112 = QtWidgets.QLabel()
        self.text112.setText("Allow Window Titlebar")
        self.param_list.append('window_frame')
        
        for i, j in enumerate(self.param_list):
            index = i+1
            if index < 10:
                index_str = '0' + str(index)
            else:
                index_str = str(index)
            text = eval('self.text1{}'.format(index_str))
            line = eval('self.line1{}'.format(index_str))
            self.gl1.addWidget(text, index, 0, 1, 1)
            self.gl1.addWidget(line, index, 1, 1, 1)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j, 'appearance'))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j, 'appearance'))
    
    def mediaserver(self):
        self.media_param = []
        self.line11 = QtWidgets.QLineEdit()
        self.line11.setText("{}:{}".format(ui.local_ip_stream, ui.local_port_stream))
        self.text11 = QtWidgets.QLabel()
        self.text11.setText("Local Stream IP")
        self.btn11 = QtWidgets.QPushButton()
        self.btn11.setText(" Check IP ")
        self.btn11.clicked.connect(partial(self.check_and_set_ip, self.line11, 'local_ip_stream'))
        self.media_param.append('local_ip_stream')
        
        self.line12 = QtWidgets.QComboBox()
        self.line12.addItem("False")
        self.line12.addItem("True")
        index = self.line12.findText(str(ui.https_media_server))
        self.line12.setCurrentIndex(index)
        self.text12 = QtWidgets.QLabel()
        self.text12.setText("HTTPS ON")
        self.media_param.append('https_media_server')
        
        self.line13 = QtWidgets.QComboBox()
        self.line13.addItem("False")
        self.line13.addItem("True")
        index = self.line13.findText(str(ui.media_server_cookie))
        self.line13.setCurrentIndex(index)
        self.text13 = QtWidgets.QLabel()
        self.text13.setText("Media Server Cookie")
        self.media_param.append('media_server_cookie')
        
        self.line14 = QtWidgets.QLineEdit()
        self.line14.setPlaceholderText("{} (In Hours)".format(ui.cookie_expiry_limit))
        self.text14 = QtWidgets.QLabel()
        self.text14.setText("Cookie Expiry Limit")
        self.media_param.append('cookie_expiry_limit')
        
        self.line15 = QtWidgets.QLineEdit()
        self.line15.setPlaceholderText("{} (In Hours)".format(ui.cookie_playlist_expiry_limit))
        self.text15 = QtWidgets.QLabel()
        self.text15.setText("Cookie Playlist Expiry Limit")
        self.media_param.append('cookie_playlist_expiry_limit')
        
        self.line16 = QtWidgets.QComboBox()
        self.line16.addItem("False")
        self.line16.addItem("True")
        index = self.line16.findText(str(ui.media_server_autostart))
        self.line16.setCurrentIndex(index)
        self.text16 = QtWidgets.QLabel()
        self.text16.setText("Media Server Autostart")
        self.media_param.append('media_server_autostart')
        
        self.line17 = QtWidgets.QLineEdit()
        self.line17.setPlaceholderText("{} (upload speed in peer to peer mode)".format(ui.setuploadspeed))
        self.text17 = QtWidgets.QLabel()
        self.text17.setText("P2P Upload Speed")
        self.media_param.append('setuploadspeed')
        
        self.line18 = QtWidgets.QLineEdit()
        self.line18.setPlaceholderText("{}".format(ui.broadcast_message))
        self.text18 = QtWidgets.QLabel()
        self.text18.setText("Broadcast Message")
        self.media_param.append('broadcast_message')
        
        for index, j in enumerate(self.media_param):
            i = index + 1
            text = eval('self.text1{}'.format(i))
            line = eval('self.line1{}'.format(i))
            if i == 1:
                self.gl2.addWidget(text, i, 0, 1, 1)
                self.gl2.addWidget(line, i, 1, 1, 1)
                self.gl2.addWidget(eval('self.btn1{}'.format(i)), i, 2, 1, 1)
            else:
                self.gl2.addWidget(text, i, 0, 1, 1)
                if j != 'broadcast_message':
                    self.gl2.addWidget(line, i, 1, 1, 2)
                else:
                    self.gl2.addWidget(line, i, 1, 1, 1)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j, 'mediaserver'))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j, 'mediaserver'))
        self.mediaserver_extra_buttons(index=index+1, mode=1)
        
    def mediaserver_extra_buttons(self, index=None, mode=None):
        if index and mode == 1:
            self.line021 = QtWidgets.QPushButton(ui.action_player_menu[8].text())
            self.line021.clicked.connect(partial(self.media_server_start, 'broadcast server'))
            self.gl2.addWidget(self.line021, index, 2, 1, 1)
            
            self.line022 = QtWidgets.QPushButton('Username/Password')
            self.line022.clicked.connect(partial(self.media_server_start, 'username'))
            self.gl2.addWidget(self.line022, index+1, 0, 1, 1)
            
            self.line19 = QtWidgets.QPushButton(ui.action_player_menu[7].text())
            self.line19.clicked.connect(partial(self.media_server_start, 'start'))
            self.gl2.addWidget(self.line19, index+1, 1, 1, 1)
            
            self.line020 = QtWidgets.QPushButton(ui.action_player_menu[9].text())
            self.line020.clicked.connect(partial(self.media_server_start, 'remote_control'))
            self.gl2.addWidget(self.line020, index+1, 2, 1, 1)
            
            
        elif index is None and mode == 2:
            self.line19.setText(ui.action_player_menu[7].text())
            self.line020.setText(ui.action_player_menu[9].text())
            self.line021.setText(ui.action_player_menu[8].text())
            
    def media_server_start(self, val):
        if val == 'start':
            ui.playerPlaylist('Start Media Server')
        elif val == 'remote_control':
            ui.playerPlaylist('turn on remote control')
        elif val == 'broadcast server':
            ui.playerPlaylist('Broadcast Server')
        elif val == 'username':
            ui.playerPlaylist('set media server user/password')
            
    def torrentsettings(self):
        self.torrent_param = []
        self.line21 = QtWidgets.QLineEdit()
        self.line21.setText("{}:{}".format(ui.local_ip, ui.local_port))
        self.text21 = QtWidgets.QLabel()
        self.text21.setText("Torrent Stream IP")
        self.btn21 = QtWidgets.QPushButton()
        self.btn21.setText(" Check IP ")
        self.btn21.clicked.connect(partial(self.check_and_set_ip, self.line21, 'local_ip'))
        self.torrent_param.append('local_ip')
        
        self.line22 = QtWidgets.QLineEdit()
        self.line22.setPlaceholderText(ui.torrent_download_folder)
        self.text22 = QtWidgets.QLabel()
        self.text22.setText("Torrent Download Folder")
        self.btn22 = QtWidgets.QPushButton()
        self.btn22.setText(" Set Location ")
        self.btn22.clicked.connect(partial(self.set_folder, self.line22, 'torrent_download_folder'))
        self.torrent_param.append('torrent_download_folder')
        
        self.line23 = QtWidgets.QLineEdit()
        self.line23.setPlaceholderText("{} (in KB, 0 means unlimited )".format(int(ui.torrent_upload_limit/1024)))
        self.text23 = QtWidgets.QLabel()
        self.text23.setText("Torrent Upload Rate")
        self.torrent_param.append('torrent_upload_limit')
        
        self.line24 = QtWidgets.QLineEdit()
        self.line24.setPlaceholderText("{}".format(int(ui.torrent_download_limit/1024)))
        self.text24 = QtWidgets.QLabel()
        self.text24.setText("Torrent Download Rate")
        self.torrent_param.append('torrent_download_limit')
        
        for index, j in enumerate(self.torrent_param):
            i = index + 1
            text = eval('self.text2{}'.format(i))
            line = eval('self.line2{}'.format(i))
            if i == 1 or i == 2:
                self.gl3.addWidget(text, i, 0, 1, 1)
                self.gl3.addWidget(line, i, 1, 1, 1)
                self.gl3.addWidget(eval('self.btn2{}'.format(i)), i, 2, 1, 1)
            else:
                self.gl3.addWidget(text, i, 0, 1, 1)
                self.gl3.addWidget(line, i, 1, 1, 2)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j, option='torrent'))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j, option='torrent'))
    
    def othersettings(self):
        self.other_settings = []
        self.line31 = QtWidgets.QLineEdit()
        self.line31.setPlaceholderText("{}".format(ui.default_download_location))
        self.text31 = QtWidgets.QLabel()
        self.text31.setText("Default Download Location")
        self.btn31 = QtWidgets.QPushButton()
        self.btn31.setText(" Set Location ")
        self.btn31.clicked.connect(partial(self.set_folder, self.line31, 'default_download_location'))
        self.other_settings.append('default_download_location')
        
        self.line32 = QtWidgets.QComboBox()
        self.line32.addItem("QTWEBENGINE")
        self.line32.addItem("QTWEBKIT")
        index = self.line32.findText(str(ui.browser_backend.upper()))
        self.line32.setCurrentIndex(index)
        self.text32 = QtWidgets.QLabel()
        self.text32.setText("Browser Backend")
        self.other_settings.append('browser_backend')
        
        self.line33 = QtWidgets.QLineEdit()
        self.line33.setPlaceholderText(
            '{} (Available options: default, automatic or complete path)'.format(
                ui.ytdl_path
                )
            )
        self.text33 = QtWidgets.QLabel()
        self.text33.setText("YTDL Path")
        self.text33.setToolTip("<html>default, automatic or complete path.\
         1. default: it will look for executable in system path. \
         2. automatic: it will grab ytdl executable automatically\
         from official website and set path accordingly.\
         3. or enter complete path of executable</html>")
        self.other_settings.append('ytdl_path')
        
        self.line34 = QtWidgets.QComboBox()
        self.line34.addItem('Off')
        self.line34.addItem('On')
        if ui.logging_module:
            logging_module = 'On'
        else:
            logging_module = 'Off'
        index = self.line34.findText(logging_module)
        self.line34.setCurrentIndex(index)
        self.text34 = QtWidgets.QLabel()
        self.text34.setText("Logging")
        self.other_settings.append('logging_module')
        
        self.line35 = QtWidgets.QComboBox()
        self.line35.addItem('pycurl')
        self.line35.addItem('curl')
        self.line35.addItem('wget')
        index = self.line35.findText(str(ui.get_fetch_library))
        self.line35.setCurrentIndex(index)
        self.text35 = QtWidgets.QLabel()
        self.text35.setText("Get Library")
        self.other_settings.append('get_fetch_library')
        
        self.line36 = QtWidgets.QComboBox()
        self.line36.addItem('True')
        self.line36.addItem('False')
        index = self.line36.findText(str(ui.anime_review_site))
        self.line36.setCurrentIndex(index)
        self.text36 = QtWidgets.QLabel()
        self.text36.setText("Anime Review Site")
        self.other_settings.append('anime_review_site')
        
        self.line37 = QtWidgets.QComboBox()
        self.line37.addItem('False')
        self.line37.addItem('True')
        index = self.line37.findText(str(ui.get_artist_metadata))
        self.line37.setCurrentIndex(index)
        self.text37 = QtWidgets.QLabel()
        self.text37.setText("Get Music Metadata")
        self.other_settings.append('get_artist_metadata')
        
        for index, j in enumerate(self.other_settings):
            i = index + 1
            text = eval('self.text3{}'.format(i))
            line = eval('self.line3{}'.format(i))
            if i == 1:
                self.gl4.addWidget(text, i, 0, 1, 1)
                self.gl4.addWidget(line, i, 1, 1, 1)
                self.gl4.addWidget(eval('self.btn3{}'.format(i)), i, 2, 1, 1)
            else:
                self.gl4.addWidget(text, i, 0, 1, 1)
                self.gl4.addWidget(line, i, 1, 1, 2)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j, 'othersettings'))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j, 'othersettings'))
                
    def library(self):
        self.list_library = QtWidgets.QListWidget()
        self.list_library.setObjectName("list_library")
        self.add_library_btn = QtWidgets.QPushButton()
        self.add_library_btn.setObjectName('add_library_btn')
        self.add_library_btn.setText(" Add Folder ")
        self.remove_library_btn = QtWidgets.QPushButton()
        self.remove_library_btn.setObjectName('remove_library_btn')
        self.remove_library_btn.setText(' Remove Folder ')
        self.add_library_btn.setMinimumHeight(32)
        self.remove_library_btn.setMinimumHeight(32)
        self.gl5.addWidget(self.list_library, 0, 0, 1, 2)
        self.gl5.addWidget(self.add_library_btn, 1, 0, 1, 1)
        self.gl5.addWidget(self.remove_library_btn, 1, 1, 1, 1)
        if os.path.exists(self.library_file_name):
            lines = open_files(self.library_file_name, True)
            self.list_library.clear()
            for i in lines:
                i = i.strip()
                self.list_library.addItem(i)
        self.add_library_btn.clicked.connect(self.add_folder_to_library)
        self.remove_library_btn.clicked.connect(self.remove_folder_from_library)
            
    def player_settings(self):
        self.player_list = []
        
        self.line41 = QtWidgets.QComboBox()
        self.line41.addItem("False")
        self.line41.addItem("True")
        index = self.line41.findText(str(ui.restore_volume))
        self.line41.setCurrentIndex(index)
        self.text41 = QtWidgets.QLabel()
        self.text41.setText("Remember Volume Per Video")
        self.player_list.append('restore_volume')
        
        self.line42 = QtWidgets.QComboBox()
        self.line42.addItem("False")
        self.line42.addItem("True")
        index = self.line42.findText(str(ui.restore_aspect))
        self.line42.setCurrentIndex(index)
        self.text42 = QtWidgets.QLabel()
        self.text42.setText("Remember Aspect Per Video")
        self.player_list.append('restore_aspect')
        
        self.line43 = QtWidgets.QLineEdit()
        self.line43.setPlaceholderText(str(ui.cache_pause_seconds) + ' (In Seconds)')
        msg = '<html>Stop this many seconds before starting out again when run\
                out of cache</html>'
        self.text43 = QtWidgets.QLabel()
        self.text43.setText("Cache Pause Seconds")
        self.text43.setToolTip(msg)
        self.player_list.append('cache_pause_seconds')
        
        self.line44 = QtWidgets.QLineEdit()
        if len(ui.playback_engine) > 2:
            extra_players = [i for i in ui.playback_engine if i not in ['mpv', 'mplayer']]
            extra_string = ','.join(extra_players)
        else:
            extra_string = 'None'
        self.line44.setPlaceholderText(
            "{} (Comma separated list of external players commands)".format(
                extra_string
                )
            )
        msg = ("<html>Comma Separated list of external players like vlc, kodi etc...\
                Users can also write MPV, MPLAYER in capital letters here,\
                which will open videos in cli versions of mpv and mplayer.\
                The list will be available in sidebar.</html>")
        self.text44 = QtWidgets.QLabel()
        self.text44.setText("Extra Players")
        self.text44.setToolTip(msg)
        self.player_list.append('playback_engine')
        
        self.line45 = QtWidgets.QLineEdit()
        self.line45.setPlaceholderText("{}".format(ui.screenshot_directory))
        self.text45 = QtWidgets.QLabel()
        self.text45.setText("Screenshot Directory")
        self.player_list.append('screenshot_directory')
        self.btn45 = QtWidgets.QPushButton()
        self.btn45.setText('  Set  ')
        self.btn45.clicked.connect(partial(self.set_folder, self.line45, 'screenshot_directory'))
        
        self.line46 = QtWidgets.QComboBox()
        self.line46.addItem("False")
        self.line46.addItem("True")
        index = self.line46.findText(str(ui.gapless_playback))
        self.line46.setCurrentIndex(index)
        self.text46 = QtWidgets.QLabel()
        self.text46.setText("Gapless Playback")
        self.player_list.append('gapless_playback')
        msg = 'Experimental. Useful for playlist containing local files and for \
               aceesing media server library in p2p mode. Do not use it on playlist\
               with mix of local files and network streams'
        self.text46.setToolTip('<html>{}</html>'.format(msg))
        
        self.line47 = QtWidgets.QComboBox()
        self.line47.addItem("False")
        self.line47.addItem("True")
        index = self.line47.findText(str(ui.gapless_network_stream))
        self.line47.setCurrentIndex(index)
        self.text47 = QtWidgets.QLabel()
        self.text47.setText("Gapless Network Stream")
        self.player_list.append('gapless_network_stream')
        msg = 'Experimental. Gapless Playback of Network streams'
        self.text47.setToolTip('<html>{}</html>'.format(msg))
        
        self.line48 = QtWidgets.QComboBox()
        self.line48.addItem("False")
        self.line48.addItem("True")
        index = self.line48.findText(str(ui.use_single_network_stream))
        self.line48.setCurrentIndex(index)
        self.text48 = QtWidgets.QLabel()
        self.text48.setText("Use Single Network Stream For\nGapless Playback")
        self.text48.setWordWrap(True)
        self.player_list.append('use_single_network_stream')
        msg = "Setting it True (Default) will Disable separate audio and video files.\
        Useful only for gapless playback and prefetching of network streams.\
        This option won't be of any use if gapless playback of network stream is disabled.\
        For experiment, Try setting it to False and see what happens with gapless\
        playback, if ytdl fetches separate audio and video streams."
        self.text48.setToolTip('<html>{}</html>'.format(msg))
        
        self.line49 = QtWidgets.QTextEdit()
        msg = ("Few Tips:\n1. Apart from remembering volume and aspect ratio per video, \
              the application remembers audio and subtitle track by default. \
              It also remembers last quit position for every video in the History\
              section. If user will watch video from history then it will be played\
              from last position. If user wants the application to remember last quit\
              position for videos in other sections, then while quitting mpv/mplayer\
              they have to use key 'shift+q' instead of 'q'.\
              \n\n2. Use key 'w' on playlist items to toggle their watch/unwatch\
              status. Series having items with watch status are included in history\
              section.\
              \n\n3. Both titlelist and playlist columns have contextmenus with variety of\
              features including metadata fetching for series and movies.\
              \n4. When on titlelist, use keys ctrl+up or ctrl+right to fetch metadata from\
              tvdb. When on playlist use keys F8 or F7 to fetch episode information.\
              \n\n5. If metadata is not found, then directly focus on title and from\
              its contextmenu directly go to reviews->tvdb using internal browser. Contextmenu\
              of internal browser has been tweaked to facilitate fetching metadata.\
              \n\n6. For better metadata fetching, rename title entries with proper\
              name using key F2. Episodes also needs to be renamed properly according\
              to standard convention. For better match use episode names in a format\
              mentioned below.\
              \n\n7. Episodes can be mass renamed in the database without affecting names of\
              original files. Some tips, shortcuts and options on renaming episodes can be found\
              in playlist contextmenu. ")
        msg = re.sub(' +', ' ', msg)
        
        msg1 = ('For fetching Episode Summary from TVDB, first focus either \
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
                   needs to be focussed.\
                   \n\nIf application does not find episodes names in regular convention\
                    then it will find metadata according to its order. First entry of \
                    playlist will be treated as first episode and last entry will be\
                    treated as last episode of the series, and then entries will be\
                    mapped with tvdb databse. Ordering option for episodes can be found by\
                    pressing filter/order button (or use shortcut ctrl+f). \
                    For manual order use page-up and page-down keys')
                    
        msg1 = re.sub('  +', ' ', msg1)
        msg = msg + '\n\n' + msg1
        
        self.line49.setText(msg)
        self.line49.setMaximumHeight(ui.height_allowed)
        for i, j in enumerate(self.player_list):
            index = i+1
            text = eval('self.text4{}'.format(index))
            line = eval('self.line4{}'.format(index))
            if j == 'screenshot_directory':
                self.gl6.addWidget(text, index, 0, 1, 1)
                self.gl6.addWidget(line, index, 1, 1, 1)
                btn = eval('self.btn4{}'.format(index))
                self.gl6.addWidget(btn, index, 2, 1, 1)
            else:
                self.gl6.addWidget(text, index, 0, 1, 1)
                self.gl6.addWidget(line, index, 1, 1, 2)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j, 'player_settings'))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j, 'player_settings'))
                
        self.gl6.addWidget(self.line49, index+1, 0, 1, 3)
        
    
    def configsettings(self):
        self.line501 = QtWidgets.QTextEdit()
        self.gl7.addWidget(self.line501, 0, 0, 1, 3)
        msg = '<html>Use this config file, otherwise global config file will be used</html>'
        self.checkbox = QtWidgets.QCheckBox("Use This Config File")
        self.checkbox.stateChanged.connect(self.use_config_file)
        self.checkbox.setToolTip(msg)
        self.gl7.addWidget(self.checkbox, 1, 0, 1, 1)
        if ui.use_custom_config_file:
            self.checkbox.setChecked(True)
        mpvlist = self.basic_params(player='mpv')
        mpvstr = '\n'.join(mpvlist)
        self.line501.setText(mpvstr) 
        
        self.btn_default_settings = QtWidgets.QPushButton('Default Settings')
        self.gl7.addWidget(self.btn_default_settings, 1, 1, 1, 1)
        self.btn_default_settings.clicked.connect(self.get_default_config_settings)
        
        self.btn_confirm = QtWidgets.QPushButton('Save Changes')
        self.gl7.addWidget(self.btn_confirm, 1, 2, 1, 1)
        self.btn_confirm.clicked.connect(self.save_config_settings)
        
    def apply_tab_shortcuts(self):
        self.line601 = QtWidgets.QTextEdit()
        self.gl8.addWidget(self.line601, 0, 0, 1, 2)
        
        if os.path.isfile(ui.custom_key_file) and os.stat(ui.custom_key_file).st_size:
            lines = open_files(ui.mpv_input_conf, True)
            lines = [i.strip() for i in lines if i.strip()]
            text = self.get_default_shortcuts_in_text(ui.tab_5.mpv_default, lines)
            self.line601.setText(text) 
        else:
            self.get_default_shortcuts_settings()
        
        self.btn_shortcut_default = QtWidgets.QPushButton('Default Settings')
        self.gl8.addWidget(self.btn_shortcut_default, 1, 0, 1, 1)
        self.btn_shortcut_default.clicked.connect(self.get_default_shortcuts_settings)
        
        self.btn_shortcut_confirm = QtWidgets.QPushButton('Save Changes')
        self.gl8.addWidget(self.btn_shortcut_confirm, 1, 1, 1, 1)
        self.btn_shortcut_confirm.clicked.connect(self.save_shortcut_settings)
    
    def get_default_config_settings(self):
        mpvlist = self.basic_params(player='mpv', mode='default')
        mpvstr = '\n'.join(mpvlist)
        self.line501.setText(mpvstr)
    
    def get_default_shortcuts_settings(self):
        mpv_default = ui.tab_5.key_map.get_default_keys()
        _, input_conf_list = ui.tab_5.key_map.get_custom_keys(ui.mpv_input_conf)
        text = self.get_default_shortcuts_in_text(mpv_default, input_conf_list)
        self.line601.setText(text) 
    
    def get_default_shortcuts_in_text(self, mpv_default, input_conf_list):
        text = '#shortcut_key command. For executing multiple commands per key separate them with double colon "::"'
        for key in mpv_default:
            if not text:
                text = key + ' ' + mpv_default[key]
            else:
                text = text + '\n' + key + ' ' + mpv_default[key]
                
        text = text.replace('\n', '\n\n')
        for i in input_conf_list:
            if i.startswith('#'):
                text = text + '\n' + i
            else:
                text = text + '\n#' + i
        return text
        
    def save_shortcut_settings(self):
        text = self.line601.toPlainText()
        text_lines = text.split('\n')
        new_lines = []
        for i in text_lines:
            i = i.strip()
            if i and not i.startswith('#'):
                new_lines.append(i)
        write_files(ui.custom_key_file, new_lines, line_by_line=True)
        new_dict, _ = ui.tab_5.key_map.get_custom_keys(ui.custom_key_file)
        ui.tab_5.mpv_default = new_dict.copy()
        
    def save_config_settings(self):
        txt = self.line501.toPlainText()
        txt_list = txt.split('\n')
        mpv_cmd_dict = {}
        mpv_cmd = []
        ui.mpvplayer_string_list.clear()
        for i in txt_list:
            i = i.strip()
            mpv_cmd.append(i)
            if i and not i.startswith('#'):
                i = re.sub('#[^\n]*', '', i)
                if '=' in i:
                    j = i.split('=')[1]
                    if not j:
                        i = ''
                if i and i not in ui.mpvplayer_string_list:
                    ui.mpvplayer_string_list.append('--'+i)
        write_files(self.config_file_name, mpv_cmd, line_by_line=True)
        mpv_cmd_dict.update({'file':mpv_cmd})
        mpv_cmd_dict.update({'str':ui.mpvplayer_string_list})
        try:
            with open(self.config_file_name, 'wb') as config_file:
                pickle.dump(mpv_cmd_dict, config_file)
        except Exception as err:
            logger.error(err)
            
    def use_config_file(self):
        if self.checkbox.isChecked():
            ui.use_custom_config_file = True
        else:
            ui.use_custom_config_file = False
        change_opt_file(self.option_file, 'USE_CUSTOM_CONFIG_FILE=',
                        'USE_CUSTOM_CONFIG_FILE={}'.format(ui.use_custom_config_file))
        
    def basic_params(self, player=None, mode=None):
        mpv_cmd = []
        if mode is None:
            try:
                if os.path.isfile(self.config_file_name):
                    with open(self.config_file_name, 'rb') as config_file:
                        mpv_cmd_dict = pickle.load(config_file)
                        mpv_cmd = mpv_cmd_dict['file']
            except Exception as err:
                logger.error(err)
        
        if not ui.video_outputs or not ui.audio_outputs:
            ui.video_outputs, ui.audio_outputs = self.get_audio_video_outputs()
            change_opt_file(self.option_file, 'AUDIO_OUTPUTS=', 'AUDIO_OUTPUTS={}'.format(ui.audio_outputs))
            change_opt_file(self.option_file, 'VIDEO_OUTPUTS=', 'VIDEO_OUTPUTS={}'.format(ui.video_outputs))
        if not mpv_cmd:
            mpv_cmd = [
                "##Define Custom Settings Here for mpv. Comment out lines as per need",
                '##Write string with space in double quotes',
                "##Available Video Outputs (vo): {}".format(ui.video_outputs),
                "vo=gpu",
                "##Available Audio Outputs (ao): {}".format(ui.audio_outputs),
                "ao=pulse",
                '##Set OSD level',
                '#osd-level=1',
                "#Cache Settings",
                "cache=auto",
                'cache-secs=120',
                "cache-default=100000",
                "cache-initial=0",
                "cache-seek-min=100",
                "cache-pause",
                "##Set Video Aspect: cycle through aspect ratio using key a",
                "video-aspect=-1",
                "##Set Audio and Subtitle language options",
                "#alang=mr,hi,ja,jpn,en,eng",
                "#slang=en,eng",
                "##For smooth motion",
                "#video-sync=display-resample",
                "#interpolation=yes",
                "#tscale=oversample",
                '##Subtitle Options',
                '#sub-font=',
                '#sub-font-size=',
                '#sub-color=',
                '#sub-border-color=',
                '#sub-border-size=',
                '#sub-shadow-offset=',
                '#sub-shadow-offset=',
                '#sub-shadow-color=',
                '#sub-spacing=',
                '#blend-subtitle=yes',
                '##Setup screenshot directory. Take screenshot using keys s, S',
                '#screenshot-format=png',
                '#screenshot-png-compression=9',
                '#screenshot-directory="{}"'.format(ui.tmp_download_folder),
                '##Define user agent string, sometimes necessary for streaming videos',
                '#user-agent="Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:58.0) Gecko/20100101 Firefox/58.0"'
                ]
        return mpv_cmd
        
    def get_audio_video_outputs(self, val=None):
        output_audio = ''
        output_video = ''
        for value in ['--vo', '--ao']:
            output = None
            try:
                if os.name == 'posix':
                    output = subprocess.check_output(['mpv', value, 'help'])
                else:
                    output = subprocess.check_output(['mpv', value, 'help'], shell=True)
                output = output.decode('utf-8')
            except Exception as err:
                logger.error(err)
            if output:
                output_list = output.split('\n')
                for i in output_list:
                    i = i.strip()
                    if ':' in i:
                        i = i.split(':')[0].strip()
                    if i and not i.lower().startswith('available'):
                        if value == '--vo':
                            if not output_video:
                                output_video = i
                            else:
                                output_video = output_video + ', ' + i
                        else:
                            if not output_audio:
                                output_audio = i
                            else:
                                output_audio = output_audio + ', ' + i
        return (output_video, output_audio)
        
    def set_folder(self, widget, var_name=None):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
                    MainWindow, 'Add Directory',
                    ui.last_dir
                    )
        if fname:
            if os.path.exists(fname):
                ui.last_dir = fname
                widget.setText(fname)
                if var_name == 'torrent_download_folder':
                    self.line_entered(widget, var_name, option='torrent')
                else:
                    self.line_entered(widget, var_name)
                
    def check_and_set_ip(self, widget, var_name):
        try:
            ip = get_lan_ip()
            text = ''
            if var_name == 'local_ip_stream':
                text = ip + ':' + str(ui.local_port_stream)
            elif var_name == 'local_ip':
                text = ip + ':' + str(ui.local_port)
            if text:
                widget.setText(text)
                if var_name == 'local_ip':
                    self.line_entered(widget, var_name, option='torrent')
                else:
                    self.line_entered(widget, var_name)
        except Exception as err:
            logger.error(err)
            msg = 'Not able to find. Try Setting it up manually in the format ip:port'
            widget.setText(msg)
    
    def change_playlist_viewmode(self):
        if ui.list_with_thumbnail:
            ui.widget_style.change_list2_style(mode=True)
            if not ui.float_window.isHidden():
                ui.list2.setMaximumHeight(16777215)
            ui.update_list2()
        else:
            ui.widget_style.change_list2_style(mode=False)
            if not ui.float_window.isHidden():
                if ui.new_tray_widget.cover_mode.text() == ui.player_buttons['down']: 
                    ui.list2.setMaximumHeight(30)
                else:
                    ui.list2.setMaximumHeight(16777215)
            ui.update_list2()

    def combobox_changed(self, widget, var_name=None, option=None):
        obj_name = widget.objectName()
        obj_value = widget.currentText()
        if var_name == 'use_single_network_stream':
            param = 'USE_SINGLE_NETWORK_STREAM='
        else:
            param = obj_name + '='
        param_value = param + obj_value
        logger.debug('{}::{}::{}::{}'.format(param, param_value, var_name, obj_value))
        if obj_value.lower() in ['true', 'false']:
            if var_name == 'window_frame':
                ui.tray_widget.right_menu._remove_frame()
            else:
                exec('ui.{} = {}'.format(var_name, obj_value.title()))
                if var_name == 'list_with_thumbnail':
                    self.change_playlist_viewmode()
        else:
            if var_name == 'keep_background_constant':
                if obj_value.lower() == 'yes':
                    ui.keep_background_constant = True
                else:
                    ui.keep_background_constant = False
            elif var_name == 'logging_module':
                if obj_value.lower() == 'on':
                    ui.logging_module = True
                    ui.logger.disabled = False
                else:
                    ui.logging_module = False
                    ui.logger.disabled = True
            elif var_name == 'player_theme':
                ui.player_theme = obj_value.lower()
                if ui.player_theme == 'dark' or ui.player_theme == 'default':
                    self.appeareance_setdefault()
            else:
                exec('ui.{} = "{}"'.format(var_name, obj_value))
        if option == 'torrent':
            change_opt_file(self.torrent_config, param, param_value)
        else:
            change_opt_file(self.option_file, param, param_value)
            
        if option == 'appearance':
            self.post_changes(var_name)
            
    def line_entered(self, widget, var_name=None, option=None):
        obj_name = widget.objectName()
        obj_value = widget.text()
        param = obj_name + '='
        param_value = param + obj_value
        print(param, param_value, var_name, obj_value)
        widget.clear()
        if obj_value.isnumeric() or len(obj_value) < 10 or var_name == 'global_font':
            widget.setPlaceholderText(obj_value)
        else:
            widget.setText(obj_value)
        if var_name == 'local_ip_stream':
            if ':' in obj_value:
                ip, port = obj_value.rsplit(':', 1)
                ui.local_ip_stream = ip
                ui.local_port_stream = int(port)
        elif var_name == 'local_ip':
            if ':' in obj_value:
                ip, port = obj_value.rsplit(':', 1)
                ui.local_ip = ip
                ui.local_port = int(port)
        elif var_name == 'torrent_download_limit' and obj_value.isnumeric():
            ui.torrent_download_limit = int(obj_value) * 1024
        elif var_name == 'torrent_upload_limit' and obj_value.isnumeric():
            ui.torrent_upload_limit = int(obj_value) * 1024
        elif var_name == 'setuploadspeed' and obj_value.isnumeric():
            ui.setuploadspeed = int(obj_value)
        elif var_name == 'global_font_size' and obj_value.isnumeric():
            ui.global_font_size = int(obj_value)
        elif var_name == 'playback_engine':
            extra_players = obj_value.split(',')
            for extra_player in extra_players:
                if (extra_player not in ui.playback_engine
                        and extra_player.lower() != 'none'):
                    ui.playback_engine.append(extra_player)
        elif var_name == 'ytdl_path':
            k = obj_value.lower()
            if k == 'default':
                ui.ytdl_path = 'default'
            elif k == 'automatic':
                if os.name == 'posix':
                    ui.ytdl_path = os.path.join(ui.home_folder, 'src', 'ytdl')
                elif os.name == 'nt':
                    ui.ytdl_path = os.path.join(ui.home_folder, 'src', 'ytdl.exe') 
            else:
                if os.path.exists(obj_value):
                    ui.ytdl_path = obj_value
                else:
                    ui.ytdl_path = 'default'
        elif var_name == 'cache_pause_seconds' and obj_value.isnumeric():
            ui.cache_pause_seconds = int(obj_value)
        else:
            exec('ui.{} = "{}"'.format(var_name, obj_value))
        if option == 'torrent':
            change_opt_file(self.torrent_config, param, param_value)
        else:
            change_opt_file(self.option_file, param, param_value)
            
        if option == 'appearance':
            self.post_changes(var_name)
            
    def post_changes(self, var_name):
        if ui.player_theme.istitle():
            ui.player_theme = ui.player_theme.lower()
        msg = 'Restart Application, if changes are not applied'
        if var_name == 'player_theme' or 'font' in var_name or 'color' in var_name:
            ui.apply_new_font()
            ui.apply_new_style()
        ui.progressEpn.setValue(0)
        if var_name == 'player_theme' and ui.player_theme == 'system':
            msg = 'System Theme requires application restart'
        ui.progressEpn.setFormat((msg))
            
    def add_folder_to_library(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
                MainWindow, 'open folder', ui.last_dir)
        if fname:
            ui.last_dir = fname
            logger.info(ui.last_dir)
            logger.info(fname)
            self.list_library.addItem(fname)
            write_files(self.library_file_name, fname, line_by_line=True)
    
    def remove_folder_from_library(self):
        index = self.list_library.currentRow()
        item  = self.list_library.item(index)
        if item:
            lines = open_files(self.library_file_name, True)
            logger.info(self.list_library.item(index).text())
            self.list_library.takeItem(index)
            del item
            del lines[index]
            write_files(self.library_file_name, lines, line_by_line=True)
