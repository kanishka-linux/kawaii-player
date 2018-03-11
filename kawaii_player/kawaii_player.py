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

OSNAME = os.name

import sys
if getattr(sys, 'frozen', False):
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(sys.executable))
else:
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(__file__))
print(BASEDIR, BASEFILE, os.getcwd())
sys.path.insert(0, BASEDIR)
RESOURCE_DIR = os.path.join(BASEDIR, 'resources')
print(sys.path)

import urllib.parse
import urllib.request
import imp
import shutil
from io import StringIO, BytesIO
from tempfile import mkstemp, mkdtemp
import re
import subprocess
import lxml
import calendar
import datetime
import time
import random
import textwrap
from functools import partial
import weakref
import socket
import struct
import sqlite3
import json
import base64
import ipaddress
import ssl
import hashlib
import uuid
import platform
import logging
import pickle
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn, TCPServer
import pycurl
from bs4 import BeautifulSoup
import PIL
from PIL import Image, ImageDraw
from PyQt5 import QtCore, QtGui, QtNetwork, QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from player_functions import write_files, ccurl, send_notification
from player_functions import wget_string, open_files, get_config_options
from player_functions import get_tmp_dir, naturallysorted, set_logger
from player_functions import get_home_dir, change_opt_file, create_ssl_cert
from player_functions import set_user_password, get_lan_ip
from yt import get_yt_url, get_yt_sub_
from ds import CustomList
from meta_engine import MetaEngine

HOME_DIR = get_home_dir()
HOME_OPT_FILE = os.path.join(HOME_DIR, 'other_options.txt')
BROWSER_BACKEND = get_config_options(HOME_OPT_FILE, 'BROWSER_BACKEND')
QT_WEB_ENGINE = True
print(BROWSER_BACKEND)
if (not BROWSER_BACKEND or (BROWSER_BACKEND != 'QTWEBKIT' 
        and BROWSER_BACKEND != 'QTWEBENGINE')):
    if os.path.exists(HOME_OPT_FILE) and not BROWSER_BACKEND:
        write_files(HOME_OPT_FILE, 'BROWSER_BACKEND=QTWEBENGINE', line_by_line=True)
    else:
        change_opt_file(HOME_OPT_FILE, 'BROWSER_BACKEND=', 'BROWSER_BACKEND=QTWEBENGINE')
    BROWSER_BACKEND = 'QTWEBENGINE'

if BROWSER_BACKEND == 'QTWEBENGINE':
    try:
        from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from browser import Browser
        from hls_webengine.hls_engine import BrowseUrlT
        QT_WEB_ENGINE = True
        print('Using QTWEBENGINE')
    except Exception as err_msg:
        print(err_msg)
        try:
            from PyQt5 import QtWebKitWidgets
            from PyQt5.QtWebKitWidgets import QWebView
            from browser_webkit import Browser
            from hls_webkit.hls_engine_webkit import BrowseUrlT
            QT_WEB_ENGINE = False
            print('Using QTWEBKIT')
            change_opt_file(HOME_OPT_FILE, 'BROWSER_BACKEND=', 'BROWSER_BACKEND=QTWEBKIT')
            BROWSER_BACKEND = 'QTWEBKIT'
        except Exception as err_msg:
            print(err_msg)
            msg_txt = 'Browser Backend Not Available. Install either QtWebKit or QtWebEngine'
            send_notification(msg_txt, code=0)
elif BROWSER_BACKEND == 'QTWEBKIT':
    try:
        from PyQt5 import QtWebKitWidgets
        from PyQt5.QtWebKitWidgets import QWebView
        from browser_webkit import Browser
        from hls_webkit.hls_engine_webkit import BrowseUrlT
        QT_WEB_ENGINE = False
        print('Directly Using QTWEBKIT')
    except Exception as err_msg:
        print(err_msg)
        msg_txt = 'QTWEBKIT Not Available, Try QTWEBENGINE'
        send_notification(msg_txt, code=0)

TMPDIR = get_tmp_dir()

if TMPDIR and not os.path.exists(TMPDIR):
    try:
        os.makedirs(TMPDIR)
    except OSError as e:
        print(e)
        TMPDIR = mkdtemp(suffix=None, prefix='kawaii-player_')


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

logger = set_logger('kawaii-player.log', TMPDIR)


print(TMPDIR, OSNAME)

try:
    import mutagen
except Exception as e:
    print(e,'--143--')

try:
    import dbus
    import dbus.service
    import dbus.mainloop.pyqt5
    from mpris_dbus import MprisServer
except Exception as e:
    from mpris_nodbus import MprisServer
    print(e, 'No mpris server')

try:
    import libtorrent as lt
    from stream import ThreadServer, TorrentThread, get_torrent_info
    from stream import set_torrent_info, get_torrent_info_magnet
    from stream import set_new_torrent_file_limit, torrent_session_status
    from stream import get_torrent_download_location
except Exception as e:
    print(e, '---156---')
    notify_txt = 'python3 bindings for libtorrent are broken\
                 Torrent Streaming feature will be disabled'
    send_notification(notify_txt, code=0)

from settings_widget import LoginAuth, OptionsSettings
from media_server import ThreadServerLocal
from database import MediaDatabase
from player import PlayerWidget
from widgets.thumbnail import ThumbnailWidget, TitleThumbnailWidget
from widgets.thumbnail import TitleListWidgetPoster, TabThumbnail
from widgets.playlist import PlaylistWidget
from widgets.titlelist import TitleListWidget
from widgets.traywidget import SystemAppIndicator, FloatWindowWidget
from widgets.optionwidgets import *
from widgets.scrollwidgets import *
from thread_modules import FindPosterThread, ThreadingThumbnail
from thread_modules import ThreadingExample, DownloadThread, UpdateMusicThread
from thread_modules import GetIpThread, YTdlThread, PlayerWaitThread
from thread_modules import DiscoverServer, BroadcastServer, SetThumbnailGrid
from thread_modules import GetServerEpisodeInfo, PlayerGetEpn, SetThumbnail
from stylesheet import WidgetStyleSheet
from serverlib import ServerLib

def set_mainwindow_palette(fanart, first_time=None, theme=None):
    if theme is None or theme == 'default':
        logger.info('\n{0}:  mainwindow background\n'.format(fanart))
        if fanart.endswith('default.jpg'):
            default_dir, default_img = os.path.split(fanart)
            default_fit = os.path.join(default_dir, 'default_fit.jpg')
            if not os.path.exists(default_fit):
                ui.image_fit_option(fanart, default_fit, fit_size=1)
            fanart = default_fit
                
        if not os.path.isfile(fanart) or ui.keep_background_constant:
            fanart = ui.default_background
        if os.path.isfile(fanart):
            if not ui.keep_background_constant or first_time:
                palette	= QtGui.QPalette()
                palette.setBrush(QtGui.QPalette.Background, 
                                QtGui.QBrush(QtGui.QPixmap(fanart)))
                MainWindow.setPalette(palette)
                ui.current_background = fanart
    elif theme in ['system', 'transparent', 'mix', 'dark']:
        if theme == 'dark' and first_time:
            palette	= QtGui.QPalette()
            palette.setColor(MainWindow.backgroundRole(), QtGui.QColor(56,60,74))
            MainWindow.setPalette(palette)
        if os.path.isfile(fanart) and ui.layout_mode != 'Music':
            ui.current_background = fanart
            if '.' in fanart:
                fanart_name, ext = fanart.rsplit('.', 1)
                if not fanart_name.endswith('default'):
                    fanart_new = fanart_name + '-new.' + ext
                    picn = ui.image_fit_option(
                            fanart, fanart_new, fit_size=6, widget=ui.label_new
                            )
                    if os.path.exists(fanart_new):
                        ui.label_new.setPixmap(QtGui.QPixmap(fanart_new, "1"))
                else:
                    ui.label_new.clear()
        else:
            ui.label_new.clear()


class DoGetSignalNew(QtCore.QObject):
    new_signal = pyqtSignal(str)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.new_signal.connect(goto_ui_jump)
        
@pyqtSlot(str)
def goto_ui_jump(nm):
    global ui
    url = ui.getdb.epn_return_from_bookmark(nm, from_client=True)


class MainWindowWidget(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindowWidget, self).__init__()
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event):
        data = event.mimeData()
        if data.hasUrls():
            event.accept()
        else:
            event.ignore()
        
    def dropEvent(self, event):
        global ui, logger
        urls = event.mimeData().urls()
        for i in urls:
            i = i.toString()
            logger.debug(i)
            if i.startswith('file:///') or i.startswith('http') or i.startswith('magnet:'):
                if OSNAME == 'posix':
                    i = i.replace('file://', '', 1)
                else:
                    i = i.replace('file:///', '', 1)
            ui.watch_external_video('{}'.format(i), start_now=True)
    
    def mouseMoveEvent(self, event):
        global site, ui
        pos = event.pos()
        px = pos.x()
        x = self.width()
        dock_w = ui.dockWidget_3.width()
        if ui.orientation_dock == 'right':
            if px <= x and px >= x-6 and ui.auto_hide_dock:
                ui.dockWidget_3.show()
                ui.btn1.setFocus()
                logger.info('show options sidebar')
            elif px <= x-dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden():
                    ui.list1.setFocus()
                elif not ui.list2.isHidden():
                    ui.list2.setFocus()
        else:
            if px >= 0 and px <= 10 and ui.auto_hide_dock:
                ui.dockWidget_3.show()
                ui.btn1.setFocus()
                logger.info('show options sidebar')
            elif px >= dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden():
                    ui.list1.setFocus()
                elif not ui.list2.isHidden():
                    ui.list2.setFocus()
        if self.isFullScreen() and ui.mpvplayer_val.processId() > 0:
            logger.info('FullScreen Window but not video')
            if (not ui.tab_6.isHidden() or not ui.list2.isHidden()
                    or not ui.list1.isHidden() or not ui.tab_2.isHidden()):
                if ui.frame1.isHidden():
                    ui.frame1.show()
            else:
                ht = self.height()
                if pos.y() <= ht and pos.y() > ht - 5 and ui.frame1.isHidden():
                    ui.frame1.show()
                    ui.frame1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                elif pos.y() <= ht-32 and not ui.frame1.isHidden():
                    if site != 'Music' and ui.list2.isHidden() and ui.tab_6.isHidden() and ui.tab_2.isHidden():
                        ui.frame1.hide()
                        

class EventFilterFloatWindow(QtCore.QObject):

    def eventFilter(self, receiver, event):
        global tray, MainWindow, ui
        if event.type():
            #print("event is {0} with id {1}".format(event, event.type()))
            if(event.type() == QtCore.QEvent.Enter):
                if ui.float_timer.isActive():
                    ui.float_timer.stop()
                if ui.new_tray_widget.hasFocus():
                    print('focus')
                else:
                    print('unFocus')
                return 0
            elif(event.type() == QtCore.QEvent.Leave):
                if ui.new_tray_widget.remove_toolbar:
                    if ui.float_timer.isActive():
                        ui.float_timer.stop()
                    ui.float_timer.start(10)
                return 0
            else:
                return super(EventFilterFloatWindow, self).eventFilter(receiver, event)
        else:
            return super(EventFilterFloatWindow, self).eventFilter(receiver, event)


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow, media_data=None, home_val=None,
                scr_width=None, scr_height=None):
        global BASEDIR, screen_width, screen_height, home
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        #MainWindow.resize(875, 600)
        if media_data is not None:
            self.media_data = media_data
        if home_val is not None:
            home = home_val
        if scr_width is not None:
            screen_width = scr_width
        if scr_height is not None:
            screen_height = scr_height
        icon_path = os.path.join(RESOURCE_DIR, 'tray.png')
        if not os.path.exists(icon_path):
            icon_path = '/usr/share/kawaii-player/tray.png'
        if os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
        else:
            icon = QtGui.QIcon("")
        MainWindow.setWindowIcon(icon)
        self.superTab = QtWidgets.QWidget(MainWindow)
        self.superTab.setObjectName(_fromUtf8("superTab"))
        self.superGridLayout = QtWidgets.QGridLayout(MainWindow)
        self.superGridLayout.setObjectName(_fromUtf8("superGridLayout"))
        self.gridLayout = QtWidgets.QGridLayout(self.superTab)
        #self.gridLayout.setMouseTracking(True)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.superTab.setMouseTracking(True)
        self.superGridLayout.addWidget(self.superTab, 0, 1, 1, 1)
        self.superGridLayout.setContentsMargins(5, 5, 5, 5)
        self.superGridLayout.setSpacing(0)
        self.gridLayout.setSpacing(5)
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.gridLayout.addLayout(self.horizontalLayout_7, 1, 0, 1, 1)
        
        self.vertical_layout_new = QtWidgets.QVBoxLayout()
        self.vertical_layout_new.setObjectName(_fromUtf8('vertical_layout_new'))
        self.gridLayout.addLayout(self.vertical_layout_new, 0, 1, 1, 1)
        
        self.VerticalLayoutLabel = QtWidgets.QHBoxLayout()
        self.VerticalLayoutLabel.setObjectName(_fromUtf8("VerticalLayoutLabel"))
        #self.gridLayout.addLayout(self.VerticalLayoutLabel, 0, 1, 1, 1)
        self.vertical_layout_new.insertLayout(1, self.VerticalLayoutLabel)
        
        self.verticalLayout_40 = QtWidgets.QVBoxLayout()
        self.verticalLayout_40.setObjectName(_fromUtf8("verticalLayout_40"))
        self.gridLayout.addLayout(self.verticalLayout_40, 0, 2, 1, 1)
        
        self.verticalLayout_50 = QtWidgets.QVBoxLayout()
        self.verticalLayout_50.setObjectName(_fromUtf8("verticalLayout_50"))
        self.gridLayout.addLayout(self.verticalLayout_50, 0, 3, 1, 1)
        
        
        self.label = ThumbnailWidget(MainWindow)
        self.label.setup_globals(MainWindow, self, home, TMPDIR,
                                 logger, screen_width, screen_height, 'label')
        
        self.label_new = ThumbnailWidget(MainWindow)
        self.label_new.setup_globals(MainWindow, self, home, TMPDIR,
                                 logger, screen_width, screen_height, 'label_new')
        self.label_new.setMouseTracking(True)
        #self.label_new.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        #self.text = QtWidgets.QTextBrowser(MainWindow)
        self.text = QtWidgets.QTextEdit(MainWindow)
        self.text.setAcceptRichText(False)
        self.text.setObjectName(_fromUtf8("text"))
        self.text.copyAvailable.connect(self.text_editor_changed)
        self.text_save_btn = QtWidgets.QPushButton(MainWindow)
        self.text_save_btn.setText('Save')
        self.text_save_btn.setMinimumSize(QtCore.QSize(30, 25))
        self.text_save_btn.clicked.connect(self.save_text_edit)
        self.text_save_btn.hide()
        self.text_save_btn_timer = QtCore.QTimer()
        #self.text.setMaximumSize(QtCore.QSize(450, 250))
        #self.text.setMinimumSize(QtCore.QSize(450, 250))
        self.text_save_btn_timer.timeout.connect(self.text_save_btn_hide)
        self.text_save_btn_timer.setSingleShot(True)
        
        self.search_on_type_btn = QLineCustomSearch(MainWindow, self)
        self.search_on_type_btn.hide()
        
        self.text.lineWrapMode()
        #self.VerticalLayoutLabel.setStretch(2, 1)
        self.vertical_layout_new.insertWidget(0, self.label_new)
        self.VerticalLayoutLabel.insertWidget(0, self.label, 0)
        self.VerticalLayoutLabel.insertWidget(1, self.text, 0)
        #self.VerticalLayoutLabel.setStretch(1, 2)
        ##self.VerticalLayoutLabel.addStretch(1)#after label + text
        #self.text.hide()
        self.label.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
        self.label_new.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.VerticalLayoutLabel.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.VerticalLayoutLabel.setSpacing(5)
        self.VerticalLayoutLabel.setContentsMargins(0, 0, 0, 0)
        
        self.vertical_layout_new.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignBottom)
        self.vertical_layout_new.setSpacing(5)
        self.vertical_layout_new.setContentsMargins(0, 0, 0, 0)
        
        self.list1 = TitleListWidget(MainWindow, self, home, TMPDIR, logger)
        self.list1.setObjectName(_fromUtf8("list1"))
        #self.list1.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list1.setMouseTracking(True)
        #self.list1.setMinimumSize(QtCore.QSize(450, 16777215))
        self.verticalLayout_40.insertWidget(0, self.list1, 0)
        
        self.btnEpnList = QtWidgets.QComboBox(MainWindow)
        self.btnEpnList.setObjectName(_fromUtf8("btnEpnList"))
        self.verticalLayout_40.addWidget(self.btnEpnList)
        self.btnEpnList.hide()
        #self.btnEpnList.setMaximumSize(QtCore.QSize(350, 16777215))
        ###################################
        #self.list2 = QtGui.QListWidget(self.tab)
        self.list2 = PlaylistWidget(MainWindow, self, home, TMPDIR, logger)
        self.list2.setObjectName(_fromUtf8("list2"))
        #self.list2.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list2.setMouseTracking(True)
        
        self.verticalLayout_40.setAlignment(QtCore.Qt.AlignBottom)
        
        #self.verticalLayout_50.insertWidget(0, self.list1, 0)
        self.verticalLayout_50.insertWidget(0, self.list2, 0)
        #self.verticalLayout_50.insertWidget(2, self.text, 0)
        #self.verticalLayout_50.insertWidget(3, self.label, 0)
        self.verticalLayout_50.setAlignment(QtCore.Qt.AlignBottom)
        
        self.list4 = FilterTitleList(MainWindow, self, home)
        self.list4.setObjectName(_fromUtf8("list4"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list4.setMouseTracking(True)
        
        self.list4.hide()
        
        self.list5 = FilterPlaylist(MainWindow, self, home, logger)
        self.list5.setObjectName(_fromUtf8("list5"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list5.setMouseTracking(True)
        self.verticalLayout_50.insertWidget(1, self.list5, 0)
        self.list5.hide()
        
        self.list6 = QueueListWidget(MainWindow, self, home)
        self.list6.setObjectName(_fromUtf8("list6"))
        #self.list4.setMaximumSize(QtCore.QSize(400, 16777215))
        self.list6.setMouseTracking(True)
        self.verticalLayout_50.insertWidget(2, self.list6, 0)
        self.list6.hide()
        self.list6.addItem("Queue Empty: \
Select Item and Press 'ctrl+Q' to EnQueue it. \
If Queue List is Empty then Items Will be\
Played Sequentially as per Playlist. \
(Queue Feature Works Only With\n Local/Offline Content)\
Select Item and Press 'W' to toggle\
watch/unwatch status")
        #self.gridLayout.addWidget(self.list2, 0, 2, 1, 1)
        self.frame = QtWidgets.QFrame(MainWindow)
        #self.frame.setMinimumSize(QtCore.QSize(500, 22))
        self.frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        
        self.backward = QtWidgets.QPushButton(self.frame)
        self.backward.setObjectName(_fromUtf8("backward"))
        self.horizontalLayout_3.addWidget(self.backward)
        
        self.hide_btn_list1 = QtWidgets.QPushButton(self.frame)
        self.hide_btn_list1.setObjectName(_fromUtf8("hide_btn_list1"))
        
        self.hide_btn_list1.setMinimumHeight(30)
        self.hide_btn_list1_menu = QtWidgets.QMenu()
        self.hide_btn_menu_option = ['Sort', 'Shuffle']
        self.action_player_menu2 =[]
        for i in self.hide_btn_menu_option:
            self.action_player_menu2.append(
                self.hide_btn_list1_menu.addAction(i, lambda x=i:self.playerPlaylist1(x)))
                
        self.hide_btn_list1.setMenu(self.hide_btn_list1_menu)
        self.hide_btn_list1.setCheckable(True)
        self.hide_btn_list1.setText('Order')
        self.filter_btn = QtWidgets.QPushButton(self.frame)
        self.filter_btn.setObjectName(_fromUtf8("filter_btn"))
        
        self.filter_btn.setMinimumHeight(30)
        self.filter_btn.hide()
        #self.go_page = QtGui.QLineEdit(self.frame)
        
        self.page_number = QtWidgets.QLineEdit(self.frame)
        self.page_number.setObjectName(_fromUtf8("page_number"))
        
        self.page_number.setMaximumWidth(48)
        self.page_number.setMinimumHeight(30)
        
        self.go_page = QLineCustom(self.frame, self)
        self.go_page.setObjectName(_fromUtf8("go_page"))
        self.go_page.setMinimumHeight(30)
        self.go_page.setPlaceholderText('Filter')
        #self.go_page.hide()
        
        self.forward = QtWidgets.QPushButton(self.frame)
        self.forward.setObjectName(_fromUtf8("forward"))
        self.horizontalLayout_3.addWidget(self.forward)
        self.forward.hide()
        self.backward.hide()
        
        self.horizontalLayout_3.insertWidget(2, self.page_number, 0)
        self.horizontalLayout_3.insertWidget(3, self.go_page, 0)
        self.horizontalLayout_3.insertWidget(4, self.filter_btn, 0)
        self.horizontalLayout_3.insertWidget(5, self.hide_btn_list1, 0)
        
        self.goto_epn = QtWidgets.QFrame(MainWindow)
        self.goto_epn.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.goto_epn.setFrameShadow(QtWidgets.QFrame.Raised)
        self.goto_epn.setObjectName(_fromUtf8("goto_epn"))
        self.horizontalLayout_goto_epn = QtWidgets.QHBoxLayout(self.goto_epn)
        self.horizontalLayout_goto_epn.setObjectName(_fromUtf8("horizontalLayout_goto_epn"))
        self.horizontalLayout_goto_epn.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_goto_epn.setSpacing(5)
        #self.gridLayout.addWidget(self.goto_epn, 1, 2, 1, 1)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(5)
        
        self.goto_epn.hide()
        self.frame.hide()
        
        #self.progress = QtWidgets.QProgressBar(MainWindow)
        self.progress = QProgressBarCustom(MainWindow, self)
        self.progress.setObjectName(_fromUtf8("progress"))
        #self.gridLayout.addWidget(self.progress, 1, 3, 1, 1)
        self.verticalLayout_50.insertWidget(3, self.progress, 0)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setTextVisible(True)
        self.progress.hide()
        self.progress.setToolTip("Click for more options")
        self.player_buttons = {
            'play':'\u25B8', 'pause':'\u2225', 'stop':'\u25FE', 
            'prev':'\u2190', 'next':'\u2192', 'lock':'\u21BA', 
            'unlock':'\u21C4', 'quit':'\u2127', 'attach':'\u2022', 
            'left':'\u21A2', 'right':'\u21A3', 'pr':'\u226A', 
            'nxt':'\u226B', 'min':'\u2581', 'max':'\u25A2', 
            'close':'\u2715', 'resize':'M', 'up':'\u21E1', 
            'down':'\u21E3', 'browser':'\u25CC', 'vol':'\U0001F50A'
            }
                                
        self.check_symbol = '\u2714'
        self.torrent_frame = QtWidgets.QFrame(MainWindow)
        self.torrent_frame.setMaximumSize(QtCore.QSize(300, 16777215))
        self.torrent_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.torrent_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.torrent_frame.setObjectName(_fromUtf8("torrent_frame"))
        self.verticalLayout_50.insertWidget(4, self.torrent_frame, 0)
        self.horizontalLayout_torrent_frame = QtWidgets.QHBoxLayout(self.torrent_frame)
        self.horizontalLayout_torrent_frame.setContentsMargins(0, 2, 0, 2)
        self.horizontalLayout_torrent_frame.setSpacing(2)
        self.horizontalLayout_torrent_frame.setObjectName(_fromUtf8("horizontalLayout_torrent_frame"))
        self.torrent_frame.hide()
        
        self.label_torrent_stop = QtWidgets.QPushButton(self.torrent_frame)
        self.label_torrent_stop.setObjectName(_fromUtf8("label_torrent_stop"))
        self.label_torrent_stop.setText(self.player_buttons['stop'])
        self.label_torrent_stop.setMinimumWidth(24)
        self.horizontalLayout_torrent_frame.insertWidget(0, self.label_torrent_stop, 0)
        #self.label_torrent_stop.setToolTip("Stop Torrent")
        
        self.label_down_speed = QtWidgets.QLineEdit(self.torrent_frame)
        self.label_down_speed.setObjectName(_fromUtf8("label_down_speed"))
        self.label_down_speed.setToolTip("Set Download Speed Limit For Current Session in KB\nEnter Only Integer Values")
        self.horizontalLayout_torrent_frame.insertWidget(1, self.label_down_speed, 0)
        #self.label_down_speed.setMaximumWidth(100)
        self.label_up_speed = QtWidgets.QLineEdit(self.torrent_frame)
        self.label_up_speed.setObjectName(_fromUtf8("label_up_speed"))
        self.label_up_speed.setToolTip("Set Upload Speed Limit in KB for Current Session\nEnter Only Integer Values")
        self.horizontalLayout_torrent_frame.insertWidget(2, self.label_up_speed, 0)
        
        self.frame1 = QtWidgets.QFrame(MainWindow)
        self.frame1.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame1.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame1.setObjectName(_fromUtf8("frame1"))
        self.horizontalLayout_31 = QtWidgets.QVBoxLayout(self.frame1)
        self.horizontalLayout_31.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_31.setSpacing(0)
        self.horizontalLayout_31.setObjectName(_fromUtf8("horizontalLayout_31"))
        #self.gridLayout.addWidget(self.frame1, 1, 0, 1, 1)
        
        self.frame2 = QtWidgets.QFrame(MainWindow)
        #self.frame2.setMaximumSize(QtCore.QSize(16777215, 32))
        self.frame2.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame2.setObjectName(_fromUtf8("frame2"))
        self.horizontalLayout_101= QtWidgets.QHBoxLayout(self.frame2)
        self.horizontalLayout_101.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_101.setSpacing(10)
        self.horizontalLayout_101.setObjectName(_fromUtf8("horizontalLayout_101"))
        #self.gridLayout.addWidget(self.frame1, 1, 0, 1, 1)
    
        
        self.progressEpn = QtWidgets.QProgressBar(self.frame1)
        self.progressEpn.setObjectName(_fromUtf8("progressEpn"))
        #self.gridLayout.addWidget(self.progressEpn, 1, 0, 1, 1)
        self.progressEpn.setMinimum(0)
        self.progressEpn.setMaximum(100)
        self.progressEpn.setMaximumSize(QtCore.QSize(16777215, 32))
        self.progressEpn.setTextVisible(True)
        
        self.slider = MySlider(self.frame1, self, home)
        self.slider.setObjectName(_fromUtf8("slider"))
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        
        self.slider.setRange(0, 100)
        self.slider.setMouseTracking(True)
        
        
        
        try:
            aspect = (screen_width/screen_height)
        except NameError:
            screen_width = 800
            screen_height = 400
            aspect = (screen_width/screen_height)
            home = get_home_dir(mode='test')
            if not os.path.exists(home):
                os.makedirs(home)
        self.screen_size = (screen_width, screen_height)
        self.width_allowed = int((screen_width)/4.5)
        self.height_allowed = (self.width_allowed/aspect) #int((screen_height)/3.3)
        self.frame_height = int(self.height_allowed/2.5)
        self.image_aspect_allowed = (self.width_allowed/self.height_allowed)
        print(self.width_allowed, '--width--allowed--')
        self.list1.setMaximumWidth(self.width_allowed)
        self.list2.setMaximumWidth(self.width_allowed)
        self.list2.setIconSize(QtCore.QSize(128, 128))
        self.frame.setMaximumWidth(self.width_allowed)
        self.list4.setMaximumWidth(self.width_allowed)
        self.list5.setMaximumWidth(self.width_allowed)
        self.list6.setMaximumWidth(self.width_allowed)
        self.goto_epn.setMaximumWidth(self.width_allowed)
        
        self.text_width = screen_width-3*self.width_allowed-35
        self.text.setMaximumWidth(self.text_width)
        self.text.setMaximumHeight(self.height_allowed)
        self.text.setMinimumWidth(self.width_allowed)
        self.label.setMaximumHeight(self.height_allowed)
        self.label.setMinimumHeight(self.height_allowed)
        self.label.setMaximumWidth(self.width_allowed)
        self.label.setMinimumWidth(self.width_allowed)
        self.label_new_width = screen_width-2*self.width_allowed-35
        self.label_new.setMaximumWidth(self.label_new_width)
        #self.label_new.setMaximumHeight(screen_height - self.height_allowed - self.frame_height -100)
        self.label_new.setMaximumHeight(2.5*self.height_allowed)
        #self.label_new.setScaledContents(True)
        self.progress.setMaximumSize(QtCore.QSize(self.width_allowed, 16777215))
        self.thumbnail_video_width = int(self.width_allowed*2.5)
        self.frame1.setMaximumSize(QtCore.QSize(16777215, self.frame_height))
        
        #self.label.setMaximumSize(QtCore.QSize(280, 250))
        #self.label.setMinimumSize(QtCore.QSize(280, 250))
        
        self.list1.setWordWrap(True)
        self.list1.setTextElideMode(QtCore.Qt.ElideRight)
        self.list2.setWordWrap(True)
        self.list2.setTextElideMode(QtCore.Qt.ElideRight)
        self.list2.setBatchSize(10)
        self.list4.setWordWrap(True)
        self.list4.setTextElideMode(QtCore.Qt.ElideRight)
        self.list5.setWordWrap(True)
        self.list5.setTextElideMode(QtCore.Qt.ElideRight)
        self.list6.setWordWrap(True)
        self.list6.setTextElideMode(QtCore.Qt.ElideRight)
        
        #self.gridLayout.setAlignment(QtCore.Qt.AlignLeft)#Can cause video disappear in fullscreen mode
        #self.superGridLayout.setAlignment(QtCore.Qt.AlignRight)Can cause video disappear in fullscreen mode
        #self.verticalLayout_40.insertWidget(1, self.frame, 0)
        
        self.player_opt = QtWidgets.QFrame(self.frame1)
        self.player_opt.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.player_opt.setFrameShadow(QtWidgets.QFrame.Raised)
        self.player_opt.setObjectName(_fromUtf8("player_opt"))
        self.horizontalLayout_player_opt = QtWidgets.QHBoxLayout(self.player_opt)
        self.horizontalLayout_player_opt.setObjectName(_fromUtf8("horizontalLayout_player_opt"))
        self.horizontalLayout_player_opt.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_player_opt.setSpacing(0)
        self.horizontalLayout_31.insertWidget(0, self.player_opt, 0)
        self.horizontalLayout_31.insertWidget(1, self.progressEpn, 0)
        self.horizontalLayout_31.insertWidget(2, self.slider, 0)
        
        self.player_opt_toolbar= QtWidgets.QPushButton(self.player_opt)
        self.player_opt_toolbar.setObjectName(_fromUtf8("player_opt_toolbar"))
        self.horizontalLayout_player_opt.insertWidget(0, self.player_opt_toolbar, 0)
        self.player_opt_toolbar.setText("Menu")
        self.player_opt_toolbar.setToolTip('Shift+G')
        
        self.sd_hd = QtWidgets.QPushButton(self.player_opt)
        self.sd_hd.setObjectName(_fromUtf8("sd_hd"))
        self.horizontalLayout_player_opt.insertWidget(1, self.sd_hd, 0)
        self.sd_hd.setText("BEST")
        self.sd_hd.setToolTip('Select Quality')
        
        self.subtitle_track = QtWidgets.QPushButton(self.player_opt)
        self.subtitle_track.setObjectName(_fromUtf8("subtitle_track"))
        self.horizontalLayout_player_opt.insertWidget(2, self.subtitle_track, 0)
        self.subtitle_track.setText("SUB")
        self.subtitle_track.setToolTip('Toggle Subtitle (J)')
        
        self.audio_track = QtWidgets.QPushButton(self.player_opt)
        self.audio_track.setObjectName(_fromUtf8("audio_track"))
        self.horizontalLayout_player_opt.insertWidget(3, self.audio_track, 0)
        self.audio_track.setText("A/V")
        self.audio_track.setToolTip('Toggle Audio (K)')
        
        self.player_loop_file = QtWidgets.QPushButton(self.player_opt)
        self.player_loop_file.setObjectName(_fromUtf8("player_loop_file"))
        self.horizontalLayout_player_opt.insertWidget(4, self.player_loop_file, 0)
        self.player_loop_file.setText(self.player_buttons['unlock'])
        self.player_loop_file.setToolTip('Lock/unLock File (L)')
        #self.player_loop_file.hide()
        
        self.player_stop = QtWidgets.QPushButton(self.player_opt)
        self.player_stop.setObjectName(_fromUtf8("player_stop"))
        self.horizontalLayout_player_opt.insertWidget(5, self.player_stop, 0)
        self.player_stop.setText(self.player_buttons['stop'])
        self.player_stop.setToolTip('Stop (Q)')
        
        self.player_play_pause = QtWidgets.QPushButton(self.player_opt)
        self.player_play_pause.setObjectName(_fromUtf8("player_play_pause"))
        self.horizontalLayout_player_opt.insertWidget(6, self.player_play_pause, 0)
        self.player_play_pause.setText(self.player_buttons['play'])
        self.player_play_pause.setToolTip('Play/Pause (Space)')
        
        self.player_prev = QtWidgets.QPushButton(self.player_opt)
        self.player_prev.setObjectName(_fromUtf8("player_prev"))
        self.horizontalLayout_player_opt.insertWidget(7, self.player_prev, 0)
        self.player_prev.setText(self.player_buttons['prev'])
        self.player_prev.setToolTip('Previous (Comma)')
        
        self.player_next = QtWidgets.QPushButton(self.player_opt)
        self.player_next.setObjectName(_fromUtf8("player_next"))
        self.horizontalLayout_player_opt.insertWidget(8, self.player_next, 0)
        self.player_next.setText(self.player_buttons['next'])
        self.player_next.setToolTip('Next (Period)')
        
        
        
        self.player_showhide_title_list = QtWidgets.QPushButton(self.player_opt)
        self.player_showhide_title_list.setObjectName(_fromUtf8("player_showhide_title_list"))
        self.horizontalLayout_player_opt.insertWidget(9, self.player_showhide_title_list, 0)
        self.player_showhide_title_list.setText('T')
        self.player_showhide_title_list.clicked.connect(lambda x=0:self.playerPlaylist("Show/Hide Title List"))
        self.player_showhide_title_list.setToolTip('Show/Hide Title List')
        
        self.player_showhide_playlist = QtWidgets.QPushButton(self.player_opt)
        self.player_showhide_playlist.setObjectName(_fromUtf8("player_showhide_playlist"))
        self.horizontalLayout_player_opt.insertWidget(10, self.player_showhide_playlist, 0)
        #self.player_showhide_playlist.setText('\u2118')
        self.player_showhide_playlist.setText('PL')
        self.player_showhide_playlist.clicked.connect(
            lambda x=0:self.playerPlaylist("Show/Hide Playlist"))
        self.player_showhide_playlist.setToolTip('Show/Hide Playlist')
        
        self.queue_manage = QtWidgets.QPushButton(self.player_opt)
        self.queue_manage.setObjectName(_fromUtf8("queue_manage"))
        self.horizontalLayout_player_opt.insertWidget(11, self.queue_manage, 0)
        self.queue_manage.setText("Q")
        self.queue_manage.setToolTip('Show/Hide Queue')
        #self.queue_manage.setMinimumWidth(30)
        self.queue_manage.clicked.connect(self.queue_manage_list)
        
        
        
        self.player_filter = QtWidgets.QPushButton(self.player_opt)
        self.player_filter.setObjectName(_fromUtf8("player_filter"))
        self.horizontalLayout_player_opt.insertWidget(12, self.player_filter, 0)
        self.player_filter.setText('Y')
        self.player_filter.setToolTip('Show/Hide Filter and other options (Ctrl+F)')
        self.player_filter.clicked.connect(self.show_hide_filter_toolbar)
        
        self.btnWebHide = QtWidgets.QPushButton(self.player_opt)
        self.btnWebHide.setObjectName(_fromUtf8("btnWebHide"))
        
        self.horizontalLayout_player_opt.insertWidget(13, self.btnWebHide, 0)
        self.btnWebHide.setText(self.player_buttons['browser'])
        self.btnWebHide.clicked.connect(self.webHide)
        self.btnWebHide.setToolTip('Show/Hide Browser (Ctrl+X)')
        
        self.vol_manage = QtWidgets.QPushButton(self.player_opt)
        self.vol_manage.setObjectName(_fromUtf8("vol_manage"))
        self.horizontalLayout_player_opt.insertWidget(14, self.vol_manage, 0)
        self.vol_manage.setText('E')
        self.vol_manage.setToolTip('Extra Toolbar')
        #self.queue_manage.setMinimumWidth(30)
        self.vol_manage.clicked.connect(self.player_volume_manager)
        #self.vol_manage.setStyleSheet("text-align: bottom;")
        #self.vol_manage.hide()
        
        self.detach_video_button = QtWidgets.QPushButton(self.player_opt)
        self.detach_video_button.setText(self.player_buttons['attach'])
        #self.attach.clicked.connect(tray.right_menu._detach_video)
        self.detach_video_button.setToolTip('Detach Video (aka Picture in Picture)')
        self.horizontalLayout_player_opt.insertWidget(15, self.detach_video_button, 0)
        
        self.player_playlist = QtWidgets.QPushButton(self.player_opt)
        self.player_playlist.setObjectName(_fromUtf8("player_playlist"))
        self.horizontalLayout_player_opt.insertWidget(16, self.player_playlist, 0)
        self.player_playlist.setText("More")
        self.player_menu = QtWidgets.QMenu()
        self.player_menu_option = [
                'Show/Hide Video', 'Show/Hide Cover And Summary', 
                'Lock Playlist', 'Shuffle', 'Stop After Current File (Ctrl+Q)', 
                'Continue(default Mode)', 'Set Media Server User/PassWord', 
                'Start Media Server', 'Broadcast Server', 'Turn ON Remote Control', 
                'Set Current Background As Default', 'Preferences (Ctrl+P)'
                ]
                                
        self.action_player_menu =[]
        for i in self.player_menu_option:
            self.action_player_menu.append(
                self.player_menu.addAction(i, lambda x=i:self.playerPlaylist(x)))
                
        
        self.player_seek_10 = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_10.setObjectName(_fromUtf8("player_seek_10"))
        self.horizontalLayout_player_opt.insertWidget(17, self.player_seek_10, 0)
        self.player_seek_10.setText('+10s')
        self.player_seek_10.clicked.connect(lambda x=0: self.seek_to_val(10))
        self.player_seek_10.hide()
        
        self.player_seek_10_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_10_.setObjectName(_fromUtf8("player_seek_10_"))
        self.horizontalLayout_player_opt.insertWidget(18, self.player_seek_10_, 0)
        self.player_seek_10_.setText('-10s')
        self.player_seek_10_.clicked.connect(lambda x=0: self.seek_to_val(-10))
        self.player_seek_10_.hide()
        
        self.player_vol_5 = QtWidgets.QPushButton(self.player_opt)
        self.player_vol_5.setObjectName(_fromUtf8("player_vol_5"))
        self.horizontalLayout_player_opt.insertWidget(19, self.player_vol_5, 0)
        self.player_vol_5.setText('+5')
        self.player_vol_5.clicked.connect(lambda x=0: self.seek_to_vol_val(5))
        self.player_vol_5.hide()
        
        self.player_vol_5_ = QtWidgets.QPushButton(self.player_opt)
        self.player_vol_5_.setObjectName(_fromUtf8("player_vol_5_"))
        self.horizontalLayout_player_opt.insertWidget(20, self.player_vol_5_, 0)
        self.player_vol_5_.setText('-5')
        self.player_vol_5_.clicked.connect(lambda x=0: self.seek_to_vol_val(-5))
        self.player_vol_5_.hide()
        
        self.player_fullscreen = QtWidgets.QPushButton(self.player_opt)
        self.player_fullscreen.setObjectName(_fromUtf8("player_fullscreen"))
        self.horizontalLayout_player_opt.insertWidget(21, self.player_fullscreen, 0)
        self.player_fullscreen.setText('F')
        self.player_fullscreen.clicked.connect(self.remote_fullscreen)
        self.player_fullscreen.hide()
        
        self.player_seek_60 = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_60.setObjectName(_fromUtf8("player_seek_60"))
        self.horizontalLayout_player_opt.insertWidget(22, self.player_seek_60, 0)
        self.player_seek_60.setText('60s')
        self.player_seek_60.clicked.connect(lambda x=0: self.seek_to_val(60))
        self.player_seek_60.hide()
        
        self.player_seek_60_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_60_.setObjectName(_fromUtf8("player_seek_60_"))
        self.horizontalLayout_player_opt.insertWidget(23, self.player_seek_60_, 0)
        self.player_seek_60_.setText('-60s')
        self.player_seek_60_.clicked.connect(lambda x=0: self.seek_to_val(-60))
        self.player_seek_60_.hide()
        
        self.player_seek_5m = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_5m.setObjectName(_fromUtf8("player_seek_5m"))
        self.horizontalLayout_player_opt.insertWidget(24, self.player_seek_5m, 0)
        self.player_seek_5m.setText('5m')
        self.player_seek_5m.clicked.connect(lambda x=0: self.seek_to_val(300))
        self.player_seek_5m.hide()
        
        self.player_seek_5m_ = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_5m_.setObjectName(_fromUtf8("player_seek_5m_"))
        self.horizontalLayout_player_opt.insertWidget(25, self.player_seek_5m_, 0)
        self.player_seek_5m_.setText('-5m')
        self.player_seek_5m_.clicked.connect(lambda x=0: self.seek_to_val(-300))
        self.player_seek_5m_.hide()
        
        self.client_seek_val = 0
        
        self.player_seek_all = QtWidgets.QPushButton(self.player_opt)
        self.player_seek_all.setObjectName(_fromUtf8("player_seek_all"))
        self.horizontalLayout_player_opt.insertWidget(26, self.player_seek_all, 0)
        self.player_seek_all.setText('all')
        self.player_seek_all.clicked.connect(self.seek_to_val_abs)
        self.player_seek_all.hide()
        
        self.player_play_pause_play = QtWidgets.QPushButton(self.player_opt)
        self.player_play_pause_play.setObjectName(_fromUtf8("player_play_pause_play"))
        self.horizontalLayout_player_opt.insertWidget(27, self.player_play_pause_play, 0)
        self.player_play_pause_play.setText('play')
        self.player_play_pause_play.clicked.connect(self.player_force_play)
        self.player_play_pause_play.hide()
        
        self.player_play_pause_pause = QtWidgets.QPushButton(self.player_opt)
        self.player_play_pause_pause.setObjectName(_fromUtf8("player_play_pause_pause"))
        self.horizontalLayout_player_opt.insertWidget(28, self.player_play_pause_pause, 0)
        self.player_play_pause_pause.setText('pause')
        self.player_play_pause_pause.clicked.connect(self.player_force_pause)
        self.player_play_pause_pause.hide()
        
        self.player_show_btn = QtWidgets.QPushButton(self.player_opt)
        self.player_show_btn.setObjectName(_fromUtf8("player_show_btn"))
        self.horizontalLayout_player_opt.insertWidget(29, self.player_show_btn, 0)
        self.player_show_btn.setText('Show')
        self.player_show_btn.clicked.connect(MainWindow.show)
        self.player_show_btn.hide()
        
        self.player_hide_btn = QtWidgets.QPushButton(self.player_opt)
        self.player_hide_btn.setObjectName(_fromUtf8("player_hide_btn"))
        self.horizontalLayout_player_opt.insertWidget(30, self.player_hide_btn, 0)
        self.player_hide_btn.setText('Hide')
        self.player_hide_btn.clicked.connect(MainWindow.hide)
        self.player_hide_btn.hide()
        
        self.player_btn_update_list2 = QtWidgets.QPushButton(self.player_opt)
        self.player_btn_update_list2.setObjectName(_fromUtf8("player_btn_update_list2"))
        self.horizontalLayout_player_opt.insertWidget(31, self.player_btn_update_list2, 0)
        self.player_btn_update_list2.setText('Shuffle')
        self.player_btn_update_list2.clicked.connect(self.update_list2)
        self.player_btn_update_list2.hide()
        
        self.quick_url_play_btn = QtWidgets.QPushButton(self.player_opt)
        self.quick_url_play_btn.setObjectName(_fromUtf8("quick_url_play_btn"))
        self.horizontalLayout_player_opt.insertWidget(32, self.quick_url_play_btn, 0)
        self.quick_url_play_btn.setText('quick')
        self.quick_url_play_btn.clicked.connect(self.quick_url_play_method)
        self.quick_url_play_btn.hide()
        
        self.set_quality_server_btn = QtWidgets.QPushButton(self.player_opt)
        self.set_quality_server_btn.setObjectName(_fromUtf8("set_quality_server_btn"))
        self.horizontalLayout_player_opt.insertWidget(33, self.set_quality_server_btn, 0)
        self.set_quality_server_btn.setText('quality')
        self.set_quality_server_btn.clicked.connect(self.set_quality_server_btn_method)
        self.set_quality_server_btn.hide()
        
        self.set_queue_item_btn = QtWidgets.QPushButton(self.player_opt)
        self.set_queue_item_btn.setObjectName(_fromUtf8("set_queue_item_btn"))
        self.horizontalLayout_player_opt.insertWidget(34, self.set_queue_item_btn, 0)
        self.set_queue_item_btn.setText('queue')
        self.set_queue_item_btn.clicked.connect(self.set_queue_item_btn_method)
        self.set_queue_item_btn.hide()
        self.queue_item_external = -1
        
        self.remove_queue_item_btn = QtWidgets.QPushButton(self.player_opt)
        self.remove_queue_item_btn.setObjectName(_fromUtf8("remove_queue_item_btn"))
        self.horizontalLayout_player_opt.insertWidget(35, self.remove_queue_item_btn, 0)
        self.remove_queue_item_btn.setText('remove queue')
        self.remove_queue_item_btn.clicked.connect(self.remove_queue_item_btn_method)
        self.remove_queue_item_btn.hide()
        self.queue_item_external_remove = -1
        
        self.player_playlist.setMenu(self.player_menu)
        self.player_playlist.setCheckable(True)
        
        self.mirror_change = QtWidgets.QPushButton(self.goto_epn)
        self.mirror_change.setObjectName(_fromUtf8("mirror_change"))
        self.horizontalLayout_goto_epn.insertWidget(1, self.mirror_change, 0)
        self.mirror_change.setText("Mirror")
        self.mirror_change.hide()
        
        self.goto_epn_filter = QtWidgets.QPushButton(self.goto_epn)
        self.goto_epn_filter.setObjectName(_fromUtf8("Filter Button"))
        self.horizontalLayout_goto_epn.insertWidget(2, self.goto_epn_filter, 0)
        self.goto_epn_filter.setText("Filter")
        self.goto_epn_filter.hide()
        
        self.goto_epn_filter_txt = QLineCustomEpn(self.goto_epn, self)
        self.goto_epn_filter_txt.setObjectName(_fromUtf8("Filter Text"))
        self.horizontalLayout_goto_epn.insertWidget(3, self.goto_epn_filter_txt, 0)
        self.goto_epn_filter_txt.setPlaceholderText("Filter")
        #self.goto_epn_filter_txt.hide()
        
        self.player_playlist1 = QtWidgets.QPushButton(self.goto_epn)
        self.player_playlist1.setObjectName(_fromUtf8("player_playlist1"))
        self.horizontalLayout_goto_epn.insertWidget(4, self.player_playlist1, 0)
        self.player_playlist1.setText("Order")
        self.player_menu1 = QtWidgets.QMenu()
        self.player_menu_option1 = [
            'Order by Name(Ascending)', 'Order by Name(Descending)', 
            'Order by Date(Ascending)', 'Order by Date(Descending)'
            ]
        self.action_player_menu1 =[]
        for i in self.player_menu_option1:
            self.action_player_menu1.append(
                self.player_menu1.addAction(i, lambda x=i: self.playerPlaylist(x)))
            
        self.player_playlist1.setMenu(self.player_menu1)
        self.player_playlist1.setCheckable(True)
        
        self.frame1.setMinimumHeight(self.frame_height)
        self.frame.setMinimumHeight(30)
        self.goto_epn.setMinimumHeight(30)
        self.frame1.setMaximumHeight(self.frame_height)
        self.frame.setMaximumHeight(30)
        self.goto_epn.setMaximumHeight(30)
        
        self.mirror_change.setMaximumHeight(30)
        self.player_playlist1.setMaximumHeight(30)
        self.backward.setMaximumHeight(30)
        self.forward.setMaximumHeight(30)
        self.goto_epn_filter.setMaximumHeight(30)
        self.goto_epn_filter_txt.setMaximumHeight(30)
        self.queue_manage.setMaximumWidth(60)
        #self.queue_manage.setMaximumHeight(30)
        self.vol_manage.setMaximumWidth(60)
        self.detach_video_button.setMaximumWidth(60)
        #self.vol_manage.setMaximumHeight(30)
        
        #self.frame.setMaximumWidth(300)
        #self.tabWidget1.addTab(self.tab_2, _fromUtf8(""))
        self.mpv_input_conf = os.path.join(home, 'src', 'input.conf')
        self.custom_key_file = os.path.join(home, 'src', 'customkey')
        self.tab_5 = PlayerWidget(MainWindow, ui=self, logr= logger, tmp=TMPDIR)
        #self.tab_5 = tab5(None)
        self.tab_5.setObjectName(_fromUtf8("tab_5"))
        #self.tabWidget1.addTab(self.tab_5, _fromUtf8(""))
        self.gridLayout.addWidget(self.tab_5, 0, 1, 1, 1)
        self.tab_5.setMouseTracking(True)
        #self.VerticalLayoutLabel.insertWidget(1, self.tab_5, 0)
        self.tab_5.hide()
        self.idw = str(int(self.tab_5.winId()))
        #self.tab_5.setMinimumSize(100, 100)
        #self.tab_6 = QtGui.QWidget(MainWindow)
        self.tab_6 = TabThumbnail(MainWindow, self)
        self.tab_6.setMouseTracking(True)
        #self.tab_6 = QtGui.QWidget()
        #self.gridLayout.addWidget(self.tab_6)
        #ui.gridLayout.addWidget(ui.tab_6, 0, 4, 1, 1)
        self.tab_6.setObjectName(_fromUtf8("tab_6"))
        #self.tabWidget1.addTab(self.tab_6, _fromUtf8(""))
        self.tab_6.hide()
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout.addWidget(self.tab_2, 0, 2, 1, 1)
        #self.superGridLayout.addWidget(self.tab_2, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)
        self.tab_2.hide()
        
        self.dockWidget_3 = QtWidgets.QFrame(MainWindow)
        self.dock_vert = QtWidgets.QVBoxLayout(self.dockWidget_3)
        self.dock_vert.setContentsMargins(0, 0, 0, 0)
        self.dockWidget_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.dockWidget_3.setFrameShadow(QtWidgets.QFrame.Raised)
        #self.dockWidget_3.setStyleSheet("""QFrame{background-color:gray;border: 1px solid rgba(0, 0, 0, 40%)};""")
        self.dockWidget_3.setMouseTracking(True)
        self.dockWidget_3.setObjectName(_fromUtf8("dockWidget_3"))
        self.dockWidget_3.setMaximumWidth(self.width_allowed-100)
        #self.dockWidget_3.setMaximumHeight(500)
        
        #self.gridLayout.addLayout(self.VerticalLayoutLabel, 0, 0, 1, 1)
        
        #self.dockWidget_3.setMaximumSize(QtCore.QSize(150, 1000))
        self.dockWidgetContents_3 = QtWidgets.QWidget()
        self.dockWidgetContents_3.setObjectName(_fromUtf8("dockWidgetContents_3"))
        self.dock_vert.insertWidget(0, self.dockWidgetContents_3, 0)
        
        self.VerticalLayoutLabel_Dock3 = QtWidgets.QVBoxLayout(self.dockWidgetContents_3)
        self.VerticalLayoutLabel_Dock3.setObjectName(_fromUtf8("VerticalLayoutLabel_Dock3"))
        self.VerticalLayoutLabel_Dock3.setSpacing(0)
        self.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
        self.list3 = SidebarWidget(self.dockWidgetContents_3, self, home)
        self.list3.setMouseTracking(True)
        self.list3.setGeometry(QtCore.QRect(20, 100, 130, 201))
        self.list3.setObjectName(_fromUtf8("list3"))
        self.line = QtWidgets.QLineEdit(self.dockWidgetContents_3)
        self.line.setGeometry(QtCore.QRect(20, 20, 130, 26))
        #self.line.setGeometry(QtCore.QRect(20, 55, 130, 31))
        self.line.setObjectName(_fromUtf8("line"))
        #self.line.hide()
        self.line.setReadOnly(True)
        self.btn1 = SelectButton(self.dockWidgetContents_3, self)
        #self.btn1.setGeometry(QtCore.QRect(20, 55, 130, 31))
        #self.btn1.setGeometry(QtCore.QRect(20, 20, 130, 26))
        self.btn1.setObjectName(_fromUtf8("btn1"))
        
        self.btnAddon = SelectButton(self.dockWidgetContents_3, self)
        self.btnAddon.setObjectName(_fromUtf8("btnAddon"))
        self.btnAddon.hide()
        #self.btn1.setEditable(True)
        #self.btn1.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        
        #self.dockWidget_3.setWidget(self.dockWidgetContents_3)
        #MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget_3)
        self.dockWidget_4 = QtWidgets.QDockWidget(MainWindow)
        ##self.dockWidget_4.setMinimumSize(QtCore.QSize(92, 159))
        self.dockWidget_4.setMaximumSize(QtCore.QSize(52000, 200))
        self.dockWidget_4.setObjectName(_fromUtf8("dockWidget_4"))
        
        self.dockWidgetContents_4 = QtWidgets.QWidget()
        self.dockWidgetContents_4.setObjectName(_fromUtf8("dockWidgetContents_4"))
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.dockWidgetContents_4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        #self.text = QtGui.QTextBrowser(self.dockWidgetContents_4)
        #self.text.setObjectName(_fromUtf8("text"))
        #self.horizontalLayout.addWidget(self.text)
        self.dockWidget_4.setWidget(self.dockWidgetContents_4)
        
        ###################  Browser Layout  ##############################
        self.horizontalLayout_5 = QtWidgets.QVBoxLayout(self.tab_2)
        #MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8), self.dockWidget_4)
        
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.dialog = QtWidgets.QDialog()
        #self.web = QWebView(self.tab_2)
        self.web = ''
        #self.web = Browser()
        #self.web.setObjectName(_fromUtf8("web"))
        #self.horizontalLayout_5.addWidget(self.web)
        ##self.gridLayout.addWidget(self.tab_2, 2, 1, 1, 1)
        #self.web.hide()
        self.frame_web = QtWidgets.QFrame(MainWindow)
        self.frame_web.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.frame_web.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_web.setObjectName(_fromUtf8("frame_web"))
        
        self.horizLayout_web = QtWidgets.QHBoxLayout(self.frame_web)
        #self.horizLayout_web.setSpacing(0)
        self.horizLayout_web.setContentsMargins(0, 0 ,0, 0)
        self.horizLayout_web.setObjectName(_fromUtf8("horizLayout_web"))
        self.horizontalLayout_5.insertWidget(0 ,self.frame_web, 0)
        
        
        
        self.btnWebClose = QtWidgets.QPushButton(self.tab_2)
        self.btnWebClose.setObjectName(_fromUtf8("btnWebClose"))
        self.btnWebClose.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(1, self.btnWebClose, 0)
        self.btnWebClose.setText(self.player_buttons['close'])
        self.btnWebClose.clicked.connect(self.webClose)
        
        self.btnWebResize = QtWidgets.QPushButton(self.tab_2)
        self.btnWebResize.setObjectName(_fromUtf8("btnWebResize"))
        self.btnWebResize.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(2, self.btnWebResize, 0)
        self.btnWebResize.setText(self.player_buttons['resize'])
        self.btnWebResize.clicked.connect(self.webResize)
        
        self.btnWebPrev = QtWidgets.QPushButton(self.tab_2)
        self.btnWebPrev.setObjectName(_fromUtf8("btnWebPrev"))
        self.btnWebPrev.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(3, self.btnWebPrev, 0)
        self.btnWebPrev.clicked.connect(self.go_prev_web_page)
        self.btnWebPrev.setText(self.player_buttons['pr'])
        
        self.btnWebNext = QtWidgets.QPushButton(self.tab_2)
        self.btnWebNext.setObjectName(_fromUtf8("btnWebNext"))
        self.btnWebNext.setMaximumSize(200, 50)
        self.horizLayout_web.insertWidget(4, self.btnWebNext, 0)
        self.btnWebNext.clicked.connect(self.go_next_web_page)
        self.btnWebNext.setText(self.player_buttons['nxt'])
        
        self.btnWebReviews = QtWidgets.QComboBox(self.tab_2)
        self.btnWebReviews.setObjectName(_fromUtf8("btnWebReviews"))
        self.horizLayout_web.insertWidget(5, self.btnWebReviews, 0)
        self.btnWebReviews.setMaximumSize(200, 50)
        
        self.btnGoWeb = QtWidgets.QPushButton(self.tab_2)
        self.btnGoWeb.setObjectName(_fromUtf8("btnGoWeb"))
        self.horizLayout_web.insertWidget(6, self.btnGoWeb, 0)
        self.btnGoWeb.setMaximumSize(200, 50)
        self.btnGoWeb.setText("Go")
        self.btnGoWeb.clicked.connect(
            lambda x=0: self.reviewsWeb(action='btn_pushed')
            )
        
        self.btnWebReviews_search = QtWidgets.QLineEdit(self.tab_2)
        self.btnWebReviews_search.setObjectName(_fromUtf8("btnWebReviews_search"))
        self.horizLayout_web.insertWidget(7, self.btnWebReviews_search, 0)
        self.btnWebReviews_search.setMaximumSize(200, 50)
        self.btnWebReviews_search.setPlaceholderText('Search Web')
        self.btnWebReviews_search.returnPressed.connect(
            lambda x=0:self.reviewsWeb(action='return_pressed')
            )
        self.browser_buttons = [
            self.btnWebClose, self.btnWebResize, self.btnWebPrev,
            self.btnWebNext, self.btnWebReviews, self.btnGoWeb,
            self.btnWebReviews_search
            ]
        ##################
        
        self.btn2 = QtWidgets.QComboBox(self.dockWidgetContents_3)
        self.btn2.setObjectName(_fromUtf8("btn2"))
        self.btn3 = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn3.setObjectName(_fromUtf8("btn3"))
        self.btn3.setMinimumHeight(30)
        
        self.thumbnail_text_color_dict = {
            'white':QtCore.Qt.white, 'black':QtCore.Qt.black,
            'red':QtCore.Qt.red, 'darkred':QtCore.Qt.darkRed,
            'green':QtCore.Qt.green, 'darkgreen':QtCore.Qt.darkGreen,
            'blue':QtCore.Qt.blue, 'darkblue':QtCore.Qt.darkBlue,
            'cyan':QtCore.Qt.cyan, 'darkcyan':QtCore.Qt.darkCyan,
            'magenta':QtCore.Qt.magenta, 'darkmagenta':QtCore.Qt.darkMagenta,
            'yellow':QtCore.Qt.yellow,  'darkyellow':QtCore.Qt.darkYellow,
            'gray':QtCore.Qt.gray, 'darkgray':QtCore.Qt.darkGray,
            'lightgray':QtCore.Qt.lightGray, 'transparent':QtCore.Qt.transparent
            }
        self.thumbnail_text_color = 'white'
        self.thumbnail_text_color_focus = 'green'
        self.list_text_color = 'white'
        self.list_text_color_focus = 'violet'
        self.font_bold = True
        self.horizontalLayout10 = QtWidgets.QVBoxLayout(self.tab_6)
        self.horizontalLayout10.setObjectName(_fromUtf8("horizontalLayout"))
        self.scrollArea = QtGuiQWidgetScroll(self.tab_6, self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMouseTracking(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout1 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout1.setObjectName(_fromUtf8("gridLayout1"))
        self.scrollArea1 = QtGuiQWidgetScroll1(self.tab_6, self)
        self.scrollArea1.setWidgetResizable(True)
        self.scrollArea1.setMouseTracking(True)
        self.scrollArea1.setObjectName(_fromUtf8("scrollArea1"))
        #self.scrollAreaWidgetContents.setBaseSize(QtCore.QSize(screen_width, 200000))
        
        self.scrollAreaWidgetContents1 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents1.setObjectName(_fromUtf8("scrollAreaWidgetContents1"))
        self.gridLayout2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents1)
        self.gridLayout2.setObjectName(_fromUtf8("gridLayout2"))
        self.gridLayout2.setSpacing(0)
        
        self.btn10 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.btn10.setObjectName(_fromUtf8("btn10"))
        self.btn10.hide()
        self.gridLayout1.addWidget(self.btn10, 0, 0, 1, 1)
        
        self.scrollAreaWidgetContents.setMouseTracking(True)
        self.scrollAreaWidgetContents1.setMouseTracking(True)
        
        
        """                        Thumbnail Mode                          """
        
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_20.setObjectName(_fromUtf8("horizontalLayout_20"))
        self.gridLayout1.addLayout(self.horizontalLayout_20, 0, 1, 1, 1)
        self.gridLayout1.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignCenter)
        self.gridLayout2.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignCenter)
        self.gridLayout2.setSpacing(5)
        
        
        
        self.btn30 = SelectButton(self.scrollAreaWidgetContents, self)
        self.btn30.setObjectName(_fromUtf8("btn30"))
        self.horizontalLayout_20.insertWidget(0, self.btn30, 0)
        self.comboBox20 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox20.setObjectName(_fromUtf8("comboBox20"))
        self.horizontalLayout_20.insertWidget(1, self.comboBox20, 0)
        
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_30.setObjectName(_fromUtf8("horizontalLayout_30"))
        self.gridLayout1.addLayout(self.horizontalLayout_30, 0, 2, 1, 1)
        
        self.comboBox30 = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBox30.setObjectName(_fromUtf8("comboBox30"))
        self.horizontalLayout_30.insertWidget(0, self.comboBox30, 0)
        
        self.comboBoxMode = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.comboBoxMode.setObjectName(_fromUtf8("comboBoxMode"))
        
        self.btn20 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btn20.setObjectName(_fromUtf8("btn20"))
        
        self.labelFrame2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.labelFrame2.setObjectName(_fromUtf8("labelFrame2"))
        self.labelFrame2.setScaledContents(True)
        self.labelFrame2.setAlignment(QtCore.Qt.AlignCenter)
        
        self.label_search = QLineCustom(self.scrollAreaWidgetContents, self)
        self.label_search.setObjectName(_fromUtf8("label_search"))
        self.label_search.setMaximumWidth(100)
        
        self.btn201 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.btn201.setObjectName(_fromUtf8("btn201"))
        self.float_window = QLabelFloat()
        self.float_window.set_globals(self, home)
        self.float_window_layout = QtWidgets.QVBoxLayout(self.float_window)
        self.float_window.setMinimumSize(200, 100)
        self.float_window.hide()
        self.float_window_dim = [1023, 28, 337, 226]
        self.float_window.setMouseTracking(True)
        #self.float_window.setScaledContents(True)
        self.float_window.setObjectName(_fromUtf8("float_window"))
        try:
            self.float_window.setWindowIcon(icon)
        except Exception as err:
            print(err, '--2170--')
        #self.float_window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.float_window.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.float_window_layout.setContentsMargins(0, 0, 0, 0)
        self.float_window_layout.setSpacing(0)
        
        self.horizontalLayout10.insertWidget(2, self.frame2, 0)
        self.horizontalLayout10.setSpacing(0)
        
        self.btn20.setMaximumWidth(96)
        self.comboBoxMode.setMaximumWidth(96)
        self.btn201.setMaximumWidth(96)
        
        self.horizontalLayout_101.insertWidget(0, self.btn20, 0)
        self.horizontalLayout_101.insertWidget(1, self.comboBoxMode, 0)
        self.horizontalLayout_101.insertWidget(2, self.labelFrame2, 0)
        self.horizontalLayout_101.insertWidget(3, self.btn201, 0)
        self.horizontalLayout_101.insertWidget(4, self.label_search, 0)
        self.horizontalLayout_101.setSpacing(0)
        
        self.frame2_height = int(self.frame_height/2.25)
        
        self.frame2.setMinimumHeight(self.frame2_height)
        self.frame2.setMaximumHeight(self.frame2_height)
        self.frame_web.setMinimumHeight(self.frame2_height)
        self.frame_web.setMaximumHeight(self.frame2_height)
        for browser_btn in self.browser_buttons:
            browser_btn.setMinimumHeight(self.frame2_height)
        
        self.btn20.setMaximumHeight(self.frame2_height)
        self.comboBoxMode.setMaximumHeight(self.frame2_height)
        self.btn201.setMaximumHeight(self.frame2_height)
        self.label_search.setMaximumHeight(self.frame2_height)
        ####################################################
        self.comboBox20.hide()
        self.comboBox30.hide()
        self.btn30.hide()
        self.btn10.setMaximumSize(QtCore.QSize(350, 16777215))
        self.comboBox20.setMaximumSize(QtCore.QSize(100, 16777215))
        
        self.chk = QtWidgets.QPushButton(self.dockWidget_3) 
        self.chk.setObjectName(_fromUtf8("chk"))
        self.chk.setText("mpv")
        self.comboView = QtWidgets.QComboBox(self.dockWidget_3) 
        self.comboView.setObjectName(_fromUtf8("comboView"))
        self.comboView.hide()
        
        #############################################
        self.btnOpt = QtWidgets.QComboBox(MainWindow)
        self.btnOpt.setObjectName(_fromUtf8("btnOpt"))
        self.horizontalLayout_7.addWidget(self.btnOpt)
        self.btnOpt.hide()
        self.go_opt = QtWidgets.QPushButton(MainWindow)
        self.go_opt.setObjectName(_fromUtf8("go_opt"))
        self.horizontalLayout_7.addWidget(self.go_opt)
        self.go_opt.hide()
        #####################################################
        self.close_frame = QtWidgets.QFrame(MainWindow)
        self.close_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.close_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.horiz_close_frame = QtWidgets.QHBoxLayout(self.close_frame)
        self.horiz_close_frame.setSpacing(0)
        self.horiz_close_frame.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout10.addWidget(self.scrollArea)
        self.scrollArea1.setWidget(self.scrollAreaWidgetContents1)
        self.horizontalLayout10.addWidget(self.scrollArea1)
        self.btn4 = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn4.setObjectName(_fromUtf8("btn4"))
        self.btn4.setMinimumHeight(30)
        self.btn4.setText('--')
        self.btn4.setToolTip('Auto-Hide On/Off')
        self.btn4.clicked.connect(self.close_frame_btn)
        self.auto_hide_dock = True
        
        self.btn_orient = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn_orient.setObjectName(_fromUtf8("btn_orient"))
        self.btn_orient.setMinimumHeight(30)
        self.btn_orient.setText(self.player_buttons['right'])
        self.btn_orient.setToolTip('Move Dock to Right')
        self.btn_orient.clicked.connect(self.orient_dock)
        self.orientation_dock = 'left'
        
        self.btn_quit = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btn_quit.setObjectName(_fromUtf8("btn_quit"))
        self.btn_quit.setMinimumHeight(30)
        self.btn_quit.setText(self.player_buttons['quit'])
        self.btn_quit.setToolTip('Quit')
        self.btn_quit.clicked.connect(QtWidgets.qApp.quit)
        
        self.horiz_close_frame.insertWidget(0, self.btn_quit, 0)
        self.horiz_close_frame.insertWidget(1, self.btn_orient, 0)
        self.horiz_close_frame.insertWidget(2, self.btn4, 0)
        
        self.btnHistory = QtWidgets.QPushButton(self.dockWidgetContents_3)
        self.btnHistory.setObjectName(_fromUtf8("btnHistory"))
        self.btnHistory.hide()
        
        self.VerticalLayoutLabel_Dock3.insertWidget(0, self.line, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(1, self.btn1, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(2, self.btnAddon, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(3, self.list3, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(4, self.btnHistory, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(5, self.btn3, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(6, self.chk, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(7, self.comboView, 0)
        self.VerticalLayoutLabel_Dock3.insertWidget(8, self.close_frame, 0)
        
        self.btn3.setMinimumHeight(30)
        self.line.setMinimumHeight(30)
        self.btn1.setMinimumHeight(30)
        self.btnAddon.setMinimumHeight(30)
        self.chk.setMinimumHeight(30)
        self.comboView.setMinimumHeight(30)
        self.btnHistory.setMinimumHeight(30)
        
        self.superGridLayout.addWidget(self.frame1, 1, 1, 1, 1)
        
        self.verticalLayout_50.insertWidget(0, self.list2, 0)
        self.verticalLayout_50.insertWidget(1, self.list6, 0)
        self.verticalLayout_50.insertWidget(2, self.list5, 0)
        self.verticalLayout_50.insertWidget(3, self.goto_epn, 0)
        
        self.verticalLayout_40.insertWidget(0, self.list1, 0)
        self.verticalLayout_40.insertWidget(1, self.list4, 0)
        self.verticalLayout_40.insertWidget(2, self.frame, 0)
        self.verticalLayout_40.setSpacing(5)
        self.verticalLayout_50.setSpacing(5)
        
        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.frame_options)
        self.frame_timer.setSingleShot(True)
    
        self.mplayer_timer = QtCore.QTimer()
        self.mplayer_timer.timeout.connect(self.mplayer_unpause)
        self.mplayer_timer.setSingleShot(True)
        self.version_number = (3, 3, 0, 0)
        self.threadPool = []
        self.threadPoolthumb = []
        self.thumbnail_cnt = 0
        self.player_setLoop_var = False
        self.playerPlaylist_setLoop_var = 0
        self.thread_server = QtCore.QThread()
        self.do_get_thread = QtCore.QThread()
        self.mplayer_status_thread = QtCore.QThread()
        self.stream_session = None
        self.start_streaming = False
        self.local_http_server = QtCore.QThread()
        self.local_ip = ''
        self.local_port = ''
        self.local_ip_stream = ''
        self.local_port_stream = ''
        self.search_term = ''
        self.mpv_cnt = 0
        self.remote_control = False
        self.remote_control_field = False
        self.local_file_index = []
        self.quality_val = 'best'
        self.client_quality_val = 'best'
        self.client_yt_mode = 'offline'
        self.quality_dict = {'sd':'SD', 'hd':'HD', 'best':'BEST', 'sd480p':'480'}
        self.playlist_auth_dict_ui = {}
        self.media_server_key = None
        self.my_public_ip = None
        self.get_ip_interval = 1
        self.access_from_outside_network = False
        self.cloud_ip_file = None
        self.keep_background_constant = False
        self.https_media_server = False
        self.media_server_cookie = False
        self.cookie_expiry_limit = 24
        self.cookie_playlist_expiry_limit = 24
        self.logging_module = False
        self.ytdl_path = 'default'
        self.ytdl_arr = []
        self.anime_review_site = False
        self.get_artist_metadata = False
        self.https_cert_file = os.path.join(home, 'cert.pem')
        self.progress_counter = 0
        self.posterfound_arr = []
        self.client_auth_arr = ['127.0.0.1', '0.0.0.0']
        self.video_db_location = os.path.join(home, 'VideoDB')
        if not os.path.isdir(self.video_db_location):
            os.makedirs(self.video_db_location)
        self.current_background = os.path.join(home, 'default.jpg')
        self.default_background = os.path.join(home, 'default.jpg')
        self.yt_sub_folder = os.path.join(home, 'External-Subtitle')
        
        self.playing_history_file = os.path.join(self.video_db_location, 'historydata')
        self.playing_queue_file = os.path.join(home, 'src', 'queuedata')
        self.tmp_pls_file = os.path.join(TMPDIR, 'tmp_playlist.m3u')
        self.tmp_pls_file_lines = []
        self.tmp_pls_file_dict = {}
        self.torrent_type = 'file'
        self.torrent_handle = ''
        self.list_with_thumbnail = False
        self.mpvplayer_val = QtCore.QProcess()
        self.playback_mode = 'single'
        self.gapless_playback = False
        self.gapless_network_stream = False
        self.gapless_network_stream_disabled = False
        self.gapless_playback_disabled = False
        self.mpv_prefetch_url_started = False
        self.use_single_network_stream = True
        self.mpv_prefetch_url_thread = QtCore.QThread()
        self.title_list_changed = False
        self.fullscreen_video = False
        self.subtitle_dict = {}
        self.apply_subtitle_settings = True
        self.screenshot_directory = TMPDIR
        self.gsbc_dict = {}
        self.clicked_label_new = False
        self.layout_mode = 'Default'
        self.audio_outputs = ''
        self.video_outputs = ''
        self.cache_pause_seconds = 4
        self.player_volume = 'auto'
        self.volume_type = 'ao-volume'
        self.use_custom_config_file = False
        self.browser_backend = BROWSER_BACKEND
        self.settings_tab_index = 0
        #video_parameters=[url, seek_time, cur_time, sub, aid, rem_quit, vol, asp]
        self.theme_list = ['Default', 'Dark', 'System']
        self.video_parameters = ['none', 0, 0, 'auto', 'auto', 0, 'auto', '-1']
        self.local_site_list = ['Video', 'Music', 'PlayLists', 'None', 'MyServer', 'NONE']
        self.quit_really = 'no'
        self.restore_volume = False
        self.restore_aspect = True
        self.wget = QtCore.QProcess()
        self.video_local_stream = False
        self.cur_row = 0
        self.mpvplayer_string_list = []
        try:
            self.global_font = QtGui.QFont().defaultFamily()
        except Exception as err:
            logger.error(err)
            self.global_font = 'Ubuntu'
        self.global_font_size = 10
        self.show_search_thumbnail = False
        self.tab_6_size_indicator = []
        self.tab_6_player = False
        self.epn_list_count = []
        self.view_mode = 'list'
        self.queue_stop = False
        self.queue_item = None
        self.history_dict_obj = {}
        self.series_info_dict = {}
        self.poster_count_start = 0
        self.focus_widget = None
        self.status_dict = {'label_dock':0}
        self.status_dict_widget = {}
        self.player_theme = 'default'
        self.mpv_length_find_attempt = 0
        self.force_fs = False
        self.media_server_cache_music = {}
        self.media_server_cache_video = {}
        self.media_server_cache_playlist = {}
        self.icon_poster_indicator = [6]
        self.mplayer_finished_counter = 0
        self.wget_counter_list = []
        self.wget_counter_list_text = []
        self.options_mode = 'legacy'
        self.acquire_subtitle_lock = False
        self.cache_mpv_indicator = False
        self.cache_mpv_counter = '00'
        self.mpv_playback_duration = None
        self.thumbnail_label_number = [0, 'None']
        self.broadcast_message = 'kawaii-player {0}'.format(self.version_number)
        self.broadcast_server = False
        self.broadcast_thread = None
        self.discover_server = False
        self.discover_thread = None
        self.broadcast_server_list = []
        self.myserver_cache = {}
        self.newlistfound_thread_box = []
        self.myserver_threads_count = 0
        self.mpvplayer_aspect = {'0':'-1', '1':'16:9', '2':'4:3', '3':'2.35:1', '4':'0'}
        self.playback_engine = ["mpv", 'mplayer']
        self.mpvplayer_aspect_cycle = 0
        self.setuploadspeed = 0
        self.custom_mpv_input_conf = False
        self.mpv_custom_pause = False
        self.epn_lock_thread = False
        self.epn_wait_thread = QtCore.QThread()
        self.epnfound_final_link = ""
        self.eof_reached = False
        self.eof_lock = False
        self.detach_fullscreen = False
        self.tray_widget = None
        self.web_review_browser_started = False
        self.external_audio_file = False
        self.show_client_thumbnails = True
        self.navigate_playlist_history = CustomList()
        self.set_thumbnail_thread_list = []
        self.thread_grid_thumbnail = []
        self.music_playlist = False
        self.downloadWgetText = []
        self.quick_url_play = ''
        self.yt_title_thread = False
        self.media_server_autostart = False
        self.category_dict = {
            'anime':'Anime', 'movies':'Movies', 'tv shows':'TV Shows',
            'cartoons':'Cartoons', 'others':'Others'
            }
        self.category_array = ['Anime', 'Movies', 'TV Shows', 'Cartoons', 'Others']
        self.update_video_dict_criteria()
        self.posterfind_batch = 0
        self.epn_arr_list = []
        self.icon_size_arr = []
        self.original_path_name = []
        self.download_video = 0
        self.total_seek = 0
        self.new_tray_widget = None
        self.widget_style = WidgetStyleSheet(self, home, BASEDIR, MainWindow)
        self.metaengine = MetaEngine(self, logger, TMPDIR, home)
        self.player_val = 'mpv'
        self.addons_option_arr = []
        self.mpvplayer_started = False
        self.mplayerLength = 0
        self.mpvplayer_command = []
        self.torrent_upload_limit = 0
        self.torrent_download_limit = 0
        self.torrent_download_folder = TMPDIR
        self.default_download_location = TMPDIR
        self.tmp_download_folder = TMPDIR
        self.logger = logger
        self.home_folder = home
        self.last_dir = os.path.expanduser("~")
        self.epn_name_in_list = ''
        self.getdb = None
        self.review_site_code = 'g'
        self.external_url = False
        self.subtitle_new_added = False
        self.window_frame = 'true'
        self.float_window_open = False
        self.music_mode_dim = [454, 29, 910, 340]
        self.music_mode_dim_show = False
        self.site_var = ''
        self.record_history = False
        self.depth_list = 0
        self.display_list = False
        self.tmp_web_srch = ''
        self.get_fetch_library = 'pycurl'
        self.image_fit_option_val = 3
        self.tmp_folder_remove = 'no'
        self.video_mode_index = 1
        self.current_thumbnail_position = (0, 0, 1, 1)
        self.fullscreen_mode = 0
        self.mplayer_pause_buffer = False
        self.mplayer_nop_error_pause = False
        self.started_from_external_client = False
        self.music_type_arr = [
            'mp3', 'flac', 'ogg', 'wav', 'aac', 'wma',
            'm4a', 'm4b', 'opus', 'webm'
            ]
        self.video_type_arr = [
            'mkv', 'mp4', 'avi', 'flv', 'ogg', 'wmv', 'webm'
            ]
        self.video_dict = {}
        self.music_dict = {}
        self.browser_bookmark = {
            'Reviews': 'Reviews',
            'ANN': 'http://www.animenewsnetwork.com/encyclopedia/search/name?q=',
            'AniDB': 'http://anidb.net/perl-bin/animedb.pl?show=animelist&do.search=search&adb.search=',
            'Zerochan': 'http://www.zerochan.net/search?q=',
            'MyAnimeList': 'http://myanimelist.net/anime.php?q=',
            'Anime-Planet': 'http://www.anime-planet.com/anime/all?name=',
            'Anime-Source': 'http://www.anime-source.com/banzai/modules.php?name=NuSearch&type=all&action=search&info=',
            'TVDB': 'http://thetvdb.com/?searchseriesid=&tab=listseries&function=Search&string=',
            'TMDB': 'https://www.themoviedb.org/search?query=',
            'Google': 'https://www.google.com/search?q=',
            'YouTube': 'https://m.youtube.com/results?search_query=',
            'DuckDuckGo': 'https://duckduckgo.com/?q=',
            'last.fm': 'http://www.last.fm/search?q='
            }
        self.list_poster = TitleListWidgetPoster(
                MainWindow, self, home, TMPDIR, logger,
                screen_width, screen_height
                )
        self.list_poster.hide()
        #self.settings_close_btn = QtWidgets.QPushButton(MainWindow)
        #self.settings_close_btn.hide()
        self.settings_box = OptionsSettings(MainWindow, self, TMPDIR)
        self.settings_box.setMaximumWidth(screen_width-self.width_allowed-35)
        #self.settings_box.setElideMode(QtCore.Qt.ElideRight)
        self.vertical_layout_new.insertWidget(0, self.settings_box)
        #self.settings_box.setTabPosition(QtWidgets.QTabWidget.West)
        self.settings_box.setUsesScrollButtons(False)
        self.settings_box.hide()
        self.widget_dict = {
            'list1':self.list1, 'list2':self.list2, 'frame1':self.frame1,
            'label':self.label, 'label_new':self.label_new, 'text':self.text,
            'player':self.tab_5, 'scrollArea':self.scrollArea,
            'scrollArea1':self.scrollArea1, 'frame':self.frame,
            'dock_3':self.dockWidget_3, 'tab_2':self.tab_2,
            'tab_6':self.tab_6
            }
        self.frame_extra_toolbar = ExtraToolBar(MainWindow, self)
        self.verticalLayout_50.insertWidget(5, self.frame_extra_toolbar, 0)
        self.frame_extra_toolbar.setMaximumSize(QtCore.QSize(self.width_allowed, int(screen_height/1.5)))
        
        self.browser_dict_widget = {}
        self.update_proc = QtCore.QProcess()
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn30.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        self.btn2.addItem(_fromUtf8(""))
        
        
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboBox20.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboView.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.comboBoxMode.addItem(_fromUtf8(""))
        self.global_shortcut_keys = {
            'Shift+F':self.fullscreenToggle,
            'Shift+L':self.setPlayerFocus,
            'Shift+G':self.dockShowHide,
            'Shift+H':self.show_hide_progressbar,
            'Ctrl+F':self.show_hide_filter_toolbar,
            'Ctrl+P':self.settings_box.start,
            'Ctrl+Z':self.IconView,
            'Shift+Z':(self.IconViewEpn, 3),
            'F1': (self.experiment_list, 'show'),
            'Ctrl+X':self.webHide,
            'ESC':self.HideEveryThing,
            'Alt+Right': (self.direct_web, 'right'),
            'Alt+Left': (self.direct_web, 'left'),
            'Ctrl+0': (self.change_fanart_aspect, 0),
            'Ctrl+1': (self.change_fanart_aspect, 1),
            'Ctrl+2': (self.change_fanart_aspect, 2),
            'Ctrl+3': (self.change_fanart_aspect, 3),
            'Ctrl+4': (self.change_fanart_aspect, 4),
            'Ctrl+5': (self.change_fanart_aspect, 5),
            'Ctrl+6': (self.change_fanart_aspect, 6),
            'Ctrl+7': (self.change_fanart_aspect, 7),
            'Ctrl+8': (self.change_fanart_aspect, 8),
            'Ctrl+9': (self.change_fanart_aspect, 9),
            }
        for i in self.global_shortcut_keys:
            QtWidgets.QShortcut(
                QtGui.QKeySequence(i), MainWindow,
                partial(self.global_shortcuts, i ,self.global_shortcut_keys[i])
                )
        self.list1.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list3.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list4.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list4.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list5.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list5.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list6.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.list6.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea1.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea1.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.retranslateUi(MainWindow)
        
        self.player_opt_toolbar.clicked.connect(self.player_opt_toolbar_dock)
        self.sd_hd.clicked.connect(self.selectQuality)
        self.goto_epn_filter.clicked.connect(self.goto_epn_filter_on)
        self.audio_track.clicked.connect(self.toggleAudio)
        self.subtitle_track.clicked.connect(self.toggleSubtitle)
        self.player_stop.clicked.connect(self.playerStop)
        self.player_prev.clicked.connect(self.mpvPrevEpnList)
        self.player_play_pause.clicked.connect(self.playerPlayPause)
        self.player_loop_file.clicked.connect(
            lambda x=0: self.playerLoopFile(self.player_loop_file)
            )
        self.player_next.clicked.connect(self.mpvNextEpnList)
        self.mirror_change.clicked.connect(self.mirrorChange)
        self.btn20.clicked.connect(lambda r = 0: self.thumbnailHide('clicked'))
        self.btn201.clicked.connect(self.prev_thumbnails)
        
        #self.go_opt.clicked.connect(self.go_opt_options)
        #self.btn10.currentIndexChanged['int'].connect(self.browse_epn)
        self.line.returnPressed.connect(self.searchNew)
        self.label_down_speed.returnPressed.connect(self.set_new_download_speed)
        self.label_up_speed.returnPressed.connect(self.set_new_upload_speed)
        self.label_torrent_stop.clicked.connect(self.stop_torrent)
        self.page_number.returnPressed.connect(self.gotopage)
        self.btn1.currentIndexChanged['int'].connect(self.ka)
        self.btnAddon.currentIndexChanged['int'].connect(self.ka2)
        self.btn30.currentIndexChanged['int'].connect(self.ka1)
        #self.comboBox20.currentIndexChanged['int'].connect(self.browserView_view)
        #self.comboView.currentIndexChanged['int'].connect(self.viewPreference)
        self.comboBoxMode.currentIndexChanged['int'].connect(self.set_video_mode)
        
        self.list1.itemDoubleClicked['QListWidgetItem*'].connect(self.list1_double_clicked)
        self.list1.currentRowChanged['int'].connect(self.history_highlight)
        self.list3.currentRowChanged['int'].connect(self.options_clicked)
        self.list4.currentRowChanged['int'].connect(self.search_highlight)
        self.list2.itemDoubleClicked['QListWidgetItem*'].connect(self.epnClicked)
        self.list2.currentRowChanged['int'].connect(self.epn_highlight)
        self.list3.itemDoubleClicked['QListWidgetItem*'].connect(
            lambda var = 'clicked':self.newoptions('clicked')
            )
        self.forward.clicked.connect(lambda r= "": self.nextp('next'))
        self.backward.clicked.connect(lambda r= "": self.backp('back'))
        self.filter_btn.clicked.connect(self.filter_btn_options)
        self.hide_btn_list1.clicked.connect(self.hide_btn_list1_pressed)
        self.go_page.textChanged['QString'].connect(self.filter_list)
        self.search_on_type_btn.textChanged['QString'].connect(self.search_on_type)
        self.label_search.textChanged['QString'].connect(self.filter_label_list)
        self.goto_epn_filter_txt.textChanged['QString'].connect(self.filter_epn_list_txt)
        self.btn3.clicked.connect(self.addToLibrary)
        self.btnHistory.clicked.connect(self.setPreOpt)
        self.chk.clicked.connect(self.preview)
        
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.btn2.hide()
        self.line.setPlaceholderText("Search")
        self.label_search.setPlaceholderText("Filter")
        self.go_page.setPlaceholderText("Filter")
        
    def retranslateUi(self, MainWindow):
        global home
        MainWindow.setWindowTitle("Kawaii-Player")
        self.float_window.setWindowTitle("Kawaii-Player")
        self.line.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p>Enter Search Keyword</p></body></html>", 
            None)
            )
        self.backward.setText(_translate("MainWindow", "Previous", None))
        self.filter_btn.setText(_translate("MainWindow", "Filter", None))
        self.btnHistory.setText(_translate("MainWindow", "History", None))
        self.go_opt.setText(_translate("MainWindow", "Go", None))
        self.go_page.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p>Filter or Search</p></body></html>", 
            None)
            )
        self.forward.setText(_translate("MainWindow", "Next", None))
        self.page_number.setToolTip(
            _translate("MainWindow", 
            "<html><head/><body><p align=\"center\">Enter Page Number</p></body></html>", 
            None)
            )
        self.btn30.setItemText(0, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(1, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(2, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(3, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(4, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(5, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(6, _translate("MainWindow", "Select", None))
        self.btn30.setItemText(7, _translate("MainWindow", "Select", None))
        self.btn3.setText(_translate("MainWindow", "Library", None))
        self.btn2.setItemText(0, _translate("MainWindow", "Reviews", None))
        self.btn2.setItemText(1, _translate("MainWindow", "MyAnimeList", None))
        self.btn2.setItemText(2, _translate("MainWindow", "Anime-Planet", None))
        self.btn2.setItemText(3, _translate("MainWindow", "Anime-Source", None))
        self.btn2.setItemText(4, _translate("MainWindow", "TVDB", None))
        self.btn2.setItemText(5, _translate("MainWindow", "ANN", None))
        self.btn2.setItemText(6, _translate("MainWindow", "AniDB", None))
        self.btn2.setItemText(7, _translate("MainWindow", "Google", None))
        self.btn2.setItemText(8, _translate("MainWindow", "Youtube", None))
        
        self.comboBox20.setItemText(0, _translate("MainWindow", "Options", None))
        self.comboBox20.setItemText(1, _translate("MainWindow", "Clear", None))
        self.comboBox20.setItemText(2, _translate("MainWindow", "MostPopular", None))
        self.comboBox20.setItemText(3, _translate("MainWindow", "Random", None))
        self.comboBox20.setItemText(4, _translate("MainWindow", "History", None))
        self.comboView.setItemText(0, _translate("MainWindow", "View Mode", None))
        self.comboView.setItemText(1, _translate("MainWindow", "List", None))
        self.comboView.setItemText(2, _translate("MainWindow", "Thumbnail", None))
        self.btn20.setText(_translate("MainWindow", self.player_buttons['close'], None))
        self.btn201.setText(_translate("MainWindow", self.player_buttons['prev'], None))
        self.comboBoxMode.setItemText(0, 'Mode 1')
        self.comboBoxMode.setItemText(1, 'Mode 2')
        self.comboBoxMode.setItemText(2, 'Mode 3')
        self.comboBoxMode.setItemText(3, 'Mode 4')
        self.comboBoxMode.setItemText(4, 'Mode 5')
        
        self.thumb_timer = QtCore.QTimer()
        self.mplayer_OsdTimer = QtCore.QTimer()
        self.mplayer_OsdTimer.timeout.connect(self.osd_hide)
        self.mplayer_OsdTimer.setSingleShot(True)
        
        self.mplayer_SubTimer = QtCore.QTimer()
        self.mplayer_SubTimer.timeout.connect(self.subMplayer)
        self.mplayer_SubTimer.setSingleShot(True)
        
        self.external_SubTimer = QtCore.QTimer()
        self.external_SubTimer.timeout.connect(self.load_external_sub)
        self.external_SubTimer.setSingleShot(True)
        
        self.float_timer = QtCore.QTimer()
        self.float_timer.timeout.connect(self.float_activity)
        self.float_timer.setSingleShot(True)
        
        self.total_file_size = 0
        self.id_audio_bitrate = 0
        self.id_video_bitrate = 0
        self.final_playing_url = ""
        self.queue_url_list = []
        self.downloadWget = []
        self.downloadWget_cnt = 0
        self.lock_process = False
        self.mpv_thumbnail_lock = False
        
    def player_volume_manager(self):
        if self.frame_extra_toolbar.isHidden():
            if self.fullscreen_video:
                self.gridLayout.setSpacing(5)
                self.superGridLayout.setSpacing(5)
            self.frame_extra_toolbar.show()
            if self.list2.isHidden():
                self.list2.show()
                self.frame_extra_toolbar.playlist_hide = True
                if self.list_with_thumbnail:
                    if self.title_list_changed:
                        self.update_list2()
                    if self.cur_row < self.list2.count():
                        self.list2.setCurrentRow(self.cur_row)
                    self.title_list_changed = False
        else:
            if self.fullscreen_video:
                self.gridLayout.setSpacing(0)
                self.superGridLayout.setSpacing(0)
            self.frame_extra_toolbar.slider_volume.pressed = False
            self.frame_extra_toolbar.hide()
            if self.frame_extra_toolbar.playlist_hide:
                self.list2.hide()
            self.frame_extra_toolbar.playlist_hide = False
        
    def global_shortcuts(self, val, val_function):
        player_focus = False
        if self.mpvplayer_val.processId() > 0:
            if self.idw == str(int(self.tab_5.winId())):
                if self.tab_5.hasFocus():
                    player_focus = True
            elif self.idw == str(int(self.label_new.winId())):
                if self.label_new.hasFocus():
                    player_focus = True
            elif self.idw == str(int(self.label.winId())):
                if self.label.hasFocus():
                    player_focus = True
            else:
                player_focus = True
        if player_focus:
            modifier = None
            modifier_event = None
            value = None
            if '+' in val:
                modifier, value = val.split('+', 1)
            else:
                value = val
            if modifier == 'Shift':
                modifier_event = QtGui.QKeyEvent(
                    QtCore.QEvent.KeyPress, QtCore.Qt.Key_Shift,
                    QtCore.Qt.ShiftModifier, None, False, 1
                )
            elif modifier == 'Ctrl':
                modifier_event = QtGui.QKeyEvent(
                    QtCore.QEvent.KeyPress, QtCore.Qt.Key_Control,
                    QtCore.Qt.ControlModifier, 'control', False, 1
                )
            elif modifier == 'Alt':
                modifier_event = QtGui.QKeyEvent(
                    QtCore.QEvent.KeyPress, QtCore.Qt.Key_Control,
                    QtCore.Qt.AltModifier, 'alt', False, 1
                )
            if modifier_event:
                self.tab_5.keyPressEvent(modifier_event)
                
            if value:
                key = None
                val_string = ''
                if value == 'F1':
                    key = QtCore.Qt.Key_F1
                elif value == 'ESC':
                    key = QtCore.Qt.Key_Escape
                else:
                    try:
                        key = eval('QtCore.Qt.Key_{}'.format(value))
                    except Exception as err:
                        logger.error(err)
                logger.debug(key)
                if key:
                    key_event =  QtGui.QKeyEvent(
                        QtCore.QEvent.KeyPress, key,
                        QtCore.Qt.NoModifier, value.lower(), False, 1
                        )
                    self.tab_5.keyPressEvent(key_event)
                else:
                    self.process_regular_shortcuts(val, val_function)
            else:
                self.process_regular_shortcuts(val, val_function)
        else:
            self.process_regular_shortcuts(val, val_function)
                
    def process_regular_shortcuts(self, val, val_function):
        if not isinstance(val_function, tuple):
            val_function()
        else: 
            function_map = val_function[0]
            function_arg = val_function[1]
            if val == 'Shift+Z':
                function_map(mode=function_arg)
            else:
                function_map(function_arg)
            
    def experiment_list(self, mode=None):
        global screen_width, screen_height
        self.view_mode = 'thumbnail_light'
        self.list_poster.title_clicked = True
        if mode == 'show' or mode is None:
            self.list_poster.show_list()
        elif mode == 'hide':
            logger.debug(self.list_poster.title_clicked)
            
    def give_search_index(self, txt, mode=None, widget=None):
        index_found = False
        widget_list = None
        if widget == self.list1:
            widget_list = self.original_path_name
        else:
            widget_list = self.epn_arr_list
        if widget_list:
            for i, j in enumerate(widget_list):
                if '\t' in j:
                    title_name = j.split('\t')[0]
                else:
                    title_name = j
                title_name = title_name.lower()
                if title_name.startswith('#'):
                    title_name = title_name.replace('#', '', 1)
                if mode == 0:
                    if title_name.startswith(txt):
                        index_found = True
                        break
                elif mode == 1:
                    if txt in title_name:
                        index_found = True
                        break
        if index_found:
            return i
        else:
            return -1
            
    def search_on_type(self):
        txt = self.search_on_type_btn.text()
        index = self.give_search_index(txt, mode=0, widget=self.focus_widget)
        if index < 0:
            index = self.give_search_index(txt, mode=1, widget=self.focus_widget)
        if index >=0:
            if self.focus_widget == self.list1:
                try:
                    self.list1.setCurrentRow(index)
                    if self.view_mode == 'thumbnail' and not self.lock_process:
                        self.take_to_thumbnail(row=index, mode='title')
                        self.scrollArea.cur_row = index
                    elif self.view_mode == 'thumbnail_light':
                        self.list_poster.setCurrentRow(index)
                except Exception as err:
                    logger.error(err)
            elif self.focus_widget == self.list2:
                self.list2.setCurrentRow(index)
                try:
                    if not self.tab_6.isHidden():
                        self.take_to_thumbnail(row=index, mode='epn')
                        self.scrollArea1.cur_row = index
                except Exception as err:
                    logger.error(err)
            
    def remove_queue_item_btn_method(self, row=None):
        row = self.queue_item_external_remove
        if row >= 0:
            r = row
            if self.list6.item(r):
                item = self.list6.item(r)
                self.list6.takeItem(r)
                del item
                if not self.video_local_stream and r < len(self.queue_url_list):
                    del self.queue_url_list[r]
            self.queue_item_external_remove = -1
    
    def set_queue_item_btn_method(self, row=None):
        global site
        #if row is None:
        row = self.queue_item_external
        if row >= 0:
            if (site == "Music" or site == "Video" or site == "Local" 
                    or site == "PlayLists" or site == "None"):
                file_path = os.path.join(home, 'Playlists', 'Queue')
                if not os.path.exists(file_path):
                    f = open(file_path, 'w')
                    f.close()
                if not self.queue_url_list:
                    self.list6.clear()
                r = row
                item = self.list2.item(r)
                if item:
                    self.queue_url_list.append(self.epn_arr_list[r])
                    self.list6.addItem(self.epn_arr_list[r].split('	')[0])
                    logger.info(self.queue_url_list)
                    write_files(file_path, self.epn_arr_list[r], line_by_line=True)
            elif self.video_local_stream:
                if ui.list6.count() > 0:
                    txt = self.list6.item(0).text()
                    if txt.startswith('Queue Empty:'):
                        self.list6.clear()
                item = self.list2.item(row)
                if item:
                    self.list6.addItem(item.text()+':'+str(row))
            else:
                if not self.queue_url_list:
                    self.list6.clear()
                r = row
                item = self.list2.item(r)
                if item:
                    self.queue_url_list.append(self.epn_arr_list[r])
                    self.list6.addItem(self.epn_arr_list[r].split('	')[0])
            self.queue_item_external = -1
    
    def set_quality_server_btn_method(self):
        if self.quality_val in self.quality_dict:
            self.sd_hd.setText(self.quality_dict[self.quality_val])
            
    def show_hide_progressbar(self):
        if self.progress.isHidden():
            self.progress.show()
        else:
            self.progress.hide()
            
    def quick_torrent_play_method(self, url):
        if self.thread_server.isRunning():
            self.label_torrent_stop.clicked.emit()
        time.sleep(0.5)
        hist_folder = os.path.join(home, 'History', 'Torrent')
        hist_name = self.getdb.record_torrent(url, hist_folder)
        self.btn1.setCurrentIndex(0)
        index = self.btn1.findText('Addons')
        self.btn1.setCurrentIndex(index)
        time.sleep(1)
        self.btnAddon.setCurrentIndex(0)
        index = self.btnAddon.findText('Torrent')
        self.btnAddon.setCurrentIndex(index)
        time.sleep(1)
        list_item = self.list3.findItems('History', QtCore.Qt.MatchExactly)
        if len(list_item) > 0:
            for i in list_item:
                row = self.list3.row(i)
                self.list3.setFocus()
                self.list3.setCurrentRow(row)
                item = self.list3.item(row)
                logger.debug(':::::row:::{0}::::::::'.format(row))
                if item:
                    self.list3.itemDoubleClicked['QListWidgetItem*'].emit(item)
        time.sleep(1)
        list_item = self.list1.findItems(hist_name, QtCore.Qt.MatchExactly)
        if len(list_item) > 0:
            for i in list_item:
                row = self.list1.row(i)
                self.list1.setFocus()
                self.list1.setCurrentRow(row)
                item = self.list1.item(row)
                logger.debug(':::::row:::{0}::::::::'.format(row))
                if item:
                    self.list1.itemDoubleClicked['QListWidgetItem*'].emit(item)
        time.sleep(1)
        self.list2.setFocus()
        item = self.list2.item(0)
        self.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
        #self.torrent_frame.show()
        self.progress.show()
            
    def quick_url_play_method(self):
        if self.gapless_playback:
            self.gapless_playback = False
            self.gapless_playback_disabled = True
        if self.gapless_network_stream:
            self.gapless_network_stream = False
            self.gapless_network_stream_disabled = True
        if self.quick_url_play.startswith('magnet'):
            self.quick_torrent_play_method(url=self.quick_url_play)
        else:
            self.watch_external_video(self.quick_url_play, start_now=True)
            self.btn1.setCurrentIndex(0)
    
    def download_thread_finished(self, dest, r, length):
        
        logger.info("Download tvdb image: {0} :completed".format(dest))
        self.image_fit_option(dest, dest, fit_size=6, widget=self.label)
        logger.info("Image: {0} : aspect ratio changed".format(dest))
        try:
            if r < self.list2.count() and self.list_with_thumbnail:
                icon_new_pixel = self.create_new_image_pixel(dest, 128)
                if os.path.exists(icon_new_pixel):
                    self.list2.item(r).setIcon(QtGui.QIcon(icon_new_pixel))
        except Exception as e:
            print(e)
        self.downloadWget_cnt += 1
        thr = self.downloadWget[length]
        del thr
        self.downloadWget[length] = None
        
        if not self.wget_counter_list:
            for i in self.downloadWget:
                if i is not None:
                    self.wget_counter_list.append(1)
            if not self.wget_counter_list:
                self.downloadWget[:] = []
        else:
            self.wget_counter_list.pop()
        
        if length+1 < len(self.downloadWget):
            if self.downloadWget[length+1] is not None:
                if self.downloadWget[length+1].isFinished():
                    pass
                elif not self.downloadWget[length+1].isRunning():
                    self.downloadWget[length+1].start()
        
        if length+2 < len(self.downloadWget):
            if self.downloadWget[length+2] is not None:
                if self.downloadWget[length+2].isFinished():
                    pass
                elif not self.downloadWget[length+2].isRunning():
                    self.downloadWget[length+2].start()
        
    def download_thread_text_finished(self, dest, r, length):
        logger.info("Download tvdb summary: {0} :completed".format(dest))
        thr = self.downloadWgetText[length]
        del thr
        self.downloadWgetText[length] = None
        
        if not self.wget_counter_list_text:
            for i in self.downloadWgetText:
                if i is not None:
                    self.wget_counter_list_text.append(1)
            if not self.wget_counter_list_text:
                self.downloadWgetText[:] = []
        else:
            self.wget_counter_list_text.pop()
        
        if length+1 < len(self.downloadWgetText):
            if self.downloadWgetText[length+1] is not None:
                if self.downloadWgetText[length+1].isFinished():
                    pass
                elif not self.downloadWgetText[length+1].isRunning():
                    self.downloadWgetText[length+1].start()
        
        if length+2 < len(self.downloadWgetText):
            if self.downloadWgetText[length+2] is not None:
                if self.downloadWgetText[length+2].isFinished():
                    pass
                elif not self.downloadWgetText[length+2].isRunning():
                    self.downloadWgetText[length+2].start()

    def update_video_dict_criteria(self):
        video_dir_path = os.path.join(home, 'VideoDB')
        if not os.path.exists(video_dir_path):
            os.makedirs(video_dir_path)
        video_category_path = os.path.join(video_dir_path, 'extra_category')
        if not os.path.isfile(video_category_path):
            open(video_category_path, 'w').close()
        else:
            cat_lines = open_files(video_category_path, True)
            cat_lines = [i.strip() for i in cat_lines if i.strip()]
            for i in cat_lines:
                self.category_array.append(i)
                self.category_dict.update({i.lower():i})
            logger.info('{0}::{1}::--1808--'.format(self.category_dict, self.category_array))
            
    def direct_web(self, mode):
        if not self.tab_2.isHidden():
            if mode == 'right':
                self.go_next_web_page()
            elif mode == 'left':
                self.go_prev_web_page()
    
    def set_parameters_value(
            self, siteval=None, curRow=None, quit_r=None, thumb_indicator=None,
            iconv=None, bufm=None, cache_val=None, iconvr=None, pause_i=None,
            mpv_i=None, fullsc=None, tab_6=None, cur_label=None, path_final=None,
            idw_val=None, amp=None, cur_ply=None, t6_ply=None, inter=None,
            memory_num=None, show_hide_pl=None, show_hide_tl=None, op=None,
            qual=None, mir=None, name_val=None, catg=None, local_ip=None,
            book_mark=None):
        global site, iconv_r, thumbnail_indicator
        global buffering_mplayer, cache_empty, iconv_r_indicator
        global pause_indicator, mpv_indicator
        global cur_label_num, path_final_Url, current_playing_file_path
        global artist_name_mplayer, tab_6_player, interval, memory_num_arr
        global show_hide_playlist, show_hide_titlelist, opt, mirrorNo
        global name, category, bookmark
        if siteval:
            site = siteval
        if catg:
            category = catg
        if op:
            opt = op
        if book_mark:
            bookmark = True
        if local_ip:
            self.local_ip_stream = get_lan_ip()
        if mir:
            mirrorNo = mir
        if name_val:
            name = name_val
        if iconv:
            iconv_r = iconv
        if iconvr:
            iconv_r_indicator = iconvr
        if pause_i:
            pause_indicator = pause_i
        if mpv_i:
            mpv_indicator = mpv_i
        if memory_num:
            memory_num_arr = memory_num
        if cur_label:
            cur_label_num = cur_label
        if show_hide_pl:
            show_hide_playlist = show_hide_pl
        if show_hide_tl:
            show_hide_titlelist = show_hide_tl
        if tab_6:
            self.tab_6_size_indicator = tab_6.copy()
        if amp:
            artist_name_mplayer = amp
        if cur_ply:
            current_playing_file_path = cur_ply
        if t6_ply:
            self.tab_6_player = t6_ply
        if path_final:
            path_final_Url = path_final
        if inter:
            interval = inter
        if thumb_indicator:
            if thumb_indicator == 'empty':
                thumbnail_indicator[:] = []
        if bufm:
            buffering_mplayer = bufm
        if cache_val:
            cache_empty = cache_val
            
    def get_parameters_value(self, *arg, **kargs):
        global path_final_Url, opt, site, siteName
        global name, html_default_arr
        global pause_indicator, mpv_indicator, rfr_url, total_till
        global show_hide_titlelist, show_hide_cover, iconv_r_indicator
        global iconv_r, cur_label_num, tab_6_size_indicator
        global refererNeeded, server, memory_num_arr
        global finalUrlFound, interval, name, opt, bookmark, status
        global base_url, embed, mirrorNo, category, screen_width, screen_height
        arg_dict = {}
        for key, val in kargs.items():
            arg_dict.update({'{0}'.format(val):eval(str(val))})
        return arg_dict
        
    def remote_fullscreen(self):
        global MainWindow, site
        if MainWindow.isHidden():
            MainWindow.show()
        if not MainWindow.isHidden():
            if not MainWindow.isFullScreen():
                if os.name == 'nt' and self.web_review_browser_started:
                    self.detach_fullscreen = True
                    MainWindow.hide()
                    self.tray_widget.right_menu._detach_video()
                    if not self.float_window.isFullScreen():
                        self.float_window.showFullScreen()
                        self.tab_5.setFocus()
                else:
                    if not self.tab_6.isHidden():
                        self.fullscreen_mode = 1
                    elif not self.float_window.isHidden():
                        self.fullscreen_mode = 2
                    else: 
                        self.fullscreen_mode = 0
                    
                    #self.btn20.hide()
                    if self.wget.processId() > 0 or self.video_local_stream:
                        self.progress.hide()
                        if not self.torrent_frame.isHidden():
                            self.torrent_frame.hide()
                    if site == 'Music':
                        if self.frame1.isHidden():
                            self.frame1.show()
                        if self.text.isHidden():
                            self.text.show()
                        if self.label.isHidden():
                            self.label.show()
                            self.label_new.show()
                        if self.list2.isHidden():
                            self.list2.show()
                    else:
                        self.gridLayout.setSpacing(0)
                        self.superGridLayout.setSpacing(0)
                        self.gridLayout.setContentsMargins(0, 0, 0, 0)
                        self.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        self.text.hide()
                        self.label.hide()
                        self.label_new.hide()
                        self.frame1.hide()
                        self.list2.hide()
                        
                    self.list1.hide()
                    self.tab_6.hide()
                    self.goto_epn.hide()
                    self.list6.hide()
                    
                    self.frame.hide()
                    self.dockWidget_3.hide()
                    self.tab_5.show()
                    self.tab_5.setFocus()
                    if not self.tab_2.isHidden():
                        self.tab_2.hide()
                    if (self.player_val == "mplayer" or self.player_val=="mpv"):
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                    MainWindow.showFullScreen()
            else:
                self.gridLayout.setSpacing(5)
                self.superGridLayout.setSpacing(0)
                self.gridLayout.setContentsMargins(5, 5, 5, 5)
                self.superGridLayout.setContentsMargins(5, 5, 5, 5)
                self.list2.show()
                self.btn20.show()
                if self.wget.processId() > 0 or self.video_local_stream:
                    self.progress.show()
                self.frame1.show()
                if self.player_val == "mplayer" or self.player_val=="mpv":
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                MainWindow.showNormal()
                MainWindow.showMaximized()
                if total_till != 0 or self.fullscreen_mode == 1:
                    self.tab_6.show()
                    self.list2.hide()
                    self.goto_epn.hide()
                if self.btn1.currentText().lower() == 'youtube':
                    self.list2.hide()
                    self.goto_epn.hide()
                    self.tab_2.show()
        else:
            if self.detach_fullscreen:
                self.detach_fullscreen = False
                self.tray_widget.right_menu._detach_video()
                self.tab_5.setFocus()
            else:
                if not self.float_window.isHidden():
                    if not self.float_window.isFullScreen():
                        self.float_window.showFullScreen()
                    else:
                        self.float_window.showNormal()
        
    def seek_to_val_abs(self):
        val = self.client_seek_val
        if self.player_val == "mplayer":
            txt1 = '\n osd 1 \n'
            txt = '\n seek {0} 2\n'.format(val)
        else:
            txt1 = '\n set osd-level 1 \n'
            txt = '\n osd-msg-bar seek {0} absolute \n'.format(val)
            print(txt)
        self.mpvplayer_val.write(bytes(txt1, 'utf-8'))
        self.mpvplayer_val.write(bytes(txt, 'utf-8'))
    
    def seek_to_val(self, val):
        if self.player_val == "mplayer":
            txt1 = '\n osd 1 \n'
            txt = '\n seek {0}\n'.format(val)
        else:
            txt1 = '\n set osd-level 1 \n'
            txt = '\n osd-msg-bar seek {0} relative+exact \n'.format(val)
            print(txt)
        self.mpvplayer_val.write(bytes(txt1, 'utf-8'))
        self.mpvplayer_val.write(bytes(txt, 'utf-8'))
        
    def seek_to_vol_val(self, val, action=None):
        msg = None
        if self.player_val == "mplayer":
            txt1 = '\n osd 1 \n'
            txt = '\n volume {0} \n'.format(val)
            self.mpvplayer_val.write(b'')
        else:
            txt1 = '\n set osd-level 1 \n'
            if self.volume_type == 'ao-volume':
                if action:
                    txt = '\n osd-msg-bar set ao-volume {0} \n'.format(val)
                else:
                    txt = '\n osd-msg-bar add ao-volume {0} \n'.format(val)
                msg = '\n print-text ao-volume-print=${ao-volume} \n'
            else:
                if action:
                    txt = '\n osd-msg-bar set volume {0} \n'.format(val)
                else:
                    txt = '\n osd-msg-bar add volume {0} \n'.format(val)
                msg = '\n print-text volume-print=${volume} \n'
        #if action is None:
        #    self.mpvplayer_val.write(bytes(txt1, 'utf-8'))
        self.mpvplayer_val.write(bytes(txt, 'utf-8'))
        if msg and (action is None or action == 'pressed'):
            self.mpvplayer_val.write(bytes(msg, 'utf-8'))
    
    def float_activity(self):
        if not self.new_tray_widget.isHidden() and self.new_tray_widget.remove_toolbar:
            self.new_tray_widget.hide()
            print('--float--activity--')
            
    def set_video_mode(self):
        txt = self.comboBoxMode.currentText()
        txt = txt.lower()
        if txt == 'mode 1':
            self.video_mode_index = 1
        elif txt == 'mode 2':
            self.video_mode_index = 2
        elif txt == 'mode 3':
            self.video_mode_index = 3
        elif txt == 'mode 4':
            self.video_mode_index = 4
        elif txt == 'mode 5':
            self.video_mode_index = 5
        if self.mpvplayer_val.processId() > 0:
            self.mpvplayer_val.kill()
    
    def change_fanart_aspect(self, var):
        dir_name = self.get_current_directory()
        fanart = os.path.join(dir_name, 'fanart.jpg')
        poster = os.path.join(dir_name, 'poster.jpg')
        thumbnail = os.path.join(dir_name, 'thumbnail.jpg')
        summary = ''
        picn = os.path.join(dir_name, 'original-fanart.jpg')
        self.image_fit_option_val = var
        logger.info(picn)
        if not os.path.exists(picn) and os.path.exists(fanart):
            shutil.copy(fanart, picn)
        elif not os.path.exists(picn) and os.path.exists(poster):
            shutil.copy(poster, picn)
        if os.path.exists(picn):
            logger.info(
                "\npicn={0}, fanart={1}, image_fit_option={2}\n".format(
                picn, fanart, self.image_fit_option_val))
            if var == 8:
                self.image_fit_option(picn, fanart, fit_size=6, widget=self.label_new)
            else:
                self.image_fit_option(picn, fanart, fit_size=self.image_fit_option_val)
            set_mainwindow_palette(fanart, theme=self.player_theme)
        
    def webResize(self):
        global screen_width
        if self.btnWebReviews_search.isHidden():
            self.btnWebReviews_search.show()
        else:
            wdt = self.tab_2.width()
            if wdt <= 400:
                self.tab_2.setMaximumWidth(screen_width)
            else:
                self.tab_2.setMaximumWidth(400)
            
    def go_prev_web_page(self):
        if self.web:
            self.web.back()
            
    def go_next_web_page(self):
        if self.web:
            self.web.forward()
            
    def text_save_btn_hide(self):
        self.text_save_btn.hide()
        
    def save_text_edit(self):
        txt = self.text.toPlainText()
        self.text.clear()
        logger.debug(txt)
        if txt.startswith('Air Date:'):
            if self.list2.currentItem():
                row = self.list2.currentRow()
                row_txt = self.epn_arr_list[row]
                picn = self.get_thumbnail_image_path(row, row_txt, only_name=True)
                path, file_name = os.path.split(picn)
                file_name = file_name.replace('.jpg', '.txt', 1)
                file_path = os.path.join(path, file_name)
                logger.debug(file_path)
                write_files(file_path, txt, False)
                self.text.setText(txt)
        else:
            self.copySummary(copy_sum=txt, find_name=True)
        
    def text_editor_changed(self):
        g = self.text.geometry()
        txt = self.text.toPlainText()
        print(g.x(), g.y())
        self.text_save_btn.setGeometry(g.x()+g.width()-30, g.y()-25, 35, 25)
        self.text_save_btn.show()
        self.text_save_btn_timer.start(4000)
    
    def show_hide_filter_toolbar(self):
        if self.view_mode in ['thumbnail', 'thumbnail_light']:
            self.label_search.clear()
            self.label_search.setFocus()
        else:
            print(type(self))
            go_pg = False
            go_epn = False
            if self.list1.isHidden() and self.list2.isHidden():
                pass
            elif not self.list1.isHidden() and self.list2.isHidden():
                if self.frame.isHidden():
                    self.frame.show()
                    #go_pg = True
                elif not self.frame.isHidden():
                    self.frame.hide()
            elif self.list1.isHidden() and not self.list2.isHidden():
                if self.goto_epn.isHidden():
                    self.goto_epn.show()
                elif not self.goto_epn.isHidden():
                    self.goto_epn.hide()
            elif not self.list1.isHidden() and not self.list2.isHidden():
                if self.frame.isHidden() and not self.goto_epn.isHidden():
                    self.goto_epn.hide()
                elif not self.frame.isHidden() and self.goto_epn.isHidden():
                    self.frame.hide()
                elif not self.frame.isHidden() and not self.goto_epn.isHidden():
                    self.frame.hide()
                    self.goto_epn.hide()
                elif self.frame.isHidden() and self.goto_epn.isHidden():
                    self.frame.show()
                    self.goto_epn.show()
                
            if not self.frame.isHidden():
                self.go_page.setFocus()
            elif not self.goto_epn.isHidden():
                self.goto_epn_filter_txt.setFocus()
            
            if self.frame.isHidden() and self.goto_epn.isHidden():
                if not self.list1.isHidden():
                    self.list1.setFocus()
                elif not self.list2.isHidden():
                    self.list2.setFocus()
                    
    def orient_dock(self, initial_start=None):
        if initial_start:
            txt = initial_start
            if txt == 'left':
                self.btn_orient.setText(self.player_buttons['right'])
                self.btn_orient.setToolTip('Orient Dock to Right')
                self.orientation_dock = 'left'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 1, 1, 1)
            else:
                self.btn_orient.setText(self.player_buttons['left'])
                self.btn_orient.setToolTip('Orient Dock to Left')
                self.orientation_dock = 'right'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 5, 2, 1)
                #self.gridLayout.addWidget(self.dockWidget_3, 0, 3, 1, 1)
        else:
            txt = self.btn_orient.text()
            if txt == self.player_buttons['right']:
                self.btn_orient.setText(self.player_buttons['left'])
                self.btn_orient.setToolTip('Orient Dock to Left')
                self.orientation_dock = 'right'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 5, 2, 1)
                #self.gridLayout.addWidget(self.dockWidget_3, 0, 3, 1, 1)
            else:
                self.player_buttons['left']
                self.btn_orient.setText(self.player_buttons['right'])
                self.btn_orient.setToolTip('Orient Dock to Right')
                self.orientation_dock = 'left'
                self.superGridLayout.addWidget(self.dockWidget_3, 0, 1, 1, 1)
            
    def close_frame_btn(self):
        txt = self.btn4.text()
        if txt == '--':
            self.btn4.setText('+')
            #self.btn4.setToolTip('Auto Hide Off')
            self.auto_hide_dock = False
        else:
            self.btn4.setText('--')
            #self.btn4.setToolTip('Auto Hide On')
            self.auto_hide_dock = True
            self.dockWidget_3.hide()
            
    def generate_thumbnail_method(self, picn, interval, path,
                                  width_allowed=None, from_client=None):
        path = path.replace('"', '')
        inter = str(interval)
        
        new_tmp = '"'+TMPDIR+'"'
        if not self.mpv_thumbnail_lock:
            if OSNAME == 'posix':
                if width_allowed:
                    wd = str(width_allowed)
                else:
                    wd = str(self.width_allowed)
                if from_client:
                    self.mpv_thumbnail_lock = True
                if path.endswith('.mp3') or path.endswith('.flac'):
                    try:
                        f = mutagen.File(path)
                        artwork = f.tags['APIC:'].data
                        with open(picn, 'wb') as img:
                            img.write(artwork) 
                    except Exception as e:
                        try:
                            f = open(picn, 'w').close()
                            print(e, '--9048--')
                        except Exception as e:
                            print(e, '--9065--')
                            
                else:
                    subprocess.call(["ffmpegthumbnailer", "-i", path, "-o", picn, 
                                "-t", str(inter), '-q', '10', '-s', wd])
                logger.info("{0}:{1}".format(path, picn))
                if from_client:
                    self.mpv_thumbnail_lock = False
                if os.path.exists(picn) and os.stat(picn).st_size and not from_client:
                    #self.image_fit_option(picn, picn, fit_size=6, widget_size=(480, 360))
                    self.create_new_image_pixel(picn, 128)
                    self.create_new_image_pixel(picn, 480)
                    label_name = 'label.'+os.path.basename(picn)
                    path_thumb, new_title = os.path.split(picn)
                    new_picn = os.path.join(path_thumb, label_name)
                    if not os.path.exists(new_picn):
                        self.image_fit_option(picn, new_picn, fit_size=6, widget=self.label)
            else:
                if path.endswith('.mp3') or path.endswith('.flac'):
                    try:
                        f = mutagen.File(path)
                        artwork = f.tags['APIC:'].data
                        with open(picn, 'wb') as img:
                            img.write(artwork) 
                    except Exception as e:
                        try:
                            f = open(picn, 'w').close()
                            print(e, '--9048--')
                        except Exception as e:
                            print(e, '--9065--')
                    logger.info("{0}:{1}".format(path, picn))
                    if os.path.exists(picn) and os.stat(picn).st_size and not from_client:
                        self.image_fit_option(picn, picn, fit_size=6, widget=self.label)
                else:
                    if inter.endswith('s'):
                        inter = inter[:-1]
                    self.mpv_thumbnail_lock = True
                    if 'youtube.com' in path:
                        new_tmp = new_tmp.replace('"', '')
                        subprocess.call(["mpv", "--vo=image", "--no-sub", "--ytdl=yes", "--quiet", 
                                        "-aid=no", "-sid=no", "--vo-image-outdir="+new_tmp, 
                                        "--start="+str(inter)+"%", "--frames=1"
                                        , path])
                    else:
                        if self.player_val == 'mpv':
                            new_tmp = new_tmp.replace('"', '')
                            subprocess.call(["mpv", "--vo=image", "--no-sub", "--ytdl=no", 
                            "--quiet", "-aid=no", "-sid=no", "--vo-image-outdir="+new_tmp, 
                            "--start="+str(inter)+"%", "--frames=1", path], shell=True)
                        elif self.player_val == 'mplayer':
                            subprocess.call(["mplayer", "-nosub", "-nolirc", "-nosound", 
                            '-vo', "jpeg:quality=100:outdir="+new_tmp, "-ss", str(inter), 
                            "-endpos", "1", "-frames", "1", "-vf", "scale=320:180", 
                            path], shell=True)
                        
                    picn_path = os.path.join(TMPDIR, '00000001.jpg')
                    if os.path.exists(picn_path):
                        shutil.copy(picn_path, picn)
                        os.remove(picn_path)
                        if os.path.exists(picn) and os.stat(picn).st_size and not from_client:
                            #self.image_fit_option(picn, picn, fit_size=6, widget=self.label)
                            self.create_new_image_pixel(picn, 128)
                            self.create_new_image_pixel(picn, 480)
                    self.mpv_thumbnail_lock = False
    
    def create_new_image_pixel(self, art_url, pixel):
        art_url_name = str(pixel)+'px.'+os.path.basename(art_url)
        path_thumb, new_title = os.path.split(art_url)
        abs_path_thumb = os.path.join(path_thumb, art_url_name)
        #logger.debug(abs_path_thumb)
        try:
            if not os.path.exists(abs_path_thumb) and os.path.exists(art_url):
                basewidth = pixel
                img = Image.open(str(art_url))
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                try:
                    img.save(str(abs_path_thumb))
                except Exception as err:
                    print(err)
                    self.handle_png_to_jpg(abs_path_thumb, img)
            elif not os.path.exists(art_url):
                art_url_name = str(pixel)+'px.'+os.path.basename(self.default_background)
                path_thumb, new_title = os.path.split(self.default_background)
                abs_path_thumb = os.path.join(path_thumb, art_url_name)

                if not os.path.exists(abs_path_thumb) and os.path.exists(self.default_background):
                    basewidth = pixel
                    img = Image.open(str(self.default_background))
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                    try:
                        img.save(str(abs_path_thumb))
                    except Exception as err:
                        print(err)
                        self.handle_png_to_jpg(abs_path_thumb, img)
        except:
            art_url_name = str(pixel)+'px.'+os.path.basename(self.default_background)
            path_thumb, new_title = os.path.split(self.default_background)
            abs_path_thumb = os.path.join(path_thumb, art_url_name)
            if not os.path.exists(abs_path_thumb) and os.path.exists(self.default_background):
                basewidth = pixel
                img = Image.open(str(self.default_background))
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                try:
                    img.save(str(abs_path_thumb))
                except Exception as err:
                    print(err)
                    self.handle_png_to_jpg(abs_path_thumb, img)
            
        return abs_path_thumb
        
    def list1_double_clicked(self):
        global show_hide_titlelist, show_hide_playlist
        self.listfound()
        if site == "Music" and not self.list2.isHidden():
            self.list2.setFocus()
            self.list2.setCurrentRow(0)
            self.cur_row = 0
            self.list1.show()
            self.list1.setFocus()
        else:
            if self.list2.isHidden():
                self.list1.hide()
                self.frame.hide()
                self.list2.show()
                self.list2.setFocus()
                show_hide_titlelist = 0
                show_hide_playlist = 1
        self.update_list2()
        
    def hide_torrent_info(self):
        self.torrent_frame.hide()
        self.progress.hide()
        
    def stop_torrent(self, from_client=None):
        global site
        try:
            stop_now = False
            new_video_local_stream = False
            if from_client:
                if self.started_from_external_client:
                    stop_now = True
                    new_video_local_stream = True
            else:
                stop_now = True
            if stop_now:
                if self.video_local_stream or new_video_local_stream:
                    if self.do_get_thread.isRunning():
                        logger.debug('----------stream-----pausing-----')
                        t_list = self.stream_session.get_torrents()
                        for i in t_list:
                            logger.info('--removing--{0}'.format(i.name()))
                            self.stream_session.remove_torrent(i)
                        self.stream_session.pause()
                    elif self.stream_session:
                        if not self.stream_session.is_paused():
                            self.stream_session.pause()
                    txt = 'Torrent Stopped'
                    send_notification(txt)
                    self.torrent_frame.hide()
                    self.progress.hide()
                elif self.wget.processId() > 0:
                    ui.queue_stop = True
                    self.wget.kill()
                    msg = 'Stopping download'
                    send_notification(msg)
                    self.torrent_frame.hide()
                    self.progress.hide()
                    if self.queue_item:
                        self.queue_url_list.insert(0, self.queue_item)
                        if isinstance(self.queue_item, tuple):
                            txt = self.queue_item[-1]
                        else:
                            txt = self.queue_item
                        if txt.startswith('#'):
                            txt = txt.replace('#', '', 1)
                        self.list6.insertItem(0, txt)
                elif self.queue_url_list:
                    queue_item = self.queue_url_list[0]
                    if isinstance(queue_item, tuple):
                        self.queue_item = queue_item
                        item = self.list6.item(0)
                        if item:
                            del self.queue_url_list[0]
                            self.list6.takeItem(0)
                            del item
                            self.start_offline_mode(0, self.queue_item)
                        logger.debug('queue:{0}::list6:{1}'.format(len(self.queue_url_list, self.list6.count())))
        except Exception as e:
            logger.error(e)
    
    def stop_torrent_forcefully(self, from_client=None):
        global site
        try:
            if self.do_get_thread.isRunning():
                print('----------stream-----pausing-----')
                t_list = self.stream_session.get_torrents()
                for i in t_list:
                    logger.info('--removing--{0}'.format(i.name()))
                    self.stream_session.remove_torrent(i)
                self.stream_session.pause()
                #self.stream_session = None
            elif self.stream_session:
                if not self.stream_session.is_paused():
                    self.stream_session.pause()
                    #self.stream_session = None
            txt = 'Torrent Stopped'
            send_notification(txt)
            self.torrent_frame.hide()
            self.progress.hide()
        except Exception as e:
            print(e, '--9368--')
    
    def set_new_download_speed(self):
        txt = self.label_down_speed.text()
        try:
            self.torrent_download_limit = int(txt) * 1024
        except:
            txt_notify = 'Please enter valid speed in KB'
            send_notification(txt_notify)
        self.label_down_speed.clear()
        self.torrent_handle.set_download_limit(self.torrent_download_limit)
        #print(type(self.torrent_handle))
        down = '\u2193 SET TO: ' +str(int(self.torrent_download_limit/1024))+'K'
        self.label_down_speed.setPlaceholderText(down)
        
    def set_new_upload_speed(self):
        txt = self.label_up_speed.text()
        try:
            self.torrent_upload_limit = int(txt) * 1024
        except:
            txt_notify = 'Please enter valid speed in KB'
            send_notification(txt_notify)
        self.label_up_speed.clear()
        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
        #print(type(self.torrent_handle))
        up = '\u2191 SET TO: ' +str(int(self.torrent_upload_limit/1024))+'K'
        self.label_up_speed.setPlaceholderText(up)
        
    def quitApp(self):
        app.quit()
        
    def queueList_return_pressed(self, r):
        queue_item = self.queue_url_list[r]
        del self.queue_url_list[r]
        item = self.list6.item(r)
        queue_txt = item.text()
        self.list6.takeItem(r)
        del item
        if isinstance(queue_item, tuple):
            self.queue_item = queue_item
            self.start_offline_mode(0, self.queue_item)
        else:
            self.list6.insertItem(0, queue_txt)
            self.queue_url_list.insert(0, queue_item)
            self.getQueueInList()
        logger.debug('queue:{0}::list6:{1}'.format(len(self.queue_url_list), self.list6.count()))
        
    def queue_manage_list(self):
        if self.list6.isHidden():
            self.list6.show()
            self.list6.setFocus()
        else:
            self.list6.hide()
            
    def goto_epn_filter_on(self):
        if self.goto_epn_filter_txt.isHidden():
            self.goto_epn_filter_txt.show()
            self.goto_epn_filter_txt.setFocus()
        else:
            self.goto_epn_filter_txt.clear()
            
    def player_started_playing(self):
        global player_start_now
        player_start_now = 1
        print("started")
        
    def player_opt_toolbar_dock(self):
        if self.dockWidget_3.isHidden():
            self.dockWidget_3.show()
        else:
            self.dockWidget_3.hide()
            
    def hide_btn_list1_pressed(self):
        if self.list1.isHidden():
            self.list1.show()
            self.hide_btn_list1.setText("Hide")
        else:
            self.list1.hide()
            self.hide_btn_list1.setText("Show")
    
    def set_sub_audio(self, aid, sid, seek_time=None, rem_quit=None, vol=None):
        global site
        if seek_time is None:
            seek_time = 0
        if rem_quit is None:
            rem_quit = 0
        if not aid:
            aid = 'auto'
        if not sid:
            sid = 'auto'
        if self.player_val == 'mpv':
            txt_str = '\n set aid {0}\n'.format(aid)
            self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
            txt_str = '\n set sid {0}\n'.format(sid)
            self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
            if (site.lower() == 'video' and opt.lower() == 'history') or rem_quit:
                if seek_time > 0:
                    txt_str = '\n osd-msg-bar seek {0} relative+exact \n'.format(seek_time-2)
                    self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
        else:
            if aid == 'auto':
                aid = '0'
            if sid == 'auto':
                sid = '0'
            txt_str = '\n set_property switch_audio {0}\n'.format(aid)
            self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
            txt_str = '\n set_property sub {0}\n'.format(sid)
            self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
            if (site.lower() == 'video' and opt.lower() == 'history') or rem_quit:
                if seek_time > 0:
                    txt_str = '\n seek {0} \n'.format(seek_time-10)
                    self.mpvplayer_val.write(bytes(txt_str, 'utf-8'))
                    
    def set_sub_audio_text(self, val, value=None):
        if val == 'aid':
            self.mpvplayer_val.write(b'\n print-text "AUDIO_ID=${aid}" \n')
        elif val == 'sid':
            self.mpvplayer_val.write(b'\n print-text "SUB_ID=${sid}" \n')
        elif val == 'vol':
            if value is not None:
                if self.volume_type == 'ao-volume':
                    txt = '\n set ao-volume {0} \n'.format(value)
                else:
                    txt = '\n set volume {0} \n'.format(value)
                logger.debug(txt)
                txt = bytes(txt, 'utf-8')
                self.mpvplayer_val.write(txt)
        elif val == 'asp':
            if value is not None:
                txt = '\n set video-aspect "{0}" \n'.format(value)
                logger.debug(txt)
                txt = bytes(txt, 'utf-8')
                self.mpvplayer_val.write(txt)
        
                
    def subMplayer(self):
        global audio_id, sub_id, site
        atxt = self.audio_track.text()
        subtxt = self.subtitle_track.text()
        if self.final_playing_url in self.history_dict_obj:
            seek_time, cur_time, sub_id, audio_id, rem_quit, vol, asp = self.history_dict_obj.get(self.final_playing_url)
            aid = audio_id
            sid = sub_id
            self.video_parameters = [
                self.final_playing_url ,seek_time, cur_time, sub_id,
                audio_id, rem_quit, vol, asp
                ]
        else:
            rem_quit = 0
            seek_time = 0
            aid = 'auto'
            sid = 'auto'
            vol = 'auto'
            asp = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
        if atxt != 'A/V' and aid == 'auto':
            aidr = re.search('[0-9]+', atxt)
            if aidr:
                aid = aidr.group()
        if subtxt != 'SUB' and sid == 'auto':
            sidr = re.search('[0-9]+', subtxt)
            if sidr:
                sid = sidr.group()
            elif 'no' in subtxt:
                sid = 'no'
                sub_id = 'no'
            elif 'auto' in subtxt:
                sid = 'auto'
                sub_id = 'auto'
        logger.debug('\nsid={}::aid={}\n'.format(sid, aid))
        if site != 'Music' or rem_quit:
            if vol != 'auto' and self.restore_volume:
                QtCore.QTimer.singleShot(100, partial(self.set_sub_audio_text, 'vol', value=vol))
            aspect = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
            if self.restore_aspect:
                QtCore.QTimer.singleShot(500, partial(self.set_sub_audio_text, 'asp', value=asp))
            self.set_sub_audio(aid, sid, seek_time, rem_quit)
            QtCore.QTimer.singleShot(1000, partial(self.set_sub_audio_text, 'aid'))
            QtCore.QTimer.singleShot(1500, partial(self.set_sub_audio_text, 'sid'))
            
            
    def osd_hide(self):
        pass
        """
        if self.player_val == 'mplayer':
            self.mpvplayer_val.write(b'\n osd 0 \n')
        else:
            self.mpvplayer_val.write(b'\n set osd-level 0 \n')
        """
        
    def mirrorChange(self):
        global mirrorNo
        txt = str(self.mirror_change.text())
        if txt == "Mirror":
            mirrorNo = 1
            self.mirror_change.setText("1")
        else:
            mirrorNo = int(txt)
            mirrorNo = mirrorNo + 1
            if mirrorNo == 10:
                self.mirror_change.setText("Mirror")
                mirrorNo = 1
            else:
                self.mirror_change.setText(str(mirrorNo))
        
    def toggleAudio(self):
        global audio_id
        if self.mpvplayer_val.processId() > 0:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer_val.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                
                self.mpvplayer_val.write(b'\n switch_audio \n')
                self.mpvplayer_val.write(b'\n get_property switch_audio \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer_val.write(b'\n cycle audio \n')
                self.mpvplayer_val.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
                self.mpvplayer_val.write(b'\n show-text "${aid}" \n')
        self.audio_track.setText("A:"+str(audio_id))
            
    def load_external_sub(self):
        global sub_id, current_playing_file_path
        external_sub = False
        sub_arr = []
        new_name = self.epn_name_in_list.replace('/', '-')
        if new_name.startswith(self.check_symbol):
            new_name = new_name[1:]
        ext_arr = self.video_type_arr
        if new_name.startswith('.'):
            new_name = new_name[1:]
            new_name = new_name.strip()
        if '.' in new_name:
            ext = new_name.rsplit('.', 1)[1]
            ext_n = ext.strip()
            if ext_n in ext_arr:
                new_name = new_name.rsplit('.', 1)[0]
        new_name_original = new_name
        
        if new_name.endswith('YouTube'):
            new_name = ''.join(new_name.rsplit('YouTube', 1))
            new_name = new_name.strip()
            if new_name.endswith('-'):
                new_name = new_name[:-1]
                new_name = new_name.strip()
                
        new_path = current_playing_file_path.replace('"', '')
        if os.path.exists(new_path):
            sub_name_bytes = bytes(new_path, 'utf-8')
            h = hashlib.sha256(sub_name_bytes)
            sub_name = h.hexdigest()
            sub_path = os.path.join(self.yt_sub_folder, sub_name+'.vtt')
            if os.path.exists(sub_path):
                sub_arr.append(sub_path)
                external_sub = True
                logger.info(sub_path)
        lang_ext = ['.en', '.es', '.jp', '.fr']
        sub_ext = ['.vtt', '.srt', '.ass']
        for i in lang_ext:
            for j in sub_ext:
                k1 = new_name_original+i+j
                k2 = new_name+i+j
                sub_name_1 = os.path.join(self.yt_sub_folder, k1)
                sub_name_2 = os.path.join(self.yt_sub_folder, k2)
                #print(sub_name)
                if os.path.exists(sub_name_1):
                    sub_arr.append(sub_name_1)
                    external_sub = True
                    logger.info(sub_name_1)
                if os.path.exists(sub_name_2):
                    sub_arr.append(sub_name_2)
                    external_sub = True
                    logger.info(sub_name_2)
        logger.info('--new--name--{0}'.format(new_name))
        
            
        if self.mpvplayer_val.processId() > 0 and sub_arr:
            sub_arr.reverse()
            for title_sub in sub_arr:
                if self.player_val == "mplayer":
                    if os.path.exists(title_sub):
                        txt = '\nsub_load '+'"'+title_sub+'"\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer_val.write(txt_b)
                else:
                    if os.path.exists(title_sub):
                        txt = '\nsub_add '+'"'+title_sub+'" select\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer_val.write(txt_b)
                        
    def toggleSubtitle(self):
        global sub_id
        if self.mpvplayer_val.processId() > 0:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer_val.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer_val.write(b'\n sub_select \n')
                self.mpvplayer_val.write(b'\n get_property sub \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer_val.write(b'\n cycle sub \n')
                self.mpvplayer_val.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
                self.mpvplayer_val.write(b'\n show-text "${sid}" \n')
        self.subtitle_track.setText('Sub:'+str(sub_id))
    
    def mark_epn_thumbnail_label_new(self, txt, index):
        if txt.startswith('#'):
            txt = txt.replace('#', self.check_symbol, 1)
        p1 = "self.label_epn_{0}".format(index)
        label_number = eval(p1)
        label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
        try:
            p1 = "self.label_epn_{0}.setText('{1}')".format(index, txt)
            exec(p1)
        except Exception as e:
            logger.debug('{0}::first try'.format(e))
            try:
                p1 = 'self.label_epn_{0}.setText("{1}")'.format(index, txt)
                exec(p1)
            except Exception as e:
                logger.debug('{0}::Second try'.format(e))
        p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(index)
        exec(p1)
    
    def mark_epn_thumbnail_label(self, num, old_num=None):
        if self.idw and self.idw != str(int(self.tab_5.winId())) and self.idw != str(int(self.label.winId())):
            try:
                index = num + self.list2.count()
                txt = self.list2.item(num).text()
                self.mark_epn_thumbnail_label_new(txt, index)
                if old_num:
                    txt = ui.thumbnail_label_number[1]
                    index = ui.thumbnail_label_number[0] + self.list2.count()
                    self.mark_epn_thumbnail_label_new(txt, index)
            except Exception as e:
                logger.error(e)
    
    def update_thumbnail_position(self, context=None):
        r = self.list2.currentRow()
        if r < 0:
            r = 0
        #QtWidgets.QApplication.processEvents()
        try:
            p1="self.label_epn_"+str(r)+".y()"
            yy=eval(p1)
        except Exception as err:
            print(err)
            yy = 0
        self.scrollArea1.verticalScrollBar().setValue(yy-5)
        #QtWidgets.QApplication.processEvents()
        self.frame1.show()
        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        self.superGridLayout.setContentsMargins(5, 5, 5, 5)
        self.gridLayout1.setContentsMargins(5, 5, 5, 5)
        self.gridLayout2.setContentsMargins(5, 5, 5, 5)
        #ui.horizontalLayout10.setContentsMargins(0, 0, 0, 0)
        #ui.horizontalLayout10.setSpacing(0)
        self.gridLayout.setSpacing(5)
        self.gridLayout1.setSpacing(5)
        self.gridLayout2.setSpacing(5)
        self.superGridLayout.setSpacing(5)
        self.tab_6.show()
        QtWidgets.QApplication.processEvents()
        try:
            p1="self.label_epn_"+str(r)+".setFocus()"
            exec(p1)
        except Exception as err:
            print(err)
        if not context:
            logger.debug('quit::{0}::'.format(self.quit_really))
            if self.quit_really == 'no':
                self.mark_epn_thumbnail_label(r)
            else:
                self.mark_epn_thumbnail_label(r, old_num=True)
        
    def thumbnail_window_present_mode(self, mode=None):
        global iconv_r, MainWindow, iconv_r_indicator
        
        if MainWindow.isFullScreen() and mode != 5:
            if self.list2.count() == 0:
                return 0
            w = float((self.tab_6.width()-60)/iconv_r)
            h = int(w/self.image_aspect_allowed)
            width=str(int(w))
            height=str(int(h))
            r = self.current_thumbnail_position[0]
            c = self.current_thumbnail_position[1]
            print(r, c, '--thumbnail--7323--')
            thumbnail_index = self.thumbnail_label_number[0]
            p6 = "self.gridLayout2.addWidget(self.label_epn_"+str(thumbnail_index)+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
            exec(p6)
            #QtWidgets.QApplication.processEvents()
            p2 = "self.label_epn_"+str(thumbnail_index)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
            p3 = "self.label_epn_"+str(thumbnail_index)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
            exec(p2)
            exec(p3)

            self.gridLayout.setSpacing(5)
            #self.gridLayout.setContentsMargins(10, 10, 10, 10)
            self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            if self.wget.processId() > 0:
                self.goto_epn.hide()
                self.progress.show()
            self.frame2.show()
            if self.tab_6.isHidden() and not self.force_fs:
                MainWindow.showNormal()
                MainWindow.showMaximized()
            self.frame1.show()
            self.gridLayout.setContentsMargins(5, 5, 5, 5)
            self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            self.gridLayout1.setContentsMargins(5, 5, 5, 5)
            self.gridLayout2.setContentsMargins(5, 5, 5, 5)
            #ui.horizontalLayout10.setContentsMargins(0, 0, 0, 0)
            #ui.horizontalLayout10.setSpacing(0)
            self.gridLayout.setSpacing(5)
            self.gridLayout1.setSpacing(5)
            self.gridLayout2.setSpacing(5)
            self.superGridLayout.setSpacing(5)
            self.tab_6.show()
        else:
            self.thumbnail_label_update_epn()
        QtCore.QTimer.singleShot(1000, partial(self.update_thumbnail_position))
            
    def playerStop(self, msg=None, restart=None):
        global thumbnail_indicator, total_till, browse_cnt
        global iconv_r_indicator, iconv_r, show_hide_cover
        global show_hide_playlist, show_hide_titlelist
        global new_tray_widget, sub_id, audio_id
        change_spacing = False
        if self.mpvplayer_val.processId() > 0 or msg:
            logger.warn(self.progress_counter)
            if self.player_val == 'mpv':
                counter = self.progress_counter
            else:
                counter = (self.progress_counter/1000)
            if msg == 'remember quit':
                rem_quit = 1
            else:
                rem_quit = 0
            if site != 'Music' or rem_quit:
                param_avail = False
                if self.video_parameters:
                    if self.final_playing_url == self.video_parameters[0]:
                        asp = self.video_parameters[-1]
                        vol = self.video_parameters[-2]
                        param_avail = True
                if not param_avail:        
                    asp = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
                    vol = self.player_volume
                self.history_dict_obj.update(
                        {
                        self.final_playing_url:[
                            counter, time.time(), sub_id,
                            audio_id, rem_quit, vol, asp
                            ]
                        }
                    )
                logger.debug(self.history_dict_obj[self.final_playing_url])
                logger.debug(self.video_parameters)
            if restart:
                self.quit_really = 'no'
            else:
                self.quit_really = "yes"
            if msg:
                if msg.lower() == 'already quit':
                    logger.debug(msg)
                else:
                    self.mpvplayer_val.kill()
            else:
                self.mpvplayer_val.kill()
            self.player_play_pause.setText(self.player_buttons['play'])
            if self.tab_6.isHidden() and (str(self.idw) == str(int(self.tab_5.winId()))):
                change_spacing = True
                if not self.float_window.isHidden():
                    if self.float_window.isFullScreen():
                        self.float_window.showNormal()
                    else:
                        pass
                else:
                    self.tab_5.showNormal()
                    self.tab_5.hide()
                    if self.tab_2.isHidden():
                        if self.fullscreen_mode == 0:
                            if show_hide_titlelist == 1:
                                self.list1.show()
                            if show_hide_cover == 1:
                                self.label.show()
                                if self.layout_mode != 'Music':
                                    self.label_new.show()
                                self.text.show()
                            if show_hide_titlelist == 1:
                                self.list2.show()
                            self.list2.setFocus()
                        elif self.fullscreen_mode == 1:
                            self.tab_6.show()
                            self.frame2.show()
                            self.frame1.show()
                            self.labelFrame2.show()
                            if self.video_mode_index != 1:
                                self.gridLayout.setSpacing(5)
                                self.tab_6.setMaximumSize(16777215, 16777215)
                                self.tab_6_size_indicator.append(screen_width-20)
                                thumbnail_indicator[:]=[]
                                if iconv_r_indicator:
                                    iconv_r = iconv_r_indicator[0]
                                else:
                                    iconv_r = 6
                                logger.debug(iconv_r_indicator)
                                self.thumbnail_label_update_epn()
                            QtCore.QTimer.singleShot(1000, partial(self.update_thumbnail_position))
                    else:
                        pass
                    self.gridLayout.setContentsMargins(5, 5, 5, 5)
                    self.gridLayout.setSpacing(5)
                    self.frame1.show()
                    self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            else:
                if not self.float_window.isHidden():
                    if self.float_window.isFullScreen():
                        self.float_window.showNormal()
                    else:
                        pass
                else:
                    if ((str(self.idw) != str(int(self.tab_5.winId()))) 
                            and (str(self.idw) != str(int(self.label.winId())))
                            and (str(self.idw) != str(int(self.label_new.winId())))):
                        if iconv_r_indicator:
                            iconv_r = iconv_r_indicator[0]
                        #self.scrollArea1.verticalScrollBar().setValue(0)
                        if self.video_mode_index == 5:
                            self.thumbnail_window_present_mode(mode=5)
                        else:
                            self.thumbnail_window_present_mode()
                    elif (str(self.idw) == str(int(self.tab_5.winId()))):
                        self.tab_5.hide()
                        self.scrollArea1.hide()
                        QtWidgets.QApplication.processEvents()
                        self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)
                        self.gridLayout.setSpacing(5)
                        self.tab_6.setMaximumSize(16777215, 16777215)
                        
                        self.tab_6_size_indicator.append(screen_width-20)
                        thumbnail_indicator[:]=[]
                        if iconv_r_indicator:
                            iconv_r = iconv_r_indicator[0]
                        else:
                            iconv_r = 6
                        logger.debug(iconv_r_indicator)
                        self.frame2.show()
                        self.frame1.show()
                        self.labelFrame2.show()
                        self.thumbnail_label_update_epn()
                        QtCore.QTimer.singleShot(1000, partial(self.update_thumbnail_position))
                    elif str(self.idw) in [str(int(self.label.winId())), str(int(self.label_new.winId()))]:
                        if self.player_theme == 'default':
                            self.label_new.setMinimumHeight(0)
                        if self.video_mode_index == 7:
                            wd = self.label_new.maximumWidth()
                            ht = self.label_new.maximumHeight()
                            fs = False
                            logger.debug('{0}, {1}::original {2}, {3}'.format(wd, ht, screen_width, screen_height))
                            if wd == screen_width and ht == screen_height:
                                fs = True
                            if fs:
                                self.gridLayout.setSpacing(5)
                                self.superGridLayout.setSpacing(0)
                                self.gridLayout.setContentsMargins(5, 5, 5, 5)
                                self.superGridLayout.setContentsMargins(5, 5, 5, 5)
                                self.vertical_layout_new.insertWidget(0, self.label_new)
                                if not self.force_fs:
                                    MainWindow.showNormal()
                                    MainWindow.showMaximized()
                                wd, ht = self.label_new.prev_dim_label
                                self.label_new.setMaximumSize(QtCore.QSize(wd, ht))
                                self.HideEveryThing(mode='fs')
                                self.label_new.setFocus()
                        
            if (((MainWindow.isFullScreen() and self.tab_6.isHidden())
                    or self.fullscreen_mode == 1) and not self.force_fs):
                MainWindow.showNormal()
                MainWindow.showMaximized()
                MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            QtCore.QTimer.singleShot(3000, partial(self.show_cursor_now))
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat((''))
        self.idw = str(int(self.tab_5.winId()))
        if self.video_mode_index in [6, 7]:
            self.set_video_mode()
        if self.orientation_dock == 'right':
            self.superGridLayout.addWidget(self.dockWidget_3, 0, 5, 2, 1)
        MainWindow.setWindowTitle('Kawaii-Player')
        if not self.float_window.isHidden():
            self.float_window.setWindowTitle('Kawaii-Player')
        self.fullscreen_video = False
        #if change_spacing:
        #    self.gridLayout.setSpacing(5)
        #    self.superGridLayout.setSpacing(5)
        #    self.gridLayout.setContentsMargins(5, 5, 5, 5)
        #    self.superGridLayout.setContentsMargins(5, 5, 5, 5)
            
    def show_cursor_now(self):
        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    
    def shufflePlaylist(self):
        global site
        if (site == "Local" or site =="Video" or site == "Music" 
                or site == "PlayLists" or self.epn_arr_list):
            if self.epn_arr_list:
                if '	' in self.epn_arr_list[0]:
                    print("++++++++++++++++")
                    self.epn_arr_list = random.sample(self.epn_arr_list, len(self.epn_arr_list))
                    self.update_list2()
            
    def playerPlaylist1(self, val):
        if val == "Shuffle":
            self.shuffleList()
        else:
            self.sortList()
            
    def set_playerLoopFile(self):
        global tray, new_tray_widget
        if self.mpvplayer_val.processId() > 0:
            if self.player_val == 'mpv':
                self.mpvplayer_val.write(b'\n set loop-file inf \n')
            else:
                self.mpvplayer_val.write(b'\n set_property loop 0 \n')
                
    def playerLoopFile(self, loop_widget):
        global tray, new_tray_widget
        txt = loop_widget.text()
        #txt = self.player_loop_file.text()
        
        if txt == self.player_buttons['unlock']:
            self.player_setLoop_var = True
            self.player_loop_file.setText(self.player_buttons['lock'])
            new_tray_widget.lock.setText(self.player_buttons['lock'])
            self.quit_really = 'no'
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file inf \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop 0 \n')
        else:
            self.player_setLoop_var = False
            self.player_loop_file.setText(self.player_buttons['unlock'])
            new_tray_widget.lock.setText(self.player_buttons['unlock'])
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file no \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop -1 \n')
                
    def playerPlayPause(self):
        global cur_label_num
        
        txt = self.player_play_pause.text() 
        if txt == self.player_buttons['play']:
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == "mpv":
                    txt_osd = '\n set osd-level 1 \n'
                    #self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                    self.mpvplayer_val.write(b'\n set pause no \n')
                    self.player_play_pause.setText(self.player_buttons['pause'])
                else:
                    self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                if self.list2.currentItem():
                    self.cur_row = self.list2.currentRow()
                    if not self.idw or self.idw == str(int(self.tab_5.winId())):
                        self.epnfound()
                    elif self.idw == str(int(self.label.winId())):
                        pass
                    else:
                        p1 = "self.label_epn_{0}.winId()".format(str(self.thumbnail_label_number[0]))
                        id_w = eval(p1)
                        self.idw = str(int(id_w))
                        finalUrl = self.epn_return(self.cur_row)
                        self.play_file_now(finalUrl, win_id=self.idw)
        elif txt == self.player_buttons['pause']:
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == "mpv":
                    txt_osd = '\n set osd-level 3 \n'
                    #self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                    self.mpvplayer_val.write(b'\n set pause yes \n')
                    self.player_play_pause.setText(self.player_buttons['play'])
                else:
                    self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                if self.list2.currentItem():
                    self.cur_row = self.list2.currentRow()
                    self.epnfound()
    
    def player_force_play(self):
        global cur_label_num
        if self.mpvplayer_val.processId() > 0:
            if self.player_val == "mpv":
                txt_osd = '\n set osd-level 1 \n'
                #self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                self.mpvplayer_val.write(b'\n set pause no \n')
                self.player_play_pause.setText(self.player_buttons['pause'])
            else:
                self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
            
    def player_force_pause(self):
        global cur_label_num
        if self.player_val == "mpv":
            txt_osd = '\n set osd-level 3 \n'
            #self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
            self.mpvplayer_val.write(b'\n set pause yes \n')
            self.player_play_pause.setText(self.player_buttons['play'])
        else:
            self.mpvplayer_val.write(b'\n pausing_toggle osd_show_progression \n')
    
    def player_play_pause_status(self, status=None):
        txt = self.player_play_pause.text() 
        if txt == self.player_buttons['play'] and status == 'play':
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == "mpv":
                    self.player_play_pause.setText(self.player_buttons['pause'])
                    if (MainWindow.isFullScreen() and site != "Music" and self.tab_6.isHidden()
                            and self.list2.isHidden() and self.tab_2.isHidden()):
                        self.frame1.hide()
        elif txt == self.player_buttons['pause'] and status == 'pause':
            if self.mpvplayer_val.processId() > 0:
                if self.player_val == "mpv":
                    self.player_play_pause.setText(self.player_buttons['play'])
                    if (MainWindow.isFullScreen() and site != "Music" and self.tab_6.isHidden()
                            and self.list2.isHidden() and self.tab_2.isHidden()):
                        self.frame1.show()
        
    def playerPlaylist(self, val):
        global playlist_show, site, thumbnail_indicator
        global show_hide_cover, show_hide_playlist, show_hide_titlelist
        global show_hide_player, httpd, cur_label_num
        
        self.player_menu_option = [
            'Show/Hide Video', 'Show/Hide Cover And Summary', 
            'Lock Playlist', 'Shuffle', 'Stop After Current File (Ctrl+Q)', 
            'Continue(default Mode)', 'Set Media Server User/PassWord', 
            'Start Media Server', 'Broadcast Server', 'Turn ON Remote Control',
            'Set Current Background As Default', 'Preferences (Ctrl+P)'
            ]
        
        print(val)
        if val == "Show/Hide Cover And Summary":
            v = str(self.action_player_menu[1].text())
            if self.text.isHidden() and self.label.isHidden():
                self.text.show()
                self.label.show()
                self.label_new.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            elif self.text.isHidden() and not self.label.isHidden():
                self.text.show()
                self.label.show()
                self.label_new.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            elif not self.text.isHidden() and self.label.isHidden():
                self.text.show()
                self.label.show()
                self.label_new.show()
                show_hide_cover = 1
                self.tab_5.hide()
                show_hide_player = 0
            else:
                self.text.hide()
                self.label.hide()
                self.label_new.hide()
                show_hide_cover = 0
                self.tab_5.show()
                show_hide_player = 1
        elif val == "Show/Hide Playlist":
            if not self.list2.isHidden():
                if self.fullscreen_video:
                    self.gridLayout.setSpacing(0)
                    self.superGridLayout.setSpacing(0)
                ht = self.list2.height()
                self.list2.hide()
                self.goto_epn.hide()
                show_hide_playlist = 0
                width = self.label_new.maximumWidth()
                height = self.label_new.maximumHeight()
                logger.debug('wd={}::ht={}::{}::{}'.format(width, height, screen_width, screen_height))
                if width != screen_width or height != screen_height:
                    self.text.setMaximumWidth(self.text.maximumWidth()+self.width_allowed)
                    self.label_new.setMaximumWidth(self.text.maximumWidth()+self.width_allowed)
                    self.label_new.setMaximumHeight(ht - self.height_allowed)
            else:
                if self.fullscreen_video:
                    self.gridLayout.setSpacing(5)
                    self.superGridLayout.setSpacing(5)
                self.list2.show()
                show_hide_playlist = 1
                if MainWindow.isFullScreen():
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                if self.list_with_thumbnail:
                    if self.title_list_changed:
                        self.update_list2()
                    if self.cur_row < self.list2.count():
                        self.list2.setCurrentRow(self.cur_row)
                    self.title_list_changed = False
        elif val == "Show/Hide Title List":
            if self.view_mode == 'thumbnail' and thumbnail_indicator:
                pass
            else:
                if not self.list1.isHidden():
                    ht = self.list1.height()
                    self.list1.hide()
                    self.frame.hide()
                    show_hide_titlelist = 0
                    width = self.label_new.maximumWidth()
                    height = self.label_new.maximumHeight()
                    if width != screen_width or height != screen_height:
                        self.text.setMaximumWidth(self.text.maximumWidth()+self.width_allowed)
                        self.label_new.setMaximumWidth(self.text.maximumWidth()+self.width_allowed)
                        self.label_new.setMaximumHeight(ht - self.height_allowed)
                else:
                    width = self.label_new.maximumWidth()
                    height = self.label_new.maximumHeight()
                    show_list = True
                    if width == screen_width and height == screen_height:
                        show_list = False
                    if show_list:
                        self.list1.show()
                        show_hide_titlelist = 1
                        if MainWindow.isFullScreen():
                            MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        elif val == "Lock File":
            v = str(self.action_player_menu[5].text())
            if v == "Lock File":
                self.player_setLoop_var = True
                self.action_player_menu[5].setText("UnLock File")
                self.player_loop_file.setText("unLock")
                if self.player_val == 'mpv':
                    self.mpvplayer_val.write(b'\n set loop-file inf \n')
                else:
                    self.mpvplayer_val.write(b'\n set_property loop 0 \n')
            elif v == "UnLock File":
                    self.player_setLoop_var = False
                    self.action_player_menu[5].setText("Lock File")
                    self.player_loop_file.setText("Lock")
                    if self.player_val == 'mpv':
                        self.mpvplayer_val.write(b'\n set loop-file no \n')
                    else:
                        self.mpvplayer_val.write(b'\n set_property loop -1 \n')
        elif val == "Lock Playlist":
            v = str(self.action_player_menu[2].text())
            if v == "Lock Playlist":
                self.playerPlaylist_setLoop_var = 1
                self.action_player_menu[2].setText("UnLock Playlist")
            elif v == "UnLock Playlist":
                    self.playerPlaylist_setLoop_var = 0
                    self.action_player_menu[2].setText("Lock Playlist")
        elif val == "Stop After Current File (Ctrl+Q)":
            self.quit_really = "yes"
        elif val == "Continue(default Mode)":
            self.quit_really = "no"
        elif val == "Shuffle":
            self.epn_arr_list = random.sample(self.epn_arr_list, len(self.epn_arr_list))
            self.update_list2()
        elif val == "Show/Hide Video":
            if self.tab_5.isHidden():
                self.tab_5.show()
                show_hide_player = 1
                if not self.label.isHidden():
                    self.label.hide()
                    self.label_new.hide()
                    self.text.hide()
                    show_hide_cover = 0
            else:
                self.tab_5.hide()
                show_hide_player = 0
        elif val =="Start Media Server":
            v= str(self.action_player_menu[7].text())
            if v == 'Start Media Server':
                self.start_stop_media_server(True)
            elif v == 'Stop Media Server':
                self.start_stop_media_server(False)
            if self.settings_box.tabs_present:
                self.settings_box.line19.setText(self.action_player_menu[7].text())
        elif val =="Broadcast Server":
            v= str(self.action_player_menu[8].text())
            if v == 'Broadcast Server' and self.local_http_server.isRunning():
                self.broadcast_server = True
                self.action_player_menu[8].setText("Stop Broadcasting")
                if not self.broadcast_thread:
                    self.broadcast_thread = BroadcastServer(self)
                    self.broadcast_thread.start()
                elif isinstance(self.broadcast_thread, BroadcastServer):
                    if not self.broadcast_thread.isRunning():
                        self.broadcast_thread.start()
            elif v == 'Stop Broadcasting':
                self.broadcast_server = False
                self.action_player_menu[8].setText("Broadcast Server")
            elif not self.local_http_server.isRunning():
                send_notification('No Server To Broadcast. First Start Media Server')
            if self.settings_box.tabs_present:
                self.settings_box.line021.setText(self.action_player_menu[8].text())
        elif val.lower() == 'turn on remote control':
            v= str(self.action_player_menu[9].text()).lower()
            msg = "Not Able to Take Action"
            if v == 'turn on remote control':
                self.remote_control_field = True
                self.action_player_menu[9].setText("Turn Off Remote Control")
                change_opt_file(HOME_OPT_FILE, 'REMOTE_CONTROL=', 'REMOTE_CONTROL=True')
                msg = "Remote Control Mode Enabled, Now Start Media server to control the player remotely"
            elif v == 'turn off remote control':
                self.remote_control_field = False
                self.remote_control = False
                self.action_player_menu[9].setText("Turn ON Remote Control")
                change_opt_file(HOME_OPT_FILE, 'REMOTE_CONTROL=', 'REMOTE_CONTROL=False')
                msg = "Remote Control Mode Disabled"
            send_notification(msg)
            if self.settings_box.tabs_present:
                self.settings_box.line020.setText(self.action_player_menu[9].text())
        elif val.lower() == 'set media server user/password':
            new_set = LoginAuth(parent=MainWindow, media_server=True, ui=self, tmp=TMPDIR)
        elif val.lower() == 'preferences (ctrl+p)':
            self.settings_box.start()
        elif val == "Set Current Background As Default":
            if (os.path.exists(self.current_background) 
                        and self.current_background != self.default_background):
                    shutil.copy(self.current_background, self.default_background)
                    arr_chk = [
                        os.path.join(self.home_folder, 'default_poster.jpg'),
                        os.path.join(self.home_folder, 'default_fit.jpg')
                        ]
                    for i in arr_chk:
                        if os.path.isfile(i):
                            os.remove(i)
                    QtCore.QTimer.singleShot(
                        100, partial(
                            set_mainwindow_palette, self.default_background,
                            first_time=True, theme='default'
                            )
                        )
        elif val == "Show/Hide Web Browser":
            self.showHideBrowser()
        elif (site == "Music" or site == "Local" or site == "Video" 
                or site == "PlayLists"):
            convert_str = (lambda txt: int(txt) if txt.isdigit() else txt.lower())
            create_key = (lambda txt: [convert_str(i) for i in re.split('([0-9]+)', txt)])
            if val == "Order by Name(Descending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list,
                        key = lambda x : create_key(str(x).split('	')[0].replace('#', '', 1)), 
                        reverse=True
                        )
                except Exception as err:
                    logger.error(err)
            elif val == "Order by Name(Ascending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list,
                        key = lambda x : create_key(str(x).split('	')[0].replace('#', '', 1)),
                        )
                except Exception as err:
                    logger.error(err)
            elif val == "Order by Date(Descending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : os.path.getmtime((
                        str(x).split('	')[1]).replace('"', '')), reverse=True)
                except Exception as e:
                    logger.error(e)
            elif val == "Order by Date(Ascending)":
                try:
                    self.epn_arr_list = sorted(
                        self.epn_arr_list, key = lambda x : os.path.getmtime((
                        str(x).split('	')[1]).replace('"', '')))
                except Exception as e:
                    logger.error(e)
            self.update_list2()
        
    def selectQuality(self):
        txt = str(self.sd_hd.text())
        if txt == "SD":
            quality = "sd480p"
            self.sd_hd.setText("480")
        elif txt == "480":
            quality = "hd"
            self.sd_hd.setText("HD")
        elif txt == "HD":
            quality = "best"
            self.sd_hd.setText("BEST")
        elif txt == "BEST":
            quality = "sd"
            self.sd_hd.setText("SD")
        self.quality_val = quality
    
    def start_stop_media_server(self, start_now):
        self.media_server_cache_music.clear()
        self.media_server_cache_playlist.clear()
        self.media_server_cache_video.clear()
        self.navigate_playlist_history.clear()
        if start_now:
            self.start_streaming = True
            self.action_player_menu[7].setText("Stop Media Server")
            if not self.local_http_server.isRunning():
                if not self.local_ip_stream:
                    self.local_ip_stream = '127.0.0.1'
                    self.local_port_stream = 9001
                self.local_http_server = ThreadServerLocal(
                    self.local_ip_stream, self.local_port_stream, ui_widget=ui, 
                    logr=logger, hm=home, window=MainWindow)
                self.local_http_server.start()
        else:
            self.start_streaming = False
            self.action_player_menu[7].setText("Start Media Server")
            if self.local_http_server.isRunning():
                self.local_http_server.httpd.shutdown()
                self.local_http_server.quit()
                msg = 'Stopping Media Server\n '+self.local_ip_stream+':'+str(self.local_port_stream)
                send_notification(msg)
    
    def filter_btn_options(self):
        if not self.frame.isHidden() and self.tab_6.isHidden():
            if self.go_page.isHidden():
                self.go_page.show()
                self.go_page.setFocus()
                self.list4.show()
                self.go_page.clear()
            else:
                self.list4.hide()
                self.list1.setFocus()
        elif not self.tab_6.isHidden():
            self.label_search.setFocus()
            
    def addToLibrary(self):
        self.settings_box.start(index='library')
        
    def options_clicked(self):
        global site, bookmark, siteName, opt, genre_num
        r = self.list3.currentRow()
        item = self.list3.item(r)
        if item and not self.lock_process:
            if (site == "PlayLists" or bookmark
                    or site == "Local" or site =="Music"):
                self.options('local') 
        
    def prev_thumbnails(self):
        global thumbnail_indicator, total_till, browse_cnt
        global total_till_epn, iconv_r, iconv_r_indicator
        logger.debug(self.view_mode)
        self.epn_list_count.append(self.list2.count())
        if self.view_mode == 'thumbnail_light':
            self.list_poster.show_list(mode='prev')
            try:
                for i in range(0, total_till_epn):
                    t = "self.label_epn_{0}.deleteLater()".format(i)
                    exec(t)
                total_till_epn=0
            
            except Exception as err:
                logger.error(err)
            try:
                self.labelFrame2.setText(
                '{0}. {1}'.format(
                    self.list1.currentRow()+1,
                    self.list1.currentItem().text()
                    )
                 )
            except Exception as err:
                logger.error(err)
        elif self.view_mode == 'thumbnail':
            self.scrollArea1.hide()
            self.scrollArea.show()
            try:
                self.labelFrame2.setText(self.list1.currentItem().text())
            except AttributeError as attr_err:
                logger.error(attr_err)
                return 0
            try:
                for i in range(0, total_till_epn):
                    t = "self.label_epn_"+str(i)+".deleteLater()"
                    exec(t)
                total_till_epn=0
            except Exception as err:
                logger.error(err)
            print(total_till, 2*self.list1.count()-1, '--prev-thumbnail--')
            if self.mpvplayer_val.processId() > 0:
                print(self.mpvplayer_val.processId(), '--prev-thumb--')
                self.icon_poster_indicator.append(1)
                self.next_page('not_deleted')
                QtWidgets.QApplication.processEvents()
                row = self.list1.currentRow()
                p1 = "self.label_"+str(row)+".y()"
                yy=eval(p1)
                self.scrollArea.verticalScrollBar().setValue(yy)
            elif total_till > 0 and total_till == 2*self.list1.count():
                row = self.list1.currentRow()
                p1 = "self.label_"+str(row)+".y()"
                yy=eval(p1)
                self.scrollArea.verticalScrollBar().setValue(yy)
                self.scrollArea1.hide()
                self.scrollArea.show()
            else:
                self.next_page('not_deleted')
                row = self.list1.currentRow()
                p1 = "self.label_"+str(row)+".y()"
                yy=eval(p1)
                self.scrollArea.verticalScrollBar().setValue(yy)
                self.scrollArea1.hide()
                self.scrollArea.show()
        
    def mplayer_unpause(self):
        global buffering_mplayer, mpv_indicator
        global cache_empty, pause_indicator
        buffering_mplayer = "no"
        self.mplayer_pause_buffer = False
        self.mplayer_nop_error_pause = False
        if self.player_val == "mplayer":
            self.mpvplayer_val.write(b'\n pause \n')
        else:
            self.mpvplayer_val.write(b'\n set pause no \n')
            if mpv_indicator:
                mpv_indicator.pop()
                cache_empty = 'no'
            if pause_indicator:
                pause_indicator.pop()
        print("UnPausing")
        if MainWindow.isFullScreen():
            if not self.frame_timer.isActive():
                self.frame1.hide()
                
    def frame_options(self):
        print("Frame Hiding" )
        if (MainWindow.isFullScreen() and site != "Music" and self.tab_6.isHidden() 
                and self.list2.isHidden() and self.tab_2.isHidden()):
            self.frame1.hide()
            self.gridLayout.setSpacing(5)
            
    

    def setPlayerFocus(self):
        global player_focus
        player_focus = 1 - player_focus
        if player_focus == 1:
            self.tab_5.show()
            self.tab_5.setFocus()
            self.list1.hide()
            self.label.hide()
            self.label_new.hide()
            self.text.hide()
            self.frame.hide()
            if not self.tab_6.isHidden():
                self.list2.hide()
                self.goto_epn.hide()
        else:
            self.tab_5.hide()
            self.list1.show()
            self.list2.show()
            self.text.show()
            self.label.show()
            self.label_new.show()
            self.list1.setFocus()
            
    def display_image(self, br_cnt, br_cnt_opt,
                      iconv_r_poster=None, value_str=None,
                      dimn=None, txt_name=None):
        global site, name, base_url, embed, opt, pre_opt, mirrorNo
        global row_history, home, epn, iconv_r
        global total_till, browse_cnt
        global bookmark, status, thumbnail_indicator
        global siteName, category, finalUrlFound, refererNeeded
        
        browse_cnt = br_cnt
        if txt_name:
            name_tmp = txt_name
        else:
            name_tmp = self.original_path_name[browse_cnt]
            if '\t' in name_tmp:
                name_tmp = name_tmp.split('\t')[0]
        length = self.list1.count()
        m =[]
        if (bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt'))):
            file_name = os.path.join(home, 'Bookmark', status+'.txt')
            line_a = open_files(file_name, True)
            tmp = line_a[browse_cnt]
            tmp = re.sub('\n', '', tmp)
            tmp1 = tmp.split(':')
            site = tmp1[0]
            if site == "Music" or site == "Video":
                opt = "Not Defined"
                if site == "Music":
                    music_opt = tmp1[1]
                else:
                    video_opt = tmp1[1]
            else:
                opt = tmp1[1]
            pre_opt = tmp1[2]
            siteName = tmp1[2]
            base_url = int(tmp1[3])
            embed = int(tmp1[4])
            name_tmp = tmp1[5]
            logger.info(name_tmp)
            if len(tmp1) > 6:
                if tmp1[6] == "True":
                    finalUrlFound = True
                else:
                    finalUrlFound = False
                if tmp1[7] == "True":
                    refererNeeded = True
                else:
                    refererNeeded = False
                if len(tmp1) >= 9:
                    if tmp1[8] == "True":
                        self.video_local_stream = True
                    else:
                        self.video_local_stream = False
                print(finalUrlFound)
                print(refererNeeded)
                print(self.video_local_stream)
            else:
                refererNeeded = False
                finalUrlFound = False
                self.video_local_stream = False
            logger.info(site + ":"+opt)
        
        if site == "Video":
            picn = os.path.join(home, 'Local', name_tmp, 'poster.jpg')
            m.append(picn)
            if os.path.exists(os.path.join(home, 'Local', name_tmp, 'summary.txt')):
                summary = open_files(
                        os.path.join(home, 'Local', name_tmp, 'summary.txt'), 
                        False)
                m.append(summary)
            else:
                m.append("Summary Not Available")
        elif site == "Music":
            picn = os.path.join(home, 'Music', 'Artist', name_tmp, 'poster.jpg')
            m.append(picn)
            logger.info(picn)
            if os.path.exists(os.path.join(home, 'Music', 'Artist', name_tmp, 'bio.txt')):
                summary = open_files(
                        os.path.join(home, 'Music', 'Artist', name_tmp, 'bio.txt'), 
                        False)
                m.append(summary)
            else:
                m.append("Summary Not Available")
        elif opt == "History":
            if siteName:
                dir_name =os.path.join(home, 'History', site, siteName, name_tmp)
            else:
                dir_name =os.path.join(home, 'History', site, name_tmp)
            if os.path.exists(dir_name):
                logger.info(dir_name)
                picn = os.path.join(home, 'History', site, name_tmp, 'poster.jpg')
                thumbnail = os.path.join(home, 'History', site, name_tmp, 'thumbnail.jpg')
                picn = thumbnail
                m.append(os.path.join(dir_name, 'poster.jpg'))
                try:	
                    summary = open_files(
                            os.path.join(dir_name, 'summary.txt'), False)
                    m.append(summary)
                except:
                    m.append("Not Available")
            else:
                m.append('No.jpg')
                m.append('Not Available')
        try:
            summary = m.pop()
        except:
            summary = "Not Available"
        try:
            picn = m.pop()
        except:
            picn = "No.jpg"
        if br_cnt_opt == 'image_list':
            if picn != "No.jpg" and os.path.exists(picn):
                if dimn:
                    picn = self.image_fit_option(picn, '', fit_size=6, widget_size=(int(dimn[0]), int(dimn[1])))
                #img = QtGui.QPixmap(picn, "1")
                picn = re.sub('poster.jpg', 'thumbnail.jpg', picn)
            return (picn, summary)
        elif br_cnt_opt == "image":
            if picn != "No.jpg" and os.path.exists(picn):
                if dimn:
                    picn = self.image_fit_option(picn, '', fit_size=6, widget_size=(int(dimn[0]), int(dimn[1])))
                img = QtGui.QPixmap(picn, "1")
                q1="self.label_"+str(browse_cnt)+".setPixmap(img)"
                exec (q1)
            
            name1 = name_tmp
            q3="self.label_"+str(length+browse_cnt)+".setText((name1))"
            exec (q3)
            try:
                sumry = "<html><h1>"+name1+"</h1><head/><body><p>"+summary+"</p>"+"</body></html>"
            except:
                sumry = "<html><h1>"+str(name1)+"</h1><head/><body><p>"+str(summary)+"</p>"+"</body></html>"
            q4="self.label_"+str(length+browse_cnt)+".setToolTip((sumry))"			
            exec (q4)
            p8="self.label_"+str(length+browse_cnt)+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(p8)
            if value_str == 'deleted':
                total_till = total_till+2
            if total_till%(2*iconv_r_poster) == 0:
                #QtWidgets.QApplication.processEvents()
                pass
                
    def next_page(self, value_str):
        global site, name, embed, opt, pre_opt, mirrorNo
        global row_history, home, epn, iconv_r
        global total_till
        global total_till, browse_cnt
        global bookmark, status, thumbnail_indicator
        global siteName, category, finalUrlFound, refererNeeded
        
        self.lock_process = True
        m=[]
        if value_str == "deleted":
            for i in range(total_till):
                t = "self.label_"+str(i)+".clear()"
                exec(t)
                t = "self.label_"+str(i)+".deleteLater()"
                exec(t)
            total_till = 0
        if total_till==0 or value_str=="not_deleted" or value_str == 'zoom':
            length = self.list1.count()
        else:
            if (site == "Local" or site == "None" or site == "PlayLists" 
                    or site=="Video" or site=="Music" or opt == "History"
                    or site == 'MyServer'):
                length = self.list1.count()
        iconv_r_poster = ui.icon_poster_indicator[-1]
        if iconv_r_poster == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        print("width="+str(self.tab_6.width()))
        
        if iconv_r_poster > 1:
            w = float((self.tab_6.width()-60)/iconv_r_poster)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if self.tab_6_size_indicator:
                        l= (self.tab_6_size_indicator[-1]-60)/iconv_r_poster
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r_poster == 1:
            w = float(self.tab_6.width()-60)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
        if self.font_bold:
            font_bold = 'bold'
        else:
            font_bold = ''
        font_size = self.global_font_size + 3
        width = int(w)
        height = int(h)
        hei_ght= int(h/3)
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        logger.debug(length)
        logger.debug(browse_cnt)
        dim_tuple = (height, width)
        self.labelFrame2.setText('Wait...')
        if total_till==0 or value_str == "not_deleted" or value_str == 'zoom':
            i = 0
            j = iconv_r_poster+1
            k = 0
            if opt != "History":
                if site in ["Video", "Music", 'PlayLists', 'MyServer']:
                    length = self.list1.count()
                else:
                    length = 100
            if iconv_r_poster == 1:
                j1 = 3
            else:
                j1 = 2*iconv_r_poster
            if total_till == 0:
                value_str = "deleted"
            while(i<length):
                logger.debug('--value--str={0}'.format(value_str))
                if value_str == "deleted":
                    p1 = "self.label_{0} = TitleThumbnailWidget(self.scrollAreaWidgetContents)".format(i)
                    exec(p1)
                    p1 = "l_{0} = weakref.ref(self.label_{0})".format(i)
                    exec(p1)
                label_title = eval('self.label_{0}'.format(i))
                label_title.setup_globals(self, home, TMPDIR, logger)
                label_title.setMaximumSize(QtCore.QSize(height, width))
                label_title.setMinimumSize(QtCore.QSize(height, width))
                label_title.setObjectName(_fromUtf8('label_{0}'.format(i)))
                self.gridLayout1.addWidget(label_title, j, k, 1, 1, QtCore.Qt.AlignCenter)
                label_title.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
                label_title.setMouseTracking(True)
                
                if value_str == "deleted":
                    p1 = "self.label_{0} = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)".format(length+i)
                    exec(p1)
                    p1 = "l_{0} = weakref.ref(self.label_{0})".format(length+i)
                    exec(p1)
                label_title_txt = eval('self.label_{0}'.format(length+i))
                label_title_txt.setMinimumWidth(width)
                label_title_txt.setMaximumHeight(hei_ght)
                label_title_txt.lineWrapMode()
                label_title_txt.setObjectName('label_{0}'.format(length+i))
                self.gridLayout1.addWidget(label_title_txt, j1, k, 1, 1, QtCore.Qt.AlignCenter)
                label_title_txt.setReadOnly(True)
                label_title_txt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                label_title_txt.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                if self.global_font != 'default':
                    if self.player_theme == 'default':
                        label_title_txt.setStyleSheet(
                            """font: {bold} {size}px {0};color: {1};
                            QToolTip{{ font: {bold} {size}px {0}; color:{1};
                            background:rgb(56,60,74);
                            }}
                            """.format(self.global_font, self.thumbnail_text_color, bold=font_bold, size=font_size)
                            )
                    else:
                        label_title_txt.setStyleSheet(
                            """font: {bold} {size}px {0}; color: {1};
                            QToolTip{{ font: {bold} {size}px {0}; color:{1};
                            background:rgb(56,60,74);
                            }}
                            """.format(self.global_font, self.thumbnail_text_color, bold=font_bold, size=font_size)
                            )
                if value_str == "deleted" or value_str == 'zoom':
                    self.display_image(i, "image", iconv_r_poster, value_str, dimn=dim_tuple)
                    
                i=i+1
                k = k+1
                if k == iconv_r_poster:
                    j = j + 2*iconv_r_poster
                    j1 = j1+2*iconv_r_poster
                    k = 0
                    self.labelFrame2.setText('Wait...{0}/{1}'.format(int(i/2), int(length/2)))
                    QtWidgets.QApplication.processEvents()
            self.labelFrame2.setText('Finished!')
        self.lock_process = False
            
    def thumbnail_label_update(self, clicked_num=None):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator
        global finalUrlFound, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        print("width="+str(self.tab_6.width()))
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if self.tab_6_size_indicator:
                        l= (self.tab_6_size_indicator[-1]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-40)
            #w = float(self.tab_6.width())
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
        width = int(w)
        height = int(h)
        print("self.width={}".format(width))
        print("self.height={}".format(height))
        
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
            
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
        if clicked_num:
            range_show = [i for i in range(clicked_num-15, clicked_num+15)]
        else:
            range_show = None
        self.scrollArea1.hide()
        if total_till_epn > 0:
            i = 0
            j = iconv_r+1
            k = 0
            length1 = 2*length
            ii = length
            if iconv_r == 1:
                jj = 3
            else:
                jj = 2*iconv_r
            kk = 0
            while(i<length):
                p2 = "self.label_epn_{0}".format(i)
                label_epn = eval(p2)
                label_hide = False
                if range_show:
                    if i not in range_show:
                        label_epn.hide()
                        label_hide = True
                if not label_hide:
                    label_epn.setMaximumSize(QtCore.QSize(width, height))
                    label_epn.setMinimumSize(QtCore.QSize(width, height))
                    label_epn.setObjectName(_fromUtf8('label_epn_{0}'.format(i)))
                    self.gridLayout2.addWidget(label_epn, j, k, 1, 1, QtCore.Qt.AlignCenter)
                    label_epn.show()
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
                
                p2 = "self.label_epn_{0}".format(ii)
                label_epn_txt = eval(p2)
                if not label_hide:
                    label_epn_txt.setMinimumWidth(width)
                    label_epn_txt.setMaximumWidth(width)
                    label_epn_txt.setObjectName(_fromUtf8('label_epn_{0}'.format(ii)))
                    self.gridLayout2.addWidget(label_epn_txt, jj, kk, 1, 1, QtCore.Qt.AlignCenter)
                    label_epn_txt.show()
                else:
                    label_epn_txt.hide()
                ii += 1
                kk += 1
                if kk == iconv_r:
                    jj = jj + 2*iconv_r
                    kk = 0
            total_till_epn = length1
            self.scrollArea1.show()
            
    def thumbnail_label_update_epn(self, clicked_num=None):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator
        global finalUrlFound, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        print("width="+str(self.tab_6.width()))
        #QtWidgets.QApplication.processEvents()
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if self.tab_6_size_indicator:
                        l= (self.tab_6_size_indicator[-1]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    #h = float((9*w)/16)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-40)
            #h = float((9*w)/16)
            h = int(w/self.image_aspect_allowed)
        width = int(w)
        height = int(h)
        hei_ght= int(int(height)/3)
        print("self.width={}".format(width))
        print("self.height={}".format(height))
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
        if clicked_num:
            range_show = [i for i in range(clicked_num-15, clicked_num+15)]
        else:
            range_show = None
        print(range_show, '--range--')
        self.scrollArea1.hide()
        if total_till_epn > 0:
            i = 0
            j = iconv_r+1
            k = 0
            length1 = 2*length
            ii = length
            if iconv_r == 1:
                jj = 3
            else:
                jj = 2*iconv_r
            kk = 0
            label_txt = self.labelFrame2.text()
            self.labelFrame2.setText('Wait...')
            while(i<length):
                p2 = "self.label_epn_{0}".format(i)
                label_epn = eval(p2)
                label_hide = False
                if range_show:
                    if i not in range_show:
                        label_epn.hide()
                        label_hide = True
                if not label_hide:
                    label_epn.setMaximumSize(QtCore.QSize(width, height))
                    label_epn.setMinimumSize(QtCore.QSize(width, height))
                    label_epn.setObjectName(_fromUtf8('label_epn_{0}'.format(i)))
                    label_epn.show()
                self.gridLayout2.addWidget(label_epn, j, k, 1, 1, QtCore.Qt.AlignCenter)
                counter = i
                if not label_hide:
                    if site in ["Video", "Music", 'PlayLists', 'MyServer', 'None']:
                        if '	' in self.epn_arr_list[counter]:
                            nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                            
                            path = ((self.epn_arr_list[counter]).split('	')[1])
                        else:
                            nameEpn = os.path.basename(self.epn_arr_list[counter])
                            path = (self.epn_arr_list[counter])
                        nameEpn = nameEpn.strip()
                        if self.list1.currentItem():
                            name_t = self.list1.currentItem().text()
                        else:
                            name_t = ''
                        picn = self.get_thumbnail_image_path(counter, self.epn_arr_list[counter])
                    else:
                        if finalUrlFound == True:
                            if '	' in self.epn_arr_list[counter]:
                                nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                            
                            else:
                                nameEpn = os.path.basename(self.epn_arr_list[counter])
                            nameEpn = nameEpn
                        else:
                            if '	' in self.epn_arr_list[counter]:
                                nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                            else:
                                nameEpn = (self.epn_arr_list[counter])
                            nameEpn = nameEpn
                        picnD = os.path.join(home, 'thumbnails', name)
                        if not os.path.exists(picnD):
                            os.makedirs(picnD)
                        picn = os.path.join(picnD, nameEpn+'.jpg')
                        picn = picn.replace('#', '', 1)
                        if picn.startswith(self.check_symbol):
                            picn = picn[1:]
                    
                    picn_old = picn
                    picn = self.image_fit_option(picn_old, '', fit_size=6, widget_size=(int(width), int(height)))
                    img = QtGui.QPixmap(picn, "1")
                    q1="self.label_epn_"+str(counter)+".setPixmap(img)"
                    exec (q1)
                
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
                
                p2 = "self.label_epn_{0}".format(ii)
                label_epn_txt = eval(p2)
                if not label_hide:
                    label_epn_txt.setMinimumWidth(width)
                    label_epn_txt.setMaximumWidth(width)
                    label_epn_txt.setMaximumHeight(hei_ght)
                    label_epn_txt.setObjectName(_fromUtf8('label_epn_{0}'.format(ii)))
                    label_epn_txt.show()
                else:
                    label_epn_txt.hide()
                self.gridLayout2.addWidget(label_epn_txt, jj, kk, 1, 1, QtCore.Qt.AlignCenter)
                ii += 1
                kk += 1
                if kk == iconv_r:
                    jj = jj + 2*iconv_r
                    kk = 0
                    self.labelFrame2.setText('Wait...{0}/{1}'.format(int(i), int(length)))
            self.labelFrame2.setText(label_txt)
            total_till_epn = length1
            self.scrollArea1.show()
            
    def get_thumbnail_image_path(self, row_cnt, row_string, only_name=None,
                                 title_list=None, start_async=None, send_path=None):
        global site, home, name
        picn = ''
        title = row_string.strip()
        path = ''
        if (site == "Local" or site == "None" or site == "Music" 
                or site.lower() == 'playlists' or site == "Video" 
                or site.lower() == 'myserver'):
            
            thumbnail_dir = os.path.join(home, 'thumbnails', 'thumbnail_server')
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)
            
            if title_list:
                name_t = title_list
            else:
                if self.list1.currentItem():
                    name_t = self.list1.currentItem().text()
                else:
                    name_t = name
                    
            if '	' in title:
                path = title.split('	')[1]
            else:
                path = name_t +'_'+ title
            
            if path.startswith('abs_path='):
                path = self.if_path_is_rel(path, thumbnail=True)
                
            path = path.replace('"', '')
            thumb_name_bytes = bytes(path, 'utf-8')
            h = hashlib.sha256(thumb_name_bytes)
            thumb_name = h.hexdigest()
            picn = os.path.join(thumbnail_dir, thumb_name+'.jpg')
            pic = ''
            if site == "Music":
                if os.path.exists(picn):
                    if os.stat(picn).st_size == 0:
                        art_n =title.split('	')[2]
                        if OSNAME != 'posix':
                            art_n = self.replace_special_characters(art_n)
                        pic = os.path.join(home, 'Music', 'Artist', art_n, 'poster.jpg')
                        if os.path.exists(pic):
                            if os.stat(pic).st_size:
                                shutil.copy(pic, picn)
                                picn = pic
        else:
            if '	' in title:
                nameEpn = title.split('	')[0]
            else:
                nameEpn = title
                
            if title_list:
                name_t = title_list
            else:
                if self.list1.currentItem():
                    name_t = self.list1.currentItem().text()
                else:
                    name_t = name
                    
            if OSNAME != 'posix':
                nameEpn = self.replace_special_characters(nameEpn)
                namedir = self.replace_special_characters(name_t)
            else:
                namedir = name_t
            picnD = os.path.join(home, 'thumbnails', namedir)
            if not os.path.exists(picnD):
                try:
                    os.makedirs(picnD)
                except Exception as e:
                    print(e)
                    return os.path.join(home, 'default.jpg')
            picn = os.path.join(picnD, nameEpn+'.jpg')
            picn = picn.replace('#', '', 1)
            if picn.startswith(self.check_symbol):
                picn = picn[1:]
        inter = "10s"
        if send_path and only_name:
            return (picn, path)
        elif only_name:
            return picn
            
        if ((picn and not os.path.exists(picn) and 'http' not in path) 
                or (picn and not os.path.exists(picn) and 'http' in path and 'youtube.com' in path)
                or (picn and 'http' in path and site.lower() == 'myserver' and not os.path.exists(picn))
                or start_async):
            path = path.replace('"', '')
            if (('http' in path and 'youtube.com' in path and '/watch?' in path) or
                    ('http' in path and site.lower() == 'myserver')):
                if site.lower() == 'myserver':
                    path = path + '.image'
                else:
                    path = self.create_img_url(path)
            self.threadPoolthumb.append(ThreadingThumbnail(self, logger, path, picn, inter))
            self.threadPoolthumb[len(self.threadPoolthumb)-1].finished.connect(
                partial(self.thumbnail_generated, row_cnt, picn))
            length = len(self.threadPoolthumb)
            if length == 1:
                if not self.threadPoolthumb[0].isRunning():
                    self.threadPoolthumb[0].start()
        return picn
    
    def thumbnailEpn(self):
        global total_till, browse_cnt, home, iconv_r, site
        global thumbnail_indicator
        global finalUrlFound, home, total_till_epn
        
        m=[]
        self.scrollArea.hide()
        self.scrollArea1.show()
        if iconv_r == 1 and not self.tab_5.isHidden():
            self.tab_6.setMaximumSize(self.width_allowed, 16777215)
        else:
            self.tab_6.setMaximumSize(16777215, 16777215)
        self.labelFrame2.show()
        print("width="+str(self.tab_6.width()))
        if iconv_r > 1:
            w = float((self.tab_6.width()-60)/iconv_r)
            h = int(w/self.image_aspect_allowed)
            if self.tab_5.isHidden() and self.mpvplayer_val:
                if self.mpvplayer_val.processId() > 0:
                    if self.tab_6_size_indicator:
                        l= (self.tab_6_size_indicator[-1]-60)/iconv_r
                    else:
                        l = self.tab_6.width()-60
                    w = float(l)
                    h = int(w/self.image_aspect_allowed)
        elif iconv_r == 1:
            w = float(self.tab_6.width()-40)
            h = int(w/self.image_aspect_allowed)
        width = int(w)
        height = int(h)
        if self.font_bold:
            font_bold = 'bold'
        else:
            font_bold = ''
        font_size = self.global_font_size + 3
        if self.icon_size_arr:
            self.icon_size_arr[:]=[]
        self.icon_size_arr.append(width)
        self.icon_size_arr.append(height)
        if not thumbnail_indicator:
            thumbnail_indicator.append("Thumbnail View")
        length = self.list2.count()
        if len(self.epn_list_count) >= 2:
            prev_count = self.epn_list_count[-2]
        else:
            prev_count = -1
        logger.debug('current={0}::prev={1}'.format(length, prev_count))
        if total_till_epn==0:
            i = 0
            #j = 5
            j = iconv_r+1
            k = 0
            
            length1 = 2*length
            ii = length
            if iconv_r == 1:
                jj = 3
            else:
                jj = 2*iconv_r
            kk = 0
            hei_ght = int((int(height)/3))
            label_txt = self.labelFrame2.text()
            self.labelFrame2.setText('Wait...')
            while(i<length):
                if prev_count >= 0 and prev_count <= length and i < prev_count:
                    create_widget = False
                elif prev_count >= 0 and prev_count > length and i < length:
                    create_widget = False
                else:
                    create_widget = True
                p1 = "self.label_epn_{0} = ThumbnailWidget(self.scrollAreaWidgetContents1)".format(i)
                exec (p1)
                p1 = "l_{0} = weakref.ref(self.label_epn_{0})".format(i)
                exec (p1)
                label_epn = eval('self.label_epn_{0}'.format(i))
                label_epn.setup_globals(MainWindow, ui, home, TMPDIR, logger, screen_width, screen_height)
                label_epn.setMaximumSize(QtCore.QSize(width, height))
                label_epn.setMinimumSize(QtCore.QSize(width, height))
                label_epn.setObjectName(_fromUtf8('label_epn_{0}'.format(i)))
                self.gridLayout2.addWidget(label_epn, j, k, 1, 1, QtCore.Qt.AlignCenter)
                label_epn.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
                label_epn.setMouseTracking(True)
                if self.player_theme == 'dark':
                    label_epn.setStyleSheet("""
                    QMenu{{
                    color: white;
                    background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 2px;
                    }}
                    QMenu::item{{
                    color: {0};
                    background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 4px; margin: 2px 2px 2px 10px;
                    }}
                    QMenu::item:selected{{
                    color: {1};
                    background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                    }}
                    """.format(self.list_text_color, self.list_text_color_focus))
                counter = i
                start_already = False
                if site in [site=="None", "Music", "Video", 'MyServer', 'PlayLists']: 
                    if '	' in self.epn_arr_list[counter]:
                        nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                        
                        path = ((self.epn_arr_list[counter]).split('	')[1])
                    else:
                        nameEpn = os.path.basename(self.epn_arr_list[counter])
                        path = (self.epn_arr_list[counter])
                    nameEpn = nameEpn.strip()
                    if self.list1.currentItem():
                        name_t = self.list1.currentItem().text()
                    else:
                        name_t = ''
                    picn, path = self.get_thumbnail_image_path(
                        counter, self.epn_arr_list[counter], only_name=True,
                        send_path=True)
                    
                    if not os.path.exists(picn):
                        picn = self.get_thumbnail_image_path(counter, self.epn_arr_list[counter], start_async=True)
                        new_obj = SetThumbnailGrid(self, logger, counter, picn, '',
                                                   fit_size=6, widget_size=(int(width), int(height)),
                                                   length=length, nameEpn=nameEpn, path=path)
                        self.append_to_thread_list(self.thread_grid_thumbnail, new_obj,
                                                   self.grid_thumbnail_process_finished,
                                                   counter)
                        start_already = True
                else:
                    if finalUrlFound == True:
                        if '	' in self.epn_arr_list[counter]:
                            nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                        
                        else:
                            nameEpn = os.path.basename(self.epn_arr_list[counter])
                        nameEpn = nameEpn
                    else:
                        if '	' in self.epn_arr_list[counter]:
                            nameEpn = (self.epn_arr_list[counter]).split('	')[0]
                        else:
                            nameEpn = (self.epn_arr_list[counter])
                        nameEpn = nameEpn
                    picnD = os.path.join(home, 'thumbnails', name)
                    if not os.path.exists(picnD):
                        os.makedirs(picnD)
                    picn = os.path.join(picnD, nameEpn+'.jpg')
                    picn = picn.replace('#', '', 1)
                    if picn.startswith(self.check_symbol):
                        picn = picn[1:]
                        
                picn_old = picn
                if not start_already:
                    picn = ui.image_fit_option(picn_old, '', fit_size=6, widget_size=(int(width), int(height)))
                    img = QtGui.QPixmap(picn, "1")
                    label_epn.setPixmap(img)
                
                i=i+1
                k = k+1
                if k == iconv_r:
                    j = j + 2*iconv_r
                    k = 0
                    
                p1 = "self.label_epn_{} = QtWidgets.QTextEdit(self.scrollAreaWidgetContents1)".format(ii)
                exec(p1)
                p7 = "l_"+str(ii)+" = weakref.ref(self.label_epn_"+str(ii)+")"
                exec(p7)
                label_epn_txt = eval('self.label_epn_{0}'.format(ii))
                label_epn_txt.setMinimumWidth(width)
                label_epn_txt.setObjectName(_fromUtf8('label_epn_{}'.format(ii)))
                self.gridLayout2.addWidget(label_epn_txt, jj, kk, 1, 1, QtCore.Qt.AlignCenter)
                label_epn_txt.setMaximumHeight(hei_ght)
                label_epn_txt.lineWrapMode()
                label_epn_txt.setReadOnly(True)
                label_epn_txt.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                label_epn_txt.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
                    
                if nameEpn.startswith('#'):
                    nameEpn = nameEpn.replace('#', self.check_symbol, 1)
                nameEpn = nameEpn.replace('_', ' ')
                sumry = "<html><h4>"+nameEpn+"</h4></html>"
                sumry = sumry.replace('"', '')
                
                path_thumb, new_title = os.path.split(picn_old)
                txt_file = new_title.replace('.jpg', '.txt', 1)
                txt_path = os.path.join(path_thumb, txt_file)
                if os.path.isfile(txt_path):
                    sumry = open_files(txt_path, False)
                    sumry = sumry.replace('\n', '<br>')
                    sumry = "<html>"+sumry+"</html>"
                label_epn_txt.setText(nameEpn)
                label_epn_txt.setAlignment(QtCore.Qt.AlignCenter)
                if self.global_font != 'default':
                    if self.player_theme == 'default':
                        label_epn_txt.setStyleSheet(
                            """font: {bold} {size}px {0};color: {1};
                            QToolTip{{ font: {bold} {size}px {0}; color:{1};
                            background:rgb(56,60,74);
                            }}
                            """.format(self.global_font, self.thumbnail_text_color,
                                       bold=font_bold, size=font_size)
                            )
                    else:
                        label_epn_txt.setStyleSheet(
                            """font: {bold} {size}px {0};color: {1};
                            QToolTip{{ font: {bold} {size}px {0}; color:{1};
                            background:rgb(56,60,74);
                            }}
                            """.format(self.global_font, self.thumbnail_text_color,
                                       bold=font_bold, size=font_size)
                            )
                label_epn_txt.setToolTip(sumry)
                ii += 1
                kk += 1
                if kk == iconv_r:
                    jj = jj+2*iconv_r
                    kk = 0
                    self.labelFrame2.setText('Wait...{0}/{1}'.format(int(i), int(length)))
                QtWidgets.QApplication.processEvents()
            self.labelFrame2.setText(label_txt)
            total_till_epn = length1
            self.scrollArea1.setFocus()
            
    def grid_thumbnail_process_finished(self, k):
        logger.debug('finished={0}'.format(k))
        
    def append_to_thread_list(self, thread_arr, thread_obj, finish_fun, *args):
        thread_arr.append(thread_obj)
        length = len(thread_arr) - 1
        thread_arr[length].finished.connect(partial(finish_fun, args[0]))
        thread_arr[length].start()
    
    def get_external_url_status(self, finalUrl):
        external_url = False
        if finalUrl.startswith('"http') or finalUrl.startswith('http'):
            try:
                ip_addr = finalUrl.split('/')[2]
                if ':' in ip_addr:
                    ip_addr = ip_addr.split(':')[0]
            except Exception as e:
                print(e)
                ip_addr = 'none'
            private_ip = False
            try:
                ip_obj = ipaddress.ip_address(ip_addr)
                print(ip_obj)
                if ip_obj.is_private:
                    private_ip = True
            except Exception as e:
                print(e)
            if not private_ip:
                external_url = True
        return external_url
    
    def get_redirected_url_if_any(self, finalUrl, external_url):
        if not external_url:
            if finalUrl.startswith('"http') or finalUrl.startswith('http'):
                finalUrl = finalUrl.replace('"', '')
                content = ccurl(finalUrl+'#'+'-H')
                if "Location:" in content:
                    m = re.findall('Location: [^\n]*', content)
                    finalUrl = re.sub('Location: |\r', '', m[-1])
        return finalUrl
            
    def epnClicked(self, dock_check=None):
        global queueNo, MainWindow
        self.cur_row = self.list2.currentRow()
        queueNo = queueNo + 1
        thumb_mode = False
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat(('Wait...'))
        if self.float_window.isHidden():
            if (self.view_mode == 'thumbnail' and self.idw != str(int(self.tab_5.winId())) and thumbnail_indicator):
                num = self.list2.currentRow()
                if self.mpvplayer_val.processId() > 0:
                    self.mpvNextEpnList(play_row=num, mode= 'play_now')
                else:
                    exec_str = 'self.label_epn_{0}.change_video_mode({1}, {2})'.format(num, self.video_mode_index, num)
                    exec(exec_str)
                thumb_mode = True
            else:
                if self.mpvplayer_val.processId() > 0:
                    if self.idw != str(int(self.tab_5.winId())):
                        if self.idw == str(int(self.label_new.winId())):
                            self.mpvNextEpnList(play_row=self.cur_row, mode='play_now')
                        else:
                            self.mpvplayer_val.kill()
                            self.mpvplayer_started = False
                            self.idw = str(int(self.tab_5.winId()))
                    if self.mpvplayer_started:
                        self.mpvNextEpnList(play_row=self.cur_row, mode='play_now')
                    else:
                        self.epnfound()
                else:
                    self.epnfound()
            if dock_check:
                if self.auto_hide_dock:
                    self.dockWidget_3.hide()
        else:
            if not self.idw or self.idw == str(int(self.tab_5.winId())):
                self.epnfound()
            elif self.idw == str(int(self.label.winId())) or self.idw == str(int(self.label_new.winId())):
                self.epnfound()
            else:
                final = self.epn_return(self.cur_row)
                self.play_file_now(final)
                self.paste_background(self.cur_row)
                try:
                    server._emitMeta("Play", site, self.epn_arr_list)
                except Exception as e:
                    print(e)
        if MainWindow.isFullScreen() and site.lower() != 'music' and self.list2.isHidden():
            if thumb_mode:
                exec_str = 'self.label_epn_{0}.player_thumbnail_fs(mode="{1}")'.format(num, 'fs')
                exec(exec_str)
            else:
                self.tab_5.player_fs(mode='fs')
    
    def mpvNextEpnList(self, play_row=None, mode=None):
        global epn, site
        print(play_row, '--play_row--', mode)
        self.cache_mpv_counter = '00'
        self.cache_mpv_indicator = False
        if self.mpvplayer_val.processId() > 0:
            print("-----------inside-------")
            if play_row != None and mode == 'play_now':
                self.cur_row = play_row
            else:
                if self.cur_row == self.list2.count() - 1:
                    self.cur_row = 0
                    if (site == "Music" and not self.playerPlaylist_setLoop_var) or (self.list2.count()==1):
                        r1 = self.list1.currentRow()
                        it1 = self.list1.item(r1)
                        if it1:
                            if r1 < self.list1.count():
                                r2 = r1+1
                            else:
                                r2 = 0
                            self.list1.setCurrentRow(r2)
                            self.listfound()
                else:
                    self.cur_row += 1

            self.list2.setCurrentRow(self.cur_row)
            if site != "PlayLists" and not self.queue_url_list:
                try:
                    if '	' in self.epn_arr_list[self.cur_row]:
                        epn = self.epn_arr_list[self.cur_row].split('	')[1]
                    else:
                        epn = self.list2.currentItem().text()
                    epn = epn.replace('#', '', 1)
                    if epn.startswith(self.check_symbol):
                        epn = epn[1:]
                except:
                    pass
            
            if site in ["Music", "Video", "None", "PlayLists", 'MyServer']:
                self.external_url = self.get_external_url_status(self.final_playing_url)
                if self.player_val == 'mpv':
                    seek_time = self.progress_counter
                else:
                    seek_time = (self.progress_counter/1000)
                logger.debug('seek-time:{0}'.format(seek_time))
                if self.final_playing_url in self.history_dict_obj:
                    _, _, sub_id, audio_id, rem_quit, vol, asp = self.history_dict_obj.get(self.final_playing_url)
                    if seek_time <= 10:
                        seek_time = 0
                    self.history_dict_obj.update(
                        {self.final_playing_url:[seek_time, time.time(), sub_id, audio_id, rem_quit, vol, asp]}
                        )    
                
                if self.external_url:
                    if '	' in self.epn_arr_list[self.cur_row]:
                        lnk_epn = self.epn_arr_list[self.cur_row].split('	')[1]
                    else:
                        lnk_epn = self.list2.currentItem().text()
                    if lnk_epn.startswith('abs_path=') or lnk_epn.startswith('relative_path='):
                        print(self.mpvplayer_val.processId())
                    else:
                        self.mpvplayer_val.kill()
                        self.mpvplayer_started = False
                        
                move_ahead = True
                if self.gapless_network_stream:
                    if self.tmp_pls_file_dict.get(self.cur_row) and self.playback_mode == 'playlist':
                        if self.tmp_pls_file_lines[self.cur_row].startswith('http'):
                            move_ahead = False
                            tname = self.epn_arr_list[self.cur_row]
                            if tname.startswith('#'):
                                tname = tname.replace('#', '', 1)
                            if '\t' in tname:
                                self.epn_name_in_list = tname.split('\t')[0]
                            else:
                                self.epn_name_in_list = tname
                            MainWindow.setWindowTitle(self.epn_name_in_list)
                            self.float_window.setWindowTitle(self.epn_name_in_list)
                            server._emitMeta("Next", site, self.epn_arr_list)
                            self.mpv_execute_command('set playlist-pos {}'.format(self.cur_row), self.cur_row)
                        
                if len(self.queue_url_list)>0:
                    if isinstance(self.queue_url_list[0], tuple):
                        if move_ahead:
                            self.localGetInList(eofcode='next')
                    else:
                        self.getQueueInList(eofcode='next')
                else:
                    if move_ahead:
                        self.localGetInList(eofcode='next')
            else:
                if self.player_val == "mpv":
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.getNextInList(eofcode='next')
                else:
                    print(self.mpvplayer_val.state())
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    print(self.mpvplayer_val.processId(), '--mpvnext---')
                    self.getNextInList(eofcode='next')
    
    def mpvPrevEpnList(self):
        global epn, site
        global current_playing_file_path
        self.cache_mpv_counter = '00'
        self.cache_mpv_indicator = False
        if self.mpvplayer_val.processId() > 0:
            print("inside")
            if self.cur_row == 0:
                self.cur_row = self.list2.count() - 1
                if ((site == "Music" and not self.playerPlaylist_setLoop_var) 
                        or (self.list2.count() == 1)):
                    r1 = self.list1.currentRow()
                    it1 = self.list1.item(r1)
                    if it1:
                        if r1 > 0:
                            r2 = r1-1
                        else:
                            r2 = self.list2.count()-1
                        self.cur_row = self.list2.count() - 1
            else:
                self.cur_row -= 1
            self.mpvNextEpnList(play_row=self.cur_row, mode='play_now')
    
    def HideEveryThing(self, widget_except=None, mode=None):
        global view_layout
        if not self.search_on_type_btn.isHidden():
            self.search_on_type_btn.hide()
        elif self.mpvplayer_val.processId() > 0 and mode != 'fs':
            pass
        else:
            if not self.status_dict_widget:
                self.status_dict_widget = {
                        'list1':ui.list1.isHidden(), 'list2':ui.list2.isHidden(),
                        'frame1':ui.frame1.isHidden(), 'label':ui.label.isHidden(),
                        'label_new':ui.label_new.isHidden(), 'text':ui.text.isHidden(),
                        'player':ui.tab_5.isHidden(), 'scrollArea':ui.scrollArea.isHidden(),
                        'scrollArea1':ui.scrollArea1.isHidden(), 'frame':ui.frame.isHidden(),
                        'dock_3':ui.dockWidget_3.isHidden(), 'tab_2':ui.tab_2.isHidden(),
                        'tab_6':ui.tab_6.isHidden()
                        }
                for i in self.status_dict_widget:
                    status = self.status_dict_widget[i]
                    if not status:
                        self.widget_dict[i].hide()
                if widget_except is not None:
                    if isinstance(widget_except, list):
                        for widget in widget_except:
                            widget.show()
                    elif widget_except.isHidden():
                        widget_except.show()
            else:
                for i in self.status_dict_widget:
                    status = self.status_dict_widget[i]
                    if not status:
                        self.widget_dict[i].show()
                self.status_dict_widget.clear()
        
    def thumbnailHide(self, context):
        global view_layout, total_till, browse_cnt, iconv_r
        global memory_num_arr
        global thumbnail_indicator, iconv_r_indicator, total_till_epn
        self.idw = str(int(self.tab_5.winId()))
        thumbnail_indicator[:]=[]
        memory_num_arr[:]=[]
        i = 0
        if context == "ExtendedQLabel":
            pass
        else:
            if total_till > 0:
                while(i<total_till):
                    t = "self.label_"+str(i)+".deleteLater()"
                    exec(t)
                    i = i+1
            if total_till_epn > 0:
                for i in range(total_till_epn):
                    t = "self.label_epn_"+str(i)+".deleteLater()"
                    exec(t)
            self.list_poster.clear()
            self.list_poster.title_clicked = False
            total_till = 0
            total_till_epn = 0
        if iconv_r_indicator:
            iconv_r = iconv_r_indicator[0]
        else:
            iconv_r = 6
        self.tab_6.setMaximumSize(16777215, 16777215)
        browse_cnt = 0
        self.list_poster.hide()
        self.tab_6.hide()
        self.list1.show()
        self.list2.show()
        self.label.show()
        self.label_new.show()
        self.frame1.show()
        self.text.show()
        self.fullscreen_mode = 0
        if context == "ExtendedQLabel":
            pass
        else:
            view_layout = "List"
            self.view_mode = "list"
        if self.mpvplayer_val.processId() > 0:
            self.text.hide()
            self.label.hide()
            self.label_new.hide()
            self.list1.hide()
            self.frame.hide()
            self.tab_5.show()
        self.update_list2()
        
    def webClose(self):
        global view_layout, desktop_session
        
        #if not self.VerticalLayoutLabel.itemAt(2):
        #    self.VerticalLayoutLabel.addStretch(2)
        #    print('--stretch -- added--to --label and text widget--')
        
        self.tmp_web_srch = ''
        if self.web:
            self.web.setHtml('<html>Reviews:</html>')
        if desktop_session == 'ubuntu':
            print('--page--cleared--')
        else:
            try:
                QtCore.QTimer.singleShot(2000, partial(self.delete_web_instance, self.web))
            except Exception as e:
                print(e)
            print('--web closed--')
            
        self.tab_2.hide()
        self.list1.show()
        self.list2.show()
        self.label.show()
        self.label_new.show()
        self.text.show()
        self.frame1.show()
        
    def delete_web_instance(self, web):
        if web:
            web.close()
            web.deleteLater()
            self.web = None
        
    def webHide(self):
        if self.mpvplayer_val.processId() > 0:
            if self.tab_2.isHidden():
                self.tab_2.show()
                self.list1.hide()
                self.list2.hide()
                self.label.hide()
                self.label_new.hide()
                self.text.hide()
            else:
                self.tab_2.hide()
                if site == 'Music':
                    self.list2.show()
                    self.label.show()
                    self.label_new.show()
                    self.text.show()
        else:
            self.showHideBrowser()
            
    def togglePlaylist(self):
        if self.list2.isHidden():
            self.list2.show()
            #self.goto_epn.show()
        else:
            self.list2.hide()
            self.goto_epn.hide()
            
    def dockShowHide(self):
        if self.dockWidget_3.isHidden():
            self.dockWidget_3.show()
            self.btn1.setFocus()
        else:
            self.dockWidget_3.hide()
            if self.mpvplayer_val.processId() > 0:
                self.tab_5.setFocus()
            elif not self.tab_6.isHidden():
                self.tab_6.setFocus()
            else:
                self.list1.setFocus()
        
    def showHideBrowser(self):
        global view_layout
        if self.tab_2.isHidden():
            for widget in self.widget_dict:
                self.browser_dict_widget.update(
                    {widget:self.widget_dict[widget].isHidden()}
                    )
            for i in self.browser_dict_widget:
                status = self.browser_dict_widget[i]
                if not status:
                    self.widget_dict[i].hide()
            self.tab_2.show()
        else:
            self.tab_2.hide()
            for i in self.browser_dict_widget:
                status = self.browser_dict_widget[i]
                if not status:
                    self.widget_dict[i].show()
            
        self.frame1.show()
            
    def IconView(self):
        global total_till, browse_cnt
        global view_layout, thumbnail_indicator, total_till_epn
        
        if self.list_poster is not None:
            self.list_poster.title_clicked = False
        if self.list1.count() == 0:
            return 0
        self.view_mode = 'thumbnail'
        thumbnail_indicator[:]=[]
        self.scrollArea1.hide()
        self.scrollArea.show()
        browse_cnt=0
        num = self.list2.currentRow()
        i = 0
        if total_till > 0:
            while(i<total_till):
                t = "self.label_"+str(i)+".deleteLater()"
                exec (t)
                i = i+1
            total_till = 0
        i = 0
        if total_till_epn > 0:
            while(i<total_till_epn):
                t = "self.label_epn_"+str(i)+".deleteLater()"
                exec (t)
                i = i+1
            total_till_epn = 0
            
        if self.tab_6.isHidden():
            self.list1.hide()
            self.list2.hide()
            self.tab_5.hide()
            self.label.hide()
            self.label_new.hide()
            self.text.hide()
            self.frame.hide()
            self.frame1.hide()
            self.goto_epn.hide()
            if ui.auto_hide_dock:
                self.dockWidget_3.hide()
            self.tab_6.show()
            
            self.next_page('deleted')
            self.tab_2.hide()
        else:
            self.tab_6.hide()
            self.list1.show()
            self.list2.show()
            self.label.show()
            self.label_new.show()
            self.list1.setFocus()
            self.text.show()
            self.frame1.show()
    
    def take_to_thumbnail(self, row=None, mode=None, focus=None):
        if not row:
            if mode == 'epn' and self.list2.currentItem():
                row = self.list2.currentRow()
            elif mode == 'title' and self.list1.currentItem():
                row = self.list1.currentRow()
            else:
                row = -1
        if row >= 0:
            if mode == 'title':
                p1 = "self.label_"+str(row)+".y()"
                yy = eval(p1)
                self.scrollArea.verticalScrollBar().setValue(yy -10)
                if focus:
                    p1 = "self.label_"+str(row)+".setFocus()"
                    exec(p1)
                new_cnt = row+self.list1.count()
                p1 = "self.label_{0}".format(new_cnt)
                label_number = eval(p1)
                label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
                txt = label_number.toPlainText()
                label_number.setText(txt)
                label_number.setAlignment(QtCore.Qt.AlignCenter)
                self.labelFrame2.setText(txt)
                self.list1.setCurrentRow(row)
            elif mode == 'epn':
                p1 = "self.label_epn_"+str(row)+".y()"
                yy = eval(p1)
                self.scrollArea1.verticalScrollBar().setValue(yy -10)
                if focus:
                    p1 = "self.label_epn_"+str(row)+".setFocus()"
                    exec(p1)
                new_cnt = row+self.list2.count()
                p1 = "self.label_epn_{0}".format(new_cnt)
                label_number = eval(p1)
                label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
                txt = label_number.toPlainText()
                label_number.setText(txt)
                label_number.setAlignment(QtCore.Qt.AlignCenter)
                self.labelFrame2.setText(txt)
            QtWidgets.QApplication.processEvents()
    
    def IconViewEpn(self, start=None, mode=None):
        global total_till, browse_cnt
        global view_layout, iconv_r, thumbnail_indicator
        global site, total_till_epn
        if isinstance(mode, int):
            if mode == 3:
                if self.view_mode == 'list':
                    self.view_mode = 'thumbnail'
            elif mode == 1:
                self.view_mode = 'thumbnail'
            else:
                self.view_mode = 'thumbnail_light'
        if self.list2.count() == 0:
            return 0
        else:
            self.epn_list_count.append(self.list2.count())
        thumbnail_indicator[:]=[]
        self.scrollArea.hide()
        num = self.list2.currentRow()
        if num < 0:
            num = 0
        i = 0
        print(self.view_mode, site, '--viewmode--')
        if self.tab_6.isHidden() or self.view_mode in ["thumbnail", 'thumbnail_light'] or start:
            self.list1.hide()
            self.list2.hide()
            self.tab_5.hide()
            self.label.hide()
            self.label_new.hide()
            self.text.hide()
            self.frame.hide()
            #self.frame1.hide()
            self.goto_epn.hide()
            if self.view_mode == 'thumbnail_light':
                if not self.list_poster.isHidden():
                    self.list_poster.hide()
                if start:
                    self.list_poster.title_clicked = True
            if ui.auto_hide_dock:
                self.dockWidget_3.hide()
            if self.mpvplayer_val.processId()>0:
                self.tab_5.show()
                self.frame1.show()
                iconv_r = 1
                self.gridLayout.addWidget(self.tab_6, 0, 2, 1, 1)
            else:
                self.gridLayout.addWidget(self.tab_6, 0, 1, 1, 1)
            self.tab_6.show()
            self.thumbnailEpn()
            self.tab_2.hide()
            QtWidgets.QApplication.processEvents()
            try:
                if self.list2.currentItem():
                    r = self.list2.currentRow()
                    self.take_to_thumbnail(row=r, mode='epn', focus=True)
            except Exception as err:
                print(err)
        else:
            self.tab_6.hide()
            self.list1.show()
            self.list2.show()
            self.label.show()
            self.label_new.show()
            self.list1.setFocus()
            self.text.show()
            self.frame1.show()
        if start is True:
            time.sleep(0.01)
            self.thumbnail_label_update_epn()
            try:
                if self.list2.currentItem():
                    r = self.list2.currentRow()
                    self.take_to_thumbnail(row=r, mode='epn', focus=True)
            except Exception as err:
                print(err)
            QtWidgets.QApplication.processEvents()
            
    def fullscreenToggle(self):
        if not MainWindow.isFullScreen():
            #self.dockWidget_4.close()
            self.dockWidget_3.hide()
            MainWindow.showFullScreen()
            self.force_fs = True
        else:
            self.dockWidget_3.show()
            MainWindow.showNormal()
            MainWindow.showMaximized()
            self.force_fs = False
    
    
    def shuffleList(self):
        global pre_opt, opt, hdr, site, embed
        global finalUrlFound
        global total_till, browse_cnt
        global bookmark
        browse_cnt=0
        embed = 0
        n = []
        m = []
            
        if site == "Music" or site=="Video":
            if self.original_path_name:
                tmp = self.original_path_name[0]
                if '/' in tmp:
                    p = random.sample(self.original_path_name, len(self.original_path_name))
                    self.original_path_name[:]=[]
                    self.original_path_name = p
                    
                    for i in p:
                        if site=="Video":
                            m.append(i.split('	')[0])
                        else:
                            #m.append(i.split('/')[-1])
                            m.append(os.path.basename(i))
                else:
                    for i in range(self.list1.count()):
                        n.append(str(self.list1.item(i).text()))
                    m = random.sample(n, len(n))
        else:
            m = random.sample(self.original_path_name, len(self.original_path_name))
            self.original_path_name[:]=[]
            self.original_path_name = m
            
        if m and not bookmark: 
            self.label.clear()
            self.line.clear()
            self.list1.clear()
            self.list2.clear()
            self.text.clear()
            for i in m:
                if site.lower() == 'video' or site.lower() == 'music':
                    pass
                else:
                    if '	' in i:
                        i = i.split('	')[0]
                self.list1.addItem(i)
        opt = "Random"
        
    def sortList(self):
        global pre_opt, opt, hdr, site, embed
        global finalUrlFound
        global total_till
        global browse_cnt, bookmark
        
        browse_cnt=0
        tmp_arr = []
        embed = 0
        n = []
        m =[]
        if site == "Music" or site == "Video":
            if self.original_path_name:
                tmp = self.original_path_name[0]
                if '/' in tmp:
                    if site == "Video":
                        p = sorted(
                            self.original_path_name, 
                            key = lambda x: x.split('	')[0].lower()
                            )
                    else:
                        p = sorted(
                            self.original_path_name, 
                            key = lambda x: os.path.basename(x).lower()
                            )
                    self.original_path_name[:]=[]
                    self.original_path_name = p
                    for i in p:
                        if site == "Video":
                            m.append(i.split('	')[0])
                        else:
                            m.append(os.path.basename(i))
                else:
                    for i in range(self.list1.count()):
                        n.append(str(self.list1.item(i).text()))
                    m = list(set(n))
                    m.sort()
        else:
            self.original_path_name.sort()
            m = self.original_path_name
        
        if m and not bookmark:
            self.label.clear()
            self.line.clear()
            self.list1.clear()
            self.list2.clear()
            self.text.clear()
            for i in m:
                if site.lower() == 'music' or site.lower() == 'video':
                    pass
                else:
                    if '	' in i:
                        i = i.split('	')[0]
                self.list1.addItem(i)
        
    def deleteArtwork(self):
            global name
            thumb = os.path.join(TMPDIR, name+'.jpg')
            self.label.clear()
            if os.path.isfile(thumb):
                    os.remove(thumb)
                    
    def get_current_directory(self):
        global name, site, opt, pre_opt, home, siteName
        print(site)
        print(opt)
        print(pre_opt)
        logger.info(name)
        if '/' in name:
            name = name.replace('/', '-')
        path = ""
        
        if (opt == "History" and (site.lower()!= 'video' 
                and site.lower()!= 'music' and site.lower()!= 'local')):
            if siteName:
                path= os.path.join(home, 'History', site, siteName, name)
            else:
                path = os.path.join(home, 'History', site, name)
        elif (site == "Local" or site == "Video"):
            path = os.path.join(home, 'Local', name)
        elif (site == "Music"):
            logger.info(name)
            try:
                r = self.list2.currentRow()
                nm = self.epn_arr_list[r].split('	')[2]
            except:
                nm = ""
            if nm:
                path = os.path.join(home, 'Music', 'Artist', nm)
            logger.info("current directory is {0} and name is {1}".format(path, nm))
        logger.info("current directory is {0} and name is {1}".format(path, name))
        return path
    
    def metadata_copy(self, dir_path, picn, thumbnail=None, mode=None,
                      img_opt=None, site=None):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if mode == 'img' and os.path.isfile(picn) and thumbnail:
            self.image_fit_option(picn, thumbnail, fit_size=450)
            shutil.copy(picn, os.path.join(dir_path, 'poster.jpg'))
            if os.path.exists(thumbnail):
                self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                shutil.copy(thumbnail, os.path.join(dir_path, 'thumbnail.jpg'))
            self.videoImage(
                picn, os.path.join(dir_path, 'thumbnail.jpg'),
                os.path.join(dir_path, 'fanart.jpg'), '')
        elif mode == 'fanart' and os.path.isfile(picn) and img_opt:
            self.image_fit_option(picn, picn, fit_size=img_opt)
            shutil.copy(picn, os.path.join(dir_path, 'original-fanart.jpg'))
            shutil.copy(picn, os.path.join(dir_path, 'fanart.jpg'))
            self.videoImage(
                picn, os.path.join(dir_path, 'thumbnail.jpg'),
                os.path.join(dir_path, 'fanart.jpg'), '')
        elif mode == 'summary' and os.path.isfile(picn):
            if site == 'Music':
                file_path = os.path.join(dir_path, 'bio.txt')
            else:
                file_path = os.path.join(dir_path, 'summary.txt')
            sumry = picn
            shutil.copy(sumry, file_path)
    
    
    def get_metadata_location(self, site, opt, siteName, new_name, mode=None,
                              copy_sum=None, find_name=None):
        picn = ''
        img_opt = ''
        thumbnail = ''
        sumry = ''
        dir_path = None
        if not new_name:
            new_name = name
        if '/' in new_name:
            new_name = new_name.replace('/', '-')
        if site == 'Music':
            try:
                if not new_name or find_name:
                    if str(self.list3.currentItem().text()) == "Artist":
                        new_name = self.list1.currentItem().text()
                    else:
                        r = self.list2.currentRow()
                        new_name = self.epn_arr_list[r].split('	')[2]
                        new_name = new_name.replace('"', '')
            except Exception as err:
                print(err, '--5474--')
        
        if new_name and mode == 'img':
            picn = os.path.join(TMPDIR, new_name+'.jpg')
        elif new_name and mode == 'fanart':
            picn = os.path.join(TMPDIR, new_name+'-fanart.jpg')
            if (not os.path.exists(picn) or ((os.path.exists(picn) 
                    and not os.stat(picn).st_size))):
                picn = os.path.join(TMPDIR, new_name+'.jpg')
            if self.image_fit_option_val in range(1, 11):
                if self.image_fit_option_val != 6:
                    img_opt = self.image_fit_option_val
                else:
                    img_opt = 1
            else:
                img_opt = 1
        elif new_name and mode == 'summary':
            if site == 'Music':
                sumry = os.path.join(TMPDIR, new_name+'-bio.txt')
            else:
                sumry = os.path.join(TMPDIR, new_name+'-summary.txt')
            picn = sumry
            if copy_sum and sumry:
                write_files(sumry, copy_sum, False)
                
        logger.info('{0}--copyimg--'.format(picn))
        
        if not os.path.isfile(picn) and mode != 'summary':
            picn = os.path.join(home, 'default.jpg')
        
        if (os.path.isfile(picn) and opt == "History" 
                and (site.lower()!= 'video' and site.lower()!= 'music' 
                and site.lower()!= 'local') and new_name):
            if siteName and new_name:
                dir_path = os.path.join(home, 'History', site, siteName, new_name)
            else:
                dir_path = os.path.join(home, 'History', site, new_name)
        elif os.path.isfile(picn) and (site == "Local" or site == "Video") and new_name:
            dir_path = os.path.join(home, 'Local', new_name)
        elif site == "Music" and new_name:
            logger.info('nm={0}'.format(new_name))
            dir_path = os.path.join(home, 'Music', 'Artist', new_name)
            if mode == 'fanart':
                picn = os.path.join(TMPDIR, new_name+'.jpg')
        
        if dir_path and new_name and mode == 'img' :
            thumbnail = os.path.join(TMPDIR, new_name+'-thumbnail.jpg')
            logger.info('picn={0}-thumbnail={1}'.format(picn, thumbnail))
        
        return (dir_path, thumbnail, picn, img_opt)
        
    def copyImg(self, new_name=None):
        global name, site, opt, pre_opt, home, siteName
        
        dir_path, thumbnail, picn, img_opt = self.get_metadata_location(
            site, opt, siteName, new_name, mode='img'
            )
        
        if dir_path and os.path.exists(picn):
             self.metadata_copy(dir_path, picn, thumbnail, mode='img')
             
    def copyFanart(self, new_name=None):
        global name, site, opt, pre_opt, home, siteName
        
        dir_path, thumbnail, picn, img_opt = self.get_metadata_location(
            site, opt, siteName, new_name, mode='fanart'
            )
        
        if dir_path and os.path.exists(picn):
            self.metadata_copy(dir_path, picn, mode='fanart', img_opt=img_opt)
                    
                
    def copySummary(self, copy_sum=None, new_name=None, find_name=None):
        global name, site, opt, pre_opt, home, siteName
        
        dir_path, thumbnail, picn, img_opt = self.get_metadata_location(
            site, opt, siteName, new_name, mode='summary',
            copy_sum=copy_sum, find_name=find_name
            )
        sumry = picn
        if dir_path and os.path.exists(sumry):
            self.metadata_copy(dir_path, sumry, mode='summary', site=site)
        
        if os.path.exists(sumry):
            txt = open_files(sumry, False)
            logger.info('{0}--copy-summary--'.format(txt))
            self.text.setText(txt)
    
    def showImage(self):
        global name
        thumb = os.path.join(TMPDIR, name+'.jpg')
        logger.info(thumb)
        if os.path.exists(thumb):
            Image.open(thumb).show()
    
    def posterfound_new(
            self, name, site=None, url=None, copy_poster=None, copy_fanart=None, 
            copy_summary=None, direct_url=None, use_search=None, get_all=None,
            video_dir=None):
        
        logger.info('{0}-{1}-{2}--posterfound--new--'.format(url, direct_url, name))
        self.posterfound_arr.append(FindPosterThread(
            self, logger, TMPDIR, name, url, direct_url, copy_fanart,
            copy_poster, copy_summary, use_search, video_dir))
        if get_all:
            self.posterfound_arr[len(self.posterfound_arr)-1].finished.connect(
                lambda x=0: self.posterfound_thread_all_finished(name, url,
                    direct_url, copy_fanart, copy_poster, copy_summary, use_search))
        else:
            self.posterfound_arr[len(self.posterfound_arr)-1].finished.connect(
                lambda x=0: self.posterfound_thread_finished(name, copy_fanart, 
                copy_poster, copy_summary))
        
        self.posterfound_arr[len(self.posterfound_arr)-1].start()
            
            
    def posterfound_thread_finished(self, name, copy_fan, copy_poster, copy_summary):
        logger.info('{0}-{1}-{2}--{3}--posterfound_thread_finished--'.format(name, copy_fan, copy_poster, copy_summary))
        copy_sum = 'Not Available'
        if copy_summary:
            copy_sum = self.text.toPlainText().replace('Wait..Downloading Poster and Fanart..\n\n', '')
        if copy_poster:
            self.copyImg(new_name=name)
        if copy_fan:
            self.copyFanart(new_name=name)
        if copy_summary:
            self.text.setText(copy_sum)
    
    def posterfound_thread_all_finished(
            self, name, url, direct_url, copy_fanart, copy_poster,
            copy_summary, use_search):
        self.posterfind_batch += 1
        logger.info('{0}-{1}-{2}--{3}--posterfound_thread_finished--'.format(name, copy_fanart, copy_poster, copy_summary))
        copy_sum = 'Not Available'
        if copy_summary:
            copy_sum = self.text.toPlainText().replace('Wait..Downloading Poster and Fanart..\n\n', '')
        if copy_poster:
            self.copyImg(new_name=name)
        if copy_fanart:
            self.copyFanart(new_name=name)
        if copy_summary:
            self.text.setText(copy_sum)
        range_val = 3
        if (self.posterfind_batch == self.poster_count_start) or (self.posterfind_batch % range_val == 0):
            index = self.posterfind_batch
            for i in range(0, range_val):
                if index == 1:
                    row = i+1
                    if row == range_val:
                        break
                else:
                    row = index + i
                if row < len(self.original_path_name):
                    nm = self.get_title_name(row)
                    video_dir = None
                    if site.lower() == 'video':
                        video_dir = ui.original_path_name[row].split('\t')[-1]
                    elif site.lower() == 'playlists' or site.lower() == 'none' or site.lower() == 'music':
                        pass
                    else:
                        video_dir = ui.original_path_name[row]
                    self.posterfound_new(
                        name=nm, site=site, url=False, copy_poster=True, copy_fanart=True, 
                        copy_summary=True, direct_url=False, use_search=use_search, get_all=True,
                        video_dir=video_dir)
    
    def get_final_link(self, url, quality, ytdl_path, loger, nm, hdr):
        logger.info('{0}-{1}-{2}--{3}--get-final--link--'.format(url, quality, ytdl_path, nm))
        self.ytdl_arr.append(YTdlThread(self, logger, url, quality, ytdl_path, loger, nm, hdr))
        length = len(self.ytdl_arr) - 1
        self.ytdl_arr[len(self.ytdl_arr)-1].finished.connect(lambda x=0: self.got_final_link(length))
        self.ytdl_arr[len(self.ytdl_arr)-1].start()
        self.tab_5.show()
        self.frame1.show()
        self.tab_2.setMaximumWidth(self.width_allowed+50)
        self.btnWebReviews_search.hide()
        #self.progressEpn.setFormat('Wait....')
        #QtWidgets.QApplication.processEvents()
    
    def got_final_link(self, length):
        if length == len(self.ytdl_arr) - 1:
            del self.ytdl_arr[length]
            logger.info('--finished--getting link--')
            logger.info('arr: {0}---'.format(self.ytdl_arr))
        elif length < len(self.ytdl_arr) - 1:
            self.ytdl_arr[length] = None
            
        if self.ytdl_arr:
            empty = True
            for i in self.ytdl_arr:
                if i is not None:
                    empty = False
            if empty:
                print('empty arr')
                self.ytdl_arr[:] = []
        else:
            logger.info('--13898--link-fetched-properly')
    
    def chkMirrorTwo(self):
        global site, mirrorNo, siteName
        mirrorNo = 2
        if siteName:
            self.epnfound()
        mirrorNo = 1
            
    def chkMirrorThree(self):
        global site, mirrorNo, siteName
        mirrorNo = 3
        if siteName:
            self.epnfound()
        mirrorNo = 1		
        
    def chkMirrorDefault(self):
        global site, mirrorNo, siteName
        mirrorNo = 1
        if siteName:
            self.epnfound()
            
    def setPreOpt(self, option_val=None):
        global pre_opt, opt, hdr, site, insidePreopt, home
        global name, bookmark, status, total_till, browse_cnt
        global siteName
        
        insidePreopt = 1
        var = (self.btn1.currentText())
        if var == "Select":
            return 0
        if bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt')):
            opt = "History"
            line_a = open_files(os.path.join(home, 'Bookmark', status+'.txt'), True)
            self.list1.clear()
            self.original_path_name[:] = []
            for i in line_a:
                i = i.replace('\n', '')
                if i:
                    j = i.split(':')
                    logger.info(j)
                    if j[0] == "Local":
                        t = j[5].split('@')[-1]
                    else:
                        t = j[5]
                    if '	' in t:
                        t = t.split('	')[0]
                    self.list1.addItem(t)
                    self.original_path_name.append(j[5])
        else:
            if option_val:
                if option_val == 'fromtitlelist':
                    opt = 'History'
                else:
                    opt = option_val
            else:
                opt = "History"
            print(site, option_val, ':setpreopt:')
            if site.lower() == 'myserver' and option_val == 'fromtitlelist':
                self.newoptions('history+offline')
            else:
                self.newoptions(opt.lower())
                
    def mark_video_list(self, mark_val, row):
        global site
        if site.lower() == "video":
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if mark_val == 'mark' and i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'unmark' and not i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'mark' and not i.startswith(self.check_symbol):
                    url1 = self.epn_arr_list[row].split('	')[1]
                    item.setText(self.check_symbol+i)
                    self.media_data.update_video_count('mark', url1, rownum=row)
                elif mark_val == 'unmark' and i.startswith(self.check_symbol):
                    url1 = self.epn_arr_list[row].split('	')[1]
                    i = i[1:]
                    item.setText(i)
                    self.media_data.update_video_count('unmark', url1, rownum=row)
                self.list2.setCurrentRow(row)
                
    def update_playlist_file(self, file_path):
        if os.path.exists(file_path):
            write_files(file_path, self.epn_arr_list, line_by_line=True)
            
    def mark_playlist(self, mark_val, row):
        global site, home
        music_pl = False
        if site == 'music':
            if self.list3.currentItem():
                if self.list3.currentItem().text().lower() == 'playlist':
                    music_pl = True
                    
        if site.lower() == "playlists" or music_pl:
            item = self.list2.item(row)
            file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
            if item:
                i = str(self.list2.item(row).text())
                if mark_val == 'mark' and i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'unmark' and not i.startswith(self.check_symbol):
                    pass
                elif mark_val == 'mark' and not i.startswith(self.check_symbol):
                    item.setText(self.check_symbol+i)
                    self.epn_arr_list[row] = '#'+self.epn_arr_list[row]
                    self.list2.setCurrentRow(row)
                    self.update_playlist_file(file_path)
                elif mark_val == 'unmark' and i.startswith(self.check_symbol):
                    i = i[1:]
                    item.setText(i)
                    self.epn_arr_list[row] = self.epn_arr_list[row].replace('#', '', 1)
                    self.list2.setCurrentRow(row)
                    self.update_playlist_file(file_path)
                    
    def get_local_file_ep_name(self):
        global site, name, siteName
        file_path = ''
        if site.lower() == "local":
            file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
        elif siteName:
            file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
        elif site.lower() == 'playlists' and self.list1.currentItem():
            file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
        elif site.lower() == 'music' and self.list3.currentItem():
            if self.list1.currentItem():
                file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
        elif site.lower() != 'video':
            file_path = os.path.join(home, 'History', site, name, 'Ep.txt')
        return file_path
        
    def mark_addons_history_list(self, mark_val, row):
        global opt, site, home, site, name, siteName, finalUrlFound
        global refererNeeded, path_Local_Dir
        
        if (opt == "History" and (site.lower() !="video" 
                and site.lower()!= 'music' and site.lower()!= 'playlists' 
                and site.lower()!= 'none')):
            file_change = False
            item = self.list2.item(row)
            if item:
                if '	' in self.epn_arr_list[row]:
                    if self.epn_arr_list[row].startswith('#') and mark_val == 'unmark':
                        n_epn = self.epn_arr_list[row].replace('#', '', 1)
                    elif not self.epn_arr_list[row].startswith('#') and mark_val == 'mark':
                        n_epn = '#'+self.epn_arr_list[row]
                    else:
                        return 0
                else:
                    epn = self.epn_arr_list[row]
                    if site != "Local":
                        if epn.startswith('#') and mark_val == 'unmark':
                            n_epn = epn[1:]
                            epn = epn
                        elif not epn.startswith('#') and mark_val == 'mark':
                            n_epn = '#' + epn
                            epn = epn
                        else:
                            return 0
                        
                file_path = self.get_local_file_ep_name()
                txt = item.text()
                
                if txt.startswith(self.check_symbol) and mark_val == 'unmark':
                    txt = txt[1:]
                    self.list2.item(row).setText(txt)
                    file_change = True
                elif not txt.startswith(self.check_symbol) and mark_val == 'mark':
                    self.list2.item(row).setText(self.check_symbol+txt)
                    file_change = True
                    
                if os.path.exists(file_path) and file_change:
                    lines = open_files(file_path, True)
                    if finalUrlFound == True:
                        if lines[row].startswith('#') and mark_val == 'unmark':
                            lines[row]=lines[row].replace('#', '', 1)
                        elif not lines[row].startswith('#') and mark_val == 'mark':
                            lines[row] = '#'+lines[row]
                    else:
                        if "\n" in lines[row]:
                            lines[row] = n_epn + "\n"
                            logger.info(lines[row])
                        else:
                            lines[row] = n_epn
                    
                    self.epn_arr_list[:]=[]
                    for i in lines:
                        i = i.strip()
                        self.epn_arr_list.append(i)
                    write_files(file_path, lines, line_by_line=True)
                self.list2.setCurrentRow(row)
        
    def watchToggle(self):
        global site, epn, epn_goto, pre_opt, home, path_Local_Dir
        global opt, siteName, finalUrlFound, refererNeeded
        if (opt == "History" and (site.lower() !="video" 
                    and site.lower()!= 'music' and site.lower()!= 'playlists' 
                    and site.lower()!= 'none')):
                row = self.list2.currentRow()
                item = self.list2.item(row)
                if item:
                    i = (self.list2.item(row).text())
                    if i.startswith(self.check_symbol):
                        self.mark_addons_history_list('unmark', row)
                    else:
                        self.mark_addons_history_list('mark', row)
        elif site.lower() == "playlists":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if i.startswith(self.check_symbol):
                    self.mark_playlist('unmark', row)
                else:
                    self.mark_playlist('mark', row)
        elif site.lower() == "video":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                i = self.list2.item(row).text()
                if i.startswith(self.check_symbol):
                    self.mark_video_list('unmark', row)
                else:
                    self.mark_video_list('mark', row)
                #title_row = self.list1.currentRow()
                #dir_path, file_path = os.path.split(self.original_path_name[title_row].split('\t')[-1])
                #logger.info('--------7790----{0}'.format(dir_path))
    
    
    def search_list4_options(self):
        global opt, site, name, pre_opt, bookmark
        
        r = self.list4.currentRow()
        item = self.list4.item(r)
        if item:
            tmp = str(self.list4.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list1.setCurrentRow(num)
            self.listfound()
            self.list1.setFocus()
            self.list4.hide()
            self.go_page.clear()
            
    def search_list5_options(self):
        global opt, site, name, pre_opt, bookmark
        r = self.list5.currentRow()
        item = self.list5.item(r)
        if item:
            tmp = str(self.list5.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list2.setCurrentRow(num)
            self.epnfound()
            self.list5.setFocus()
            self.goto_epn_filter_txt.clear()
            
    def history_highlight(self):
        global opt, site, name, pre_opt, bookmark
        global category, audio_id, sub_id
        audio_id = 'auto'
        sub_id = 'auto'
        self.title_list_changed = True
        if site!= "Music":
            self.subtitle_track.setText("SUB")
            self.audio_track.setText("A/V")
        if (opt == "History" or site == "Music" or site == "Video" 
                or site == "PlayLists") and site != 'MyServer':
            self.listfound()
        elif (site.lower() == 'myserver' and opt.lower() != 'history' 
                and opt.lower() != 'login' and opt.lower() != 'discover'):
            name_now = ''
            if self.list1.currentItem() and self.myserver_threads_count <= 10:
                cur_row = self.list1.currentRow()
                new_name_with_info = self.original_path_name[cur_row].strip()
                extra_info = ''
                if '	' in new_name_with_info:
                    name_now = new_name_with_info.split('	')[0]
                    extra_info = new_name_with_info.split('	')[1]
                else:
                    name_now = new_name_with_info
                self.newlistfound_thread_box.append(
                    GetServerEpisodeInfo(
                        self, logger, site, opt, siteName,
                        self.video_local_stream, name_now, extra_info,
                        category,from_cache=False
                    ))
                length = len(self.newlistfound_thread_box)-1
                self.newlistfound_thread_box[length].finished.connect(
                    partial(self.finished_newlistfound, length)
                    )
                self.newlistfound_thread_box[length].start()
                self.myserver_threads_count += 1
        else:
            self.rawlist_highlight()
        if self.series_info_dict.get(name):
            del self.series_info_dict[name]
            
    def finished_newlistfound(self, length):
        if self.myserver_threads_count:
            self.myserver_threads_count -= 1
        logger.info('{0} thread remaining'.format(self.myserver_threads_count))
        logger.info('completed {}'.format(length))
        self.update_list2()
        
    def search_highlight(self):
        global opt, site, name, pre_opt, bookmark
        r = self.list4.currentRow()
        item = self.list4.item(r)
        if item:
            tmp = str(self.list4.currentItem().text())
            tmp1 = tmp.split(':')[0]
            num = int(tmp1)
            self.list1.setCurrentRow(num)
            if opt == "History" or site == "Music":
                self.listfound()
            else:
                self.rawlist_highlight()
    
    def update_list2(self, epn_arr=None):
        global site
        update_pl_thumb = True
        
        if not self.epn_arr_list and epn_arr is None:
            pass
        else:
            if self.list2.isHidden():
                update_pl_thumb = False
            if epn_arr:
                new_epn_arr = epn_arr.copy()
            else:
                new_epn_arr = self.epn_arr_list
            print(update_pl_thumb, 'update_playlist_thumb')
            row = self.list2.currentRow()
            self.list2.clear()
            for i in new_epn_arr:
                i = i.strip()
                if '	' in i:
                    i = i.split('	')[0]
                i = i.replace('_', ' ')
                if i.startswith('#'):
                    i = i.replace('#', self.check_symbol, 1)
                self.list2.addItem(i)
            self.list2.setCurrentRow(row)
            if self.list1.currentItem():
                title_list = self.list1.currentItem().text()
            else:
                title_list = 'NONE'
            new_thread = SetThumbnail(self, logger, new_epn_arr, update_pl_thumb, title_list)
            self.set_thumbnail_thread_list.append(new_thread)
            self.set_thumbnail_thread_list[len(self.set_thumbnail_thread_list) - 1].finished.connect(
                partial(self.thumbnail_thread_finished, len(self.set_thumbnail_thread_list) - 1))
            self.set_thumbnail_thread_list[len(self.set_thumbnail_thread_list) - 1].start()
            
    def thumbnail_thread_finished(self, k):
        logger.debug('Title No {0} thumbnail finished'.format(k))
        txt_str = str(self.list1.count())+'/'+str(self.list2.count())
        self.page_number.setText(txt_str)
        m = self.set_thumbnail_thread_list[k]
        self.set_thumbnail_thread_list[k] = None
        del m
        
        
    def set_icon_list2(self, epnArr, list_thumb, update_pl):
        for k in range(len(epnArr)):
            if list_thumb and update_pl:
                try:
                    icon_name = self.get_thumbnail_image_path(k, epnArr[k])
                    icon_new_pixel = self.create_new_image_pixel(icon_name, 128)
                    if os.path.exists(icon_new_pixel):
                        try:
                            self.list2.item(k).setIcon(QtGui.QIcon(icon_new_pixel))
                        except:
                            pass
                except Exception as e:
                    print(e)
        txt_str = str(self.list1.count())+'/'+str(self.list2.count())
        self.page_number.setText(txt_str)
        
    def mark_History(self):
        global opt, siteName, site, name, home
        file_path = ""
        row = self.list2.currentRow()
        if opt == "History" and site != "PlayLists":
            if siteName:
                if os.path.exists(os.path.join(home, 'History', site, siteName, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, name, 'Ep.txt')):
                    file_path = os.path.join(home, 'History', site, name, 'Ep.txt')

            if os.path.exists(file_path):
                lines = open_files(file_path, True)
                if '#' in self.epn_arr_list[row]:
                    n_epn = self.epn_arr_list[row]
                else:
                    n_epn = '#'+self.epn_arr_list[row]
                if '\n' in lines[row]:
                    lines[row] = n_epn + '\n'
                else:
                    lines[row]= n_epn
                self.epn_arr_list[:]=[]
                for i in lines:
                    i = i.strip()
                    self.epn_arr_list.append(i)
                write_files(file_path, lines, line_by_line=True)
            self.update_list2()
        
    def deleteHistory(self):
        global opt, site, name, pre_opt, home, bookmark, status, siteName
        
        if self.list1.currentItem():
            epn = self.list1.currentItem().text()
            row = self.list1.currentRow()
        else:
            return 0
        nepn = str(epn) + "\n"
        replc = ""
    
        if site == 'None':
            return 0
            
        if (bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt'))):
            file_path = os.path.join(home, 'Bookmark', status+'.txt')
            if self.list1.currentItem() and os.path.isfile(file_path):
                row = self.list1.currentRow()
                item = self.list1.item(row)
                lines = open_files(file_path, True)
                lines = [i.strip() for i in lines if i.strip()]
                if row < len(lines):
                    del lines[row]
                    write_files(file_path, lines, line_by_line=True)
                    self.list1.takeItem(row)
                    del item
                    if row < self.list1.count():
                        self.list1.setCurrentRow(row)
                    else:
                        self.list1.setCurrentRow(self.list1.count()-1)
        elif opt == "History" and not bookmark:
            file_path = ''
            if siteName:
                if os.path.exists(os.path.join(home, 'History', site, siteName, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
            else:
                if os.path.exists(os.path.join(home, 'History', site, 'history.txt')):
                    file_path = os.path.join(home, 'History', site, 'history.txt')
            if not file_path:
                return 0
            row = self.list1.currentRow()
            item = self.list1.item(row)
            nam = str(item.text())
            if item and nam:
                if self.epn_arr_list:
                    icon_name = self.get_thumbnail_image_path(0, self.epn_arr_list[0])
                    icon_dir_path, thumb_name = os.path.split(icon_name)
                    thumb_path = os.path.join(home, 'thumbnails')
                    thumbnail_server_path = os.path.join(home, 'thumbnails', 'thumbnail_server')
                    logger.info('{0}--thumbnail--path--'.format(icon_dir_path))
                    icon_dir_list = [thumb_path, thumbnail_server_path]
                    if icon_dir_path.startswith(thumb_path) and icon_dir_path not in icon_dir_list:
                        if os.path.exists(icon_dir_path):
                            shutil.rmtree(icon_dir_path)
                            logger.info('{0}--thumbnail--directory--deleted--'.format(icon_dir_path))
                    elif icon_dir_path in icon_dir_list:
                        logger.error('no thumbnails available')
                if siteName:
                    dir_name =os.path.join(home, 'History', site, siteName, nam)
                    logger.info(dir_name)
                else:
                    dir_name =os.path.join(home, 'History', site, nam)
                    logger.info(dir_name)
                if os.path.exists(dir_name):
                    shutil.rmtree(dir_name)
                    if self.video_local_stream:
                        torrent_file = dir_name+'.torrent'
                        if os.path.exists(torrent_file):
                            os.remove(torrent_file)
            if item:
                self.list1.takeItem(row)
                del item
                del self.original_path_name[row]
                length = self.list1.count() - 1
                write_files(file_path, self.original_path_name, line_by_line=True)
            
    def create_img_url(self, path):
        m = []
        img_url = ''
        if '/watch?' in path:
            a = path.split('?')[-1]
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
            img_url="https://i.ytimg.com/vi/"+d['v']+"/hqdefault.jpg"
        return img_url
    
    def epn_highlight(self):
        global home, site
        num = self.list2.currentRow()
        move_ahead = True
        if num < 0:
            move_ahead = False
        if self.list2.currentItem() and num < len(self.epn_arr_list) and move_ahead:
            epn_h = self.list2.currentItem().text()
            picn = self.get_thumbnail_image_path(num, self.epn_arr_list[num])
            label_name = 'label.'+os.path.basename(picn)
            path_thumb, new_title = os.path.split(picn)
            new_picn = os.path.join(path_thumb, label_name)
            if os.path.exists(picn):
                if not picn.endswith('default.jpg'):
                    if not os.path.exists(new_picn):
                        self.image_fit_option(picn, new_picn, fit_size=6, widget=self.label)
                    if os.path.isfile(new_picn):
                        self.label.setPixmap(QtGui.QPixmap(new_picn, "1"))
            txt_file = new_title.replace('.jpg', '.txt', 1)
            txt_path = os.path.join(path_thumb, txt_file)
            if os.path.isfile(txt_path):
                #logger.debug(txt_path)
                summary = open_files(txt_path, False)
                self.text.setText(summary)
                
    def thumbnail_generated(self, row=None, picn=None):
        try:
            if os.path.exists(picn):
                if not os.stat(picn).st_size:
                    picn = self.default_background
            if self.list_with_thumbnail:
                icon_new_pixel = self.create_new_image_pixel(picn, 128)
                if os.path.exists(icon_new_pixel):
                    try:
                        if row < self.list2.count():
                            self.list2.item(row).setIcon(QtGui.QIcon(icon_new_pixel))
                    except Exception as err:
                        print(err, '--6238--')
        except Exception as err:
            print(err, '--6240--')
        print("Thumbnail Process Ended")
        self.threadPoolthumb = self.threadPoolthumb[1:]
        length = len(self.threadPoolthumb)
        if length > 0:
            if not self.threadPoolthumb[0].isRunning():
                self.threadPoolthumb[0].start()
                
    def directepn(self):
        global epn, epn_goto
        epn_goto = 1
        epn = self.goto_epn.text()
        epn = re.sub("#", "", str(epn))
        self.epnfound()
    
    def preview(self):
        txt = str(self.chk.text())
        index = self.playback_engine.index(txt)
        index = (index + 1) % (len(self.playback_engine))
        txt = self.playback_engine[index]
        self.chk.setText(txt)
        self.player_val = txt
        if self.mpvplayer_val.processId()>0 and self.tab_2.isHidden() and self.player_val in ['mpv', 'mplayer']:
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False
            self.epnfound()
    
    def nextp(self, val):
        global opt, pgn, genre_num, site, mirrorNo, name
        global total_till, browse_cnt
    
        browse_cnt=0
        
        if val == "next":
            r = self.list3.currentRow()
        else:
            r = val
        item = self.list3.item(r)
        print(r)
        if item:
            opt_val = str(item.text())
            print(opt_val)
            if opt_val == "History" or opt_val == "Random" or opt_val == "List":
                return 0
        elif opt == 'Search':
            opt_val = 'Search'
        else:
            return 0
            
        print(opt_val, pgn, genre_num, name)
        
        self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
        
        try:
            code = 6
            pgn = pgn + 1
            if opt:
                m = self.site_var.getNextPage(opt_val, pgn, genre_num, self.search_term)
                self.list1.clear()
                self.original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    self.original_path_name.append(j)
        except:
            pass
        
    def backp(self, val):
        global opt, pgn, genre_num, mirrorNo, name
        self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
        if val == "back":
            r = self.list3.currentRow()
        else:
            r = val
        item = self.list3.item(r)
        if item:
            opt_val = str(item.text())
            if opt_val == "History" or opt_val == "Random" or opt_val == "List":
                return 0
        elif opt == 'Search':
            opt_val = 'Search'
        else:
            return 0
        
        try:
            pgn = pgn - 1
            if opt:
                m = self.site_var.getPrevPage(opt_val, pgn, genre_num, self.search_term)
                self.list1.clear()
                self.original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    self.original_path_name.append(j)
        except:
            pass
                    
    def gotopage(self):
        key = self.page_number.text()
        global opt, pgn, site
        if key and opt and site not in ['Video', 'Music', 'None', 'MyServer', 'PlayLists']:
            self.list1.verticalScrollBar().setValue(self.list1.verticalScrollBar().minimum())
            pgn = int(key)
            pgn = pgn - 1
            self.nextp(-1)
                
    def label_filter_list_update(self, item_index):
        global opt, site, bookmark, thumbnail_indicator, total_till
        global browse_cnt
        
        length = len(item_index)
        if not self.scrollArea.isHidden():
            length1 = self.list1.count()
        else:
            length1 = self.list2.count()
        
        print(length, '--length-filter-epn--')
        if item_index and not self.lock_process:
            i = 0
            if not self.scrollArea.isHidden():
                while(i < length):
                    if item_index[i] == 1:
                        t = "self.label_"+str(i)+".show()"
                        exec(t)
                        t = "self.label_"+str(i+length1)+".show()"
                        exec(t)
                    else:
                        t = "self.label_"+str(i)+".hide()"
                        exec(t)
                        t = "self.label_"+str(i+length1)+".hide()"
                        exec(t)
                    i = i+1
            else:
                while(i < length):
                    if item_index[i] == 1:
                        t = "self.label_epn_"+str(i)+".show()"
                        exec(t)
                        t = "self.label_epn_"+str(i+length1)+".show()"
                        exec(t)
                    else:
                        t = "self.label_epn_"+str(i)+".hide()"
                        exec(t)
                        t = "self.label_epn_"+str(i+length1)+".hide()"
                        exec(t)
                    i = i+1
            
    def filter_label_list(self):
        global opt, pgn, site, filter_on
        print("filter label")
        filter_on = 1
        row_history = []
        key = str(self.label_search.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        if not self.scrollArea.isHidden() or not self.list_poster.isHidden():
            if key:
                for i in range(self.list1.count()):
                    srch = str(self.list1.item(i).text()).lower()
                    if key in srch:
                        found_item.append(i)
                        found_item_index.append(1)
                    else:
                        found_item_index.append(0)
            else:
                for i in range(self.list1.count()):
                        found_item_index.append(1)
        else:
            if key:
                for i in range(self.list2.count()):
                    srch = str(self.list2.item(i).text()).lower()
                    if key in srch:
                        found_item.append(i)
                        found_item_index.append(1)
                    else:
                        found_item_index.append(0)
            else:
                for i in range(self.list2.count()):
                        found_item_index.append(1)
        if self.list_poster.isHidden():
            self.label_filter_list_update(found_item_index)
        else:
            if found_item_index:
                first_item = None
                for i, j in enumerate(found_item_index):
                    if j == 1:
                        if first_item is None:
                            first_item = i
                        self.list_poster.item(i).setHidden(False)
                    else:
                        self.list_poster.item(i).setHidden(True)
                if first_item is not None:
                    self.list_poster.setCurrentRow(first_item)
    
    def filter_list(self):
        global opt, pgn, site, filter_on
        print("filter label")
        filter_on = 1
        row_history = []
        key = str(self.go_page.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        
        if key:
            self.list4.show()
            for i in range(self.list1.count()):
                srch = str(self.list1.item(i).text())
                srch1 = srch.lower()
                if key in srch1:
                    found_item.append(str(i)+':'+srch)
                    
            length = len(found_item_index)
            self.list4.clear()
            for i in found_item:
                self.list4.addItem(i)
        else:
            self.list4.clear()
            self.list4.hide()
            self.list1.show()
                
    def filter_epn_list_txt(self):
        global opt, pgn, site, filter_on
        print("filter epn list")
        filter_on = 1
        row_history = []
        key = str(self.goto_epn_filter_txt.text()).lower()
        if not key:
            filter_on = 0
        found_item = []
        found_item_index = []
        print(opt)
        print(site)
        found_item_index[:]=[]
        
        if key:
            #self.list1.hide()
            self.list5.show()
            for i in range(len(self.epn_arr_list)):
                srch = self.epn_arr_list[i]
                
                srch1 = srch.lower()
                srch2 = str(self.list2.item(i).text())
                if key in srch1:
                    found_item.append(str(i)+':'+srch2)
                    
            length = len(found_item_index)
            self.list5.clear()
            for i in found_item:
                self.list5.addItem(i)
        else:
            self.list5.clear()
            self.list5.hide()
            self.list2.show()
            
    def ka(self):
        global site, home
        global total_till, browse_cnt
        global bookmark, total_till, thumbnail_indicator, genre_num
        global rfr_url, finalUrlFound, refererNeeded
        global siteName, audio_id, sub_id
        
        self.options_mode = 'legacy'
        self.music_playlist = False
        genre_num = 0
        audio_id = 'auto'
        sub_id = 'auto'
        self.audio_track.setText('A/V')
        self.subtitle_track.setText('SUB')
        #total_till = 0
        if self.site_var:
            del self.site_var
            self.site_var = ''
        self.label.clear()
        self.text.clear()
        if self.myserver_cache:
            self.myserver_cache.clear()
        self.original_path_name[:]=[]
        rfr_url = ""
        finalUrlFound = False
        refererNeeded = False
        site = str(self.btn1.currentText())
        siteName = ""
        if not self.btnAddon.isHidden():
            self.btnAddon.hide()
        if not self.btnHistory.isHidden():
            self.btnHistory.hide()
        self.list3.clear()
        self.list1.clear()
        self.list2.clear()
        self.label.clear()
        self.text.clear()
        
        if site == "PlayLists":
            self.mirror_change.hide()
            self.line.setPlaceholderText("No Search Option")
            self.line.setReadOnly(True)
            refererNeeded = False
            
            bookmark = False
            criteria = os.listdir(os.path.join(home, 'Playlists'))
            criteria.sort()
            home_n = os.path.join(home, 'Playlists')
            criteria = naturallysorted(criteria)
            self.original_path_name[:] = []
            for i in criteria:
                self.list1.addItem(i)
                self.original_path_name.append(i)
            criteria = ['List', 'Open File', 'Open Url', 'Open Directory']
            for i in criteria:
                self.list3.addItem(i)
            self.video_local_stream = False
        elif site == "Bookmark":
            bookmark = True
            criteria = [
                'All', 'Watching', 'Completed', 'Incomplete',
                'Interesting', 'Music Videos', 'Later'
                ]
            bookmark_array = [
                'bookmark', 'Watching', 'Completed', 'Incomplete', 
                'Later', 'Interesting', 'Music Videos'
                ]
            bookmark_extra = []
            for i in bookmark_array:
                f_path = os.path.join(home, 'Bookmark', i+'.txt')
                if not os.path.exists(f_path):
                    f = open(f_path, 'w')
                    f.close()
            m = os.listdir(os.path.join(home, 'Bookmark'))
            for i in m:
                i = i.replace('.txt', '')
                if i not in bookmark_array:
                    bookmark_extra.append(i)
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            for i in bookmark_extra:
                self.list3.addItem(i)
        elif site == "Select":
            site = 'None'
        elif site == "Addons":
            site = 'None'
            self.btnAddon.show()
            site = self.btnAddon.currentText()
            if self.site_var:
                del self.site_var
                self.site_var = ''
            print(type(self.site_var), site, '--addon-changed--')
            plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
            if os.path.exists(plugin_path):
                module = imp.load_source(site, plugin_path)
            self.site_var = getattr(module, site)(TMPDIR)
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        elif site == "YouTube":
            site = 'None'
            bookmark = False
            self.search()
        else:
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        
    def ka2(self):
        global site, home
        global total_till, browse_cnt
        global bookmark, total_till, thumbnail_indicator
        global genre_num, rfr_url, finalUrlFound, refererNeeded, siteName
        
        genre_num = 0
        
        if self.site_var:
            del self.site_var
            self.site_var = ''
        self.label.clear()
        self.text.clear()
        self.original_path_name[:]=[]
        rfr_url = ""
        finalUrlFound = False
        refererNeeded = False
        self.list3.clear()
        self.list1.clear()
        self.list2.clear()
        self.label.clear()
        self.text.clear()
        site = (self.btnAddon.currentText())
        siteName = ""
        print(type(self.site_var), site, '--addon-changed--')
        plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
        if os.path.exists(plugin_path):
            module = imp.load_source(site, plugin_path)
        self.site_var = getattr(module, site)(TMPDIR)
        print(type(self.site_var), site, '--addon-changed--')
        if siteName:
            self.btnHistory.show()
        else:
            if not self.btnHistory.isHidden():
                self.btnHistory.hide()
        bookmark = False
        if not os.path.exists(os.path.join(home, "History", site)):
            os.makedirs(os.path.join(home, "History", site))
        self.search()
    
    def ka1(self):
        global site, home
        global total_till, browse_cnt
        global bookmark
        
        self.label.clear()
        self.text.clear()
        site = str(self.btn30.currentText())
        if site == "Bookmark":
            bookmark = True
            criteria = [
                'All', 'Watching', 'Completed', 'Incomplete', "Later", 
                'Interesting'
                ]
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i) 
        else:
            bookmark = False
            if not os.path.exists(os.path.join(home, "History", site)):
                os.makedirs(os.path.join(home, "History", site))
            self.search()
        
            
    def reviewsWeb(self, srch_txt=None, review_site=None, action=None):
        global name, nam, old_manager, new_manager, home, screen_width
        global site
        if self.tab_2.isHidden():
            self.showHideBrowser()
        self.web_review_browser_started = True
        btn_hide = self.horizontalLayout_player_opt.itemAt(14)
        print(btn_hide, '--hide--btn--')
        original_srch_txt = None
        new_url = ''
        if srch_txt:
            srch_txt = self.metaengine.name_adjust(srch_txt)
            
        if not review_site:
            review_site = self.btnWebReviews.currentText()
            
        self.review_site_code = review_site
        print(self.web, '0')
        if not self.web and review_site:
            try:
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
            except NameError:
                site = 'None'
                self.epn_arr_list = []
                name = srch_txt
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
            self.web.setObjectName(_fromUtf8("web"))
            self.horizontalLayout_5.addWidget(self.web)
            print(self.web, '1')
        elif self.web:
            if QT_WEB_ENGINE:
                cur_location = self.web.url().url()
            else:
                cur_location = self.web.url().toString()
            logger.info('{0}--web--url--'.format(cur_location))
            if 'youtube' in review_site.lower() and 'youtube' not in cur_location and QT_WEB_ENGINE:
                self.web.close()
                self.web.deleteLater()
                self.web = Browser(self, home, screen_width, self.quality_val, site, self.epn_arr_list)
                self.web.setObjectName(_fromUtf8("web"))
                self.horizontalLayout_5.addWidget(self.web)
            print(self.web, '2')
        #print(self.VerticalLayoutLabel.itemAt(2), '--itemAt--')
        #if self.VerticalLayoutLabel.itemAt(2):
        #    self.VerticalLayoutLabel.takeAt(2)
        #    print('--stretch--deleted--')
        self.tab_2.show()
        try:
            name = str(name)
        except:
            name = srch_txt
        name1 = self.metaengine.name_adjust(name)
        logger.info(name1)
        key = ''
        if action:
            if action == 'return_pressed':
                key = self.btnWebReviews_search.text()
                self.btnWebReviews_search.clear()
                self.tmp_web_srch = key
                if review_site == 'Reviews':
                    review_site = 'DuckDuckGo'
                if key.startswith('http:') or key.startswith('https:'):
                    self.web.load(QUrl(key))
                    return 0
            elif action == 'context_menu' or action == 'search_by_name':
                key = srch_txt
            elif action == 'index_changed' or action == 'btn_pushed':
                if not self.tmp_web_srch:
                    key = name1
                else:
                    key = self.tmp_web_srch
            elif action == 'line_return_pressed':
                key = self.line.text()
                self.line.clear()
        else:
            key = self.line.text()
            self.line.clear()
        if key:
            name1 = str(key)
        pl_list = False
        
        if not name1:
            if self.list1.currentItem():
                name1 = self.list1.currentItem().text()
                if self.list2.currentItem() and self.btn1.currentText() == 'PlayLists':
                    name1 = self.list2.currentItem().text()
                    r = self.list2.currentRow()
                    finalUrl = self.epn_arr_list[r].split('	')[1]
                    if 'youtube.com' in finalUrl and 'list=' in finalUrl:
                        new_url = finalUrl
                        pl_list = True
            elif self.list2.currentItem():
                name1 = self.list2.currentItem().text()
                
            if name1.startswith(self.check_symbol):
                name1 = name1[1:]
                
        logger.info(self.web)
        self.widget_style.webStyle(self.web)
        logger.info('--13527---{0}-{1}'.format(review_site, name1))
        self.review_site_code = review_site
        if not name1:
            name1 = self.btnWebReviews_search.text()
            name1 = name1.replace(' ', '+')
        if review_site == "YouTube":
            if not name1:
                name1 = 'GNU Linux FSF Open Source'
            if pl_list and new_url and action != 'open':
                self.web.load(QUrl(new_url))
            elif action=='open' and original_srch_txt:
                self.web.load(QUrl(original_srch_txt))
            else:
                if self.browser_bookmark.get(review_site):
                    self.web.load(QUrl(self.browser_bookmark.get(review_site)+name1))
            logger.info('{0}--yt--open--'.format(srch_txt))
        elif review_site == "Reviews":
            self.web.setHtml('<html>Reviews:</html>')
        else:
            if self.browser_bookmark.get(review_site):
                self.web.load(QUrl(self.browser_bookmark.get(review_site)+name1))
        if review_site:
            self.btnWebReviews_search.setPlaceholderText('Search ' + review_site)
        
    def rawlist_highlight(self):
        global site, name, opt, pre_opt, mirrorNo
        global row_history, home, epn, path_Local_Dir
        global bookmark, status, siteName
        global screen_height, screen_width
        #print('========raw_list_highlight==========')
        if self.list1.currentItem():
            nm = self.original_path_name[self.list1.currentRow()].strip()
            if '	' in nm:
                name = nm.split('	')[0]
            else:
                name = nm
        else:
            return 0
        cur_row = self.list1.currentRow()
        fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
        thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
        m = []
        self.epn_arr_list[:]=[]
        #print('========raw_list_highlight==========')
        summary = 'Summary Not Available'
        picn = 'No.jpg'
        if siteName:
            file_name = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            picn1 = os.path.join(home, 'History', site, siteName, name, 'poster.jpg')
            fanart1 = os.path.join(home, 'History', site, siteName, name, 'fanart.jpg')
            thumbnail1 = os.path.join(home, 'History', site, siteName, name, 'thumbnail.jpg')
            summary_file = os.path.join(home, 'History', site, siteName, name, 'summary.txt')
        else:
            file_name = os.path.join(home, 'History', site, name, 'Ep.txt')
            picn1 = os.path.join(home, 'History', site, name, 'poster.jpg')
            fanart1 = os.path.join(home, 'History', site, name, 'fanart.jpg')
            thumbnail1 = os.path.join(home, 'History', site, name, 'thumbnail.jpg')
            summary_file = os.path.join(home, 'History', site, name, 'summary.txt')
        logger.info(file_name)
        if os.path.exists(file_name) and site!="PlayLists":
            lines = open_files(file_name, True)
            m = []
            if lines:
                logger.info(file_name)
                for i in lines:
                    i = i.strip()
                    if i:
                        self.epn_arr_list.append(i)
                        m.append(i)
                    
            picn = picn1
            fanart = fanart1
            thumbnail = thumbnail1
            
            if os.path.isfile(summary_file):
                summary = open_files(summary_file, False)
            
            j = 0
            
            self.text.clear()
            
            self.text.lineWrapMode()
            if site!= "Local":
                pass
                
            if summary.lower() == 'summary not available':
                summary = summary+'\n'+self.original_path_name[cur_row]
                
            self.videoImage(picn, thumbnail, fanart, summary)
                
            if os.path.isfile(file_name):
                self.list2.clear()
                self.update_list2()
        else:
            if summary.lower() == 'summary not available':
                txt = self.original_path_name[cur_row]
                if '	' in txt:
                    txt1, txt2 = txt.split('	')
                    summary = summary+'\n\n'+txt1+'\n\n'+txt2
            self.text.clear()
            self.text.insertPlainText(summary)
            self.list2.clear()
            
    def searchNew(self):
        global search, name
        self.show_search_thumbnail = False
        if self.btn1.currentText() == "Select":
            site = "None"
            self.line.clear()
            return 0
        elif (self.line.placeholderText()) == "No Search Option":
            self.line.clear()
            return 0
        else:
            self.search()
            name = (self.line.text())
        
        
    def search(self):
        code = 1
        global site, opt, mirrorNo, hdr
        global site_arr, siteName, finalUrlFound
        global total_till, browse_cnt
        global bookmark, refererNeeded, name
        
        browse_cnt=0
        opt = "Search"
        m=[]
        criteria = []
        self.options_mode = 'legacy'
        self.music_playlist = False
        print(site, self.btn1.currentText().lower())
        
        if site and (site not in site_arr) and self.site_var:
            print(site)
            
            self.mirror_change.hide()
            
            if self.site_var:
                criteria = self.site_var.getOptions() 
                self.list3.clear()
                print(criteria)
                tmp = criteria[-1]
                if tmp.lower() == 'newversion':
                    criteria.pop()
                    self.options_mode = 'new'
                    tmp = criteria[-1]
                if tmp == 'LocalStreaming':
                    criteria.pop()
                    self.video_local_stream = True
                    if not self.local_ip:
                        self.local_ip = get_lan_ip()
                    if not self.local_port:
                        self.local_port = 8001
                    self.torrent_type = 'file'
                else:
                    finalUrlFound = False
                    refererNeeded = False
                    self.video_local_stream = False
                for i in criteria:
                    self.list3.addItem(i)
                self.line.setPlaceholderText("Search Available")
                self.line.setReadOnly(False)
                self.line.show()
                name = self.line.text()
                if name:
                    self.line.clear()
                    self.list1.clear()
                    genre_num = 0
                    try:
                        self.text.setText('Wait...Loading')
                        QtWidgets.QApplication.processEvents()
                        m = self.site_var.search(name)
                        self.search_term = name
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed')
                        return 0
                    if type(m) is list:
                        self.original_path_name[:] = []
                        for i in m:
                            i = i.strip()
                            j = i
                            if '	' in i:
                                i = i.split('	')[0]
                            self.list1.addItem(i)
                            self.original_path_name.append(j)
                    else:
                        self.list1.addItem("Sorry No Search Function")
        elif site == "Music":
            self.show_search_thumbnail = True
            self.mirror_change.hide()
            criteria = [
                'Playlist', "Artist", 'Album', 'Title', 'Directory', 
                'Fav-Artist', 'Fav-Album', 'Fav-Directory', 
                'Last 50 Played', 'Last 50 Newly Added', 
                'Last 50 Most Played'
                ]
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            self.line.setPlaceholderText("No Search Option")
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            refererNeeded = False
            self.video_local_stream = False
            nm = self.line.text()
            if nm:
                self.line.clear()
                self.list1.clear()
                music_db = os.path.join(home, 'Music', 'Music.db')
                m = self.media_data.get_music_db(music_db, 'Search', nm)
                logger.info(m)
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    i1 = i[1]
                    i2 = i[2]
                    i3 = i[0]
                    j = i1+'	'+i2+'	'+i3
                    try:
                        self.epn_arr_list.append(str(j))
                    except:
                        self.epn_arr_list.append(j)
                self.update_list2()
                if self.gapless_playback:
                    self.use_playlist_method()
        elif site == "Video":
            self.show_search_thumbnail = True
            self.mirror_change.hide()
            criteria = [
                'Directory', 'Available', 'History', 'Recent', 'Update', 'UpdateAll'
                ]
            insert_index = criteria.index('Update')
            for i in self.category_array:
                criteria.insert(insert_index, i)
                insert_index += 1
                
            self.list3.clear()
            for i in criteria:
                self.list3.addItem(i)
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            refererNeeded = False
            self.video_local_stream = False
            nm = self.line.text()
            if nm:
                self.line.clear()
                self.list1.clear()
                video_db = os.path.join(home, 'VideoDB', 'Video.db')
                m = self.media_data.get_video_db(video_db, 'Search', nm)
                logger.info(m)
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    j = i[0]+'	'+i[1]+'	'+'NONE'
                    try:
                        self.epn_arr_list.append(str(j))
                    except:
                        self.epn_arr_list.append(j)
                self.update_list2()
                if self.gapless_playback:
                    self.use_playlist_method()
        elif ((site == "None" and self.btn1.currentText().lower() == 'youtube') or not self.tab_2.isHidden()):
            self.video_local_stream = False
            self.mirror_change.hide()
            self.line.setPlaceholderText("Search Available")
            self.line.setReadOnly(False)
            name_t = self.line.text()
            if name_t:
                name = name_t
                self.btnWebReviews_search.setText(name_t)
                index = self.btnWebReviews.findText('YouTube')
                if index >= 0:
                    self.btnWebReviews.setCurrentIndex(0)
                    self.btnWebReviews.setCurrentIndex(index)
                #self.reviewsWeb(srch_txt=name, review_site='yt', action='line_return_pressed')
        elif siteName:
            self.video_local_stream = False
            self.mirror_change.show()
            
            if self.site_var:
                criteria = self.site_var.getOptions() 
                code = 7
                self.list3.clear()
                for i in criteria:
                    self.list3.addItem(i)
                self.line.setPlaceholderText("No Search Option")
                self.line.setReadOnly(True)
                name = self.line.text()
                if name:
                    self.line.clear()
                    self.list1.clear()
                    genre_num = 0
                    self.text.setText('Wait...Loading')
                    QtWidgets.QApplication.processEvents()
                    try:
                        m = self.site_var.getCompleteList(siteName, category, 'Search')
                        self.text.setText('Load Complete!')
                    except Exception as e:
                        print(e)
                        self.text.setText('Load Failed')
                        return 0
                    self.original_path_name[:] = []
                    for i in m:
                        i = i.strip()
                        j = i
                        if '	' in i:
                            i = i.split('	')[0]
                        self.list1.addItem(i)
                        self.original_path_name.append(i)
        self.line.clear()
    
    def get_torrent_handle(self, nm):
        handle = None
        if self.stream_session:
            t_list = self.stream_session.get_torrents()
            logger.info('--15197---')
            for i in t_list:
                old_name = i.name()
                logger.info('--check--{0}'.format(old_name))
                if old_name == nm:
                    logger.info('selecting handle: {0}'.format(nm))
                    handle = i
                    break
        return handle
    
    def summary_write_and_image_copy(self, hist_sum, summary, picn, hist_picn):
        write_files(hist_sum, summary, line_by_line=False)
        if os.path.isfile(picn):
            shutil.copy(picn, hist_picn)
            
    def get_summary_history(self, file_name):
        summary = open_files(file_name, False)
        return summary

    def get_title_name(self, row):
        global site
        name = ''
        if (site != "PlayLists" and site != "Music" and site != "Video" 
                and site!="Local" and site !="None"):
            cur_row = row
            new_name_with_info = self.original_path_name[cur_row].strip()
            extra_info = ''
            if '	' in new_name_with_info:
                name = new_name_with_info.split('	')[0]
                extra_info = new_name_with_info.split('	')[1]
            else:
                name = new_name_with_info
        elif site == 'Music':
            nm = ''
            try:
                if str(self.list3.currentItem().text()) == "Artist":
                    nm = self.list1.item(row).text()
                else:
                    row = self.list2.currentRow()
                    nm = self.epn_arr_list[row].split('	')[2]
                    nm = nm.replace('"', '')
            except Exception as e:
                    print(e)
                    nm = ""
            name = nm
            if '/' in name:
                name = name.replace('/', '-')
        elif site == 'Video':
            item = self.list1.item(row)
            if item:
                art_n = str(self.list1.item(row).text())
                name = art_n
        return name
    
    def newlistfound(self, site, opt, siteName, video_local_stream,
                     name, extra_info, category, from_cache=None):
        global home
        m = []
        if (site != "PlayLists" and site != "Music" and site != "Video" 
                and site!="Local" and site !="None") and name:
            fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
            thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
            summary = "Summary Not Available"
            picn = "No.jpg"
            #self.list2.clear()
            site_variable = '{0}::{1}::{2}::{3}::{4}::{5}'.format(
                    site, siteName, opt, name, extra_info, category
                    )
            print(site_variable)
            if not from_cache and site_variable not in self.myserver_cache:
                if opt != "History" or site.lower() == 'myserver':
                    try:
                        if video_local_stream:
                            siteName = os.path.join(home, 'History', site)
                            if not os.path.exists(siteName):
                                os.makedirs(siteName)
                        m, summary, picn, self.record_history, self.depth_list = self.site_var.getEpnList(
                                name, opt, self.depth_list, extra_info, siteName, 
                                category)
                    except Exception as e:
                        print(e)
                    if not m:
                        pass
                    else:
                        self.myserver_cache.update({site_variable:m.copy()})
            else:
                m = self.myserver_cache.get(site_variable)
            if m:
                self.set_parameters_value(name_val=name)
                self.epn_arr_list.clear()
                for i in m:
                    self.epn_arr_list.append(i)
                if self.gapless_playback:
                    self.use_playlist_method()
            if from_cache:
                if siteName:
                    hist_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                else:
                    hist_path = os.path.join(home, 'History', site, 'history.txt')

                hist_dir, last_field = os.path.split(hist_path)
                hist_site = os.path.join(hist_dir, name)
                hist_epn = os.path.join(hist_site, 'Ep.txt')
                hist_sum = os.path.join(hist_site, 'summary.txt')
                hist_picn = os.path.join(hist_site, 'poster.jpg')
                self.update_list2()
                if os.path.isfile(hist_sum) or os.path.isfile(hist_picn):
                    self.videoImage(picn, thumbnail, fanart, summary)
    
    def replace_special_characters(self, newname, replc_dict=None):
        if not replc_dict:
            replc_dict = {
                ':':'-', '|':'-', '&':'-and-', '?':'-', '+':'-', '#':'-',
                '"':'-', '*':'-'
                }
        if '\t' in newname:
            title, restpart = newname.split('\t', 1)
        else:
            title = newname
            restpart = ''
        for i in replc_dict:
            title = title.replace(i, replc_dict[i])
        if restpart:
            title = title+'\t'+restpart
        return title
    
    def listfound(self, send_list=None, row_select=None, show_ep_thumbnail=None):
        global site, name, base_url, embed, opt, pre_opt, mirrorNo
        global row_history, home, epn, path_Local_Dir, bookmark
        global status, finalUrlFound, refererNeeded, audio_id, sub_id
        global opt_movies_indicator, siteName
        global screen_height, screen_width
        
        opt_movies_indicator[:]=[]
        new_dir_path = None
        fanart = os.path.join(TMPDIR, name+'-fanart.jpg')
        thumbnail = os.path.join(TMPDIR, name+'-thumbnail.jpg')
        summary = "Summary Not Available"
        picn = "No.jpg"
        m = []
        if not row_select:
            if self.list1.currentItem():
                row_select = self.list1.currentRow()
            else:
                row_select = -1
        elif isinstance(row_select, int):
            if row_select not in range (0, self.list1.count()):
                row_select = -1
        else:
            row_select = -1
        if row_select == -1:
            return 0
        if bookmark and os.path.exists(os.path.join(home, 'Bookmark', status+'.txt')):
            #tmp = site+':'+opt+':'+pre_opt+':'+base_url+':'+str(embed)+':'+name':'+
            #finalUrlFound+':'+refererNeeded+':'+video_local_stream
            #f = open(os.path.join(home, 'Bookmark', status+'.txt'), 'r')
            line_a = open_files(os.path.join(home, 'Bookmark', status+'.txt'), True)
            if row_select < 0 or row_select >= len(line_a):
                logger.info('--wrong--value--of row--7014--')
                return 0
            tmp = line_a[row_select]
            tmp = tmp.strip()
            tmp1 = tmp.split(':')
            site = tmp1[0]
            if site == "Music" or site == "Video":
                opt = "Not Defined"
                if site == "Music":
                    music_opt = tmp1[1]
                else:
                    video_opt = tmp1[1]
            else:
                opt = tmp1[1]
            pre_opt = tmp1[2]
            siteName = tmp1[2]
            base_url = int(tmp1[3])
            embed = int(tmp1[4])
            name = tmp1[5]
            if site=="Local":
                name_path = name
            
            logger.info(name)
            if len(tmp1) > 6:
                if tmp1[6] == "True":
                    finalUrlFound = True
                else:
                    finalUrlFound = False
                if tmp1[7] == "True":
                    refererNeeded = True
                else:
                    refererNeeded = False
                if len(tmp1) >=9:
                    if tmp1[8] == "True":
                        self.video_local_stream = True
                    else:
                        self.video_local_stream = False
                if len(tmp1) >=10:
                    new_dir_path = tmp1[9]
                    if OSNAME == 'nt':
                        if len(tmp1) == 11:
                            new_dir_path = new_dir_path + ':' + tmp1[10]
                        
                print(finalUrlFound)
                print(refererNeeded)
                print(self.video_local_stream)
                logger.info(new_dir_path)
            else:
                refererNeeded = False
                finalUrlFound = False
                self.video_local_stream = False
            logger.info(site + ":"+opt)
            if (site != "PlayLists" and site != "Music" and site != "Video" 
                    and site!="Local" and site !="None"):
                plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
                if os.path.exists(plugin_path):
                    if self.site_var:
                        del self.site_var
                        self.site_var = ''
                    module = imp.load_source(site, plugin_path)
                    self.site_var = getattr(module, site)(TMPDIR)
                else:
                    return 0
                    
        if site not in ["PlayLists", "Music", "Video", "None"]:
            self.list2.clear()
            if row_select >= 0:
                m = []
                if send_list is None:
                    self.depth_list = row_select
                    new_name_with_info = self.original_path_name[row_select].strip()
                    extra_info = ''
                    if '	' in new_name_with_info:
                        name = new_name_with_info.split('	')[0]
                        extra_info = new_name_with_info.split('	')[1]
                    else:
                        name = new_name_with_info
                elif isinstance(send_list, list):
                    if not send_list:
                        logger.error('No List Sent')
                    else:
                        m, summary, picn = send_list[0], send_list[1], send_list[2]
                        self.record_history, self.depth_list = send_list[3], send_list[4]
                        name, extra_info = send_list[5], send_list[6]
                        siteName, opt = send_list[7], send_list[8]
                        row_select = send_list[9]
                        new_name_with_info = self.original_path_name[row_select].strip()
                        self.text.setText('Load..Complete')
                        logger.info(m)
                        logger.info(summary)
                        logger.info(picn)
                        logger.info('site={0};opt={1};name={2};extra_info={3}'.format(
                            site, opt, name, extra_info))
                if opt != "History" or site.lower() == 'myserver':
                    if send_list is None:
                        self.text.setText('Wait...Loading')
                        QtWidgets.QApplication.processEvents()
                        try:
                            if self.video_local_stream:
                                siteName = os.path.join(home, 'History', site)
                                if not os.path.exists(siteName):
                                    os.makedirs(siteName)
                            if site.lower() == 'myserver':
                                m, summary, picn, self.record_history, self.depth_list = self.site_var.getEpnList(
                                    name, opt, self.depth_list, extra_info, siteName, 
                                    category)
                                self.text.setText('Load..Complete')
                            else:
                                if not self.epn_wait_thread.isRunning():
                                    self.epn_wait_thread = PlayerGetEpn(
                                        self, logger, 'list', name, opt, 
                                        self.depth_list, extra_info, siteName,
                                        category, row_select)
                                    self.epn_wait_thread.start()
                                    return 0
                                else:
                                    self.text.setText('Please Wait...Loading of\
                                                      Earlier Title is in process')
                                    return 0
                        except Exception as e:
                            print(e)
                            self.text.setText('Load..Failed')
                            return 0
                    if not m:
                        logger.error('Nothing found')
                        return 0
                    else:
                        level_mark = m[-1]
                    
                    if level_mark == 1:
                        m.pop()
                        self.original_path_name.clear()
                        self.list1.clear()
                        for i in m:
                            i = i.strip()
                            if '\t' in i:
                                j = i.split('\t')[0]
                            else:
                                j = i
                            self.list1.addItem(j)
                            self.original_path_name.append(i)
                        self.list1.setCurrentRow(self.depth_list)
                        return 0
                    else:
                        self.epn_arr_list.clear()
                        for i in m:
                            self.epn_arr_list.append(i)
                        
                    if siteName:
                        hist_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                    else:
                        hist_path = os.path.join(home, 'History', site, 'history.txt')
                    if not os.path.isfile(hist_path):
                        hist_dir, last_field = os.path.split(hist_path)
                        if not os.path.exists(hist_dir):
                            os.makedirs(hist_dir)
                        f = open(hist_path, 'w').close()
                    print(self.record_history, '--self.record_history---')
                    if os.path.isfile(hist_path) and self.record_history:
                        if OSNAME != 'posix':
                            new_name_with_info = self.replace_special_characters(new_name_with_info)
                        if (os.stat(hist_path).st_size == 0):
                            write_files(hist_path, new_name_with_info, line_by_line=True)
                        else:
                            lines = open_files(hist_path, True)
                            line_list = []
                            for i in lines :
                                i = i.strip()
                                line_list.append(i)
                                
                            if new_name_with_info not in line_list:
                                write_files(hist_path, new_name_with_info, line_by_line=True)
                    
                    hist_dir, last_field = os.path.split(hist_path)
                    if OSNAME != 'posix':
                        name = self.replace_special_characters(name)
                    hist_site = os.path.join(hist_dir, name)
                    hist_epn = os.path.join(hist_site, 'Ep.txt')
                    if (not os.path.exists(hist_site) and self.record_history) or (os.path.exists(hist_epn)):
                        try:
                            first_try = False
                            if not os.path.exists(hist_site):
                                os.makedirs(hist_site)
                                first_try = True
                            
                            if not first_try or site == 'MyServer':
                                lines = open_files(hist_epn, True)
                                if len(m) > len(lines):
                                    length_old = len(lines)
                                    m = m[length_old:]
                                    m = lines + m
                            
                            write_files(hist_epn, m, line_by_line=True)
                            
                            if first_try:
                                hist_sum = os.path.join(hist_site, 'summary.txt')
                                hist_picn = os.path.join(hist_site, 'poster.jpg')
                                self.summary_write_and_image_copy(hist_sum, summary, picn, hist_picn)
                        except Exception as e:
                            print(e)
                            return 0
                else:
                    if OSNAME != 'posix':
                        name = self.replace_special_characters(name)
                    if siteName:
                        hist_site = os.path.join(home, 'History', site, siteName, name)
                    else:
                        hist_site = os.path.join(home, 'History', site, name)
                        
                    hist_epn = os.path.join(hist_site, 'Ep.txt')
                    logger.info(hist_epn)
                    if os.path.exists(hist_epn):
                        lines = open_files(hist_epn, True)
                        m = []
                        self.epn_arr_list[:]=[]
                        for i in lines:
                            i = i.strip()
                            self.epn_arr_list.append(i)
                            m.append(i)
                                
                        picn = os.path.join(hist_site, 'poster.jpg')
                        fanart = os.path.join(hist_site, 'fanart.jpg')
                        thumbnail = os.path.join(hist_site, 'thumbnail.jpg')
                        sum_file = os.path.join(hist_site, 'summary.txt')
                        summary = self.get_summary_history(sum_file)

                        f_name = os.path.join(hist_site, 'Ep.txt')
                        if os.path.exists(f_name):
                            lines = open_files(f_name, True)
                            if len(self.epn_arr_list) > len(lines):
                                write_files(f_name, m, line_by_line=True)
                self.videoImage(picn, thumbnail, fanart, summary)
        elif site == "Music":
            try:
                art_n = self.list1.item(row_select).text()
            except:
                return 0
            music_dir = os.path.join(home, 'Music')
            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            if not bookmark:
                if not self.list3.currentItem():
                    self.list3.setCurrentRow(0)
                music_opt = self.list3.currentItem().text()

            artist =[]

            if music_opt == "Directory":
                art_n = self.original_path_name[row_select]
            if music_opt == "Fav-Directory":
                art_n = self.original_path_name[row_select]
            if music_opt == "Playlist":
                item = self.list1.item(row_select)
                if item:
                    pls = item.text()
                    m = open_files(os.path.join(home, 'Playlists', pls), True)
                    for i in m:
                        i = i.replace('\n', '')
                        if i:
                            j = i.split('	')
                            i1 = j[0]
                            i2 = j[1]
                            try:
                                i3 = j[2]
                            except:
                                i3 = "None"
                            artist.append(i1+'	'+i2+'	'+i3)
            else:
                if art_n in self.music_dict:
                    m = self.music_dict.get(music_opt.lower()+'::'+art_n)
                    logger.debug('Getting Music from Cache')
                else:
                    m = self.media_data.get_music_db(music_db, music_opt, art_n)
                    mlist = [list(i) for i in m]
                    self.music_dict.update({music_opt.lower()+'::'+art_n:mlist})
                for i in m:
                    if len(i) > 2:
                        artist.append(i[1]+'	'+i[2]+'	'+i[0])
            self.epn_arr_list[:]=[]
            self.list2.clear()
            for i in artist:
                try:
                    self.epn_arr_list.append(str(i))
                except:
                    self.epn_arr_list.append((i))
                
            self.musicBackground(0, 'offline')
        elif site == "PlayLists":
            self.list2.clear()
            item = self.list1.item(row_select)
            self.epn_arr_list[:]=[]
            if item:
                pls = self.list1.item(row_select).text()
                file_path = os.path.join(home, 'Playlists', str(pls))
                if os.path.exists(file_path):
                    lines = open_files(file_path, True)
                    k = 0
                    for i in lines:
                        i = i.replace('\n', '')
                        if i:	
                            self.epn_arr_list.append(i)
        elif site == "Video":
            item = self.list1.item(row_select)
            if item:
                art_n = item.text()
                name = art_n
                video_dir = os.path.join(home, 'VideoDB')
                video_db = os.path.join(video_dir, 'Video.db')
                video_file = os.path.join(video_dir, 'Video.txt')
                video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
                
                artist =[]
                if not bookmark:
                    if self.list3.currentItem():
                        video_opt = str(self.list3.currentItem().text())
                    else:
                        video_opt = 'History'
                    if video_opt == "Update" or video_opt == "UpdateAll":
                        video_opt = "Available"
                        self.video_dict.clear()
                    if video_opt.lower() != "update" and video_opt.lower() != "updateall":
                        art_n = self.original_path_name[row_select].split('	')[-1]
                        if art_n in self.video_dict:
                            m = self.video_dict[art_n]
                            logger.info('Getting from Cache')
                        else:
                            m = self.media_data.get_video_db(video_db, "Directory", art_n)
                            mlist = [list(i) for i in m]
                            self.video_dict.update({art_n:mlist})
                            logger.info('Getting from DB')
                            logger.info(type(m))
                else:
                    new_art_n = art_n
                    if new_dir_path is not None:
                        if new_dir_path.lower() != 'none':
                            new_art_n = new_dir_path
                            m = self.media_data.get_video_db(video_db, "Directory", new_art_n)
                        else:
                            m = self.media_data.get_video_db(video_db, "Bookmark", new_art_n)
                    else:
                        m = self.media_data.get_video_db(video_db, "Bookmark", new_art_n)
                
                if video_opt.lower() == 'recent':
                    check_path = (lambda x: os.path.getctime(x) if os.path.exists(x) else 0)
                    m = sorted(m, key=lambda x: check_path(x[1]), reverse=True)
                
                self.epn_arr_list.clear()
                self.list2.clear()
                self.epn_arr_list = [i[0]+'\t'+i[1] for i in m]
                art_n = self.list1.item(row_select).text()
                dir_path = os.path.join(home, 'Local', art_n)
                if os.path.exists(dir_path):
                    picn = os.path.join(home, 'Local', art_n, 'poster.jpg')
                    thumbnail = os.path.join(home, 'Local', art_n, 'thumbnail.jpg')
                    fanart = os.path.join(home, 'Local', art_n, 'fanart.jpg')
                    summary1 = os.path.join(home, 'Local', art_n, 'summary.txt')
                    if os.path.exists(summary1):
                        summary = open_files(summary1, False)
                    else:
                        summary = "Not Available"
                    
                    self.videoImage(picn, thumbnail, fanart, summary)
                    logger.info(picn)
                else:
                    os.makedirs(dir_path)
        self.current_background = fanart
        self.update_list2()
        if show_ep_thumbnail:
            if self.view_mode == 'thumbnail':
                self.IconViewEpn(mode=1)
            elif self.view_mode == 'thumbnail_light':
                self.IconViewEpn(mode=2)
        if self.gapless_playback:
            self.use_playlist_method()
    
    def use_playlist_method(self):
        global site
        self.tmp_pls_file_lines.clear()
        self.tmp_pls_file_dict.clear()
        if site in self.local_site_list:
            for j, i in enumerate(self.epn_arr_list):
                if '\t' in i:
                    item = i.split('\t')[1].strip()
                else:
                    item = i.strip()
                if item:
                    item = item.replace('"', '')
                    if item.startswith('abs_path=') or item.startswith('relative_path='):
                        item = self.if_path_is_rel(item, thumbnail=True)
                    if item.startswith('ytdl:'):
                        item = item.replace('ytdl:', '', 1)
                    self.tmp_pls_file_lines.append(item)
                    if self.gapless_network_stream:
                        self.tmp_pls_file_dict.update({j:False})
    
    def set_list_thumbnail(self, k):
        if self.list_with_thumbnail:
            icon_name = self.get_thumbnail_image_path(k, self.epn_arr_list[k])
            if os.path.exists(icon_name):
                self.list2.item(k).setIcon(QtGui.QIcon(icon_name))

    def musicBackground(self, val, srch):
        global name, artist_name_mplayer, site
        logger.info('{0}-{1}--music--background--'.format(val, srch))
        if self.list3.currentItem() and site.lower() == 'music':
            if self.list3.currentItem().text().lower() == "artist":
                artist_mode = True
            else:
                artist_mode = False
        else:
            artist_mode = False
        print(artist_mode, '----artist--mode---')
        if artist_mode:
            music_dir_art = os.path.join(home, 'Music', 'Artist')
            if not os.path.exists(music_dir_art):
                os.makedirs(music_dir_art)
            if self.list1.currentItem():
                if srch != "Queue":
                    nm = str(self.list1.currentItem().text())
                    if '/' in nm:
                        nm = nm.replace('/', '-')
                else:
                    nm = artist_name_mplayer
                if OSNAME != 'posix':
                    nm = self.replace_special_characters(nm)
                music_dir_art_name = os.path.join(home, 'Music', 'Artist', nm)
                logger.info(music_dir_art_name)
                if not os.path.exists(music_dir_art_name):
                    os.makedirs(music_dir_art_name)
                else:
                    art_list = os.listdir(music_dir_art_name)
                    sumr = os.path.join(music_dir_art_name, 'bio.txt')
                    if os.path.exists(sumr):
                        summary = open_files(sumr, False)
                    else:
                        summary = "Not Available"
                    
                    poster = os.path.join(music_dir_art_name, 'poster.jpg')
                    fan = os.path.join(music_dir_art_name, 'fanart.jpg')
                    thumb = os.path.join(music_dir_art_name, 'thumbnail.jpg')
                    if not os.path.exists(poster) and srch != "offline" and self.get_artist_metadata:	
                        self.threadPool.append(ThreadingExample(nm, logger, TMPDIR))
                        self.threadPool[len(self.threadPool)-1].finished.connect(lambda x=nm: self.finishedM(nm))
                        self.threadPool[len(self.threadPool)-1].start()
                    else:
                        self.videoImage(poster, thumb, fan, summary)
        else:
            music_dir_art = os.path.join(home, 'Music', 'Artist')
            logger.info('{0}=music_dir_art'.format(music_dir_art))
            try:
                if srch != "Queue":
                    nm = self.epn_arr_list[val].split('	')[2]
                else:
                    nm = artist_name_mplayer
            except:
                nm = ""
            logger.info("Name of Artist is {0}".format(nm))
            if nm:
                if '/' in nm:
                    nm = nm.replace('/', '-')
                nm = nm.replace('"', '')
                #nm = nm.replace("'", "")
                if nm.lower()!= 'none' and not nm.startswith('http'):
                    artist_name_mplayer = nm
                else:
                    artist_name_mplayer = ''
                if OSNAME != 'posix':
                    nm = self.replace_special_characters(nm)
                music_dir_art_name = os.path.join(home, 'Music', 'Artist', nm)
                logger.info('music_dir_art_name={0}'.format(music_dir_art_name))
                if not os.path.exists(music_dir_art_name):
                    os.makedirs(music_dir_art_name)
                #else:
                art_list = os.listdir(music_dir_art_name)
                sumr = os.path.join(music_dir_art_name, 'bio.txt')
                if os.path.exists(sumr):
                    summary = open_files(sumr, False)
                else:
                    summary = "Not Available"
                    
                poster = os.path.join(music_dir_art_name, 'poster.jpg')
                fan = os.path.join(music_dir_art_name, 'fanart.jpg')
                thumb = os.path.join(music_dir_art_name, 'thumbnail.jpg')
                logger.info('poster={0}--srch={1}--artist={2}'.format(poster, srch, artist_name_mplayer))
                if (not os.path.exists(poster) and srch != "offline" 
                        and artist_name_mplayer.lower() != "none" 
                        and artist_name_mplayer and self.get_artist_metadata):	
                    print('--starting--thread--')
                    self.threadPool.append(ThreadingExample(nm, logger, TMPDIR))
                    self.threadPool[len(self.threadPool)-1].finished.connect(lambda x=nm: self.finishedM(nm))
                    self.threadPool[len(self.threadPool)-1].start()
                elif os.path.exists(poster) or os.path.exists(fan) or os.path.exists(thumb):
                    self.videoImage(poster, thumb, fan, summary)
                else:
                    try:
                        r = self.list2.currentRow()
                        thumb_path = self.get_thumbnail_image_path(r, self.epn_arr_list[r])
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        print('No Thumbnail Available: {0}'.format(e))
            else:
                try:
                    r = self.list2.currentRow()
                    thumb_path = self.get_thumbnail_image_path(r, self.epn_arr_list[r])
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    print('No Thumbnail Available: {0}'.format(e))
                    
    def round_corner(self, im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        #alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        #alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        #alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def image_fit_option(self, picn, fanart, fit_size=None, widget=None,
                         widget_size=None, color=None):
        """
        fit_size = 1. Fit to Screen (Doesn't Preserve aspect ratio (A.R.))
        fit_size = 2. Fit to Screen Width (Preserve A.R.)
        fit_size = 3. Fit to Screen Height (Preserve A.R.)
        fit_size = 4. Fit to Screen Height and (screen-width - playlist_width) 
        with black border (Preserve A.R.)
        fit_size = 5. Fit to Screen Height with black border (Preserve A.R.)
        fit_size = 6. Fit to given widget size and preserve aspect ratio
        fit_size = 7. Fit to Screen Height (Left Side) with black border gap 
        between two posters
        fit_size = 8. Fit to Screen Height (Left Side) with black border
        """
        #print(color,'--color--')
        #logger.info('{0}:{1}:{2}:{3}:{4}:{5}'.format(picn,fanart,fit_size,widget,widget_size,color))
        global screen_height, screen_width
        if not color:
            color = 'RGB'
        color_val = (56,60,74)
        try:
            if fit_size:
                if (fit_size == 1 or fit_size == 2) or fit_size > 100:
                    if fit_size == 1 or fit_size == 2:
                        if widget:
                            basewidth = widget.width()
                        else:
                            basewidth = screen_width
                    else:
                        basewidth = fit_size
                    try:
                        if widget == self.float_window:
                            if os.path.isfile(fanart):
                                img = Image.open(str(fanart))
                            else:
                                img = Image.open(str(picn))
                        else:
                            img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13238')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    if fit_size == 1:
                        hsize = screen_height
                    else:
                        wpercent = (basewidth / float(img.size[0]))
                        hsize = int((float(img.size[1]) * float(wpercent)))
                    
                    if widget == self.float_window:
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        bg = Image.new(color, (basewidth, widget.height()))
                        if hsize < widget.height():
                            offset = int((widget.height() - hsize)/2)
                            bg.paste(img, (0, offset))
                            #bg.paste(img, (0, 0))
                            #bg.paste(img, (0, hsize))
                        else:
                            bg.paste(img, (0, 0))
                        tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                        try:
                            bg.save(str(tmp_img), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(tmp_img, bg)
                        return tmp_img
                    else:
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        bg = Image.new(color, (basewidth, hsize))
                        bg.paste(img, (0, 0))
                        try:
                            bg.save(str(fanart), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(fanart, bg)
                elif fit_size == 3:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13253')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    #img.save(str(fanart), 'JPEG', quality=100)
                    bg = Image.new(color, (wsize, screen_height))
                    bg.paste(img, (0, 0))
                    try:
                        bg.save(str(fanart), 'JPEG', quality=100)
                    except Exception as err:
                        print(err)
                        self.handle_png_to_jpg(fanart, bg)
                elif fit_size == 7:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13268')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    bg = Image.new(color, (wsize+20, baseheight), color_val)
                    offset = (0, 0)
                    bg.paste(img, offset)
                    try:
                        bg.save(str(fanart), 'JPEG', quality=100)
                    except Exception as err:
                        print(err)
                        self.handle_png_to_jpg(fanart, bg)
                elif fit_size == 5 or fit_size == 8:
                    baseheight = screen_height
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13284')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (baseheight / float(img.size[1]))
                    wsize = int((float(img.size[0]) * float(wpercent)))
                    sz = (wsize, baseheight)
                    img = img.resize((wsize, baseheight), PIL.Image.ANTIALIAS)
                    bg = Image.new(color, (screen_width, screen_height), color_val)
                    if fit_size == 5:
                        offset = (int((screen_width-wsize)/2), int((screen_height-baseheight)/2))
                    else:
                        offset = (int((0)), int((screen_height-baseheight)/2))
                    bg.paste(img, offset)
                    try:
                        bg.save(str(fanart), 'JPEG', quality=100)
                    except Exception as err:
                        print(err)
                        self.handle_png_to_jpg(fanart, bg)
                elif fit_size == 9 or fit_size == 10:
                    baseheight = screen_height - (self.frame1.height()+self.label.height()+100)
                    #baseheight = screen_height - self.label.x()
                    if fit_size == 9:
                        basewidth = screen_width - self.width_allowed - 40
                    else:
                        basewidth = screen_width - 2*self.width_allowed - 40
                    try:
                        img = Image.open(str(picn))
                    except Exception as e:
                        print(e, 'Error in opening image, videoImage, ---13284')
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    #img = self.round_corner(img, 30)
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    bg = Image.new(color, (screen_width, screen_height), color_val)
                    #bg = Image.open(os.path.join(home, 'default.jpg'))
                    if hsize < screen_height:
                        sz = (basewidth, hsize)
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        offset = (20,20)
                        #new_offset = (20+basewidth, 20)
                        bg.paste(img, offset)
                        #bg.paste(img, new_offset)
                        try:
                            bg.save(str(fanart), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(fanart, bg)
                    else:
                        wp = float(baseheight/hsize)
                        nbw = int(float(wp)*float(basewidth))
                        img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
                        offset = (20, 20)
                        if fit_size == 9:
                            new_offset = (40+nbw, 20)
                        else:
                            new_offset = (20+nbw, 20)
                        bg.paste(img, offset)
                        bg.paste(img, new_offset)
                        try:
                            bg.save(str(fanart), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(fanart, bg)
                elif fit_size == 6 or fit_size == 4:
                    if widget and fit_size == 6:
                        if widget in [self.label, self.label_new]:
                            basewidth = widget.maximumWidth()
                            baseheight = widget.maximumHeight()
                        else:
                            basewidth = widget.width()
                            baseheight = widget.height()
                    elif fit_size == 4:
                        basewidth = screen_width - self.width_allowed
                        baseheight = screen_height
                    else:
                        if widget_size:
                            basewidth = widget_size[0]
                            baseheight = widget_size[1]
                        else:
                            basewidth = self.float_window.width()
                            baseheight = self.float_window.height()
                    if fit_size == 6:
                        bg = Image.new(color, (basewidth, baseheight))
                    else:
                        bg = Image.new(color, (basewidth, baseheight))
                    try:
                        if os.path.exists(picn) and os.stat(picn).st_size:
                            img = Image.open(str(picn))
                        else:
                            picn = os.path.join(home, 'default.jpg')
                            img = Image.open(str(picn))
                    except Exception as e:
                        logger.error('{0}::Error in opening image, videoImage ---13321'.format(e))
                        picn = os.path.join(home, 'default.jpg')
                        img = Image.open(str(picn))
                    wpercent = (basewidth / float(img.size[0]))
                    hsize = int((float(img.size[1]) * float(wpercent)))
                    sz = (basewidth, hsize)
                    if hsize > baseheight:
                        wp = float(baseheight/hsize)
                        nbw = int(float(wp)*float(basewidth))
                        img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
                        offset = (int((basewidth-nbw)/2), 0)
                    else:
                        img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
                        offset = (0, int((baseheight-hsize)/2))
                    bg.paste(img, offset)
                    
                    if widget and fit_size == 6:
                        if widget in [self.label, self.label_new]:
                            try:
                                img.save(str(fanart), 'JPEG', quality=100)
                            except Exception as err:
                                logger.error(err)
                                self.handle_png_to_jpg(fanart, img)
                        elif widget == self.float_window:
                            tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                            try:
                                bg.save(str(tmp_img), 'JPEG', quality=100)
                            except Exception as err:
                                print(err)
                                self.handle_png_to_jpg(tmp_img, bg)
                            return tmp_img
                    elif widget_size:
                        tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                        try:
                            img.save(str(tmp_img), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(tmp_img, img)
                        return tmp_img
                    elif fit_size == 4:
                        try:
                            bg.save(str(fanart), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(fanart, bg)
                    else:
                        tmp_img = (os.path.join(TMPDIR, 'tmp.jpg'))
                        try:
                            bg.save(str(tmp_img), 'JPEG', quality=100)
                        except Exception as err:
                            print(err)
                            self.handle_png_to_jpg(tmp_img, bg)
                        return tmp_img
        except Exception as e:
            print(e, ':Error in resizing and changing aspect ratio --13353--')
    
    def handle_png_to_jpg(self, fanart, img):
        newfanart = fanart.rsplit('.')[0]+'.png'
        img.save(str(newfanart), 'PNG', quality=100)
        img_new = Image.open(newfanart)
        img_new_rgb = img_new.convert("RGB")
        img_new_rgb.save(fanart, 'JPEG', quality=100)
    
    def change_aspect_only(self, picn):
        global screen_height, screen_width
        basewidth = self.label.maximumWidth()
        baseheight = self.label.maximumHeight()
        #mask = Image.new('L', (100, 100), 0)
        try:
            img = Image.open(str(picn))
        except Exception as e:
            print(e, 'Error in opening image, videoImage, ---13364')
            picn = os.path.join(home, 'default.jpg')
            img = Image.open(str(picn))
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        sz = (basewidth, hsize)
        if hsize > baseheight:
            wp = float(baseheight/hsize)
            nbw = int(float(wp)*float(basewidth))
            img = img.resize((nbw, baseheight), PIL.Image.ANTIALIAS)
            bg = Image.new('RGB', (nbw, baseheight))
        else:
            img = img.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
            bg = Image.new('RGB', (basewidth, hsize))
        tmp_img = (os.path.join(TMPDIR, 'new_tmp.jpg'))
        bg.paste(img, (0, 0))
        bg.save(str(tmp_img), 'JPEG', quality=100)
        #img.save(str(tmp_img), 'JPEG', quality=100)
        return tmp_img

    def videoImage(self, picn, thumbnail, fanart, summary, mode=None):
        global screen_height, screen_width
        if self.image_fit_option_val in range(1, 11):
            if self.image_fit_option_val !=6:
                img_opt = self.image_fit_option_val
            else:
                img_opt = 1
        else:
            img_opt = 2
        logger.info('img_opt={0}'.format(img_opt))
        self.label.clear()
        print(self.label.maximumWidth(), '--max--width--label--')
        try:
            image_dir, image_name = os.path.split(fanart)
            original_fanart = os.path.join(image_dir, 'original-fanart.jpg')
            logger.info('videoimage picn file is {0}'.format(picn))
            if os.path.isfile(str(picn)):
                if not os.path.isfile(fanart):
                    if not os.path.exists(original_fanart):
                        shutil.copy(picn, original_fanart)
                    self.image_fit_option(picn, fanart, fit_size=img_opt)
                get_thumbnail = False
                if os.path.isfile(thumbnail):
                    if not os.stat(thumbnail).st_size:
                        get_thumbnail = True
                elif not os.path.isfile(thumbnail):
                    get_thumbnail = True
                    #self.image_fit_option(picn, thumbnail, fit_size=450)
                if get_thumbnail:
                    self.image_fit_option(picn, thumbnail, fit_size=6, widget=self.label)
                poster = picn
                picn = thumbnail
                if (picn == thumbnail == fanart):
                    pass
                else:
                    QtCore.QTimer.singleShot(100, partial(set_mainwindow_palette, fanart, theme=self.player_theme))
                try:
                    poster_dir, _ = os.path.split(poster)
                    poster_picn = os.path.join(poster_dir, 'thumbnail.jpg')
                    if 'poster.jpg' in poster:
                        #picn = self.change_aspect_only(poster)
                        if not os.path.exists(poster_picn):
                            self.image_fit_option(poster, poster_picn, fit_size=6, widget=self.label)
                        picn = poster_picn
                except Exception as e:
                    print(e, '--10147--')
                    
                logger.info(picn)
                self.label.setPixmap(QtGui.QPixmap(picn, "1"))
                if not self.float_window.isHidden():
                    picn = self.image_fit_option(
                        picn, fanart, fit_size=2, widget=self.float_window
                        )
                    self.float_window.setPixmap(QtGui.QPixmap(picn, "1"))
            else:
                if os.path.exists(self.default_background):
                    dir_n, p = os.path.split(self.default_background)
                    new_jpg =  os.path.join(dir_n, 'default_poster.jpg')
                    if not os.path.exists(new_jpg):
                        picn = self.change_aspect_only(self.default_background)
                        shutil.copy(picn, new_jpg)
                    self.label.setPixmap(QtGui.QPixmap(new_jpg, "1"))
        except Exception as e:
            print(e, '--error--in processing image--VideoImage 13432')
            if os.path.exists(self.default_background):
                QtCore.QTimer.singleShot(10, partial(set_mainwindow_palette, self.default_background, theme=self.player_theme))
                dir_n, p = os.path.split(self.default_background)
                new_jpg =  os.path.join(dir_n, 'default_poster.jpg')
                if not os.path.exists(new_jpg):
                    picn = self.change_aspect_only(self.default_background)
                    shutil.copy(picn, new_jpg)
                self.label.setPixmap(QtGui.QPixmap(new_jpg, "1"))

        if summary:
            self.text.clear()
            self.text.setText(summary)
        elif mode is None or mode == 'no summary':
            txt_old = self.text.toPlainText()
            if self.list2.item(self.cur_row):
                txt = self.list2.item(self.cur_row).text()
                if txt.startswith(self.check_symbol):
                    txt = txt.replace(self.check_symbol, '', 1)
            else:
                txt = 'No Summary Available'
            if txt_old.startswith('Air Date:'):
                pass
            else:
                self.text.setText(txt)
            logger.debug(txt)

    def playlistUpdate(self):
        global home
        row = self.list2.currentRow()
        item = self.list2.item(row)
        if item:
            i = str(self.list2.item(row).text())
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
                self.epn_arr_list[row] = '#'+self.epn_arr_list[row]
            else:
                self.list2.item(row).setText(i)
            self.list2.setCurrentRow(row)
            if self.list1.currentItem():
                file_path = os.path.join(home, 'Playlists', self.list1.currentItem().text())
                write_files(file_path, self.epn_arr_list, line_by_line=True)

    def get_file_name(self, row, list_widget):
        global name, site
        file_name_mkv = ''
        file_name_mp4 = ''
        if list_widget.item(row):
            new_epn = list_widget.item(row).text().replace('#', '', 1)
        else:
            new_epn = ''
        final_val = ''
        if row < len(self.epn_arr_list):
            if '\t' in self.epn_arr_list[row]:
                final_val = self.epn_arr_list[row].split('\t')[1]
            else:
                final_val = self.epn_arr_list[row]
            if final_val.startswith('abs_path=') or final_val.startswith('relative_path='):
                final_val = self.if_path_is_rel(final_val, thumbnail=True)
        if new_epn.startswith(self.check_symbol):
            new_epn = new_epn[1:]
        new_epn = new_epn.replace('/', '-')
        new_epn = new_epn.replace('"', '')
        new_epn = re.sub('"|.mkv|.mp4|.avi', '', new_epn)
        if new_epn.startswith('.'):
            new_epn = new_epn[1:]
        opt_val = self.btn1.currentText().lower()
        
        if '.' in final_val:
            _, file_ext = final_val.rsplit('.', 1)
            if file_ext in self.video_type_arr or file_ext in self.music_type_arr:
                new_epn = new_epn + '.' + file_ext
            else:
                new_epn = new_epn+'.mp4'
        else:
            new_epn = new_epn+'.mp4'
        
        logger.debug(new_epn)
        if OSNAME == 'nt':
            if '?' in new_epn:
                new_epn = new_epn.replace('?', '_')
        try:
            if (site.lower() == 'playlists' or self.music_playlist):
                try:
                    title = self.list1.currentItem().text()
                except:
                    title = name
            else:
                title = name
        except:
            title = self.epn_arr_list[row].split('	')[0]
            file_name_mkv = file_name_mp4 = final_val
            logger.info('--14986--function_get_file_name={0}-{1}'.format(file_name_mkv, file_name_mp4))
            return file_name_mp4, file_name_mkv

        if (site.lower() != 'video' and site.lower() != 'music' 
                and site.lower() != 'local' and site.lower() != 'playlists' 
                and site.lower() != 'none'):
            new_epn_mkv = new_epn
            new_epn_mp4 = new_epn
            file_name_mkv = os.path.join(self.default_download_location, title, new_epn_mkv)
            file_name_mp4 = os.path.join(self.default_download_location, title, new_epn_mp4)
        elif (site.lower() == 'playlists' or opt_val == 'youtube' or self.music_playlist):
            if list_widget == self.list2:
                st = final_val
            elif list_widget == self.list6:
                st = self.queue_url_list[row].split('	')[1]
                if st.startswith('abs_path=') or st.startswith('relative_path='):
                    st = self.if_path_is_rel(st)
            st = st.replace('"', '')
            if st.startswith('http'):
                new_epn_mkv = new_epn
                new_epn_mp4 = new_epn
                file_name_mkv = os.path.join(self.default_download_location, title, new_epn_mkv)
                file_name_mp4 = os.path.join(self.default_download_location, title, new_epn_mp4)
            else:
                new_epn_mkv = os.path.basename(st)
                new_epn_mp4 = new_epn_mkv
                file_name_mkv = st
                file_name_mp4 = st
        elif (site.lower() == 'video' or site.lower() == 'music' 
                or site.lower() == 'local' or site.lower() == 'none'):
            if not self.queue_url_list:
                print(row)
                file_name_mkv = file_name_mp4 = final_val
            else:
                queue_item = self.queue_url_list[0]
                queue_split = []
                if isinstance(queue_item, tuple):
                    file_name_mkv = file_name_mp4 = final_val
                elif row < len(self.queue_url_list):
                    queue_split = self.queue_url_list[row].split('	')
                    if len(queue_split) > 1:
                        st = queue_split[1]
                        if st.startswith('abs_path=') or st.startswith('relative_path='):
                            st = self.if_path_is_rel(st)
                        file_name_mkv = file_name_mp4 = st
                        
                
        logger.info('function---15025--{0}-{1}'.format(file_name_mkv, file_name_mp4))
        return file_name_mp4, file_name_mkv

    def play_file_now(self, file_name, win_id=None, eofcode=None):
        global current_playing_file_path, cur_label_num, sub_id, audio_id
        
        if file_name.startswith('abs_path=') or file_name.startswith('relative_path='):
            file_name = self.if_path_is_rel(file_name)
        
        self.mplayerLength = 0
        self.quit_really = 'no'
        logger.info(file_name)
        if self.mpvplayer_val.processId() == 0:
            self.initial_view_mode()
        finalUrl = file_name.replace('"', '')
        self.final_playing_url = finalUrl
        finalUrl = '"'+finalUrl+'"'
        if finalUrl.startswith('"http'):
            current_playing_file_path = finalUrl.replace('"', '')
            finalUrl = finalUrl.replace('"', '')
        else:
            current_playing_file_path = finalUrl
        setinfo = False
        if (self.mpvplayer_val.processId() > 0 and self.mpvplayer_started
                and not finalUrl.startswith('http') and not self.external_audio_file
                and (OSNAME == 'posix' or self.gapless_playback)):
            epnShow = "Playing: {0}".format(self.epn_name_in_list)
            msg = None
            cmd = None
            if not self.gapless_playback:
                if self.player_val.lower() == "mplayer":
                    msg = '\n show_text "{0}" \n'.format(epnShow)
                    cmd = '\n loadfile {0} replace \n'.format(finalUrl)
                elif self.player_val.lower() == 'mpv':
                    msg = '\n show-text "{0}" \n'.format(epnShow)
                    cmd = '\n loadfile {0} replace \n'.format(finalUrl)
                logger.info('command---------{0}--------'.format(cmd))
                if msg and cmd:
                    self.mpvplayer_val.write(bytes(msg, 'utf-8'))
                    self.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            else:
                if (eofcode == 'next' or eofcode is None) and self.playback_mode == 'playlist':
                    cmd = '\n set playlist-pos {} \n'.format(self.cur_row)
                    self.mpvplayer_val.write(bytes(cmd, 'utf-8'))
                    logger.debug(cmd)
                elif eofcode == 'end' and self.playback_mode == 'playlist':
                    logger.debug('.....Continue.....Playlist.....')
                elif self.playback_mode == 'single':
                    if self.mpvplayer_val.processId()>0:
                        self.mpvplayer_val.kill()
                        self.mpvplayer_started = False
                        self.external_audio_file = False
                    if OSNAME == 'posix':
                        if not win_id:
                            self.idw = str(int(self.tab_5.winId()))
                        else:
                            self.idw = str(win_id)
                    elif OSNAME == 'nt':
                        if win_id:
                            self.idw = str(win_id)
                        elif thumbnail_indicator and self.video_mode_index not in [1, 2]:
                            try:
                                p1 = 'self.label_epn_{0}.winId()'.format(str(self.thumbnail_label_number[0]))
                                self.idw = str(int(eval(p1)))
                            except Exception as e:
                                print(e)
                                self.idw = str(int(self.tab_5.winId()))
                        else:
                            self.idw = str(int(self.tab_5.winId()))
                    command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
                    logger.info('command: function_play_file_now = {0}'.format(command))
                    self.infoPlay(command)
            setinfo = True
        else:
            if self.mpvplayer_val.processId()>0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
                self.external_audio_file = False
            if OSNAME == 'posix':
                if not win_id:
                    self.idw = str(int(self.tab_5.winId()))
                else:
                    self.idw = str(win_id)
            elif OSNAME == 'nt':
                if win_id:
                    self.idw = str(win_id)
                elif thumbnail_indicator and self.video_mode_index not in [1, 2]:
                    try:
                        p1 = 'self.label_epn_{0}.winId()'.format(str(self.thumbnail_label_number[0]))
                        self.idw = str(int(eval(p1)))
                    except Exception as e:
                        print(e)
                        self.idw = str(int(self.tab_5.winId()))
                else:
                    self.idw = str(int(self.tab_5.winId()))
            command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
            logger.info('command: function_play_file_now = {0}'.format(command))
            self.infoPlay(command)
        seek_time = 0
        rem_quit = 0
        vol = 'auto'
        asp = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
        if self.final_playing_url in self.history_dict_obj:
            seek_time, cur_time, sub_id, audio_id, rem_quit, vol, asp = self.history_dict_obj.get(self.final_playing_url)
            cur_time = time.time()
            self.history_dict_obj.update(
                    {
                        self.final_playing_url:[
                            seek_time, cur_time, sub_id, audio_id,
                            rem_quit, vol, asp
                            ]
                    }
                )
            self.video_parameters = [
                self.final_playing_url, seek_time, cur_time,
                sub_id, audio_id, rem_quit, vol, asp
                ]
        elif site != 'Music':
            self.history_dict_obj.update(
                    {
                        self.final_playing_url:[
                            seek_time, time.time(), 'auto', 'auto',
                            rem_quit, vol, asp
                            ]
                    }
                )
        if setinfo and (site!= 'Music' or rem_quit):
            if self.mplayer_SubTimer.isActive():
                self.mplayer_SubTimer.stop()
            self.mplayer_SubTimer.start(1000)
        if not self.external_SubTimer.isActive():
            self.external_SubTimer.start(3000)
        MainWindow.setWindowTitle(self.epn_name_in_list)
        if not self.float_window.isHidden():
            self.float_window.setWindowTitle(self.epn_name_in_list)
            
    def is_artist_exists(self, row):
        try:
            arr = self.epn_arr_list[row].split('	')
        except:
            return False
        audio_file = True
        artist = ''
        if len(arr) >=3 :
            artist = arr[2].replace('"', '')
            if '.' in arr[1]:
                ext = arr[1].rsplit('.', 1)[1]
                ext = ext.replace('"', '')
                if ext != 'mp3' and ext != 'flac':
                    audio_file = False
        if artist.lower() and (artist.lower() != 'none') and not artist.startswith('http') and audio_file:
            return True
        else:
            return False

    def if_file_path_exists_then_play(self, row, list_widget, play_now=None, eofcode=None):
        global site, artist_name_mplayer
        
        file_path_name_mp4, file_path_name_mkv = self.get_file_name(row, list_widget)
        
        if ((os.path.exists(file_path_name_mp4) or os.path.exists(file_path_name_mkv)) 
                and (site.lower() != 'video' and site.lower() != 'music' 
                and site.lower() != 'local') and not self.video_local_stream):
            logger.info('now--playing: {0}-{1}'.format(file_path_name_mp4, file_path_name_mkv))
            if play_now:
                self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                if self.epn_name_in_list.startswith(self.check_symbol):
                    self.epn_name_in_list = self.epn_name_in_list[1:]
                if os.path.exists(file_path_name_mp4):
                    self.play_file_now(file_path_name_mp4, eofcode=eofcode)
                    finalUrl = file_path_name_mp4
                else:
                    self.play_file_now(file_path_name_mkv, eofcode=eofcode)
                    finalUrl = file_path_name_mkv
                finalUrl = '"'+finalUrl+'"'
                if (site.lower() == 'playlists'):
                    if self.is_artist_exists(row):
                        self.musicBackground(row, 'get now')
                        self.media_data.update_music_count('count', finalUrl)
                    else:
                        try:
                            thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                            logger.info("thumbnail path = {0}".format(thumb_path))
                            if os.path.exists(thumb_path):
                                self.videoImage(thumb_path, thumb_path, thumb_path, '')
                        except Exception as e:
                            logger.info('Error in getting Thumbnail: {0}'.format(e))
                else:
                    self.mark_addons_history_list('mark', row)
                return True
            else:
                if os.path.exists(file_path_name_mp4):
                    return file_path_name_mp4
                else:
                    return file_path_name_mkv
        elif (site.lower() == 'music' and self.list3.currentItem() 
                and (os.path.exists(file_path_name_mp4) 
                or os.path.exists(file_path_name_mkv)) and not self.video_local_stream):
            if self.list3.currentItem().text().lower() == 'playlist':
                logger.info('now--playing: {0}-{1}--8626'.format(file_path_name_mp4, file_path_name_mkv))
                if play_now:
                    self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                    if self.epn_name_in_list.startswith(self.check_symbol):
                        self.epn_name_in_list = self.epn_name_in_list[1:]
                    if os.path.exists(file_path_name_mp4):
                        self.play_file_now(file_path_name_mp4, eofcode=eofcode)
                        finalUrl = file_path_name_mp4
                    else:
                        self.play_file_now(file_path_name_mkv, eofcode=eofcode)
                        finalUrl = file_path_name_mkv
                    if list_widget == self.list6:
                        txt = self.list6.item(0).text()
                        r = self.get_index_list(list_widget, txt)
                        if r is None:
                            r = 0
                        else:
                            list_widget_row = r
                        self.list2.setCurrentRow(r)
                    else:
                        r = row
                    finalUrl = '"'+finalUrl+'"'
                    self.musicBackground(r, 'Search')
                    print(r, '--search--musicbackground--')
                    self.media_data.update_music_count('count', finalUrl)
                    return True
                else:
                    if os.path.exists(file_path_name_mp4):
                        return file_path_name_mp4
                    else:
                        return file_path_name_mkv
        elif ((os.path.exists(file_path_name_mp4) or os.path.exists(file_path_name_mkv)) 
                and (site.lower() == 'video' or site.lower() == 'music' 
                or site.lower() == 'local' or site.lower() == 'none') 
                and not self.video_local_stream):
            logger.info('now--playing: {0}-{1}'.format(file_path_name_mp4, file_path_name_mkv))
            if play_now:
                if list_widget.item(row):
                    self.epn_name_in_list = list_widget.item(row).text().replace('#', '', 1)
                    
                if self.epn_name_in_list.startswith(self.check_symbol):
                    self.epn_name_in_list = self.epn_name_in_list[1:]
                if os.path.exists(file_path_name_mp4):
                    self.play_file_now(file_path_name_mp4, eofcode=eofcode)
                    finalUrl = file_path_name_mp4
                else:
                    self.play_file_now(file_path_name_mkv, eofcode=eofcode)
                    finalUrl = file_path_name_mkv
                list_widget_row = None
                if list_widget == self.list6:
                    txt = self.list6.item(0).text()
                    r = self.get_index_list(list_widget, txt)
                    if r is None:
                        r = 0
                    else:
                        list_widget_row = r
                    self.list2.setCurrentRow(r)
                    logger.info('\n row = {0} txt= {1}\n'.format(r,txt))
                else:
                    r = row
                    
                if list_widget_row is not None:
                    row = list_widget_row
                
                finalUrl = finalUrl.replace('"', '')
                finalUrl = '"'+finalUrl+'"'
                if site.lower() == "music":
                    logger.info(finalUrl)
                    try:
                        artist_name_mplayer = self.epn_arr_list[row].split('	')[2]
                        if artist_name_mplayer.lower() == "none":
                            artist_name_mplayer = ""
                    except:
                        artist_name_mplayer = ""
                    if not 'youtube.com' in finalUrl.lower():
                        self.musicBackground(r, 'Search')
                        self.media_data.update_music_count('count', finalUrl)
                elif site.lower() == "video":
                    self.mark_video_list('mark', row)
                    self.media_data.update_video_count('mark', finalUrl, rownum=row)
                elif site.lower() == 'local':
                    self.mark_addons_history_list('mark', row)
                    
                if site.lower() == 'video':
                    try:
                        thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '', mode='no summary')
                    except Exception as e:
                        logger.error('Error in getting Thumbnail - localvideogetinlist: {0}'.format(e))
                    
                return True
            else:
                if os.path.exists(file_path_name_mp4):
                    return file_path_name_mp4
                else:
                    return file_path_name_mkv
        elif self.wget.processId() > 0 and play_now:
            return True
        else:
            return False

    def get_index_list(self, list_widget, txt):
        r = None
        txt = txt.replace('#', '', 1)
        if txt.startswith(self.check_symbol):
                txt = txt[1:]
        for i,val in enumerate(self.epn_arr_list):
            if '\t' in val:
                new_txt = val.split('\t')[0]
            else:
                new_txt = val
            if new_txt.startswith('#'):
                new_txt = new_txt[1:]
            if new_txt.lower() == txt.lower():
                r = i
            #logger.info('\ntxt={0}: new_txt={1}\n: 11116'.format(txt, new_txt))
        return r

    def set_init_settings(self):
        global music_arr_setting, default_arr_setting
        if site == "Music":
            if self.list3.currentRow() >= 0:
                music_arr_setting[0]=self.list3.currentRow()
                if self.list1.currentRow() >= 0:
                    music_arr_setting[1]=self.list1.currentRow()
                    if self.list2.currentRow() >= 0:
                        music_arr_setting[2]=self.list2.currentRow()
        else:
            if self.btn1.currentIndex() > 0:
                default_arr_setting[0]=self.btn1.currentIndex()
                if self.list3.currentRow() >= 0:
                    default_arr_setting[1]=self.list3.currentRow()
                    if self.list1.currentRow() >= 0:
                        default_arr_setting[2]=self.list1.currentRow()
                        if self.list2.currentRow() >= 0:
                            default_arr_setting[3]=self.list2.currentRow()
                if self.btnAddon.currentIndex() >= 0:
                    default_arr_setting[4]=self.btnAddon.currentIndex()

    def if_path_is_rel(self, path, thumbnail=None):
        global my_ipaddress
        nm = ''
        if path.startswith('abs_path='):
            path = path.split('abs_path=', 1)[1]
            nm = path
            nm = str(base64.b64decode(nm).decode('utf-8'))
            logger.info(nm)
            num_row = None
            if nm.startswith('http'):
                http_val = 'http'
                if ui.https_media_server:
                    http_val = "https" 
                n_url = http_val+'://'+str(self.local_ip_stream)+':'+str(self.local_port_stream)
                logger.info('abs_path_playing={0}'.format(n_url))
                if nm.startswith(n_url):
                    try:
                        num_row = self.path.rsplit('/', 1)[-1]
                        if num_row == 'server' or num_row == 'now_playing':
                            row = self.cur_row
                        else:
                            row = int(num_row)
                    except Exception as err_val:
                        print(err_val, '--1112--')
                        row = 0
                    if row < 0:
                        row = 0
                    nm = self.epn_return(row)
                    if nm.startswith('"'):
                        nm = nm.replace('"', '')
                elif 'youtube.com' in nm and not thumbnail:
                    nm = get_yt_url(nm, ui.quality_val, ui.ytdl_path, logger, mode='offline').strip()
                    if '::' in nm:
                        nm = nm.split('::')[0]
        elif path.startswith('relative_path='):
            path = path.split('relative_path=', 1)[1]
            nm = path
            nm = str(base64.b64decode(nm).decode('utf-8'))
            logger.info('------------------{0}'.format(nm))
            nm_arr = nm.split('&')
            if len(nm_arr) > 7:
                new_tmp_arr = nm_arr[3:]
                row_index = -1
                local_stream_index = -1
                for i, j in enumerate(new_tmp_arr):
                    if j.isnumeric():
                        row = int(j)
                        row_index = i
                    if j.lower() == 'true' or j.lower() == 'false':
                        local_stream = j
                        local_stream_index = i
            else:
                local_stream = nm_arr[4]
            if local_stream == 'True':
                old_nm = nm
                new_torrent_signal = DoGetSignalNew()
                if ui.https_media_server:
                    https_val = 'https'
                else:
                    https_val = 'http'
                nm = https_val+"://"+str(self.local_ip)+':'+str(self.local_port)+'/'
                new_torrent_signal.new_signal.emit(old_nm)
                logger.info('--nm---{0}'.format(nm))
            else:
                nm = self.getdb.epn_return_from_bookmark(nm, from_client=True)
        return nm
    
    def start_gapless_stream_process(self, row, link=None):
        if  ((self.tmp_pls_file_dict.get(row) is False
                and not self.mpv_prefetch_url_started
                and not self.mpv_prefetch_url_thread.isRunning()) or link):
            self.mpv_prefetch_url_started = True
            if row >= self.list2.count() and link is None:
                row = 0
            print(row)
            if (self.tmp_pls_file_lines and row < len(self.tmp_pls_file_lines)) or link is not None:
                if link is not None:
                    turl = link
                else:
                    turl = self.tmp_pls_file_lines[row]
                if turl.startswith('http'):
                    if site == 'Music':
                        yt_mode = 'yt_prefetch_a'
                    else:
                        yt_mode = 'yt_prefetch_av'
                    self.mpv_prefetch_url_thread = PlayerGetEpn(
                        self, logger, yt_mode, turl,
                        self.quality_val, self.ytdl_path, row
                        )
                    self.mpv_prefetch_url_thread.start()
                else:
                    self.tmp_pls_file_dict.update({row:True})
                    self.mpv_prefetch_url_started = False
                    
    def epnfound_now_start_prefetch(self, url_lnk, row_val, mode):
        url_lnk = url_lnk.strip()
        surl = None
        aurl = None
        nsurl = None
        if '::' in url_lnk:
            if url_lnk.count('::') == 1:
                url_lnk, aurl = url_lnk.split('::', 1)
            else:
                url_lnk, aurl, surl = url_lnk.split('::', 2)
            url_lnk = url_lnk.strip()
            if aurl.endswith('.vtt'):
                if surl:
                    surl = aurl+'::'+surl
                else:
                    surl = aurl
                aurl = None
            if surl:
                if '::' in surl:
                    for i, j in enumerate(surl.split('::')):
                        if i == 0:
                            nsurl = 'sub-file="{}"'.format(j)
                        else:
                            nsurl = nsurl + ':' + 'sub-file="{}"'.format(j)
                else:
                    nsurl = 'sub-file="{}"'.format(surl)
        logger.debug('{}::{}'.format(aurl, nsurl))
        if self.mpvplayer_val.processId() > 0:
            if self.mpv_prefetch_url_started:
                cmd_arr = []
                append_audio = False
                if aurl:
                    cmd1 = 'loadfile "{}" append audio-file="{}"'.format(url_lnk, aurl)
                    append_audio = True
                else:
                    cmd1 = 'loadfile "{}" append'.format(url_lnk)
                if nsurl:
                    if append_audio:
                        cmd1 = cmd1 + ':' + nsurl
                    else:
                        cmd1 = cmd1 + ' ' + nsurl
                cmd_arr.append(cmd1)
                if self.playback_mode == 'playlist':
                    cmd2 = 'playlist-move {} {}'.format(self.list2.count(), row_val)
                    cmd3 = 'playlist-remove {}'.format(row_val+1)
                    cmd_arr.append(cmd2)
                    cmd_arr.append(cmd3)
                cmd4 = 'set prefetch-playlist=yes'
                cmd_arr.append(cmd4)
                counter = 500
                for cmd in cmd_arr:
                    QtCore.QTimer.singleShot(
                        counter, partial(self.mpv_execute_command, cmd, row_val)
                        )
                    counter += 500
        else:
            command = self.mplayermpv_command(
                self.idw, url_lnk, self.player_val,
                s_url=surl, a_url=aurl, from_function='now_start'
                )
            self.infoPlay(command)
            if row_val < self.list2.count():
                self.list2.setCurrentRow(row_val)
                self.cur_row = row_val
                
    def mpv_execute_command(self, cmd, row):
        cmdb = bytes('\n {} \n'.format(cmd), 'utf-8')
        self.mpvplayer_val.write(cmdb)
        if cmd.startswith('set prefetch-playlist'):
            self.mpv_prefetch_url_started = False
            self.tmp_pls_file_dict.update({row:True})
        logger.debug(cmd)
        
    def epnfound_now_start_player(self, url_link, row_val):
        global site, refererNeeded, current_playing_file_path
        global refererNeeded, finalUrlFound, rfr_url
        finalUrl = url_link
        print(row_val, '--epn--row--')
        if not self.idw:
            self.idw = str(int(self.tab_5.winId()))
        if row_val.isnumeric():
            row = int(row_val)
            self.cur_row = row
            self.list2.setCurrentRow(row)
        else:
            row = row_val
        referer = ''
        aurl = None
        surl = None
        self.external_audio_file = False
        if '::' in finalUrl:
            if finalUrl.count('::') == 1:
                finalUrl, aurl = finalUrl.split('::')
            else:
                finalUrl, aurl, surl = finalUrl.split('::', 2)
            if aurl or surl:
                self.external_audio_file = True
        if isinstance(finalUrl, list):
            rfr_exists = finalUrl[-1]
            rfr_needed = False
            if rfr_exists == 'referer sent':
                rfr_needed = True
                finalUrl.pop()
            if refererNeeded or rfr_needed:
                referer = finalUrl[1]
            finalUrl = finalUrl[0]
            
        finalUrl = finalUrl.replace('"', '')
        finalUrl = finalUrl.strip()
        finalUrl = '"'+finalUrl+'"'
        try:
            finalUrl = str(finalUrl)
        except:
            finalUrl = finalUrl
        if self.music_playlist and aurl:
            finalUrl = aurl
        if self.mpvplayer_val.processId() > 0:
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False
        if self.player_val == "mpv":
            if not referer:
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val, a_url=aurl,
                    s_url=surl, from_function='now_start')
            else:
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val,
                    rfr=referer)
            logger.info(command)
            self.infoPlay(command)
        elif self.player_val == "mplayer":
            self.quit_really = "no"
            self.idw = str(int(self.tab_5.winId()))
            if site != "Music":
                self.tab_5.show()
            if not referer:
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val, a_url=aurl,
                    s_url=surl
                    )
            else:
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val,
                    rfr=referer
                    )
            logger.info(command)
            self.infoPlay(command)
        else:
            finalUrl = finalUrl.replace('"', '')
            if self.player_val.lower() in ['mpv', 'mplayer']:
                subprocess.Popen([self.player_val.lower(), finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            else:
                subprocess.Popen([self.player_val, finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            
        if not isinstance(finalUrl, list):
            self.final_playing_url = finalUrl.replace('"', '')
            if self.final_playing_url.startswith('http'):
                current_playing_file_path = self.final_playing_url
            else:
                current_playing_file_path = '"'+self.final_playing_url+'"'
        else:
            self.final_playing_url = finalUrl[0].replace('"', '')
            if refererNeeded == True:
                rfr_url = finalUrl[1].replace('"', '')
        if self.download_video == 0:
            self.initial_view_mode()
        if isinstance(row, int):
            if '	' in self.epn_arr_list[row]:
                epn_name = (self.epn_arr_list[row]).split('	')[0]
            else:
                epn_name = self.epn_arr_list[row]
        else:
            epn_name = row
        self.epn_name_in_list = epn_name.replace('#', '', 1)
        if isinstance(row, int):
            self.paste_background(row)
        
    def epnfound(self):
        global site, epn, epn_goto, mirrorNo
        global finalUrl, home, hdr, path_Local_Dir
        global siteName, finalUrlFound, refererNeeded, show_hide_player
        global show_hide_cover
        global new_epn, buffering_mplayer
        global opt_movies_indicator
        global name, artist_name_mplayer, rfr_url, server
        global current_playing_file_path
        global music_arr_setting, default_arr_setting, local_torrent_file_path
        buffering_mplayer="no"
        self.list4.hide()
        self.player_play_pause.setText(self.player_buttons['pause'])
        self.quit_really = "no"
        finalUrl = ''
        try:
            server._emitMeta("Play", site, self.epn_arr_list)
        except:
            pass

        if self.video_local_stream:
            tmp_pl = os.path.join(TMPDIR, 'player_stop.txt')
            if os.path.exists(tmp_pl):
                os.remove(tmp_pl)

        if (self.mpvplayer_val.processId() > 0 and (current_playing_file_path.startswith('http') 
                or current_playing_file_path.startswith('"http'))):
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False

        if epn_goto == 0 and site != "PlayLists" and self.download_video == 0:
            if self.list2.currentItem():
                epn = (self.list2.currentItem().text())
            else:
                return 0
            self.epn_name_in_list = epn
            if not epn:
                return 0

            row = self.list2.currentRow()

            if '	' in self.epn_arr_list[row]:
                epn = (self.epn_arr_list[row]).split('	')[1]
            else:
                epn = self.epn_arr_list[row].replace('#', '', 1)
            epn = epn.replace('#', '', 1)
            if epn.startswith(self.check_symbol):
                epn = epn[1:]

        self.set_init_settings()

        row = self.list2.currentRow()
        if self.if_file_path_exists_then_play(row, self.list2, True):
            self.initial_view_mode()
            return 0

        if(site!="PlayLists" and site !="None" and site!= "Music" 
                and site != "Video" and site!= "Local"):
            if siteName:
                hist_path = os.path.join(home, 'History', site, siteName, name, 'Ep.txt')
            else:
                hist_path = os.path.join(home, 'History', site, name, 'Ep.txt')
            logger.info('hist_path={0}'.format(hist_path))
            if ((os.path.exists(hist_path) and (epn_goto == 0)) 
                        or (os.path.exists(hist_path) and bookmark)):
                    if self.epn_arr_list[row].startswith('#'):
                        n_epn = self.epn_arr_list[row]
                        txt = n_epn.replace('#', self.check_symbol, 1)
                    else:
                        n_epn = '#'+self.epn_arr_list[row]
                        file_path = hist_path
                        lines = open_files(file_path, True)
                        if row < len(lines):
                            if "\n" in lines[row]:
                                lines[row] = n_epn + "\n"
                            else:
                                lines[row] = n_epn
                            write_files(file_path, lines, line_by_line=True)
                        else:
                            logger.debug('row > playlist')
                        txt = self.check_symbol + self.epn_arr_list[row]
                    txt = txt.replace('_', ' ', 1)
                    if '	' in txt:
                        txt = txt.split('	')[0]
                    self.list2.item(row).setText(txt)

            else:
                i = str(self.list2.item(row).text())
                i = i.replace('_', ' ')
                if not i.startswith(self.check_symbol):
                    self.list2.item(row).setText(self.check_symbol+i)
                else:
                    self.list2.item(row).setText(i)
                #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
                self.list2.setCurrentRow(row)

            if site != "Local":
                try:
                    self.progressEpn.setFormat('Wait..')
                    if self.video_local_stream:
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                row_file = os.path.join(TMPDIR, 'row.txt')
                                f = open(row_file, 'w')
                                f.write(str(row))
                                f.close()
                                if self.https_media_server:
                                    https_val = 'https'
                                else:
                                    https_val = 'http'
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Next', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                            
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        #finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, quality)
                        if not self.epn_wait_thread.isRunning():
                            self.epn_wait_thread = PlayerGetEpn(
                                self, logger, 'addons', name, epn, mirrorNo,
                                self.quality_val, row)
                            self.epn_wait_thread.start()
                except Exception as e:
                    print(e)
                    self.progressEpn.setFormat('Load Failed!')
                    return 0
        elif site == "PlayLists":
            row = self.list2.currentRow()
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) >= 2:
                    path_rel = arr[1]
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        arr[1] = self.if_path_is_rel(path_rel)
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                self.epn_name_in_list = arr[0]
                epn = self.epn_name_in_list
                self.playlistUpdate()
                if self.gapless_network_stream:
                    yt_mode = 'yt_prefetch_av'
                else:
                    yt_mode = 'yt'
                if 'youtube.com' in finalUrl or finalUrl.startswith('ytdl:'):
                    print(self.epn_wait_thread.isRunning())
                    if not self.epn_wait_thread.isRunning():
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, yt_mode, finalUrl, self.quality_val,
                            self.ytdl_path, row)
                        self.epn_wait_thread.start()
        elif site == "None" or site == "Music" or site == "Video" or site == "Local":
            if site == "Local" and opt == "History":
                self.mark_History()
            if '	' in self.epn_arr_list[row]:
                    finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
            else:
                    finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if self.list3.currentItem():
                if site.lower() == 'music' and self.list3.currentItem().text().lower() == 'playlist':
                    path_rel = finalUrl.replace('"', '')
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        finalUrl = '"'+self.if_path_is_rel(path_rel)+'"'
            logger.info(finalUrl)
            i = str(self.list2.item(row).text())
            i = i.replace('_', ' ')
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
            else:
                self.list2.item(row).setText(i)
            #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
            self.list2.setCurrentRow(row)
            if self.gapless_network_stream:
                yt_mode = 'yt_prefetch_a'
            else:
                if self.music_playlist:
                    yt_mode = 'yt_music'
                else:
                    yt_mode = 'yt'
            if site == 'None' and self.video_local_stream:
                    finalUrl = self.local_torrent_open(local_torrent_file_path)
            elif site == 'None' and self.btn1.currentText().lower() == 'youtube':
                    if not self.epn_wait_thread.isRunning():
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, yt_mode, finalUrl, self.quality_val,
                            self.ytdl_path, row)
                        self.epn_wait_thread.start()
            if 'youtube.com' in finalUrl.lower() or finalUrl.startswith('ytdl:'):
                if not self.epn_wait_thread.isRunning():
                    self.epn_wait_thread = PlayerGetEpn(
                        self, logger, yt_mode, finalUrl, self.quality_val,
                        self.ytdl_path, row)
                    self.epn_wait_thread.start()
                
        new_epn = self.epn_name_in_list
        
        self.idw = str(int(self.tab_5.winId()))
        if site != "Music":
            self.tab_5.show()
            
        #logger.info(finalUrl)
        print("***********", self.epn_wait_thread.isRunning())
        if (site == "Local" or site == "Video" or site == "Music" or site == "None" 
                or site == "PlayLists" and (not type(finalUrl) is list 
                or (type(finalUrl) is list and len(finalUrl) == 1)) 
                and self.download_video == 0 and not self.epn_wait_thread.isRunning()):
            if type(finalUrl) is list:
                finalUrl = finalUrl[0]
                
            finalUrl = finalUrl.replace('"', '')
            
            finalUrl = '"'+finalUrl+'"'
            try:
                finalUrl = str(finalUrl)
            except:
                finalUrl = finalUrl
            if self.mpvplayer_val.processId() > 0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
            if self.player_val == "mpv":
                command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
                logger.info(command)
                logger.debug('**********************8808-----')
                self.infoPlay(command)
            elif self.player_val == "mplayer":
                self.quit_really = "no"
                
                self.idw = str(int(self.tab_5.winId()))
                if site != "Music":
                    self.tab_5.show()
                command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
                logger.info(command)
                self.infoPlay(command)
            else:
                finalUrl = finalUrl.replace('"', '')
                if self.player_val.lower() in ['mpv', 'mplayer']:
                    subprocess.Popen([self.player_val.lower(), finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                else:
                    subprocess.Popen([self.player_val, finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        elif not self.epn_wait_thread.isRunning():
            if self.download_video == 0 and self.player_val == "mpv":
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                if isinstance(finalUrl, list):
                    rfr_exists = finalUrl[-1]
                    rfr_needed = False
                    if rfr_exists == 'referer sent':
                        rfr_needed = True
                        finalUrl.pop()
                    if finalUrlFound == True or refererNeeded == True or site=="PlayLists" or rfr_needed:
                        if refererNeeded == True or rfr_needed:
                            rfr_url = finalUrl[1]
                            nepn = '"'+str(finalUrl[0])+'"'
                            command = self.mplayermpv_command(self.idw, nepn, self.player_val, rfr=rfr_url)
                        else:
                            nepn = str(finalUrl[0])
                            command = self.mplayermpv_command(self.idw, nepn, self.player_val)
                        logger.info(command)
                    
                    else:
                    
                        self.queue_url_list[:]=[]
                        epnShow = finalUrl[0]
                        for i in range(len(finalUrl)-1):
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        command = self.mplayermpv_command(self.idw, epnShow, self.player_val)
                    self.infoPlay(command)
                else:
                    if '""' in finalUrl:
                        finalUrl = finalUrl.replace('""', '"')
                    try:
                        finalUrl = str(finalUrl)
                    except:
                        finalUrl = finalUrl
                    command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
                    self.infoPlay(command)
            elif self.download_video == 0 and self.player_val != "mpv":
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                if isinstance(finalUrl, list):
                    rfr_exists = finalUrl[-1]
                    rfr_needed = False
                    if rfr_exists == 'referer sent':
                        rfr_needed = True
                        finalUrl.pop()
                    if finalUrlFound == True or site=="PlayLists" or rfr_needed:
                        if refererNeeded == True or rfr_needed:
                            rfr_url = finalUrl[1]
                            if self.player_val == "mplayer":
                                self.quit_really = "no"
                                self.idw = str(int(self.tab_5.winId()))
                                self.tab_5.show()
                                final_url = str(finalUrl[0])
                                command = self.mplayermpv_command(self.idw, final_url, self.player_val, rfr=rfr_url)
                                logger.info(command)
                                self.infoPlay(command)
                            else:
                                if self.player_val.lower() in ['mpv', 'mplayer']:
                                    subprocess.Popen([self.player_val.lower(), "-referrer", rfr_url, finalUrl[0]])
                                else:
                                    subprocess.Popen([self.player_val, "-referrer", rfr_url, finalUrl[0]])
                        else:
                            if self.player_val == "mplayer":
                                self.quit_really = "no"
                                self.idw = str(int(self.tab_5.winId()))
                                self.tab_5.show()
                                final_url = str(finalUrl[0])
                                command = self.mplayermpv_command(self.idw, final_url, self.player_val)
                                logger.info(command)
                                self.infoPlay(command)
                            else:
                                final_url = str(finalUrl[0])
                                if self.player_val.lower() in ['mpv', 'mplayer']:
                                    subprocess.Popen([self.player_val.lower(), final_url])
                                else:
                                    subprocess.Popen([self.player_val, final_url])
                    else:
                        epnShow = finalUrl[0]
                        for i in range(len(finalUrl)-1):
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        command = self.mplayermpv_command(self.idw, epnShow, self.player_val)
                        logger.info(command)
                        self.infoPlay(command)
                else:
                    print(self.player_val)
                    logger.info("15712:Final Url mplayer = {0}".format(finalUrl))
                    if '""' in finalUrl:
                        finalUrl = finalUrl.replace('""', '"')
                    finalUrl = str(finalUrl)
                    if self.player_val == "mplayer":
                        self.quit_really = "no"
                        self.idw = str(int(self.tab_5.winId()))
                        self.tab_5.show()
                        command = self.mplayermpv_command(self.idw, finalUrl, self.player_val)
                        logger.info(command)
                        self.infoPlay(command)
                    else:
                        finalUrl = re.sub('"', "", finalUrl)
                        if self.player_val.lower() in ['mpv', 'mplayer']:
                            subprocess.Popen([self.player_val.lower(), finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        else:
                            subprocess.Popen([self.player_val, finalUrl], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            elif self.download_video == 1 and refererNeeded == False:
                if type(finalUrl) is list:
                    j = 0
                    length = len(finalUrl)
                    for i in finalUrl:
                        if length == 1:
                            nepn1 = new_epn
                        else:
                            nepn1 = new_epn + "-Part-" + str(j+1)
                        subprocess.Popen(["uget-gtk", "--quiet=yes",
                            "--http-user-agent="+hdr, finalUrl[j],
                            "--filename="+nepn1+".mp4"])
                        j = j+1
                else:
                    finalUrl = finalUrl.replace('"', '')
                    self.list2.setFocus()
                    r = self.list2.currentRow()
                    print(r)
                    new_epn = self.list2.item(row).text()
                    if new_epn.startswith(self.check_symbol):
                        new_epn = new_epn.replace(self.check_symbol, '', 1)
                    new_epn = new_epn.replace('/', '-')
                    new_epn = new_epn.replace('"', '')
                    if new_epn.startswith('.'):
                        new_epn = new_epn[1:]
                    if finalUrl.endswith('.mkv'):
                        new_epn = new_epn+'.mkv'
                    else:
                        new_epn = new_epn+'.mp4'
                    if site.lower() == 'playlists':
                        title = self.list1.currentItem().text()
                    else:
                        title = name
                    folder_name = os.path.join(self.default_download_location, title)
                    if not os.path.exists(folder_name):
                        os.makedirs(folder_name)
                    npn = os.path.join(folder_name, new_epn)
                    
                    if finalUrl.startswith('http'):
                        command = wget_string(finalUrl, npn, self.get_fetch_library)
                        logger.info(command)
                        self.infoWget(command, 0)
                self.download_video = 0
            elif refererNeeded == True and self.download_video == 1:
                rfr = finalUrl[1]
                logger.info(rfr)
                url1 = re.sub('#', '', finalUrl[0])
                logger.info(url1)
                url1 = str(url1)
                command = wget_string(
                    url1, os.path.join(TMPDIR, new_epn), self.get_fetch_library, rfr)
                logger.info(command)
                self.infoWget(command, 0)
                self.download_video = 0
                
        if epn_goto == 0:
            self.list2.setCurrentRow(row)
        epn_goto = 0
        
        if not self.epn_wait_thread.isRunning():
            if not isinstance(finalUrl, list):
                self.final_playing_url = finalUrl.replace('"', '')
                if self.final_playing_url.startswith('http'):
                    current_playing_file_path = self.final_playing_url
                else:
                    current_playing_file_path = '"'+self.final_playing_url+'"'
            else:
                self.final_playing_url = finalUrl[0].replace('"', '')
                if refererNeeded == True:
                    rfr_url = finalUrl[1].replace('"', '')
                    
            if self.download_video == 0:
                self.initial_view_mode()
            self.epn_name_in_list = self.epn_name_in_list.replace('#', '', 1)
            
            self.paste_background(row)


    def start_torrent_stream(
            self, name_file, epn_index, local_ip, status, path_folder, session, 
            site_name=None, from_client=None):
        global site, home
        torrent_thread = None
        index = int(epn_index)
        ip_n = local_ip.rsplit(':', 1)
        ip = ip_n[0]
        port = int(ip_n[1])
        path = path_folder
        if site_name:
            site_name_val = site_name
        else:
            if from_client:
                site_name_val = 'Torrent'
            else:
                site_name_val = site
        site_home = os.path.join(home, 'History', site_name_val)
        torrent_dest = os.path.join(site_home, name_file+'.torrent')
        logger.info('torrent_dest={0} ; index={1}; path={2}'.format(torrent_dest, index, path))
        if self.https_media_server:
            https_val = 'https'
        else:
            https_val = 'http'
        url = https_val+'://'+ip+':'+str(port)+'/'
        print(url, '-local-ip-url', status)
        
        if status.lower() == 'get next':
            self.torrent_handle = set_new_torrent_file_limit(
                torrent_dest, index, path, self.stream_session, self.list6, 
                self.progress, TMPDIR, self.media_server_key, self.client_auth_arr)
        else:
            print('--line--15410--', self.thread_server.isRunning(), '=thread_server')
            if status.lower() =='first run' and not self.thread_server.isRunning():
                thread_server = ThreadServer(
                    ip, port, self.media_server_key, self.client_auth_arr, 
                    self.https_media_server, self.https_cert_file, self)
                thread_server.start()
            print('--line--15415--', self.thread_server.isRunning(), '=thread_server')
            handle, ses, info, cnt, cnt_limit, file_name = get_torrent_info(
                                    torrent_dest, index, path, session, self.list6, 
                                    self.progress, TMPDIR, self.media_server_key, 
                                    self.client_auth_arr)
            print('--line--15419--', self.do_get_thread.isRunning(), '--do_get--')
            if not self.do_get_thread.isRunning():
                torrent_thread = TorrentThread(
                                handle, cnt, cnt_limit, ses, row=index, 
                                from_client=from_client)
                torrent_thread.start()
            print('--line--15425--', self.do_get_thread.isRunning(), '--do_get--')
            if self.progress.isHidden():
                self.progress.show()
            if from_client:
                self.progress.hide()
                self.started_from_external_client = True
            else:
                self.started_from_external_client = False
            if status.lower() == 'first run':
                self.list6.clear()
                i=0
                for f in info.files():
                    file_path = f.path
                    file_exists = False
                    new_path = os.path.join(path, file_path)
                    new_size = f.size
                    if os.path.exists(new_path) and os.stat(new_path).st_size == new_size:
                        file_exists = True
                    if i > index and not file_exists:
                        txt = os.path.basename(file_path)+':'+str(i)
                        self.list6.addItem(txt)
                    i = i+1
                return url, thread_server, torrent_thread, ses, handle
            else:
                if torrent_thread is None:
                    torrent_thread = self.do_get_thread
                return url, torrent_thread, ses, handle
    
    def initial_view_mode(self):
        global site, show_hide_player
        
        if site.lower() == "music" and show_hide_player == 0:
            if self.float_window.isHidden():
                self.tab_5.hide()
        else:
            if self.player_val in ['mpv', 'mplayer']:
                self.tab_5.show()
                self.list1.hide()
                self.frame.hide()
                self.text.hide()
                self.label.hide()
                self.label_new.hide()
            
    def local_torrent_open(self, tmp, start_now=None):
        global local_torrent_file_path, site
        if not self.local_ip:
            self.local_ip = get_lan_ip()
        if not self.local_port:
            self.local_port = 8001
        
        ip = self.local_ip
        port = int(self.local_port)
        if not self.thread_server.isRunning():
            self.thread_server = ThreadServer(
                ip, port, self.media_server_key, self.client_auth_arr, 
                self.https_media_server, self.https_cert_file, ui=self)
            self.thread_server.start()
        logger.info(tmp)
        tmp = str(tmp)
        if self.torrent_type == 'magnet' or 'magnet:' in tmp:
            
            if tmp.startswith('magnet:'):
                print('------------magnet-----------')
                path = self.torrent_download_folder
                torrent_dest = local_torrent_file_path
                logger.info('torrent_dest={0};path={1}'.format(torrent_dest, path))
                
                self.torrent_handle, self.stream_session, info = get_torrent_info_magnet(
                        tmp, path, self.list6, self.progress, self.tmp_download_folder)
                #self.handle.pause()
                file_arr = []
                self.list2.clear()
                self.epn_arr_list[:]=[]
                mycopy = []
                for f in info.files():
                    file_path = f.path
                    #if '/' in f.path:
                    #	file_path = file_path.split('/')[-1]
                    file_path = os.path.basename(file_path)
                    ##Needs Verification
                    self.epn_arr_list.append(file_path+'	'+path)
                    self.list2.addItem((file_path))
                mycopy = self.epn_arr_list.copy()
                self.torrent_handle.pause()
                self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                self.torrent_handle.set_download_limit(self.torrent_download_limit)
                if start_now:
                    pass
            else:
                index = int(self.list2.currentRow())
                
                cnt, cnt_limit = set_torrent_info(
                    self.torrent_handle, index, self.torrent_download_folder, 
                    self.stream_session, self.list6, self.progress, 
                    self.tmp_download_folder, self.media_server_key, 
                    self.client_auth_arr)
                
                self.do_get_thread = TorrentThread(
                    self.torrent_handle, cnt, cnt_limit, self.stream_session)
                self.do_get_thread.start()
                if self.https_media_server:
                    https_val = 'https'
                else:
                    https_val = 'http'
                url = https_val+'://'+ip+':'+str(port)+'/'
                print(url, '-local-ip-url')
            
                return url
            
        else:
            index = int(self.list2.currentRow())
            path = self.torrent_download_folder
            
            torrent_dest = local_torrent_file_path
            logger.info('torrent_dest={0};index={1};path={2}'.format(torrent_dest, index, path))
            
            self.torrent_handle, self.stream_session, info, cnt, cnt_limit, file_name = get_torrent_info(
                    torrent_dest, index, path, self.stream_session, self.list6, 
                    self.progress, self.tmp_download_folder, self.media_server_key, 
                    self.client_auth_arr)
            
            self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
            self.torrent_handle.set_download_limit(self.torrent_download_limit)
            
            self.do_get_thread = TorrentThread(
                self.torrent_handle, cnt, cnt_limit, self.stream_session)
            self.do_get_thread.start()
            if self.https_media_server:
                https_val = 'https'
            else:
                https_val = 'http'
            url = https_val+'://'+ip+':'+str(port)+'/'
            print(url, '-local-ip-url', site)
            
            return url
                
    def epn_return(self, row, mode=None):
        global site, epn_goto, mirrorNo
        global finalUrl, home, hdr, path_Local_Dir
        global new_epn, buffering_mplayer
        global path_final_Url, siteName, finalUrlFound, refererNeeded, category
        
        if self.if_file_path_exists_then_play(row, self.list2, False):
            finalUrl = self.if_file_path_exists_then_play(row, self.list2, False)
            finalUrl = finalUrl.replace('"', '')
            finalUrl = '"'+finalUrl+'"'
            return finalUrl
        
        item = self.list2.item(row)
        if item:
            epn = item.text()
            epn = epn.replace('#', '', 1)
        else:
            return ''
        if '	' in self.epn_arr_list[row]:
            epn = (self.epn_arr_list[row]).split('	')[1]
        else:
            epn = self.epn_arr_list[row].replace('#', '', 1)
        if site == "PlayLists":
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                epn = arr[0]
                if 'youtube.com' in finalUrl or finalUrl.startswith('ytdl:'):
                    if self.gapless_network_stream:
                        yt_mode = 'yt_prefetch_a'
                    else:
                        if self.music_playlist:
                            yt_mode = 'yt_music'
                        else:
                            yt_mode = 'yt'
                    finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode=yt_mode).strip()
                    
        
        if (site!="PlayLists" and site!= "None" and site != "Music" 
                and site != "Video" and site !="Local"):
            if site != "Local":
                try:
                    if self.video_local_stream:
                        if self.https_media_server:
                            https_val = 'https'
                        else:
                            https_val = 'http'
                        finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                        print(finalUrl, '=finalUrl--torrent--')
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                row_file = os.path.join(TMPDIR, 'row.txt')
                                f = open(row_file, 'w')
                                f.write(str(row))
                                f.close()
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Next', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, self.quality_val)
                except:
                    return ''
        elif site=="None" or site == "Music" or site == "Video" or site == "Local":
            if '	' in self.epn_arr_list[row]:
                finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
                
            else:
                finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if site == 'None' and self.btn1.currentText().lower() == 'youtube':
                    finalUrl = finalUrl.replace('"', '')
                    if mode == 'offline':
                        finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode='offline').strip()
                        if '::' in finalUrl:
                            finalUrl = finalUrl.split('::')[0]
                    else:
                        finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger).strip()
                    finalUrl = '"'+finalUrl+'"'
            if 'youtube.com' in finalUrl.lower():
                finalUrl = finalUrl.replace('"', '')
                if self.gapless_network_stream:
                    yt_mode = 'yt_prefetch_a'
                else:
                    if self.music_playlist:
                        yt_mode = 'yt_music'
                    else:
                        yt_mode = 'yt'
                finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode=yt_mode).strip()
        return finalUrl
        
    def watchDirectly(self, finalUrl, title, quit_val):
        global site
        global path_final_Url, current_playing_file_path
        self.cur_row = 0
        if title:
            self.epn_name_in_list = title
        else:
            self.epn_name_in_list = 'No Title'
            
        title_sub_path = title.replace('/', '-')
        if title_sub_path.startswith('.'):
            title_sub_path = title_sub_path[1:]
        title_sub_path = os.path.join(self.yt_sub_folder, title_sub_path+'.en.vtt')
        
        if self.player_val=='mplayer':
            print(self.mpvplayer_val.processId(), '=self.mpvplayer_val.processId()')
            if (self.mpvplayer_val.processId()>0):
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
        if self.mpvplayer_val.processId() > 0:
            self.mpvplayer_val.kill()
            self.mpvplayer_started = False
        self.quit_really = quit_val
        
        self.list1.hide()
        self.text.hide()
        self.label.hide()
        self.label_new.hide()
        self.frame.hide()
        self.idw = str(int(self.tab_5.winId()))
        self.tab_5.show()
        self.tab_5.setFocus()
        
        finalUrl = str(finalUrl)
        path_final_Url = finalUrl
        current_playing_file_path = finalUrl
        a_url = None
        s_url = None
        if '::' in finalUrl:
            if finalUrl.count('::') == 1:
                finalUrl, a_url = finalUrl.split('::')
            else:
                finalUrl, a_url, s_url = finalUrl.split('::', 2)
            if a_url or s_url:
                self.external_audio_file = True
        command = self.mplayermpv_command(
            self.idw, finalUrl, self.player_val, a_url=a_url,
            s_url=s_url, from_function='now_start'
            )
        if os.path.exists(title_sub_path):
            if self.player_val == 'mpv':
                command = command+' --sub-file='+title_sub_path
                logger.info(command)
        self.infoPlay(command)
        self.tab_5.setFocus()

    def finishedM(self, nm):
        global name, site
        if (site == "Music" and self.list3.currentItem()) or (site == 'PlayLists'):
            if nm:
                m_path = os.path.join(home, 'Music', 'Artist', nm, 'poster.jpg')
                t_path = os.path.join(home, 'Music', 'Artist', nm, 'thumbnail.jpg')
                f_path = os.path.join(home, 'Music', 'Artist', nm, 'fanart.jpg')
                b_path = os.path.join(home, 'Music', 'Artist', nm, 'bio.txt')
                tmp_nm = os.path.join(TMPDIR, nm)
                logger.info(tmp_nm)
                if os.path.exists(tmp_nm+'.jpg'):
                    shutil.copy(tmp_nm+'.jpg', m_path)
                if os.path.exists(tmp_nm+'-bio.txt'):
                    shutil.copy(tmp_nm+'-bio.txt', b_path)
                if os.path.exists(b_path):
                    sumr = open_files(b_path, False)
                else:
                    sumr = "Summary Not Available"
                self.videoImage(m_path, t_path, f_path, sumr)
                self.label.show()
                self.label_new.show()
                self.text.show()
    
    def start_offline_mode(self, row, extra=None):
        global site, name, hdr
        self.queue_stop = False
        if not self.epn_wait_thread.isRunning():
            if site not in ['Video', 'Music', 'PlayLists', 'None'] and extra:
                n, e, m, q, r, s, sn, ep = extra
                self.epn_wait_thread = PlayerGetEpn(
                    self, logger, 'type_three', n, e, m, q, r, s, sn, ep)
                self.epn_wait_thread.start()
            else:
                self.epn_wait_thread = PlayerGetEpn(
                    self, logger, 'offline', row, 'offline')
                self.epn_wait_thread.start()
                
    def start_offline_mode_post(self, finalUrl, row, title=None, new_epn=None):
        global site, name, hdr
        referer = False
        if not isinstance(finalUrl, list):
            finalUrl = finalUrl.replace('"', '')
        else:
            rfr = finalUrl[1]
            logger.info(rfr)
            finalUrl = re.sub('#|"', '', finalUrl[0])
            logger.info(finalUrl)
            referer = True
        if not new_epn:
            self.list2.setFocus()
            r = self.list2.currentRow()
            print(r)
            new_epn = self.list2.item(row).text()
        if new_epn.startswith(self.check_symbol):
            new_epn = new_epn[1:] 
        new_epn = new_epn.replace('/', '-')
        new_epn = re.sub('"|.mkv|.mp4', '', new_epn)
                
        if new_epn.startswith('.'):
            new_epn = new_epn[1:]
        if '.' in finalUrl:
            _, file_ext = finalUrl.rsplit('.', 1)
            if file_ext in self.video_type_arr or file_ext in self.music_type_arr:
                new_epn = new_epn + '.' + file_ext
            else:
                new_epn = new_epn+'.mp4'
        else:
            new_epn = new_epn+'.mp4'
        if not title:
            if self.list1.currentItem():
                title = self.list1.currentItem().text()
            else:
                title = name
        folder_name = os.path.join(self.default_download_location, title)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        npn = os.path.join(folder_name, new_epn)
        if platform.system().lower() == 'linux':
            fetch_library = 'wget'
        else:
            fetch_library = self.get_fetch_library
        if finalUrl.startswith('http'):
            finalUrl = finalUrl.strip()
            if not referer:
                command = wget_string(finalUrl, npn, fetch_library)
            else:
                command = wget_string(finalUrl, npn, fetch_library, rfr)
            logger.info(command)
            self.infoWget(command, 0, fetch_library)
        self.download_video = 0
        
    def dataReadyW(self, p, get_lib):
        global new_epn, epn, opt, site
        global sizeFile
        #print('----------------', a)
        if not get_lib:
            get_fetch_lib = self.get_fetch_library.lower()
        else:
            get_fetch_lib = get_lib.lower()
        try:
            a = str(p.readAllStandardOutput(), 'utf-8').strip()
            #print(a)
        except:
            a =''
        if get_fetch_lib == 'wget':
            if "Length:" in a:
                l = re.findall('[(][^)]*[)]', a)
                if l:
                    sizeFile = l[0]
                
            if "%" in a:
                m = re.findall('[0-9][^\n]*', a)
                if m:
                    n = re.findall('[^%]*', m[0])
                    if n:
                        try:
                            val = int(n[0])
                        except:
                            val = 0
                        self.progress.setValue(val)
                    try:
                        out = str(m[0])+" "+sizeFile
                    except:
                        out = str(m[0])+" "+'0'
                    self.progress.setFormat(out)
        else:
            b = a.split(' ')
            c = []
            for i in b:
                if i:
                    c.append(i)
            
            d = []
            for j in range(len(c)):
                if j == 2 or j == 4 or j == 5 or j == 6 or j == 7 or j == 8 or j == 9:
                    pass
                else:
                    d.append(c[j])
            if d:
                try:
                    if ':' not in d[0] and len(d) > 3:
                        percent = int(d[0])
                        self.progress.setValue(percent)
                except Exception as e:
                    print(e)
            word = ' '.join(d)
            if len(c)<=3 and len(c)>=2:
                self.curl_progress_end = c[-2]+' '+c[-1]
            elif len(c)>=3:
                if ':' not in c[0]:
                    self.curl_progress_init = c[0]+'% '+c[1]+' '+c[3]
                if 'k' in c[-1]:
                    self.curl_progress_end = c[-2]+' '+c[-1]
                    
            word = self.curl_progress_init+' '+self.curl_progress_end
            self.progress.setFormat(word)
                
    def startedW(self):
        global new_epn
        self.progress.setValue(0)
        if not MainWindow.isFullScreen():
            self.progress.show()
        print("Process Started")
        
    def finishedW(self, src):
        global name, hdr, site
        print("Process Ended")
        self.progress.setValue(100)
        self.progress.hide()
        if self.tab_2.isHidden():
            pass
        type_int = False
        if self.queue_url_list and not self.queue_stop:
            type_tuple = False
            for j, i in enumerate(self.queue_url_list):
                if isinstance(i, tuple):
                    type_tuple = True
                    break
            
            if type_tuple:
                n, e, m, q, r, s, sn, ep = self.queue_url_list[j]
                self.queue_item = self.queue_url_list[j]
                itm = self.list6.item(j)
                nepn = ep
                nepn = re.sub('#|"', '', nepn)
                nepn = nepn.replace('/', '-')
                nepn = re.sub('"|.mkv|.mp4|.avi', '', nepn)
                nepn = nepn.replace('_', ' ')
                self.list6.takeItem(j)
                del itm
                del self.queue_url_list[j]
                site_tmp = s
                if not self.epn_wait_thread.isRunning():
                    if site_tmp not in ['Video', 'Music', 'PlayLists', 'None']:
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, 'type_three', n, e, m, q, r, s, sn, ep)
                        self.epn_wait_thread.start()
                    else:
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, 'offline', r, 'offline')
                        self.epn_wait_thread.start()
        
    def infoWget(self, command, src, get_library=None):
        self.wget = QtCore.QProcess()
        self.wget.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.curl_progress_init = ''
        self.curl_progress_end = ''
        self.wget.started.connect(self.startedW)
        self.wget.readyReadStandardOutput.connect(partial(self.dataReadyW, self.wget, get_library))
        self.wget.finished.connect(lambda x=src : self.finishedW(src))
        QtCore.QTimer.singleShot(1000, partial(self.wget.start, command))
    
    def change_sid_aid_video(self, sid=None, aid=None, vol=None, asp=None):
        aasp = '-1'
        if self.final_playing_url in self.history_dict_obj:
            seek_time, cur_time, ssid, aaid, rem_quit, vvol, aasp = self.history_dict_obj.get(self.final_playing_url)
            if sid:
                ssid = sid
            if aid:
                aaid = aid
            if vol:
                vvol = vol
            if asp:
                aasp = asp
            cur_time = time.time()
            self.history_dict_obj.update(
                    {
                        self.final_playing_url:[
                            seek_time, cur_time, ssid, aaid,
                            rem_quit, vvol, aasp
                            ]
                    }
                )
            self.video_parameters = [
                self.final_playing_url, seek_time, cur_time,
                ssid, rem_quit, vvol, aasp
                ]
        elif site != 'Music':
            seek_time = 0
            rem_quit = 0
            ssid = 'auto'
            aaid = 'auto'
            vvol = 'auto'
            aasp = '-1'
            if sid:
                ssid = sid
            if aid:
                aaid = aid
            if vol:
                vvol = vol
            if asp:
                aasp = asp
            self.history_dict_obj.update(
                {self.final_playing_url:[seek_time, time.time(), ssid, aaid, rem_quit, vvol, aasp]}
                )
        logger.debug('sid={}::aid={}::vol={}::aspect={}::updating file info'.format(sid, aid, vol, aasp))
                                
    def dataReady(self, p):
        global new_epn, epn, opt, site
        global cache_empty, buffering_mplayer, slider_clicked
        global artist_name_mplayer, server
        global new_tray_widget, pause_indicator
        global mpv_indicator, mpv_start, cur_label_num
        global sub_id, audio_id, current_playing_file_path, desktop_session
        
        try:
            a = str(p.readAllStandardOutput(), 'utf-8').strip()
            #logger.debug('-->{0}<--'.format(a))
            if 'volume' in a:
                logger.debug(a)
            elif 'Video' in a:
                logger.debug(a)
            elif 'Audio' in a:
                logger.info(a)
            if self.custom_mpv_input_conf and self.player_val.lower() == 'mpv':
                if 'set property: fullscreen' in a.lower():
                    logger.debug(a)
                    if (self.tab_5.width() >= screen_width
                            and self.tab_5.height() >= screen_height):
                        self.tab_5.player_fs()
                    else:
                        self.tab_5.player_fs(mode='fs')
                    a = 'FULLSCREEN_TOGGLE'
                elif 'playlist-next' in a.lower():
                    self.mpvNextEpnList()
                elif 'playlist-prev' in a.lower():
                    self.mpvPrevEpnList()
                elif 'set property: pause' in a.lower():
                    if self.mpv_custom_pause:
                        self.mpv_custom_pause = False
                        self.player_play_pause_status('play')
                    else:
                        self.mpv_custom_pause = True
                        self.player_play_pause_status('pause')
                elif 'Exiting... (Quit)' in a:
                    self.playerStop(msg='already quit')
                elif 'load_sub: load_external_subtitle' in a.lower():
                    if not self.acquire_subtitle_lock:
                        self.acquire_subtitle_lock = True
                        self.tab_5.load_external_sub()
                elif 'stop_cmd: stop_after_current_file' in a.lower():
                    self.quit_really = 'yes'
                    txt_osd = '\n show-text "Stop After Current File" \n'
                    self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                    logger.debug(a)
                elif 'set property: video-aspect=' in a.lower():
                    logger.debug(a)
                    aspect_val = a.split('video-aspect=')[1].split(' ')[0]
                    for asp_ratio in self.mpvplayer_aspect:
                        if aspect_val == self.mpvplayer_aspect[asp_ratio]:
                            self.mpvplayer_aspect_cycle = int(asp_ratio)
                            logger.info('SET ASPECT = {0}::{1}'.format(self.mpvplayer_aspect_cycle, aspect_val))
                            a = 'ASPECT CHANGED'
                            if aspect_val == '-1':
                                show_text_val = 'Original Aspect'
                            elif aspect_val == '0':
                                show_text_val = 'Aspect Ratio Disabled'
                            else:
                                show_text_val = aspect_val
                            txt_osd = '\n show-text "{0}" \n'.format(show_text_val)
                            self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                            break
                if a and 'AV:' not in a and 'A:' not in a:
                    #logger.debug('-->{0}<--'.format(a))
                    pass
            if (self.player_val.lower() == 'mpv' and self.mplayerLength
                    and ("EOF code: 1" in a
                    or "HTTP error 403 Forbidden" in a 
                    or self.progress_counter > self.mplayerLength + 1
                    or 'finished playback, success (reason 0)' in a)):
                if not self.eof_reached and not self.player_setLoop_var:
                    self.eof_reached = True
                    self.eof_lock = True
                logger.debug('<<<<<<<<<<<< start <<<<>>>>>>>>>>>>>>>>>')
                logger.debug(a)
                logger.debug('{0}::{1}'.format(self.mplayerLength, self.progress_counter))
                logger.debug('<<<<<<<<<<<<<<< end <<<<>>>>>>>>>>>>>>>')
            if 'icy info:' in a.lower() or 'icy-title:' in a.lower():
                if 'icy info:' in a.lower():
                    song_title = re.search("'[^']*", a)
                    self.epn_name_in_list = song_title.group().replace("'", '')
                else:
                    song_title = re.search("icy-title:[^\n]*", a)
                    self.epn_name_in_list = song_title.group().replace('icy-title:', '')
                print(self.epn_name_in_list, '--radio--song--')
                self.mplayerLength = 1
                self.epn_name_in_list = self.epn_name_in_list.strip()
                server._emitMeta('internet-radio#'+self.epn_name_in_list, site, self.epn_arr_list)
        except Exception as e:
            print(e)
            a = ""
        try:
            if self.player_val.lower() == "mpv":
                if "AUDIO_ID" in a or "AUDIO_KEY_ID" in a:
                    new_arr = a.split('\n')
                    a_id = None
                    for i in new_arr:
                        if i.startswith('AUDIO_ID') or i.startswith('AUDIO_KEY_ID'):
                            a_id = i.split('=')[-1]
                            break
                    if a_id is not None:
                        audio_s = (re.search('[(][^)]*', a_id))
                        if audio_s:
                            audio_id = (audio_s.group()).replace('(', '')
                        else:
                            audio_id="no"
                        self.audio_track.setText("A:"+str(a_id[:8]))
                        if 'AUDIO_KEY_ID' in a:
                            self.change_sid_aid_video(aid=audio_id)
                    else:
                        logger.error('error getting proper a_id')
                elif "SUB_ID" in a or "SUB_KEY_ID" in a:
                    tsid = sub_id
                    new_arr = a.split('\n')
                    s_id = None
                    for i in new_arr:
                        if i.startswith('SUB_ID') or i.startswith('SUB_KEY_ID'):
                            s_id = i.split('=')[-1]
                            break
                    if s_id is not None:
                        sub_s = (re.search('[(][^)]*', s_id))
                        if sub_s:
                            sub_id = (sub_s.group()).replace('(', '')
                        else:
                            sub_id = "no"
                        if tsid == 'auto' and sub_id == 'no':
                            val_id = 'auto'
                            sub_id = 'auto'
                            self.mpvplayer_val.write(b'\n cycle sub \n')
                        else:
                            val_id = str(s_id[:8])
                        self.subtitle_track.setText("Sub:"+val_id)
                        if 'SUB_KEY_ID' in a:
                            self.change_sid_aid_video(sid=sub_id)
                    else:
                        logger.error('error getting proper sub id')
                elif 'volume-print=' in a:
                    if 'ao-volume-print=' in a:
                        self.volume_type = 'ao-volume'
                    else:
                        self.volume_type = 'volume'
                    player_vol = re.search('volume-print=[0-9]+', a)
                    print(player_vol)
                    if player_vol:
                        player_vol = player_vol.group()
                        self.player_volume = player_vol.split('=')[1]
                        self.change_sid_aid_video(vol=self.player_volume)
                        logger.debug('set volume={0}'.format(self.player_volume))
                        if self.player_volume.isnumeric():
                            if self.volume_type == 'ao-volume':
                                msg_str = 'AO Volume'
                            else:
                                msg_str = 'Volume'
                            msg = '\n show-text "{}: {}%" \n'.format(msg_str, self.player_volume)
                            self.mpvplayer_val.write(bytes(msg, 'utf-8'))
                            #self.frame_extra_toolbar.slider_volume.pressed = False
                            #self.frame_extra_toolbar.slider_volume.setValue(int(self.player_volume))
                elif "LENGTH_SECONDS=" in a:
                    mpl = re.search('LENGTH_SECONDS=[0-9]+[:][0-9]+[:][0-9]+', a)
                    if not mpl:
                        mpl = re.search('LENGTH_SECONDS=[0-9]+', a)
                    logger.debug('{} {}'.format(mpl, a))
                    if mpl:
                        mpl = mpl.group()
                        logger.debug(mpl)
                        if ':' in mpl:
                            n = mpl.split('=')[1]
                            o = n.split(':')
                            self.mplayerLength = int(o[0])*3600+int(o[1])*60+int(o[2])
                            self.mpv_playback_duration = n
                        else:
                            self.mplayerLength = int(mpl.split('=')[1])
                        self.slider.setRange(0, int(self.mplayerLength))
                elif ("AV:" in a or "A:" in a) and not self.eof_reached:
                    if not mpv_start:
                        mpv_start.append("Start")
                        try:
                            msg = 'Playing: {0}'.format(self.epn_name_in_list.replace('#', '', 1))
                            MainWindow.setWindowTitle(self.epn_name_in_list)
                            if not self.float_window.isHidden():
                                self.float_window.setWindowTitle(self.epn_name_in_list)
                            msg = bytes('\n show-text "{0}" 2000 \n'.format(msg), 'utf-8')
                            self.mpvplayer_val.write(msg)
                        except Exception as err:
                            logger.error(err)
                        self.mplayer_finished_counter = 0
                        if (MainWindow.isFullScreen() and site != "Music"
                                and self.list2.isHidden() and self.tab_6.isHidden()
                                and self.tab_2.isHidden()):
                            self.gridLayout.setSpacing(0)
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            if self.tab_6.isHidden():
                                self.frame_timer.start(5000)
                        self.subMplayer()
                    if ("Buffering" in a and not mpv_indicator 
                            and (site != "Local" or site != "Music" 
                            or site != "Video")):
                        cache_empty = "yes"
                        mpv_indicator.append("cache empty") 
                        print("buffering")
                        self.mpvplayer_val.write(b'\n set pause yes \n')
                        self.player_play_pause.setText(self.player_buttons['play'])
                        if not pause_indicator:
                            pause_indicator.append('Pause')
                        if MainWindow.isFullScreen() and self.layout_mode != "Music":
                            self.gridLayout.setSpacing(0)
                            self.frame1.show()
                    timearr = re.findall("[0-9][0-9]+:[0-9][0-9]+:[0-9][0-9]+", a)
                    percomp = re.search("[(]*[0-9]*\%[)]*", a)
                    if timearr:
                        val1 = timearr[0].split(':')
                        if val1:
                            val = int(val1[0])*3600+int(val1[1])*60+int(val1[2])
                        else:
                            val = 0
                        if len(timearr) == 1:
                            end_time = '00:00:00'
                            if self.mplayerLength > 1:
                                txt = self.progressEpn.text()
                                timearr = re.findall("[0-9][0-9]+:[0-9][0-9]+:[0-9][0-9]+", txt)
                                if timearr and len(timearr) == 2:
                                    end_time = timearr[1]
                                elif self.mpv_playback_duration:
                                    end_time = self.mpv_playback_duration
                            out = timearr[0] + ' / ' + end_time
                        else:
                            out = timearr[0] + ' / ' + timearr[1]
                        per_comp = '(0%)'
                        if percomp:
                            per_comp = percomp.group()
                            if not per_comp.endswith(')'):
                                per_comp = per_comp + ')'
                        else:
                            txt = self.progressEpn.text()
                            percomp = re.search("[(]*[0-9]*\%[)]*", txt)
                            if percomp:
                                per_comp = percomp.group()
                            elif self.mplayerLength > 1:
                                per_comp = '('+str(int(100*val/self.mplayerLength))+'%)'
                                
                        out = out + ' ' + per_comp
                            
                        cache_exists = False
                        if "Cache:" in a:
                            self.cache_mpv_indicator = True
                            cache_int = 0
                            n = re.findall("Cache:[^+]*", a)
                            if 's' in n[0]:
                                cache_val = re.search("[0-9][^s]*", n[0]).group()
                            else:
                                cache_val = self.cache_mpv_counter
                            
                            try:
                                cache_int = int(cache_val)
                            except Exception as err_val:
                                print(err_val)
                                cache_int = 0
                            
                            if cache_int >= 119:
                                cache_int = 119
                            elif cache_int >=9 and cache_int < 12:
                                cache_int = 10
                            if cache_int < 10:
                                cache_val = '0'+str(cache_int)
                            else:
                                cache_val = str(cache_int)
                            cache_exists = True
                            self.cache_mpv_counter = cache_val
                        else:
                            cache_val = '00'
                            cache_int = 0
                        try:
                            new_cache_val = cache_int
                        except Exception as e:
                            print(e, '--cache-val-error--')
                            new_cache_val = 0
                        if self.cache_mpv_indicator:
                            out = out +"  Cache:"+str(self.cache_mpv_counter)+'s'
                        if "Paused" in a and not mpv_indicator:
                            out = "(Paused) "+out
                            if self.custom_mpv_input_conf:
                                self.mpv_custom_pause = True
                        elif "Paused" in a and mpv_indicator:
                            out = "(Paused Caching..) "+out
                            if self.custom_mpv_input_conf:
                                self.mpv_custom_pause = True
                        
                        
                        if not self.mplayerLength:
                            if self.mpv_cnt > 4:
                                m = re.findall('[/][^(]*', out)
                                try:
                                    n = re.sub(' |[/]', '', m[0])
                                except Exception as err_msg:
                                    print(err_msg)
                                    n = '00:00:00'
                                print(n)
                                o = n.split(':')
                                self.mplayerLength = int(o[0])*3600+int(o[1])*60+int(o[2])
                                print(self.mplayerLength, "--mpvlength", a)
                                if self.mplayerLength == 0:
                                    if self.mpv_length_find_attempt >= 4:
                                        self.mplayerLength = 1
                                        self.mpv_length_find_attempt = 0
                                        logger.warn('No Suitable length detected')
                                        msg = '\n print-text "LENGTH_SECONDS=${duration}" \n'
                                        self.mpvplayer_val.write(bytes(msg, 'utf-8'))
                                    else:
                                        self.mpv_cnt = 0
                                        self.mpv_length_find_attempt += 1
                                        logger.warn(self.mpv_length_find_attempt)
                                        msg = '\n print-text "LENGTH_SECONDS=${duration}" \n'
                                        self.mpvplayer_val.write(bytes(msg, 'utf-8'))
                                self.mpv_playback_duration = n
                                self.progressEpn.setMaximum(int(self.mplayerLength))
                                self.slider.setRange(0, int(self.mplayerLength))
                                self.mpv_cnt = 0
                            logger.debug(self.mplayerLength)
                            self.mpv_cnt = self.mpv_cnt + 1
                            if (MainWindow.isFullScreen() and site != 'Music'
                                    and self.list2.isHidden() and self.tab_6.isHidden()
                                    and self.tab_2.isHidden()):
                                self.gridLayout.setSpacing(0)
                                self.frame1.show()
                                if self.frame_timer.isActive():
                                    self.frame_timer.stop()
                                if self.tab_6.isHidden():
                                    self.frame_timer.start(2000)
                        out1 = out+" ["+self.epn_name_in_list+"]"
                        self.progressEpn.setFormat((out1))
                        if self.mplayerLength == 1:
                            val = 0
                            self.slider.setValue(0)
                        else:
                            self.slider.setValue(val)
                        if self.progress_counter == self.mplayerLength:
                            self.progress_counter += 1
                            logger.debug(self.progress_counter)
                        else:
                            self.progress_counter = val
                            if (self.gapless_network_stream and not self.queue_url_list
                                    and site in ['Music', 'PlayLists', 'None', 'NONE']): 
                                if self.progress_counter > int(self.mplayerLength/2):
                                    if self.tmp_pls_file_dict.get(self.cur_row+1) is False:
                                        self.start_gapless_stream_process(self.cur_row+1)
                        if not new_tray_widget.isHidden():
                            new_tray_widget.update_signal.emit(out, val)
                        if cache_empty == 'yes':
                            try:
                                if new_cache_val > self.cache_pause_seconds:
                                    cache_empty = 'no'
                                    self.mpvplayer_val.write(b'\n set pause no \n')
                                    self.player_play_pause.setText(self.player_buttons['pause'])
                                    if mpv_indicator:
                                        mpv_indicator.pop()
                                    if pause_indicator:
                                        pause_indicator.pop()
                                    if self.frame_timer.isActive():
                                        self.frame_timer.stop()
                                    self.frame_timer.start(100)
                            except Exception as err_val:
                                print(err_val, '--mpv--cache-error--')
                elif ("VO:" in a or "AO:" in a or 'Stream opened successfully' in a) and not self.mplayerLength:
                    self.cache_mpv_indicator = False
                    self.cache_mpv_counter = '00'
                    self.mpv_playback_duration = None
                    t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
                    self.progressEpn.setFormat((t))
                    self.eof_reached = False
                    self.eof_lock = False
                    QtCore.QTimer.singleShot(1000, partial(self.set_sub_audio_text, 'aid'))
                    QtCore.QTimer.singleShot(1500, partial(self.set_sub_audio_text, 'sid'))
                    if OSNAME == 'nt':
                        sub_spacing = self.subtitle_dict.get('sub-spacing')
                        if sub_spacing:
                            cmd = 'set sub-spacing {}'.format(sub_spacing)
                        QtCore.QTimer.singleShot(
                            2000, partial(self.mpv_execute_command, cmd, self.cur_row)
                            )
                elif (self.eof_reached and self.eof_lock 
                        and not self.epn_wait_thread.isRunning()):
                    self.eof_lock = False
                    self.eof_reached = False
                    if "EOF code: 1" in a:
                        reason_end = 'EOF code: 1'
                    else:
                        reason_end = 'length of file equals progress counter'
                    if self.final_playing_url in self.history_dict_obj:
                        param_avail = False
                        if self.video_parameters:
                            if self.final_playing_url == self.video_parameters[0]:
                                asp = self.video_parameters[-1]
                                vol = self.video_parameters[-2]
                                param_avail = True
                        if not param_avail:        
                            asp = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
                            vol = self.player_volume
                        self.history_dict_obj.update(
                            {   self.final_playing_url:[
                                    0, time.time(), sub_id, audio_id,
                                    0, vol, asp
                                ]
                            }
                            )
                        logger.debug(self.video_parameters)
                    self.cache_mpv_indicator = False
                    self.cache_mpv_counter = '00'
                    self.mpv_playback_duration = None
                    logger.debug('\ntrack no. {0} ended due to reason={1}\n::{2}'.format(self.cur_row, reason_end, a))
                    logger.debug('{0}::{1}'.format(self.mplayerLength, self.progress_counter))
                    queue_item = None
                    if self.queue_url_list:
                        queue_item = self.queue_url_list[0]
                    if self.player_setLoop_var:
                        pass
                    elif queue_item is None or isinstance(queue_item, tuple):
                        if self.list2.count() == 0:
                            return 0
                        if self.cur_row == self.list2.count() - 1:
                            self.cur_row = 0
                            if site == "Music" and not self.playerPlaylist_setLoop_var:
                                r1 = self.list1.currentRow()
                                it1 = self.list1.item(r1)
                                if it1:
                                    if r1 < self.list1.count():
                                        r2 = r1+1
                                    else:
                                        r2 = 0
                                    self.list1.setCurrentRow(r2)
                                    self.listfound()
                        else:
                            self.cur_row += 1
                        self.list2.setCurrentRow(self.cur_row)
                        logger.debug('\ncurR={0}\n'.format(self.cur_row))
                    self.mplayerLength = 0
                    self.total_file_size = 0
                    if mpv_start:
                        mpv_start.pop()
                    if "HTTP error 403 Forbidden" in a:
                        print(a)
                        self.quit_really = "yes"
                    if self.quit_really == "no" and not self.epn_wait_thread.isRunning():
                        if self.tab_5.isHidden() and thumbnail_indicator:
                            length_1 = self.list2.count()
                            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setText(self.epn_name_in_list)"
                            exec(q3)
                            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setAlignment(QtCore.Qt.AlignCenter)"
                            exec(q3)
                        if site in ["Video", "Music", "PlayLists", "None", "MyServer"]:
                            if queue_item is None or isinstance(queue_item, tuple):
                                move_ahead = True
                                if self.gapless_network_stream:
                                    if self.tmp_pls_file_dict.get(self.cur_row):
                                        if self.tmp_pls_file_lines[self.cur_row].startswith('http'):
                                            move_ahead = False
                                            tname = self.epn_arr_list[self.cur_row]
                                            if tname.startswith('#'):
                                                tname = tname.replace('#', '', 1)
                                            if '\t' in tname:
                                                self.epn_name_in_list = tname.split('\t')[0]
                                            else:
                                                self.epn_name_in_list = tname
                                            MainWindow.setWindowTitle(self.epn_name_in_list)
                                            self.float_window.setWindowTitle(self.epn_name_in_list)
                                            server._emitMeta("Next", site, self.epn_arr_list)
                                        self.tmp_pls_file_dict.update({self.cur_row:False})
                                if move_ahead:
                                    self.localGetInList(eofcode='end')
                            else:
                                self.getQueueInList(eofcode='end')
                        else:
                            if queue_item is None or isinstance(queue_item, tuple):
                                self.getNextInList(eofcode='end')
                            else:
                                self.getQueueInList(eofcode='end')
                    elif self.quit_really == "yes": 
                        self.player_stop.clicked.emit()
                        self.list2.setFocus()
            elif self.player_val.lower() == "mplayer":
                if "PAUSE" in a:
                    if buffering_mplayer != 'yes':
                        self.player_play_pause.setText(self.player_buttons['play'])
                        #print('set play button text = Play')
                    if MainWindow.isFullScreen() and self.layout_mode != "Music":
                        self.gridLayout.setSpacing(0)
                        self.frame1.show()
                        if (buffering_mplayer == "yes"):
                            if self.frame_timer.isActive:
                                self.frame_timer.stop()
                            self.frame_timer.start(10000)
                if "Cache empty" in a:
                    cache_empty = "yes"
                    
                if "ID_VIDEO_BITRATE" in a:
                    try:
                        a0 = re.findall('ID_VIDEO_BITRATE=[^\n]*', a)
                        print(a0[0], '--videobit')
                        a1 = a0[0].replace('ID_VIDEO_BITRATE=', '')
                        self.id_video_bitrate=int(a1)
                    except:
                        self.id_video_bitrate = 0
                    
                if "ID_AUDIO_BITRATE" in a:
                    try:
                        a0 = re.findall('ID_AUDIO_BITRATE=[^\n]*', a)
                        print(a0[0], '--audiobit')
                        a1 = a0[0].replace('ID_AUDIO_BITRATE=', '')
                        self.id_audio_bitrate=int(a1)
                    except:
                        self.id_audio_bitrate=0
                if "ANS_switch_audio" in a:
                    print(a)
                    audio_id = a.split('=')[-1]
                    
                    print("audio_id="+audio_id)
                    self.audio_track.setText("A:"+str(audio_id))
                if "ANS_sub" in a:
                    sub_id = a.split('=')[-1]
                    
                    print("sub_id="+sub_id)
                    self.subtitle_track.setText("Sub:"+str(sub_id))
                
                if "ID_LENGTH" in a and not self.mplayerLength:
                    t = re.findall('ID_LENGTH=[0-9][^.]*', a)
                    self.mplayerLength = re.sub('ID_LENGTH=', '', t[0])
                    print(self.mplayerLength)
                    self.mplayerLength = int(self.mplayerLength) *1000
                    self.slider.setRange(0, int(self.mplayerLength))
                    self.total_file_size = int(((self.id_audio_bitrate+self.id_video_bitrate)*self.mplayerLength)/(8*1024*1024*1000))
                    print(self.total_file_size, ' MB')
                if ("A:" in a) or ("PAUSE" in a):
                    if not mpv_start:
                        mpv_start.append("Start")
                        try:
                            if self.tab_5.mplayer_aspect_msg:
                                aspect_val = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
                                if aspect_val == '-1':
                                    show_text_val = 'Original Aspect'
                                elif aspect_val == '0':
                                    show_text_val = 'Aspect Ratio Disabled'
                                else:
                                    show_text_val = aspect_val
                                txt_osd = '\n osd_show_text "{0}" 2000\n'.format(show_text_val)
                                self.mpvplayer_val.write(bytes(txt_osd, 'utf-8'))
                                self.tab_5.mplayer_aspect_msg = False
                            else:
                                npn = '"'+"Playing: "+self.epn_name_in_list.replace('#', '', 1)+'"'
                                npn1 = bytes('\n'+'osd_show_text '+str(npn)+' 4000'+'\n', 'utf-8')
                                MainWindow.setWindowTitle(self.epn_name_in_list)
                                if not self.float_window.isHidden():
                                    self.float_window.setWindowTitle(self.epn_name_in_list)
                                self.mpvplayer_val.write(npn1)
                            self.mplayer_finished_counter = 0
                        except:
                            pass
                        if (MainWindow.isFullScreen() and self.layout_mode != "Music"
                                and self.list2.isHidden() and self.tab_2.isHidden()
                                and self.tab_6.isHidden()):
                            self.gridLayout.setSpacing(0)
                            if not self.frame1.isHidden():
                                self.frame1.hide()
                            if self.frame_timer.isActive():
                                self.frame_timer.stop()
                            self.frame_timer.start(1000)
                        self.subMplayer()
                    if "PAUSE" in a:
                        print(a, 'Pause A')
                        c = None
                        c_int = 0
                        if "%" in a:
                            #print a
                            m = a.split(' ')
                            print(m)
                            if m:
                                try:
                                    c = m[-1]
                                    if len(c) > 3:
                                        c = "0%"
                                    c_int = int(c.replace('%', '')) 
                                except Exception as e:
                                    print(e, '--percent cache error--')
                        try:
                            t = str(self.progressEpn.text())
                            if c and c_int:
                                t = re.sub('Cache:[0-9]*%', '', t)
                            t = t.strip()
                            if '(Paused) ' in t:
                                t = t.replace('(Paused) ', '')
                            if '(Paused Caching..Wait) ' in t:
                                t = t.replace('(Paused Caching..Wait) ', '')
                        except:
                            t = ""
                        #print(t, ' --t val--')
                        if buffering_mplayer == "yes" or self.mplayer_pause_buffer:
                            print('buffering mplayer')
                            if 'Cache:' not in t:
                                out = "(Paused Caching..Wait) "+t+' Cache:'+c
                            else:
                                out = "(Paused Caching..Wait) "+t
                            if ((not self.mplayer_timer.isActive()) 
                                    and (not self.video_local_stream) and c_int > 0):
                                self.mplayer_timer.start(1000)
                            elif ((not self.mplayer_timer.isActive()) 
                                    and (self.video_local_stream) and c_int > 5):
                                self.mplayer_timer.start(1000)
                            #buffering_mplayer = "no"
                        else:
                            if c_int and c:
                                out = "(Paused) "+t+' Cache:'+c
                            else:
                                out = "(Paused) "+t
                            
                            if ((not self.mplayer_timer.isActive()) 
                                    and (self.video_local_stream) and c_int > 5):
                                self.mplayer_timer.start(1000)
                        #print(out, '--out--')
                    else:
                        if "%" in a:
                            #print a
                            m = a.split(' ')
                            try:
                                c = m[-2]
                            except:
                                c = "0%"
                        else:
                            c = "0%"
                    
                        t = re.findall('A:[^.]*', a)
                        #print t
                        l = re.sub('A:[^0-9]*', '', t[0])
                        #l = int(l)
                        l =int(l)*1000
                        
                        if self.mplayerLength == 1:
                            l = 0
                            self.slider.setValue(0)
                        else:
                            self.slider.setValue(l)
                        
                        if self.progress_counter == self.mplayerLength:
                            self.progress_counter += 1
                            logger.debug(self.progress_counter)
                        else:
                            self.progress_counter = l
                        
                        if site == "Music":
                            out_time = str(datetime.timedelta(milliseconds=int(l))) + " / " + str(datetime.timedelta(milliseconds=int(self.mplayerLength)))
                            
                            out = out_time + " ["+self.epn_name_in_list+'('+artist_name_mplayer+')' +"]"
                        else:
                            out_time = str(datetime.timedelta(milliseconds=int(l))) + " / " + str(datetime.timedelta(milliseconds=int(self.mplayerLength)))
                            
                            out = out_time + " ["+self.epn_name_in_list+"]" +' Cache:'+c
                            
                        if not new_tray_widget.isHidden():
                            new_tray_widget.update_signal.emit(out_time, int(l))
                        if self.video_local_stream:
                            if c == '0%' and not self.mplayer_pause_buffer and not self.mplayer_nop_error_pause:
                                self.mpvplayer_val.write(b'\n pause \n')
                                self.mplayer_pause_buffer = True
                    if ((cache_empty == "yes" ) 
                            and (site != "Local" or site != "Music" or site != "Video")):
                        print('---nop--error--pausing---')
                        if not self.mplayer_pause_buffer:
                            self.mpvplayer_val.write(b'\n pause \n')
                            cache_empty = "no"
                            buffering_mplayer = "yes"
                    elif (('nop_streaming_read_error' in a) 
                            and (site != "Local" or site != "Music" or site != "Video")):
                        print('---nop--error--pausing---')
                        if not self.mplayer_pause_buffer:
                            self.mpvplayer_val.write(b'\n pause \n')
                            cache_empty = "no"
                            buffering_mplayer = "yes"
                            self.mplayer_nop_error_pause = True
                    if self.total_seek != 0:
                        r = "Seeking "+str(self.total_seek)+'s'
                        self.progressEpn.setFormat((r))
                    else:
                        self.progressEpn.setFormat((out))
                if 'http' in a:
                    t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
                    self.progressEpn.setFormat((t))
                    if MainWindow.isFullScreen() and self.layout_mode != "Music":
                        self.gridLayout.setSpacing(0)
                        self.frame1.show()
                        if self.frame_timer.isActive():
                            self.frame_timer.stop()
                        self.frame_timer.start(1000)
                if ("EOF code: 1" in a or "HTTP error 403 Forbidden" in a):
                    self.mplayerLength = 0
                    self.total_file_size = 0
                    mpv_start.pop()
                    if self.final_playing_url in self.history_dict_obj:
                        asp = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
                        self.history_dict_obj.update(
                                {
                                    self.final_playing_url:[
                                        0, time.time(), sub_id, audio_id,
                                        0, self.player_volume, asp
                                        ]
                                }
                            )
                    if self.player_setLoop_var:
                        t2 = bytes('\n'+"loadfile "+(current_playing_file_path)+" replace"+'\n', 'utf-8')
                        self.mpvplayer_val.write(t2)
                        #print(t2)
                        return 0
                    else:
                        if not self.queue_url_list:
                            if self.list2.count() == 0:
                                return 0
                            if self.cur_row == self.list2.count() - 1:
                                self.cur_row = 0
                                if site == "Music" and not self.playerPlaylist_setLoop_var:
                                    r1 = self.list1.currentRow()
                                    it1 = self.list1.item(r1)
                                    if it1:
                                        if r1 < self.list1.count():
                                            r2 = r1+1
                                        else:
                                            r2 = 0
                                        self.list1.setCurrentRow(r2)
                                        self.listfound()
                            else:
                                self.cur_row += 1
                            self.list2.setCurrentRow(self.cur_row)
                        
                    if "HTTP error 403 Forbidden" in a:
                        print(a)
                        self.quit_really = "yes"
                    if self.quit_really == "no" and not self.epn_wait_thread.isRunning():
                        if (site == "Local" or site == "Video" 
                                or site == "Music" or site == "PlayLists" 
                                or site == "None" or site == 'MyServer'):
                            if self.queue_url_list:
                                if isinstance(self.queue_url_list[0], tuple):
                                    self.localGetInList(eofcode='end')
                                else:
                                    self.getQueueInList(eofcode='end')
                            else:
                                self.localGetInList(eofcode='end')
                        else:
                            if self.queue_url_list:
                                if isinstance(self.queue_url_list[0], tuple):
                                    self.getNextInList(eofcode='end')
                                else:
                                    self.getQueueInList(eofcode='end')
                            else:
                                self.getNextInList(eofcode='end')
                        if self.tab_5.isHidden() and thumbnail_indicator:
                            length_1 = self.list2.count()
                            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setText((self.epn_name_in_list))"
                            exec (q3)
                            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setAlignment(QtCore.Qt.AlignCenter)"
                            exec(q3)
                            QtWidgets.QApplication.processEvents()
                    elif self.quit_really == "yes":
                        self.player_stop.clicked.emit() 
                        self.list2.setFocus()
        except Exception as e:
            logger.error('{0}::dataready-exception'.format(e))
        
    def started(self):
        global epn, new_epn, mpv_start
        global cur_label_num, site
        if self.tab_5.isHidden() and thumbnail_indicator and self.video_mode_index not in [6, 7]:
            length_1 = self.list2.count()
            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setText((self.epn_name_in_list))"
            exec(q3)
            q3="self.label_epn_"+str(length_1+self.thumbnail_label_number[0])+".setAlignment(QtCore.Qt.AlignCenter)"
            exec(q3)
            QtWidgets.QApplication.processEvents()
        print("Process Started")
        print(self.mpvplayer_val.processId())
        mpv_start =[]
        mpv_start[:]=[]
        t = "Loading: "+self.epn_name_in_list+" (Please Wait)"
        #print t
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat((t))
        if (MainWindow.isFullScreen() and site!="Music" and self.list2.isHidden()
                and self.tab_2.isHidden() and self.tab_6.isHidden()):
            self.superGridLayout.setSpacing(0)
            self.gridLayout.setSpacing(0)
            self.frame1.show()
            if self.frame_timer.isActive():
                self.frame_timer.stop()
        
    def finished(self):
        global mpv_start, thumbnail_indicator
        if mpv_start:
            mpv_start.pop()
        self.mplayerLength = 0
        self.mpv_playback_duration = None
        self.progressEpn.setMaximum(100)
        self.slider.setRange(0, 100)
        print("Process Ended")
        self.progressEpn.setValue(0)
        self.slider.setValue(0)
        self.progressEpn.setFormat("")
        self.mplayer_finished_counter += 1
        print(self.mpvplayer_val.processId(), '--finished--id--')
        logger.debug('mpvplayer_started = {0}'.format(self.mpvplayer_started))
        if (self.quit_really == 'no' and self.mpvplayer_val.processId() == 0
                and OSNAME == 'posix' and self.mpvplayer_started and self.mplayer_finished_counter == 1):
            self.player_restart()
            
    def player_restart(self):
        global mpv_start, thumbnail_indicator
        logger.warning('quit={0} , hence --restarting--'.format(self.quit_really))
        num = self.cur_row
        self.list2.setCurrentRow(num)
        item = self.list2.item(num)
        if item:
            if ((self.view_mode == 'thumbnail' and self.idw != str(int(self.tab_5.winId()))
                    and thumbnail_indicator) or self.fullscreen_mode == 1
                    or self.idw == str(int(self.label_new.winId()))):
                logger.debug('playback inside thumbnails')
                finalUrl = self.epn_return(num)
                if finalUrl.startswith('"'):
                    finalUrl = finalUrl.replace('"', '')
                elif finalUrl.startswith("'"):
                    finalUrl = finalUrl.replace("'", '')
                if finalUrl.startswith('abs_path=') or finalUrl.startswith('relative_path='):
                    finalUrl = self.if_path_is_rel(finalUrl)
                if self.player_val == "mplayer":
                    command = self.mplayermpv_command(self.idw, finalUrl, 'mplayer')
                    logger.info(command)
                    self.infoPlay(command)
                elif self.player_val == "mpv":
                    command = self.mplayermpv_command(self.idw, finalUrl, 'mpv')
                    logger.info(command)
                    self.infoPlay(command)
            else:
                logger.debug('main player widget')
                self.list2.itemDoubleClicked['QListWidgetItem*'].emit(item)
                
    def infoPlay(self, command):
        global site, new_epn, mpv_indicator, cache_empty
        self.eof_reached = False
        self.eof_lock = False
        self.mpv_playback_duration = None
        logger.debug('Now Starting')
        if not command:
            t = "Loading Failed: No Url/File Found. Try Again"
            self.progressEpn.setFormat(t)
        else:
            if mpv_indicator:
                mpv_indicator.pop()
            cache_empty = 'no'
            if command.startswith('mplayer') and OSNAME == 'nt':
                command = command + ' -vo gl'
            if self.player_setLoop_var:
                if self.player_val == 'mplayer':
                    command = command+' -loop 0'
                    
            print('--line--15662--')
            if self.mpvplayer_val.processId()>0:
                self.mpvplayer_val.kill()
                self.mpvplayer_started = False
                try:
                    if not self.mplayer_status_thread.isRunning():
                        self.mplayer_status_thread = PlayerWaitThread(self, command)
                        self.mplayer_status_thread.start()
                    else:
                        self.mpvplayer_command.append(command)
                except Exception as e:
                    print(e)
            else:
                if self.mpvplayer_command:
                    command = self.mpvplayer_command[-1]
                    self.mpvplayer_command[:] = []
                self.tab_5.set_mpvplayer(player=self.player_val, mpvplayer=self.mpvplayer_val)
                self.mpvplayer_val.setProcessChannelMode(QtCore.QProcess.MergedChannels)
                self.mpvplayer_val.started.connect(self.started)
                self.mpvplayer_val.readyReadStandardOutput.connect(partial(self.dataReady, self.mpvplayer_val))
                self.mpvplayer_val.finished.connect(self.finished)
                QtCore.QTimer.singleShot(100, partial(self.mpvplayer_val.start, command))
                logger.info(command)
                logger.info('infoplay--18165--')
                self.mpvplayer_started = True
                if self.player_setLoop_var and self.player_val == 'mpv':
                    QtCore.QTimer.singleShot(15000, partial(self.set_playerLoopFile))
                
    def adjust_thumbnail_window(self, row):
        global thumbnail_indicator
        if self.epn_name_in_list.startswith('#'):
            self.epn_name_in_list = self.epn_name_in_list.replace('#', '', 1)
        if (thumbnail_indicator and self.idw == str(int(self.tab_5.winId()))):
            try:
                title_num = row + self.list2.count()
                if self.epn_name_in_list.startswith(self.check_symbol):
                    newTitle = self.epn_name_in_list
                else:
                    newTitle = self.check_symbol+self.epn_name_in_list
                    
                sumry = "<html><h1>"+self.epn_name_in_list+"</h1></html>"
                q4="self.label_epn_"+str(title_num)+".setToolTip((sumry))"
                exec (q4)
                q3="self.label_epn_"+str(title_num)+".setText((newTitle))"
                exec (q3)
                q3="self.label_epn_"+str(title_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                exec(q3)
                QtWidgets.QApplication.processEvents()
                
                p1 = "self.label_epn_"+str(row)+".y()"
                ht=eval(p1)
                
                self.scrollArea1.verticalScrollBar().setValue(ht)
                self.labelFrame2.setText(newTitle)
                
                new_cnt = self.cur_row + self.list2.count()
                p1 = "self.label_epn_{0}".format(new_cnt)
                label_number = eval(p1)
                label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
                p1 = "self.label_epn_{0}.toPlainText()".format(new_cnt)
                txt = eval(p1)
                try:
                    p1 = "self.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                    exec(p1)
                except Exception as e:
                    print(e, '--line--4597--')
                    try:
                        p1 = 'self.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e)
                p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                exec(p1)
                QtWidgets.QApplication.processEvents()
            except Exception as e:
                print(e)
        else:
            if (self.idw and self.idw != str(int(self.tab_5.winId()))
                    and self.idw != str(int(self.label.winId())) 
                    and self.idw != str(int(self.label_new.winId()))):
                try:
                    title_num = row + self.list2.count()
                    if self.epn_name_in_list.startswith(self.check_symbol):
                        newTitle = self.epn_name_in_list
                    else:
                        newTitle = self.check_symbol+self.epn_name_in_list
                    sumry = "<html><h1>"+self.epn_name_in_list+"</h1></html>"
                    q4="self.label_epn_"+str(title_num)+".setToolTip((sumry))"
                    exec (q4)
                    q3="self.label_epn_"+str(title_num)+".setText((newTitle))"
                    exec (q3)
                    q3="self.label_epn_"+str(title_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                    exec(q3)
                    QtWidgets.QApplication.processEvents()
                    
                    if self.video_mode_index == 2:
                        p1 = "self.label_epn_"+str(row)+".y()"
                        ht=eval(p1)
                        self.scrollArea1.verticalScrollBar().setValue(ht)
                    self.labelFrame2.setText(newTitle)
                    
                    new_cnt = self.cur_row + self.list2.count()
                    p1 = "self.label_epn_{0}".format(new_cnt)
                    label_number = eval(p1)
                    label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
                    p1 = "self.label_epn_{0}.toPlainText()".format(new_cnt)
                    txt = eval(p1)
                    try:
                        p1 = "self.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e, '--line--4597--')
                        try:
                            p1 = 'self.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                            exec(p1)
                        except Exception as e:
                            print(e)
                    p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                    exec(p1)
                    
                    init_cnt = self.thumbnail_label_number[0] + self.list2.count()
                    if self.quit_really == 'yes':
                        txt = self.thumbnail_label_number[1]
                    p1 = "self.label_epn_{0}".format(init_cnt)
                    label_number = eval(p1)
                    label_number.setTextColor(self.thumbnail_text_color_dict[self.thumbnail_text_color_focus])
                    try:
                        p1 = "self.label_epn_{0}.setText('{1}')".format(init_cnt, txt)
                        exec(p1)
                    except Exception as e:
                        print(e, '--line--4597--')
                        try:
                            p1 = 'self.label_epn_{0}.setText("{1}")'.format(init_cnt, txt)
                            exec(p1)
                        except Exception as e:
                            print(e)
                    p1="self.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(init_cnt)
                    exec(p1)
                except Exception as e:
                    print(e)
    
    def localGetInList(self, eofcode=None):
        global site, epn, epn_goto, mirrorNo
        global finalUrl, home, buffering_mplayer
        global opt_movies_indicator, audio_id, sub_id, siteName, artist_name_mplayer
        global new_epn, path_Local_Dir
        global thumbnail_indicator, category, finalUrlFound, refererNeeded
        global server, current_playing_file_path, music_arr_setting
        global default_arr_setting
        
        self.external_url = False
        print(self.player_setLoop_var)
        row = self.list2.currentRow()
        print('--line--15677--')
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat(('Wait...'))
        logger.debug('external-audio-file={0}'.format(self.external_audio_file))
        if row > len(self.epn_arr_list) or row < 0:
            row = len(self.epn_arr_list)-1
        finalUrl = ""
        try:
            server._emitMeta("Next", site, self.epn_arr_list)
        except:
            pass
        self.mplayerLength = 0
        buffering_mplayer = "no"
        
        if self.if_file_path_exists_then_play(row, self.list2, True, eofcode=eofcode):
            self.adjust_thumbnail_window(row)
            return 0
                    
        self.set_init_settings()
        
        if site != "PlayLists":
            if '	' in self.epn_arr_list[row]:
                epn = self.epn_arr_list[row].split('	')[1]
                self.epn_name_in_list = (self.epn_arr_list[row]).split('	')[0]
            else:
                epn = self.list2.currentItem().text()
                self.epn_name_in_list = str(epn)
                epn = self.epn_arr_list[row].replace('#', '', 1)
            if not epn:
                return 0
            epn = epn.replace('#', '', 1)
        else:
            item = self.list2.item(row)
            if item:
                arr = self.epn_arr_list[row].split('	')
                if len(arr) >= 2:
                    path_rel = arr[1]
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        arr[1] = self.if_path_is_rel(path_rel)
                if len(arr) > 2:
                    if arr[2].startswith('http') or arr[2].startswith('"http'):
                        finalUrl = []
                        finalUrl.append(arr[1])
                        finalUrl.append(arr[2])
                        refererNeeded = True
                    else:
                        finalUrl = arr[1]
                        refererNeeded = False
                else:
                    finalUrl = arr[1]
                    refererNeeded = False
                self.epn_name_in_list = arr[0]
                epn = self.epn_name_in_list
                self.playlistUpdate()
                self.list2.setCurrentRow(row)
                if 'youtube.com' in finalUrl or finalUrl.startswith('ytdl:'):
                    if not self.epn_wait_thread.isRunning():
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, 'yt', finalUrl, self.quality_val,
                            self.ytdl_path, row)
                        self.epn_wait_thread.start()
                #self.external_url = self.get_external_url_status(finalUrl)
        
        self.adjust_thumbnail_window(row)
            
        if site in ['Video', 'Music', 'None', 'MyServer']:
            if '	' in self.epn_arr_list[row]:
                    finalUrl = '"'+(self.epn_arr_list[row]).split('	')[1]+'"'
            else:
                    finalUrl = '"'+(self.epn_arr_list[row]).replace('#', '', 1)+'"'
            if self.list3.currentItem():
                if site.lower() == 'music' and self.list3.currentItem().text().lower() == 'playlist':
                    path_rel = finalUrl.replace('"', '')
                    if path_rel.startswith('abs_path=') or path_rel.startswith('relative_path='):
                        finalUrl = '"'+self.if_path_is_rel(path_rel)+'"'
            logger.info('--line--15803--{0}'.format(finalUrl))
            i = str(self.list2.item(row).text())
            if not i.startswith(self.check_symbol):
                self.list2.item(row).setText(self.check_symbol+i)
            else:
                self.list2.item(row).setText(i)
            #self.list2.item(row).setFont(QtGui.QFont('SansSerif', 10, italic=True))
            self.list2.setCurrentRow(row)
            if self.music_playlist:
                yt_mode = 'yt_music'
            else:
                yt_mode = 'yt'
            if 'youtube.com' in finalUrl.lower() or finalUrl.startswith('ytdl:'):
                if not self.epn_wait_thread.isRunning():
                    self.epn_wait_thread = PlayerGetEpn(
                        self, logger, yt_mode, finalUrl, self.quality_val,
                        self.ytdl_path, row)
                    self.epn_wait_thread.start()
            self.external_url = self.get_external_url_status(finalUrl)
        new_epn = self.epn_name_in_list
    
        finalUrl = finalUrl.replace('"', '')
        finalUrl = '"'+finalUrl+'"'
        try:
            finalUrl = str(finalUrl, 'utf-8')
        except:
            finalUrl = finalUrl
            
        if self.mpvplayer_val.processId() > 0 and not self.epn_wait_thread.isRunning() and not self.gapless_playback:
            if self.player_val.lower() == "mplayer":
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val, a_id=audio_id,
                    s_id=sub_id
                    )
                if (not self.external_url and self.mpvplayer_started 
                        and not self.external_audio_file and OSNAME == 'posix'):
                    #try:
                    epnShow = '"' + "Queued:  "+ new_epn + '"'
                    t1 = bytes('\n '+'show_text '+(epnShow)+' \n', 'utf-8')
                    t2 = bytes('\n '+"loadfile "+(finalUrl)+" replace"+' \n', 'utf-8')
                    logger.info(t2)
                    self.mpvplayer_val.write(t2)
                    self.mpvplayer_val.write(t1)
                    if self.mplayer_SubTimer.isActive():
                        self.mplayer_SubTimer.stop()
                    self.mplayer_SubTimer.start(2000)
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.external_audio_file = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
            elif self.player_val.lower() == "mpv":
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val, a_id=audio_id,
                    s_id=sub_id
                    )
                if (not self.external_url and self.mpvplayer_started 
                        and not self.external_audio_file and OSNAME == 'posix'):
                    epnShow = '"' + "Playing:  "+ new_epn + '"'
                    t1 = bytes('\n '+'show-text '+epnShow+' \n', 'utf-8')
                    t2 = bytes('\n '+"loadfile "+finalUrl+' \n', 'utf-8')
                    self.mpvplayer_val.write(t2)
                    self.mpvplayer_val.write(t1)
                    logger.debug('mpv::{0}'.format(t2))
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.external_audio_file = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.debug('mpv-restart{0}'.format(command))
            print("mpv=" + str(self.mpvplayer_val.processId()))
        elif not self.epn_wait_thread.isRunning() and not self.gapless_playback:
            command = self.mplayermpv_command(
                self.idw, finalUrl, self.player_val, a_id=audio_id,
                s_id=sub_id
                )
            self.infoPlay(command)
            print("mpv=" + str(self.mpvplayer_val.processId()))
        elif self.gapless_playback and site in self.local_site_list:
            if (self.cur_row == 0 or eofcode == 'next') and self.playback_mode == 'playlist':
                cmd = '\n set playlist-pos {} \n'.format(self.cur_row)
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif self.playback_mode == 'single':
                self.play_file_now(finalUrl)
            
        if finalUrl.startswith('"'):
            current_playing_file_path = finalUrl.replace('"', '')
        else:
            current_playing_file_path = finalUrl
        self.final_playing_url = current_playing_file_path
        self.paste_background(row)
        MainWindow.setWindowTitle(self.epn_name_in_list)
        if not self.float_window.isHidden():
            self.float_window.setWindowTitle(self.epn_name_in_list)
    
    def paste_background(self, row):
        global site, artist_name_mplayer
        
        try:
            if site == "Music":
                try:
                    artist_name_mplayer = self.epn_arr_list[row].split('	')[2]
                    if artist_name_mplayer.lower() == "none" or 'http' in artist_name_mplayer:
                        artist_name_mplayer = ""
                except:
                    artist_name_mplayer = ""
                if artist_name_mplayer:
                    self.media_data.update_music_count('count', finalUrl)
                    self.musicBackground(row, 'Search')
                else:
                    try:
                        thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            self.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        logger.info('Error in getting Thumbnail: {0}'.format(e))
            elif site.lower() == 'video' or site.lower() == 'local' or site.lower() == 'playlists':
                if site == "Video":
                    self.media_data.update_video_count('mark', finalUrl, rownum=row)
                try:
                    thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                    logger.info("thumbnail path = {0}".format(thumb_path))
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    logger.info('Error in getting Thumbnail -14179- epnfound: {0}'.format(e))
            else:
                try:
                    thumb_path = self.get_thumbnail_image_path(row, self.epn_arr_list[row])
                    logger.info("thumbnail path = {0}".format(thumb_path))
                    if os.path.exists(thumb_path):
                        self.videoImage(thumb_path, thumb_path, thumb_path, '')
                except Exception as e:
                    logger.info('Error in getting Thumbnail: {0}'.format(e))
        except Exception as e:
            print(e, '--14180--')
        
    def getQueueInList(self, eofcode=None):
        global site, artist_name_mplayer
        global sub_id, audio_id, server, current_playing_file_path
        try:
            t1 = self.queue_url_list[0]
            server._emitMeta("queue"+'#'+t1, site, self.epn_arr_list)
        except:
            pass
        self.external_url = False
        #print(self.list6.item(0).text(), self.queue_url_list)
        if self.list6.item(0):
            old_txt = self.list6.item(0).text()
            if old_txt.lower().startswith('queue empty:'):
                self.list6.clear()
        if self.list6.item(0) and not self.gapless_playback:
            if self.if_file_path_exists_then_play(0, self.list6, True, eofcode=eofcode):
                del self.queue_url_list[0]
                self.list6.takeItem(0)
                del t1
                return 0
        
        if site in self.local_site_list and not self.gapless_playback:
            t = self.queue_url_list[0]
            epnShow = t.split('	')[1]
            epnShow = epnShow.replace('"', '')
            if epnShow.startswith('abs_path=') or epnShow.startswith('relative_path='):
                epnShow = self.if_path_is_rel(epnShow)
            epnShow = '"'+epnShow+'"'
            self.epn_name_in_list = t.split('	')[0]
            if self.epn_name_in_list.startswith('#'):
                self.epn_name_in_list = self.epn_name_in_list[1:]
            if site == "Music":
                artist_name_mplayer = t.split('	')[2]
                if artist_name_mplayer == "None":
                    artist_name_mplayer = ""
            del self.queue_url_list[0]
            t1 = self.list6.item(0)
            if t1:
                self.list6.takeItem(0)
                del t1
            if not self.idw:
                self.idw = str(int(self.tab_5.winId()))
            if 'youtube.com' in epnShow.lower():
                finalUrl = epnShow.replace('"', '')
                epnShow = finalUrl
                if self.music_playlist:
                    yt_mode = 'yt_music'
                else:
                    yt_mode = 'yt'
                if not self.epn_wait_thread.isRunning():
                    self.epn_wait_thread = PlayerGetEpn(
                        self, logger, yt_mode, finalUrl, self.quality_val,
                        self.ytdl_path, self.epn_name_in_list)
                    self.epn_wait_thread.start()
            self.external_url = self.get_external_url_status(epnShow)
        elif self.gapless_playback and site in self.local_site_list:
            item = self.queue_url_list[0]
            epnShow = item.split('	')[1]
            epnShow = epnShow.replace('"', '')
            if epnShow.startswith('abs_path=') or epnShow.startswith('relative_path='):
                epnShow = self.if_path_is_rel(epnShow)
            epnShow = '"'+epnShow+'"'
            try:
                index = self.epn_arr_list.index(item)
            except Exception as err:
                logger.error(err)
                index = -1
            self.epn_name_in_list = item.split('	')[0]
            if self.epn_name_in_list.startswith('#'):
                self.epn_name_in_list = self.epn_name_in_list[1:]
            if site == "Music":
                artist_name_mplayer = item.split('	')[2]
                if artist_name_mplayer == "None":
                    artist_name_mplayer = ""
            del self.queue_url_list[0]
            t1 = self.list6.item(0)
            if t1:
                self.list6.takeItem(0)
                del t1
            if not self.idw:
                self.idw = str(int(self.tab_5.winId()))
            if 'youtube.com' in epnShow.lower():
                finalUrl = epnShow.replace('"', '')
                epnShow = finalUrl
                if self.music_playlist:
                    yt_mode = 'yt_music'
                else:
                    yt_mode = 'yt'
                if not self.epn_wait_thread.isRunning():
                    self.epn_wait_thread = PlayerGetEpn(
                        self, logger, yt_mode, finalUrl, self.quality_val,
                        self.ytdl_path, self.epn_name_in_list)
                    self.epn_wait_thread.start()
            else:
                finalUrl = epnShow.replace('"', '')
            self.external_url = self.get_external_url_status(epnShow)
            logger.debug('code={}::mode={}::index={}::final={}'.format(
                eofcode, self.playback_mode, index, finalUrl)
                )
            if eofcode == 'end' and self.playback_mode == 'playlist':
                cmd = '\n set playlist-pos {} \n'.format(index)
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif self.playback_mode == 'single':
                if index >= 0:
                    self.cur_row = index
                    self.list2.setCurrentRow(index)
                self.play_file_now(finalUrl)
            else:
                self.play_file_now(finalUrl)
        else:
            epnShow = self.queue_url_list.pop()
            self.cur_row -= 1
            self.list2.setCurrentRow(self.cur_row)
            
        
        epnShowN = '"'+epnShow.replace('"', '')+'"'
        command = self.mplayermpv_command(
            self.idw, epnShowN, self.player_val, a_id=audio_id,
            s_id=sub_id
            )
        if (self.mpvplayer_val.processId() > 0 and not self.epn_wait_thread.isRunning()
                and OSNAME == 'posix' and not self.gapless_playback):
            epnShow = '"'+epnShow.replace('"', '')+'"'
            t2 = bytes('\n '+"loadfile "+epnShow+" replace"+' \n', 'utf-8')
            if self.player_val.lower() == 'mpv':
                if not self.external_url and not self.external_audio_file:
                    self.mpvplayer_val.write(t2)
                    logger.info(t2)
                else:
                    self.mpvplayer_val.write(b'\n quit \n')
                    self.external_audio_file = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
            elif self.player_val.lower() == "mplayer":
                if not self.external_url and not self.external_audio_file:
                    self.mpvplayer_val.write(t2)
                    logger.info(t2)
                    if self.mplayer_SubTimer.isActive():
                        self.mplayer_SubTimer.stop()
                    self.mplayer_SubTimer.start(2000)
                else:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                    self.external_audio_file = False
                    self.infoPlay(command)
                    #self.external_url = False
                    logger.info(command)
        elif not self.epn_wait_thread.isRunning() and not self.gapless_playback:
            self.infoPlay(command)
            logger.info(command)
            self.list1.hide()
            self.frame.hide()
            self.text.hide()
            self.label.hide()
            self.label_new.hide()
            self.tab_5.show()
        
        epnShow = epnShow.replace('"', '')
        if not epnShow.startswith('http'):
            if site == "Music":
                self.media_data.update_music_count('count', epnShowN)
                self.musicBackground(0, 'Queue')
            elif site == "Video":
                self.media_data.update_video_count('mark', epnShowN)
                logger.info('{0}--mark-video-queue----13147--'.format(epnShowN))
        if epnShow.startswith('http'):
            current_playing_file_path = epnShow
        else:
            current_playing_file_path = '"'+epnShow+'"'
        MainWindow.setWindowTitle(self.epn_name_in_list)
        if not self.float_window.isHidden():
            self.float_window.setWindowTitle(self.epn_name_in_list)
        
    def mplayermpv_command(self, idw, finalUrl, player, a_id=None, s_id=None,
                           rfr=None, a_url=None, s_url=None, from_function=None):
        global site
        finalUrl = finalUrl.replace('"', '')
        aspect_value = self.mpvplayer_aspect.get(str(self.mpvplayer_aspect_cycle))
        if player.lower() == 'mplayer':
            if finalUrl.startswith('http'):
                command = 'mplayer -idle -identify -msglevel statusline=5:global=6 -cache 100000 -cache-min 0.001 -cache-seek-min 0.001 -osdlevel 0 -slave -wid {0}'.format(idw)
            else:
                command = 'mplayer -idle -identify -msglevel statusline=5:global=6 -nocache -osdlevel 0 -slave -wid {0}'.format(idw)
            if aspect_value == '0':
                command = command + ' -nokeepaspect'
            elif aspect_value == '-1':
                pass
            else:
                command = command + ' -aspect {0}'.format(aspect_value)
        elif player.lower() == "mpv":
            self.mpv_custom_pause = False
            command = 'mpv --cache-secs=120 --cache=auto --cache-default=100000\
 --cache-initial=0 --cache-seek-min=100 --cache-pause\
 --idle -msg-level=all=v --osd-level=0 --cursor-autohide=no\
 --no-input-cursor --no-osc --no-osd-bar --ytdl=no\
 --input-file=/dev/stdin --input-terminal=no\
 --input-vo-keyboard=no --video-aspect {0} -wid {1} --input-conf="{2}"\
 --screenshot-directory="{3}"'.format(aspect_value, idw, self.mpv_input_conf,
                                      self.screenshot_directory)
        else:
            command = self.player_val
        if a_id:
            if a_id == "auto":
                if player == 'mplayer':
                    command = command+" -aid 0"
                elif player == 'mpv':
                    command = command+" -aid auto"
            else:
                command = command+" -aid {0}".format(a_id)
            
        if s_id:
            if s_id == "auto":
                if player == 'mplayer':
                    command = command+" -sid 0"
                elif player == 'mpv':
                    command = command+" -sid auto"
            else:
                command = command+" -sid {0}".format(s_id)
                
        if rfr:
            if player == 'mplayer':
                command = command+" -referrer {0}".format(rfr)
            elif player == 'mpv':
                command = command+" --referrer={0}".format(rfr)
                
        if a_url:
            if player == 'mplayer':
                command = command+" -audiofile {0}".format(a_url)
            elif player == 'mpv':
                command = command+" --audio-file={0}".format(a_url)
        if self.gapless_playback or self.gapless_network_stream:
            command = command + " --gapless-audio=yes --prefetch-playlist=yes"
        if self.player_volume:
            if self.player_volume.isnumeric():
                if player == 'mplayer':
                    command = command + " -volume={}".format(self.player_volume)
                elif player == 'mpv':
                    if self.volume_type == 'volume':
                        command = command + " --volume={}".format(self.player_volume)
        if self.gsbc_dict:
            for i in self.gsbc_dict:
                if i == 'subscale':
                    pass
                else:
                    command = command + ' --{}={}'.format(i, self.gsbc_dict[i])
        if self.subtitle_dict and self.apply_subtitle_settings:
            for i in self.subtitle_dict:
                command = command + ' --{}="{}"'.format(i, self.subtitle_dict[i])
        elif self.subtitle_dict and not self.apply_subtitle_settings:
            scale = self.subtitle_dict.get('sub-scale')
            if scale:
                command = command + ' --sub-scale="{}"'.format(scale)
        if s_url:
            s_url_arr = s_url.split('::')
            for i in s_url_arr:
                if player == 'mpv':
                    command = command + ' --sub-file=' + i
                elif player == 'mplayer':
                    command = command + ' -sub ' + i
        if site.lower() == 'music':
            if player == 'mpv':
                command = command + ' --no-video'
            elif player == 'mplayer':
                command = command + ' -novideo'
        if self.custom_mpv_input_conf:
            command = re.sub('--input-vo-keyboard=no|--input-terminal=no', '', command)
            command = command.replace('--osd-level=0', '--osd-level=1')
        if player == 'MPV':
            command = re.sub('-wid [0-9]+|--input-vo-keyboard=no|--input-terminal=no', '', command)
            command = re.sub('--cursor-autohide=no|--no-input-cursor|--no-osc|--no-osd-bar|--ytdl=no', '', command)
        elif player == 'MPLAYER':
            command = re.sub('-wid [0-9]+', '', command)
        logger.debug(command)
        if self.player_val.lower() == 'mpv' and self.use_custom_config_file and self.mpvplayer_string_list:
            command = command + ' ' + ' '.join(self.mpvplayer_string_list)
        logger.debug(finalUrl)
        if finalUrl:
            finalUrl = finalUrl.strip()
            if self.quality_val == 'best' and self.ytdl_path == 'default':
                if ('youtube.com' in finalUrl or finalUrl.startswith('ytdl:')) and player == 'mpv':
                    if finalUrl.startswith('ytdl:'):
                        finalUrl = finalUrl.replace('ytdl:', '', 1)
                    command = command.replace('ytdl=no', 'ytdl=yes')
                elif ('youtube.com' in finalUrl or finalUrl.startswith('ytdl:')) and player == 'mplayer':
                    finalUrl = get_yt_url(finalUrl, self.quality_val, self.ytdl_path, logger, mode="offline").strip()
            if self.gapless_playback and site in self.local_site_list:
                if site != 'MyServer' and from_function == 'now_start':
                    command = '{} "{}"'.format(command, finalUrl.replace('"', ''))
                    self.playback_mode = 'single'
                else:
                    if self.tmp_pls_file_lines:
                        write_files(self.tmp_pls_file, self.tmp_pls_file_lines, line_by_line=True)
                        command = '{} "{}" --playlist-start={}'.format(
                            command, self.tmp_pls_file, self.cur_row
                            )
                        self.playback_mode = 'playlist'
            else:
                command = '{} "{}"'.format(command, finalUrl.replace('"', ''))
                self.playback_mode = 'single'
        else:
            command = ''
        if self.gapless_playback_disabled:
            self.gapless_playback = True
            self.gapless_playback_disabled = False
        if self.gapless_network_stream_disabled:
            self.gapless_network_stream = True
            self.gapless_network_stream_disabled = False
        return command
    
    def replace_line_in_file(self, file_name, lineno, content):
        lines = open_files(file_name, True)
        lines = [i.strip() for i in lines if i.strip()]
        if lineno < len(lines):
            lines[lineno] = content
            write_files(file_name, lines, line_by_line=True)
    
    def getNextInList(self, eofcode=None):
        global site, epn, epn_goto, mirrorNo
        global finalUrl, home, buffering_mplayer
        global opt_movies_indicator, audio_id, sub_id, siteName, rfr_url
        global new_epn, path_Local_Dir
        global thumbnail_indicator, category, finalUrlFound, refererNeeded
        global server, current_playing_file_path, default_arr_setting
        global music_arr_setting, audio_id, sub_id
        audio_id = 'auto'
        sub_id = 'auto'
        row = self.list2.currentRow()
        self.total_file_size = 0
        self.mplayerLength = 0
        buffering_mplayer = "no"
        finalUrl = ''
        self.progressEpn.setValue(0)
        self.progressEpn.setFormat(('Wait...'))
        try:
            server._emitMeta("Next", site, self.epn_arr_list)
        except:
            pass
        
        if self.if_file_path_exists_then_play(row, self.list2, True, eofcode=eofcode):
            self.adjust_thumbnail_window(row)
            return 0
        
        if site != "PlayLists":
            if '	' in self.epn_arr_list[row]:
                epn = self.epn_arr_list[row].split('	')[1]
                self.epn_name_in_list = (self.epn_arr_list[row]).split('	')[0]
            else:
                epn = str(self.list2.currentItem().text())
                self.epn_name_in_list = (epn)
                epn = self.epn_arr_list[row]
            if not epn:
                return 0
            epn = epn.replace('#', '', 1)
        
        self.adjust_thumbnail_window(row)
        
        self.set_init_settings()
        
        if (site!="PlayLists" and site!="None" and site!="Music" 
                and site!= "Video" and site!="Local"):
            if opt == "History":
                self.mark_History()
            else:
                i = str(self.list2.item(row).text())
                if not self.check_symbol in i:
                    self.list2.item(row).setText(self.check_symbol+i)
                else:
                    self.list2.item(row).setText(i)
                self.list2.setCurrentRow(row)
                
            if site != "Local":
                try:
                    print(site)
                except:
                    return 0
                self.progressEpn.setFormat('Wait..')
                try:
                    if self.video_local_stream:
                        if self.thread_server.isRunning():
                            if self.do_get_thread.isRunning():
                                if self.https_media_server:
                                    https_val = 'https'
                                else:
                                    https_val = 'http'
                                finalUrl = https_val+"://"+self.local_ip+':'+str(self.local_port)+'/'
                                if self.torrent_handle.file_priority(row):
                                    self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Get Next', self.torrent_download_folder, self.stream_session)
                                else:
                                    if self.player_val == 'mplayer':
                                        self.mpvplayer_val.write(b'\n quit \n')
                            else:
                                finalUrl, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'Already Running', self.torrent_download_folder, self.stream_session)
                        else:
                            finalUrl, self.thread_server, self.do_get_thread, self.stream_session, self.torrent_handle = self.start_torrent_stream(name, row, self.local_ip+':'+str(self.local_port), 'First Run', self.torrent_download_folder, self.stream_session)
                        self.torrent_handle.set_upload_limit(self.torrent_upload_limit)
                        self.torrent_handle.set_download_limit(self.torrent_download_limit)
                    else:
                        #finalUrl = self.site_var.getFinalUrl(name, epn, mirrorNo, quality)
                        print(self.epn_wait_thread.isRunning(), self.cur_row, epn, '--10619--')
                        if not self.epn_wait_thread.isRunning():
                            self.epn_wait_thread = PlayerGetEpn(
                                self, logger, 'addons', name, epn, mirrorNo,
                                self.quality_val, row)
                            self.epn_wait_thread.start()
                except Exception as e:
                    print(e)
                    self.progressEpn.setFormat('Load Failed!')
                    print('final url not found')
                    return 0
                
        new_epn = self.epn_name_in_list
        
        if not self.epn_wait_thread.isRunning():
            if isinstance(finalUrl, list):
                rfr_exists = finalUrl[-1]
                rfr_needed = False
                if rfr_exists == 'referer sent':
                    rfr_needed = True
                    finalUrl.pop()
                if self.mpvplayer_val:
                    if self.mpvplayer_val.processId() > 0:
                        if refererNeeded == "True":
                            finalUrl.pop()
                        epnShow = '"'+finalUrl[0]+'"'
                        t2 = bytes('\n'+"loadfile "+epnShow+" replace"+'\n', 'utf-8')
                        self.mpvplayer_val.write(t2)
                        self.queue_url_list[:]=[]
                        for i in range(len(finalUrl)-1):
                            epnShow ='"'+finalUrl[i+1]+'"'
                            self.queue_url_list.append(finalUrl[i+1])
                        self.queue_url_list.reverse()
                        logger.info('---hello-----{0}'.format(finalUrl))
                    else:
                        if finalUrlFound == True or site=="PlayLists" or rfr_needed:
                            if refererNeeded == True or rfr_needed:
                                rfr_url = finalUrl[1]
                                nepn = str(finalUrl[0])
                                epnShow = str(nepn)
                                command = self.mplayermpv_command(
                                    self.idw, nepn, self.player_val,
                                    rfr=rfr_url
                                    )
                                
                            else:
                                nepn = str(finalUrl[0])
                                epnShow = nepn
                                command = self.mplayermpv_command(self.idw, nepn, self.player_val)
                                
                        else:
                            self.queue_url_list[:]=[]
                            epnShow = finalUrl[0]
                            for i in range(len(finalUrl)-1):
                                self.queue_url_list.append(finalUrl[i+1])
                            self.queue_url_list.reverse()
                            command = self.mplayermpv_command(self.idw, epnShow, self.player_val)
                            
                        logger.info(command)
                        if self.mpvplayer_val.processId() > 0:
                            self.mpvplayer_val.kill()
                            self.mpvplayer_started = False
                        self.infoPlay(command)
            else:
                finalUrl = finalUrl.replace('"', '')
                self.external_url = self.get_external_url_status(finalUrl)
                try:
                    finalUrl = str(finalUrl)
                except:
                    finalUrl = finalUrl
                command = self.mplayermpv_command(
                    self.idw, finalUrl, self.player_val, a_id=audio_id,
                    s_id=sub_id
                    )
                
                if self.mpvplayer_val.processId() > 0:
                    self.mpvplayer_val.kill()
                    self.mpvplayer_started = False
                self.infoPlay(command)
        
        if not self.epn_wait_thread.isRunning():
            if not isinstance(finalUrl, list):
                self.final_playing_url = finalUrl.replace('"', '')
                if self.final_playing_url.startswith('http'):
                    current_playing_file_path = self.final_playing_url
                else:
                    current_playing_file_path = '"'+self.final_playing_url+'"'
            else:
                self.final_playing_url = finalUrl[0].replace('"', '')
                if refererNeeded == True:
                    rfr_url = finalUrl[1].replace('"', '')
        MainWindow.setWindowTitle(self.epn_name_in_list)
        if not self.float_window.isHidden():
            self.float_window.setWindowTitle(self.epn_name_in_list)
            
    def update_playlist_original(self, pls):
        self.list2.clear()
        file_path = pls
        if os.path.exists(file_path):
            write_files(file_path, self.epn_arr_list, line_by_line=True)
            self.update_list2()
            
    def update_playlist(self, pls):
        file_path = pls
        if os.path.exists(file_path):
            index = self.btn1.findText('PlayLists')
            if index >= 0:
                self.btn1.setCurrentIndex(index)
                
        if os.path.exists(file_path) and self.btn1.currentText().lower() == 'youtube':
            self.list2.clear()
            self.epn_arr_list[:]=[]
            lines = open_files(file_path, True)
            for i in lines:
                i = i.replace('\n', '')
                if i:
                    self.epn_arr_list.append(i)
            self.update_list2()
        elif os.path.exists(file_path) and self.btn1.currentText().lower() == 'playlists':
            pl_name = os.path.basename(file_path)
            if not self.list1.currentItem():
                self.list1.setCurrentRow(0)
            if self.list1.currentItem().text() != pl_name:  
                for i in range(self.list1.count()):
                    item = self.list1.item(i)
                    if item.text() == pl_name:
                        self.list1.setCurrentRow(i)
                        break
            else:
                lines = open_files(file_path, True)
                new_epn = lines[-1].strip()
                self.epn_arr_list.append(new_epn)
                new_epn_title = new_epn.split('	')[0]
                if new_epn_title.startswith('#'):
                    new_epn_title = new_epn_title.replace('#', self.check_symbol, 1)
                self.list2.addItem(new_epn_title)
        if self.gapless_playback:
            self.use_playlist_method()
            
    def newoptions(self, val=None):
        self.show_search_thumbnail = False
        if self.options_mode == 'legacy':
            self.options(val)
        else:
            self.newoptionmode(val)
            
    def newoptionmode(self, val):
        global opt, home, site, pgn, siteName
        t_opt = "History"
        offline_history = False
        print(val, '----clicked---', type(val))
        if val == "clicked":
            row_number = self.list3.currentRow()
            item = self.list3.item(row_number)
            if item:
                t_opt = str(self.list3.currentItem().text())
        elif val == 'history+offline':
            t_opt = 'History'
            row_number = 0
            offline_history = True
        elif val == "history":
            t_opt = "History"
            row_number = 0
        opt = t_opt
        self.line.clear()
        self.list2.clear()
        print(offline_history, val, opt, ':newoptions:')
        if (t_opt == "History" and site.lower() != 'myserver') or offline_history:
            self.list1.clear()
            opt = t_opt
            if siteName:
                file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
            else:
                file_path = os.path.join(home, 'History', site, 'history.txt')
            if os.path.isfile(file_path):
                lines = open_files(file_path, True)
                lins = open_files(file_path, True)
                self.original_path_name[:] = []
                for i in lins:
                    i = i.strip()
                    j = i
                    if '	' in i:
                        i = i.split('	')[0]
                    self.list1.addItem(i)
                    self.original_path_name.append(j)
                self.forward.hide()
                self.backward.hide()
        else:
            self.text.setText('Wait...Loading')
            QtWidgets.QApplication.processEvents()
            if self.video_local_stream:
                try:
                    history_folder = os.path.join(home, 'History', site)
                    if not os.path.exists(history_folder):
                        os.makedirs(history_folder)
                    m = self.site_var.getCompleteList(
                            t_opt, self.list6, self.progress, 
                            self.tmp_download_folder, history_folder
                            )
                    self.text.setText('Load Complete!')
                except Exception as e:
                    print(e)
                    m = []
                    self.text.setText('Load Failed!')
                    return 0
            else:
                try:
                    m = self.site_var.getCompleteList(t_opt, row_number)
                    self.text.setText('Load Complete!')
                except Exception as e:
                    print(e)
                    m = []
                    self.text.setText('Load Failed!')
                    return 0
            opt = t_opt
            list_1 = list_2 = list_3 = False
            if m:
                list_tuple = m[-1] #(code, row_number)
                if isinstance(list_tuple, tuple):
                    code = list_tuple[0]
                    row_value = list_tuple[1]
                elif isinstance(list_tuple, int):
                    code = list_tuple
                    row_value = 0
                else:
                    code = 0
                    row_value = 0
                    
                if code == 0:
                    list_3 = True
                    m.pop()
                    if m:
                        subsite = m[-1]
                        if subsite.startswith('sitename='):
                            siteName = subsite.split('=')[1]
                            m.pop()
                elif code == 1:
                    list_1 = True
                    m.pop()
                elif code == 2:
                    list_3 = True
                    m.pop()
                elif code == 3 or code == 5:
                    if site.lower() == 'myserver':
                        self.myserver_cache.clear()
                    mval = m.pop()
                    if mval == 3:
                        self.text.setText('Login Required')
                    else:
                        self.text.setText('Logged out')
                    return 0
                elif code == 4:
                    m.pop()
                    if site.lower() == 'myserver' and opt.lower() == 'discover':
                        if not self.discover_thread:
                            self.discover_thread = DiscoverServer(self, True)
                            self.discover_thread.start()
                        elif isinstance(self.discover_thread, DiscoverServer):
                            if not self.discover_thread.isRunning():
                                self.discover_thread = DiscoverServer(self, True)
                                self.discover_thread.start()
                            else:
                                self.discover_server = False
                    return 0
                elif code == 6:
                    file_path = os.path.join(home, 'History', 'MyServer', 'history.txt')
                    if os.path.isfile(file_path):
                        lines = open_files(file_path, True)
                        m = [i for i in lines]
                        list_1 = True
                        
            if not list_1 and not list_2 and not list_3:
                list_1 = True
            if list_3:
                self.list1.clear()
                self.list3.clear()
                for i in m:
                    self.list3.addItem(i)
                self.forward.hide()
                self.backward.hide()
                self.list3.setCurrentRow(row_value)
            elif list_1:
                self.list1.clear()
                self.original_path_name[:] = []
                for i in m:
                    if isinstance(i ,int):
                        pass
                    else:
                        i = i.strip()
                        if '	' in i:
                            j = i.split('	')[0]
                        else:
                            j = i
                        if j:
                            self.list1.addItem(j)
                            self.original_path_name.append(i)
                self.forward.show()
                self.backward.show()
            elif list_2:
                self.list1.clear()
                self.epn_arr_list.clear()
                for i in m:
                    if '\t' in i:
                        j = i.split('\t')[0]
                    self.list2.addItem(j)
                    self.epn_arr_list.append(i)
                self.forward.hide()
                self.backward.hide()
                if self.gapless_playback:
                    self.use_playlist_method()
        
    def options(self, val=None):
        global opt, pgn, genre_num, site, name
        global pre_opt, mirrorNo, insidePreopt, home, siteName, finalUrlFound
        global show_hide_playlist, show_hide_titlelist, total_till_epn
        global total_till, browse_cnt
        global bookmark, status
        
        browse_cnt=0
        if bookmark:
            r = self.list3.currentRow()
            item = self.list3.item(r)
            if item:
                opt = item.text()
                
                if opt == "All":
                    status = "bookmark"
                else:
                    status = opt
                
                book_path = os.path.join(home, 'Bookmark', status+'.txt')
                if not os.path.isfile(book_path):
                    f = open(book_path, 'w')
                    f.close()
                else:
                    self.setPreOpt()
        elif site == "Music":
            global update_start
            self.show_search_thumbnail = True
            music_dir = os.path.join(home, 'Music')
            if not os.path.exists(music_dir):
                os.makedirs(music_dir)
            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            if not os.path.exists(music_db):
                self.media_data.create_update_music_db(music_db, music_file, music_file_bak)
                update_start = 1
            elif not update_start:
                update_start = 1
                self.update_thread = UpdateMusicThread(self, music_db, music_file, music_file_bak)
                if not self.update_thread.isRunning():
                    self.update_thread.start()
            if self.list3.currentItem():
                music_opt = str(self.list3.currentItem().text())
            else:
                music_opt = ""
            print(music_opt)
            
            artist =[]
            if music_opt == "Playlist":
                pls = os.path.join(home, 'Playlists')
                if os.path.exists(pls):
                    m = os.listdir(pls)
                    m.sort()
                    for i in m:
                        artist.append(i)
            else:
                m = self.media_data.get_music_db(music_db, music_opt, "")
                for i in m:
                    artist.append(i[0])
            self.list1.clear()
            self.original_path_name[:] = []
            self.music_playlist = False
            if (music_opt == "Artist" or music_opt == "Album" or music_opt == "Title" 
                    or music_opt == "Fav-Artist" or music_opt == "Fav-Album"):
                for i in artist:
                    self.original_path_name.append(i)
                    self.list1.addItem((i))
            elif music_opt == "Directory" or music_opt == "Fav-Directory":
                for i in artist:
                    self.original_path_name.append(i)
                    #i = i.split('/')[-1]
                    i = os.path.basename(i)
                    self.list1.addItem((i))
            elif music_opt == "Playlist":
                self.music_playlist = True
                for i in artist:
                    self.original_path_name.append(os.path.join(home, 'Playlists', i))
                    self.list1.addItem((i))
            else:
                artist[:]=[]
                self.epn_arr_list[:]=[]
                self.list2.clear()
                for i in m:
                    self.epn_arr_list.append(str(i[1]+'	'+i[2]+'	'+i[0]))
                    #self.list2.addItem((i[1]))
                self.update_list2()
        elif site == "Video":
            video_dir = os.path.join(home, 'VideoDB')
            if not os.path.exists(video_dir):
                os.makedirs(video_dir)
            video_db = os.path.join(video_dir, 'Video.db')
            video_file = os.path.join(video_dir, 'Video.txt')
            video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
            
            if self.list3.currentItem() and val != 'history':
                video_opt = str(self.list3.currentItem().text())
            else:
                video_opt = "History"
            print('----video-----opt', video_opt)
            if val == 'history' and video_opt == 'History':
                video_opt = "History"
            if not os.path.exists(video_db):
                self.media_data.create_update_video_db(video_db, video_file, video_file_bak)
            elif video_opt == "UpdateAll":
                msg = ('This Option Will Update The Database\
                        \nby Removing All Unreachable Links\
                        \nFrom it. Do You Want To Continue?')
                msg = re.sub('[ ]+', ' ', msg)
                msgreply = QtWidgets.QMessageBox.question(
                    MainWindow, 'Total Update', msg ,QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                    )
                if msgreply == QtWidgets.QMessageBox.Yes:
                    self.media_data.update_on_start_video_db(video_db, video_file, video_file_bak, video_opt)
                    logger.debug('Proceed With Removing unreachable links')
                else:
                    logger.debug('Canceled UpdateAll')
                self.video_dict.clear()
                video_opt = "Directory"
            elif video_opt == "Update":
                self.media_data.update_on_start_video_db(video_db, video_file, video_file_bak, video_opt)
                video_opt = "Directory"
                self.video_dict.clear()
            logger.debug(video_opt)
            if video_opt.lower() != 'update' and video_opt.lower() != 'updateall':
                opt = video_opt
            artist = []
            print('----video-----opt', video_opt)
            if video_opt == "Available":
                m = self.media_data.get_video_db(video_db, "Directory", "")
            elif video_opt == "History":
                m = self.media_data.get_video_db(video_db, "History", "")
            else:
                m = self.media_data.get_video_db(video_db, video_opt, "")
            for i in m:
                artist.append(i[0]+'	'+i[1])
            self.list1.clear()
            self.original_path_name[:] = []
            logger.info('\n{0}::\n'.format(video_opt))
            if video_opt.lower() != "update" or video_opt.lower() != "updateall":
                if video_opt.lower() == 'available':
                    show_all = False
                else:
                    show_all = True
                for i in artist:
                    ti = i.split('	')[0]
                    di = i.split('	')[1]
                    if os.path.exists(di) or show_all:
                        eptitle = ti.lower()
                        if (eptitle.startswith('season') or eptitle.startswith('special')
                                or eptitle.startswith('extra')):
                            new_di, new_ti = os.path.split(di)
                            new_di = os.path.basename(new_di)
                            ti = new_di+'-'+ti
                            self.original_path_name.append(ti+'	'+di)
                        else:
                            self.original_path_name.append(i)
                        self.list1.addItem((ti))
                if video_opt.lower() not in ['directory', 'history', 'recent']:
                    self.sortList()
        elif site == "PlayLists" and val == 'clicked':
            if self.list3.currentItem():
                txt = self.list3.currentItem().text().lower()
                if txt == 'list':
                    criteria = os.listdir(os.path.join(home, 'Playlists'))
                    criteria.sort()
                    home_n = os.path.join(home, 'Playlists')
                    criteria = naturallysorted(criteria)
                    self.original_path_name[:] = []
                    self.list1.clear()
                    self.list2.clear()
                    for i in criteria:
                        self.list1.addItem(i)
                        self.original_path_name.append(i)
                elif txt == 'open file':
                    a = 0
                    print("add")
                    fname = QtWidgets.QFileDialog.getOpenFileNames(
                            MainWindow, 'Select One or More Files', self.last_dir)
                    if fname:
                        logger.info(fname)
                        if fname[0]:
                            self.last_dir, file_choose = os.path.split(fname[0][0])
                        self.list2.clear()
                        file_list = fname[0]
                        self.epn_arr_list[:] = []
                        for i in file_list:
                            j = os.path.basename(i)
                            if '.' in j:
                                k = j.rsplit('.', 1)[1]
                                if (k in self.music_type_arr 
                                        or k in self.video_type_arr or k == 'm3u'
                                        or k == 'pls'):
                                    if k != 'm3u' and k != 'pls':
                                        new_val = j+'	'+i+'	'+'NONE'
                                        self.epn_arr_list.append(new_val)
                                        self.list2.addItem(j)
                                    else:
                                        self.watch_external_video(i)
                        if self.epn_arr_list:
                            file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                            f = open(file_name, 'w').close()
                            write_files(file_name, self.epn_arr_list, True)
                            self.list1.clear()
                            self.list1.addItem('TMP_PLAYLIST')
                elif txt == 'open url':
                    item, ok = QtWidgets.QInputDialog.getText(
                        MainWindow, 'Input Dialog', 'Enter Url of External Media or Playlist')
                    if ok and item:
                        self.list2.clear()
                        self.list1.clear()
                        if item.startswith('http'):
                            if not self.gapless_network_stream:
                                self.progressEpn.setFormat('Wait! Trying to get final link.')
                            QtWidgets.QApplication.processEvents()
                            self.watch_external_video(item, mode='open url')
                elif txt == 'open directory':
                    fname = QtWidgets.QFileDialog.getExistingDirectory(
                            MainWindow, 'Add Directory', self.last_dir)
                    if fname:
                        if os.path.exists(fname):
                            self.last_dir = fname
                            self.watch_external_video(fname)
        self.page_number.setText(str(self.list1.count()))
        insidePreopt = 0
        
        if ((self.view_mode in ["thumbnail", "thumbnail_light"] or not self.tab_6.isHidden()) 
                and (opt == "History" or site=='Video' or bookmark
                or site == "PlayLists")):
            if site == "NotMentioned":
                print("PlayLists")
            elif self.view_mode == 'thumbnail_light':
                if self.list_poster.title_clicked:
                    self.list_poster.show_list(mode='next')
                    try:
                        for i in range(0, total_till_epn):
                            t = "self.label_epn_"+str(i)+".deleteLater()"
                            exec (t)
                        total_till_epn=0
                    except Exception as err:
                        logger.error(err)
            elif self.view_mode == 'thumbnail':
                self.list1.hide()
                self.list2.hide()
                self.tab_5.hide()
                self.label.hide()
                self.label_new.hide()
                self.text.hide()
                self.frame.hide()
                self.frame1.hide()
                self.goto_epn.hide()
                self.tab_6.show()
                self.tab_2.hide()
                self.scrollArea1.hide()
                self.scrollArea.show()
                if (opt == "History" or (site == "Video" or site == 'PlayLists') 
                        or bookmark):
                    print(total_till, 2*self.list1.count()-1, '--count--')
                    if not self.lock_process and val == 'clicked':
                        if not self.scrollArea.isHidden():
                            self.next_page('deleted')
                        elif not self.scrollArea1.isHidden():
                            self.scrollArea1.hide()
                            self.scrollArea.show()
                            if thumbnail_indicator:
                                thumbnail_indicator.pop()
                            i = 0
                            while(i<total_till_epn):
                                t = "self.label_epn_"+str(i)+".deleteLater()"
                                exec (t)
                                i = i+1
                            total_till_epn=0
                            self.next_page('deleted')
                            #self.thumbnail_label_update_epn()
                
        if self.list1.isHidden() and not self.list2.isHidden():
            if self.list1.count() > 0:
                self.list1.show()
                show_hide_titlelist = 1
                self.list2.hide()
                self.goto_epn.hide()
                show_hide_playlist = 0
        elif not self.list1.isHidden() and self.list2.isHidden():
            if self.list1.count() == 0 and self.list2.count() > 0:
                self.list1.hide()
                self.frame.hide()
                show_hide_titlelist = 0
                self.list2.show()
                show_hide_playlist = 1
        if self.gapless_playback:
            self.use_playlist_method()
        
    def music_mode_layout(self):
        global screen_width, show_hide_cover, show_hide_player
        global show_hide_playlist, show_hide_titlelist, music_arr_setting
        global opt, new_tray_widget, tray
        #ui.VerticalLayoutLabel.takeAt(2)
        if self.player_theme in ['dark', 'system']:
            self.label_new.hide()
        if not self.float_window.isHidden():
            tray.right_menu._detach_video()
            
        self.music_mode_dim_show = True
        #self.list_with_thumbnail = False
        self.image_fit_option_val = 3
        
        print('Music Mode')
        self.layout_mode = "Music"
        print(self.music_mode_dim, '--music--mode--')
        MainWindow.showNormal()
        MainWindow.hide()
        MainWindow.setGeometry(
            ui.music_mode_dim[0], ui.music_mode_dim[1], 
            ui.music_mode_dim[2], ui.music_mode_dim[3]
            )
        MainWindow.hide()
        MainWindow.setMaximumWidth(ui.music_mode_dim[2])
        MainWindow.setMaximumHeight(ui.music_mode_dim[3])
        #MainWindow.showMaximized()
        #MainWindow.hide()
        MainWindow.show()
        self.text.show()
        self.label.show()
        #self.label_new.show()
        show_hide_cover = 1
        self.tab_5.hide()
        show_hide_player = 0
        self.sd_hd.hide()
        self.audio_track.hide()
        self.subtitle_track.hide()
        self.player_loop_file.show()
        
        cnt = self.btn1.findText("Music")
        print(music_arr_setting, '--music-setting--')
        if cnt >=0 and cnt < self.btn1.count():
            self.btn1.setCurrentIndex(cnt)
            self.list3.setCurrentRow(music_arr_setting[0])
            self.list1.setCurrentRow(music_arr_setting[1])
            self.list1.hide()
            self.frame.hide()
            show_hide_titlelist = 0
            self.list2.setCurrentRow(music_arr_setting[2])
            self.list2.show()
            #ui.goto_epn.show()
            show_hide_playlist = 1
            self.list2.setFocus()
        self.widget_style.change_list2_style()
        self.apply_new_font()
        
    def video_mode_layout(self):
        global default_arr_setting, opt, new_tray_widget, tray, site
        global show_hide_titlelist
        #ui.VerticalLayoutLabel.addStretch(1)
        if not self.float_window.isHidden():
            tray.right_menu._detach_video()
        print('default Mode')
        if MainWindow.pos().y() < 0:
            yc = 32
        else:
            yc = MainWindow.pos().y()
        if self.music_mode_dim_show:
            self.music_mode_dim = [
                MainWindow.pos().x(), yc, 
                MainWindow.width(), MainWindow.height()
                ]
        print(self.music_mode_dim, '--video--mode--')
        self.music_mode_dim_show = False
        if self.player_theme in ['dark', 'system']:
            self.label_new.show()
        self.layout_mode = "Default"
        self.sd_hd.show()
        self.audio_track.show()
        self.subtitle_track.show()
        self.list1.show()
        show_hide_titlelist = 1
        #ui.frame.show()
        self.list2.show()
        #ui.goto_epn.show()
        MainWindow.setMaximumSize(QtCore.QSize(16777215, 16777215))
        print(default_arr_setting, '--default-setting--')
        if default_arr_setting[0] > 0 and default_arr_setting[0] < self.btn1.count():
            self.btn1.setCurrentIndex(default_arr_setting[0])
            if self.btn1.currentText() == 'Addons':
                self.btnAddon.setCurrentIndex(default_arr_setting[4])
            self.list3.setCurrentRow(default_arr_setting[1])
            try:
                option_val = self.list3.currentItem().text()
            except:
                option_val = "History"
            if (option_val and (option_val == 'History' or option_val == 'Available' 
                    or option_val == 'Directory') or site == 'Video'):
                if option_val == 'History':
                    print('--setting-history-option--')
                    opt = 'History'
                else:
                    opt = option_val
                self.setPreOpt(option_val=opt)
            if site == 'Video' and opt == 'History':
                self.list1.setCurrentRow(0)
            else:
                self.list1.setCurrentRow(default_arr_setting[2])
            self.list2.setCurrentRow(default_arr_setting[3])
            self.list2.setFocus()
            
        MainWindow.showMaximized()
        self.widget_style.change_list2_style()
        self.apply_new_font()
        
    def _set_window_frame(self):
        global new_tray_widget
        txt = self.window_frame
        if txt.lower() == 'false':
            MainWindow.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
            self.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint 
                | QtCore.Qt.WindowStaysOnTopHint)
        else:
            MainWindow.setWindowFlags(QtCore.Qt.Window 
                                      | QtCore.Qt.WindowTitleHint)
            self.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.WindowTitleHint 
                | QtCore.Qt.WindowStaysOnTopHint)
        MainWindow.show()
        
    def apply_new_style(self):
        change_opt_file(HOME_OPT_FILE, 'THEME=', 'THEME={0}'.format(self.player_theme.upper()))
        if self.player_theme == 'system':
            msg = 'Restart Application To Apply System Theme'
            send_notification(msg)
            self.text.setText(msg)
            self.progressEpn.setValue(0)
            self.progressEpn.setFormat((msg))
        else:
            if self.player_theme == 'mix':
                QtCore.QTimer.singleShot(
                    100, partial(
                        set_mainwindow_palette, self.default_background,
                        first_time=True, theme='default'
                        )
                    )
            else:
                QtCore.QTimer.singleShot(
                    100, partial(
                        set_mainwindow_palette, self.current_background,
                        first_time=True, theme=self.player_theme
                        )
                    )
            self.widget_style.apply_stylesheet(theme=self.player_theme)
            self.list1.setAlternatingRowColors(False)
            self.list2.setAlternatingRowColors(False)
            self.list3.setAlternatingRowColors(False)
            self.label_new.clear()
            #self.VerticalLayoutLabel_Dock3.setSpacing(5)
            #self.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
            
    def watch_external_video(self, var, mode=None, start_now=None):
        global site, home, local_torrent_file_path
        t = var
        logger.info(t)
        file_exists = False
        site = 'None'
        if os.path.exists(var):
            file_exists = True
        if (("file:///" in t or t.startswith('/') or t.startswith('http') or 
                file_exists) and not t.endswith('.torrent') and not 'magnet:' in t):
            self.quit_really="no"
            logger.info(t)
            txt_file = True
            if 'http' in t:
                t = re.search('http[^"]*', t).group()
                logger.info(t)
            if t.endswith('.m3u') or t.endswith('.pls'):
                t = urllib.parse.unquote(t)
                if os.path.exists(t):
                    lines = open_files(t, True)
                    logger.info(lines)
                elif t.startswith('http'):
                    content = ccurl(t)
                    logger.info(content)
                    if content:
                        lines = content.split('\n')
                    else:
                        lines = None
                    logger.info(lines)
                else:
                    lines = None
                if lines:
                    self.epn_arr_list[:] = []
                    cnt = len(lines)
                    i = 0
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    if t.endswith('.m3u'):
                        while i < cnt:
                            try:
                                if 'EXTINF' in lines[i]:
                                    n_epn = (lines[i].strip()).split(',', 1)[1]
                                    if n_epn.startswith('NONE - '):
                                        n_epn = n_epn.replace('NONE - ', '', 1)
                                    self.list2.addItem(n_epn)
                                    if i+1 < cnt:
                                        entry_epn = n_epn+'	'+lines[i+1].strip()+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                    i = i+2
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                                i = i+1
                    else:
                        while i < cnt:
                            try:
                                if lines[i].lower().startswith('file'):
                                    n_url = lines[i].strip().split('=', 1)[1]
                                    if i+1 < cnt:
                                        n_epn = str(i)
                                        if lines[i+1].lower().startswith('title'):
                                            n_epn = (lines[i+1].strip()).split('=', 1)[1]
                                            i = i+2
                                        elif lines[i-1].lower().startswith('title'):
                                            n_epn = (lines[i+1].strip()).split('=', 1)[1]
                                            i = i+1
                                        else:
                                            i = i+2
                                        if n_epn.startswith('NONE - '):
                                            n_epn = n_epn.replace('NONE - ', '', 1)
                                        self.list2.addItem(n_epn)
                                        entry_epn = n_epn+'	'+n_url+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                                i = i+1
                    if self.epn_arr_list:
                        file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                        f = open(file_name, 'w').close()
                        write_files(file_name, self.epn_arr_list, True)
                        self.list1.clear()
                        self.list1.addItem('TMP_PLAYLIST')
            elif t.startswith('http'):
                site = "PlayLists"
                t = urllib.parse.unquote(t)
                content = ccurl(t+'#'+'-I')
                if ('www-authenticate' in content.lower() 
                        or '401 unauthorized' in content.lower()):
                    dlg = LoginAuth(parent=MainWindow, url=t, ui=self, tmp=TMPDIR)
                    return 0
                torrent_file = False
                m3u_file = False
                if 'application/x-bittorrent' in content:
                    torrent_file = True
                elif ('audio/mpegurl' in content) or ('text/html' in content):
                    content = ccurl(t)
                    if '#EXTM3U' in content:
                        m3u_file = True
                
                if m3u_file:
                    lines = content.split('\n')
                    if lines:
                        self.epn_arr_list[:] = []
                        cnt = len(lines)
                        i = 0
                        self.btn1.setCurrentIndex(self.btn1.findText(site))
                        self.list2.clear()
                        while i < cnt:
                            try:
                                if 'EXTINF' in lines[i]:
                                    n_epn = (lines[i].strip()).split(',', 1)[1]
                                    if n_epn.startswith('NONE - '):
                                        n_epn = n_epn.replace('NONE - ', '', 1)
                                    self.list2.addItem(n_epn)
                                    if i+1 < cnt:
                                        entry_epn = n_epn+'	'+lines[i+1].strip()+'	'+'NONE'
                                        self.epn_arr_list.append(entry_epn)
                                    i = i+2
                                else:
                                    i = i+1
                            except Exception as e:
                                print(e)
                        if self.epn_arr_list:
                            file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                            f = open(file_name, 'w').close()
                            write_files(file_name, self.epn_arr_list, True)
                            self.list1.clear()
                            self.list1.addItem('TMP_PLAYLIST')
                elif torrent_file:
                    self.quick_torrent_play_method(url=t)
                else:
                    site == 'None'
                    finalUrl = t
                    if 'youtube.com' in t:
                        title_url = t
                    else:
                        title_url = 'ytdl:' + t
                    tmp_file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                    lines = open_files(tmp_file_name, True)
                    length = len(lines)
                    if self.gapless_network_stream: 
                        yt_mode = 'yt_title'
                    else:
                        yt_mode = 'yt+title'
                    if not self.epn_wait_thread.isRunning():
                        self.epn_wait_thread = PlayerGetEpn(
                            self, logger, yt_mode, title_url, self.quality_val,
                            self.ytdl_path, length)
                        self.epn_wait_thread.start()
                        self.yt_title_thread = True
                    else:
                        if self.yt_title_thread:
                            self.epn_wait_thread.terminate()
                            self.epn_wait_thread.wait()
                            self.yt_title_thread = False
                            if not self.epn_wait_thread.isRunning():
                                self.epn_wait_thread = PlayerGetEpn(
                                    self, logger, yt_mode, title_url, self.quality_val,
                                    self.ytdl_path, length)
                                self.epn_wait_thread.start()
                                self.yt_title_thread = True
                    if self.gapless_network_stream:
                        self.start_gapless_stream_process(length, link=title_url.replace('ytdl:', '', 1))
                    if mode == 'open url':
                        file_name = os.path.join(ui.home_folder, 'Playlists', 'TMP_PLAYLIST')
                        if not os.path.exists(file_name):
                            f = open(file_name, 'w').close()
                        self.list1.clear()
                        self.list1.addItem('TMP_PLAYLIST')
                        #self.list1.hide()
                        self.list1.show()
                        self.list1.setFocus()
                        self.list1.setCurrentRow(0)
            else:
                if not os.path.isfile(t):
                    t = urllib.parse.unquote(t)
                if os.path.isfile(t):
                    new_epn = os.path.basename(t)
                    self.epn_name_in_list = urllib.parse.unquote(new_epn)
                    self.watchDirectly(urllib.parse.unquote('"'+t+'"'), self.epn_name_in_list, 'no')
                    self.dockWidget_3.hide()
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    m = []
                    try:
                        path_Local_Dir, name = os.path.split(t)
                        list_dir = os.listdir(path_Local_Dir)
                    except Exception as e:
                        print(e)
                        return 0
                else:
                    self.dockWidget_3.hide()
                    site = "PlayLists"
                    self.btn1.setCurrentIndex(self.btn1.findText(site))
                    self.list2.clear()
                    m = []
                    try:
                        path_Local_Dir = t
                        list_dir = os.listdir(path_Local_Dir)
                    except Exception as e:
                        logger.error(e)
                        return 0
                for z in list_dir:
                    if ('.mkv' in z or '.mp4' in z or '.avi' in z or '.mp3' in z 
                                or '.flv' in z or '.flac' in z or '.wma' in z
                                or '.wmv' in z or '.ogg' in z or '.webm' in z
                                or '.wma' in z):
                            m.append(os.path.join(path_Local_Dir, z))
                m=naturallysorted(m)
                #print m
                self.epn_arr_list[:]=[]
                j = 0
                row = 0
                t = t.replace('"', '')
                t=urllib.parse.unquote(t)
                
                e = os.path.basename(t)
                
                for i in m:
                    i1 = i
                    i = os.path.basename(i)
                    self.epn_arr_list.append(i+'	'+i1+'	'+'NONE')
                    self.list2.addItem((i))
                    i = i
                    if i == e:
                        row = j
                    j =j+1
                self.list2.setCurrentRow(row)
                self.cur_row = row
                if self.epn_arr_list:
                    file_name = os.path.join(home, 'Playlists', 'TMP_PLAYLIST')
                    f = open(file_name, 'w').close()
                    write_files(file_name, self.epn_arr_list, True)
                    self.list1.clear()
                    self.list1.addItem('TMP_PLAYLIST')
                    self.list1.setCurrentRow(0)
                self.list2.setFocus()
        elif t.endswith('.torrent') or 'magnet:' in t:
            if t.startswith('http') or os.path.isfile(t) or 'magnet:' in t:
                self.quick_torrent_play_method(url=t)
            else:
                self.torrent_type = 'file'
                self.video_local_stream = True
                site = 'None'
                if OSNAME == 'posix':
                    t = t.replace('file:///', '/', 1)
                else:
                    t = t.replace('file:///', '', 1)
                t=urllib.parse.unquote(t)
                logger.info(t)
                local_torrent_file_path = t
                info = lt.torrent_info(t)
                file_arr = []
                self.list2.clear()
                self.epn_arr_list[:]=[]
                QtWidgets.QApplication.processEvents()
                for f in info.files():
                    file_path = f.path
                    logger.info(file_path)
                    file_path = os.path.basename(file_path)
                    self.epn_arr_list.append(file_path+'	'+t)
                    self.list2.addItem((file_path))
        elif 'magnet:' in t:
            t = re.search('magnet:[^"]*', t).group()
            site = 'None'
            self.torrent_type = 'magnet'
            self.video_local_stream = True
            self.local_torrent_open(t, start_now=start_now)
        else:
            self.quit_really = "yes"
            new_epn = os.path.basename(t)
            t = '"'+t+'"'
            self.epn_name_in_list = urllib.parse.unquote(new_epn)
            site = 'None'
            self.watchDirectly(urllib.parse.unquote(t), '', 'no')
            self.dockWidget_3.hide()
        #self.update_list2()
        if self.gapless_playback:
            self.use_playlist_method()
        
    def apply_new_font(self):
        global app
        try:
            font = 'default'
            if self.global_font != 'default':
                if isinstance(self.global_font_size, int):
                    font = QtGui.QFont(self.global_font, self.global_font_size)
                else:
                    font = QtGui.QFont(self.global_font)
                app.setFont(font)
            elif isinstance(self.global_font_size, int):
                font = QtGui.QFont('default', self.global_font_size)
                app.setFont(font)
            logger.debug('{}{}'.format(self.global_font, self.global_font_size))
            QtWidgets.QApplication.processEvents()
        except Exception as err:
            logger.error(err)
            
def main():
    global ui, MainWindow, tray, hdr, name, pgn, genre_num, site, name, epn
    global embed, epn_goto, opt, mirrorNo, queueNo
    global pre_opt, insidePreopt
    global new_tray_widget
    global rfr_url, category, home
    global player_focus, artist_name_mplayer
    global total_till, browse_cnt
    global view_layout
    global status, playlist_show
    global cache_empty, buffering_mplayer, slider_clicked, interval
    global iconv_r, path_final_Url, memory_num_arr, mpv_indicator
    global pause_indicator, default_option_arr
    global thumbnail_indicator, opt_movies_indicator
    global cur_label_num, iconv_r_indicator
    global audio_id, sub_id, site_arr, siteName, finalUrlFound
    global refererNeeded
    global update_start, screen_width, screen_height, total_till_epn
    global mpv_start
    global show_hide_cover, show_hide_playlist, show_hide_titlelist, server
    global show_hide_player, current_playing_file_path
    global music_arr_setting, default_arr_setting
    global local_torrent_file_path, wait_player, desktop_session
    global html_default_arr, app
    
    wait_player = False
    local_torrent_file_path = ''
    path_final_Url = ''
    default_arr_setting = [0, 0, 0, 0, 0]
    music_arr_setting = [0, 0, 0]
    show_hide_player = 0
    show_hide_cover = 1
    show_hide_playlist = 1
    show_hide_titlelist = 1
    mpv_start = []
    total_till_epn = 0
    update_start = 0
    artist_name_mplayer =""
    playlist_show = 1
    siteName = ""
    finalUrlFound = False
    refererNeeded = False
    site_arr = [
        "Local", "PlayLists", "Bookmark", 
        "Music", 'Video', 'YouTube', 'None'
        ]
    default_option_arr = [
        "Select", "Video", "Music", "Bookmark", 
        "PlayLists", "YouTube", "Addons"
        ]
    html_default_arr = ["Select", "Video", "Music", "Bookmark", "PlayLists"]
    MUSIC_EXT_LIST = [
        'mp3', 'flac', 'ogg', 'wav', 'aac', 'wma',
        'm4a', 'm4b', 'opus', 'webm'
        ]
    VIDEO_EXT_LIST = [
        'mkv', 'mp4', 'avi', 'flv', 'ogg', 'wmv',
        'webm', 'mpg', 'mpeg', 'mov'
        ]
    audio_id = "auto"
    sub_id = "auto"
    iconv_r_indicator = []
    cur_label_num = 0
    opt_movies_indicator=[]
    thumbnail_indicator=[]
    pause_indicator = []
    mpv_indicator = []
    memory_num_arr = []
    iconv_r = 6
    interval = 0
    slider_clicked = "no"
    buffering_mplayer = "no"
    cache_empty = "no"
    player_focus = 0
        
    status = "bookmark"
    view_layout = "List"
    total_till = 0
    browse_cnt = 0
    home = get_home_dir()
    category = "Animes"
    rfr_url = ""
    
    insidePreopt = 0
    pre_opt = ""
    queueNo = 0
    mirrorNo = 1
    epn_goto = 0
    epn = ""
    embed = 0
    epn = ''
    name = ''
    site = "None"
    genre_num = 0
    opt = ""
    pgn = 1
    site_index = 0
    addon_index = 0
    option_index = -1
    name_index = -1
    episode_index = -1
    option_val = ''
    option_sitename = None
    thumb_light = False
    dock_opt = 1
    pos_x = 0
    pos_y = 0
    w_ht = 0
    w_wdt = 50
    old_version = (0, 0, 0, 0)
    hdr = "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0"
    
    try:
        dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    except:
        pass
    desktop_session = os.getenv('DESKTOP_SESSION')
    if desktop_session:
        desktop_session = desktop_session.lower()
    else:
        desktop_session = 'lxde'
    print(OSNAME, desktop_session)
    app = QtWidgets.QApplication(sys.argv)
    media_data = MediaDatabase(
        home=home, logger=logger,
        music_ext=MUSIC_EXT_LIST, video_ext=VIDEO_EXT_LIST)
    screen_resolution = app.desktop().screenGeometry()
    screen_width = screen_resolution.width()
    screen_height = screen_resolution.height()
    print(screen_height, screen_width)
    MainWindow = MainWindowWidget()
    MainWindow.setMouseTracking(True)
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow, media_data=media_data)
    ui.media_data.set_ui(ui)
    ui.tab_5.set_mpvplayer(player=ui.player_val, mpvplayer=ui.mpvplayer_val)
    ui.getdb = ServerLib(ui, home, BASEDIR, TMPDIR, logger)
    ui.btn1.setFocus()
    ui.dockWidget_4.hide()
    ui.screen_size = (screen_width, screen_height)
    if not os.path.exists(home):
        os.makedirs(home)
    if not os.path.exists(os.path.join(home, 'src')):
        src_new = os.path.join(home, 'src')
        os.makedirs(src_new)
        if os.path.exists(RESOURCE_DIR):
            m = os.listdir(RESOURCE_DIR)
            for i in m:
                src_path = os.path.join(RESOURCE_DIR, i)
                if os.path.isfile(src_path):
                    if i == 'default.jpg':
                        shutil.copy(src_path, home)
                    elif i == 'kawaii-player.desktop':
                        pass
                    else:
                        shutil.copy(src_path, src_new)
        depend_path = os.path.join(BASEDIR, 'extra')
        if os.path.isdir(depend_path):
            m = os.listdir(depend_path)
            for i in m:
                depend_nm = os.path.join(depend_path, i)
                if os.path.isfile(depend_nm):
                    shutil.copy(depend_nm, src_new)
    picn = os.path.join(home, 'default.jpg')
    if not os.path.exists(picn):
        picn_1 = os.path.join(RESOURCE_DIR, 'default.jpg')
        if os.path.exists(picn_1):
            shutil.copy(picn_1, picn)
    
    if os.path.isfile(ui.playing_history_file):
        with open(ui.playing_history_file, 'rb') as pls_file_read:
            ui.history_dict_obj = pickle.load(pls_file_read)
            if '#GSBCH@DICT' in ui.history_dict_obj:
                ui.gsbc_dict = ui.history_dict_obj['#GSBCH@DICT'][0].copy()
                if ui.gsbc_dict:
                    for i in ui.gsbc_dict:
                        try:
                            slider = eval('ui.frame_extra_toolbar.{}_slider'.format(i))
                            slider.setValue(int(ui.gsbc_dict[i]))
                            logger.debug(i)
                        except Exception as err:
                            logger.error(err)
            if '#SUBTITLE@DICT' in ui.history_dict_obj:
                ui.subtitle_dict = ui.history_dict_obj['#SUBTITLE@DICT'][0].copy()
                scale = ui.subtitle_dict.get('sub-scale')
                if scale:
                    scale = 100 * float(scale)
                    ui.frame_extra_toolbar.subscale_slider.setValue(scale)
                
    if os.path.isfile(ui.playing_queue_file):
        with open(ui.playing_queue_file, 'rb') as queue_file_read:
            ui.queue_url_list = pickle.load(queue_file_read)
        ui.list6.clear()
        for i in ui.queue_url_list:
            if isinstance(i, tuple):
                txt_load = i[-1]
            else:
                if '\t' in i:
                    txt_load = i.split('\t')[0]
                else:
                    txt_load = i
                if txt_load.startswith('#'):
                    txt_load = txt_load.replace('#', '', 1)
            ui.list6.addItem(txt_load)
        os.remove(ui.playing_queue_file)
        
    if not os.path.exists(os.path.join(home, 'src', 'Plugins')):
        os.makedirs(os.path.join(home, 'src', 'Plugins'))
        sys.path.append(os.path.join(home, 'src', 'Plugins'))
        plugin_Dir = os.path.join(home, 'src', 'Plugins')
        s_dir = os.path.join(BASEDIR, 'Plugins')
        if not os.path.exists(s_dir):
            s_dir = os.path.join(BASEDIR, 'plugins')
        if os.path.exists(s_dir):
            m_tmp = os.listdir(s_dir)
            for i in m_tmp:
                k = os.path.join(s_dir, i)
                if (os.path.isfile(k) and i != "install.py" 
                        and i != "installPlugins.py" and i != '__init__'):
                    shutil.copy(k, plugin_Dir)
                    print("addons loading....")
                        
    if os.path.exists(os.path.join(home, 'config.txt')):
        lines = open_files(os.path.join(home, 'config.txt'), True)
        for i in lines:
            if not i.startswith('#'):
                j = i.split('=')[-1]
                if "VERSION_NUMBER" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('(', '')
                        j = j.replace(')', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        jr = []
                        for l in k:
                            jr.append(int(l))
                        old_version = tuple(jr)
                    except:
                        pass
                    #print(old_version)
                elif "FloatWindow" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('[', '')
                        j = j.replace(']', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        ui.float_window_dim[:] = []
                        for l in k:
                            ui.float_window_dim.append(int(l))
                        print(ui.float_window_dim)
                    except:
                        ui.float_window_dim = [0, 0, 250, 200]
                elif "MusicWindowDim" in i:
                    try:
                        j = j.replace('\n', '')
                        j = j.replace('[', '')
                        j = j.replace(']', '')
                        j = j.replace(' ', '')
                        k = j.split(',')
                        ui.music_mode_dim[:] = []
                        for l in k:
                            ui.music_mode_dim.append(int(l))
                        print(ui.music_mode_dim, '--music--mode--dimension--set--')
                    except:
                        ui.music_mode_dim = [0, 0, 900, 350]
                elif "DefaultPlayer" in i:
                    player_txt_val = j.strip().lower()
                    if player_txt_val in ui.playback_engine:
                        player_txt = player_txt_val
                    else:
                        player_txt = 'mpv'
                    ui.player_val = player_txt
                    ui.chk.setText(ui.player_val)
                    if j.strip() in ['MPV', 'MPLAYER']:
                        ui.player_val = j.strip()
                        ui.chk.setText(ui.player_val)
                elif "WindowFrame" in i:
                    try:
                        j = j.replace('\n', '')
                        ui.window_frame = str(j)
                    except:
                        ui.window_frame = 'true'
                elif "DockPos" in i:
                    try:
                        j = j.strip()
                        ui.orientation_dock = str(j)
                    except:
                        ui.orientation_dock = 'left'
                elif "MusicModeDimShow" in i:
                    try:
                        j = j.replace('\n', '')
                        val_m = str(j)
                    except:
                        val_m = 'False'
                    if val_m.lower() == 'true':
                        ui.music_mode_dim_show = True
                    else:
                        ui.music_mode_dim_show = False
                elif "Video_Mode_Index" in i:
                    try:
                        j = j.replace('\n', '')
                        ui.video_mode_index = int(j)+1
                        ui.comboBoxMode.setCurrentIndex(int(j))
                    except:
                        ui.video_mode_index = 1
                        ui.comboBoxMode.setCurrentIndex(0)
                elif "List_Mode_With_Thumbnail" in i:
                    tmp_mode = re.sub('\n', '', j)
                    if tmp_mode.lower() == 'true':
                        ui.list_with_thumbnail = True
                    else:
                        ui.list_with_thumbnail = False
                    #ui.widget_style.apply_stylesheet(widget=ui.list2, theme=ui.player_theme)
                elif "Site_Index" in i:
                    site_i = re.sub('\n', '', j)
                    if site_i.isdigit():
                        site_index = int(site_i)
                    print(site_index, '--site-index--')
                elif "Addon_Index" in i:
                    addon_i = re.sub('\n', '', j)
                    if addon_i.isdigit():
                        addon_index = int(addon_i)
                    print(addon_index, '--addon-index--')
                elif "Option_Index" in i:
                    opt_i = re.sub('\n', '', j)
                    if opt_i.isdigit():
                        option_index = int(opt_i)
                    print(option_index, '--option-index--')
                elif "SUB_ID" in i:
                    sub_id = re.sub('\n', '', j)
                elif "AUDIO_ID" in i:
                    audio_id = re.sub('\n', '', j)
                elif i.startswith('VOLUME_TYPE='):
                    try:
                        j = j.strip()
                        if j and j in ['ao-volume', 'volume']:
                            ui.volume_type = j
                    except Exception as err:
                        logger.error(err)
                elif i.startswith('VOLUME_VALUE='):
                    try:
                        j = j.strip()
                        if j:
                            if j.isnumeric():
                                ui.player_volume = j
                            else:
                                ui.player_volume = '50'
                            if ui.player_volume.isnumeric():
                                ui.frame_extra_toolbar.slider_volume.setValue(int(ui.player_volume))
                    except Exception as err:
                        logger.error(err)
                elif i.startswith('CLICKED_LABEL_NEW='):
                    try:
                        j = j.strip()
                        if j.lower() == 'true':
                            ui.clicked_label_new = True
                    except Exception as err:
                        logger.error(err)
                elif i.startswith('APPLY_SUBTITLE_SETTINGS='):
                    try:
                        j = j.strip()
                        if j.lower() == 'false':
                            ui.apply_subtitle_settings = False
                            ui.frame_extra_toolbar.checkbox_dont.setChecked(True)
                    except Exception as err:
                        logger.error(err)
                elif "Option_SiteName" in i:
                    option_sitename = re.sub('\n', '', j)
                    if option_sitename:
                        if option_sitename.lower() == 'none':
                            option_sitename = None
                    print(option_sitename, siteName, '-------')
                elif "Thumbnail_Light" in i:
                    thumb_light = re.sub('\n', '', j)
                    if thumb_light:
                        if thumb_light.lower() == 'true':
                            thumb_light = True
                elif "Video_Aspect" in i:
                    video_aspect = re.sub('\n', '', j)
                    if video_aspect.isdigit():
                        ui.mpvplayer_aspect_cycle = int(video_aspect)
                    print(video_aspect, '--video-aspect--')
                elif "Upload_Speed" in i:
                    upspeed = re.sub('\n', '', j)
                    if upspeed.isnumeric():
                        ui.setuploadspeed = int(upspeed)
                    #print(upspeed, '--server-upspeed--')
                elif "Name_Index" in i:
                    name_i = re.sub('\n', '', j)
                    if name_i.isdigit():
                        name_index = int(name_i)
                    print(name_index, '--name-index--')
                elif "Episode_Index" in i:
                    epi_i = re.sub('\n', '', j)
                    if epi_i.isdigit():
                        episode_index = int(epi_i)
                    print(episode_index, '--episode-index--')
                elif "Option_Val" in i:
                    opt_v = re.sub('\n', '', j)
                    option_val = opt_v
                    print(option_val, '--option--')
                elif "Quality" in i:
                    quality = re.sub('\n', '', j)
                    ui.client_quality_val = quality
                    ui.quality_val = quality
                    print(quality, '----quality---')
                    if quality == "hd":
                        ui.sd_hd.setText("HD")
                    elif quality == 'sd480p':
                        ui.sd_hd.setText("480")
                    elif quality == 'best':
                        ui.sd_hd.setText("BEST")
                    else:
                        ui.sd_hd.setText("SD")
                elif "Dock_Option" in i:
                    dock_o = re.sub('\n', '', j)
                    if dock_o.isdigit():
                        dock_opt = int(dock_o)
                elif "Show_Hide_Cover" in i:
                    try:
                        show_hide_cover = int(j)
                        if show_hide_cover == 0:
                            ui.text.hide()
                            ui.label.hide()
                    except:
                        show_hide_cover = 0
                elif 'SETTINGS_TAB_INDEX' in i:
                    try:
                        ui.settings_tab_index = int(j)
                    except Exception as err:
                        logger.error(err)
                elif "Show_Hide_Playlist" in i:
                    try:
                        show_hide_playlist = int(j)
                        if show_hide_playlist == 0:
                            ui.list2.hide()
                            ui.goto_epn.hide()
                    except:
                        show_hide_playlist = 0
                elif "Show_Hide_Titlelist" in i:
                    try:
                        show_hide_titlelist = int(j)
                        if show_hide_titlelist == 0:
                            ui.list1.hide()
                            ui.frame.hide()
                    except:
                        show_hide_titlelist = 0
                elif "Show_Hide_Player" in i:
                    try:
                        show_hide_player = int(j)
                    except:
                        show_hide_player = 0
                elif "Force_FS" in i:
                    j = j.strip()
                    try:
                        if j.lower() == 'true':
                            ui.force_fs = True
                        else:
                            ui.force_fs = False
                    except Exception as err:
                        logger.error(err)
                        ui.force_fs = False
                    logger.debug('fs={0}'.format(ui.force_fs))
                elif "Thumbnail_Size" in i:
                    j = j.replace('\n', '')
                    if j:
                        iconv_r = int(j)
                        iconv_r_indicator.append(iconv_r)
                elif "Thumbnail_Poster" in i:
                    j = j.replace('\n', '')
                    if j:
                        icon_poster = int(j)
                        ui.icon_poster_indicator.append(icon_poster)
                elif "View" in i:
                    view_mode = j.replace('\n', '')
                    if view_mode == "thumbnail":
                        ui.view_mode = 'thumbnail'
                    elif view_mode == 'thumbnail_light':
                        ui.view_mode = 'thumbnail_light'
                elif "Layout" in i:
                    ui.layout_mode = j.replace('\n', '')
                elif "POSX" in i:
                    posx = re.sub('\n', '', j)
                    if posx.isdigit():
                        pos_x = int(posx)
                elif "POSY" in i:
                    pos_yy = re.sub('\n', '', j)
                    if pos_yy.isdigit():
                        pos_y = int(pos_yy)
                elif "WHeight" in i:
                    ht1 = re.sub('\n', '', j)
                    if ht1.isdigit():
                        w_ht = int(ht1)
                elif "WWidth" in i:
                    wd2 = re.sub('\n', '', j)
                    if wd2.isdigit():
                        w_wdt = int(wd2)
                elif "Default_Mode" in i:
                    try:
                        def_m = re.sub('\n', '', j)
                        t_v = def_m.split(',')
                        for l,z in enumerate(t_v):
                            if z:
                                default_arr_setting[l] = int(z.strip())
                        logger.info(default_arr_setting)
                    except Exception as e:
                        print(e,'--20251--')
                elif 'Music_Mode' in i:
                    try:
                        def_m = re.sub('\n', '', j)
                        t_v = def_m.split(',')
                        for l,z in enumerate(t_v):
                            if z:
                                music_arr_setting[l] = int(z.strip())
                        logger.info(music_arr_setting)
                    except Exception as e:
                        print(e,'--20261--')
    else:
        f = open(os.path.join(home, 'config.txt'), 'w')
        f.write("DefaultPlayer=mpv")
        f.close()
    
    if os.path.exists(os.path.join(home, 'torrent_config.txt')):
        lines = open_files(os.path.join(home, 'torrent_config.txt'), True)
        #print(lines)
        for i in lines:
            if not i.startswith('#'):
                j = i.split('=')[-1]
                if "TORRENT_STREAM_IP" in i:
                    j = re.sub('\n', '', j)
                    j1 = j.split(':')
                    if len(j1) == 2:
                        if j1[0].lower()=='localhost' or not j1[0]:
                            ui.local_ip = '127.0.0.1'
                        else:
                            ui.local_ip = j1[0]
                        try:
                            ui.local_port = int(j1[1])
                        except Exception as e:
                            print(e)
                            ui.local_port = 8001
                    else:
                        ui.local_ip = '127.0.0.1'
                        ui.local_port = 8001
                    if ui.local_ip not in ui.client_auth_arr:
                        ui.client_auth_arr.append(ui.local_ip)
                elif "TORRENT_DOWNLOAD_FOLDER" in i:
                    j = re.sub('\n', '', j)
                    if j.endswith('/'):
                        j = j[:-1]
                    if os.path.exists(j):
                        ui.torrent_download_folder = j
                    else:
                        ui.torrent_download_folder = TMPDIR
                elif "TORRENT_UPLOAD_RATE" in i:
                    j = re.sub('\n', '', j)
                    try:
                        ui.torrent_upload_limit = int(j)*1024
                    except:
                        ui.torrent_upload_limit = 0
                elif "TORRENT_DOWNLOAD_RATE" in i:
                    j = re.sub('\n', '', j)
                    try:
                        ui.torrent_download_limit = int(j)*1024
                    except:
                        ui.torrent_download_limit = 0
    else:
        f = open(os.path.join(home, 'torrent_config.txt'), 'w')
        f.write("TORRENT_STREAM_IP=127.0.0.1:8001")
        f.write("\nTORRENT_DOWNLOAD_FOLDER="+TMPDIR)
        f.write("\nTORRENT_UPLOAD_RATE=0")
        f.write("\nTORRENT_DOWNLOAD_RATE=0")
        f.close()
        ui.local_ip = '127.0.0.1'
        ui.local_port = 8001
    options_txt_file = os.path.join(home, 'other_options.txt')
    if os.path.exists(options_txt_file):
        lines = open_files(options_txt_file, True)
        for i in lines:
            i = i.strip()
            if not i.startswith('#'):
                j = i.split('=')[-1]
                if "LOCAL_STREAM_IP" in i:
                    j1 = j.split(':')
                    if len(j1) == 2:
                        if j1[0].lower()=='localhost' or not j1[0]:
                            ui.local_ip_stream = '127.0.0.1'
                        else:
                            ui.local_ip_stream = j1[0]
                        try:
                            ui.local_port_stream = int(j1[1])
                        except Exception as e:
                            print(e)
                            ui.local_port_stream = 9001
                    else:
                        ui.local_ip_stream = '127.0.0.1'
                        ui.local_port_stream = 9001
                    if ui.local_ip_stream not in ui.client_auth_arr:
                        ui.client_auth_arr.append(ui.local_ip_stream)
                elif 'DEFAULT_DOWNLOAD_LOCATION' in i:
                    ui.default_download_location = j
                elif 'GET_LIBRARY' in i:
                    ui.get_fetch_library = j
                elif 'TMP_REMOVE' in i:
                    if j == 'yes' or j == 'no':
                        ui.tmp_folder_remove = j
                    else:
                        ui.tmp_folder_remove = 'no'
                elif 'IMAGE_FIT_OPTION' in i:
                    try:
                        k = int(j)
                    except Exception as e:
                        print(e)
                        k = 3
                    ui.image_fit_option_val = k
                elif i.startswith('AUTH='):
                    try:
                        if (j.lower() != 'none'):
                            ui.media_server_key = j
                        else:
                            ui.media_server_key = None
                    except Exception as e:
                        print(e)
                        ui.media_server_key = None
                elif i.startswith('ACCESS_FROM_OUTSIDE_NETWORK='):
                    try:
                        if (':' in j) and (j.lower() != 'none'):
                            tmp = j.split(':')
                            if tmp[0].lower() == 'true':
                                ui.access_from_outside_network = True
                            else:
                                ui.access_from_outside_network = False
                            try:
                                ui.get_ip_interval = float(tmp[1])
                            except Exception as e:
                                print(e)
                                ui.get_ip_interval = 1
                        else:
                            if j.lower() == 'true':
                                ui.access_from_outside_network = True
                            else:
                                ui.access_from_outside_network = False
                                
                    except Exception as e:
                        print(e)
                        ui.access_from_outside_network = False
                elif i.startswith('CLOUD_IP_FILE='):
                    try:
                        if j.lower() == 'none' or j.lower() == 'false' or not j:
                            ui.cloud_ip_file = None
                        else:
                            if os.path.isfile(j):
                                ui.cloud_ip_file = j
                            else:
                                ui.cloud_ip_file = None
                    except Exception as e:
                        print(e)
                        ui.cloud_ip_file = None
                elif i.startswith('KEEP_BACKGROUND_CONSTANT='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.keep_background_constant = True
                            else:
                                ui.keep_background_constant = False
                    except Exception as e:
                        print(e)
                        ui.keep_background_constant = False
                elif i.startswith('GAPLESS_PLAYBACK='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.gapless_playback = True
                    except Exception as e:
                        print(e)
                elif i.startswith('GAPLESS_NETWORK_STREAM='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.gapless_network_stream = True
                    except Exception as e:
                        print(e)
                elif i.startswith('USE_SINGLE_NETWORK_STREAM='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'no' or k == 'false' or k == '0':
                                ui.use_single_network_stream = False
                    except Exception as e:
                        print(e)
                elif i.startswith('HTTPS_ON='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.https_media_server = True
                            else:
                                ui.https_media_server = False
                    except Exception as e:
                        print(e)
                        ui.https_media_server = False
                elif i.startswith('MEDIA_SERVER_AUTOSTART='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.media_server_autostart = True
                            else:
                                ui.media_server_autostart = False
                    except Exception as e:
                        print(e)
                        ui.media_server_autostart = False
                elif i.startswith('MEDIA_SERVER_COOKIE='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.media_server_cookie = True
                            else:
                                ui.media_server_cookie = False
                    except Exception as e:
                        print(e)
                        ui.media_server_cookie = False
                elif i.startswith('COOKIE_EXPIRY_LIMIT='):
                    try:
                        k = float(j)
                        ui.cookie_expiry_limit = k
                    except Exception as e:
                        print(e)
                        ui.cookie_expiry_limit = 24
                elif i.startswith('COOKIE_PLAYLIST_EXPIRY_LIMIT='):
                    try:
                        k = float(j)
                        ui.cookie_playlist_expiry_limit = k
                    except Exception as e:
                        print(e)
                        ui.cookie_playlist_expiry_limit = 24
                elif i.startswith('CACHE_PAUSE_SECONDS='):
                    try:
                        if j.isnumeric():
                            ui.cache_pause_seconds = int(j)
                    except Exception as e:
                        print(e)
                elif i.startswith('LOGGING='):
                    try:
                        k = j.lower()
                        if k == 'off' or k == 'false':
                            ui.logging_module = False
                        elif k == 'on' or k == 'true':
                            ui.logging_module = True
                        else:
                            ui.logging_module = False
                    except Exception as e:
                        print(e)
                        ui.logging_module = False
                elif i.startswith('GET_MUSIC_METADATA='):
                    try:
                        k = j.lower()
                        if k == 'on' or k == 'true' or k == 'yes':
                            ui.get_artist_metadata = True
                    except Exception as e:
                        print(e)
                elif i.startswith('REMOTE_CONTROL='):
                    try:
                        k = j.lower()
                        if k == 'on' or k == 'true' or k == 'yes':
                            ui.remote_control_field = True
                            ui.action_player_menu[9].setText("Turn Off Remote Control")
                    except Exception as e:
                        print(e)
                elif i.startswith('BROADCAST_MESSAGE='):
                    try:
                        j = j.replace('"', '')
                        j = j.replace("'", '')
                        if j and j.lower() != 'false':
                            ui.broadcast_message = j
                    except Exception as e:
                        print(e)
                elif i.startswith('MPV_INPUT_CONF='):
                    try:
                        if j and j.lower() == 'true':
                            ui.custom_mpv_input_conf = True
                        logger.info('mpv_conf: {0}'.format(ui.custom_mpv_input_conf))
                    except Exception as e:
                        print(e)
                elif i.startswith('USE_CUSTOM_CONFIG_FILE='):
                    try:
                        if j and j.lower() in ['true', 'yes']:
                            ui.use_custom_config_file = True
                    except Exception as e:
                        print(e)
                elif i.startswith('ANIME_REVIEW_SITE='):
                    try:
                        k = j.lower()
                        if k:
                            if k == 'yes' or k == 'true' or k == '1':
                                ui.anime_review_site = True
                            else:
                                ui.anime_review_site = False
                    except Exception as e:
                        print(e)
                        ui.anime_review_site = False
                elif i.startswith('THEME='):
                    try:
                        k = j.lower()
                        if k:
                            if k in ['system', 'transparent', 'mix', 'dark']:
                                ui.player_theme = k
                            else:
                                ui.player_theme = 'default'
                    except Exception as e:
                        print(e)
                        ui.player_theme = 'default'
                elif i.startswith('EXTRA_PLAYERS='):
                    try:
                        extra_players = j.split(',')
                        for extra_player in extra_players:
                            if (extra_player not in ui.playback_engine
                                    and extra_player.lower() != 'none'):
                                ui.playback_engine.append(extra_player)
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('THUMBNAIL_TEXT_COLOR='):
                    try:
                        thumb_color = j.lower()
                        if thumb_color in ui.thumbnail_text_color_dict:
                            ui.thumbnail_text_color = thumb_color
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('THUMBNAIL_TEXT_COLOR_FOCUS='):
                    try:
                        thumb_color = j.lower()
                        if thumb_color in ui.thumbnail_text_color_dict:
                            ui.thumbnail_text_color_focus = thumb_color
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('LIST_TEXT_COLOR='):
                    try:
                        list_color = j.lower()
                        if list_color in ui.thumbnail_text_color_dict:
                            ui.list_text_color = list_color
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('LIST_TEXT_COLOR_FOCUS='):
                    try:
                        list_color = j.lower()
                        if list_color in ui.thumbnail_text_color_dict:
                            ui.list_text_color_focus = list_color
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('GLOBAL_FONT='):
                    try:
                        global_font = j
                        if global_font:
                            if global_font.lower() == 'default':
                                ui.global_font = QtGui.QFont().defaultFamily()
                            else:
                                ui.global_font = global_font
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('FONT_BOLD='):
                    try:
                        font_bold = j.lower()
                        if font_bold in ['false', 'no']:
                            ui.font_bold = False
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('GLOBAL_FONT_SIZE='):
                    try:
                        global_font_size = j.lower()
                        if global_font_size.isnumeric():
                            ui.global_font_size = int(global_font_size)
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('SCREENSHOT_DIRECTORY='):
                    try:
                        if os.path.exists(j):
                            ui.screenshot_directory = j
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('REMEMBER_VOLUME_PER_VIDEO='):
                    try:
                        vol = j.lower()
                        if vol in ['true', 'yes']:
                            ui.restore_volume = True
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('REMEMBER_ASPECT_PER_VIDEO='):
                    try:
                        asp = j.lower()
                        if asp in ['true', 'yes']:
                            ui.restore_aspect = True
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('AUDIO_OUTPUTS='):
                    try:
                        ui.audio_outputs = j
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('VIDEO_OUTPUTS='):
                    try:
                        ui.video_outputs = j
                    except Exception as e:
                        logger.error(e)
                elif i.startswith('YTDL_PATH='):
                    try:
                        k = j.lower()
                        if k == 'default':
                            ui.ytdl_path = 'default'
                        elif k == 'automatic':
                            if OSNAME == 'posix':
                                ui.ytdl_path = os.path.join(home, 'src', 'ytdl')
                            elif OSNAME == 'nt':
                                ui.ytdl_path = os.path.join(home, 'src', 'ytdl.exe') 
                        else:
                            if os.path.exists(j):
                                ui.ytdl_path = j
                            else:
                                ui.ytdl_path = 'default'
                    except Exception as e:
                        print(e)
                        ui.ytdl_path = 'default'
            else:
                logger.debug(i)
    else:
        with open(options_txt_file, 'w') as f:
            f.write("#BROWSER_BACKEND=QTWEBENGINE,QTWEBKIT")
            if BROWSER_BACKEND == 'QTWEBENGINE':
                f.write("\nBROWSER_BACKEND=QTWEBENGINE")
            elif BROWSER_BACKEND == 'QTWEBKIT':
                f.write("\nBROWSER_BACKEND=QTWEBKIT")
            f.write("\nLOCAL_STREAM_IP=127.0.0.1:9001")
            f.write("\nDEFAULT_DOWNLOAD_LOCATION="+TMPDIR)
            f.write("\nKEEP_BACKGROUND_CONSTANT=no")
            f.write("\nTMP_REMOVE=no")
            f.write("\n#GET_LIBRARY=pycurl,curl,wget")
            if OSNAME == 'nt':
                f.write("\nGET_LIBRARY=curl")
            else:
                f.write("\nGET_LIBRARY=pycurl")
            f.write("\n#IMAGE_FIT_OPTION=0-9")
            f.write("\nIMAGE_FIT_OPTION=3")
            f.write("\nAUTH=NONE")
            f.write("\nACCESS_FROM_OUTSIDE_NETWORK=False")
            f.write("\nCLOUD_IP_FILE=none")
            f.write("\nHTTPS_ON=False")
            f.write("\nMEDIA_SERVER_COOKIE=False")
            f.write("\nCOOKIE_EXPIRY_LIMIT=24")
            f.write("\nCOOKIE_PLAYLIST_EXPIRY_LIMIT=24")
            f.write("\nLOGGING=Off")
            f.write("\n#YTDL_PATH=default,automatic")
            f.write("\nYTDL_PATH=DEFAULT")
            f.write("\nANIME_REVIEW_SITE=False")
            f.write("\nGET_MUSIC_METADATA=False")
            f.write("\nREMOTE_CONTROL=False")
            f.write("\nMPV_INPUT_CONF=False")
            f.write("\nBROADCAST_MESSAGE=False")
            f.write("\nMEDIA_SERVER_AUTOSTART=False")
            f.write("\n#THEME=default,system,dark")
            f.write("\nTHEME=DEFAULT")
            f.write("\n#EXTRA_PLAYERS=vlc,kodi etc..")
            f.write("\nEXTRA_PLAYERS=NONE")
            f.write("\n#GLOBAL_FONT=Name of Font")
            f.write("\nGLOBAL_FONT=Default")
            f.write("\nGLOBAL_FONT_SIZE=Default")
            f.write("\nFONT_BOLD=True")
            msg = ("\n#THUMBNAIL_TEXT_COLOR/LIST_TEXT_COLOR=red,green,blue,yellow,\
                   gray,white,black,cyan,magenta,darkgray,lightgray,darkred,\
                   darkblue,darkyellow,transparent")
            msg = re.sub('[ ]+', ' ', msg)
            f.write(msg)
            f.write("\n#For Dark Theme, use lightgray, if white color looks bright")
            f.write("\nTHUMBNAIL_TEXT_COLOR=white")
            f.write("\nTHUMBNAIL_TEXT_COLOR_FOCUS=green")
            f.write("\nLIST_TEXT_COLOR=white")
            f.write("\nLIST_TEXT_COLOR_FOCUS=violet")
            f.write("\nREMEMBER_VOLUME_PER_VIDEO=False")
            f.write("\nREMEMBER_ASPECT_PER_VIDEO=True")
        ui.local_ip_stream = '127.0.0.1'
        ui.local_port_stream = 9001
    if ui.player_theme == 'mix':
        QtCore.QTimer.singleShot(
            100, partial(
                set_mainwindow_palette, ui.default_background,
                first_time=True, theme='default'
                )
            )
    else:
        QtCore.QTimer.singleShot(
            100, partial(
                set_mainwindow_palette, picn, first_time=True,
                theme=ui.player_theme
                )
            )
    
    try:
        font = 'default'
        if ui.global_font != 'default':
            if isinstance(ui.global_font_size, int):
                font = QtGui.QFont(ui.global_font, ui.global_font_size)
            else:
                font = QtGui.QFont(ui.global_font)
            app.setFont(font)
        elif isinstance(ui.global_font_size, int):
            font = QtGui.QFont('default', ui.global_font_size)
            app.setFont(font)
        logger.debug('{}{}'.format(ui.global_font, ui.global_font_size))
    except Exception as err:
        logger.error(err)
    
    ui.widget_style.apply_stylesheet(theme=ui.player_theme)
    print(ui.torrent_download_limit, ui.torrent_upload_limit)
    
    anime_review_arr = ["MyAnimeList", "Anime-Planet", "Anime-Source", "AniDB", 
                        "Zerochan", "ANN"]
    if not ui.anime_review_site:
        for i in anime_review_arr:
            if ui.browser_bookmark.get(i):
                del ui.browser_bookmark[i]
    for i in ui.browser_bookmark:
        ui.btnWebReviews.addItem(i)
    ui.btnWebReviews.currentIndexChanged['int'].connect(
        lambda x: ui.reviewsWeb(action='index_changed')
        )
    if not ui.logging_module:
        logger.disabled = True
        
    arr_setting = []
    
    arr_setting.append(show_hide_titlelist)
    arr_setting.append(show_hide_playlist)
    
    if not os.path.exists(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.exists(home):
        os.makedirs(home)
    if os.path.exists(os.path.join(home, 'src')):
        os.chdir(os.path.join(home, 'src'))
        #sys.path.append(os.path.join(home, 'src'))
    else:
        os.chdir(BASEDIR)
    if not os.path.exists(os.path.join(home, "History")):
        os.makedirs(os.path.join(home, "History"))
    if not os.path.exists(os.path.join(home, "thumbnails")):
        os.makedirs(os.path.join(home, "thumbnails"))
    if not os.path.exists(os.path.join(home, "Local")):
        os.makedirs(os.path.join(home, "Local"))
    if not os.path.exists(os.path.join(home, "tmp")):
        os.makedirs(os.path.join(home, "tmp"))
    if not os.path.exists(os.path.join(home, "Bookmark")):
        os.makedirs(os.path.join(home, "Bookmark"))
        bookmark_array = [
            'bookmark', 'Watching', 'Completed', 'Incomplete', 
            'Later', 'Interesting', 'Music Videos'
            ]
        for i in bookmark_array:
            bookmark_path = os.path.join(home, 'Bookmark', i+'.txt')
            if not os.path.exists(bookmark_path):
                f = open(bookmark_path, 'w')
                f.close()
    if not os.path.exists(os.path.join(home, "config.txt")):
        f = open(os.path.join(home, "config.txt"), "w")
        f.write("DefaultPlayer=mpv")
        f.close()
    if not os.path.exists(os.path.join(home, "Playlists")):
        os.makedirs(os.path.join(home, "Playlists"))
    if not os.path.exists(ui.yt_sub_folder):
        os.makedirs(ui.yt_sub_folder)
    if not os.path.exists(os.path.join(home, "Playlists", "Default")):
        f = open(os.path.join(home, "Playlists", "Default"), "w")
        f.close()
    
    if os.path.exists(os.path.join(home, 'src', 'Plugins')):
        sys.path.append(os.path.join(home, 'src', 'Plugins'))
        print("plugins")
        
        if ui.version_number > old_version:
            print(ui.version_number, '>', old_version)
            plugin_Dir = os.path.join(home, 'src', 'Plugins')
            s_dir = os.path.join(BASEDIR, 'Plugins')
            if not os.path.exists(s_dir):
                s_dir = os.path.join(BASEDIR, 'plugins')
            if os.path.exists(s_dir):
                m_tmp = os.listdir(s_dir)
                for i in m_tmp:
                    k = os.path.join(s_dir, i)
                    if (os.path.isfile(k) and i != "install.py" 
                            and i != "installPlugins.py" and i != '__init__'):
                        shutil.copy(k, plugin_Dir)
                        print('Addons loading ....')
            if ui.history_dict_obj:
                last_title_list = ui.history_dict_obj.get('#LAST@TITLE')
                if last_title_list:
                    if len(last_title_list) in [5, 6]:
                        for item in ui.history_dict_obj:
                            item_val = ui.history_dict_obj[item]
                            if len(item_val) == 5:
                                item_val.append('auto')
                                item_val.append('-1')
                                ui.history_dict_obj.update({item:item_val})
                            elif len(item_val) == 6:
                                item_val.append('-1')
                                ui.history_dict_obj.update({item:item_val})
                                logger.debug('updating...')
        m = os.listdir(os.path.join(home, 'src', 'Plugins'))
        m.sort()
        for i in m:
            if i.endswith('.py'):
                i = i.replace('.py', '')
                if (i != 'headlessBrowser' and i != 'headlessEngine' 
                        and i!='stream' and i!='local_ip' 
                        and i!= 'headlessBrowser_webkit' and i!='installPlugins' 
                        and i != '__init__'):
                    ui.addons_option_arr.append(i)
    
    
    f = open(os.path.join(home, "History", "queue.m3u"), "w")
    f.write("#EXTM3U")
    f.close()
            
    for i in default_option_arr:
        ui.btn1.addItem(i)
    for i in ui.addons_option_arr:
        ui.btnAddon.addItem(i)
    
    print(site, site_index, '==site_index')
    if site_index >0 and site_index < ui.btn1.count():
        ui.btn1.setCurrentIndex(site_index)
        if (ui.btn1.currentText() == 'Addons' and addon_index >=0 
                and addon_index < ui.btnAddon.count()):
            ui.btnAddon.setCurrentIndex(addon_index)
    elif site_index == 0:
        ui.btn1.setCurrentIndex(1)
        ui.btn1.setCurrentIndex(0)
        
    if option_index < 0 and ui.list3.count() > 0:
        option_index = 0
        print(option_index, ui.list3.count(), '--list3--cnt--')
    
    if option_index >=0 and option_index < ui.list3.count():
        ui.list3.setCurrentRow(option_index)
        ui.list3.setFocus()
        if option_val and option_val.lower() != 'update' and option_val.lower() != 'updateall': 
            if option_val == 'History':
                print('--setting-history-option--')
                opt = 'History'
                print(opt, siteName)
                if ui.btn1.currentText() == 'Addons':
                    if option_sitename:
                        siteName = option_sitename
                        list3_item = ui.list3.findItems(siteName, QtCore.Qt.MatchExactly)
                        if list3_item:
                            list3_row = ui.list3.row(list3_item[0])
                            ui.list3.setFocus()
                            ui.list3.setCurrentRow(list3_row)
                            ui.list3.itemDoubleClicked['QListWidgetItem*'].emit(list3_item[0])
                                
                    list3_item = ui.list3.findItems('History', QtCore.Qt.MatchExactly)
                    if list3_item:
                        list3_row = ui.list3.row(list3_item[0])
                        ui.list3.setFocus()
                        ui.list3.setCurrentRow(list3_row)
                        ui.list3.itemDoubleClicked['QListWidgetItem*'].emit(list3_item[0])
                else:
                    ui.setPreOpt(option_val=opt)
            else:
                opt = option_val
                ui.setPreOpt(option_val=opt)
    print(name_index, ui.list1.count())
    if name_index >=0 and name_index < ui.list1.count():
        found_list_item = False
        if ('#LAST@TITLE' in ui.history_dict_obj and site.lower() == 'video'
                and opt.lower() == 'history'):
            list_title = ui.history_dict_obj.get('#LAST@TITLE')[2]
            list1_srch = ui.list1.findItems(list_title, QtCore.Qt.MatchExactly)
            if list1_srch:
                list1_row = ui.list1.row(list1_srch[0])
                ui.list1.setFocus()
                ui.list1.setCurrentRow(list1_row)
                found_list_item = True
        if not found_list_item:
            ui.list1.setCurrentRow(name_index)
            ui.list1.setFocus()
            ui.list1_double_clicked()
    if episode_index >=0 and episode_index < ui.list2.count():
        ui.list2.setCurrentRow(episode_index)
        ui.list2.setFocus()
    print(dock_opt, '--dock-option---')
    if ui.orientation_dock == 'left':
        ui.orient_dock('left')
    else:
        ui.orient_dock('right')
    if dock_opt == 0:
        ui.dockWidget_3.hide()
    else:
        ui.dockWidget_3.show()
    
    print(int(MainWindow.winId()))
    
    try:
        tray = SystemAppIndicator(ui_widget=ui, home=home, window=MainWindow, logr=logger)
        tray.right_menu.setup_globals(screen_width, screen_height)
        tray.show()
        ui.tray_widget = tray
        ui.detach_video_button.clicked.connect(ui.tray_widget.right_menu._detach_video)
    except Exception as e:
        print('System Tray Failed with Exception: {0}'.format(e))
        tray = None
        
    new_tray_widget = FloatWindowWidget(ui, tray, logger)
    ui.new_tray_widget = new_tray_widget
    try:
        m_event = EventFilterFloatWindow()
        new_tray_widget.installEventFilter(m_event)
        print('Event Filter Installed in new_tray_widget')
    except Exception as e:
        print("Error in Tray Widget Event Filter with error message {0}".format(e))
    
    if ui.window_frame == 'false':
        ui._set_window_frame()
    
    try:
        server = MprisServer(ui, home, tray, new_tray_widget)
    except Exception as e:
        print("can't open Mpris plugin, Exception raised: {0}".format(e))
    
    if ui.layout_mode == "Music":
        try:
            t1 = tray.geometry().height()
        except:
            t1 = 65
        MainWindow.setGeometry(
            ui.music_mode_dim[0], ui.music_mode_dim[1], 
            ui.music_mode_dim[2], ui.music_mode_dim[3])
        ui.image_fit_option_val = 3
    else:
        ui.sd_hd.show()
        ui.audio_track.show()
        ui.subtitle_track.show()
        MainWindow.showMaximized()
    
    show_hide_titlelist = arr_setting[0]
    show_hide_playlist = arr_setting[1]
        
    print(arr_setting)
    
    if show_hide_playlist == 1:
        ui.list2.show()
        ui.update_list2()
    elif show_hide_playlist == 0:
        ui.list2.hide()
        ui.goto_epn.hide()
            
    if show_hide_titlelist == 1:
        ui.list1.show()
    elif show_hide_titlelist == 0:
        ui.list1.hide()
        ui.frame.hide()
    if (ui.list1.isHidden() or ui.list2.isHidden()) and ui.view_mode == 'list':
        ui.text.setMaximumWidth(ui.text.maximumWidth()+ui.width_allowed)
        ui.label_new.setMaximumWidth(ui.text.maximumWidth()+ui.width_allowed)
        if ui.layout_mode == 'Music':
            ui.label_new.hide()
    if ui.access_from_outside_network:
        get_ip_thread = GetIpThread(ui, interval=ui.get_ip_interval, ip_file=ui.cloud_ip_file)
        get_ip_thread.start()
        print('--ip--thread--started--')
    #MainWindow.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
    html_default_arr = html_default_arr + ui.addons_option_arr
    MainWindow.show()
    
    if len(sys.argv) >= 2:
        logger.info(sys.argv)
        if '--start-media-server' in sys.argv or '--start-media-server' in sys.argv[1]:
            ui.playerPlaylist('Start Media Server')
            if '--update-video-db' in sys.argv:
                index = ui.btn1.findText('Video')
                if index >= 0:
                    ui.btn1.setCurrentIndex(index)
                    ui.list3.setCurrentRow(3)
            if '--update-music-db' in sys.argv:
                index = ui.btn1.findText('Music')
                if index >= 0:
                    ui.btn1.setCurrentIndex(index)
                    ui.list3.setCurrentRow(0)
            if '--user' in sys.argv:
                index = sys.argv.index('--user')
                if index+1 < len(sys.argv):
                    user_set = sys.argv[index+1]
                    if '--password' in sys.argv:
                        index = sys.argv.index('--password')
                        if index+1 < len(sys.argv):
                            pass_set = sys.argv[index+1]
                            set_user_password(user_set, pass_set)
            if '--generate-ssl' in sys.argv:
                index = sys.argv.index('--generate-ssl')
                if index+1 < len(sys.argv):
                    pass_phrase = sys.argv[index+1]
                    create_ssl_cert(ui, TMPDIR, pass_phrase)
        elif os.path.exists(sys.argv[1]):
            ui.watch_external_video(sys.argv[1])
    
    if old_version <= (2, 0, 0, 0) and old_version > (0, 0, 0, 0):
        logger.info('old version: need to change videodb schema')
        ui.media_data.alter_table_and_update(old_version)
    
    if ui.media_server_autostart:
        ui.start_stop_media_server(True)
    if ui.view_mode in ['thumbnail', 'thumbnail_light']:
        time.sleep(0.01)
        if ui.view_mode == 'thumbnail':
            ui.IconViewEpn(start=True, mode=1)
        else:
            ui.IconViewEpn(start=True, mode=2)
    logger.debug('FullScreen={}'.format(ui.force_fs))
    if ui.force_fs:
        MainWindow.showFullScreen()
    if not os.path.isfile(ui.mpv_input_conf):
        input_conf = os.path.join(RESOURCE_DIR, 'input.conf')
        if os.path.isfile(input_conf):
            shutil.copy(input_conf, ui.mpv_input_conf)
        
    try:
        if os.path.isfile(ui.settings_box.config_file_name) and ui.use_custom_config_file:
            with open(ui.settings_box.config_file_name, 'rb') as config_file:
                config_dict = pickle.load(config_file)
                ui.mpvplayer_string_list = config_dict['str']
    except Exception as err:
        logger.error(err)
        
    ret = app.exec_()
    
    """Starting of Final code which will be Executed just before 
    Application Quits"""
    
    if ui.dockWidget_3.isHidden() or ui.auto_hide_dock:
        dock_opt = 0
    else:
        dock_opt = 1
        
    def_val = ''
    for i in default_arr_setting:
        def_val = def_val + str(i) + ', '
    def_val = def_val[:-1]
    
    music_val = ''
    for i in music_arr_setting:
        music_val = music_val + str(i)+', '
    music_val = music_val[:-1]
    
    if ui.float_window_open:
        if ui.float_window.width() != screen_width and ui.float_window.height() != screen_height:
            ui.float_window_dim = [
                ui.float_window.pos().x(), ui.float_window.pos().y(), 
                ui.float_window.width(), ui.float_window.height()
            ]
    if ui.music_mode_dim_show:
        ui.music_mode_dim = [
            MainWindow.pos().x(), MainWindow.pos().y(), 
            MainWindow.width(), MainWindow.height()
            ]
    if ui.list1.isHidden():
        show_hide_titlelist = 0
    else:
        show_hide_titlelist = 1
    if ui.list2.isHidden():
        show_hide_playlist = 0
    else:
        show_hide_playlist = 1
    icon_poster = iconv_r
    config_path = os.path.join(home, "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write("VERSION_NUMBER="+str(ui.version_number))
            f.write("\nDefaultPlayer="+ui.player_val)
            f.write("\nWindowFrame="+str(ui.window_frame))
            f.write("\nFloatWindow="+str(ui.float_window_dim))
            f.write("\nDockPos="+str(ui.orientation_dock))
            f.write("\nMusicWindowDim="+str(ui.music_mode_dim))
            f.write("\nMusicModeDimShow="+str(ui.music_mode_dim_show))
            if iconv_r_indicator:
                iconv_r = icon_poster = iconv_r_indicator[0]
            if ui.icon_poster_indicator:
                icon_poster = ui.icon_poster_indicator[-1]
            f.write("\nThumbnail_Poster="+str(icon_poster))
            f.write("\nThumbnail_Size="+str(iconv_r))
            f.write("\nView="+str(ui.view_mode))
            f.write("\nQuality="+str(ui.quality_val))
            f.write("\nSite_Index="+str(ui.btn1.currentIndex()))
            f.write("\nAddon_Index="+str(ui.btnAddon.currentIndex()))
            opt_val = opt
            if ui.list3.currentItem():
                opt_index = ui.list3.currentRow()
                opt_txt = ui.list3.currentItem().text()
                if opt_txt.lower() in ['update', 'updateall']:
                    opt_val = 'Available'
                    opt_index = '1'
            else:
                opt_index = '0'
            f.write("\nOption_Val="+str(opt_val))
            f.write("\nOption_Index="+str(opt_index))
            f.write("\nOption_SiteName="+str(siteName))
            f.write("\nName_Index="+str(ui.list1.currentRow()))
            f.write("\nEpisode_Index="+str(ui.list2.currentRow()))
            f.write("\nShow_Hide_Cover="+str(show_hide_cover))
            f.write("\nShow_Hide_Playlist="+str(show_hide_playlist))
            f.write("\nShow_Hide_Titlelist="+str(show_hide_titlelist))
            f.write("\nShow_Hide_Player="+str(show_hide_player))
            f.write("\nDock_Option="+str(dock_opt))
            f.write("\nPOSX="+str(MainWindow.pos().x()))
            f.write("\nPOSY="+str(MainWindow.pos().y()))
            f.write("\nWHeight="+str(MainWindow.height()))
            f.write("\nWWidth="+str(MainWindow.width()))
            f.write("\nLayout="+str(ui.layout_mode))
            f.write("\nDefault_Mode="+str(def_val))
            f.write("\nList_Mode_With_Thumbnail="+str(ui.list_with_thumbnail))
            f.write("\nMusic_Mode="+str(music_val))
            f.write("\nVideo_Mode_Index="+str(ui.comboBoxMode.currentIndex()))
            f.write("\nVideo_Aspect="+str(ui.mpvplayer_aspect_cycle))
            f.write("\nUpload_Speed="+str(ui.setuploadspeed))
            f.write("\nForce_FS={0}".format(ui.force_fs))
            f.write("\nSETTINGS_TAB_INDEX={0}".format(ui.settings_tab_index))
            f.write("\nVOLUME_TYPE={0}".format(ui.volume_type))
            f.write("\nVOLUME_VALUE={0}".format(ui.player_volume))
            f.write("\nAPPLY_SUBTITLE_SETTINGS={0}".format(ui.apply_subtitle_settings))
            f.write("\nCLICKED_LABEL_NEW={0}".format(ui.clicked_label_new))
    if ui.wget.processId() > 0 and ui.queue_item:
        if isinstance(ui.queue_item, tuple):
            ui.queue_url_list.insert(0, ui.queue_item)
    if ui.queue_url_list:
        with open(ui.playing_queue_file, 'wb') as pls_file_queue:
            pickle.dump(ui.queue_url_list, pls_file_queue)
    with open(ui.playing_history_file, 'wb') as pls_file:
        if ui.list1.currentItem():
            ui.history_dict_obj.update(
                {
                    '#LAST@TITLE':[
                            ui.cur_row, ui.cur_row, ui.list1.currentItem().text(),
                            '', 1, 'auto', '-1'
                        ]
                }
            )
            ui.history_dict_obj.update({'#GSBCH@DICT':[ui.gsbc_dict]})
            ui.history_dict_obj.update({'#SUBTITLE@DICT':[ui.subtitle_dict]})
        pickle.dump(ui.history_dict_obj, pls_file)
    if ui.mpvplayer_val.processId() > 0:
        ui.mpvplayer_val.kill()
    print(ret, '--Return--')
    del app
    sys.exit(ret)
    
    
if __name__ == "__main__":
    main()
    
