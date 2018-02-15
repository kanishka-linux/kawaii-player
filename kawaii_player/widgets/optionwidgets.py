import os
import datetime
from PyQt5 import QtCore, QtWidgets, QtGui
from player_functions import write_files
from thread_modules import DiscoverServer

class SidebarWidget(QtWidgets.QListWidget):
    """
    Options Sidebar Widget
    """
    def __init__(self, parent, uiwidget, home_dir):
        super(SidebarWidget, self).__init__(parent)
        global ui, home
        ui = uiwidget
        home = home_dir

    def mouseMoveEvent(self, event): 
        self.setFocus()
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_O:
            ui.setPreOpt()
        elif event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if self.currentRow() == 0:
                self.setCurrentRow(self.count()-1)
            else:
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_Right:
            if not ui.list1.isHidden():
                ui.list1.setFocus()
            elif not ui.scrollArea.isHidden():
                ui.scrollArea.setFocus()
            elif not ui.scrollArea1.isHidden():
                ui.scrollArea1.setFocus()
            elif not ui.list_poster.isHidden():
                ui.list_poster.setFocus()
            ui.dockWidget_3.hide()
        elif event.key() == QtCore.Qt.Key_Return:
            ui.newoptions('clicked')
            self.setFocus()
        elif event.key() == QtCore.Qt.Key_Left:
            if not ui.list2.isHidden():
                if ui.list2.currentItem():
                    index = ui.list2.currentRow()
                    ui.list2.setCurrentRow(index)
                ui.list2.setFocus()
            elif not ui.list1.isHidden():
                ui.list1.setFocus()
            elif not ui.scrollArea.isHidden():
                ui.scrollArea.setFocus()
            elif not ui.scrollArea1.isHidden():
                ui.scrollArea1.setFocus()
            elif not ui.list_poster.isHidden():
                ui.list_poster.setFocus()
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()
        elif event.key() == QtCore.Qt.Key_H:
            ui.setPreOpt()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_D):
            site = ui.get_parameters_value(s='site')['site']
            if site.lower() == 'myserver':
                if not ui.discover_thread:
                    ui.discover_thread = DiscoverServer(ui, True)
                    ui.discover_thread.start()
                elif isinstance(ui.discover_thread, DiscoverServer):
                    if ui.discover_thread.isRunning():
                        ui.discover_server = False
                    else:
                        ui.discover_thread = DiscoverServer(ui, True)
                        ui.discover_thread.start()
        elif event.key() == QtCore.Qt.Key_Delete:
            param_dict = ui.get_parameters_value(s='site', b='bookmark')
            site = param_dict['site']
            bookmark = param_dict['bookmark']
            if site == "PlayLists":
                index = self.currentRow()
                item_r = self.item(index)
                if item_r:
                    item = str(self.currentItem().text())
                    if item != "Default":
                        file_pls = os.path.join(home, 'Playlists', item)
                        if os.path.exists(file_pls):
                            os.remove(file_pls)
                        self.takeItem(index)
                        del item_r
                        ui.list2.clear()
            if bookmark:
                index = self.currentRow()
                item_r = self.item(index)
                if item_r:
                    item = str(self.currentItem().text())
                    bookmark_array = [
                        'All', 'Watching', 'Completed', 'Incomplete', 
                        'Later', 'Interesting', 'Music-Videos'
                        ]
                    if item not in bookmark_array:
                        file_pls = os.path.join(home, 'Bookmark', item+'.txt')
                        if os.path.exists(file_pls):
                            os.remove(file_pls)
                        self.takeItem(index)
                        del item_r
                        ui.list1.clear()
                        ui.list2.clear()
        else:
            super(SidebarWidget, self).keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        history = menu.addAction("History")
        anime = menu.addAction("Animes")
        movie = menu.addAction("Movies")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == history:
            ui.setPreOpt()
        elif action == anime:
            category = "Animes"
            ui.set_parameters_value(catg=category)
        elif action == movie:
            category = "Movies"
            ui.set_parameters_value(catg=category)


class FilterTitleList(QtWidgets.QListWidget):
    """
    Filter Titlelist Widget
    """
    def __init__(self, parent, uiwidget, home_dir):
        super(FilterTitleList, self).__init__(parent)
        global ui, home
        ui = uiwidget
        home = home_dir

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                ui.go_page.setFocus()
            else:
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if self.currentRow() == 0:
                ui.go_page.setFocus()
            else:
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_Return:
            ui.search_list4_options()

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        hd = menu.addAction("Hide Search Table")
        sideBar = menu.addAction("Show Sidebar")
        history = menu.addAction("Show History")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == hd:
            self.hide()
        elif action == sideBar:
            if ui.dockWidget_3.isHidden():
                ui.dockWidget_3.show()
                ui.btn1.setFocus()
            else:
                ui.dockWidget_3.hide()
                ui.list1.setFocus()
        elif action == history:
            ui.setPreOpt()


class FilterPlaylist(QtWidgets.QListWidget):
    """
    Filter Playlist Widget
    """
    def __init__(self, parent, uiwidget, home_dir, logr):
        super(FilterPlaylist, self).__init__(parent)
        global ui, home, logger
        ui = uiwidget
        home = home_dir
        logger = logr

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                ui.goto_epn_filter_txt.setFocus()
            else:
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if self.currentRow() == 0:
                ui.goto_epn_filter_txt.setFocus()
            else:
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_Return:
            ui.search_list5_options()
        elif event.key() == QtCore.Qt.Key_Q:
            site = ui.get_parameters_value(s='site')['site']
            if (site == "Music" or site == "Video" or site == "Local" 
                    or site == "PlayLists" or site == "None"):
                file_path = os.path.join(home, 'Playlists', 'Queue')
                if not os.path.exists(file_path):
                    f = open(file_path, 'w')
                    f.close()
                if not ui.queue_url_list:
                    ui.list6.clear()
                indx = self.currentRow()
                item = self.item(indx)
                if item:
                    tmp = str(self.currentItem().text())
                    tmp1 = tmp.split(':')[0]
                    r = int(tmp1)
                    ui.queue_url_list.append(ui.epn_arr_list[r])
                    ui.list6.addItem(ui.epn_arr_list[r].split('	')[0])
                    logger.info(ui.queue_url_list)
                    write_files(file_path, ui.epn_arr_list[r], line_by_line=True)


class QueueListWidget(QtWidgets.QListWidget):
    """
    Queue Widget List
    """
    def __init__(self, parent, uiwidget, home_dir):
        super(QueueListWidget, self).__init__(parent)
        global ui, home
        ui = uiwidget
        home = home_dir

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Down:
            nextr = self.currentRow() + 1
            if nextr == self.count():
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(nextr)
        elif event.key() == QtCore.Qt.Key_Up:
            prev_r = self.currentRow() - 1
            if self.currentRow() == 0:
                self.setCurrentRow(self.count()-1)
            else:
                self.setCurrentRow(prev_r)
        elif event.key() == QtCore.Qt.Key_PageUp:
            r = self.currentRow()
            if r > 0:
                r1 = r - 1
                if not ui.video_local_stream:
                    ui.queue_url_list[r], ui.queue_url_list[r1] = ui.queue_url_list[r1], ui.queue_url_list[r]
                item = self.item(r)
                txt = item.text()
                self.takeItem(r)
                del item
                self.insertItem(r1, txt)
                self.setCurrentRow(r1)
        elif event.key() == QtCore.Qt.Key_PageDown:
            r = self.currentRow()
            if r < self.count()-1 and r >= 0:
                r1 = r + 1
                if not ui.video_local_stream:
                    ui.queue_url_list[r], ui.queue_url_list[r1] = ui.queue_url_list[r1], ui.queue_url_list[r]
                item = self.item(r)
                txt = item.text()
                self.takeItem(r)
                del item
                self.insertItem(r1, txt)
                self.setCurrentRow(r1)
        elif event.key() == QtCore.Qt.Key_Return:
            r = self.currentRow()
            if self.item(r):
                ui.queueList_return_pressed(r)
        elif event.key() == QtCore.Qt.Key_Delete:
            r = self.currentRow()
            if self.item(r):
                item = self.item(r)
                self.takeItem(r)
                del item
                if not ui.video_local_stream:
                    del ui.queue_url_list[r]

class MyToolTip(QtWidgets.QToolTip):
    
    def __init__(self, uiwidget):
        super(MyToolTip).__init__()
        global ui
        ui = uiwidget
        
class MySlider(QtWidgets.QSlider):

    def __init__(self, parent, uiwidget, home_dir):
        super(MySlider, self).__init__(parent)
        global home, ui
        ui = uiwidget
        home = home_dir
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.tooltip = MyToolTip(ui)
        self.parent = parent
        
    def mouseMoveEvent(self, event): 
        t = self.minimum() + ((self.maximum()-self.minimum()) * event.x()) / self.width()
        if ui.player_val == "mplayer":
            l=str((datetime.timedelta(milliseconds=t)))
        elif ui.player_val == "mpv":
            l=str((datetime.timedelta(seconds=t)))
        else:
            l = str(0)
        if '.' in l:
            l = l.split('.')[0]
        #self.setToolTip(l)
        point = QtCore.QPoint(self.parent.x()+event.x(), self.parent.y()+self.parent.height())
        rect = QtCore.QRect(self.parent.x(), self.parent.y(), self.parent.width(), self.parent.height())
        self.tooltip.showText(point, l, self, rect, 1000)
        
    def mousePressEvent(self, event):
        old_val = int(self.value())
        t = ((event.x() - self.x())/self.width())
        t = int(t*ui.mplayerLength)
        new_val = t
        if ui.player_val == 'mplayer':
            print(old_val, new_val, int((new_val-old_val)/1000))
        else:
            print(old_val, new_val, int(new_val-old_val))
        if ui.mpvplayer_val.processId() > 0:
            if ui.player_val == "mpv":
                var = bytes('\n '+"seek "+str(new_val)+" absolute"+' \n', 'utf-8')
                ui.mpvplayer_val.write(var)
            elif ui.player_val =="mplayer":
                seek_val = int((new_val-old_val)/1000)
                var = bytes('\n '+"seek "+str(seek_val)+' \n', 'utf-8')
                ui.mpvplayer_val.write(var)


class QProgressBarCustom(QtWidgets.QProgressBar):
    
    def __init__(self, parent, gui):
        super(QProgressBarCustom, self).__init__(parent)
        self.gui = gui
        
    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            if self.gui.video_local_stream:
                if self.gui.torrent_frame.isHidden():
                    self.gui.torrent_frame.show()
                    self.gui.label_torrent_stop.setToolTip('Stop Torrent')
                    self.gui.label_down_speed.show()
                    self.gui.label_up_speed.show()
                    if self.gui.torrent_download_limit == 0:
                        down_rate = '\u221E' + ' K'
                    else:
                        down_rate = str(int(self.gui.torrent_download_limit/1024))+'K'
                    if self.gui.torrent_upload_limit == 0:
                        up_rate = '\u221E' + ' K'
                    else:
                        up_rate = str(int(self.gui.torrent_upload_limit/1024))+'K'
                    down = '\u2193 RATE: ' +down_rate
                    up = '\u2191 RATE:' +up_rate
                    self.gui.label_down_speed.setPlaceholderText(down)
                    self.gui.label_up_speed.setPlaceholderText(up)
                else:
                    self.gui.torrent_frame.hide()
            else:
                if self.gui.torrent_frame.isHidden():
                    self.gui.torrent_frame.show()
                    self.gui.label_down_speed.hide()
                    self.gui.label_up_speed.hide()
                    self.gui.label_torrent_stop.setToolTip('Stop Current Download')
                else:
                    self.gui.torrent_frame.hide()

class QLineCustom(QtWidgets.QLineEdit):
    
    def __init__(self, parent, ui_widget):
        super(QLineCustom, self).__init__(parent)
        global ui
        ui = ui_widget
        
    def keyPressEvent(self, event):
        if self.objectName() == 'go_page':
            if event.key() == QtCore.Qt.Key_Down:
                ui.list4.show()
                ui.list4.setFocus()
                self.show()
            elif event.key() == QtCore.Qt.Key_Up:
                ui.list4.show()
                ui.list4.setFocus()
                self.show()
            else:
                super(QLineCustom, self).keyPressEvent(event)
        elif self.objectName() == 'label_search':
            if event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Return]:
                if not ui.list_poster.isHidden():
                    ui.list_poster.setFocus()
                elif not ui.scrollArea.isHidden():
                    ui.scrollArea.setFocus()
                elif not ui.scrollArea1.isHidden():
                    ui.scrollArea1.setFocus()
            else:
                super(QLineCustom, self).keyPressEvent(event)


class QLineCustomSearch(QtWidgets.QLineEdit):
    
    def __init__(self, parent, ui_widget):
        super(QLineCustomSearch, self).__init__(parent)
        global ui
        ui = ui_widget
    
    def go_to_target(self):
        if ui.focus_widget == ui.list1:
            ui.list1.setFocus()
            if ui.view_mode == 'thumbnail':
                ui.tab_6.setFocus()
                ui.take_to_thumbnail(mode='title', focus=True)
            elif ui.view_mode == 'thumbnail_light':
                ui.tab_6.setFocus()
                ui.list_poster.setFocus()
        elif ui.focus_widget == ui.list2:
            ui.list2.setFocus()
            if not ui.tab_6.isHidden():
                ui.tab_6.setFocus()
                ui.take_to_thumbnail(mode='epn', focus=True)
        
    def keyPressEvent(self, event):
        print("down")
        if event.key() == QtCore.Qt.Key_Down:
            self.go_to_target()
            self.hide()
        elif event.key() == QtCore.Qt.Key_Up:
            self.hide()
        elif event.key() == QtCore.Qt.Key_Return:
            self.go_to_target()
            self.hide()
        else:
            super(QLineCustomSearch, self).keyPressEvent(event)

class QLineCustomEpn(QtWidgets.QLineEdit):
    
    def __init__(self, parent, ui_widget):
        super(QLineCustomEpn, self).__init__(parent)
        global ui
        ui = ui_widget
        
    def keyPressEvent(self, event):
        
        if (event.type()==QtCore.QEvent.KeyPress) and (event.key() == QtCore.Qt.Key_Down):
            print("Down")
            ui.list5.setFocus()
        elif event.key() == QtCore.Qt.Key_Up:
            ui.list5.setFocus()
        super(QLineCustomEpn, self).keyPressEvent(event)


class QLabelFloat(QtWidgets.QLabel):

    def __init(self, parent=None):
        QLabel.__init__(self, parent)
        
    def set_globals(self, uiwidget, home_dir):
        global ui, home
        ui = uiwidget
        home = home_dir
        
    def mouseMoveEvent(self, event):
        if ui.float_timer.isActive():
            ui.float_timer.stop()
        if ui.new_tray_widget.cover_mode.text() == ui.player_buttons['up']:
            wid_height = int(ui.float_window.height()/3)
        else:
            wid_height = int(ui.float_window.height())
        ui.new_tray_widget.setMaximumHeight(wid_height)
        ui.new_tray_widget.show()
        ui.float_timer.start(1000)
        print('float')
        
    def mouseEnterEvent(self, event):
        print('Enter Float')


class SelectButton(QtWidgets.QComboBox):
    
    def __init__(self, parent, ui_widget):
        super(SelectButton, self).__init__(parent)
        global ui
        ui = ui_widget
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            if not ui.list1.isHidden():
                ui.list1.setFocus()
            elif not ui.scrollArea.isHidden():
                ui.scrollArea.setFocus()
            elif not ui.scrollArea1.isHidden():
                ui.scrollArea1.setFocus()
            elif not ui.list_poster.isHidden():
                ui.list_poster.setFocus()
            if ui.auto_hide_dock:
                ui.dockWidget_3.hide()
        elif event.key() == QtCore.Qt.Key_Left:
            if self.currentText() == 'Addons':
                ui.btnAddon.setFocus()
            else:
                ui.list3.setFocus()
        else:
            super(SelectButton, self).keyPressEvent(event)
