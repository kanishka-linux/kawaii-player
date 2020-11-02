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
import sys
import re
import inspect
import shutil
import logging
import hashlib
import base64
import subprocess
import urllib
import platform
import random
import string
from tempfile import mkstemp, mkdtemp
from io import StringIO, BytesIO
try:
    import pycurl
except Exception as err:
    print(err)
from PyQt5 import QtWidgets, QtCore
from get_functions import wget_string, get_ca_certificate

OSNAME = os.name

def send_notification(txt, display=None, code=None):
    try:
        if os.name == 'posix':
            if platform.system().lower() == "linux":
                subprocess.Popen(["notify-send", txt])
            else:
                subprocess.Popen(["terminal-notifier", "-message", txt, "-title", "Kawaii-Player"])
        elif os.name == 'nt' and code == 0:
            print(txt)
        elif os.name == 'nt' and display != 'posix':
            subprocess.Popen(['msg', '/time:3', '*', txt])
    except Exception as e:
        print(e)

def random_string(size):
    chars=string.ascii_uppercase + string.digits
    string_generator = (random.choice(chars) for _ in range(size))
    return ''.join(string_generator)
 
def get_lan_ip():
    if OSNAME == 'posix':
        if platform.system().lower() == "linux":
            a = subprocess.check_output(['ip', 'addr', 'show'])
        else:
            a = subprocess.check_output(['ifconfig'])
        b = str(a, 'utf-8')
        print(b)
        c = re.findall('inet [^ ]*', b)
        final = ''
        for i in c:
            if '127.0.0.1' not in i:
                final = i.replace('inet ', '')
                final = re.sub('/[^"]*', '', final)
        print(c)
        print(final)
        return final
    elif OSNAME == 'nt':
        a = subprocess.check_output(['ipconfig'])
        a = str(a, 'utf-8').lower()
        b = re.search('ipv4[^\n]*', a).group()
        c = re.search(':[^\n]*', b).group()
        final = c[1:].strip()
        print(c)
        return final

def qmsg_message(txt):
    print(txt)
    #root = tkinter.Tk()
    #width = root.winfo_screenwidth()
    #height = root.winfo_screenheight()
    #print(width, height, '--screen--tk--')
    msg = QtWidgets.QMessageBox()
    msg.setGeometry(0, 0, 50, 20)
    #msg.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
    msg.setWindowModality(QtCore.Qt.NonModal)
    msg.setWindowTitle("Kawaii-Player MessageBox")
    
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(txt+'\n\n(Message Will Autohide in 5 seconds)')
    msg.show()
    
    frame_timer = QtCore.QTimer()
    frame_timer.timeout.connect(lambda x=0: frame_options(msg))
    frame_timer.setSingleShot(True)
    frame_timer.start(5000)
    msg.exec_()
    
def frame_options(box):
    box.hide()
    
def open_files(file_path, lines_read=True):
    if os.path.exists(file_path):
        if lines_read:
            lines = ''
            try:
                f = open(file_path, 'r')
                lines = f.readlines()
                f.close()
            except UnicodeDecodeError as e:
                try:
                    print(e)
                    f = open(file_path, encoding='utf-8', mode='r')
                    lines = f.readlines()
                    f.close()
                except UnicodeDecodeError as e:
                    print(e)
                    f = open(file_path, encoding='ISO-8859-1', mode='r')
                    lines = f.readlines()
                    f.close()
            except Exception as e:
                print(e)
                print("Can't Decode")
        else:
            lines = ''
            try:
                f = open(file_path, 'r')
                lines = f.read()
                f.close()
            except UnicodeDecodeError as e:
                try:
                    print(e)
                    f = open(file_path, encoding='utf-8', mode='r')
                    lines = f.read()
                    f.close()
                except UnicodeDecodeError as e:
                    print(e)
                    f = open(file_path, encoding='ISO-8859-1', mode='r')
                    lines = f.read()
                    f.close()
            except Exception as e:
                print(e)
                lines = "Can't Decode"
    else:
        if lines_read:
            lines = []
        else:
            lines = 'Not Available'
    return lines


def get_config_options(file_name, value_field):
    req_val = ''
    if os.path.exists(file_name):
        lines = open_files(file_name, True)
        for i in lines:
            i = i.strip()
            if i:
                try:
                    i, j = i.split('=')
                except Exception as e:
                    print(e, 'wrong values in config file')
                    continue
                j = j.strip()
                if str(i.lower()) == str(value_field.lower()):
                    req_val = j
                    break
    else:
        req_val = 'file_not_exists'
    return req_val


def naturallysorted(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)


def replace_all(text, di):
    for i, j in di.iteritems():
        text = text.replace(i, j)
    return text


def get_tmp_dir():
    TMPDIR = ''
    home_dir = get_home_dir()
    try:
        option_file = os.path.join(home_dir, 'other_options.txt')
        if os.path.exists(option_file):
            tmp_option = get_config_options(option_file, 'TMP_REMOVE')
            if tmp_option:
                if tmp_option.lower() == 'no':
                    TMPDIR = os.path.join(home_dir, 'tmp')
                else:
                    TMPDIR = mkdtemp(suffix=None, prefix='kawaii-player_')
            else:
                TMPDIR = os.path.join(home_dir, 'tmp')
        else:
            TMPDIR = os.path.join(home_dir, 'tmp')
    except Exception as e:
        print(e, '--error-in--creating--TEMP--Directory--') 
        TMPDIR = os.path.join(home_dir, 'tmp')
    return TMPDIR

def get_home_dir(mode=None):
    if mode == 'test':
        home = os.path.join(os.path.expanduser('~'), '.config', 'kawaii-player-test')
    else:
        home = os.path.join(os.path.expanduser('~'), '.config', 'kawaii-player')
        new_home_path = os.path.join(home, "new_home.txt")
        if os.path.exists(new_home_path):
            new_home = open_files(new_home_path, False)
            new_home = new_home.strip()
            if os.path.isdir(new_home):
                home = new_home
    return home

def change_opt_file(config_file, old, new):
    found = False
    if os.path.exists(config_file):
        lines = open_files(config_file, True)
        if isinstance(lines, list):
            for i, j in enumerate(lines):
                lines[i] = lines[i].strip()
                if lines[i].startswith(old):
                    lines[i] = new
                    found = True
            if not found:
                lines.append(new)
            write_files(config_file, lines, line_by_line=True)

def set_logger(file_name, TMPDIR):
    file_name_log = os.path.join(TMPDIR, file_name)
    #log_file = open(file_name_log, "w", encoding="utf-8")
    logging.basicConfig(level=logging.DEBUG)
    formatter_fh = logging.Formatter('%(asctime)-15s::%(module)s:%(funcName)s: %(levelname)-7s - %(message)s')
    formatter_ch = logging.Formatter('%(levelname)s::%(module)s::%(funcName)s: %(message)s')
    fh = logging.FileHandler(file_name_log)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter_ch)
    fh.setFormatter(formatter_fh)
    log = logging.getLogger(__name__)
    log.addHandler(ch)
    log.addHandler(fh)
    return log

def get_hls_path():
    try:
        try:
            from hls_webengine.hls_engine import BrowseUrlT
            webkit = False
        except Exception as e:
            print(e, '--43--')
            from hls_webkit.hls_engine_webkit import BrowseUrlT
            webkit = True
            print('webkit available')
        hls_dir, hls_file = os.path.split(sys.executable)
        if hls_file.startswith('python'):
            frozen_file = False	
            hls_dir, hls_file = os.path.split(inspect.getfile(BrowseUrlT))
            if not webkit:
                hls_path = os.path.join(hls_dir, 'hls_cmd.py')
            else:
                hls_path = os.path.join(hls_dir, 'hls_cmd_webkit.py')
        else:
            frozen_file = True
            if not webkit:
                hls_path = os.path.join(hls_dir, 'hls_cmd')
            else:
                hls_path = os.path.join(hls_dir, 'hls_cmd_webkit')
    except Exception as e:
        print(e, '--240--')
        frozen_file = False
        hls_path = None
    return (hls_path, frozen_file)
    
def set_user_password(text_val, pass_val):
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
    config_file = os.path.join(get_home_dir(), 'other_options.txt')
    change_opt_file(config_file, 'AUTH=', new_pass)


def create_ssl_cert(ui, TMPDIR, pass_word):
    if len(pass_word) >= 8:
        my_ip = str(ui.local_ip_stream)
        server_key = os.path.join(TMPDIR, 'server.key')
        server_csr = os.path.join(TMPDIR, 'server.csr')
        server_crt = os.path.join(TMPDIR, 'server.crt')
        ssl_cert = os.path.join(get_home_dir(), 'cert.pem')
        cn = '/CN='+my_ip
        if ui.my_public_ip and ui.access_from_outside_network:
            my_ip = str(ui.my_public_ip)	
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
            f = open(ssl_cert, 'w')
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
        print('Length of password less than 8 characters, Make it atleast 8')

def write_files(file_name, content, line_by_line, mode=None):
    if mode == 'test':
        tmp_new_file = os.path.join(get_home_dir(mode='test'), 'tmp', 'tmp_write.txt')
    else:
        tmp_new_file = os.path.join(get_home_dir(), 'tmp', 'tmp_write.txt')
    file_exists = False
    write_operation = True
    if os.path.exists(file_name):
        file_exists = True
        shutil.copy(file_name, tmp_new_file)
    try:
        if isinstance(content, list):
            bin_mode = False
            with open(file_name, 'w') as f:
                for j, i in enumerate(content):
                    fname = i.strip()
                    if j == 0:
                        try:
                            f.write(fname)
                        except UnicodeEncodeError as e:
                            bin_mode = True
                            break
                    else:
                        try:
                            f.write('\n'+fname)
                        except UnicodeEncodeError as e:
                            bin_mode = True
                            break
            if bin_mode:
                with open(file_name, 'wb') as f:
                    for j, i in enumerate(content):
                        fname = i.strip()
                        if j == 0:
                            f.write(fname.encode('utf-8'))
                        else:
                            f.write(('\n'+fname).encode('utf-8'))
        else:
            if line_by_line:
                content = content.strip()
                if not os.path.exists(file_name) or (os.stat(file_name).st_size == 0):
                    with open(file_name, 'w') as f:
                        bin_mode = False
                        try:
                            f.write(content)
                        except UnicodeEncodeError as e:
                            bin_mode = True
                    if bin_mode:
                        with open(file_name, 'wb') as f:
                            f.write(content.encode('utf-8'))
                else:
                    with open(file_name, 'a') as f:
                        bin_mode = False
                        try:
                            f.write('\n'+content)
                        except UnicodeEncodeError as e:
                            bin_mode = True
                    if bin_mode:
                        with open(file_name, 'ab') as f:
                            f.write(('\n'+content).encode('utf-8'))
            else:
                with open(file_name, 'w') as f:
                    bin_mode = False
                    try:
                        f.write(content)
                    except UnicodeEncodeError as e:
                        bin_mode = True
                if bin_mode:
                    with open(file_name, 'wb') as f:
                        f.write(content.encode('utf-8'))
    except Exception as e:
        write_operation = False
        print(e, 'error in handling file, hence restoring original')
        if file_exists:
            shutil.copy(tmp_new_file, file_name)
    if os.path.exists(tmp_new_file):
        if not write_operation:
            print('Debug:write operation failed hence restored original')


get_lib = get_config_options(
    os.path.join(get_home_dir(), 'other_options.txt'), 'GET_LIBRARY')


if get_lib.lower() == 'pycurl':
    from get_functions import ccurl
    print('--using pycurl--')
elif get_lib.lower() == 'curl':
    from get_functions import ccurlCmd as ccurl
    print('--using curl--')
elif get_lib.lower() == 'wget':
    from get_functions import ccurlWget as ccurl
    print('--using wget--')
else:
    from get_functions import ccurl
    print('--using default pycurl--')

        
        
        
