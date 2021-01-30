import os
import datetime
import time
import hashlib
import shutil
import subprocess
import platform
import locale
from functools import partial
import PIL
from PIL import Image
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import write_files
from thread_modules import DiscoverServer
from mpv_bak import MPV
from threading import Lock

class QBrowserWidget(QtWidgets.QWidget):

    def __init__(self, uiwidget, parent):
        QtWidgets.QWidget.__init__(self, parent)
        global ui
        ui = uiwidget
        self.setMouseTracking(True)
        
    def mouseMoveEvent(self, event):
        self.setFocus()
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        

class QPushButtonExtra(QtWidgets.QPushButton):

    def __init__(self, parent=None):
        super(QPushButtonExtra, self).__init__(parent)
        self.setMouseTracking(True)

    def clicked_connect(self, callbak):
        if platform.system().lower() == "darwin":
            super(QPushButtonExtra, self).pressed.connect(callbak)
        else:
            super(QPushButtonExtra, self).clicked.connect(callbak)

    def clicked_emit(self):
        if platform.system().lower() == "darwin":
            super(QPushButtonExtra, self).pressed.emit()
        else:
            super(QPushButtonExtra, self).clicked.emit()
            
    def mouseMoveEvent(self, event):
        self.setFocus()
        
        
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
        if ui.player_val != 'mplayer' or ui.mpvplayer_val.processId() == 0:
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

class ToolTipWidget(QtWidgets.QWidget):
    
    def __init__(self, uiwidget, parent):
        QtWidgets.QWidget.__init__(self, parent)
        global ui
        ui = uiwidget
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint 
            | QtCore.Qt.WindowStaysOnTopHint
            )
        self.setMouseTracking(True)
        
    def mouseMoveEvent(self, event):
        self.hide()
        
    def mousePressEvent(self, event):
        self.hide()

class QLabelPreview(QtWidgets.QLabel):

    def __init(self, parent=None):
        QLabel.__init__(self, parent)
        self.setMouseTracking(True)
        
    def set_globals(self, uiwidget):
        global ui
        ui = uiwidget
    
    def mouseMoveEvent(self, event):
        ui.slider.tooltip_widget.hide()
        
    def mousePressEvent(self, event):
        ui.slider.tooltip_widget.hide()
        ui.slider.preview_pending[:] = []

class PreviewThread(QtCore.QThread):
    preview_cmd = pyqtSignal(list)
    def __init__(self, slider, gui, func, apply_list):
        QtCore.QThread.__init__(self)
        global ui
        ui = gui
        self.slider = slider
        self.func = func
        self.preview_cmd.connect(preview_slot)
        self.apply_list = apply_list.copy()
        
    def __del__(self):
        self.wait()                        
    
    def run(self):
        if self.func:
            final_point = (self.apply_list[-3], self.apply_list[-2])
            if self.slider.final_point == final_point:
                self.func()
                self.preview_cmd.emit(self.apply_list)

@pyqtSlot(list)
def preview_slot(apply_list):
    global ui
    final_point = (apply_list[-3], apply_list[-2])
    if ui.slider.final_point == final_point:
        ui.slider.preview_generated(*apply_list)
    
class MySlider(QtWidgets.QSlider):

    def __init__(self, parent, uiwidget, home_dir, mw):
        super(MySlider, self).__init__(parent)
        global home, ui, MainWindow
        ui = uiwidget
        home = home_dir
        MainWindow = mw
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        version = QtCore.QT_VERSION_STR
        self.version = tuple([int(i) for i in version.split('.')])
        if self.version >= (5, 9, 0):
            self.tooltip = MyToolTip(ui)
        else:
            self.tooltip = None
        self.parent = parent
        self.preview_process = QtCore.QProcess()
        self.counter = 0
        self.preview_pending = []
        self.lock = False
        self.preview_counter = 0
        self.mousemove = False
        #self.tooltip_widget = ToolTipWidget(ui, parent)
        self.tooltip_widget = QtWidgets.QWidget(MainWindow)
        self.v = QtWidgets.QVBoxLayout(self.tooltip_widget)
        self.v.setContentsMargins(0, 0, 0, 0)
        self.pic = QLabelPreview(self)
        self.pic.set_globals(ui)
        self.pic.setScaledContents(True)
        self.v.insertWidget(0, self.pic)
        self.txt = QtWidgets.QLabel(self)
        self.v.insertWidget(1, self.txt)
        self.txt.setAlignment(QtCore.Qt.AlignCenter)
        self.tooltip_widget.setMouseTracking(True)
        self.tooltip_widget.hide()
        self.txt.setStyleSheet('color:white;background:black;')
        self.tooltip_timer = QtCore.QTimer()
        self.tooltip_timer.timeout.connect(self.update_tooltip)
        self.tooltip_timer.setSingleShot(True)
        self.final_url = None
        self.half_size = int(ui.label.maximumWidth()/2)
        self.upper_limit = self.parent.x() + self.parent.width()
        self.lower_limit = self.parent.x()
        self.file_type = 'video'
        self.enter = False
        self.empty_preview_dir = False
        self.check_dimension_again = False
        self.preview_dir = None
        self.time_format = lambda val: time.strftime('%H:%M:%S', time.gmtime(int(val)))
        self.preview_lock = Lock()
        #self.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        #self.setTickInterval(100)
        self.valueChanged.connect(self.set_value)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpv = MPV(vo="image", ytdl="no", quiet=True, aid="no", sid="no", frames=1, idle=True)
        self.preview_thread_list = []
        self.final_point = (0, 0)
        self.ui = ui
        
    def set_value(self, val):
        self.setSliderPosition(val)
    
    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Right):
            pos = self.cursor().pos()
            self.cursor().setPos(pos.x()+5, pos.y())
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_Left):
            pos = self.cursor().pos()
            self.cursor().setPos(pos.x()-5, pos.y())
        elif event.key() == QtCore.Qt.Key_Right:
            ui.mpv_execute_command('seek 5', ui.cur_row)
        elif event.key() == QtCore.Qt.Key_Left:
            ui.mpv_execute_command('seek -5', ui.cur_row)
        elif event.key() == QtCore.Qt.Key_Return:
            pos = self.cursor().pos()
            t = ((pos.x() - self.x())/self.width())
            t = int(t*ui.mplayerLength)
            ui.mpv_execute_command('seek {} absolute'.format(int(t)), ui.cur_row)
        else:
            super(MySlider, self).keyPressEvent(event)
    
    def leaveEvent(self, event, source=None):
        if self.tooltip_timer.isActive():
            self.tooltip_timer.stop()
        self.preview_pending[:] = []
        self.tooltip_widget.hide()
        if self.tooltip:
            self.tooltip.hideText()
        self.enter = False
        self.check_dimension_again = True
        #self.mpv.terminate()
        if self.preview_dir:
            picn = os.path.join(self.preview_dir, '00000001.jpg')
            if os.path.exists(picn):
                os.remove(picn)
            
    def enterEvent(self, event, source=None):
        self.enter = True
        if self.final_url != ui.final_playing_url:
            self.check_and_set_file_type()
            if (self.file_type == 'video' and ui.mpvplayer_val.processId() > 0
                    and ui.live_preview in ['slow', 'fast'] or ui.player_val == "libmpv"):
                self.create_preview_dir()
        self.mouseMoveEvent(event, source=source)
    
    def create_preview_dir(self):
        file_name_bytes = bytes(ui.final_playing_url, 'utf-8')
        h = hashlib.sha256(file_name_bytes)
        file_digest = h.hexdigest()
        self.preview_dir = os.path.join(ui.preview_download_folder, file_digest)
        if not os.path.exists(self.preview_dir):
            os.makedirs(self.preview_dir)
        ui.logger.debug('\n{}::{}\n'.format(self.preview_dir, ui.final_playing_url))
    
    def check_and_set_file_type(self):
        if ui.final_playing_url.startswith('abs_path=') or ui.final_playing_url.startswith('relative_path='):
            ui.final_playing_url = ui.if_path_is_rel(ui.final_playing_url)
        if ui.final_playing_url.startswith('http'):
            self.file_type = 'network'
        elif '.' in ui.final_playing_url:
            ext = ui.final_playing_url.rsplit('.', 1)[1]
            if ext in ui.music_type_arr:
                self.file_type = 'music'
                self.final_url = ui.final_playing_url
            elif ext in ui.video_type_arr:
                self.file_type = 'video'
            else:
                self.file_type = 'unknown'
        ui.logger.debug('{}::{}'.format(self.file_type, ui.final_playing_url))
        if self.file_type in ['network', 'music', 'unknown']:
            self.final_url = ui.final_playing_url

    def mpv_preview(self, preview_dir, t, scale, newpicn, url, final_point=None, timeout=None):
        self.preview_lock.acquire()
        picn = os.path.join(preview_dir, '00000001.jpg')
        self.mpv.vo_image_outdir = preview_dir
        self.mpv.start = t
        if scale is not None:
            self.mpv.vo_image_jpeg_quality = ui.live_preview_quality
            self.mpv.vf = "scale={}:{}".format(scale[0], scale[1])
        else:
            self.mpv.vo_image_jpeg_quality = 90
            self.mpv.vf = ""
        if (not os.path.exists(newpicn) 
                and (self.ui.live_preview == "fast" 
                or final_point is None or self.final_point == final_point)):
            self.mpv.play(url)
        self.mpv.wait_for_property("idle-active", lambda x : x, timeout=timeout)
        if os.path.exists(picn) and not os.path.exists(newpicn):
            shutil.move(picn, newpicn)
        self.mpv.stop = True
        self.preview_lock.release()
    
    def mouseMoveEvent(self, event, source=None):
        if ui.player_val != 'mplayer' or ui.mpvplayer_val.processId() == 0:
            self.setFocus()
        if self.tooltip_timer.isActive():
            self.tooltip_timer.stop()
        if self.final_url != ui.final_playing_url:
            self.check_and_set_file_type()
            if (self.file_type == 'video' and ui.mpvplayer_val.processId() > 0
                    and ui.live_preview in ['slow', 'fast'] or ui.player_val == "libmpv"):
                self.create_preview_dir()
                
        self.preview_counter += 1
        t = ((event.x() - self.x())/self.width())
        if ui.extra_toolbar_control == 'slave' and ui.mpvplayer_val.processId() == 0:
            t = int(t*self.maximum())
        else:
            t = int(t*ui.mplayerLength)
        #t = self.minimum() + ((self.maximum()-self.minimum()) * event.x()) / self.width()
        if ui.player_val == "mplayer":
            l=str((datetime.timedelta(milliseconds=t)))
        elif ui.player_val in ["mpv", "libmpv"]:
            l=str((datetime.timedelta(seconds=t)))
        else:
            l = str(0)
        if '.' in l:
            l = l.split('.')[0]
        change_aspect = False
        if source is not None:
            source_val = source.widget_name
        else:
            source_val = "none"
        if not os.path.exists(ui.preview_download_folder):
            os.makedirs(ui.preview_download_folder)
        if ui.live_preview in ['fast', 'slow'] and (ui.mpvplayer_val.processId() > 0 or ui.player_val in ["libmpv", "mpv"]) and self.file_type == 'video' and ui.extra_toolbar_control == "master":
            if self.preview_dir is None:
                self.create_preview_dir()
            command = 'mpv --vo=image --vo-image-jpeg-quality={} --no-sub --ytdl=no --quiet -aid=no -sid=no --vo-image-outdir="{}" --start={} --frames=1 "{}"'.format(ui.live_preview_quality, self.preview_dir, int(t), ui.final_playing_url)
            picn = os.path.join(self.preview_dir, '00000001.jpg')
            newpicn = os.path.join(self.preview_dir, "{}.jpg".format(int(t)))
            change_aspect = True
            if ui.player_val in ["libmpv", "mpv"]:
                #if True:
                self.final_point = (event.x(), event.y())
                func = partial(self.mpv_preview, self.preview_dir, t,
                               (ui.label.maximumWidth(), ui.label.maximumHeight()),
                               newpicn, ui.final_playing_url, (event.x(), event.y()), timeout=0.5)
                apply_list = [newpicn, l, False, t, 0, event.x(), event.y(), source_val]
                if ui.live_preview == "fast" and not os.path.exists(newpicn):
                    func()
                    ui.gui_signals.generate_preview(*apply_list.copy())
                else:
                    if not os.path.exists(newpicn):
                        pr_thread = PreviewThread(self, ui, func, apply_list)
                        self.preview_thread_list.append(pr_thread)
                        self.preview_thread_list[len(self.preview_thread_list)-1].start()
                    #self.mpv_preview(self.preview_dir, t,
                    #                (ui.label.maximumWidth(), ui.label.maximumHeight()),
                    #                newpicn, ui.final_playing_url)
                    #self.preview_generated(newpicn, l, False, t, 0, event.x(), event.y())
                if os.path.exists(newpicn):
                    ui.gui_signals.generate_preview(newpicn, l, False, t, 0, event.x(), event.y(), source_val)
        else:
            if self.tooltip is None:
                self.setToolTip(l)
            else:
                if source_val and source_val == "progressbar":
                    offset = 25
                else:
                    offset = 0
                point = QtCore.QPoint(self.parent.x()+event.x(), self.parent.y()+self.parent.height() - offset)
                rect = QtCore.QRect(self.parent.x(), self.parent.y() - offset , self.parent.width(), self.parent.height())
                self.tooltip.showText(point, l, self, rect, 1000)
        if ui.live_preview in ['fast', 'slow'] and ui.mpvplayer_val.processId() > 0 and self.file_type == 'video' and ui.player_val not in ["mpv", "libmpv"]:
            self.setToolTip('')
            if os.path.isfile(newpicn) and self.final_url == ui.final_playing_url:
                use_existing = True
            else:
                use_existing = False
            if self.preview_process.processId() == 0 and not use_existing:
                self.info_preview(
                    command, picn, l, change_aspect, t, self.preview_counter,
                    event.x(), event.y(), use_existing, lock=False
                )
            else:
                if self.preview_process.processId() > 0 or ui.live_preview == 'slow':
                    self.preview_pending.append(
                        (command, picn, l, change_aspect, t, self.preview_counter,
                         event.x(), event.y(), use_existing)
                    )
                if ui.live_preview == 'fast' and self.preview_process.processId() == 0:
                    if os.path.isfile(newpicn):
                        self.apply_pic(newpicn, event.x(), event.y(), l, resize=True)
                    else:
                        self.apply_pic(picn, event.x(), event.y(), l, resize=True)
                elif ui.live_preview == 'fast' and self.preview_process.processId() > 0:
                    self.apply_pic(picn, event.x(), event.y(), l, resize=True, only_text=True)
                    
                
    def info_preview(self, command, picn, length, change_aspect, tsec, counter, x, y, use_existing=None, lock=None):
        if self.preview_process.processId() != 0:
            self.preview_process.kill()
        if self.preview_process.processId() == 0 and lock is False and not use_existing:
            ui.logger.debug('\npreview_generating - {} - {}\n'.format(length, tsec))
            self.preview_process = QtCore.QProcess()
            self.preview_process.finished.connect(partial(self.preview_generated, picn, length, change_aspect, tsec, counter, x, y))
            QtCore.QTimer.singleShot(1, partial(self.preview_process.start, command))
        elif use_existing:
            newpicn = os.path.join(self.preview_dir, "{}.jpg".format(int(tsec)))
            if ui.live_preview == 'fast':
                self.apply_pic(newpicn, x, y, length)
                ui.logger.debug('\n use existing preview image \n')
            else:
                self.preview_process = QtCore.QProcess()
                command = 'echo "hello"'
                self.preview_process.finished.connect(partial(self.preview_generated, picn, length, change_aspect, tsec, counter, x, y))
                QtCore.QTimer.singleShot(1, partial(self.preview_process.start, command))
            
    def preview_generated(self, picn, length, change_aspect, tsec, counter, x, y, source_val=None):
        #self.tooltip_widget.hide()
        self.preview_counter -= 1
        self.lock = True
        if not self.preview_dir:
            self.create_preview_dir()
        picnew = os.path.join(self.preview_dir, "{}.jpg".format(int(tsec)))
        if os.path.isfile(picn):
            if not os.path.isfile(picnew):
                shutil.copy(picn, picnew)
                picn = picnew
                if change_aspect:
                    ui.image_fit_option(picn, picn, fit_size=6, widget=ui.label)
            else:
                picn = picnew
            txt = '<html><img src="{}">{}<html>'.format(picn, length)
            ui.logger.debug('\n{}::{}\n'.format(txt, tsec))
            point = None
            rect = None
            self.apply_pic(picn, x, y, length, source_val=source_val)
            if self.preview_pending and ui.player_val != "libmpv":
                while self.preview_counter >= 0:
                    self.preview_counter -= 1
                ui.logger.debug('\n{}::{}\n'.format(len(self.preview_pending), self.preview_counter))
                if ui.live_preview == 'slow':
                    args = self.preview_pending[0]
                    del self.preview_pending[0]
                else:
                    args = self.preview_pending.pop()
                    self.preview_pending[:] = []
                ui.logger.debug(args)
                self.lock = False
                self.info_preview(
                    args[0], args[1], args[2], args[3], args[4], args[5],
                    args[6], args[7], args[8], lock=False
                    )
    
    def apply_pic(self, picn, x, y, length, resize=None, only_text=None, source_val=None):
        
        if resize:
            txt = '<html><img src="{0}" width="{2}"><p>{1}</p><html>'.format(picn, length, 100)
        else:
            txt = '<html><img src="{}"><p>{}</p><html>'.format(picn, length)
        if ui.live_preview_style == 'tooltip':
            try:
                if self.final_url != ui.final_playing_url and not resize:
                    self.final_url = ui.final_playing_url
                    img = Image.open(picn)
                    self.half_size = int(img.size[0]/2)
                    self.upper_limit = self.parent.x() + self.parent.width()
                    self.lower_limit = self.parent.x()
                    ui.logger.debug('\n change dimensions \n')
            except Exception as err:
                ui.logger.error(err)
            if self.tooltip is None:
                self.setToolTip('')
                self.setToolTip(txt)
            else:
                if ui.fullscreen_video or ui.force_fs:
                    y_cord = self.parent.y() + self.parent.maximumHeight() - 25
                else:
                    y_cord = self.parent.y() + self.parent.maximumHeight() + 25
                x_cord = self.parent.x() + x
                if x_cord + self.half_size > self.upper_limit:
                    x_cord = self.upper_limit
                elif x_cord - self.half_size < self.lower_limit:
                    x_cord = self.parent.x()
                else:
                    x_cord = x_cord - self.half_size
                if source_val and source_val == "progressbar":
                    offset = 25
                else:
                    offset = 0
                print(offset)
                point = QtCore.QPoint(x_cord, y_cord - offset)
                rect = QtCore.QRect(self.parent.x(), self.parent.y() - offset, self.parent.width(), self.parent.height())
                #print(self.parent.x(), self.parent.y(), self.parent.width(), self.parent.height())
                if (not self.preview_pending or resize or ui.live_preview == 'slow') and self.enter:
                    self.tooltip.showText(point, txt, self, rect, 3000)
        elif ui.live_preview_style == 'widget':
            try:
                if self.check_dimension_again and not resize:
                    img = Image.open(picn)
                    self.pic.setMaximumSize(QtCore.QSize(img.size[0], img.size[1]))
                    self.pic.setMinimumSize(QtCore.QSize(img.size[0], img.size[1]))
                    self.tooltip_widget.setMaximumSize(QtCore.QSize(img.size[0], img.size[1]+30))
                    self.tooltip_widget.setMinimumSize(QtCore.QSize(img.size[0], img.size[1]+30))
                    self.txt.setMaximumSize(QtCore.QSize(img.size[0], 30))
                    self.txt.setMinimumSize(QtCore.QSize(img.size[0], 30))
                    self.half_size = int(self.tooltip_widget.width()/2)
                    self.upper_limit = self.parent.x() + self.parent.width()
                    self.lower_limit = self.parent.x()
                    ui.logger.debug('\nchange dimensions\n')
                    self.check_dimension_again = False
                if self.final_url != ui.final_playing_url:
                    img = Image.open(picn)
                    self.pic.setMaximumSize(QtCore.QSize(img.size[0], img.size[1]))
                    self.pic.setMinimumSize(QtCore.QSize(img.size[0], img.size[1]))
                    self.tooltip_widget.setMaximumSize(QtCore.QSize(img.size[0], img.size[1]+30))
                    self.tooltip_widget.setMinimumSize(QtCore.QSize(img.size[0], img.size[1]+30))
                    self.txt.setMaximumSize(QtCore.QSize(img.size[0], 30))
                    self.txt.setMinimumSize(QtCore.QSize(img.size[0], 30))
                    self.final_url = ui.final_playing_url
                    self.half_size = int(self.tooltip_widget.width()/2)
                    self.upper_limit = self.parent.x() + self.parent.width()
                    self.lower_limit = self.parent.x()
                    ui.logger.debug('\nchange dimensions\n')
                    self.check_dimension_again = True
            except Exception as err:
                ui.logger.error(err)
            if os.path.isfile(picn):
                if not only_text:
                    self.pic.setPixmap(QtGui.QPixmap(picn, "1"))
                x_cord = self.parent.x()+x
                if x_cord + self.half_size > self.upper_limit:
                    x_cord = self.upper_limit - self.tooltip_widget.width()
                elif x_cord - self.half_size < self.lower_limit:
                    x_cord = self.parent.x()
                else:
                    x_cord = x_cord - self.half_size
                y_cord = self.parent.y() - self.tooltip_widget.height() + ui.player_opt.height()
                if (not self.preview_pending or resize or ui.live_preview == 'slow') and self.enter:
                    self.tooltip_widget.setGeometry(x_cord, y_cord, 128, 128)
                    self.tooltip_widget.show()
                    self.txt.setText(length)
                
    def update_tooltip(self):
        self.tooltip_widget.hide()
        
    def mousePressEvent(self, event, source=None):
        self.preview_counter = 0
        old_val = int(self.value())
        t = ((event.x() - self.x())/self.width())
        if ui.extra_toolbar_control == 'slave' and ui.mpvplayer_val.processId() == 0:            
            seek_per = round((t * 100), 2)
            ui.client_seek_val = seek_per
            ui.settings_box.playerseekabs.clicked.emit()
            t = int(t*self.maximum())
        else:
            t = int(t*ui.mplayerLength)
        new_val = t
        if ui.player_val == 'mplayer':
            print(old_val, new_val, int((new_val-old_val)/1000))
        else:
            print(old_val, new_val, int(new_val-old_val))
        if ui.mpvplayer_val.processId() > 0 or ui.player_val in ["libmpv", "libvlc"]:
            if ui.player_val == "mpv":
                var = bytes('\n '+"seek "+str(new_val)+" absolute"+' \n', 'utf-8')
                ui.mpvplayer_val.write(var)
            elif ui.player_val == "libmpv":
                try:
                    ui.tab_5.mpv.command("seek", new_val, "absolute")
                except Exception as err:
                    print(err)
            elif ui.player_val == "libvlc":
                ui.vlc_mediaplayer.set_time(new_val * 1000)
            elif ui.player_val =="mplayer":
                seek_val = int((new_val-old_val)/1000)
                var = bytes('\n '+"seek "+str(seek_val)+' \n', 'utf-8')
                ui.mpvplayer_val.write(var)


class VolumeSlider(QtWidgets.QSlider):

    def __init__(self, parent, uiwidget, mainwidget):
        super(VolumeSlider, self).__init__(parent)
        global ui, MainWindow
        MainWindow = mainwidget
        ui = uiwidget
        self.parent = parent
        self.setOrientation(QtCore.Qt.Horizontal)
        self.setRange(0, 100)
        self.setPageStep(2)
        self.setSingleStep(2)
        self.setMouseTracking(True)
        self.valueChanged.connect(self.adjust_volume)
        self.pressed = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.release = False
    """
    def mouseMoveEvent(self, event):
        if ui.frame1.isHidden():
            ui.frame1.show()
        pos = int((event.x()/self.width())*100)
    
    def mousePressEvent(self, event):
        self.pressed = True
        self.release = False
        pos = int((event.x()/self.width())*100)
        while not self.release:
            print(pos, self.value())
            if pos > self.value():
                self.setValue(self.value() + 1)
            else:
                self.setValue(self.value() - 1)
            if self.value() >= 100 or self.value() <=0:
                break
            if pos == self.value():
                break
    
    def mouseReleaseEvent(self, event):
        self.pressed = True
        self.release = True
    
    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left]:
            self.pressed = False
            if event.key() == QtCore.Qt.Key_Right:
                self.setValue(self.value() + 1)
            else:
                self.setValue(self.value() - 1)
            ui.seek_to_vol_val(self.value(), action='dragged')
            ui.player_volume = str(self.value())
    """
    def adjust_volume(self, val):
        self.parent.volume_text.setPlaceholderText('{}'.format(val))
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            data_dict = {'param':'volume', 'volume':str(val)}
            ui.settings_box.slave_commands(data=data_dict)
        else:
            ui.player_volume = str(val)
            if ui.mpvplayer_val.processId() > 0 or ui.player_val in ["libmpv", "libvlc"]:
                ui.seek_to_vol_val(val, action='pressed')
                ui.logger.debug(val)
                
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

class QProgressBarFrame(QtWidgets.QProgressBar):
    
    def __init__(self, parent, gui):
        super(QProgressBarFrame, self).__init__(parent)
        self.gui = gui
        self.widget_name = "progressbar"
        #self.setToolTip(True)
        
    def mouseMoveEvent(self, ev):
        self.gui.slider.mouseMoveEvent(ev, source=self)

    def mousePressEvent(self, ev):
        self.gui.slider.mousePressEvent(ev, source=self)

    def leaveEvent(self, ev):
        self.gui.slider.leaveEvent(ev, source=self)

    def enterEvent(self, ev):
        self.gui.slider.enterEvent(ev, source=self)

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
            if ui.view_mode == 'thumbnail':
                ui.list1.setFocus()
                ui.tab_6.setFocus()
                ui.take_to_thumbnail(mode='title', focus=True)
            elif ui.view_mode == 'thumbnail_light':
                ui.tab_6.setFocus()
                ui.list_poster.setFocus()
        elif ui.focus_widget == ui.list2:
            if ui.view_mode == 'thumbnail_light':
                ui.tab_6.setFocus()
                ui.list_poster.setFocus()
            else:
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

class SmallLabel(QtWidgets.QLabel):

    def __init(self, parent):
        super(SmallLabel, self).__init__(parent)
    
    def set_param(self, parent):
        self.parent = parent
        
    def mousePressEvent(self, event):
        label_txt = self.text().lower()
        widget = eval('self.parent.{}_slider'.format(label_txt))
        widget.setValue(0)

class GSBCSlider(QtWidgets.QSlider):

    def __init__(self, parent, uiwidget, name):
        super(GSBCSlider, self).__init__(parent)
        global ui
        self.parent = parent
        ui = uiwidget
        self.setObjectName(name)
        self.setOrientation(QtCore.Qt.Horizontal)
        if name == 'zoom':
            self.setRange(-2000, 2000)
            self.setSingleStep(10)
            self.setPageStep(10)
        elif name == 'speed':
            self.setRange(-100, 900)
            self.setSingleStep(10)
            self.setPageStep(10)
        else:
            self.setRange(-100, 100)
            self.setSingleStep(1)
            self.setPageStep(1)
        #self.setTickInterval(5)
        self.setValue(0)
        self.setMouseTracking(True)
        self.valueChanged.connect(self.adjust_gsbc_values)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        #self.setTickPosition(QtWidgets.QSlider.TicksAbove)
        
    def adjust_gsbc_values(self, val):
        name = self.objectName()
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            data_dict = {'param':'gsbc', name:str(val)}
            ui.settings_box.slave_commands(data=data_dict)
            if name == 'zoom':
                label_value = eval('self.parent.{}_value'.format(name))
                zoom_val = 0.001* val
                label_value.setPlaceholderText(str(zoom_val))
            elif name == 'speed':
                label_value = eval('self.parent.{}_value'.format(name))
                speed_val = 1 + 0.01* val
                label_value.setPlaceholderText(str(speed_val))
            else:
                label_value = eval('self.parent.{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
        else:
            cmd = None
            if name == 'zoom':
                label_value = eval('self.parent.{}_value'.format(name))
                zoom_val = 0.001* val
                label_value.setPlaceholderText(str(zoom_val))
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    cmd = '\n set video-zoom {} \n'.format(zoom_val)
                else:
                    cmd = '\n set_property panscan {} \n'.format(zoom_val)
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'speed':
                label_value = eval('self.parent.{}_value'.format(name))
                speed_val = 1 + 0.01* val
                label_value.setPlaceholderText(str(speed_val))
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    cmd = '\n set speed {} \n'.format(speed_val)
                else:
                    cmd = '\n set_property speed {} \n'.format(speed_val)
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            else:
                label_value = eval('self.parent.{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    cmd = '\n set {} {} \n'.format(name, val)
                else:
                    cmd = '\n set_property {} {} \n'.format(name, val)
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
                ui.gsbc_dict.update({name:val})
            if cmd and ui.player_val == "libmpv":
                ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
        
class SubtitleSlider(QtWidgets.QSlider):

    def __init__(self, parent, uiwidget, name):
        super(SubtitleSlider, self).__init__(parent)
        global ui
        self.parent = parent
        ui = uiwidget
        self.setObjectName(name)
        self.setOrientation(QtCore.Qt.Horizontal)
        if name == 'text':
            self.setRange(0, 100)
            self.setSingleStep(1)
            self.setPageStep(1)
            self.setValue(55)
        elif name == 'border':
            self.setRange(0, 100)
            self.setSingleStep(1)
            self.setPageStep(1)
            self.setValue(30)
        elif name == 'shadow':
            self.setRange(0, 100)
            self.setSingleStep(1)
            self.setPageStep(1)
            self.setValue(0)
        elif name == 'blur':
            self.setRange(0, 2000)
            self.setSingleStep(10)
            self.setPageStep(10)
            self.setValue(0)
        elif name == 'subscale':
            self.setRange(0, 1000)
            self.setSingleStep(10)
            self.setPageStep(10)
            self.setValue(100)
        elif name == 'space':
            self.setRange(-1000, 1000)
            self.setSingleStep(10)
            self.setPageStep(10)
            self.setValue(0)
        elif name in ['xmargin', 'ymargin', 'xymargin']:
            self.setRange(0, 100)
            self.setSingleStep(1)
            self.setPageStep(1)
            if name == 'xmargin':
                self.setValue(25)
            elif name == 'ymargin':
                self.setValue(22)
            else:
                self.setValue(0)
        self.setMouseTracking(True)
        self.valueChanged.connect(self.adjust_sub_size)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
    def adjust_sub_size(self, val):
        name = self.objectName()
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            data_dict = {'param':'subtitle', name:str(val)}
            ui.settings_box.slave_commands(data=data_dict)
            if name == 'text':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
            elif name == 'border':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.1
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
            elif name == 'shadow':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.1
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
            elif name == 'blur':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
            elif name == 'subscale':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
            elif name == 'xmargin':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
            elif name == 'ymargin':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
            elif name == 'xymargin':
                val = 100 - val
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
            elif name == 'space':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
        else:
            cmd = None
            if name == 'text':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
                cmd = '\n set sub-font-size {} \n'.format(val)
                ui.subtitle_dict.update({'sub-font-size':str(val)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'border':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.1
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
                cmd = '\n set sub-border-size {} \n'.format(value)
                ui.subtitle_dict.update({'sub-border-size':str(value)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'shadow':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.1
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
                cmd = '\n set sub-shadow-offset {} \n'.format(value)
                ui.subtitle_dict.update({'sub-shadow-offset':str(value)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'blur':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
                cmd = '\n set sub-blur {} \n'.format(value)
                ui.subtitle_dict.update({'sub-blur':str(value)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'subscale':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    cmd = '\n set sub-scale {} \n'.format(value)
                else:
                    cmd = '\n set_property sub_scale {} \n'.format(value)
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
                ui.subtitle_dict.update({'sub-scale':value})
            elif name == 'xmargin':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
                cmd = '\n set sub-margin-x {} \n'.format(val)
                ui.subtitle_dict.update({'sub-margin-x':str(val)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'ymargin':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
                cmd = '\n set sub-margin-y {} \n'.format(val)
                ui.subtitle_dict.update({'sub-margin-y':str(val)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'xymargin':
                val = 100 - val
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                label_value.setPlaceholderText(str(val))
                cmd = '\n set sub-pos {} \n'.format(val)
                ui.subtitle_dict.update({'sub-pos':str(val)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            elif name == 'space':
                label_value = eval('self.parent.subtitle_{}_value'.format(name))
                value = val * 0.01
                value_str = str(value)
                label_value.setPlaceholderText(value_str[:4])
                cmd = '\n set sub-spacing {} \n'.format(value)
                ui.subtitle_dict.update({'sub-spacing':str(value)})
                if ui.mpvplayer_val.processId() > 0:
                    ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
            if ui.player_val == "libmpv" and cmd:
                ui.mpvplayer_val.write(bytes(cmd, 'utf-8'))
                

class QLineCustomFont(QtWidgets.QLineEdit):
    
    def __init__(self, parent, ui_widget):
        super(QLineCustomFont, self).__init__(parent)
        global ui
        ui = ui_widget
        self.setMouseTracking(True)
        
    def mouseMoveEvent(self, event):
        if ui.tab_5.arrow_timer.isActive():
            ui.tab_5.arrow_timer.stop()
        self.setFocus()
        
class ExtraToolBar(QtWidgets.QFrame):
    
    def __init__(self, parent, uiwidget):
        super(ExtraToolBar, self).__init__(parent)
        global ui, MainWindow
        ui = uiwidget
        MainWindow = parent
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("frame_extra_toolbar")
        self.super_layout = QtWidgets.QVBoxLayout(self)
        self.super_layout.setContentsMargins(0, 0, 0, 0)
        self.super_layout.setSpacing(0)
        self.tab_frame = QtWidgets.QFrame(self)
        self.tab_frame_layout = QtWidgets.QHBoxLayout(self.tab_frame)
        self.tab_frame_layout.setSpacing(0)
        self.tab_frame_layout.setContentsMargins(5,5,5,5)
        
        self.general_tab_btn = QPushButtonExtra(self.tab_frame)
        self.tab_frame_layout.insertWidget(0, self.general_tab_btn, 0)
        self.general_tab_btn.setText('General')
        self.general_tab_btn.clicked_connect(self.general_tab_show)
        
        self.subtitle_tab_btn = QPushButtonExtra(self.tab_frame)
        self.tab_frame_layout.insertWidget(1, self.subtitle_tab_btn, 0)
        self.subtitle_tab_btn.setText('Subtitle')
        self.subtitle_tab_btn.clicked_connect(self.subtitle_tab_show)
        
        self.master_slave_tab_btn = QPushButtonExtra(self.tab_frame)
        self.tab_frame_layout.insertWidget(2, self.master_slave_tab_btn, 0)
        self.master_slave_tab_btn.setText('Master')
        self.master_slave_tab_btn.clicked_connect(self.toggle_master_slave)
        msg = ('<html>Toggle use of Extra Toolbar between Master and Slave.\
                Only useful in PC-To-PC casting mode.\
                Toggle it to Slave, in order to use controls available in\
                Extra Toolbar to control Slave Computer from Master. </html>')
        self.master_slave_tab_btn.setToolTip(msg)
        
        self.child_frame = QtWidgets.QFrame(self)
        self.subtitle_frame = QtWidgets.QFrame(self)
        self.super_layout.insertWidget(0, self.tab_frame, 0)
        self.super_layout.insertWidget(1, self.child_frame, 0)
        self.super_layout.insertWidget(2, self.subtitle_frame, 0)
        self.subtitle_frame.hide()
        self.sub_layout = QtWidgets.QVBoxLayout(self.subtitle_frame)
        
        self.layout = QtWidgets.QVBoxLayout(self.child_frame)
        self.layout.setObjectName("extra_toolbar_layout")
        self.playlist_hide = False
        self.hide()
        
        self.gsbc_layout = QtWidgets.QGridLayout(self)
        self.gsbc_layout.setObjectName('gsbc_layout')
        self.layout.insertLayout(1, self.gsbc_layout)
        self.brightness_slider = GSBCSlider(self, uiwidget, 'brightness')
        self.contrast_slider = GSBCSlider(self, uiwidget, 'contrast')
        self.saturation_slider = GSBCSlider(self, uiwidget, 'saturation')
        self.gamma_slider = GSBCSlider(self, uiwidget, 'gamma')
        self.hue_slider = GSBCSlider(self, uiwidget, 'hue')
        self.zoom_slider = GSBCSlider(self, uiwidget, 'zoom')
        self.speed_slider = GSBCSlider(self, uiwidget, 'speed')
        
        self.brightness_label = SmallLabel(self)
        self.brightness_label.setText('Brightness')
        self.brightness_value = QtWidgets.QLineEdit(self)
        
        self.contrast_label = SmallLabel(self)
        self.contrast_label.setText('Contrast')
        self.contrast_value = QtWidgets.QLineEdit(self)
        
        self.saturation_label = SmallLabel(self)
        self.saturation_label.setText('Saturation')
        self.saturation_value = QtWidgets.QLineEdit(self)
        
        self.gamma_label = SmallLabel(self)
        self.gamma_label.setText('Gamma')
        self.gamma_value = QtWidgets.QLineEdit(self)
        
        self.hue_label = SmallLabel(self)
        self.hue_label.setText('Hue')
        self.hue_value = QtWidgets.QLineEdit(self)
        
        self.zoom_label = SmallLabel(self)
        self.zoom_label.setText('Zoom')
        self.zoom_value = QtWidgets.QLineEdit(self)
        
        self.speed_label = SmallLabel(self)
        self.speed_label.setText('Speed')
        self.speed_value = QtWidgets.QLineEdit(self)
        self.speed_value.setPlaceholderText('1.0')
        label_list = [
            self.brightness_label, self.contrast_label, self.saturation_label,
            self.gamma_label, self.hue_label, self.zoom_label, self.speed_label
            ]
        for label in label_list:
            label.set_param(self)
            label.setStyleSheet("""
                text-align:left;background:rgba(0,0,0,0);
                """)
            label.setToolTip('Click on Text To Reset')
        
        slider_list = [
            self.contrast_slider, self.brightness_slider,
            self.gamma_slider, self.saturation_slider, 
            self.hue_slider, self.zoom_slider, self.speed_slider
            ]
        for index, slider in enumerate(slider_list):
            label = eval("self.{}_label".format(slider.objectName()))
            label_value = eval("self.{}_value".format(slider.objectName()))
            label_value.setMaximumWidth(42)
            label_value.setPlaceholderText(str(slider.value()))
            label_value.returnPressed.connect(partial(self.gsbc_entered, label_value, slider))
            self.gsbc_layout.addWidget(label, index, 0, 1, 1)
            self.gsbc_layout.addWidget(slider, index, 1, 1, 3)
            self.gsbc_layout.addWidget(label_value, index, 5, 1, 1)
        
        self.buttons_layout = QtWidgets.QGridLayout(self)
        self.buttons_layout.setObjectName('buttons_layout')
        self.layout.insertLayout(2, self.buttons_layout)
        
        self.btn_aspect_label = QtWidgets.QLabel(self)
        self.btn_aspect_label.setText('Aspect\nRatio')
        self.buttons_layout.addWidget(self.btn_aspect_label, 0, 0, 2, 1)
        
        self.btn_aspect_original = QPushButtonExtra(self)
        self.btn_aspect_original.setText('Original')
        self.btn_aspect_original.clicked_connect(partial(self.change_aspect, 'original', 'btn_aspect_original'))
        self.buttons_layout.addWidget(self.btn_aspect_original, 0, 1, 1, 2)
        
        self.btn_aspect_disable = QPushButtonExtra(self)
        self.btn_aspect_disable.setText('Disable')
        self.btn_aspect_disable.clicked_connect(partial(self.change_aspect, 'disable', 'btn_aspect_disable'))
        self.buttons_layout.addWidget(self.btn_aspect_disable, 0, 3, 1, 1)
        
        self.btn_aspect_4_3 = QPushButtonExtra(self)
        self.btn_aspect_4_3.setText('4:3')
        self.btn_aspect_4_3.clicked_connect(partial(self.change_aspect, '4:3', 'btn_aspect_4_3'))
        self.buttons_layout.addWidget(self.btn_aspect_4_3, 1, 1, 1, 1)
        
        self.btn_aspect_16_9 = QPushButtonExtra(self)
        self.btn_aspect_16_9.setText('16:9')
        self.btn_aspect_16_9.clicked_connect(partial(self.change_aspect, '16:9', 'btn_aspect_16_9'))
        self.buttons_layout.addWidget(self.btn_aspect_16_9, 1, 2, 1, 1)
        
        self.btn_aspect_235 = QPushButtonExtra(self)
        self.btn_aspect_235.setText('2.35:1')
        self.btn_aspect_235.clicked_connect(partial(self.change_aspect, '2.35:1', 'btn_aspect_235'))
        self.buttons_layout.addWidget(self.btn_aspect_235, 1, 3, 1, 1)
        
        self.btn_scr_label = QtWidgets.QLabel(self)
        self.btn_scr_label.setText('Screenshot')
        self.buttons_layout.addWidget(self.btn_scr_label, 2, 0, 1, 1)
        
        self.btn_scr_1 = QPushButtonExtra(self)
        self.btn_scr_1.setText('1')
        self.btn_scr_1.clicked_connect(partial(self.execute_command, 'async screenshot', 'btn_scr_1'))
        self.buttons_layout.addWidget(self.btn_scr_1, 2, 1, 1, 1)
        self.btn_scr_1.setToolTip("Take Screenshot with subtitle")
        
        self.btn_scr_2 = QPushButtonExtra(self)
        self.btn_scr_2.setText('2')
        self.btn_scr_2.clicked_connect(partial(self.execute_command, 'async screenshot video', 'btn_scr_2'))
        self.buttons_layout.addWidget(self.btn_scr_2, 2, 2, 1, 1)
        self.btn_scr_2.setToolTip("Take Screenshot without subtitle")
        
        self.btn_scr_3 = QPushButtonExtra(self)
        self.btn_scr_3.setText('3')
        self.btn_scr_3.clicked_connect(partial(self.execute_command, 'async screenshot window', 'btn_scr_3'))
        self.buttons_layout.addWidget(self.btn_scr_3, 2, 3, 1, 1)
        self.btn_scr_3.setToolTip("Take Screenshot with window")
        """
        self.btn_speed_half = QPushButtonExtra(self)
        self.btn_speed_half.setText('0.5x')
        self.btn_speed_half.clicked_connect(partial(self.adjust_speed, '0.5'))
        self.buttons_layout.addWidget(self.btn_speed_half, 3, 0, 1, 1)
        self.btn_speed_half.setToolTip('Half Speed')
        
        self.btn_speed_reset = QPushButtonExtra(self)
        self.btn_speed_reset.setText('1x')
        self.btn_speed_reset.clicked_connect(partial(self.adjust_speed, '1.0'))
        self.buttons_layout.addWidget(self.btn_speed_reset, 3, 1, 1, 1)
        self.btn_speed_reset.setToolTip('Original Speed')
        
        self.btn_speed_did = QPushButtonExtra(self)
        self.btn_speed_did.setText('1.5x')
        self.btn_speed_did.clicked_connect(partial(self.adjust_speed, '1.5'))
        self.buttons_layout.addWidget(self.btn_speed_did, 3, 2, 1, 1)
        self.btn_speed_did.setToolTip('Multiply speed by 1.5')
        
        self.btn_speed_twice = QPushButtonExtra(self)
        self.btn_speed_twice.setText('2x')
        self.btn_speed_twice.clicked_connect(partial(self.adjust_speed, '2.0'))
        self.buttons_layout.addWidget(self.btn_speed_twice, 3, 3, 1, 1)
        self.btn_speed_twice.setToolTip('Multiply speed by 2')
        """
        self.btn_sub_minus = QPushButtonExtra(self)
        self.btn_sub_minus.setText('Sub-')
        self.btn_sub_minus.clicked_connect(partial(self.execute_command, 'add sub-delay -0.1', 'btn_sub_minus'))
        self.buttons_layout.addWidget(self.btn_sub_minus, 4, 0, 1, 1)
        self.btn_sub_minus.setToolTip('Add Subtitle Delay of -0.1s')
        
        self.btn_sub_plus = QPushButtonExtra(self)
        self.btn_sub_plus.setText('Sub+')
        self.btn_sub_plus.clicked_connect(partial(self.execute_command, 'add sub-delay +0.1', 'btn_sub_plus'))
        self.buttons_layout.addWidget(self.btn_sub_plus, 4, 1, 1, 1)
        self.btn_sub_plus.setToolTip('Add Subtitle Delay of +0.1s')
        
        self.btn_aud_minus = QPushButtonExtra(self)
        self.btn_aud_minus.setText('A-')
        self.btn_aud_minus.clicked_connect(partial(self.execute_command, 'add audio-delay -0.1', 'btn_aud_minus'))
        self.buttons_layout.addWidget(self.btn_aud_minus, 4, 2, 1, 1)
        self.btn_aud_minus.setToolTip('Add Audio Delay of -0.1s')
        
        self.btn_aud_plus = QPushButtonExtra(self)
        self.btn_aud_plus.setText('A+')
        self.btn_aud_plus.clicked_connect(partial(self.execute_command, 'add audio-delay +0.1', 'btn_aud_plus'))
        self.buttons_layout.addWidget(self.btn_aud_plus, 4, 3, 1, 1)
        self.btn_aud_plus.setToolTip('Add Audio Delay of +0.1s')
        
        self.btn_chapter_minus = QPushButtonExtra(self)
        self.btn_chapter_minus.setText('Chapter-')
        self.btn_chapter_minus.clicked_connect(partial(self.add_chapter, '-', 'btn_chapter_minus'))
        self.buttons_layout.addWidget(self.btn_chapter_minus, 5, 0, 1, 2)
        
        self.btn_chapter_plus = QPushButtonExtra(self)
        self.btn_chapter_plus.setText('Chapter+')
        self.btn_chapter_plus.clicked_connect(partial(self.add_chapter, '+', 'btn_chapter_plus'))
        self.buttons_layout.addWidget(self.btn_chapter_plus, 5, 2, 1, 2)
        
        self.btn_show_stat = QPushButtonExtra(self)
        self.btn_show_stat.setText('Stats')
        self.btn_show_stat.setToolTip('<html>Show Some Statistics on Video. Applicable only for mpv v0.28+</html>')
        self.btn_show_stat.clicked_connect(
            partial(self.execute_command, 'script-binding stats/display-stats-toggle', 'btn_show_stat')
            )
        self.buttons_layout.addWidget(self.btn_show_stat, 6, 0, 1, 1)
        
        self.btn_fs_window = QPushButtonExtra(self)
        self.btn_fs_window.setText('FS')
        self.btn_fs_window.setToolTip('Toggle Application Fullscreen')
        #self.btn_fs_window.clicked_connect(ui.fullscreenToggle)
        self.btn_fs_window.clicked_connect(partial(self.execute_command, 'TAFS', 'btn_fs_window'))
        self.buttons_layout.addWidget(self.btn_fs_window, 6, 1, 1, 1)
        
        self.btn_fs_video = QPushButtonExtra(self)
        self.btn_fs_video.setText('F')
        self.btn_fs_video.setToolTip('Toggle Video Fullscreen')
        #self.btn_fs_window.clicked_connect(ui.fullscreenToggle)
        self.btn_fs_video.clicked_connect(partial(self.execute_command, 'TVFS', 'btn_fs_video'))
        self.buttons_layout.addWidget(self.btn_fs_video, 6, 2, 1, 1)
        
        self.btn_external_sub = QPushButtonExtra(self)
        self.btn_external_sub.setText('ES')
        self.btn_external_sub.setToolTip('Load External Subtitle')
        self.btn_external_sub.clicked_connect(partial(self.execute_command, 'external-subtitle', 'btn_external_sub'))
        self.buttons_layout.addWidget(self.btn_external_sub, 6, 3, 1, 1)
        
        self.volume_layout = QtWidgets.QGridLayout(self)
        self.volume_layout.setObjectName('volume_layout')
        self.layout.insertLayout(3, self.volume_layout)
        
        self.scale_label = QtWidgets.QLabel(self)
        self.scale_label.setText('Sub Scale')
        self.volume_layout.addWidget(self.scale_label, 0, 0, 1, 1)
        self.subscale_slider = SubtitleSlider(self, uiwidget, 'subscale')
        self.subscale_slider.setObjectName("subscale")
        self.volume_layout.addWidget(self.subscale_slider, 0, 1, 1, 3)
        self.subtitle_subscale_value = QtWidgets.QLineEdit(self)
        self.subtitle_subscale_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_subscale_value, self.subscale_slider)
            )
        self.volume_layout.addWidget(self.subtitle_subscale_value, 0, 5, 1, 1)
        self.subtitle_subscale_value.setMaximumWidth(32)
        self.subtitle_subscale_value.setPlaceholderText('1.0')
        self.scale_label.setToolTip('<html>Scale factor for subtitle. Default 1.0.\
        This affects ASS subtitles as well, and may lead to incorrect subtitle rendering.\
        Use with care, or use Text size from Subtitle Section instead.</html>')
        
        self.volume_label = QtWidgets.QLabel(self)
        self.volume_label.setText('Volume')
        self.volume_layout.addWidget(self.volume_label, 1, 0, 1, 1)
        self.slider_volume = VolumeSlider(self, uiwidget, MainWindow)
        self.slider_volume.setObjectName("slider_volume")
        self.volume_layout.addWidget(self.slider_volume, 1, 1, 1, 3)
        self.volume_text = QtWidgets.QLineEdit(self)
        self.volume_text.returnPressed.connect(self.volume_entered)
        self.volume_layout.addWidget(self.volume_text, 1, 5, 1, 1)
        self.volume_text.setMaximumWidth(32)
        
        self.speed_value.setPlaceholderText('1.0')
        self.speed_value.setToolTip('Default Original Speed 1.0')
        
        self.generate_subtitle_frame()
        self.subtitle_box_opened = False
    
    def toggle_master_slave(self):
        txt = self.master_slave_tab_btn.text()
        if txt.lower() == 'master':
            ui.web_control = "slave"
            self.master_slave_tab_btn.setText('Slave')
            ui.extra_toolbar_control = 'slave'
            if not ui.settings_box.tabs_present:
                ui.gui_signals.box_settings('hide')
        else:
            self.master_slave_tab_btn.setText('Master')
            ui.extra_toolbar_control = 'master'
            ui.web_control = "master"
    
    def generate_subtitle_frame(self):
        try:
            self.font_families = [i for i in QtGui.QFontDatabase().families()]
        except Exception as err:
            ui.logger.error(err)
            self.font_families = [ui.global_font]
        self.sub_grid = QtWidgets.QGridLayout(self)
        self.sub_layout.insertLayout(0, self.sub_grid)
        self.completer = QtWidgets.QCompleter(self.font_families)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.font_label = QtWidgets.QLabel(self)
        self.font_label.setText('Font')
        self.font_label.setToolTip('<html>Set Subtitle Font. Start typing\
         in text box to see available fonts starting with an entered letter.</html>')
        self.sub_grid.addWidget(self.font_label, 0, 0, 1, 1)
        self.font_value = QLineCustomFont(self, ui)
        self.font_value.setCompleter(self.completer)
        self.sub_grid.addWidget(self.font_value, 0, 1, 1, 3)
        self.font_value.setPlaceholderText(ui.global_font)
        self.font_value.returnPressed.connect(partial(self.change_sub_font, self.font_value, 'font_value'))
        self.font_value.textChanged['QString'].connect(self.font_value_changed)
        
        self.font_color_label = QtWidgets.QLabel(self)
        self.font_color_label.setText('Text Color')
        self.font_color_label.setToolTip('<html>Set Subtitle Text Color</html>')
        self.font_color_label.setWordWrap(True)
        self.sub_grid.addWidget(self.font_color_label, 1, 0, 1, 1)
        self.font_color_value = QPushButtonExtra(self)
        self.font_color_value.clicked_connect(
            partial(self.choose_color, self.font_color_value, 'text', 'font_color_value')
            )
        self.sub_grid.addWidget(self.font_color_value, 1, 1, 1, 3)
        
        self.border_color_label = QtWidgets.QLabel(self)
        self.border_color_label.setText('Border')
        self.border_color_label.setToolTip('<html>Set Subtitle Border Color</html>')
        self.border_color_label.setWordWrap(True)
        self.sub_grid.addWidget(self.border_color_label, 2, 0, 1, 1)
        self.border_color_value = QPushButtonExtra(self)
        self.border_color_value.clicked_connect(
            partial(self.choose_color, self.border_color_value, 'border', 'border_color_value')
            )
        self.sub_grid.addWidget(self.border_color_value, 2, 1, 1, 3)
        
        self.shadow_color_label = QtWidgets.QLabel(self)
        self.shadow_color_label.setText('Shadow')
        self.shadow_color_label.setToolTip('<html>Set Subtitle Shadow Color</html>')
        self.shadow_color_label.setWordWrap(True)
        self.sub_grid.addWidget(self.shadow_color_label, 3, 0, 1, 1)
        self.shadow_color_value = QPushButtonExtra(self)
        self.shadow_color_value.clicked_connect(
            partial(self.choose_color, self.shadow_color_value, 'shadow', 'shadow_color_value')
            )
        self.sub_grid.addWidget(self.shadow_color_value, 3, 1, 1, 3)
        
        self.checkbox_bold = QtWidgets.QCheckBox("Bold")
        self.checkbox_bold.stateChanged.connect(
            partial(self.checkbox_options, self.checkbox_bold, 'checkbox_bold')
            )
        self.sub_grid.addWidget(self.checkbox_bold, 4, 0, 1, 1)
        
        self.checkbox_italic = QtWidgets.QCheckBox("Italic")
        self.checkbox_italic.stateChanged.connect(
            partial(self.checkbox_options, self.checkbox_italic, 'checkbox_italic')
            )
        self.sub_grid.addWidget(self.checkbox_italic, 4, 1, 1, 1)
        
        self.checkbox_gray = QtWidgets.QCheckBox("GrayScale")
        self.checkbox_gray.stateChanged.connect(
            partial(self.checkbox_options, self.checkbox_gray, 'checkbox_gray')
            )
        self.sub_grid.addWidget(self.checkbox_gray, 4, 2, 1, 2)
        self.checkbox_gray.setToolTip('Useful only for yellow DVD/Vobsubs')
        
        self.subtitle_text_label = QtWidgets.QLabel(self)
        self.subtitle_text_label.setText('Text Size')
        self.subtitle_text_label.setToolTip('<html>Set Subtitle Text Size. Default, 55</html>')
        self.subtitle_text_label.setWordWrap(True)
        self.sub_grid.addWidget(self.subtitle_text_label, 5, 0, 1, 1)
        self.subtitle_text_slider = SubtitleSlider(self, ui, 'text')
        self.sub_grid.addWidget(self.subtitle_text_slider, 5, 1, 1, 2)
        self.subtitle_text_value = QtWidgets.QLineEdit(self)
        self.subtitle_text_value.setPlaceholderText('55')
        self.sub_grid.addWidget(self.subtitle_text_value, 5, 3, 1, 1)
        self.subtitle_text_value.setMaximumWidth(42)
        self.subtitle_text_value.setToolTip('Default, 55')
        self.subtitle_text_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_text_value, self.subtitle_text_slider)
            )
        
        self.subtitle_border_label = QtWidgets.QLabel(self)
        self.subtitle_border_label.setText('Border')
        self.subtitle_border_label.setToolTip('<html>Set Subtitle Border Size. Default, 3</html>')
        self.subtitle_border_label.setWordWrap(True)
        self.sub_grid.addWidget(self.subtitle_border_label, 6, 0, 1, 1)
        self.subtitle_border_slider = SubtitleSlider(self, ui, 'border')
        self.sub_grid.addWidget(self.subtitle_border_slider, 6, 1, 1, 2)
        self.subtitle_border_value = QtWidgets.QLineEdit(self)
        self.subtitle_border_value.setPlaceholderText('3')
        self.sub_grid.addWidget(self.subtitle_border_value, 6, 3, 1, 1)
        self.subtitle_border_value.setMaximumWidth(42)
        self.subtitle_border_value.setToolTip('Default, 3')
        self.subtitle_border_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_border_value, self.subtitle_border_slider)
            )
        
        self.subtitle_shadow_label = QtWidgets.QLabel(self)
        self.subtitle_shadow_label.setText('Shadow')
        self.subtitle_shadow_label.setToolTip('<html>Set Subtitle Shadow Size. Default, 0</html>')
        self.subtitle_shadow_label.setWordWrap(True)
        self.sub_grid.addWidget(self.subtitle_shadow_label, 7, 0, 1, 1)
        self.subtitle_shadow_slider = SubtitleSlider(self, ui, 'shadow')
        self.sub_grid.addWidget(self.subtitle_shadow_slider, 7, 1, 1, 2)
        self.subtitle_shadow_value = QtWidgets.QLineEdit(self)
        self.subtitle_shadow_value.setPlaceholderText('0')
        self.sub_grid.addWidget(self.subtitle_shadow_value, 7, 3, 1, 1)
        self.subtitle_shadow_value.setMaximumWidth(42)
        self.subtitle_shadow_value.setToolTip('Default, 0')
        self.subtitle_shadow_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_shadow_value, self.subtitle_shadow_slider)
            )
        
        self.subtitle_space_label = QtWidgets.QLabel(self)
        self.subtitle_space_label.setText('Spacing')
        self.subtitle_space_label.setToolTip('<html>Set Spacing</html>')
        self.sub_grid.addWidget(self.subtitle_space_label, 8, 0, 1, 1)
        self.subtitle_space_slider = SubtitleSlider(self, ui, 'space')
        self.sub_grid.addWidget(self.subtitle_space_slider, 8, 1, 1, 2)
        self.subtitle_space_value = QtWidgets.QLineEdit(self)
        self.subtitle_space_value.setPlaceholderText('0')
        self.sub_grid.addWidget(self.subtitle_space_value, 8, 3, 1, 1)
        self.subtitle_space_value.setMaximumWidth(42)
        self.subtitle_space_value.setToolTip('Default, 0')
        self.subtitle_space_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_space_value, self.subtitle_space_slider)
            )
        
        self.subtitle_blur_label = QtWidgets.QLabel(self)
        self.subtitle_blur_label.setText('Blur')
        self.subtitle_blur_label.setToolTip('<html>Set Gaussian Blur Factor. Default, 0</html>')
        self.subtitle_blur_label.setWordWrap(True)
        self.sub_grid.addWidget(self.subtitle_blur_label, 9, 0, 1, 1)
        self.subtitle_blur_slider = SubtitleSlider(self, ui, 'blur')
        self.sub_grid.addWidget(self.subtitle_blur_slider, 9, 1, 1, 2)
        self.subtitle_blur_value = QtWidgets.QLineEdit(self)
        self.subtitle_blur_value.setPlaceholderText('0')
        self.sub_grid.addWidget(self.subtitle_blur_value, 9, 3, 1, 1)
        self.subtitle_blur_value.setMaximumWidth(42)
        self.subtitle_blur_value.setToolTip('Default, 0')
        self.subtitle_blur_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_blur_value, self.subtitle_blur_slider)
            )
        
        self.subtitle_xmargin_label = QtWidgets.QLabel(self)
        self.subtitle_xmargin_label.setText('X-Margin')
        self.sub_grid.addWidget(self.subtitle_xmargin_label, 10, 0, 1, 1)
        self.subtitle_xmargin_slider = SubtitleSlider(self, ui, 'xmargin')
        self.sub_grid.addWidget(self.subtitle_xmargin_slider, 10, 1, 1, 2)
        self.subtitle_xmargin_value = QtWidgets.QLineEdit(self)
        self.subtitle_xmargin_value.setPlaceholderText('25')
        self.sub_grid.addWidget(self.subtitle_xmargin_value, 10, 3, 1, 1)
        self.subtitle_xmargin_value.setMaximumWidth(42)
        self.subtitle_xmargin_value.setToolTip('Default, 25')
        self.subtitle_xmargin_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_xmargin_value, self.subtitle_xmargin_slider)
            )
        #self.subtitle_xmargin_value.hide()
        
        self.subtitle_ymargin_label = QtWidgets.QLabel(self)
        self.subtitle_ymargin_label.setText('Y-Margin')
        self.sub_grid.addWidget(self.subtitle_ymargin_label, 11, 0, 1, 1)
        self.subtitle_ymargin_slider = SubtitleSlider(self, ui, 'ymargin')
        self.sub_grid.addWidget(self.subtitle_ymargin_slider, 11, 1, 1, 2)
        self.subtitle_ymargin_value = QtWidgets.QLineEdit(self)
        self.subtitle_ymargin_value.setPlaceholderText('22')
        self.sub_grid.addWidget(self.subtitle_ymargin_value, 11, 3, 1, 1)
        self.subtitle_ymargin_value.setMaximumWidth(42)
        self.subtitle_ymargin_value.setToolTip('Default, 22')
        self.subtitle_ymargin_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_ymargin_value, self.subtitle_ymargin_slider)
            )
        #self.subtitle_ymargin_value.hide()
        
        self.subtitle_xymargin_label = QtWidgets.QLabel(self)
        self.subtitle_xymargin_label.setText('Vertical')
        self.subtitle_xymargin_label.setToolTip('<html>Move Subtitle Vertically</html>')
        self.sub_grid.addWidget(self.subtitle_xymargin_label, 12, 0, 1, 1)
        self.subtitle_xymargin_slider = SubtitleSlider(self, ui, 'xymargin')
        self.sub_grid.addWidget(self.subtitle_xymargin_slider, 12, 1, 1, 2)
        self.subtitle_xymargin_value = QtWidgets.QLineEdit(self)
        self.subtitle_xymargin_value.setPlaceholderText('100')
        self.sub_grid.addWidget(self.subtitle_xymargin_value, 12, 3, 1, 1)
        self.subtitle_xymargin_value.setMaximumWidth(42)
        self.subtitle_xymargin_value.setToolTip('Default, 100')
        self.subtitle_xymargin_value.returnPressed.connect(
            partial(self.gsbc_entered, self.subtitle_xymargin_value, self.subtitle_xymargin_slider)
            )
        
        self.subtitle_align_label = QtWidgets.QLabel(self)
        self.subtitle_align_label.setText('Alignment')
        self.sub_grid.addWidget(self.subtitle_align_label, 13, 0, 1, 1)
        self.subtitle_horiz_align = QtWidgets.QComboBox(self)
        self.sub_grid.addWidget(self.subtitle_horiz_align, 13, 1, 1, 1)
        for  i in ['Center', 'Left', 'Right']:
            self.subtitle_horiz_align.addItem(i)
        self.subtitle_horiz_align.currentIndexChanged['int'].connect(
            partial(self.change_alignment, self.subtitle_horiz_align, 'x', 'subtitle_horiz_align')
            )
        
        self.subtitle_vertical_align = QtWidgets.QComboBox(self)
        self.sub_grid.addWidget(self.subtitle_vertical_align, 13, 2, 1, 1)
        for  i in ['Bottom', 'Middle', 'Top']:
            self.subtitle_vertical_align.addItem(i)
        self.subtitle_vertical_align.currentIndexChanged['int'].connect(
            partial(self.change_alignment, self.subtitle_vertical_align, 'y', 'subtitle_vertical_align')
            )
        """
        self.spinbox_space = QtWidgets.QDoubleSpinBox(self)
        self.sub_grid.addWidget(self.spinbox_space, 12, 3, 1, 1)
        self.spinbox_space.setRange(-50.0, 50.0)
        self.spinbox_space.setValue(0)
        self.spinbox_space.setSingleStep(0.1)
        self.spinbox_space.valueChanged.connect(partial(self.spinbox_changed, self.spinbox_space, 'space'))
        self.spinbox_space.setMaximumWidth(42)
        self.spinbox_space.setDecimals(1)
        
        self.spinbox_scale_label = QtWidgets.QLabel(self)
        self.spinbox_scale_label.setText('Scale')
        self.sub_grid.addWidget(self.spinbox_scale_label, 13, 0, 1, 1)
        self.spinbox_scale = QtWidgets.QDoubleSpinBox(self)
        self.sub_grid.addWidget(self.spinbox_scale, 13, 1, 1, 1)
        self.spinbox_scale.setRange(0.00, 10.00)
        self.spinbox_scale.setValue(1.00)
        self.spinbox_scale.setSingleStep(0.1)
        self.spinbox_scale.setToolTip('<html>Scale factor for subtitle. Default 1.0.\
        This affects ASS subtitles as well, and may lead to incorrect subtitle rendering.\
        Use with care, or use Text size from above instead.</html>')
        self.spinbox_scale.valueChanged.connect(partial(self.spinbox_changed, self.spinbox_scale, 'scale'))
        self.spinbox_scale.hide()
        self.spinbox_scale_label.hide()
        """
        
        self.ass_override_label = QtWidgets.QLabel(self)
        self.ass_override_label.setText('Sub ASS Override')
        self.ass_override_label.setWordWrap(True)
        self.sub_grid.addWidget(self.ass_override_label, 14, 0, 1, 2)
        self.ass_override_label.setToolTip('Apply Above Style to ASS files.')
        self.ass_override_value = QtWidgets.QComboBox(self)
        for i in ['Yes', 'No', 'Force', 'Scale', 'Strip']:
            self.ass_override_value.addItem(i)
        self.ass_override_value.currentIndexChanged['int'].connect(self.ass_override_function)
        self.ass_override_value.setCurrentIndex(0)
        self.sub_grid.addWidget(self.ass_override_value, 14, 2, 1, 1)
        self.ass_override_value.setToolTip('Default, Yes')
        
        self.checkbox_dont = QtWidgets.QCheckBox("Don't Apply Above Settings")
        self.checkbox_dont.stateChanged.connect(
            partial(self.checkbox_options, self.checkbox_dont, 'checkbox_dont')
            )
        self.sub_grid.addWidget(self.checkbox_dont, 15, 0, 1, 3)
        self.checkbox_dont.setToolTip('<html>Do not apply above custom settings</html>')
        
        self.subtitle_widgets = {
            'sub-ass-override': self.ass_override_value,
            'sub-font': self.font_value,
            'sub-color': self.font_color_value,
            'sub-border-color': self.border_color_value,
            'sub-shadow-color': self.shadow_color_value,
            'sub-bold': self.checkbox_bold,
            'sub-italic': self.checkbox_italic,
            'sub-gray': self.checkbox_gray,
            'sub-font-size': self.subtitle_text_slider,
            'sub-border-size': self.subtitle_border_slider,
            'sub-shadow-offset': self.subtitle_shadow_slider,
            'sub-blur': self.subtitle_blur_slider,
            'sub-margin-x': self.subtitle_xmargin_slider,
            'sub-margin-y': self.subtitle_ymargin_slider,
            'sub-pos': self.subtitle_xymargin_slider,
            'sub-align-x': self.subtitle_horiz_align,
            'sub-align-y': self.subtitle_vertical_align,
            'sub-spacing': self.subtitle_space_slider
        }
    
    def change_alignment(self, widget, val, widget_name=None):
        txt = widget.currentText().lower()
        if txt == 'middle':
            txt = 'center'
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            self.execute_command('change_align', {widget_name:txt})
        else:
            cmd = None
            if val == 'x':
                cmd = 'set sub-align-x "{}"'.format(txt)
                ui.subtitle_dict.update({'sub-align-x':txt})
            elif val == 'y':
                cmd = 'set sub-align-y "{}"'.format(txt)
                ui.subtitle_dict.update({'sub-align-y':txt})
            if cmd:
                self.execute_command(cmd)
            
    def spinbox_changed(self, widget, val):
        flval = widget.value()
        if val == 'scale':
            self.execute_command('set sub-scale {}'.format(flval))
            ui.subtitle_dict.update({'sub-scale':flval})
        elif val == 'space':
            self.execute_command('set sub-spacing {}'.format(flval))
            
    def font_value_changed(self):
        self.font_value.setFocus()
        
    def ass_override_function(self):
        txt = self.ass_override_value.currentText().lower()
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            self.execute_command('ass_override', {'ass_override_value':txt})
        else:
            ui.subtitle_dict.update({'sub-ass-override':txt})
            self.execute_command('set sub-ass-override {}'.format(txt))
        
    def change_sub_font(self, widget, widget_name):
        txt = widget.text()
        widget.clear()
        widget.setPlaceholderText(txt)
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            self.execute_command('change_font', {widget_name:txt})
        else:
            ui.subtitle_dict.update({'sub-font':txt})
            self.execute_command('set sub-font "{}"'.format(txt))
            
    def checkbox_options(self, widget, widget_name):
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            self.execute_command('checkbox', {widget_name:str(widget.isChecked())})
        else:
            cmd = None
            if widget_name == 'checkbox_bold':
                if widget.isChecked():
                    ui.subtitle_dict.update({'sub-bold':'yes'})
                    cmd = 'set sub-bold yes'
                else:
                    ui.subtitle_dict.update({'sub-bold':'no'})
                    cmd = 'set sub-bold no'
            elif widget_name == 'checkbox_italic':
                if widget.isChecked():
                    ui.subtitle_dict.update({'sub-italic':'yes'})
                    cmd = 'set sub-italic yes'
                else:
                    ui.subtitle_dict.update({'sub-italic':'no'})
                    cmd = 'set sub-italic no'
            elif widget_name == 'checkbox_gray':
                if widget.isChecked():
                    ui.subtitle_dict.update({'sub-gray':'yes'})
                    cmd = 'set sub-gray yes'
                else:
                    ui.subtitle_dict.update({'sub-gray':'no'})
                    cmd = 'set sub-gray no'
            elif widget_name == 'checkbox_dont':
                if widget.isChecked():
                    ui.apply_subtitle_settings = False
                else:
                    ui.apply_subtitle_settings = True
                ui.playerStop(msg='remember quit', restart=True)
            if cmd:
                self.execute_command(cmd)
            
    def general_tab_show(self):
        self.subtitle_frame.hide()
        self.child_frame.show()
    
    def get_default_color(self, widget, name):
        color_name = None
        if name == 'text':
            color_name = ui.subtitle_dict.get('sub-color')
            if not color_name:
                color_name = '#FFFFFF'
        elif name == 'border':
            color_name = ui.subtitle_dict.get('sub-border-color')
            if not color_name:
                color_name = '#000000'
        elif name == 'shadow':
            color_name = ui.subtitle_dict.get('sub-shadow-color')
        if not color_name:
            color_name = '#FFFFFF'
        return color_name
        
    def choose_color(self, widget, name, widget_name):
        default_color = self.get_default_color(widget, name)
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(default_color))
        if color.isValid():
            color_name = color.name().upper()
            widget.setStyleSheet('background:{};'.format(color_name))
            if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
                self.execute_command('choose_color', {widget_name:color_name})
            else:
                cmd = None
                if name == 'text':
                    ui.subtitle_dict.update({'sub-color':color_name})
                    cmd = 'set sub-color "{}"'.format(color_name)
                elif name == 'border':
                    ui.subtitle_dict.update({'sub-border-color':color_name})
                    cmd = 'set sub-border-color "{}"'.format(color_name)
                elif name == 'shadow':
                    ui.subtitle_dict.update({'sub-shadow-color':color_name})
                    cmd = 'set sub-shadow-color "{}"'.format(color_name)
                if cmd:
                    self.execute_command(cmd)
                
    def apply_slave_subtitile_effects(self, widget_name, color_name):
        widget = eval('ui.frame_extra_toolbar.{}'.format(widget_name))
        widget.setStyleSheet('background:{};'.format(color_name))
        cmd = None
        if widget_name == 'font_color_value':
            ui.subtitle_dict.update({'sub-color':color_name})
            cmd = 'set sub-color "{}"'.format(color_name)
        elif widget_name == 'border_color_value':
            ui.subtitle_dict.update({'sub-border-color':color_name})
            cmd = 'set sub-border-color "{}"'.format(color_name)
        elif widget_name == 'shadow_color_value':
            ui.subtitle_dict.update({'sub-shadow-color':color_name})
            cmd = 'set sub-shadow-color "{}"'.format(color_name)
        if cmd:
            self.execute_command(cmd)
        
        
    def subtitle_tab_show(self):
        self.subtitle_frame.setMinimumHeight(self.child_frame.height())
        #self.subtitle_frame.setMaximumHeight(self.child_frame.height())
        self.child_frame.hide()
        self.subtitle_frame.show()
        if not self.subtitle_box_opened:
            self.subtitle_box_opened = True
            self.apply_initial_sub_settings()
        print(self.subtitle_frame.height(), self.child_frame.height())
        if self.subtitle_frame.height() > self.child_frame.height():
            self.child_frame.setMinimumHeight(self.subtitle_frame.height())
            
    def apply_initial_sub_settings(self):
        for property_name in ui.subtitle_dict:
            property_value = ui.subtitle_dict.get(property_name)
            widget = self.subtitle_widgets.get(property_name)
            if widget and property_value:
                if property_name == 'sub-font':
                    widget.clear()
                    widget.setPlaceholderText(property_value)
                elif property_name in ['sub-color', 'sub-border-color', 'sub-shadow-color']:
                    widget.setStyleSheet("background:{};".format(property_value))
                elif property_name in ['sub-bold', 'sub-italic', 'sub-gray']:
                    if property_value == 'yes':
                        widget.setChecked(True)
                    else:
                        widget.setChecked(False)
                elif property_name in ['sub-font-size', 'sub-margin-x', 'sub-margin-y']:
                    if isinstance(property_value, int):
                        widget.setValue(property_value)
                    elif isinstance(property_value, str):
                        if property_value.isnumeric():
                            widget.setValue(int(property_value))
                elif property_name == 'sub-pos':
                    if property_value.isnumeric():
                        widget.setValue(100 - int(property_value))
                elif property_name in ['sub-border-size', 'sub-shadow-offset']:
                    new_val = float(property_value) * 10
                    widget.setValue(new_val)
                elif property_name in ['sub-blur', 'sub-spacing']:
                    new_val = float(property_value) * 100
                    widget.setValue(new_val)
                elif property_name == 'sub-scale':
                    new_val = float(property_value)
                    widget.setValue(new_val)
                elif property_name in ['sub-ass-override', 'sub-align-x', 'sub-align-y']:
                    if property_name == 'sub-align-y' and property_value == 'center':
                        property_value = 'Middle'
                    property_value = property_value.title()
                    index = widget.findText(property_value)
                    widget.setCurrentIndex(index)
                    
    def mouseMoveEvent(self, event):    
        self.setFocus()
        if not self.subtitle_frame.isHidden():
            self.subtitle_frame.setFocus()
        elif not self.child_frame.isHidden():
            self.child_frame.setFocus()
        
    def change_aspect(self, val, widget=None):
        if val == '2.35:1':
            key = '3'
        elif val == 'disable':
            key = '4'
        elif val == '16:9':
            key = '1'
        elif val == '4:3':
            key = '2'
        else:
            key = '0'
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            data_dict = {'param':'click', 'widget':widget}
            ui.settings_box.slave_commands(data=data_dict)
        else:
            ui.tab_5.change_aspect_ratio(key=key)
    
    def execute_command(self, msg, widget=None):
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            if msg == 'external-subtitle':
                ui.list2.send_subtitle_method()
            elif isinstance(widget, dict):
                data_dict = {'param':'click'}
                for key, val in widget.items():
                    data_dict.update({key:val})
                ui.settings_box.slave_commands(data=data_dict)
            else:
                data_dict = {'param':'click', 'widget':widget}
                ui.settings_box.slave_commands(data=data_dict)
        else:
            if msg == 'external-subtitle':
                ui.tab_5.load_external_sub()
            elif msg == 'TAFS':
                ui.fullscreenToggle()
            elif msg == 'TVFS':
                if ui.mpvplayer_val.processId() > 0 or ui.player_val == "libmpv":
                    if ui.player_val == "libmpv":
                        if platform.system().lower() == "darwin":
                            ui.tab_5.mpv.command("set", "pause", "yes")
                        MainWindow.showMaximized()
                        ui.force_fs = False
                        if platform.system().lower() == "darwin":
                            ui.tab_5.fs_timer.start(2000)
                        else:
                            ui.tab_5.fs_timer.start(500)
                    else:
                        ui.tab_5.toggle_fullscreen_mode()
                    if ui.tab_5.arrow_timer.isActive():
                        ui.tab_5.arrow_timer.stop()
                    ui.tab_5.arrow_timer.start(5000)
            elif ui.mpvplayer_val.processId() > 0 or ui.player_val == "libmpv":
                if ui.player_val.lower() == 'mplayer':
                    if 'sub-delay' in msg or 'audio-delay' in msg:
                        msg = msg.replace('add ', '')
                        msg = msg.strip()
                        if 'sub-delay' in msg:
                            msg = msg.replace('sub-delay', 'sub_delay')
                        elif 'audio-delay' in msg:
                            msg = msg.replace('audio-delay', 'audio_delay')
                    elif 'screenshot' in msg:
                        msg = 'screenshot 0'
                bmsg = bytes('\n {} \n'.format(msg), 'utf-8')
                print(bmsg)
                ui.mpvplayer_val.write(bmsg)
                pmsg = None
                if 'sub-delay' in msg:
                    if ui.player_val.lower() in ['mpv', 'libmpv']:
                        pmsg = '\n show-text "Sub delay: ${sub-delay}" \n'
                    else:
                        pmsg = '\n osd_show_property_text "Sub delay: ${sub_delay}" \n'
                elif 'audio-delay' in msg:
                    if ui.player_val.lower() in ['mpv', 'libmpv']:
                        pmsg = '\n show-text "A-V delay: ${audio-delay}" \n'
                    else:
                        pmsg = '\n osd_show_property_text "A-V delay: ${audio_delay}" \n'
                if pmsg:
                    pmsg = bytes(pmsg, 'utf-8')
                    ui.mpvplayer_val.write(pmsg)
                
    def add_chapter(self, val, widget=None):
        if ui.extra_toolbar_control == 'slave' and ui.pc_to_pc_casting == 'master':
            data_dict = {'param':'click', 'widget':widget}
            ui.settings_box.slave_commands(data=data_dict)
        else:
            if val == '-':
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    msg = bytes('\n add chapter -1 \n', 'utf-8')
                else:
                    msg = bytes('\n seek_chapter -1 0 \n', 'utf-8')
            else:
                if ui.player_val.lower() in ['mpv', 'libmpv']:
                    msg = bytes('\n add chapter 1 \n', 'utf-8')
                else:
                    msg = bytes('\n seek_chapter +1 0 \n', 'utf-8')
            ui.mpvplayer_val.write(msg)
            if ui.player_val.lower() in ['mpv', 'libmpv']:
                pmsg = bytes('\n show-text "Chapter: ${chapter}" \n', 'utf-8')
            else:
                pmsg = bytes('\n osd_show_property_text "Chapter: ${chapter}" \n', 'utf-8')
            ui.mpvplayer_val.write(pmsg)
        
    def adjust_speed(self, val):
        msg = None
        if val == '1.0':
            msg = bytes('\n set speed 1.0 \n', 'utf-8')
        else:
            msg = bytes('\n multiply speed {} \n'.format(val), 'utf-8')
        if msg:
            ui.mpvplayer_val.write(msg)
            
    def volume_entered(self):
        txt = self.volume_text.text()
        self.volume_text.clear()
        if txt.isnumeric():
            self.slider_volume.setValue(int(txt))
        
    def gsbc_entered(self, label, slider):
        value = label.text()
        label.clear()
        try:
            if slider.objectName() == 'zoom':
                label.setPlaceholderText(value)
                value = float(value)*100
                slider.setValue(int(value))
            elif slider.objectName() == 'speed':
                label.setPlaceholderText(value)
                value = float(value)*100 - 100
                slider.setValue(int(value))
            elif slider.objectName() in ['border', 'shadow']:
                label.setPlaceholderText(value)
                value = float(value)*10
                slider.setValue(int(value))
            elif slider.objectName() in ['blur', 'space']:
                label.setPlaceholderText(value)
                value = float(value)*100
                slider.setValue(int(value))
            elif slider.objectName() == 'subscale':
                label.setPlaceholderText(value)
                value = float(value)*100
                slider.setValue(int(value))
            elif slider.objectName() == 'xymargin':
                label.setPlaceholderText(value)
                value = 100 - int(value)
                slider.setValue(value)
            else:
                slider.setValue(int(value))
                label.setPlaceholderText(value)
        except Exception as err:
            ui.logger.error(err)
            slider.setValue(0)
            label.setPlaceholderText('0')
