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

import sys
from PyQt5 import QtCore,QtGui,QtNetwork,QtWidgets,QtWebEngineWidgets
from PyQt5 import QtWebEngineCore
from PyQt5.QtNetwork import QNetworkAccessManager

class NetWorkManager(QtWebEngineCore.QWebEngineUrlRequestInterceptor):
	
	def __init__(self,parent):
		super(NetWorkManager, self).__init__(parent)
		
	def interceptRequest(self,info):
		t = info.requestUrl()
		urlLnk = t.url()
		lower_path = urlLnk.lower()
		
		block_list = [
		"doubleclick.net",'adnxs','facebook','.aspx', 
		r"||youtube-nocookie.com/gen_204?", r"youtube.com###watch-branded-actions", 
		"imagemapurl","b.scorecardresearch.com","rightstuff.com",
		"scarywater.net","popup.js","banner.htm","_tribalfusion",
		"||n4403ad.doubleclick.net^$third-party",".googlesyndication.com",
		"graphics.js","fonts.googleapis.com/css","s0.2mdn.net",
		"server.cpmstar.com","||banzai/banner.$subdocument",
		"@@||anime-source.com^$document","/pagead2.","frugal.gif",
		"jriver_banner.png","show_ads.js",'##a[href^="http://billing.frugalusenet.com/"]',
		"http://jriver.com/video.html","||animenewsnetwork.com^*.aframe?",
		"||contextweb.com^$third-party",".gutter",".iab",
		'http://www.animenewsnetwork.com/assets/[^"]*.jpg','revcontent'
		]
		
		block = False
		for l in block_list:
			if l in lower_path:
				block = True
				break
		if block:
			info.block(True)
			
			
		






             
