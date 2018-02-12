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
import ipaddress
import subprocess
from functools import partial
from PyQt5 import QtWidgets, QtCore
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
        self.addTab(self.tab_app, 'Appearance')
        self.addTab(self.tab_library, ' Library ')
        self.addTab(self.tab_server, 'Media Server')
        self.addTab(self.tab_torrent, 'Torrent')
        self.addTab(self.tab_meta, ' Other Essential ')
        self.addTab(self.tab_close, ' Close ')
        self.option_file = os.path.join(ui.home_folder, 'other_options.txt')
        self.library_file_name = os.path.join(ui.home_folder, 'local.txt')
        self.hide_label = False
        self.tabs_present = False
        self.setMouseTracking(True)
        
    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        if ui.search_on_type_btn.isHidden():
            self.setFocus()
    
    def tab_changed(self):
        index = self.currentIndex()
        if self.tabText(index) == ' Close ':
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
            if not ui.label.isHidden():
                ui.label_new.hide()
                ui.label.hide()
                ui.text.hide()
                self.hide_label = True
            self.setCurrentIndex(ui.settings_tab_index)
            if not self.tabs_present:
                self.appeareance()
                self.mediaserver()
                self.torrentsettings()
                self.othersettings()
                self.library()
                self.tabs_present = True
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
            self.setCurrentIndex(1)
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()    
        
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
    
    def appeareance(self):
        self.param_list = []
        self.line1 = QtWidgets.QComboBox()
        for i in ui.theme_list:
            self.line1.addItem(i)
        index = self.line1.findText(ui.player_theme.title())
        self.line1.setCurrentIndex(index)
        self.text1 = QtWidgets.QLabel()
        self.text1.setText("Theme")
        self.param_list.append('player_theme')
        
        self.line2 = QtWidgets.QLineEdit()
        self.line2.setPlaceholderText(ui.global_font)
        self.text2 = QtWidgets.QLabel()
        self.text2.setText("Global Font")
        self.param_list.append('global_font')
        
        self.line3 = QtWidgets.QLineEdit()
        self.line3.setPlaceholderText(str(ui.global_font_size))
        self.text3 = QtWidgets.QLabel()
        self.text3.setText("Global Font Size")
        self.param_list.append('global_font_size')
        
        self.line4 = QtWidgets.QComboBox()
        self.line4.addItem("True")
        self.line4.addItem("False")
        index = self.line4.findText(str(ui.font_bold))
        self.line4.setCurrentIndex(index)
        self.text4 = QtWidgets.QLabel()
        self.text4.setText("Font Bold")
        self.param_list.append('font_bold')
        
        self.line5 = QtWidgets.QLineEdit()
        self.line5.setPlaceholderText(ui.thumbnail_text_color)
        self.text5 = QtWidgets.QLabel()
        self.text5.setText("Thumbnail Text Color")
        self.param_list.append('thumbnail_text_color')
        
        self.line6 = QtWidgets.QLineEdit()
        self.line6.setPlaceholderText(ui.thumbnail_text_color_focus)
        self.text6 = QtWidgets.QLabel()
        self.text6.setText("Thumbnail Text Color Focus")
        self.param_list.append('thumbnail_text_color_focus')
        
        self.line7 = QtWidgets.QLineEdit()
        self.line7.setPlaceholderText(ui.list_text_color)
        self.text7 = QtWidgets.QLabel()
        self.text7.setText("List Text Color")
        self.param_list.append('list_text_color')
        
        self.line8 = QtWidgets.QLineEdit()
        self.line8.setPlaceholderText(ui.list_text_color_focus)
        self.text8 = QtWidgets.QLabel()
        self.text8.setText("List Text Color Focus")
        self.param_list.append('list_text_color_focus')
        
        self.line9 = QtWidgets.QComboBox()
        for i in range(0, 10):
            self.line9.addItem(str(i))
        index = self.line9.findText(str(ui.image_fit_option_val))
        self.line9.setCurrentIndex(index)
        self.text9 = QtWidgets.QLabel()
        self.text9.setText("Image Fit Option")
        self.param_list.append('image_fit_option_val')
        
        self.line10 = QtWidgets.QComboBox()
        self.line10.addItem("No")
        self.line10.addItem("Yes")
        if ui.keep_background_constant:
            val = 'Yes'
        else:
            val = 'No'
        index = self.line10.findText(val)
        self.line10.setCurrentIndex(index)
        self.text10 = QtWidgets.QLabel()
        self.text10.setText("Keep Background Constant")
        self.param_list.append('keep_background_constant')
        
        for i, j in enumerate(self.param_list):
            index = i+1
            text = eval('self.text{}'.format(index))
            line = eval('self.line{}'.format(index))
            self.gl1.addWidget(text, index, 0, 1, 1)
            self.gl1.addWidget(line, index, 1, 1, 1)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j))
    
    def combobox_changed(self, widget, var_name=None):
        obj_name = widget.objectName()
        obj_value = widget.currentText()
        param = obj_name + '='
        param_value = param + obj_value
        print(param, param_value, var_name, obj_value)
        if obj_value.lower() in ['true', 'false']:
            exec('ui.{} = {}'.format(var_name, obj_value.title()))
        else:
            if var_name == 'keep_background_constant':
                if obj_value.lower() == 'yes':
                    ui.keep_background_constant = True
                else:
                    ui.keep_background_constant = False
            if var_name == 'logging_module':
                if obj_value.lower() == 'on':
                    ui.logging_module = True
                    ui.logger.disabled = False
                else:
                    ui.logging_module = False
                    ui.logger.disabled = True
            else:
                exec('ui.{} = "{}"'.format(var_name, obj_value))
        change_opt_file(self.option_file, param, param_value)
        
    def line_entered(self, widget, var_name=None):
        obj_name = widget.objectName()
        obj_value = widget.text()
        param = obj_name + '='
        param_value = param + obj_value
        print(param, param_value, var_name, obj_value)
        widget.clear()
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
        elif var_name == 'playback_engine':
            extra_players = obj_value.split(',')
            for extra_player in extra_players:
                if (extra_player not in ui.playback_engine
                        and extra_player.lower() != 'none'):
                    ui.playback_engine.append(extra_player)
        else:
            exec('ui.{} = "{}"'.format(var_name, obj_value))
        change_opt_file(self.option_file, param, param_value)
    
    def mediaserver(self):
        self.media_param = []
        self.line11 = QtWidgets.QLineEdit()
        self.line11.setText("{}:{}".format(ui.local_ip_stream, ui.local_port_stream))
        self.text11 = QtWidgets.QLabel()
        self.text11.setText("Local Stream IP")
        self.btn11 = QtWidgets.QPushButton()
        self.btn11.setText(" Check IP ")
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
                self.gl2.addWidget(line, i, 1, 1, 2)
            obj_name = text.text().upper().replace(' ', '_')
            line.setObjectName(obj_name)
            if isinstance(line, QtWidgets.QComboBox):
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j))
            
    def torrentsettings(self):
        self.torrent_param = []
        self.line21 = QtWidgets.QLineEdit()
        self.line21.setText("{}:{}".format(ui.local_ip, ui.local_port))
        self.text21 = QtWidgets.QLabel()
        self.text21.setText("Torrent Stream IP")
        self.torrent_param.append('local_ip')
        
        self.btn21 = QtWidgets.QPushButton()
        self.btn21.setText("Check IP")
        self.line22 = QtWidgets.QLineEdit()
        self.line22.setPlaceholderText(ui.torrent_download_folder)
        self.text22 = QtWidgets.QLabel()
        self.text22.setText("Torrent Download Folder")
        self.btn22 = QtWidgets.QPushButton()
        self.btn22.setText(" Set Location ")
        self.btn22.clicked.connect(partial(self.set_folder, self.line22, 'torrent_download_folder'))
        self.torrent_param.append('torrent_download_folder')
        
        self.line23 = QtWidgets.QLineEdit()
        self.line23.setPlaceholderText("{} (in KB, 0 means unlimited )".format(ui.torrent_upload_limit))
        self.text23 = QtWidgets.QLabel()
        self.text23.setText("Torrent Upload Rate")
        self.torrent_param.append('torrent_upload_limit')
        
        self.line24 = QtWidgets.QLineEdit()
        self.line24.setPlaceholderText("{}".format(ui.torrent_download_limit))
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
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j))
    
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
        
        self.line38 = QtWidgets.QComboBox()
        self.line38.addItem('False')
        self.line38.addItem('True')
        index = self.line38.findText(str(ui.custom_mpv_input_conf))
        self.line38.setCurrentIndex(index)
        self.text38 = QtWidgets.QLabel()
        self.text38.setText("MPV Input Conf")
        self.other_settings.append('custom_mpv_input_conf')
        
        self.line39 = QtWidgets.QLineEdit()
        if len(ui.playback_engine) > 2:
            extra_players = [i for i in ui.playback_engine if i not in ['mpv', 'mplayer']]
            extra_string = ','.join(extra_players)
        else:
            extra_string = 'None'
        self.line39.setPlaceholderText(
            "{} (Comma separated list of external players eg: vlc, kodi etc..)".format(
                extra_string
                )
            )
        self.text39 = QtWidgets.QLabel()
        self.text39.setText("Extra Players")
        self.other_settings.append('playback_engine')
        
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
                line.currentIndexChanged['int'].connect(partial(self.combobox_changed, line, j))
            elif isinstance(line, QtWidgets.QLineEdit):
                line.returnPressed.connect(partial(self.line_entered, line, j))
                
    def set_folder(self, widget, var_name=None):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
                    MainWindow, 'Add Directory',
                    ui.last_dir
                    )
        if fname:
            if os.path.exists(fname):
                ui.last_dir = fname
                widget.setText(fname)
                self.line_entered(widget, var_name)
                
