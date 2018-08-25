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
import shutil
from PyQt5 import QtWidgets
from player_functions import send_notification, ccurl

try:
    import libtorrent as lt
    from stream import ThreadServer, TorrentThread, get_torrent_info, get_torrent_info_magnet
except Exception as err:
    print(err, '--29--')
    notify_txt = 'python3 bindings for libtorrent are broken\nTorrent Streaming feature will be disabled'
    send_notification(notify_txt)


class Torrent():
    
    def __init__(self, tmp):
        self.tmp_dir = tmp
        
    def getOptions(self):
        criteria = ['Open', 'History', 'LocalStreaming', 'newversion']
        return criteria
        
    def search(self, name):
        m = ['Not Available']
        return m
        
    def getCompleteList(self, opt, ui, progress, tmp_dir, hist_folder):
        m = ['Not Able To Open']
        if opt == 'Open':
            MainWindow = QtWidgets.QWidget()
            item, ok = QtWidgets.QInputDialog.getText(ui, 'Input Dialog', 'Enter Torrent Url or Magnet Link or local torrent file path')
            if ok and item:
                if (item.startswith('http') or (os.path.isfile(item) and item.endswith('.torrent'))):
                    home = hist_folder
                    name1 = os.path.basename(item).replace('.torrent', '')
                    torrent_dest1 = os.path.join(tmp_dir, name1+'.torrent')
                    if not os.path.exists(torrent_dest1):
                        if item.startswith('http'):
                            ccurl(item+'#'+'-o'+'#'+torrent_dest1)
                        else:
                            shutil.copy(item, torrent_dest1)
                    if os.path.exists(torrent_dest1):
                        info = lt.torrent_info(torrent_dest1)
                        name = info.name()
                        torrent_dest = os.path.join(home, name+'.torrent')
                        shutil.copy(torrent_dest1, torrent_dest)
                    m = [name]
                elif item.startswith('magnet:'):
                    
                    torrent_handle, stream_session, info = get_torrent_info_magnet(item, tmp_dir, ui, progress, tmp_dir)
                    torrent_file = lt.create_torrent(info)
                    
                    home = hist_folder
                    name = info.name()
                    torrent_dest = os.path.join(home, name+'.torrent')
                    
                    with open(torrent_dest, "wb") as f:
                        f.write(lt.bencode(torrent_file.generate()))
                        
                    torrent_handle.pause()
                    stream_session.pause()
                    m = [name]
        m.append(1)
        return m
    
    def getEpnList(self, name, opt, depth_list, extra_info, siteName, category):
        summary = ""
        torrent_dest = os.path.join(siteName, name+'.torrent')
        info = lt.torrent_info(torrent_dest)
        file_arr = []
        for f in info.files():
            file_path = f.path
            file_path = os.path.basename(file_path)	
            file_arr.append(file_path)
        
        record_history = True
        return (file_arr, 'Summary Not Available', 'No.jpg', record_history, depth_list)
        
    def getNextPage(self, opt, pgn, genre_num, name):
        m = ['Nothing']
        return m
