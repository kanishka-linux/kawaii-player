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
import time
import shutil
import subprocess
from functools import partial
from tempfile import mkstemp
from PyQt5 import QtCore
from player_functions import send_notification, ccurl, get_home_dir


def get_yt_url(url, quality, ytdl_path, logger, mode=None):
    final_url = ''
    url = url.replace('"', '')
    m = []
    home_dir = get_home_dir()
    ytdl_stamp = os.path.join(home_dir, 'tmp', 'ytdl_update_stamp.txt')
    if ytdl_path:
        if ytdl_path == 'default':
            youtube_dl = 'youtube-dl'
        else:
            if os.path.exists(ytdl_path):
                youtube_dl = ytdl_path
            else:
                if ytdl_path.endswith('ytdl') or ytdl_path.endswith('ytdl.exe'):
                    send_notification('Please Wait! Getting Latest youtube-dl')
                    youtube_dl = ytdl_path
                    if ytdl_path.endswith('ytdl'):
                        ccurl('https://yt-dl.org/downloads/latest/youtube-dl'+'#-o#'+ytdl_path)
                        subprocess.Popen(['chmod', '+x', ytdl_path])
                    else:
                        ccurl('https://yt-dl.org/latest/youtube-dl.exe'+'#-o#'+ytdl_path)
                    update_time = str(int(time.time()))
                    if not os.path.exists(ytdl_stamp):
                        f = open(ytdl_stamp, 'w')
                        f.write(update_time)
                        f.close() 
                else:
                    send_notification('youtube-dl path does not exists!')
                    youtube_dl = 'youtube-dl'
    else:
        youtube_dl = 'youtube-dl'
        
    logger.info(youtube_dl)
    ytdl_extra = False
    if '/watch?' in url and 'youtube.com' in url:
        a = url.split('?')[-1]
        b = a.split('&')
        if b:
            for i in b:
                j = i.split('=')
                k = (j[0], j[1])
                m.append(k)
        else:
            j = a.split('=')
            k = (j[0], j[1])
            m.append(k)
        d = dict(m)
        logger.info('----dict--arguments---generated---{0}'.format(d))
        try:
            url = 'https://www.youtube.com/watch?v='+d['v']
        except:
            pass
    elif url.startswith('ytdl:'):
        url = url.replace('ytdl:', '', 1)
        ytdl_extra = True
    else:
        ytdl_extra = True
    try:
        if mode == 'TITLE':
            if os.name == 'posix':
                final_url = subprocess.check_output([youtube_dl, '-e', url])
            else:
                final_url = subprocess.check_output([youtube_dl, '-e', url], shell=True)
            final_url = str(final_url, 'utf-8')
            final_url = final_url.replace(' - YouTube', '', 1)
        else:
            if mode == 'music':
                quality = 'best'
                
            if quality == 'sd':
                res = 360
            elif quality == 'hd':
                res = 720
            elif quality == 'sd480p':
                res = 480
            else:
                res = 4000
            
            if quality == 'best' and ytdl_path == 'default':
                if ytdl_extra:
                    final_url = 'ytdl:'+url
                else:
                    final_url = url
            else:
                final_url = get_final_for_resolution(
                    url, youtube_dl, logger, ytdl_extra, resolution=res,
                    mode=mode
                    )
    except Exception as e:
        logger.info('--error in processing youtube url--{0}'.format(e))
        txt = 'Please Update youtube-dl'
        send_notification(txt)
        final_url = ''
        updated_already = False
        if ytdl_path.endswith('ytdl') or ytdl_path.endswith('ytdl.exe'):
            if os.path.exists(ytdl_stamp):
                content = open(ytdl_stamp, 'r').read()
                try:
                    old_time = int(content)
                except Exception as e:
                    logger.info(e)
                    old_time = int(time.time()) - 3600
                cur_time = int(time.time())
                if (cur_time - old_time < 24*3600):
                    updated_already = True
            if not updated_already:
                send_notification('Please Wait! Getting Latest youtube-dl')
                if ytdl_path.endswith('ytdl'):
                    ccurl('https://yt-dl.org/downloads/latest/youtube-dl'+'#-o#'+ytdl_path)
                    subprocess.Popen(['chmod', '+x', ytdl_path])
                else:
                    ccurl('https://yt-dl.org/latest/youtube-dl.exe'+'#-o#'+ytdl_path)
                send_notification('Updated youtube-dl, Now Try Playing Video Again!')
                update_time = str(int(time.time()))
                if os.path.exists(ytdl_stamp):
                    os.remove(ytdl_stamp)
                if not os.path.exists(ytdl_stamp):
                    f = open(ytdl_stamp, 'w')
                    f.write(update_time)
                    f.close()
            else:
                send_notification('youtube-dl is already newest version')
        
    logger.debug('yt-link:>>{0}'.format(final_url))
    if mode == 'TITLE' and not final_url:
        final_url = url.split('/')[-1]
    return final_url

def get_final_for_resolution(url, youtube_dl, logger, ytdl_extra,
                             resolution=None, mode=None):
    final_url = ''
    if resolution:
        val = int(resolution)
    else:
        val = 720
    ytdl_list = [youtube_dl, '-F', url]
    if os.name == 'posix':
        content = subprocess.check_output(ytdl_list)
    else:
        content = subprocess.check_output(ytdl_list, shell=True)
    content = str(content, 'utf-8')
    lines = content.split('\n')
    lines = [re.sub('  +', ' ', i.strip()) for i in lines if i.strip()]
    arr = []
    audio_arr = []
    for i in lines:
        s = i.split(' ')
        res_val = s[2]
        if 'x' in res_val:
            res = res_val.split('x')[-1].strip()
            if res.isnumeric():
                res_int = int(res)
                if res_int <= val:
                    j = s[0]
                    arr.append((res, j, i))
        if 'audio only' in i:
            audio_arr.append(i)
    if arr:
        arr = sorted(arr, key=lambda x: x[0])
        logger.debug(arr)
        req = arr[-1]
        req_id = req[1]
        if audio_arr:
            audio_val = audio_arr[-1]
            audio_val_id = audio_val.split(' ')[0]
        arr.reverse()
        aud_vid = ''
        req_id_aud = req_id_vid = ''
        for i in arr:
            if 'video only' not in i[2]:
                aud_vid = i
                break
        if aud_vid:
            req_id_vid = aud_vid[1]
        if 'video only' in  req[2] and mode != 'offline':
            req_id_vid = req[1]
            req_id_aud = audio_val_id
        final_url_aud = final_url_vid = ''
        if req_id_vid:
            ytdl_list = [youtube_dl, '-f', req_id_vid, '-g', url]
            if os.name == 'posix':
                final_url = subprocess.check_output(ytdl_list)
            else:
                final_url = subprocess.check_output(ytdl_list, shell=True)
            final_url_vid = str(final_url, 'utf-8')
        if req_id_aud:
            ytdl_list = [youtube_dl, '-f', req_id_aud, '-g', url]
            if os.name == 'posix':
                final_url = subprocess.check_output(ytdl_list)
            else:
                final_url = subprocess.check_output(ytdl_list, shell=True)
            final_url_aud = str(final_url, 'utf-8')
        if final_url_vid and final_url_aud:
            final_url = final_url_vid + '::' + final_url_aud
        elif final_url_vid:
            final_url = final_url_vid
        logger.debug(final_url)
        logger.debug('mode={0}'.format(mode))
    return final_url
    
def get_best_link(url, youtube_dl, logger, mode=None):
    if mode == 'offline':
        ytdl_list = [youtube_dl, '--youtube-skip-dash-manifest', '-f', 
                     'best', '-g', '--playlist-end', '1', url]
    else:
        ytdl_list = [youtube_dl, '-g', url]
    if os.name == 'posix':
        final_url = subprocess.check_output(ytdl_list)
    else:
        final_url = subprocess.check_output(ytdl_list, shell=True)
    final_url = str(final_url, 'utf-8')
    final_url = final_url.strip()
    logger.info(final_url)
    if '\n' in final_url:
        vid, aud = final_url.split('\n')
        final_url = vid+'::'+aud
    return final_url
    
def get_yt_sub(url, name, dest_dir, tmp_dir, ytdl_path, log):
    global name_epn, dest_dir_sub, tmp_dir_sub, TMPFILE, logger
    logger = log
    if not ytdl_path:
        youtube_dl = 'youtube-dl'
    name_epn = name
    dest_dir_sub = dest_dir
    tmp_dir_sub = tmp_dir
    final_url = ''
    url = url.replace('"', '')
    m = []
    if '/watch?' in url:
        a = url.split('?')[-1]
        b = a.split('&')
        if b:
            for i in b:
                j = i.split('=')
                k = (j[0], j[1])
                m.append(k)
        else:
            j = a.split('=')
            k = (j[0], j[1])
            m.append(k)
        d = dict(m)
        print(d, '----dict--arguments---generated---')
        try:
            url = 'https://m.youtube.com/watch?v='+d['v']
        except:
            pass
    fh, TMPFILE = mkstemp(suffix=None, prefix='youtube-sub')
    dir_name, sub_name = os.path.split(TMPFILE)
    logger.info("TMPFILE={0};Output-dest={1};dir_name={2};sub_name={3}".format(TMPFILE, dest_dir_sub, dir_name, sub_name))
    if ytdl_path == 'default':
        youtube_dl = 'youtube-dl'
    else:
        youtube_dl = ytdl_path
    command = youtube_dl+" --all-sub --skip-download --output "+TMPFILE+" "+url
    logger.info(command)
    
    yt_sub_process = QtCore.QProcess()
    yt_sub_process.started.connect(yt_sub_started)
    yt_sub_process.readyReadStandardOutput.connect(partial(yt_sub_dataReady, yt_sub_process))
    yt_sub_process.finished.connect(yt_sub_finished)
    QtCore.QTimer.singleShot(1000, partial(yt_sub_process.start, command))

def yt_sub_started():
    print('Getting Sub')
    txt_notify = "Trying To Get External Subtitles Please Wait!"
    send_notification(txt_notify)
    
def yt_sub_dataReady(p):
    try:
        a = str(p.readAllStandardOutput(), 'utf-8').strip()
        print(a)
    except:
        pass
        
def yt_sub_finished():
    global name_epn, dest_dir_sub, tmp_dir_sub, TMPFILE
    name = name_epn
    dest_dir = dest_dir_sub
    dir_name, sub_name = os.path.split(TMPFILE)
    #print(dir_name, sub_name)
    m = os.listdir(dir_name)
    new_name = name.replace('/', '-')
    if new_name.startswith('.'):
        new_name = new_name[1:]
    sub_avail = False
    sub_ext = ''
    txt_notify = 'No Subtitle Found'
    for i in m:
        #j = os.path.join(dir_name, i)
        src_path = os.path.join(dir_name, i)
        if (i.startswith(sub_name) and i.endswith('.vtt') 
                and os.stat(src_path).st_size != 0):
            k1 = i.rsplit('.', 2)[1]
            k2 = i.rsplit('.', 2)[2]
            ext = k1+'.'+k2
            sub_ext = ext+', '+sub_ext
            dest_name = new_name + '.'+ ext
            #print(dest_name)
            dest_path = os.path.join(dest_dir, dest_name)
            #print(src_path, dest_path)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
                os.remove(src_path)
                sub_avail = True
    if sub_avail:
        txt_notify = "External Subtitle "+ sub_ext+" Available\nPress Shift+J to load"
    if os.path.exists(TMPFILE):
        os.remove(TMPFILE)
    send_notification(txt_notify)

def get_yt_sub_(url, name, dest_dir, tmp_dir, ytdl_path, log):
    global name_epn, dest_dir_sub, tmp_dir_sub, TMPFILE, logger
    logger = log
    if not ytdl_path:
        youtube_dl = 'youtube-dl'
    name_epn = name
    dest_dir_sub = dest_dir
    tmp_dir_sub = tmp_dir
    final_url = ''
    url = url.replace('"', '')
    m = []
    if '/watch?' in url:
        a = url.split('?')[-1]
        b = a.split('&')
        if b:
            for i in b:
                j = i.split('=')
                k = (j[0], j[1])
                m.append(k)
        else:
            j = a.split('=')
            k = (j[0], j[1])
            m.append(k)
        d = dict(m)
        print(d, '----dict--arguments---generated---')
        try:
            url = 'https://m.youtube.com/watch?v='+d['v']
        except:
            pass
    fh, TMPFILE = mkstemp(suffix=None, prefix='youtube-sub')
    dir_name, sub_name = os.path.split(TMPFILE)
    logger.info("TMPFILE={0};Output-dest={1};dir_name={2};sub_name={3}".format(TMPFILE, dest_dir_sub, dir_name, sub_name))
    if ytdl_path == 'default':
        youtube_dl = 'youtube-dl'
    else:
        youtube_dl = ytdl_path
    command = [youtube_dl, "--all-sub", "--skip-download", "--output", TMPFILE, url]
    logger.info(command)
    if os.name == 'posix':
        subprocess.call(command)
    else:
        subprocess.call(command, shell=True)
    
    name = name_epn
    dest_dir = dest_dir_sub
    dir_name, sub_name = os.path.split(TMPFILE)
    m = os.listdir(dir_name)
    new_name = name.replace('/', '-')
    if new_name.startswith('.'):
        new_name = new_name[1:]
    sub_avail = False
    sub_ext = ''
    txt_notify = 'No Subtitle Found'
    for i in m:
        #j = os.path.join(dir_name, i)
        src_path = os.path.join(dir_name, i)
        if (i.startswith(sub_name) and i.endswith('.vtt') 
                and os.stat(src_path).st_size != 0):
            k1 = i.rsplit('.', 2)[1]
            k2 = i.rsplit('.', 2)[2]
            ext = k1+'.'+k2
            sub_ext = ext+', '+sub_ext
            dest_name = new_name + '.'+ ext
            #print(dest_name)
            dest_path = os.path.join(dest_dir, dest_name)
            #print(src_path, dest_path)
            if os.path.exists(src_path):
                shutil.copy(src_path, dest_path)
                os.remove(src_path)
                sub_avail = True
    if sub_avail:
        txt_notify = "External Subtitle "+ sub_ext+" Available\nPress Shift+J to load"
    if os.path.exists(TMPFILE):
        os.remove(TMPFILE)
    send_notification(txt_notify)
    
