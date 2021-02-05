"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import urllib.parse
import re
import random
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtWidgets
from player_functions import ccurl, send_notification


class LoginWidget(QtWidgets.QDialog):

    def __init__(self, parent=None, server=None):
        super(LoginWidget, self).__init__(parent)
        self.parent = parent
        self.server = server
        self.server_ip = QtWidgets.QLineEdit(self)
        self.text_name = QtWidgets.QLineEdit(self)
        self.text_pass = QtWidgets.QLineEdit(self)
        self.server_ip.setPlaceholderText('FULL IP ADDRESS OF SERVER')
        self.text_name.setPlaceholderText('USER')
        self.text_pass.setPlaceholderText('PASSWORD')
        if self.server.server_name:
            self.server_ip.setText(self.server.server_name)
        self.text_pass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_login = QtWidgets.QPushButton('Login', self)
        self.btn_login.clicked.connect(self.handleLogin)
        self.setWindowTitle('Credentials Required')
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.server_ip)
        layout.addWidget(self.text_name)
        layout.addWidget(self.text_pass)
        layout.addWidget(self.btn_login)
        self.auth_info = ''
        self.auth_64 = ''
        self.show()
        self.found = True

    def handleLogin(self):
        self.hide()
        text_val = self.text_name.text()
        pass_val = self.text_pass.text()
        self.auth_info = text_val+':'+pass_val
        url = self.server_ip.text()
        if url:
            if not url.endswith('/'):
                url = url+'/'
            if not url.startswith('http'):
                send_notification('Enter full IP address starting with http/https properly')
            else:
                content = ccurl(
                        '{0}get_all_category.htm#-c#{1}'.format(url, self.server.cookie_file),
                        user_auth=self.auth_info, verify_peer=False
                        )
                print(content, '>>>>>')
                if ('Access Not Allowed, Authentication Failed' in content or
                        'You are not authorized to access the content' in content):
                    self.server.login_success = False
                    send_notification('Authentication Failed. Either Username or Password is incorrect')
                elif not content:
                    send_notification('Curl failure: may be server is not running or misconfigured')
                else:
                    self.server.passwd = self.auth_info
                    self.server.url = url
                    self.server.login_success = True
                    send_notification('Login Success. Now click on Login Again')
                    with open(self.server.server_list, 'w') as f:
                        f.write(self.server.url) 
                        self.server.server_name = url
        else:
            send_notification('Server IP Address Needed')

class MyServer:
    
    def __init__(self, tmp):
        self.hdr = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'
        self.tmp_dir = tmp
        self.cookie_file = os.path.join(tmp, 'myserver.txt')
        self.site_dict = {}
        self.site_arr = []
        self.site = None
        self.opt = None
        self.url = None
        self.passwd = ':'
        self.login_success = None
        self.login_widget = None
        self.server_list = os.path.join(tmp, 'server_list.txt')
        self.server_name = None
        
    def getOptions(self):
            criteria = ['Login', 'Logout', 'Discover', 'History', 'newversion']
            return criteria
            
    def getFinalUrl(self, name, epn, mirror, quality):
        if self.url:
            url = self.url+'quality='+quality
            content = ccurl(
                    '{0}#-b#{1}'.format(url, self.cookie_file),verify_peer=False
                    )
            print(content)
        final = epn
        if '\t' in epn:
            final = epn.split('\t')[1]
        return final
        
    def search(self, name):
        m = ['Not Available']
        return m
        
    def handle_login(self, server_name=None):
        if os.path.isfile(self.server_list) and not server_name:
            with open(self.server_list, 'r') as f:
                self.server_name = f.read()
        elif server_name:
            self.server_name = server_name
        if not self.url:
            self.login_widget = LoginWidget(server=self)
            self.login_widget.show()
            #self.login_widget.setWindowModality(QtCore.Qt.WindowModal)
        else:
            content = ccurl(
                '{0}get_all_category.htm#-c#{1}'.format(self.url, self.cookie_file),
                user_auth=self.passwd, verify_peer=False
                )
            print(content, '>>>>>')
            if ('Access Not Allowed, Authentication Failed' in content 
                    or 'You are not authorized to access the content' in content):
                self.login_success = False
                self.login_widget = LoginWidget(server=self)
                self.login_widget.show()
            elif not content:
                send_notification('Curl failure: may be server is not running or misconfigured')
            else:
                self.login_success = True
    
    def getCompleteList(self, opt, genre_num=None, next_login=None):
        print(self.site, opt, '--')
        m = []
        if opt.lower() == 'login':
            self.handle_login()
            print(self.login_success, 'login_success')
            if self.login_success:
                content = ccurl(
                    '{0}get_all_category.htm#-b#{1}'.format(self.url, self.cookie_file),
                    user_auth=self.passwd, verify_peer=False
                )
                print(content, '>>>>>160')
                soup = BeautifulSoup(content, 'lxml')
                print(soup.prettify())
                link_text = soup.find('div', {'id':'site_option'})
                print(link_text)
                if link_text:
                    link_text = link_text.text
                    arr = re.search('Video:[^"]*', link_text).group()
                    arr_split = arr.split(';')
                    print(arr_split)
                    old_j = None
                    site_opt = []
                    for l,i in enumerate(arr_split):
                        if i:
                            j, k = i.split(':')
                            if old_j != j:
                                old_j = j
                                site_opt.clear()
                                if old_j not in self.site_arr:
                                    self.site_arr.append(old_j)
                            site_opt.append(k)
                            if site_opt:
                                self.site_dict.update({old_j:site_opt.copy()})
                print(self.site_dict)
                try:
                    i = self.site_arr.index('MyServer')
                    del self.site_arr[i]
                    del self.site_dict['MyServer']
                except Exception as err:
                    print(err, '--111---')
                m = self.site_arr.copy()
                m.append('<--')
                m.append(0)
        elif opt in self.site_arr:
            self.site = opt
            m = self.site_dict.get(opt).copy()
            if self.site.lower() == 'playlists':
                m.append(1)
            else:
                m.append('<----')
                m.append(0)
        elif opt == '<----' or opt == '<--':
            self.site = None
            self.opt = None
            if opt == '<----':
                m = self.site_arr.copy()
                m.append('<--')
            else:
                m = ['Login', 'Logout', 'Discover', 'History']
            m.append(0)
        elif opt == 'History':
            if self.site is None:
                m.append(6)
            else:
                self.opt = opt
                url_new = self.url+urllib.parse.quote(
                    'site={0}&opt={1}'.format(self.site.lower(), self.opt.lower())
                    )
                print(url_new)
                content = ccurl(url_new+'#'+'-b'+'#'+self.cookie_file, verify_peer=False)
                #print(content)
                m = content.split('\n')
                if self.site.lower() == 'video' or self.site.lower() == 'music':
                    m = [i.replace('::::', '\t', 1) for i in m]
                m.append(1)
        elif opt.lower() == 'discover':
            self.opt = opt
            m.append(4)
        elif opt.lower() == 'logout':
            url_new = self.url+'logout'
            content = ccurl(url_new+'#'+'-b'+'#'+self.cookie_file, verify_peer=False)
            self.opt = opt
            self.url = None
            self.passwd = None
            self.login_success = False
            self.site_arr.clear()
            self.site_dict.clear()
            if os.path.isfile(self.cookie_file):
                os.remove(self.cookie_file)
            m.append(5)
        else:
            self.opt = opt
            url_new = self.url+urllib.parse.quote(
                'site={0}&opt={1}'.format(self.site.lower(), self.opt.lower())
                )
            print(url_new)
            content = ccurl(url_new+'#'+'-b'+'#'+self.cookie_file, verify_peer=False)
            #print(content)
            m = content.split('\n')
            if self.site.lower() == 'video' or self.site.lower() == 'music':
                m = [i.replace('::::', '\t', 1) for i in m]
            m.append(1)
        if not m and opt.lower() == 'login':
            m.append(3)
        return m
    
    def get_playlist(self, content):
        lines = content.split('\n')
        length = len(lines)
        i = 0
        m = []
        while i < length:
            try:
                if 'EXTINF' in lines[i]:
                    n_epn = (lines[i].strip()).split(',', 1)[1]
                    n_epn = n_epn.strip()
                    if n_epn.startswith('NONE - '):
                        n_epn = n_epn.replace('NONE - ', '', 1)
                    if n_epn.startswith('-'):
                        n_epn = n_epn.replace('-', '', 1)
                    if '/' in n_epn:
                        n_epn = n_epn.replace('/', '-')
                    n_epn = n_epn.strip()
                    if i+1 < length:
                        entry_epn = n_epn+'\t'+lines[i+1].strip()+'\t'+'NONE'
                        m.append(entry_epn)
                    i = i+2
                else:
                    i = i+1
            except Exception as e:
                print(e)
        return m
    
    def getEpnList(self, name, opt, depth_list, extra_info, siteName, category):
        summary = 'None'
        picn = 'No.jpg'
        record_history = False
        print(self.site, self.opt, opt)
        if self.site:
            if self.site.lower() == 'playlists':
                opt_val = name
                name_val = ''
            else:
                opt_val = self.opt.lower()
                name_val = name
            if self.site.lower() == 'video' or self.site.lower() == 'music':
                name_val = extra_info+'.hash'
            url_new = 'site={0}&opt={1}&s={2}&exact.m3u'.format(self.site.lower(), opt_val, name_val)
            url_new = urllib.parse.quote(url_new)
            url = self.url+url_new
            content = ccurl(url+'#'+'-b'+'#'+self.cookie_file, verify_peer=False)
            m = self.get_playlist(content)
            record_history = True
        elif self.opt == 'Discover':
            self.handle_login(server_name=name)
            m = []
            record_history = False
        else:
            m = []
        return (m, summary, picn, record_history, depth_list)
