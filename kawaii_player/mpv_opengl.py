"""

    Opengl related Code adapted from https://gist.github.com/cosven/b313de2acce1b7e15afda263779c0afc
    
"""
import os
import re
import time
import sys
import platform
import locale
import itertools
import base64
import urllib.parse
import hashlib
from functools import partial 
from collections import namedtuple
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QMetaObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget, QApplication
from PyQt5.QtOpenGL import QGLContext
import subprocess

from OpenGL import GL

try:
    import mpv
except Exception as err:
    print(err)
    print("mpv opengl-render API not detected. Please install pympv")
    
from player import PlayerWidget, KeyBoardShortcuts

def get_proc_addr(_, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    addr = int(glctx.getProcAddress(name.decode('utf-8')))
    return addr

if sys.platform == 'win32':
    from PyQt5.QtOpenGL import QGLContext
    try:
        from ctypes import windll
    except Exception as err:
        print(err)
elif sys.platform == 'darwin':
    from OpenGL.GLUT import glutGetProcAddress
else:
    from OpenGL.platform import PLATFORM
    from ctypes import c_char_p, c_void_p

def getProcAddress(proc: bytes) -> int:
    if sys.platform == 'win32':
        _ctx = QGLContext.currentContext()
        if _ctx is None:
            return 0
        _gpa = (_ctx.getProcAddress, proc.decode())
    elif sys.platform == 'darwin':
        _gpa = (glutGetProcAddress, proc)
    else:
        _getProcAddress = PLATFORM.getExtensionProcedure
        _getProcAddress.argtypes = [c_char_p]
        _getProcAddress.restype = c_void_p
        _gpa = (_getProcAddress, proc)
    return _gpa[0](_gpa[1]).__int__()


class QProcessExtra(QtCore.QProcess):
    
    def __init__(self, parent=None, ui=None, logr=None, tmp=None):
        super(QProcessExtra, self).__init__(parent)
        self.ui = ui
        
    def filter_command(self, cmd):
        file_path = re.search('"(?P<file>(.?)*)"', cmd).group('file')
        command = re.sub('"(.?)*"', "", cmd)
        arr = command.split()
        arr.insert(1, file_path)
        try:
            self.ui.tab_5.mpv.command(*arr)
        except Exception as err:
            print(err)
        return file_path

    def get_vlc_output(self, cmd):
        p1 = subprocess.Popen(["echo", cmd], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["socat", "-", self.ui.mpv_socket], stdin=p1.stdout, stdout=subprocess.PIPE)
        (data, b) = p2.communicate()
        print(data.decode("utf-8"))
        data = data.decode("utf-8")
        if data:
            data = data.strip()
        return data
        
    def write(self, cmd):
        if self.ui.player_val == "libmpv" and hasattr(self.ui.tab_5, "mpv") and self.ui.tab_5.mpv.get_property("idle-active") is False:
            print(cmd)
            cmd = str(cmd, "utf-8").strip()
            cmd_arr = cmd.split()
            print(cmd_arr)
            show_duration = None
            if cmd_arr[0] == "show-text":
                cmd_tail = cmd.split(" ", 1)[-1]
                if cmd_tail.startswith('"'):
                   cmd = cmd.replace('"', "")
                elif cmd_tail.startswith("'"):
                   cmd = cmd.replace("'", '')
                if "filename" in cmd_tail:
                    filename = self.ui.tab_5.mpv.get_property('filename')
                    cmd_tail = "filename: {}".format(filename)
                elif "chapter" in cmd_tail:
                    try:
                        chapter = self.ui.tab_5.mpv.get_property('chapter')
                        total = self.ui.tab_5.mpv.get_property('chapters')
                        meta = self.ui.tab_5.mpv.get_property('chapter-metadata')
                        if meta:
                            title = meta.get("TITLE")
                        else:
                            title = None
                        if title:
                            cmd_tail = "{} / {}".format(title, total)
                        else:
                            cmd_tail = "Chapter: {} / {}".format(chapter, total)
                    except Exception as err:
                        cmd_tail = "Chapters not available"
                elif "${aid}" in cmd_tail:
                    aid = self.ui.tab_5.mpv.get_property('aid')
                    cmd_tail = self.ui.tab_5.get_track_property(aid, "audio")
                    if cmd_tail is None:
                        cmd_tail = "Audio: Disabled"
                elif "${info}" in cmd_tail:
                    cmd_tail = "Info"
                elif "${sid}" in cmd_tail:
                    sid = self.ui.tab_5.mpv.get_property('sid')
                    cmd_tail = self.ui.tab_5.get_track_property(sid, "sub")
                    if cmd_tail is None:
                        cmd_tail = "Subtitle: Disabled"
                elif "${sub-delay}" in cmd_tail:
                    sub_delay = self.ui.tab_5.mpv.get_property('sub-delay')
                    if sub_delay:
                        sub_delay = "{} ms".format(int(sub_delay * 1000))
                    cmd_tail = "Sub delay: {}".format(sub_delay)
                elif "${audio-delay}" in cmd_tail:
                    audio_delay = self.ui.tab_5.mpv.get_property('audio-delay')
                    if audio_delay:
                        audio_delay = "{} ms".format(int(audio_delay * 1000))
                    cmd_tail = "A-V delay: {}".format(audio_delay)
                elif 'osd-sym-cc' in cmd:
                    print(cmd)
                    if "pause" in cmd or "2000" in cmd:
                        try:
                            time_pos = self.ui.tab_5.mpv.get_property('time-pos')
                        except Exception as err:
                            time_pos = 0
                        display_string = self.ui.tab_5.display_play_pause_string(time_pos)
                        if "pause-string-with-details" in cmd:
                            if self.ui.tab_5.audio_info_text:
                                display_string = "{}  {}".format(display_string, self.ui.tab_5.audio_info_text)
                            if self.ui.tab_5.subtitle_info_text:
                                display_string = "{}  {}".format(display_string, self.ui.tab_5.subtitle_info_text)
                            display_string = "{}\n{}".format(display_string, self.ui.epn_name_in_list)
                        if self.ui.tab_5.mpv_api == "opengl-render":
                            cmd_tail = self.ui.tab_5.mpv.get_property('osd-sym-cc') + " " + display_string
                        else:
                            cmd_tail = self.ui.tab_5.mpv.osd_sym_cc + b" " + bytes(display_string, "utf-8")
                    else:
                        cmd_list = cmd.split()
                        cmd_list = cmd_list[1:]
                        if self.ui.tab_5.mpv_api == "opengl-render":
                            cmd_tail = self.ui.tab_5.mpv.get_property('osd-sym-cc') + ' ' + ''.join(cmd_list)
                        else:
                            cmd_tail = self.ui.tab_5.mpv.get_property('osd-sym-cc') + b'' + bytes(''.join(cmd_list), "utf-8")
                            
                if cmd_tail:    
                    self.ui.tab_5.mpv.command("show-text", cmd_tail)
            elif cmd_arr[0] == "sub-add":
                sub_file = self.filter_command(cmd)
                self.ui.tab_5.mpv.command("show-text", "Adding-subtitle: {}".format(sub_file), 2000)
            elif cmd_arr[0] == "loadfile":
                file_path = self.filter_command(cmd)
                self.ui.tab_5.mpv.command("show-text", "loading: {}".format(file_path), 2000)
            else:
                try:
                    if cmd_arr[0] in ["stop", "quit"]:
                        self.ui.quit_now = True
                    if "set pause" in cmd or "cycle pause" in cmd:
                        try:
                            time_pos = self.ui.tab_5.mpv.get_property('time-pos')
                        except Exception as err:
                            time_pos = 0
                        self.ui.tab_5.mpv.command(*cmd_arr)
                        display_string = self.ui.tab_5.display_play_pause_string(time_pos)
                        if self.ui.tab_5.mpv_api == "opengl-render":
                            cmd_tail = self.ui.tab_5.mpv.get_property('osd-sym-cc') + " " + display_string
                        else:
                            cmd_tail = self.ui.tab_5.mpv.osd_sym_cc + b" " + bytes(display_string, "utf-8")
                        self.ui.tab_5.mpv.command("show-text", cmd_tail, 2000)
                    elif cmd_arr[0] == "set":
                        cmd_name = cmd_arr[1]
                        cmd_val = cmd_arr[-1].replace('"', '')
                        self.ui.tab_5.mpv.set_property(cmd_name, cmd_val)
                    else:
                        self.ui.tab_5.mpv.command(*cmd_arr)
                except Exception as e:
                    print(e)
                    self.ui.tab_5.mpv.command("show-text", "not found: {}, {}".format(cmd, e), 5000)
        elif self.ui.player_val == "libmpv" and hasattr(self.ui.tab_5, "mpv") and self.ui.tab_5.mpv.get_property("idle-active") is True:
            print("nothing is playing")
        elif self.ui.mpv_input_ipc_server and self.ui.player_val.lower() == "mpv":
            p1 = subprocess.Popen(["echo", cmd], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["socat", "-", self.ui.mpv_socket], stdin=p1.stdout, stdout=subprocess.PIPE)
            p2.communicate()
        elif self.ui.player_val == "libvlc":
            cmd_str = cmd.decode("utf-8")
            cmd_str = cmd_str.strip()
            print(cmd_str, "cmd-vlc")
            if "seek" in cmd_str:
                cmd = cmd_str
                cmd_arr = cmd.split()
                seek_val = int(cmd_arr[1])
                cur_val = self.ui.vlc_mediaplayer.get_time()
                if cur_val:
                    cur_val = int(cur_val) + (seek_val*1000)
                    self.ui.vlc_mediaplayer.set_time(cur_val)
                    self.ui.vlc_show_osd("time", 1000)
            elif "pause" in cmd_str:
                self.ui.vlc_mediaplayer.pause()
            elif "cycle sub" in cmd_str:
                self.ui.vlc_cycle_subtitle()
            elif "cycle audio" in cmd_str:
                self.ui.vlc_cycle_audio()
            elif "set volume" in cmd_str:
                val = cmd_str.split()[-1]
                val = int(val)
                self.ui.vlc_mediaplayer.audio_set_volume(val)
                self.ui.vlc_set_osd("volume: {}".format(val), 1000)
            elif "add volume" in cmd_str:
                val = cmd_str.split()[-1]
                val = int(val)
                initial_volume = self.ui.vlc_mediaplayer.audio_get_volume()
                new_volume = initial_volume + val
                self.ui.vlc_mediaplayer.audio_set_volume(new_volume)
                self.ui.vlc_set_osd("volume: {}".format(new_volume), 1000)
        elif self.ui.player_val in ["vlc", "cvlc"]:
            cmd_str = cmd.decode("utf-8")
            if cmd_str.startswith("key"):
                cmd = cmd_str
            elif "fullscreen" in cmd_str:
                cmd = "fullscreen"
            elif "seek" in cmd_str:
                cmd = cmd_str
                cmd_arr = cmd.split()
                val = int(cmd_arr[1])

                if val == 10:
                    cmd = "key key-jump+extrashort"
                elif val == -10:
                    cmd = "key key-jump-extrashort"
                elif val == 60:
                    cmd = "key key-jump+medium"
                elif val == -60:
                    cmd = "key key-jump-medium"
                elif val == 300:
                    cmd = "key key-jump+long"
                elif val == -300:
                    cmd = "key key-jump-long"
                else:
                    cmd = cmd_str
            elif "play" in cmd_str or "pause" in cmd_str:
                cmd = "key key-play-pause"
            elif "stop" in cmd_str or "quit" in cmd_str:
                cmd = "shutdown"
            else:
                cmd = cmd_str

            print(cmd, cmd_str, "--cmd--")
            p1 = subprocess.Popen(["echo", cmd], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["socat", "-", self.ui.mpv_socket], stdin=p1.stdout, stdout=subprocess.PIPE)
            (data, b) = p2.communicate()
            print(data.decode("utf-8"))
            if "get_length" in cmd:
                data = data.decode("utf-8")
                data = data.strip()
                if data.isnumeric():
                    self.ui.mplayerLength = int(data)
        else:
            super(QProcessExtra, self).write(cmd)
            
class KeyT(QtCore.QThread):
    mpv_cmd = pyqtSignal(list)
    def __init__(self, ui, event, cmd):
        self.ui = ui
        QtCore.QThread.__init__(self)
        self.event = event
        self.cmd = cmd
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        if self.event is not None and self.cmd:
            try:
                self.ui.tab_5.mpv.command(*self.cmd)
            except Exception as err:
                print(err)

class PlayerStatusObserver(QtCore.QThread):
    def __init__(self, ui):
        self.ui = ui
        QtCore.QThread.__init__(self)
        self.show_status = False
        self.remove_external_files = False
        
    def __del__(self):
        self.wait()
                                
    def core_observer_status(self):
        idle_active = self.ui.tab_5.mpv.get_property('idle-active')
        core_idle = self.ui.tab_5.mpv.get_property('core-idle')
        if idle_active in [False, 'no'] and core_idle in [True, 'yes']:
            self.ui.mpvplayer_val.write(b'show-text osd-sym-cc pause-string-with-details')
                
    def run(self):
        while True:
            if self.show_status:
                self.core_observer_status()
            if self.remove_external_files:
                try:
                    self.ui.tab_5.mpv.command("sub-remove")
                    self.ui.logger.info('removing external subtitles')
                except Exception as err:
                    self.ui.logger.debug('no external subtitle loaded')
                try:
                    self.ui.tab_5.mpv.command("audio-remove")
                    self.ui.logger.info('removing external audio')
                except Exception as err:
                    self.ui.logger.debug('no external audio loaded')
                self.remove_external_files = False
            time.sleep(1)
        

class ExecCommand(QtCore.QThread):
    def __init__(self, ui, func_list):
        self.ui = ui
        QtCore.QThread.__init__(self)
        self.func_list = func_list.copy()
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        if self.func_list:
            try:
                sub_gather_func, try_sub_func = self.func_list
                sub_arr, sub_lang = sub_gather_func()
                try_sub_func(sub_arr.copy(), sub_lang.copy())
            except Exception as err:
                print(err)
            
class InitAgainThread(QtCore.QThread):
    mpv_cmd = pyqtSignal(list)
    def __init__(self, uiw, me):
        global ui
        self.ui = uiw
        ui = uiw
        QtCore.QThread.__init__(self)
        self.me = me
        self.mpv_cmd.connect(mpv_cmd_direct)
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        path = self.me.mpv.get_property("path")
        self.me.mpv.command('quit-watch-later')
        if self.me.mpv_gl:
            self.me.mpv_gl.close()
        aud = None
        if path and not os.path.exists(path):
            aud = self.me.get_external_audio_file()
        func = partial(self.me.initializeGL)
        self.mpv_cmd.emit([func, self.me.mpv_api, self.me, path, aud])
            
@pyqtSlot(list)
def mpv_cmd_direct(cmd):
    global ui
    func, api, me, path, aud = cmd
    site = ui.get_parameters_value(st='site')['site']
    try:
        pls_pos = me.mpv.get_property("playlist-pos")
        if (path and os.path.exists(path) 
                and site.lower() in ["video", "music", "none", "myserver"]):
            me.mpv.set_property("playlist-pos", pls_pos)
        else:
            if aud:
                me.audio = aud
            me.mpv.command("loadfile", path)
            me.mpv.set_property('loop-playlist', 'no')
            me.mpv.set_property('loop-file', 'no')
    except Exception as err:
        print(err)
        
def mpv_log(level, component, msg):
    print('[{}] {}: {}'.format(level, component, msg))
    
class MpvOpenglWidget(QOpenGLWidget):
    
    def __init__(self, parent=None, ui=None, logr=None, tmp=None, mpv_api=None, app=None):
        global gui, MainWindow, screen_width, screen_height, logger
        super().__init__(parent)
        gui = ui
        self.ui = ui
        MainWindow = parent
        logger = logr
        self.app = app
        self.mpv_api = mpv_api
        logger.debug("using {}".format(self.mpv_api))
        self.args_dict = {'vo':'libmpv', 'ytdl':True,
                         'loop_playlist':'inf', 'idle':True,
                         'audio-display': 'attachment',
                         'osd_duration': 4000, 'osd_font_size': 25,
                         'cache': 'auto', 'cache-secs': 120}
        if platform.system().lower() == "darwin":
            self.args_dict.update({"ao":"coreaudio"})
        elif os.name == "posix":
            if hasattr(self.ui, "desktop_session") and self.ui.desktop_session == "lxde-pi":
                self.args_dict.update({"ao":"alsa"})
            else:
                self.args_dict.update({"ao":"pulse"})
        elif os.name == "nt":
            self.args_dict.update({"ao":"wasapi"})
        self.default_args = self.args_dict.copy()
        if gui.mpvplayer_string_list and gui.use_custom_config_file:
            self.create_args_dict()
        elif not gui.use_custom_config_file:
            self.parse_mpv_config_file()
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.track_list = None
        self.playlist_backup = False

        self.arrow_timer = QtCore.QTimer()
        self.arrow_timer.timeout.connect(self.arrow_hide)
        self.arrow_timer.setSingleShot(True)

        self.pause_timer = QtCore.QTimer()
        self.pause_timer.timeout.connect(self.pause_unpause)
        self.pause_timer.setSingleShot(True)

        self.fs_timer = QtCore.QTimer()
        self.fs_timer.timeout.connect(self.toggle_fullscreen_mode)
        self.fs_timer.setSingleShot(True)
        
        self.mx_timer = QtCore.QTimer()
        self.mx_timer.timeout.connect(MainWindow.showMaximized)
        self.mx_timer.setSingleShot(True)

        self.fs_timer_now = QtCore.QTimer()
        self.fs_timer_now.timeout.connect(self.only_fs_tab)
        self.fs_timer_now.setSingleShot(True)

        self.player_val = "libmpv"
        screen_width = gui.screen_size[0]
        screen_height = gui.screen_size[1]
        self.custom_keys = {}
        self.event_dict = {'ctrl':False, 'alt':False, 'shift':False}
        self.key_map = KeyBoardShortcuts(gui, self)
        self.mpv_default = self.key_map.get_default_keys()
        self.mpv_custom, self.input_conf_list = self.key_map.get_custom_keys(gui.mpv_input_conf)
        self.custom_keys, _ = self.key_map.get_custom_keys(gui.custom_key_file)
        self.function_map = self.key_map.function_map()
        self.non_alphanumeric_keys = self.key_map.non_alphanumeric_keys()
        self.alphanumeric_keys = self.key_map.alphanumeric_keys()
        if self.custom_keys:
            self.mpv_default = self.custom_keys.copy()
        self.shift_keys = [
            '?', '>', '<', '"', ':', '}', '{', '|', '+', '_', 'sharp',
            ')', '(', '*', '&', '^', '%', '$', '#', '#', '@', '!', '~'
            ]
        self.aboutToResize.connect(self.resized)
        self.aboutToCompose.connect(self.compose)
        self.audio = None
        self.subtitle = None
        self.ratio = None
        self.dim = None
        self.chapter_list = None
        self.prefetch_url = None
        self.window_title_set = False
        self.mpv_queue_tuple = None
        
        self.mpv_default_modified = {}
        for key, value in self.mpv_default.items():
            if "seek" in value:
                self.mpv_default_modified.update({key:value.split()})
        
        self.modifiers = set([QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier])
        self.total_keys = {**self.alphanumeric_keys, **self.non_alphanumeric_keys}
        self.seek_now = False
        self.aspect_map = {'0':'Original', '1':'16:9', '2':'4:3', '3':'2.35:1', '4':'Disabled'}
        self.player_volume = None
        self.initial_volume_set = False
        self.mpv_reinit = False
        self.key_thread = KeyT(self.ui, None, None)
        self.init_again_thread = InitAgainThread(self.ui, self)
        self.key_thread.start()
        self.player_observer_thread = PlayerStatusObserver(self.ui)
        self.player_observer_thread.start()
        self.sub_id = -1
        self.audio_id = -1
        self.dpr = 1.0
        self.fake_mousemove_event = ("libmpv", False)
        self.playing_queue = False
        self.exec_thread = ExecCommand(self.ui, [])
        self.started = False
        self.file_size = 0
        self.first_play = True
        self.stop_msg = None
        self.pointer_moved = False
        self.audio_track_count = 0
        self.subtitle_track_count = 0
        self.try_subtitle_path = None
        self.audio_info_text = None
        self.subtitle_info_text = None

        self.mpv_gl = None
        self.init_opengl_render()
        self.frameSwapped.connect(self.swapped, Qt.DirectConnection)

    def init_opengl_cb(self):
        try:
            self.mpv = MPV(log_handler=mpv_log, **self.args_dict)
        except Exception as err:
            logger.error("\nSome wrong config option. Restoring default\n")
            self.mpv = MPV(**self.default_args)
        self.mpv.observe_property("time-pos", self.time_observer)
        self.mpv.observe_property("eof-reached", self.eof_observer)
        self.mpv.observe_property("idle-active", self.idle_observer)
        self.mpv.observe_property("duration", self.time_duration)
        self.mpv.observe_property("sub", self.sub_changed)
        self.mpv.observe_property("audio", self.audio_changed)
        self.mpv.observe_property("seeking", self.player_seeking)
        self.mpv.observe_property("ao-volume", self.volume_observer)
        self.mpv.observe_property("quit-watch-later", self.quit_watch_later)
        self.mpv.observe_property("playback-abort", self.playback_abort_observer)
        self.mpv.observe_property("playlist-pos", self.playlist_position_observer)
        self.mpv.observe_property("core-idle", self.core_observer)
        self.init_mpv_opengl_cb()

    def init_opengl_render(self):
        self.mpv = mpv.Context()
        self.mpv.initialize()
        self.mpv.set_log_level('no')
        for key, value in self.args_dict.items():
            key = key.replace('_', '-')
            if isinstance(value, bool):
                value = 'yes' if value else 'no'
            try:
                self.mpv.set_option(key, value)
            except Exception as err:
                logger.error("Error in setting property: {} => {}, Correct config options.".format(key, value))
            if key == "msg-level":
                try:
                    if "=" in value:
                        self.mpv.set_log_level(value.rsplit('=', 1)[-1])
                    else:
                        self.mpv.set_log_level(value)
                except Exception as err:
                    logger.error("Error setting log-level")
        
        self.mpv.observe_property('time-pos')
        self.mpv.observe_property('duration')
        self.mpv.observe_property('eof-reached')
        self.mpv.observe_property('idle-active')
        self.mpv.observe_property('sub')
        self.mpv.observe_property('audio')
        self.mpv.observe_property('seeking')
        self.mpv.observe_property('ao-volume')
        self.mpv.observe_property('quit-watch-later')
        self.mpv.observe_property('playback-abort')
        self.mpv.observe_property('playlist-pos')
        self.mpv.observe_property('core-idle')
        self.observer_map = {
                    'time-pos': self.time_observer,
                    'eof-reached': self.eof_observer,
                    'idle-active': self.idle_observer,
                    'duration': self.time_duration,
                    'sub': self.sub_changed,
                    'audio': self.audio_changed,
                    'seeking': self.player_seeking,
                    'ao-volume': self.volume_observer,
                    'quit-watch-later': self.quit_watch_later,
                    'playback-abort': self.playback_abort_observer,
                    'playlist-pos': self.playlist_position_observer,
                    'core-idle': self.core_observer
                    }
        
        self.mpv.set_wakeup_callback(self.eventHandler)
    
    def eventHandler(self):
        while self.mpv:
            try:
                event = self.mpv.wait_event(1)
                if event.id in {mpv.Events.none, mpv.Events.shutdown}:
                    break
                elif event.id == mpv.Events.log_message:
                    event_log = event.data
                    log_msg = "[{}] {}-{}".format(event_log.level, event_log.prefix, event_log.text.strip())
                    print(log_msg)
                elif event.id == mpv.Events.property_change:
                    event_prop = event.data
                    observer_function = self.observer_map.get(event_prop.name)
                    if observer_function:
                        observer_function(event_prop.name, event_prop.data)
            except mpv.MPVError as err:
                logger.error(err)

    def initializeGL(self):
            try:
                self.mpv_gl = mpv.OpenGLRenderContext(self.mpv, getProcAddress)
                self.mpv_gl.set_update_callback(self.maybe_update)
            except Exception as err:
                logger.error(err)
        
    def paintGL(self):
        w = int(self.width()* self.dpr)
        h = int(self.height()* self.dpr)
        func = partial(self.mpv_gl.render, opengl_fbo={"w": w, "h": h, "fbo": self.defaultFramebufferObject()}, flip_y=True)
        func()
        
    @pyqtSlot()
    def maybe_update(self):
        self.update()

    def on_update(self, ctx=None):
        QMetaObject.invokeMethod(self, 'maybe_update')
        
    def on_update_fake(self, ctx=None):
        pass

    def swapped(self):
        if self.mpv_gl:
            self.mpv_gl.report_swap()
        
    def closeEvent(self, _):
        if self.mpv_gl:
            self.mpv_gl.close()
        self.mpv.terminate()
        
    def init_mpv_again(self):
        if self.mpv_api == "opengl-render" and platform.system().lower() in ["linux", "windows"]:
            if not self.init_again_thread.isRunning():
                self.init_again_thread = InitAgainThread(self.ui, self)
                self.init_again_thread.start()
        else:
            pass
            
    def only_fs_tab(self):
        self.setMinimumWidth(MainWindow.width())
        self.setMinimumHeight(MainWindow.height())
        
    def parse_mpv_config_file(self, file_path=None):
        self.setup_args_from_gui()
        if file_path is None or not os.path.exists(file_path):
            file_path = os.path.join(os.path.expanduser("~"), ".config/mpv/config")
        if os.path.exists(file_path):
            txt = open(file_path).read()
            if txt:
                txt_list = txt.split('\n')
            else:
                txt_list = []
            for line in txt_list:
                line = line.strip()
                if line and not line.startswith('#'):
                    line = re.sub('#[^\n]*', '', line)
                    if '=' in line:
                        key, value = line.split('=', 1)
                    else:
                        key = line
                        value = "yes"
                    value = self.sanitize_values(value)
                    key = key.replace("-", "_")
                    logger.info((key, value))
                    self.args_dict.update({key:value})
            self.args_dict.update({"vo":"libmpv"})
            
    def sanitize_values(self, value):
        if isinstance(value, str) and value.startswith('"'):
            value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
        if isinstance(value, str) and value.startswith("'"):
            value = value[1:]
            if value.endswith("'"):
                value = value[:-1]
        return value
    
    def setup_args_from_gui(self):
        self.args_dict.update({'screenshot-directory': gui.screenshot_directory})
        if gui.gsbc_dict:
            for key, value in gui.gsbc_dict.items():
                self.args_dict.update({key:value})
        if gui.subtitle_dict and gui.apply_subtitle_settings:
            for key, value in gui.subtitle_dict.items():
                self.args_dict.update({key:value})
        elif gui.subtitle_dict and not gui.apply_subtitle_settings:
            scale = gui.subtitle_dict.get('sub-scale')
            if scale:
                self.args_dict.update({'sub-scale': scale})
        if gui.gapless_playback or gui.gapless_network_stream:
            self.args_dict.update({'gapless-audio':True})
            self.args_dict.update({'prefetch-playlist': True})
        if isinstance(gui.cache_pause_seconds, int) and gui.cache_pause_seconds > 0:
            self.args_dict.update({'cache-pause': True})
            self.args_dict.update({'cache-pause-wait': gui.cache_pause_seconds})
        
    def create_args_dict(self):
        self.setup_args_from_gui()
        for param in gui.mpvplayer_string_list:
            if "=" in param:
                k, v = param.split("=", 1)
            else:
                k = param
                v = True
            if k.startswith('--'):
                k = k[2:]
            k = k.replace("-", "_")
            v = self.sanitize_values(v)
            self.args_dict.update({k:v})
        self.args_dict.update({"vo":"libmpv"})
            
    def set_mpvplayer(self, player=None, mpvplayer=None):
        if mpvplayer:
            self.mpvplayer = mpvplayer
        else:
            self.mpvplayer = self.ui.mpvplayer_val
        if player:
            self.player_val = player
        else:
            self.player_val = self.ui.player_val

    def pause_unpause(self, status=None):
        if status == "pause":
            self.mpv.command("set", "pause", "yes")
        else:
            self.mpv.command("set", "pause", "no")
            
    def compose(self):
        pass

    def resized(self):
        self.setFocus()
        if self.ui.device_pixel_ratio == 0:
            self.dpr = self.devicePixelRatio()
        else:
            self.dpr = self.ui.device_pixel_ratio
        logger.debug('Device Pixel Ratio: {}'.format(self.dpr))
            
    def arrow_hide(self):
        if gui.player_val in ['mpv', 'mplayer', 'libmpv']:
            if self.hasFocus():
                self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                logger.debug('player has focus')
                #QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor);
            else:
                logger.debug('player not focussed')
            if (self.ui.fullscreen_video and self.hasFocus() and self.ui.tab_6.isHidden()
                        and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                self.ui.frame1.hide()

    def get_track_property(self, id_val, id_type):
        txt = None
        if self.track_list:
            for i in self.mpv.get_property("track-list"):
                idval = i.get("id")
                idtype = i.get("type")
                if idval == id_val and idtype == id_type:
                    lang = i.get("lang")
                    if idtype and len(idtype) > 2:
                        idtype = idtype[:1]
                    if idtype:
                        idtype = idtype.title()
                    if lang is None:
                        lang = "auto"
                    txt = "{}:{} ({})".format(idtype, idval, lang)
                    break
        return txt
        
    def get_external_audio_file(self):
        aud = None
        for i in self.mpv.get_property("track-list"):
            idval = i.get("id")
            idtype = i.get("type")
            if idtype == "audio":
                if i.get("external") and i.get("selected"):
                    aud = i.get("external-filename")
                    break
        return aud
        
    def player_seeking(self, _name, value):
        logger.info("{} {}".format(_name, value))
        if value is True:
            self.seek_now = True
        else:
            self.seek_now = False

    def playback_abort_observer(self, name, value):
        site = self.ui.get_parameters_value(st='site')['site']
        logger.debug('\n..{} {}..\n'.format(name, value))
        if self.ui.epn_clicked and value is True and self.ui.playlist_continue:
            if self.ui.cur_row < self.ui.list2.count():
                self.ui.list2.setCurrentRow(self.ui.cur_row)
                item = self.ui.list2.item(self.ui.cur_row)
                if self.first_play and site == "Music":
                    self.mpv.command("stop")
                    self.ui.player_stop.clicked_emit()
                    self.first_play = False
                if item:
                    self.ui.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
                    logger.debug("trying again..............")
        
    def volume_observer(self, _name, value):
        logger.info("{} {}".format(_name, value))
        if value and isinstance(value, float):
            self.player_volume = value
            self.ui.player_volume = str(int(value))

    def quit_watch_later(self, _name, value):
        logger.info("{} {}".format(_name, value))        
        if value is True:
            self.rem_properties(self.ui.final_playing_url, rem_quit=1, seek_time=self.ui.progress_counter)
        
    def sub_changed(self, _name, value):
        logger.debug('{} {} {}'.format(_name, value, "--sub--"))
        self.sub_id = value
        txt = "Sub: None"
        if value is False:
            gui.subtitle_track.setText(txt)
        else:
            txt = self.get_track_property(value, "sub")
            if txt:
                gui.subtitle_track.setText(txt)
        self.subtitle_info_text = txt
                
    def audio_changed(self, _name, value):
        self.audio_id = value
        logger.debug("{} {} {}".format(_name, value, "--audio--"))
        txt = "A: None"
        if value is False:
            gui.audio_track.setText(txt)
        else:
            txt = self.get_track_property(value, "audio")
            if txt:
                gui.audio_track.setText(txt)
        self.audio_info_text = txt

    def display_play_pause_string(self, value):
        display_string = "None"
        if value is not None:
            fn = lambda val: time.strftime('%H:%M:%S', time.gmtime(int(val)))
            gui.progress_counter = value
            try:
                cache = self.mpv.get_property('demuxer-cache-duration')
            except Exception as err:
                cache = 0
            if gui.mplayerLength > 0:
                percent = int((value/gui.mplayerLength)*100)
            else:
                percent = 0
            if not cache:
                cache = 0
            if gui.mplayerLength > 0:
                display_string = '{}%  {} / {}  Cache: {}s'.format(percent, fn(value), fn(gui.mplayerLength), int(cache))
        return display_string

    def playlist_position_observer(self, _name, value):
        logger.debug("{}-{}".format(_name, value))
        if platform.system().lower() == "darwin":
            self.ui.gui_signals.cursor_method((self, "show"))
        if isinstance(value, int) and value >= 0:
            cur_row = value
            if (self.mpv.get_property('playlist-count') > 1 and cur_row < gui.list2.count() and gui.list2.count() > 1):
                gui.cur_row = cur_row
                gui.list2.setCurrentRow(gui.cur_row)
                self.set_window_title_and_epn(row=cur_row)
                if gui.view_mode == "thumbnail_light" and gui.cur_row < gui.list_poster.count():
                    gui.list_poster.setCurrentRow(gui.cur_row)
        if platform.system().lower() == "darwin":
            self.ui.gui_signals.cursor_method((self, "hide"))
        
    def time_observer(self, _name, value):
        if value is not None:
            if abs(value - gui.progress_counter) >= 0.5:
                display_string = self.display_play_pause_string(value)
                value_int = int(value)
                if self.file_size:
                    file_size = round((self.file_size)/(1024*1024), 2)
                    display_string = "{} Size: {} M".format(display_string, file_size)
                if not gui.frame1.isHidden() and not self.seek_now:
                    gui.slider.valueChanged.emit(value_int)
                    gui.gui_signals.display_string((display_string))
                if not gui.new_tray_widget.isHidden():
                    gui.new_tray_widget.update_signal.emit(display_string, int(value))

                if value_int % 30 == 0:
                    self.send_fake_event("mouse_release")
            if self.audio and int(value) in range(0, 3):
                if self.mpv.get_property("loop-file") is False:
                    self.mpv.command("audio-add", self.audio, "select")
                    logger.debug("{} {}".format("adding..audio..", self.audio))
                self.audio = None
            if self.subtitle and int(value) in range(0, 3):
                if self.mpv.get_property("loop-file") is False:
                    if "::" in self.subtitle:
                        for sub in self.subtitle.split("::"):
                            self.mpv.command("sub-add", sub)
                    else:
                        self.mpv.command("sub-add", self.subtitle, "select")
                    logger.debug("\n{} {}\n".format("adding..subtitle..", self.subtitle))
                self.subtitle = None
            if gui.gapless_network_stream and not gui.queue_url_list:
                if gui.progress_counter > int(gui.mplayerLength/2):
                    if (gui.cur_row + 1) < gui.list2.count():
                        item_index = gui.cur_row + 1
                    else:
                        item_index = 0
                    if gui.tmp_pls_file_dict.get(item_index) is False and gui.list2.count() > 1:
                        gui.start_gapless_stream_process(item_index)
            if self.prefetch_url and isinstance(self.prefetch_url, tuple) and gui.gapless_network_stream:
                finalUrl, row, type_val = self.prefetch_url
                gui.epnfound_now_start_prefetch(finalUrl, row, type_val)
                self.prefetch_url = None

    def send_fake_event(self, val):
        self.fake_mousemove_event = ("libmpv", True)
        pos = self.cursor().pos()
        if not self.pointer_moved:
            new_point = QtCore.QPoint(pos.x() + 1, pos.y())
            self.pointer_moved = True
        else:
            new_point = QtCore.QPoint(pos.x() - 1, pos.y())
            self.pointer_moved = False
        self.cursor().setPos(new_point)
        if val == "mouse_release":
            event = QtGui.QMouseEvent(
                        QtCore.QEvent.MouseButtonRelease,
                        new_point,
                        QtCore.Qt.LeftButton,
                        QtCore.Qt.LeftButton,
                        QtCore.Qt.NoModifier,
                    )
        elif val == "mouse_move":
            event = QtGui.QMouseEvent(
                        QtCore.QEvent.MouseMove,
                        new_point,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoModifier,
                    )
        self.ui.gui_signals.mouse_move_method((self, event))
        
    def rem_properties(self, final_url, rem_quit, seek_time):
        self.ui.history_dict_obj_libmpv.update(
                {
                    final_url:[
                        seek_time, time.time(), self.sub_id, self.audio_id,
                        rem_quit, self.player_volume, self.ui.mpvplayer_aspect_cycle
                        ]
                }
            )
        logger.info("remember-- {}".format(self.ui.history_dict_obj_libmpv.get(self.ui.final_playing_url)))

    def core_observer(self, _name, value):
        logger.debug("{} {}".format("core..observer.. value", value))
        if value is True and self.mpv.get_property("idle-active") is False:
            cache = self.mpv.get_property('demuxer-cache-idle')
            time_pos = self.mpv.get_property('time-pos')
            if time_pos and time_pos > 3:
                self.ui.mpvplayer_val.write(b'show-text osd-sym-cc pause-string')
                self.player_observer_thread.show_status = True
            else:
                self.player_observer_thread.show_status = False
        else:
            self.player_observer_thread.show_status = False
            if self.mpv.get_property("idle-active") is False:
                time_pos = self.mpv.get_property('time-pos')
                if time_pos and time_pos > 3:
                    self.ui.mpvplayer_val.write(b'show-text osd-sym-cc pause-string')
                    
    def eof_observer(self, _name, value):
        logger.debug("{} {}".format("eof.. value", value, _name))
        if value is True or value is None:
            if value is True:
                self.rem_properties(self.ui.final_playing_url, 0, 0)
            if self.ui.queue_url_list:
                self.check_queued_item()
            elif not gui.queue_url_list and self.playlist_backup:
                if gui.cur_row < gui.list2.count():
                    gui.list2.setCurrentRow(gui.cur_row)
                    item = gui.list2.item(gui.cur_row)
                    if item:
                        gui.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
                self.playlist_backup = False
        if (value in [None, True] and (self.ui.quit_really == "yes" or not self.ui.playlist_continue)):
            self.stop_msg = "openglwidget"
            self.mpv.command("stop")
            self.ui.player_stop.clicked_emit()

    def check_queued_item(self):
        if self.ui.queue_url_list:
            item = self.ui.queue_url_list[0]
            self.ui.queue_url_list = self.ui.queue_url_list[1:]
            self.ui.gui_signals.delete_queue_item(0)
            if '\t' in item:
                item_list = item.split('\t')
                title = item_list[0]
                url = item_list[1]
            else:
                title = item.rsplit('/')[-1]
                if not title:
                    title = item
                url = item
            if title and title.startswith("#"):
                title = title[1:]
            self.mpv.command("playlist-clear")
            url = url.replace('"', "")
            self.mpv.command("loadfile", url)
            self.ui.final_playing_url = url
            self.set_window_title_and_epn(title=title)
            self.playlist_backup = True

    def gather_external_sub(self, row=None):
        new_path = self.ui.final_playing_url.replace('"', '')
        sub_arr = []
        slang_list = self.mpv.get_property("slang")
        if not slang_list:
            slang_list = ["mr", "en", "fr", "es", "jp"]
        if os.path.exists(new_path):
            sub_name_bytes = bytes(new_path, 'utf-8')
            h = hashlib.sha256(sub_name_bytes)
            sub_name = h.hexdigest()
            sub_path_vtt = os.path.join(self.ui.yt_sub_folder, sub_name+'.vtt')
            sub_path_srt = os.path.join(self.ui.yt_sub_folder, sub_name+'.srt')
            sub_path_ass = os.path.join(self.ui.yt_sub_folder, sub_name+'.ass')
            if os.path.exists(sub_path_vtt):
                sub_arr.append({"path":sub_path_vtt, "type":"vtt", lang: "default"})
            if os.path.exists(sub_path_srt):
                sub_arr.append({"path":sub_path_srt, "type":"srt", lang: "default"})
            if os.path.exists(sub_path_ass):
                sub_arr.append({"path":sub_path_ass, "type":"ass", lang: "default"})
        if self.ui.cur_row < len(self.ui.epn_arr_list):
            if row and row < len(self.ui.epn_arr_list):
                ourl = self.ui.epn_arr_list[row]
            else:
                ourl = self.ui.epn_arr_list[self.ui.cur_row]
            if '\t' in ourl:
                param = None
                ourl = ourl.split('\t')[1]
                ourl = ourl.replace('"', "")
                if ourl.startswith("http"):
                    u = urllib.parse.urlparse(ourl)
                    if 'youtube.com' in u.netloc and 'watch' in u.path:
                        for q in u.query.split('&'):
                            if q.startswith('v='):
                                param = q.rsplit('=')[-1]
                                break
                    if param:
                        ext_fn = lambda x: [x+".vtt", x+".srt", x+".ass"]
                        
                        ext_list = list(itertools.chain.from_iterable(list(map(ext_fn, slang_list))))
                        for ext in ext_list:
                            lang, file_type = ext.split(".")
                            sub_arr.append(
                                {"path": os.path.join(self.ui.yt_sub_folder, param+"."+ext),
                                "type": file_type, "lang": lang}
                                )
        return sub_arr, slang_list

    def try_external_sub(self, sub_arr, slang_list):
        for sub in sub_arr.copy():
            path = sub.get("path")
            sub_type = sub.get("type")
            lang = sub.get("lang")
            if os.path.exists(path):
                logger.debug(path)
                if lang in slang_list or lang == "default":
                    opt = "select"
                else:
                    opt = "auto"
                self.mpv.command("sub-add", path, opt, "External-Subtitle", lang)
                    
    def idle_observer(self, _name, value):
        if value is True:
            self.disable_screen_auto_turnoff(False)
        site = self.ui.get_parameters_value(st='site')['site']
        logger.debug("...{}={}, quit-now={} site={}".format(value, _name, gui.quit_now, site))
        if (value is True and self.started
                and gui.list2.count() > 1
                and gui.quit_now is False
                and site.lower() not in ["video", "music", "none", "myserver"]):
            if site.lower() == "playlists":
                self.ui.stale_playlist = True
            if self.mpv.get_property("playlist-count") == 1 and self.ui.playlist_continue:
                logger.debug("only single playlist..")
                self.mpv.set_property('loop-playlist', 'no')
                self.mpv.set_property('loop-file', 'no')
                self.mpv.command('stop')
                gui.cur_row = (gui.cur_row + 1) % gui.list2.count()
                gui.list2.setCurrentRow(gui.cur_row)
                item = gui.list2.item(gui.cur_row)
                if item:
                    gui.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
            self.set_window_title_and_epn(row=gui.cur_row)
            
    def set_window_title_and_epn(self, title=None, row=None):
        if title is None:
            if isinstance(row, int) and row < self.ui.list2.count():
                item = gui.list2.item(row)
            else:
                item = gui.list2.item(gui.cur_row)
            if item:
                epn = item.text()
            else:
                epn = "Unknown"
            if epn.startswith(gui.check_symbol):
                epn = epn[1:]
        else:
            epn = title
        MainWindow.windowTitleChanged.emit(epn)
        gui.epn_name_in_list = epn
        self.mpv.command("show-text", epn, 2000)

    def disable_screen_auto_turnoff(self, value):
        try:
            if os.name == "nt":
                if value:
                    windll.kernel32.SetThreadExecutionState(0x80000002)
                else:
                    windll.kernel32.SetThreadExecutionState(0x80000000)
        except Exception as err:
            logger.error(err)

    def time_duration(self, _name, value):
        if value is None:
            value = self.mpv.get_property("duration")
        if value is not None:
            if self.mpv_reinit:
                self.mpv.start = "none"
                self.mpv_reinit = False
            self.ui.quit_really = False
            self.ui.epn_clicked = False
            self.started = True
            z = 'duration is {:.2f}s'.format(value)
            #gui.progressEpn.setFormat((z))
            gui.mplayerLength = int(value)
            self.disable_screen_auto_turnoff(True)
            try:
                self.file_size = self.mpv.get_property('file-size')
            except Exception as err:
                self.file_size = 0
            try:
                self.mpv.set_property("ao-volume", str(gui.player_volume))
            except Exception as err:
                logger.error(err)
            gui.progress_counter = 0
            gui.slider.setRange(0, int(gui.mplayerLength))
            gui.final_playing_url = path = self.mpv.get_property('path')
            self.track_list = self.mpv.get_property('track-list')
            self.audio_track_count = [track.get('type') == 'audio' for track in self.track_list].count(True)
            self.subtitle_track_count = [track.get('type') == 'sub' for track in self.track_list].count(True)
            abs_path = None
            self.try_subtitle_path = None
            filename = None
            if path.startswith('http') and '/master_abs_path=' in path:
                try:
                    abs_path = path.split('/master_abs_path=', 1)[1]
                    new_path = str(base64.b64decode(abs_path).decode('utf-8'))
                    self.try_subtitle_path = new_path + '.original.subtitle'
                    if "/&master_token=" in new_path:
                        new_path = path.rsplit("/&master_token=")[0]
                    filename = new_path.rsplit("/")[-1]
                    filename = urllib.parse.unquote(filename)
                except Exception as err:
                    logger.error(err)
            elif path.startswith('http') and '/abs_path=' in path:
                self.try_subtitle_path = path + ".original.subtitle"
                filename = path.rsplit("/")[-1]
                filename = urllib.parse.unquote(filename)

            # list all mpv-properties
            #property_list = self.mpv.get_property("property-list")
            #property_list.sort()
            #for prop in property_list:
            #    print(prop)

            self.chapter_list = self.mpv.get_property('chapter-list')
            if not self.initial_volume_set:
                logger.debug("setting..........volume.......{}".format(gui.player_volume))
                try:
                    self.mpv.set_property('ao-volume', int(gui.player_volume))
                    self.initial_volume_set = True
                except Exception as err:
                    logger.error(err)
            if self.ui.pc_to_pc_casting == "slave":
                saved_url = self.ui.final_playing_url.rsplit("/&master_token=")[0]
            else:
                saved_url = self.ui.final_playing_url
            if saved_url in self.ui.history_dict_obj_libmpv:
                seek_time, cur_time, sub_id, audio_id, rem_quit, vol, asp = self.ui.history_dict_obj_libmpv.get(saved_url)
                if asp == -1 or asp == "-1" or asp is None:
                    asp = "0"
                aspect_val = self.ui.mpvplayer_aspect_float.get(str(asp))
                logger.info("restoring.. -> {}".format(self.ui.history_dict_obj_libmpv.get(self.ui.final_playing_url)))
                if aspect_val and gui.restore_aspect:
                    self.mpv.set_property('video-aspect', aspect_val)
                elif not gui.restore_aspect:
                    self.mpv.command("show-text", "Bad Aspect Property: {}".format(aspect_val))
                try:
                    self.mpv.set_property('sid', sub_id)
                except:
                    pass
                try:
                    self.mpv.set_property('aid', audio_id)
                except:
                    pass
                if gui.restore_volume and vol:
                    try:
                        self.mpv.set_property('ao-volume', str(vol))
                    except Exception as err:
                        logger.error(err)
                param_dict = gui.get_parameters_value(o='opt', s="site")
                site = param_dict["site"]
                opt = param_dict["opt"]
                if rem_quit or (site.lower() == "video" and opt.lower() == "history"):
                    self.mpv.command("seek", seek_time, "absolute")
            if not self.exec_thread.isRunning() and not self.playlist_backup:
                func_gather_sub = partial(self.gather_external_sub, self.ui.cur_row)
                func_try_sub = self.try_external_sub
                self.exec_thread = ExecCommand(self.ui, [func_gather_sub, func_try_sub])
                self.exec_thread.start()
            if self.ui.pc_to_pc_casting == 'slave' and 'master_abs_path=' in self.ui.final_playing_url:
                self.ui.add_external_subtitle.clicked_emit()
        
    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            if not self.key_thread.isRunning():
                cmd = self.get_mpv_cmd(event)
                if cmd:
                    self.key_thread = KeyT(self.ui, event, cmd.copy())
                    self.key_thread.start()
                else:
                    self.keyPressEventO(event)
        else:
            self.keyPressEventO(event)
            
    def get_mpv_cmd(self, event):
        key = self.total_keys.get(event.key())
        if key and event.modifiers() not in self.modifiers:
            cmd = self.mpv_default_modified.get(key)
        else:
            cmd = None
        return cmd
            
    def keyPressEventO(self, event):
        key = self.total_keys.get(event.key())
        if key and event.modifiers() not in self.modifiers:
            cmd = self.mpv_default_modified.get(key)
        else:
            cmd = None
        if cmd:
            logger.debug(cmd)
            try:
                self.mpv.command(*cmd)
            except Exception as err:
                logger.error(err)
        else:
            PlayerWidget.keyPressEvent(self, event)
        
    def keyReleaseEvent(self, event):
        PlayerWidget.keyReleaseEvent(self, event)
        
    def mouseDoubleClickEvent(self, event):
        self.toggle_fullscreen_mode()
        for i in self.event_dict:
            self.event_dict[i] = False
            
    def mouseMoveEvent(self, event):
        self.setFocus()
        PlayerWidget.mouseMoveEvent(self, event)

    def mouseEnterEvent(self, event):
        self.setFocus()
        self.ui.gui_signals.cursor_method((self, "hide"))

    def leaveEvent(self, event):
        self.ui.gui_signals.cursor_method((self, "show"))
        
    def change_aspect_ratio(self, key=None):
        if key is None:
            self.ui.mpvplayer_aspect_cycle = (self.ui.mpvplayer_aspect_cycle + 1) % 5
        else:
            self.ui.mpvplayer_aspect_cycle = int(key)
        aspect_val = self.ui.mpvplayer_aspect_float.get(str(self.ui.mpvplayer_aspect_cycle))
        self.mpv.set_property('video-aspect', aspect_val)
        aspect_prop = self.aspect_map.get(str(self.ui.mpvplayer_aspect_cycle))
        self.mpv.command("show-text", "Video-Aspect: {}".format(aspect_prop))

    def start_player_loop(self):
        PlayerWidget.start_player_loop(self)

    def show_hide_status_frame(self):
        PlayerWidget.show_hide_status_frame(self)

    def toggle_play_pause(self):
        PlayerWidget.toggle_play_pause(self)

    def load_subtitle_from_file(self):
        PlayerWidget.load_subtitle_from_file(self)

    def load_subtitle_from_network(self):
        PlayerWidget.load_subtitle_from_network(self)
        
    def add_external_audio(self):
        fname = QtWidgets.QFileDialog.getOpenFileNames(
                MainWindow, 'Select One or More Files', self.ui.last_dir)
        sub_dict = {}
        if fname and fname[0]:
            for aud in fname[0]:
                self.ui.last_dir, file_choose = os.path.split(fname[0][0])
                logger.debug('{}, {}'.format(aud, file_choose))
                self.mpv.command("audio-add", aud, "select")

    def load_external_sub(self, mode=None, subtitle=None, title=None):
        if mode is None:
            fname = QtWidgets.QFileDialog.getOpenFileNames(
                    MainWindow, 'Select Subtitle file', self.ui.last_dir)
            if fname:
                logger.info(fname)
                if fname[0]:
                    self.ui.last_dir, file_choose = os.path.split(fname[0][0])
                    title_sub = fname[0][0]
                    if self.player_val == "mplayer":
                        txt = '\n sub_load "{}" \n'.format(title_sub)
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        gui.mpvplayer_val.write(txt_b)
                    else:
                        txt = '\n sub-add "{}" select \n'.format(title_sub)
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        gui.mpvplayer_val.write(txt_b)
            self.ui.acquire_subtitle_lock = False
        elif mode == 'network':
            site = self.ui.get_parameters_value(st='site')['site']
            if site.lower() == 'myserver':
                title_sub = self.ui.final_playing_url + '.original.subtitle'
                if self.player_val == "mplayer":
                    txt = '\n sub_load "{}" \n'.format(title_sub)
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    gui.mpvplayer_val.write(txt_b)
                else:
                    txt = '\n sub-add "{}" select \n'.format(title_sub)
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    gui.mpvplayer_val.write(txt_b)
            else:
                logger.warning('Not Allowed')
        elif mode == 'drop':
            title_sub = subtitle
            logger.debug(title_sub)
            if self.player_val == "mplayer":
                txt = '\n sub_load "{}" \n'.format(title_sub)
                txt_b = bytes(txt, 'utf-8')
                logger.info("{0} - {1}".format(txt_b, txt))
                gui.mpvplayer_val.write(txt_b)
            else:
                txt = '\n sub-add "{}" select \n'.format(title_sub)
                txt_b = bytes(txt, 'utf-8')
                logger.info("{0} - {1}".format(txt_b, txt))
                gui.mpvplayer_val.write(txt_b)
        elif mode in ['load', 'auto']:
            ext_find = subtitle.split('.')
            if len(ext_find) >= 2:
                lang = ext_find[-2]
                ext = ext_find[-1]
            else:
                lang = ext_find[-1]
                ext = ext_find[-1]
            if self.ui.player_val == "mplayer":
                cmd = 'sub_load "{}"'.format(subtitle)
            else:
                cmd = 'sub-add "{}" auto {} {}'.format(subtitle, lang, lang)
            if self.ui.list2.currentItem():
                row = self.ui.list2.currentRow()
            else:
                row = 0
            if mode == 'auto':
                self.ui.mpv_execute_command(cmd, row, 1000)
            else:
                self.ui.mpv_execute_command(cmd, row)

    def add_parameter(self, cmd):
        if ' ' in cmd:
            cmd_list = cmd.split(' ')
            cmd_name = cmd_list[1]
            if cmd_name in ['volume', 'ao-volume']:
                self.change_volume(cmd)
            elif cmd_name in ['brightness', 'contrast', 'saturation', 'hue', 'gamma']:
                cmd_val = cmd_list[-1]
                try:
                    cmd_val_int = int(cmd_val)
                    slider = eval('self.ui.frame_extra_toolbar.{}_slider'.format(cmd_name))
                    slider.setValue(slider.value() + cmd_val_int)
                except Exception as err:
                    logger.error(err)
            else:
                cmd = '\n {} \n'.format(cmd)
                command_string = bytes(cmd, 'utf-8')
                logger.debug(command_string)
                self.ui.mpvplayer_val.write(command_string)

    def change_volume(self, command):
        vol = None
        volume = False
        msg = None
        new_command = None
        if ' ' in command:
            vol_int = command.split(' ')[-1]
            if vol_int.startswith('-') or vol_int.startswith('+'):
                vol = vol_int[1:]
            else:
                vol = vol_int
            if vol.isnumeric():
                volume = True
        slider = self.ui.frame_extra_toolbar.slider_volume
        if command.startswith('add volume') and volume:
            value = slider.value() + int(vol_int)
            if self.ui.volume_type == 'ao-volume':
                msg = '\n print-text volume-print=${volume} \n'
            if value <= 100:
                slider.setValue(value)
            else:
                new_command = '\n add volume {} \n'.format(vol_int)
                msg = '\n print-text volume-print=${volume} \n'
        elif command.startswith('add ao-volume') and volume:
            slider.setValue(slider.value() + int(vol_int))
            if self.ui.volume_type == 'volume':
                msg = '\n print-text ao-volume-print=${ao-volume} \n'
        if msg:
            if new_command:
                self.ui.mpvplayer_val.write(bytes(new_command, 'utf-8'))
            msg = bytes(msg, 'utf-8')
            self.ui.mpvplayer_val.write(msg)
            
    def toggle_fullscreen_mode(self):
        wd = self.width()
        ht = self.height()
        val = self.mpv.get_property('fullscreen')
        if (val is False or val is None) or (val and not self.ui.fullscreen_video):
            self.mpv.set_property('fullscreen', 'yes')
            self.player_fs(mode='fs')
        else:
            self.mpv.set_property('fullscreen', 'no')
            self.player_fs(mode='nofs')
                

    def get_next(self):
        pls_count = self.mpv.get_property('playlist-count')
        pls_pos = self.mpv.get_property('playlist-pos')
        print(pls_count, pls_pos)
        if pls_count is not None and pls_pos is not None and pls_count == pls_pos + 1:
            self.mpv.set_property('playlist-pos', 0)
        else:
            self.mpv.command("playlist-next")

    def get_previous(self):
        pls_count = self.mpv.get_property('playlist-count')
        pls_pos = self.mpv.get_property('playlist-pos')
        print(pls_count, pls_pos)
        if pls_count is not None and pls_pos is not None and pls_pos == 0:
            self.mpv.set_property('playlist-pos', pls_count - 1)
        else:
            self.mpv.command("playlist-prev")

    def quit_player(self, msg=None):
        if msg == "rem_quit":
            self.rem_properties(self.ui.final_playing_url, 1, self.ui.progress_counter)
        else:
            self.rem_properties(self.ui.final_playing_url, 0, self.ui.progress_counter)
        self.initial_volume_set = False
        self.player_observer_thread.remove_external_files = True
        self.audio = None
        self.subtitle = None
        self.ui.quit_now = True
        self.mpv.command("stop")
        self.stop_msg = "openglwidget"
        self.ui.player_stop.clicked_emit()
        self.ui.tab_5.setMinimumWidth(0)
        self.ui.tab_5.setMinimumHeight(0)
        self.setParent(MainWindow)
        self.ui.gridLayout.addWidget(self, 0, 1, 1, 1)
        self.ui.superGridLayout.addWidget(self.ui.frame1, 1, 1, 1, 1)
        self.setMouseTracking(True)
        self.showNormal()
        self.setFocus()
        
    def remember_and_quit(self):
        self.quit_player(msg="rem_quit")

    def cycle_player_subtitle(self):
        self.ui.mpvplayer_val.write(b'\n cycle sub \n')
        self.ui.mpvplayer_val.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
        self.ui.mpvplayer_val.write(b'\n show-text "${sid}" \n')
                
    def cycle_player_audio(self):
        self.ui.mpvplayer_val.write(b'\n cycle audio \n')
        self.ui.mpvplayer_val.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
        self.ui.mpvplayer_val.write(b'\n show-text "${aid}" \n')
                
    def stop_after_current_file(self):
        self.ui.quit_really = "yes"
        msg = '"Stop After current file"'
        msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
        gui.mpvplayer_val.write(msg_byt)

    def player_fs(self, mode=None):
        if platform.system().lower() == "darwin":
            self.mpv.command("set", "pause", "yes")
        if not self.ui.idw or self.ui.idw == self.ui.get_winid():
            if self.player_val == "libmpv":
                if mode == 'fs':
                    if not self.ui.tab_6.isHidden():
                        self.ui.fullscreen_mode = 1
                    elif not self.ui.float_window.isHidden():
                        self.ui.fullscreen_mode = 2
                    else: 
                        self.ui.fullscreen_mode = 0
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                    
                    self.ui.gridLayout.setSpacing(0)
                    self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                    
                    self.ui.text.hide()
                    self.ui.label.hide()
                    self.ui.frame1.hide()
                    self.ui.tab_6.hide()
                    self.ui.goto_epn.hide()
                    if self.ui.wget.processId() > 0 or self.ui.video_local_stream or self.ui.is_torrent_active:
                        self.ui.progress.hide()
                        if not self.ui.torrent_frame.isHidden():
                            self.ui.torrent_frame.hide()

                    self.ui.list2.hide()
                    self.ui.frame_extra_toolbar.hide()
                    self.ui.frame_extra_toolbar.playlist_hide = False
                    self.ui.list6.hide()
                    self.ui.list1.hide()
                    self.ui.frame.hide()
                    self.ui.dockWidget_3.hide()
                    if self.ui.orientation_dock == 'right':
                        self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 1, 1, 1)
                    self.show()
                    self.setFocus()
                    if not self.ui.tab_2.isHidden():
                        self.ui.tab_2.hide()
                    if self.player_val in self.ui.playback_engine:
                        self.ui.gui_signals.cursor_method((MainWindow, "hide"))
                    if platform.system().lower() == "darwin" and self.ui.osx_native_fullscreen:
                        #MainWindow.hide()
                        self.setParent(None)
                        self.ui.tab_5_layout.insertWidget(1, self.ui.frame1)
                    else:
                        MainWindow.showFullScreen()
                    self.ui.fullscreen_video = True
                    
                    self.showFullScreen()
                    self.setFocus()
                    self.setMouseTracking(True)
                    if platform.system().lower() == "darwin":
                        self.setMinimumWidth(MainWindow.width())
                    if self.ui.widgets_on_video:
                        self.ui.gridLayoutVideo.addWidget(self.ui.frame1, 2, 1, 1, 1)
                elif mode == "nofs":
                    #self.hide()
                    if self.ui.widgets_on_video:
                        self.ui.superGridLayout.addWidget(self.ui.frame1, 1, 1, 1, 1)
                    if platform.system().lower() == "darwin":
                        self.mpv.command("set", "pause", "yes")
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(5)
                    self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.list2.show()
                    self.ui.btn20.show()
                    if self.ui.wget.processId() > 0 or self.ui.video_local_stream or self.ui.is_torrent_active:
                        self.ui.progress.show()
                    self.ui.frame1.show()
                    if self.player_val in self.ui.playback_engine:
                        self.ui.gui_signals.cursor_method((MainWindow, "show"))
                    if not self.ui.force_fs:
                        #MainWindow.showNormal()
                        MainWindow.show()
                        if platform.system().lower() in ["darwin", "linux"]:
                            MainWindow.showMaximized()
                    param_dict = self.ui.get_parameters_value(tl='total_till')
                    total_till = param_dict['total_till']
                    if total_till != 0 or self.ui.fullscreen_mode == 1:
                        self.ui.tab_6.show()
                        self.ui.list2.hide()
                        self.ui.frame_extra_toolbar.hide()
                        self.ui.frame_extra_toolbar.playlist_hide = False
                        self.ui.goto_epn.hide()
                    if self.ui.btn1.currentText().lower() == 'youtube':
                        self.ui.list2.hide()
                        self.ui.frame_extra_toolbar.hide()
                        self.ui.frame_extra_toolbar.playlist_hide = False
                        self.ui.goto_epn.hide()
                        self.ui.tab_2.show()
                    if self.ui.orientation_dock == 'right':
                        self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 5, 2, 1)
                    self.ui.fullscreen_video = False
                    if platform.system().lower() == "darwin" and self.ui.osx_native_fullscreen:
                        self.setParent(MainWindow)
                    
                    self.ui.gridLayout.addWidget(self, 0, 1, 1, 1)
                    self.ui.superGridLayout.addWidget(self.ui.frame1, 1, 1, 1, 1)
                    self.setMouseTracking(True)
                    self.showNormal()
                    self.setFocus()
                    #MainWindow.show()
                    #MainWindow.showMaximized()
                    self.setMinimumWidth(0)
                    self.setMinimumHeight(0)
                    if not self.mx_timer.isActive() and platform.system().lower() != "darwin":
                        self.mx_timer.start(1000) 
            else:
                if self.ui.detach_fullscreen:
                    self.ui.detach_fullscreen = False
                    self.ui.float_window.showNormal()
                    self.ui.tray_widget.right_menu._detach_video()
                    self.ui.tab_5.setFocus()
                else:
                    if not self.ui.float_window.isHidden():
                        if not self.ui.float_window.isFullScreen():
                            self.ui.float_window.showFullScreen()
                        else:
                            self.ui.float_window.showNormal()
        else:
            self.ui.tab_6_size_indicator.append(self.ui.tab_6.width())
            param_dict = self.ui.get_parameters_value(icn='iconv_r_indicator', i='iconv_r')
            iconv_r_indicator = param_dict['iconv_r_indicator']
            iconv_r = param_dict['iconv_r']
            cur_label_num = self.ui.cur_row
            if not MainWindow.isHidden():
                if self.ui.video_mode_index in [5,6,7]:
                    pass
                else:
                    if iconv_r_indicator:
                        iconv_r = iconv_r_indicator[0]
                    self.ui.set_parameters_value(iconv=iconv_r)
                    widget = eval("self.ui.label_epn_"+str(cur_label_num))
                    col = (cur_label_num%iconv_r)
                    row = 2*int(cur_label_num/iconv_r)
                    new_pos = (row, col)
                    print(new_pos)
                    if not MainWindow.isFullScreen():
                        cur_label = cur_label_num
                        index = self.ui.gridLayout2.indexOf(widget)
                        logger.debug(index)
                        if index >= 0:
                            self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                            self.ui.tab_6.hide()
                            self.ui.gridLayout.addWidget(widget, 0, 1, 1, 1)
                            widget.setMaximumSize(QtCore.QSize(screen_width, screen_height))
                            self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                            self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout1.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout2.setContentsMargins(0, 0, 0, 0)
                            self.ui.gridLayout.setSpacing(0)
                            self.ui.gridLayout1.setSpacing(0)
                            self.ui.gridLayout2.setSpacing(0)
                            self.ui.superGridLayout.setSpacing(0)
                            if self.ui.orientation_dock == 'right':
                                self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 1, 1, 1)
                            MainWindow.showFullScreen()
                            self.ui.fullscreen_video = True
                    else:
                        w = float((self.ui.tab_6.width()-60)/iconv_r)
                        h = int(w/self.ui.image_aspect_allowed)
                        width=str(int(w))
                        height=str(int(h))
                        r = self.ui.current_thumbnail_position[0]
                        c = self.ui.current_thumbnail_position[1]
                        cur_label = cur_label_num
                        self.ui.gridLayout2.addWidget(widget, r, c, 1, 1, QtCore.Qt.AlignCenter)
                        QtWidgets.QApplication.processEvents()
                        MainWindow.showNormal()
                        MainWindow.showMaximized()
                        yy = widget.y()
                        self.ui.scrollArea1.verticalScrollBar().setValue(yy)
                        QtWidgets.QApplication.processEvents()
                        self.ui.frame1.show()
                        self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                        self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout1.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout2.setContentsMargins(5, 5, 5, 5)
                        self.ui.gridLayout.setSpacing(5)
                        self.ui.gridLayout1.setSpacing(5)
                        self.ui.gridLayout2.setSpacing(5)
                        self.ui.superGridLayout.setSpacing(5)
                        self.ui.tab_6.show()
                        if self.ui.orientation_dock == 'right':
                            self.ui.superGridLayout.addWidget(self.ui.dockWidget_3, 0, 5, 2, 1)
                        QtWidgets.QApplication.processEvents()
                        widget.setFocus()
                        QtCore.QTimer.singleShot(1000, self.ui.update_thumbnail_position)
                        self.ui.fullscreen_video = False
            else:
                if not self.ui.float_window.isHidden():
                    if not self.ui.float_window.isFullScreen():
                        widget = eval("self.ui.label_epn_"+str(cur_label_num))
                        index = self.ui.gridLayout2.indexOf(widget)
                        print(index, '--index--')
                        self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                        self.ui.float_window.showFullScreen()
                    else:
                        self.ui.float_window.showNormal()
        if not self.pause_timer.isActive() and platform.system().lower() == "darwin":
            self.pause_timer.start(1000)
                        

    
