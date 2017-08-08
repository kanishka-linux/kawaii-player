"""
Copyright (C) 2017 kanishka-linux kanishka.linux@gmail.com

This file is part of hlspy.

hlspy is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

hlspy is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with hlspy.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from PyQt5 import QtCore, QtNetwork
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtCore import pyqtSignal

class NetManager(QNetworkAccessManager):
    netS = pyqtSignal(str)
    def __init__(
            self, parent=None, url=None, print_request=None, block_request=None, 
            default_block=None, select_request=None, get_link=None):
        super(NetManager, self).__init__()
        self.url = url
        self.print_request = print_request
        if block_request:
            self.block_request = block_request.split(',')
        else:
            self.block_request = []
        self.default_block = default_block
        self.select_request = select_request
        self.get_link = get_link
        
    def createRequest(self, op, request, device = None ):
        global block_list
        try:
            urlLnk = (request.url().toString())
        except UnicodeEncodeError:
            urlLnk = (request.url().path())
        if self.get_link:
            if self.get_link in urlLnk:
                self.netS.emit(urlLnk)
                
        lower_case = urlLnk.lower()
        lst = []
        if self.default_block:
            lst = [
                "doubleclick.net", 'adnxs', r"||youtube-nocookie.com/gen_204?", 
                 r"youtube.com###watch-branded-actions", "imagemapurl", 
                 "b.scorecardresearch.com", "rightstuff.com", "scarywater.net", 
                "popup.js", "banner.htm", "_tribalfusion", 
                "||n4403ad.doubleclick.net^$third-party", 
                ".googlesyndication.com", "graphics.js", "fonts.googleapis.com/css", 
                "s0.2mdn.net", "server.cpmstar.com", "||banzai/banner.$subdocument", 
                "@@||anime-source.com^$document", "/pagead2.", "frugal.gif", 
                "jriver_banner.png", "show_ads.js", 
                '##a[href^="http://billing.frugalusenet.com/"]', 
                "http://jriver.com/video.html", "||animenewsnetwork.com^*.aframe?", 
                "||contextweb.com^$third-party", ".gutter", ".iab", 'revcontent', 
                ".ads", "ads.", ".bebi", "mgid"
            ]
        if self.block_request:
            lst = lst + self.block_request
        block = False
        for l in lst:
            if lower_case.find(l) != -1:
                block = True
                break
        if (self.select_request and self.select_request in urlLnk) or self.print_request:
            print(urlLnk)

        if block:
            return QNetworkAccessManager.createRequest(self, QNetworkAccessManager.GetOperation, QtNetwork.QNetworkRequest(QtCore.QUrl()))
        else:
            return QNetworkAccessManager.createRequest(self, op, request, device)
