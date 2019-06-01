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
import ssl
import time
import base64
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
import libtorrent as lt
from player_functions import send_notification, get_home_dir, get_lan_ip


class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    protocol_version = 'HTTP/1.1'
    
    def do_HEAD(self):
        global handle, ses, info, count, count_limit, file_name, torrent_download_path
        global tmp_dir_folder, content_length
        self.send_response(200)
        self.send_header('Content-type', 'video/mp4')
        self.send_header('Content-Length', str(content_length))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Connection', 'close')
        self.end_headers()

    def get_the_content(self, get_bytes):
        global handle, ses, info, count, count_limit, file_name, torrent_download_path
        global tmp_dir_folder, httpd, media_server_key, client_auth_arr, ui_player
        global content_length

        user_agent = self.headers['User-Agent']
        range_hdr = self.headers['Range']
        upper_range = None
        lower_range = None
        try:
            if range_hdr:
                if range_hdr.startswith('bytes='):
                    range_hdr = range_hdr.replace('bytes=', '', 1)
                if '-' in range_hdr:
                    if not range_hdr.endswith('-'):
                        low, up = range_hdr.split('-')
                        lower_range = int(low)
                        upper_range = int(up)
                        print(lower_range, upper_range)
                    else:
                        lower_range = int(range_hdr.replace('-', ''))
                else:
                    lower_range = int(range_hdr)
        except Exception as err_val:
            print(err_val, '--495--')
        
        if lower_range is not None:
            get_bytes = lower_range

        print('Range: {0}-{1}'.format(str(get_bytes), str(upper_range)))

        tmp_pl_file = os.path.join(tmp_dir_folder, 'player_stop.txt')
        
        length = info.piece_length()
        print(length, '--piece--length')
        complete_file = False
        if not os.path.exists(file_name):
            dir_name, sub_file = os.path.split(file_name)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            open(file_name, 'wb').close()
        else:
            if (os.path.exists(file_name) and 
                    os.stat(file_name).st_size == content_length):
                complete_file = True
        if get_bytes:
            self.send_response(206)
        else:
            self.send_response(200)
        self.send_header('Content-type', 'video/mp4')
        self.send_header('Content-Length', str(content_length))
        self.send_header('Accept-Ranges', 'bytes')
        if get_bytes or upper_range is not None:
            if upper_range is None:
                upper_range = content_length - 1
            print('...sending range...{0}-{1}/{2}'.format(str(get_bytes),
                                                          str(upper_range),
                                                          str(content_length)))
            self.send_header(
                'Content-Range',
                'bytes ' +str(get_bytes)+'-'+str(upper_range)+'/'+str(content_length)
            )
        self.send_header('Connection', 'close')
        self.end_headers()
        seek_end = False
        
        if get_bytes:
            new_piece = int(get_bytes/length)+1
            print(new_piece, get_bytes, length, get_bytes/info.piece_length())
            req_piece = count+new_piece - 1
            if req_piece > count_limit - 10:
                seek_end = True
            print(new_piece, '--new_piece--', req_piece, count,
                  count_limit, get_bytes, content_length)
        else:
            req_piece = count
        print(file_name, req_piece, count, count_limit, '---file--download---path--')
        pri_lowered = False
        content = b'01'
        with open(file_name, 'rb') as f:
            while content and req_piece in range(count, count_limit+1):
                update_str = ''
                if handle.have_piece(req_piece):
                    update_str = ('Received Piece No. {}\nBeginning={}\nEnd={}'
                                  .format(req_piece, count, count_limit))
                    if get_bytes:
                        f.seek(get_bytes)
                        get_bytes = 0
                        if req_piece in [count_limit, count_limit+1]:
                            content = f.read(2*length)
                    else:
                        content = f.read(length)
                    try:
                        self.wfile.write(content)
                    except Exception as err:
                        print(err)
                        break
                    req_piece += 1
                    priority = 7
                    for piece in range(req_piece, req_piece+7):
                        if piece in range(count, count_limit+1) and not handle.have_piece(piece):
                            if priority in [1, 2]:
                                handle.piece_priority(piece, 2)
                            else:
                                handle.piece_priority(piece, priority)
                            priority -= 1
                            
                    if req_piece in range (count_limit-10, count_limit-7):
                        for k in range(count+1, req_piece-1):
                            if not handle.have_piece(k) and handle.piece_priority(k) == 0:
                                handle.piece_priority(k, 2)
                        self.show_piece_map(info, handle, req_piece)
                elif not handle.have_piece(count) or not handle.have_piece(count_limit):
                    handle.piece_priority(count, 7)
                    handle.piece_priority(count_limit, 7)
                    update_str = ('Waiting for Beginning and End\npiece No. {} and {}'
                                  .format(count, count_limit))
                    time.sleep(1)
                    #self.show_piece_map(info, handle, req_piece)
                else:
                    update_str = ('Waiting for Piece No. {}\nBeginning={}\nEnd={}'
                                  .format(req_piece, count, count_limit))
                    if not handle.have_piece(count_limit-1):
                        handle.piece_priority(count_limit-1, 7)
                    if not handle.have_piece(count+1):
                        handle.piece_priority(count+1, 6)
                    time.sleep(1)
                    handle.piece_priority(req_piece, 7)
                    if get_bytes and not pri_lowered:
                        if seek_end:
                            ncount = count+10
                        else:
                            ncount = count + 1
                        print(req_piece-1, ncount, '----', count_limit, count_limit-1)
                        if req_piece not in [count_limit, count_limit-1]:
                            for k in range(ncount, req_piece-1):
                                if not handle.have_piece(k) and handle.piece_priority(k) in [1, 2]:
                                    handle.piece_priority(k, 0)
                                    print('lowered {} {}/{}'.format(k, count, count_limit))
                        pri_lowered = True
                        self.show_piece_map(info, handle, req_piece)
                if update_str and not ui_player.torrent_frame.isHidden():
                    s = handle.status()
                    if ui_player.torrent_status_command == 'map':
                        update_str = self.show_piece_map(info, handle, req_piece, local=True)
                        ui_player.gui_signals.update_torrent_status(update_str)
                    elif ui_player.torrent_status_command == 'default':
                        update_str = update_str + '\nTotal={}\nDownloaded={}'.format(count_limit-count+1, s.num_pieces)
                        ui_player.gui_signals.update_torrent_status(update_str)
                if ses.is_paused() or os.path.exists(tmp_pl_file):
                    break
        if os.path.exists(tmp_pl_file):
            os.remove(tmp_pl_file)
            
    def show_piece_map(self, info, handle, req_piece, local=False):
        global count, count_limit, ui_player
        if local:
            low, up = count, count_limit + 1
        else:
            low, up = 0, info.num_pieces()
        tmp = ""
        break_line = 0
        for piece in range(low, up):
            if piece == req_piece:
                tmp = tmp+':Y'
            elif handle.have_piece(piece):
                tmp = tmp+':X'
            else:
                tmp = tmp+':'+str(handle.piece_priority(piece))
            if piece in [count, count_limit]:
                tmp = tmp + '.{}\n'.format(piece)
            if break_line%20 == 0:
                tmp = tmp + '\n'
            break_line += 1
        #ui_player.gui_signals.update_torrent_status(tmp)
        #print(tmp)
        return tmp
        
    def do_GET(self):
        global handle, ses, info, count, count_limit, file_name, torrent_download_path
        global tmp_dir_folder, httpd, media_server_key, client_auth_arr, local_ip_arr
        global ui_player
        print('do_get')
        print(self.headers)
        try:
            get_bytes = int(self.headers['Range'].split('=')[1].replace('-', ''))
        except Exception as e:
            get_bytes = 0
        print(get_bytes, '--get--bytes--')
        print(client_auth_arr, '--250--')
        cookie_verified = False
        client_addr = str(self.client_address[0])
        print(client_addr, '--client--248--', self.path)
        auth_token = None
        allow_access = False
        if '&pl_id=' in self.path:
            path, pl_id = self.path.rsplit('&pl_id=', 1)
            if '&auth_token' in pl_id:
                pl_id, _ = pl_id.rsplit('&', 1)
            del_uid = False
            found_uid = False
            try:
                if pl_id in ui_player.playlist_auth_dict_ui:
                    print(pl_id, ui_player.playlist_auth_dict_ui[pl_id], '--playlist--id--')
                    old_time = ui_player.playlist_auth_dict_ui[pl_id]
                    found_uid = True
                    time_diff = int(time.time()) - int(old_time)
                    print(time_diff, '--time--diff--')
                    if (time_diff) > ui_player.cookie_playlist_expiry_limit*3600:
                        del_uid = True
            except Exception as err_val:
                print(err_val, '--266--')

            if found_uid and not del_uid:
                cookie_verified = True
            elif found_uid and del_uid:
                print('--timeout--')
        if '&auth_token=' in self.path:
            _, auth_token = self.path.rsplit('&auth_token=', 1)
            if '&pl_id' in auth_token:
                auth_token, _ = auth_token.rsplit('&', 1)
        if auth_token and auth_token in ui_player.allowed_access_tokens:
            allow_access = True
        if ui_player.media_server_cookie:
            print('--cookie-stream--enabled--', cookie_verified, local_ip_arr)
            if cookie_verified or client_addr in local_ip_arr or allow_access:
                print('--cookie-stream-verified--')
                self.get_the_content(get_bytes)
            else:
                txt = b'You are not authorized to access the content'
                self.final_message(txt)
        else:
            if allow_access:
                self.get_the_content(get_bytes)
            elif media_server_key:
                key_en = base64.b64encode(bytes(media_server_key, 'utf-8'))
                key = (str(key_en).replace("b'", '', 1))[:-1]
                new_key = 'Basic '+key
                cli_key = self.headers['Authorization'] 
                print(client_addr, '--cli--')
                print(client_auth_arr, '--auth--')
                if not cli_key and (not client_addr in client_auth_arr):
                    print('authenticating...')
                    txt = 'Nothing'
                    print("send header")
                    self.send_response(401)
                    self.send_header('WWW-Authenticate', 'Basic realm="Auth"')
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Content-Length', len(txt))
                    self.end_headers()
                    try:
                        self.wfile.write(b'Nothing')
                    except Exception as e:
                        print(e)
                elif (cli_key == new_key) or (client_addr in client_auth_arr):
                    self.get_the_content(get_bytes)
                else:
                    txt = b'You are not authorized to access the content'
                    self.final_message(txt)
            else:
                self.get_the_content(get_bytes)

    def final_message(self, txt, cookie=None):
        self.send_response(200)
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(txt))
        self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(txt)
        except Exception as e:
            print(e)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class ThreadServer(QtCore.QThread):

    def __init__(
            self, ip, port, key=None, client_arr=None, https_conn=None,
            cert_file=None, ui=None):
        global thread_signal, media_server_key, client_auth_arr, ui_player, local_ip_arr
        QtCore.QThread.__init__(self)
        self.ip = ip
        self.port = int(port)
        media_server_key = key
        client_auth_arr = client_arr
        self.https_allow = https_conn
        self.cert_file = cert_file
        ui_player = ui
        local_ip_arr = ['127.0.0.1', '0.0.0.0', ip]
        if ui is not None:
            self.ui = ui

    def __del__(self):
        self.wait()                        

    def run(self):
        global httpd, ui_player
        print('starting server...')
        server_address = ('', self.port)
        server_start = False
        try:
            httpd = ThreadedHTTPServer(server_address, testHTTPServer_RequestHandler)
            if self.https_allow and self.cert_file:
                if os.path.exists(self.cert_file):
                    httpd.socket = ssl.wrap_socket(
                        httpd.socket, certfile=self.cert_file, 
                        ssl_version=ssl.PROTOCOL_TLSv1_2)
            server_start = True
        except Exception as err:
            print(err, '----->error')
            txt = 'Your local IP changed..or port is blocked\n..Trying to find new IP'
            send_notification(txt)
            self.ip = get_lan_ip()
            txt = 'Your New Address is '+self.ip + '\n Please restart the player'
            send_notification(txt)
        if server_start:
            print('running server...at..'+self.ip+':'+str(self.port))
            httpd.serve_forever()
        else:
            print('server..not..started..')


class TorrentThread(QtCore.QThread):

    session_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int)
    progress_signal_end = pyqtSignal(str)

    def __init__(self, v1, v2, v3, v4, row=None, from_client=None):
        QtCore.QThread.__init__(self)
        self.handle = v1
        self.count = v2
        self.count_limit = v3
        self.session = v4
        if row:
            self.current_index = row
        else:
            self.current_index = 0
        self.from_client = from_client
        self.start_next = False
        self.session_signal.connect(session_finished)
        self.progress_signal.connect(print_progress)
        self.progress_signal_end.connect(print_progress_complete)
        self.ui = None

    def __del__(self):
        self.wait()                        

    def process_next(self):
        global handle, info, ses, new_count, new_count_limit, total_size_content
        global torrent_download_path
        self.current_index += 1
        fileIndex = int(self.current_index)
        fileStr = None
        file_exists = False
        for i, f in enumerate(info.files()):
            if fileIndex == i:
                fileStr = f
                handle.file_priority(i, 5)
        try:
            new_path = os.path.join(torrent_download_path, fileStr.path)
            new_size = fileStr.size
            if os.path.exists(new_path) and os.stat(new_path).st_size == new_size:
                file_exists = True
        except Exception as err_val:
            print(err_val, '--312--stream.py--')
            file_exists = True
        if fileStr and not file_exists:
            s = self.handle.status()
            if (s.progress *100) >= 100:
                handle.force_recheck()
                print('--force--rechecking--')
            print(fileStr.path)
            total_size_content = str(int(fileStr.size/(1024*1024)))+'M'
            pr = info.map_file(fileIndex, 0, fileStr.size)
            print(pr.length, info.piece_length(), info.num_pieces())
            n_pieces = pr.length / info.piece_length() + 1 
            print(n_pieces)
            n_pieces = int(n_pieces)
            for i in range(info.num_pieces()):
                if i in range(pr.piece, pr.piece+n_pieces):
                    if i in range(pr.piece, pr.piece+10):
                        if i == pr.piece:
                            handle.piece_priority(i, 7)
                        else:
                            handle.piece_priority(i, 6)
                    elif i == pr.piece+n_pieces-1:
                        handle.piece_priority(i, 7)
                    else:
                        handle.piece_priority(i, 1)
            tmp = ''
            for i in range(info.num_pieces()):
                tmp = tmp+':'+str(handle.piece_priority(i))
            print(tmp)
            print('starting', handle.name())
            handle.set_sequential_download(True)
            new_count = pr.piece
            new_count_limit = pr.piece + n_pieces - 1
            self.start_next = False
    
    def assign_handle(self, handle):
        self.handle = handle
        
    def assign_globals(self, ui):
        self.ui = ui
        
    def run(self):
        global new_count, new_count_limit, total_size_content
        count_limit = self.count_limit
        s = self.handle.status()

        while (not self.session.is_paused()):
            s = self.handle.status()
            if not self.handle.is_seed():
                out = str(int(s.progress*100))+'%'
            else:
                out = 'SEEDING'
            out_percent = int(s.progress*100)
            TD = str(int(s.total_download/(1024*1024)))+'M'
            TU = str(int(s.total_upload/(1024*1024)))+'M'
            TDR = u'\u2193'+str(int(s.download_rate/1024)) + 'K' + '('+TD+')'
            TUR = u'\u2191'+str(int(s.upload_rate/1024)) + 'K'+'('+TU+')'
            out1 = str(out)+' '+total_size_content+' '+TDR +' '+TUR+' '+'P:'+str(s.num_peers)
            if s.state == 1:
                out1 = 'Checking Please Wait: '+str(out)
            self.progress_signal.emit(out1, out_percent)
            if (s.progress * 100) >= 99 and (s.state != 1):
                partial_down = False
                for k in range(count, count_limit+1):
                    if handle.piece_priority(k) == 0:
                        handle.piece_priority(k, 2)
                        partial_down = True
                if not partial_down:
                    if self.from_client:
                        if not self.start_next:
                            self.start_next = True
                            self.process_next()
                    else:
                        self.session_signal.emit('..Starting Next Download..')
                        time.sleep(5)
            time.sleep(1)
            if self.ui and self.ui.torrent_status_command == 'all':
                msg = get_torrent_info_all(self.ui)
                self.ui.gui_signals.update_torrent_status(msg)
        self.progress_signal_end.emit('complete')

def change_config_file(ip, port):
    home_dir = get_home_dir()
    config_file = os.path.join(home_dir, 'torrent_config.txt')
    new_ip = 'TORRENT_STREAM_IP='+ip+':'+str(port)
    content = open(config_file, 'r').read()
    content = re.sub('TORRENT_STREAM_IP=[^\n]*', new_ip, content)
    f = open(config_file, 'w')
    f.write(content)
    f.close()

def get_torrent_download_location(url, home_dir, download_loc):
    tmp_arr = url.split('&')
    
    site = tmp_arr[0]
    opt = tmp_arr[1]
    site_Name = tmp_arr[2]
    row = -1
    ep_n = ''
    if len(tmp_arr) == 7:
        name = tmp_arr[3]
        if tmp_arr[4] == 'False':
            vi_deo_local_stream = False
        else:
            vi_deo_local_stream = True
        row = int(tmp_arr[5])
        ep_n = tmp_arr[6]
    elif len(tmp_arr) > 7:
        new_tmp_arr = tmp_arr[3:]
        row_index = -1
        local_stream_index = -1
        for i, j in enumerate(new_tmp_arr):
            if j.isnumeric():
                row = int(j)
                row_index = i
            if j.lower() == 'true' or j.lower() == 'false':
                if j.lower() == 'false':
                    vi_deo_local_stream = False
                else:
                    vi_deo_local_stream = True
                local_stream_index = i
        if local_stream_index >= 0:
            name = '&'.join(new_tmp_arr[:-(len(new_tmp_arr)-local_stream_index)])
        if row_index >= 0:
            ep_n = '&'.join(new_tmp_arr[(row_index+1):])
    
    torrent_loc = os.path.join(home_dir, 'History', site, name+'.torrent')
    
    info = lt.torrent_info(torrent_loc)
    i = 0
    fileIndex = int(row)
    file_found = False
    for f in info.files():
        if fileIndex == i:
            fileStr = f
        i = i+1
    print(fileStr.path)
    file_name = os.path.join(download_loc, fileStr.path)
    return file_name
    
def get_torrent_info_all(ui):
    msg = ''
    torrent_list = ui.stream_session.get_torrents()
    for i, handle in enumerate(torrent_list):
        msg_t = str(i+1)+'. '+handle.name() +':'+torrent_session_status(handle) +'\n\n'
        if handle == ui.torrent_handle:
            msg_t = ui.check_symbol+msg_t
        msg = msg + msg_t
    return msg

def torrent_session_status(torrent_handle):
    s = torrent_handle.status()
    if not torrent_handle.is_seed():
        out = str(int(s.progress*100))+'%'
    else:
        out = 'SEEDING'
    out_percent = int(s.progress*100)
    TD = str(int(s.total_download/(1024*1024)))+'M'
    TU = str(int(s.total_upload/(1024*1024)))+'M'
    TDR = u'\u2193'+str(int(s.download_rate/1024)) + 'K' + '('+TD+')'
    TUR = u'\u2191'+str(int(s.upload_rate/1024)) + 'K'+'('+TU+')'
    SZ = str(int(s.total_wanted/(1024*1024)))+'M'
    out1 = str(out)+' '+SZ+' '+TDR +' '+TUR+' '+'P:'+str(s.num_peers)
    if s.state == 1:
        out1 = 'Checking Please Wait: '+str(out)
    return out1

def get_ip():
    a = subprocess.check_output(['ip', 'addr', 'show'])
    b = str(a, 'utf-8')
    c = re.findall('inet [^ ]*', b)
    final = ''
    for i in c:
        if '127.0.0.1' not in i:
            final = i.replace('inet ', '')
            final = re.sub('/[^"]*', '', final)
    return final

@pyqtSlot(str)
def print_progress_complete(var_str):
    global progress, ses
    progress.setValue(100)
    progress.hide()

@pyqtSlot(str, int)
def print_progress(var_str, var_int):
    global progress
    progress.setValue(var_int)
    progress.setFormat(var_str)

@pyqtSlot(str)
def session_finished(var):
    global ui, handle, info, ses, new_count, new_count_limit, total_size_content
    print(var, '--session-finished--')
    if ui.count() > 0:
        item = ui.item(0)
        if item:
            txt = item.text()
            if txt.startswith('Queue Empty:'):
                return 0
            ui.takeItem(0)
            del item
            indx = txt.split(':')[-1]
            fileIndex = int(indx)
            i = 0
            s = handle.status()
            if (s.progress *100) >= 100:
                handle.force_recheck()
                print('--force--rechecking--')
            for f in info.files():
                if fileIndex == i:
                    fileStr = f
                    handle.file_priority(i, 5)
                i += 1
            try:
                print(fileStr.path)
                total_size_content = str(int(fileStr.size/(1024*1024)))+'M'
            except:
                return 0
            pr = info.map_file(fileIndex, 0, fileStr.size)
            print(pr.length, info.piece_length(), info.num_pieces())
            n_pieces = pr.length / info.piece_length() + 1 
            print(n_pieces)
            n_pieces = int(n_pieces)
            for i in range(info.num_pieces()):
                if i in range(pr.piece, pr.piece+n_pieces):
                    if i in range(pr.piece, pr.piece+10):
                        if i == pr.piece:
                            handle.piece_priority(i, 7)
                        else:
                            handle.piece_priority(i, 6)
                    elif i == pr.piece+n_pieces-1:
                        handle.piece_priority(i, 7)
                    else:
                        handle.piece_priority(i, 1)
            tmp = ''
            for i in range(info.num_pieces()):
                tmp = tmp+':'+str(handle.piece_priority(i))
            print(tmp)
            print('starting', handle.name())
            handle.set_sequential_download(True)
            new_count = pr.piece
            new_count_limit = pr.piece + n_pieces - 1


def get_torrent_info_magnet(v1, v3, u, p_bar, tmp_dir):
    global handle, ses, info, count, count_limit, file_name, ui, progress, tmp_dir_folder
    ui = u
    progress = p_bar
    tmp_dir_folder = tmp_dir
    progress.setValue(0)
    progress.show()
    sett = lt.session_settings()
    sett.user_agent = 'qBittorrent v3.3.5'
    sett.always_send_user_agent = True
    fingerprint = lt.fingerprint('qB', 3, 3, 5, 0)
    ses = lt.session(fingerprint)

    ses.listen_on(40000, 50000)
    ses.set_settings(sett)

    handle = lt.add_magnet_uri(ses, v1, {'save_path':v3})
    i = 0
    while (not handle.has_metadata()):
        time.sleep(1)
        i = i+1
        print('finding metadata {0}'.format(i))
        if i > 300:
            print('No Metadata Available: {0}s'.format(i))
            break
    info = handle.get_torrent_info()

    handle.set_sequential_download(True)
    print(handle.trackers())

    return handle, ses, info


def get_torrent_handle(ses, nm):
    handle = None
    t_list = ses.get_torrents()
    for i in t_list:
        old_name = i.name()
        if old_name == nm:
            handle = i
            break
        print(old_name, nm)
    return handle

def assign_piece_priority(handle, info, count, count_limit):
    for i in range(info.num_pieces()):
        if i in range(count, count_limit+1):
            if i in range(count, count+10):
                if i == count:
                    handle.piece_priority(i, 7)
                else:
                    handle.piece_priority(i, 6)
            elif i == count_limit:
                handle.piece_priority(i, 7)
            else:
                handle.piece_priority(i, 2)

def get_torrent_info(torrent_file, file_index, file_dest,
                     session, u, p_bar, tmp_dir, key=None,
                     client=None, torrent_handle=None):
    global handle, ses, info, count, count_limit, file_name, ui
    global progress, total_size_content, tmp_dir_folder, content_length
    global media_server_key, client_auth_arr, torrent_download_path
    media_server_key = key
    client_auth_arr = client
    content_length = 0
    ui = u
    progress = p_bar
    tmp_dir_folder = tmp_dir
    progress.setValue(0)
    progress.show()
    if not session:
        sett = lt.session_settings()
        sett.user_agent = 'qBittorrent v3.3.5'
        sett.always_send_user_agent = True
        fingerprint = lt.fingerprint('qB', 3, 3, 5, 0)
        ses = lt.session(fingerprint)
        ses.listen_on(40000, 50000)
        ses.set_settings(sett)
    else:
        ses = session

    if torrent_file.startswith('magnet:'):
        handle = lt.add_magnet_uri(ses, torrent_file, {'save_path':file_dest})
        i = 0
        while (not handle.has_metadata()):
            time.sleep(1)
            i = i+1
            if i > 60:
                print('No Metadata Available')
                break
        info = handle.get_torrent_info()
    elif torrent_handle and torrent_handle.is_valid():
        info = lt.torrent_info(torrent_file)
        handle = torrent_handle
    else:
        info = lt.torrent_info(torrent_file)
        handle = ses.add_torrent({'ti': info, 'save_path': file_dest})

    fileIndex = int(file_index)
    for i, f in enumerate(info.files()):
        file_exists = False
        new_path = os.path.join(file_dest, f.path)
        new_size = f.size
        if os.path.exists(new_path) and os.stat(new_path).st_size:
            file_exists = True
        if fileIndex == i:
            fileStr = f
            handle.file_priority(i, 1)
        elif file_exists:
            handle.file_priority(i, 1)
        else:
            handle.file_priority(i, 0)
            
    print(fileStr.path)
    file_name = os.path.join(file_dest, fileStr.path)
    torrent_download_path = file_dest

    content_length = fileStr.size
    print(content_length, 'content-length')
    total_size_content = str(int(content_length/(1024*1024)))+'M'

    pr = info.map_file(fileIndex, 0, fileStr.size)
    print(pr.length, info.piece_length(), info.num_pieces())
    n_pieces = pr.length / info.piece_length() + 1 
    print(n_pieces)
    n_pieces = int(n_pieces)
    
    count = pr.piece
    count_limit = pr.piece + n_pieces - 1
    assign_piece_priority(handle, info, count, count_limit)
    
    print('starting', handle.name())
    handle.set_sequential_download(True)

    if ses.is_paused():
        ses.resume()
    if handle.status().paused:
        handle.resume()

    return handle, ses, info, count, count_limit, file_name

