import os
import shutil
from functools import partial
from PyQt5 import QtCore, QtWidgets, QtGui


class MainWindowWidget(QtWidgets.QWidget):

    def __init__(self, app):
        super(MainWindowWidget, self).__init__()
        self.setAcceptDrops(True)
        self.windowTitleChanged.connect(self.title_changed)
        self.app = app
        
    def title_changed(self, title):
        self.setWindowTitle(title)
        if ui.new_tray_widget and ui.float_window:
            if hasattr(ui, "player_val") and ui.player_val == "libmpv":
                ui.float_window.setWindowTitle(title)
                ui.new_tray_widget.title.setText("")
                ui.new_tray_widget.title1.setText("")
                if not ui.new_tray_widget.title1.isHidden():
                    ui.new_tray_widget.title1.hide()
                if ui.view_mode == "thumbnail_light":
                    ui.labelFrame2.setText(title)
        
    def dragEnterEvent(self, event):
        data = event.mimeData()
        if data.hasUrls():
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        if "ui" in globals():
            if hasattr(ui, "screen_size") and hasattr(ui, "gui_signals"):
                rect = self.app.desktop().availableGeometry(self)
                size_tuple = (rect.width(), rect.height())
                if ui.screen_size == size_tuple:
                    ui.logger.debug("same screen dimensions")
                else:
                    ui.logger.debug("screen dimensions changed..so resizing")
                    ui.gui_signals.adjust_mainwindow(size_tuple)
    
    def set_globals(self, uiwidget):
        global ui
        ui = uiwidget
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            url = url.toString()
            ui.logger.debug(url)
            if url.startswith('file:///') or url.startswith('http') or url.startswith('magnet:'):
                if os.name == 'posix':
                    url = url.replace('file://', '', 1)
                else:
                    url = url.replace('file:///', '', 1)
            ext = None
            if '.' in url:
                ext = url.rsplit('.', 1)[-1]
                ext = ext.lower()
            rect = QtCore.QRect(ui.label.x(), ui.label.y(), ui.label.width(), ui.label.height())
            pos = event.pos()
            name = ui.get_parameters_value(n='name')['name']
            if rect.contains(pos):
                poster_drop = True
                out_file = os.path.join(ui.tmp_download_folder, name+'.jpg')
            else:
                poster_drop = False
                out_file = os.path.join(ui.tmp_download_folder, name+'-fanart.jpg')
            if ext and ext in ['jpg', 'jpeg', 'png'] and not url.startswith('http'):
                if os.path.isfile(url):
                    shutil.copy(url, out_file)
                ui.gui_signals.poster_drop(poster_drop, url, name)
            elif url.startswith('http'):
                url = url.replace(' ', '%20')
                ui.vnt.head(url, onfinished=partial(self.process_dropped_url, poster_drop, name))
            else:
                ui.watch_external_video('{}'.format(url), start_now=True)
    
    def process_dropped_url(self, *args):
        result = args[-1]
        url = args[-2]
        poster_drop = args[0]
        nm = args[1]
        if poster_drop:
            out_file = os.path.join(ui.tmp_download_folder, nm+'.jpg')
        else:
            out_file = os.path.join(ui.tmp_download_folder, nm+'-fanart.jpg')
        if result.error is None:
            if (result.content_type in ['image/jpeg', 'image/png', 'image/webp']
                    or url.endswith('.jpg') or url.endswith('.png')):
                ui.vnt.get(url, out=out_file, onfinished=partial(self.download_fanart, poster_drop, nm))
            else:
                ui.gui_signals.poster_drop(poster_drop, url, nm)
        elif url.endswith('.jpg') or url.endswith('.png'):
            ui.vnt.get(url, out=out_file, onfinished=partial(self.download_fanart, poster_drop))
            
    def download_fanart(self, *args):
        result = args[-1]
        url = args[-2]
        poster_drop = args[0]
        nm = args[1]
        if result.error is None:
            ui.gui_signals.poster_drop(poster_drop, result.out_file, nm)
        
    def mouseMoveEvent(self, event):
        pos = event.pos()
        px = pos.x()
        x = self.width()
        dock_w = ui.dockWidget_3.width()
        if ui.orientation_dock == 'right':
            if px <= x and px >= x-6 and ui.auto_hide_dock:
                ui.dockWidget_3.show()
                if ui.player_val != 'mplayer':
                    ui.btn1.setFocus()
                ui.logger.info('show options sidebar')
            elif px <= x-dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden() and ui.player_val != 'mplayer':
                    ui.list1.setFocus()
                elif not ui.list2.isHidden() and ui.player_val != 'mplayer':
                    ui.list2.setFocus()
        else:
            if px >= 0 and px <= 10 and ui.auto_hide_dock:
                ui.dockWidget_3.show()
                if ui.player_val != 'mplayer':
                    ui.btn1.setFocus()
                ui.logger.info('show options sidebar')
            elif px >= dock_w and ui.auto_hide_dock:
                ui.dockWidget_3.hide()
                if not ui.list1.isHidden() and ui.player_val != 'mplayer':
                    ui.list1.setFocus()
                elif not ui.list2.isHidden() and ui.player_val != 'mplayer':
                    ui.list2.setFocus()
        if self.isFullScreen() and ui.mpvplayer_val.processId() > 0:
            ui.logger.info('FullScreen Window but not video')
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
                    site = ui.get_parameters_value(s='site')['site']
                    if site != 'Music' and ui.list2.isHidden() and ui.tab_6.isHidden() and ui.tab_2.isHidden():
                        ui.frame1.hide()



class EventFilterFloatWindow(QtCore.QObject):

    def set_globals(self, uiwidget):
        global ui
        ui = uiwidget
        
    def eventFilter(self, receiver, event):
        if event.type():
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
