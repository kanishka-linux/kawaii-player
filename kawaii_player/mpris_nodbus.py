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

class MprisServer:
    
    def __init__(self, ui, home, tray, new_tray):
        self.ui = ui
        self.home = home
        self.tray = tray
        self.new_tray_widget = new_tray

    def _emitMeta(self, info, site, epnArrList):
        art_url = self.ui.default_background
        artist = 'Kawaii-Player'
        title = 'Kawaii-Player'
        if epnArrList and site in ["Music", "PlayLists"]:
            try:
                queue_list = False
                if self.ui.queue_url_list:
                    t2 = info.split('#')[1]
                    t1 = t2.split('	')
                    queue_list = True
                else:
                    r = self.ui.list2.currentRow()
                    self.ui.logger.info(epnArrList[r])
                    t1 = epnArrList[r].split('	')
                if len(t1) > 2:
                    t = t1[0]
                    art = t1[2]
                else:
                    t = t1[0]
                    art = t
                if 'internet-radio#' in info:
                    self.ui.logger.info('emitMeta: {0}'.format(info))
                    art = info.split('#')[1]
                    t = epnArrList[self.ui.list2.currentRow()].split('	')[0]
                    t = t.replace('#', '')
                    self.ui.logger.info('art:{0}; title:{1}'.format(art, t))
                if (site == 'Music' and self.ui.list3.currentItem()) or (site == 'PlayLists'): 
                    if ((site == 'Music' and self.ui.list3.currentItem().text().lower() == 'playlist') 
                            or (site == 'PlayLists')):
                        artist = art
                        if artist.lower() == 'none':
                            artist = t.replace('#', '')
                            if artist.startswith(self.ui.check_symbol):
                                artist = artist[1:]
                        pls = self.ui.list1.currentItem().text()
                        if not queue_list:
                            pls_entry = self.ui.list2.currentItem().text().replace('#', '')+'.jpg'
                        else:
                            pls_entry = t.replace('#', '')
                        if pls_entry.startswith(self.ui.check_symbol):
                            pls_entry = pls_entry[1:] 
                        img_place = os.path.join(self.home, 'thumbnails', 'PlayLists', pls, pls_entry)
                        self.ui.logger.info('img_place={0}'.format(img_place))
                        title = re.sub('.jpg', '', pls_entry)
                        art_u = img_place
                    elif site == 'Music':
                        title = t
                        artist = art
                        title = title.replace('#', '')
                        artist = artist.replace('#', '')
                        if title.startswith(self.ui.check_symbol):
                            title = title[1:]
                        if artist.startswith(self.ui.check_symbol):
                            artist = artist[1:]
                        art_u = os.path.join(self.home, 'Music', 'Artist', artist, 'poster.jpg')
            except:
                title = "Kawaii-Player"
                artist = "Kawaii-Player"
        else:
            try:
                r = self.ui.list2.currentRow()
                self.ui.logger.info(epnArrList[r])
                t1 = epnArrList[r].split('	')
                title = t1[0]
                if title.startswith(self.ui.check_symbol):
                    title = title[1:]
                artist = self.ui.list1.currentItem().text()
                art_u = os.path.join(self.home, 'thumbnails', artist, title+'.jpg')
                if 'internet-radio#' in info:
                    self.ui.logger.info('emitMeta: {0}'.format(info))
                    artist = info.split('#')[1]
                    title = epnArrList[self.ui.list2.currentRow()].split('	')[0]
                    self.ui.logger.info('artist={0}; title={1}'.format(artist, title))
                title = title.replace('#', '')
            except Exception as e:
                print(e, '--no-dus-error--')
                title = "Kawaii-Player"
                artist = "Kawaii-Player"
        try:
            r = self.ui.list2.currentRow()
            art_u = self.ui.get_thumbnail_image_path(r, epnArrList[r])
            if os.path.exists(art_u):
                art_url = art_u
        except Exception as e:
            print(e, '--no-dbus--error--')

        abs_path_thumb = art_url
        if title == artist:
            if len(title) > 38:
                title = title[:36]+'..'
                artist = '..'+artist[36:]
            else:
                artist = ''
        else:
            if len(title) > 38:
                title = title[:36]+'..'
            if len(artist) > 38:
                artist = artist[:36]+'..'
        self.new_tray_widget.title.setText(title)
        self.new_tray_widget.title1.setText(artist)
