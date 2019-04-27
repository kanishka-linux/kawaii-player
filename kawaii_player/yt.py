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
import json
import subprocess
from PyQt5 import QtCore
from player_functions import send_notification, ccurl
from vinanti import Vinanti

class YTDL:
    
    def __init__(self, ui):
        self.ui = ui
        if os.name == 'posix':
            verify = True
        else:
            verify = False
        self.vnt = Vinanti(block=True, hdrs={'User-Agent':self.ui.user_agent}, verify=verify)

    def get_yt_url(self, url, quality, ytdl_path,
                   logger, mode=None, reqfrom=None):
        final_url = ''
        url = url.replace('"', '')
        m = []
        home_dir = self.ui.home_folder
        ytdl_stamp = os.path.join(home_dir, 'tmp', 'ytdl_update_stamp.txt')
        yt_sub_folder = os.path.join(home_dir, 'External-Subtitle')
        if ytdl_path:
            if ytdl_path == 'default':
                if os.name == "nt":
                    youtube_dl = 'youtube-dl.exe'
                else:
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
                if quality == 'sd':
                    res = 360
                elif quality == 'hd':
                    res = 720
                elif quality == 'sd480p':
                    res = 480
                else:
                    res = 4000
                if (quality == 'best' and ytdl_path == 'default'
                        and (reqfrom is None or reqfrom == 'desktop')
                        and not self.ui.gapless_network_stream):
                    if ytdl_extra:
                        final_url = 'ytdl:' + url
                    else:
                        final_url = url
                    time.sleep(1)
                else:
                    final_url = self.get_final_for_resolution(
                        url, youtube_dl, logger, ytdl_extra, resolution=res,
                        mode=mode, sub_folder=yt_sub_folder
                        )
                    if not final_url:
                        final_url = url
        except Exception as e:
            logger.error('--error in processing youtube url--{0}'.format(e))
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

    def get_final_for_resolution(self, url, youtube_dl, logger, ytdl_extra,
                                 resolution=None, mode=None, sub_folder=None):
        final_url = ''
        if resolution:
            res = int(resolution)
        else:
            res = 720
        ytdl_list = [youtube_dl, '-j', '-s', '--all-sub', url]
        if os.name == 'posix':
            content = subprocess.check_output(ytdl_list, stderr= subprocess.STDOUT)
        else:
            content = subprocess.check_output(ytdl_list, stderr= subprocess.STDOUT, shell=True)
        content = str(content, 'utf-8')
        if not content.startswith('{'):
            content = re.sub('[^\{]*', '', content, 1)
        audio_dict = {}
        video_dict = {}
        best = None
        subs = {}
        js = json.loads(content)
        best = js.get('format_id')
        subs = js.get('subtitles')
        title = js.get('fulltitle')
        if not subs:
            subs = {}
        for i, j in js.items():
            if isinstance(j, list):
                for k, l in enumerate(j):
                    if isinstance(l, dict):
                        attr_list = [
                            l.get('width'), l.get('height'),
                            l.get('ext'), l.get('abr'),
                            l.get('url')
                            ]
                        if l.get('width'):
                            video_dict.update({l.get('format_id'): attr_list.copy()})
                        else:
                            audio_dict.update({l.get('format_id'):attr_list.copy()})
        video_sort = [j for i, j in video_dict.items()]
        video_sort = sorted(video_sort, key=lambda x: int(x[0]), reverse=True)
        audio_sort = [j for i, j in audio_dict.items() if j[3] is not None]
        audio_sort = sorted(audio_sort, key=lambda x: int(x[3]), reverse=True)
        req_vid = None
        req_aud = None
        if best and '+' in best:
            vid, aud = best.split('+')
            req_vid = video_dict.get(vid)
            req_aud = audio_dict.get(aud)
        elif best:
            req_vid = video_dict.get(best)
            vid = aud = best
        if audio_sort:
            req_aud = audio_sort[0]
        for i in video_sort:
            if res >= int(i[0]):
                req_vid = i
                break
        ytid = js.get('id')
        sub_arr = []
        if sub_folder and not os.path.exists(sub_folder):
            os.makedirs(sub_folder)
        for key, value in subs.items():
            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict):
                        urlsub = entry.get('url')
                        ext = entry.get('ext')
                        if ext != 'ttml':
                            path = '{}.{}.{}'.format(ytid, key, ext)
                            sub_path = os.path.join(sub_folder, path)
                            sub_arr.append([urlsub, sub_path, title])
        final_url_vid = req_vid[-1]
        final_url_aud = req_aud[-1]
        if final_url_vid and final_url_aud:
            final_url = final_url_vid.strip() + '::' + final_url_aud.strip()
        elif final_url_vid:
            final_url = final_url_vid.strip()
        if mode == 'music':
            final_url = final_url_aud.strip()
            logger.debug('\n only audio required since music mode has been selected \n')
        elif mode == 'offline':
            final_url = '"{}"::"{}"::{}'.format(youtube_dl, url, "-o")
        if (sub_arr and self.ui.mpvplayer_val.processId() == 0) or not self.ui.gapless_network_stream:
            self.ui.gui_signals.subtitle_fetch(sub_arr)
        elif sub_arr and self.ui.gapless_network_stream:
            for sub in sub_arr:
                url, sub_path, title = sub
                if not os.path.isfile(sub_path):
                    self.vnt.get(url, out=sub_path)
                final_url = final_url + '::' + sub_path
                logger.debug(sub_path)
        if final_url.startswith("https://manifest."):
            final_url = url
        return final_url

    def post_subtitle_fetch(self, *args):
        result = args[-1]
        title = args[0]
        if result and result.out_file:
            self.ui.gui_signals.subtitle_apply(result.out_file, title)
    
