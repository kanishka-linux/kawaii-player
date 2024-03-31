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
                    youtube_dl = 'yt-dlp.exe'
                else:
                    youtube_dl = 'yt-dlp'
            else:
                if os.path.exists(ytdl_path):
                    youtube_dl = ytdl_path
                else:
                    if ytdl_path.endswith('yt-dlp') or ytdl_path.endswith('yt-dlp.exe'):
                        send_notification('Please Wait! Getting Latest youtube-dl')
                        youtube_dl = ytdl_path
                        if ytdl_path.endswith('yt-dlp'):
                            ccurl('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp'+'#-o#'+ytdl_path)
                            subprocess.Popen(['chmod', '+x', ytdl_path])
                        else:
                            ccurl('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe'+'#-o#'+ytdl_path)
                        update_time = str(int(time.time()))
                        if not os.path.exists(ytdl_stamp):
                            f = open(ytdl_stamp, 'w')
                            f.write(update_time)
                            f.close() 
                    else:
                        send_notification('youtube-dl path does not exists!')
                        youtube_dl = 'yt-dlp'
        else:
            youtube_dl = 'yt-dlp'
            
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
                    res = 1080
                elif quality == 'sd480p':
                    res = 480
                else:
                    res = 4000
                if (quality == 'best' and ytdl_path == 'default'
                        and self.ui.player_val != "libvlc"
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
            if ytdl_path.endswith('yt-dlp') or ytdl_path.endswith('yt-dlp.exe'):
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
                        ccurl('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp'+'#-o#'+ytdl_path)
                        subprocess.Popen(['chmod', '+x', ytdl_path])
                    else:
                        ccurl('https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe'+'#-o#'+ytdl_path)
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
        elif not final_url:
            final_url = url
        return final_url

    def get_final_for_resolution(self, url, youtube_dl, logger, ytdl_extra,
                                 resolution=None, mode=None, sub_folder=None):
        final_url = ''
        if resolution:
            res = int(resolution)
        else:
            res = 1080
        ytdl_list = [youtube_dl, '-q', '--no-warnings', '-j', '-s', '--all-sub', url]
        if os.name == 'posix':
            content = subprocess.check_output(ytdl_list, stderr= subprocess.STDOUT)
        else:
            content = subprocess.check_output(ytdl_list, stderr= subprocess.STDOUT, shell=True)
        content = str(content, 'utf-8')
        audio_dict = {}
        video_dict = {}
        best = None
        subs = {}
        js = json.loads(content)
        best = js.get('format_id')
        subs = js.get('subtitles')
        title = js.get('fulltitle')
        video_plus_audio = list(
                    filter(lambda x: x.get("acodec") != "none" and x.get("vcodec") != "none" and x.get("height") <= res, js.get("formats"))
                )
        audio_only = list(
                    filter(lambda x: x.get("acodec") != "none" and x.get("vcodec") == "none" and x.get("manifest_url") == None, js.get("formats"))
                )
        video_only = list(
                    filter(lambda x: x.get("acodec") == "none" and x.get("vcodec") != "none" and x.get("manifest_url") == None and x.get("height") <= res, js.get("formats"))
                )
        if self.ui.display_device == "rpitv":
            video_only = list(filter(lambda x: x.get("fps") < 60, video_only))
        video_only = sorted(video_only, key=lambda x: x.get("height"), reverse=True)
        audio_only = sorted(audio_only, key=lambda x: x.get("quality"), reverse=True)
        video_plus_audio = sorted(video_plus_audio, key=lambda x: x.get("height"), reverse=True)

        subs_dict = dict([(k, list(filter(lambda x: x.get("ext") == "vtt", v))) for k, v in subs.items()])

        ytid = js.get('id')
        sub_arr = []
        if sub_folder and not os.path.exists(sub_folder):
            os.makedirs(sub_folder)
        for key, value in subs_dict.items():
            if len(value) > 0:
                urlsub = value[0].get("url")
                ext = value[0].get('ext')
                path = '{}.{}.{}'.format(ytid, key, ext)
                sub_path = os.path.join(sub_folder, path)
                sub_arr.append([urlsub, sub_path, title])

        self.ui.gui_signals.subtitle_fetch(sub_arr)
        final_url = video_only[0].get("url") + "::" + audio_only[0].get("url")
        if "en" in subs_dict.keys():
            en_subs = subs_dict["en"]
            if len(en_subs) > 0:
                sub_url = en_subs[0].get("url")
                final_url = final_url + "::" + sub_url

        logger.debug("selected-video: {}".format(video_only[0]))
        logger.debug("selected-audio: {}".format(audio_only[0]))

        return final_url

    def post_subtitle_fetch(self, *args):
        result = args[-1]
        title = args[0]
        if result and result.out_file:
            self.ui.gui_signals.subtitle_apply(result.out_file, title)
