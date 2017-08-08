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
import hashlib
import ipaddress
import subprocess
from PyQt5 import QtWidgets
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
            self.img_opt.setToolTip('Use Ctrl+1 to Ctrl+8 keyboard shortcuts to Experiment with various background image modes. \n1:Fit To Screen\n2:Fit To Width\n3:Fit To Height\n4:Fit Upto Playlist\nRestart to see the effect OR if want to see immediate effect, then directly use keyboard shortcuts')
            img_opt_arr = ['IMAGE FIT OPTIONS', '1', '2', '3', '4', '5', '6', '7', '8']
            for i in img_opt_arr:
                self.img_opt.addItem(i)
            img_val = str(self.ui.image_fit_option_val)
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
