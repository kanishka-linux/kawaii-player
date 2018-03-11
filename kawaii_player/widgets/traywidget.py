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
import datetime
from functools import partial
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class QLineProgress(QtWidgets.QProgressBar):
    
    def __init__(self, parent, ui_widget=None):
        super(QLineProgress, self).__init__(parent)
        global ui
        ui = ui_widget
        
    def mouseMoveEvent(self, event): 
        #t = self.minimum() + ((self.maximum()-self.minimum()) * event.x()) / self.width()
        t = ((event.x() - self.x())/self.width())
        t = t*ui.mplayerLength
        if ui.player_val == "mplayer":
            l=str((datetime.timedelta(milliseconds=t)))
        elif ui.player_val == "mpv":
            l=str((datetime.timedelta(seconds=t)))
        else:
            l = str(0)
        if '.' in l:
            l = l.split('.')[0]
        self.setToolTip(l)
        
    def mousePressEvent(self, event):
        old_val = int((self.value()*ui.mplayerLength)/100)
        t = ((event.x() - self.x())/self.width())
        new_val = int(t*ui.mplayerLength)
        if ui.player_val == 'mplayer':
            print(old_val, new_val, int((new_val-old_val)/1000))
        else:
            print(old_val, new_val, int(new_val-old_val))
        if ui.mpvplayer_val.processId() > 0:
            if ui.player_val == "mpv":
                var = bytes('\n'+"seek "+str(new_val)+" absolute"+'\n', 'utf-8')
                ui.mpvplayer_val.write(var)
            elif ui.player_val =="mplayer":
                seek_val = int((new_val-old_val)/1000)
                var = bytes('\n'+"seek "+str(seek_val)+' \n', 'utf-8')
                ui.mpvplayer_val.write(var)

class FloatWindowWidget(QtWidgets.QWidget):

    update_signal = pyqtSignal(str, int)

    def __init__(self, ui_widget=None, tray_widget=None, logr=None):
        QtWidgets.QWidget.__init__(self)
        global tray, ui, logger
        ui = ui_widget
        tray = tray_widget
        if tray is None:
            return None
        logger = logr
        self.update_signal.connect(self.update_progress)
        self.setAcceptDrops(True)
        self.remove_toolbar = True
        self.lay = QtWidgets.QVBoxLayout(self)

        self.hide_video_window = False

        self.title = QtWidgets.QLineEdit(self)
        self.title1 = QtWidgets.QLineEdit(self)

        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title1.setAlignment(QtCore.Qt.AlignCenter)

        self.title.setReadOnly(True)
        self.title1.setReadOnly(True)

        self.progress = QLineProgress(self, ui)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setMouseTracking(True)

        self.f = QtWidgets.QFrame(self)
        self.f.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.f.setFrameShadow(QtWidgets.QFrame.Raised)
        self.horiz = QtWidgets.QHBoxLayout(self.f)

        self.p = QtWidgets.QPushButton(self)
        self.p.setText(ui.player_buttons['play'])
        self.p.clicked.connect(ui.playerPlayPause)

        self.pr = QtWidgets.QPushButton(self)
        self.pr.setText(ui.player_buttons['prev'])
        self.pr.clicked.connect(ui.mpvPrevEpnList)

        self.ne = QtWidgets.QPushButton(self)
        self.ne.setText(ui.player_buttons['next'])
        self.ne.clicked.connect(ui.mpvNextEpnList)

        self.st = QtWidgets.QPushButton(self)
        self.st.setText(ui.player_buttons['stop'])
        self.st.clicked.connect(ui.playerStop)

        self.attach = QtWidgets.QPushButton(self)
        self.attach.setText(ui.player_buttons['attach'])
        self.attach.clicked.connect(tray.right_menu._detach_video)
        self.attach.setToolTip('Attach Video')

        self.qt = QtWidgets.QPushButton(self)
        self.qt.setText(ui.player_buttons['quit'])
        self.qt.clicked.connect(QtWidgets.qApp.quit)
        self.qt.setToolTip('Quit Player')

        self.lock = QtWidgets.QPushButton(self)
        self.lock.setText(ui.player_buttons['unlock'])
        self.lock.clicked.connect(lambda x=0: ui.playerLoopFile(self.lock))

        self.h_mode = QtWidgets.QPushButton(self)
        self.h_mode.setText('--')
        self.h_mode.setToolTip('<html>Turn on/off auto hide behaviour of toolbar. Use ESC key, to show/hide toolbar</html>')
        self.h_mode.clicked.connect(self.lock_toolbar)

        self.cover_mode = QtWidgets.QPushButton(self)
        self.cover_mode.setText(ui.player_buttons['up'])
        self.cover_mode.setToolTip('Cover Entire Frame')
        self.cover_mode.clicked.connect(self.cover_frame)

        self.horiz.insertWidget(0, self.h_mode, 0)
        self.horiz.insertWidget(1, self.cover_mode, 0)
        self.horiz.insertWidget(2, self.pr, 0)
        self.horiz.insertWidget(3, self.ne, 0)
        self.horiz.insertWidget(4, self.p, 0)
        self.horiz.insertWidget(5, self.st, 0)
        self.horiz.insertWidget(6, self.lock, 0)
        self.horiz.insertWidget(7, self.attach, 0)
        self.horiz.insertWidget(8, self.qt, 0)

        self.lay.insertWidget(0, self.f, 0)
        self.lay.addStretch(1)

        self.lay.insertWidget(3, self.title, 0)
        self.lay.insertWidget(4, self.title1, 0)
        self.lay.insertWidget(5, self.progress, 0)

        self.horiz.setSpacing(0)
        self.horiz.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)
        self.lay.setContentsMargins(0, 0, 0, 0)		

        ui.float_window_layout.insertWidget(0, self, 0)
        self.hide()

        self.f.setStyleSheet("""QFrame{font: bold 15px;color:white;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);height:25px;}

        QPushButton{border-radius:0px;max-height:30px;}
        QPushButton::hover{background-color: yellow;color: black;}
        QPushButton:pressed{background-color: violet;}
        """)
        self.title.setStyleSheet("font:bold 10px;color:white;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);height:15px;")
        self.title1.setStyleSheet("font: bold 10px;color:white;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);height:15px;")
        #self.progress.setStyleSheet("font: bold 10px;color:white;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);height:15px;")
        self.progress.setStyleSheet("""QProgressBar{
            font: bold 10px;
            color:white;
            background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 1%) ;
            border-radius: 1px;
            text-align: center;
            height:15px;
            }

            QProgressBar:chunk {
            background-color: rgba(255, 255, 255, 30%);
            width: 5px;
            margin: 0.5px;
            }}""")
            
    def dragEnterEvent(self, event):
        data = event.mimeData()
        if data.hasUrls():
            event.accept()
        else:
            event.ignore()
        
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for i in urls:
            i = i.toString()
            logger.debug(i)
            if i.startswith('file:///'):
                if os.name == 'posix':
                    i = i.replace('file://', '', 1)
                else:
                    i = i.replace('file:///', '', 1)
            ui.watch_external_video('{}'.format(i), start_now=True)
            
    def mouseMoveEvent(self, event):
        if ui.float_timer.isActive():
            ui.float_timer.stop()

    def cover_frame(self):
        cur_label_num = ui.thumbnail_label_number[0]
        if not ui.list_with_thumbnail:
            ui.list2.setMaximumHeight(30)
        else:
            ui.list2.setMaximumHeight(16777215)
        txt = self.cover_mode.text()
        if txt == ui.player_buttons['up']:
            wid_height = (ui.float_window.height())
            ui.new_tray_widget.setMaximumHeight(wid_height)
            ui.new_tray_widget.show()
            self.cover_mode.setText(ui.player_buttons['down'])
            self.cover_mode.setToolTip('Restore Default')
            if (not ui.idw or str(ui.idw) == str(int(ui.tab_5.winId()))
                    or str(ui.idw) == str(int(ui.label.winId()))):
                self.hide_video_window = False
            elif str(ui.idw) == str(int(ui.label_new.winId())):
                ui.label_new.hide()
                self.hide_video_window = True
            else:
                p1 = "ui.label_epn_{0}.hide()".format(cur_label_num)
                exec(p1)
                self.hide_video_window = True
        else:
            wid_height = int(ui.float_window.height()/3)
            ui.new_tray_widget.setMaximumHeight(wid_height)
            ui.new_tray_widget.show()
            self.cover_mode.setText(ui.player_buttons['up'])
            self.cover_mode.setToolTip('Cover Entire Frame')
            if self.hide_video_window:
                if str(ui.idw) == str(int(ui.label_new.winId())):
                    ui.label_new.show()
                else:
                    p1 = "ui.label_epn_{0}.show()".format(cur_label_num)
                    exec(p1)
                self.hide_video_window = False

    def lock_toolbar(self):
        txt = self.h_mode.text()
        if txt == '--':
            self.h_mode.setText('+')
            #self.h_mode.setToolTip('Remove Toolbar')
            self.remove_toolbar = False
            if ui.float_timer.isActive():
                ui.float_timer.stop()
        else:
            self.h_mode.setText('--')
            #self.h_mode.setToolTip('Keep Toolbar')
            self.remove_toolbar = True
            ui.float_timer.start(1000)

    @pyqtSlot(str, int)
    def update_progress(self, var_str, var_int):
        self.progress.setFormat(var_str)
        #print(var_int)
        if ui.player_val == 'mpv' and ui.mplayerLength:
            self.progress.setValue(int((var_int/ui.mplayerLength)*100))
        elif ui.player_val == 'mplayer' and ui.mplayerLength:
            self.progress.setValue(int(((var_int/ui.mplayerLength)*100)))
        else:
            self.progress.setValue(0)


class RightClickMenuIndicator(QtWidgets.QMenu):

    def __init__(self, parent=None, ui_widget=None, window=None, logr=None):
        global ui, MainWindow, logger
        QtWidgets.QMenu.__init__(self, "File", parent)
        ui = ui_widget
        MainWindow = window
        logger = logr
        self.status_playlist = True

        self.initial_width = 100
        self.initial_height = 100

        self.l = QtWidgets.QLabel()
        self.l.setMaximumSize(QtCore.QSize(280, 250))
        self.l.setMinimumSize(QtCore.QSize(280, 250))
        self.l.setText(_fromUtf8(""))
        self.l.setScaledContents(True)
        self.l.setObjectName(_fromUtf8("l_label"))
        self.l.hide()

        self.h_mode = QtWidgets.QAction("&Hide", self)
        self.h_mode.triggered.connect(self._hide_mode)
        self.addAction(self.h_mode)
        self.h_mode.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.m_mode = QtWidgets.QAction("&Music Mode", self)
        self.m_mode.triggered.connect(ui.music_mode_layout)
        self.addAction(self.m_mode)
        self.m_mode.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.v_mode = QtWidgets.QAction("&Video Mode", self)
        self.v_mode.triggered.connect(ui.video_mode_layout)
        self.addAction(self.v_mode)
        self.v_mode.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.d_vid = QtWidgets.QAction("&Detach Video", self)
        self.d_vid.triggered.connect(self._detach_video)
        self.addAction(self.d_vid)
        self.d_vid.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        if ui.window_frame == 'true':
            self.frameless_mode = QtWidgets.QAction("&Remove Window Frame", self)
        else:
            self.frameless_mode = QtWidgets.QAction("&Allow Window Frame", self)
        self.frameless_mode.triggered.connect(self._remove_frame)
        self.addAction(self.frameless_mode)
        self.frameless_mode.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.exitAction = QtWidgets.QAction("&Exit", self)
        self.exitAction.triggered.connect(QtWidgets.qApp.quit)
        self.addAction(self.exitAction)
        self.exitAction.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.title = QtWidgets.QAction("Title", self)
        self.title.triggered.connect(self.info_action_icon)
        self.title.setFont(QtGui.QFont('SansSerif', 10, italic=False))

        self.title1 = QtWidgets.QAction("Title1", self)
        self.title1.triggered.connect(self.info_action_icon)
        self.title1.setFont(QtGui.QFont('SansSerif', 10, italic=False))

    def info_action_icon(self):
        print('clicked empty')

    def _remove_frame(self):
        txt = self.frameless_mode.text()
        m_w = False
        f_w = False
        if not MainWindow.isHidden():
            m_w = True
        if not ui.float_window.isHidden():
            f_w = True

        if txt.lower() == '&remove window frame':
            MainWindow.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
                )
            ui.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint 
                | QtCore.Qt.WindowStaysOnTopHint
                )
            self.frameless_mode.setText('&Allow Window Frame')
            ui.window_frame = 'false'
        else:
            MainWindow.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.WindowTitleHint
                )
            ui.float_window.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.WindowTitleHint 
                | QtCore.Qt.WindowStaysOnTopHint
                )
            self.frameless_mode.setText('&Remove Window Frame')
            ui.window_frame = 'true'

        if m_w:
            MainWindow.show()
        if f_w:
            ui.float_window.show()

    def setup_globals(self, width=None, height=None):
        global screen_width, screen_height
        screen_width = width
        screen_height = height

    def _detach_video(self):
        cur_label_num = ui.thumbnail_label_number[0]
        txt = self.d_vid.text()
        ui.float_window_open = True
        if ui.mpvplayer_val.processId() > 0:
            ui.float_window.setWindowTitle(ui.epn_name_in_list)
        if txt.lower() == '&detach video':
            self.d_vid.setText('&Attach Video')
            if str(ui.idw) == str(int(ui.tab_5.winId())) or not ui.idw:
                ui.float_window_layout.insertWidget(0, ui.tab_5, 0)
                ui.float_window.show()
                ui.tab_5.show()
            elif str(ui.idw) == str(int(ui.label_new.winId())):
                ui.float_window_layout.insertWidget(0, ui.label_new, 0)
                ui.float_window.show()
                ui.label_new.show()
            elif str(ui.idw) == str(int(ui.label.winId())):
                pass
            else:
                row = ui.list2.currentRow()
                if row >= 0:
                    p1 = "ui.gridLayout2.indexOf(ui.label_epn_{0})".format(cur_label_num)
                    index = eval(p1)
                    print(index, '--index--')
                    ui.current_thumbnail_position = ui.gridLayout2.getItemPosition(index)
                    w = 50
                    h = 50
                    p2 = "ui.label_epn_{0}.minimumWidth()".format(str(cur_label_num))
                    self.initial_width = eval(p2)
                    p2 = "ui.label_epn_{0}.minimumHeight()".format(str(cur_label_num))
                    self.initial_height = eval(p2)
                    p2 = "ui.label_epn_"+str(cur_label_num)+".setMinimumSize(QtCore.QSize("+str(1)+", "+str(1)+"))"
                    exec(p2)
                    p2 = "ui.label_epn_"+str(cur_label_num)+".setMaximumSize(QtCore.QSize("+str(screen_width)+", "+str(screen_height)+"))"
                    exec(p2)
                    p1 = "ui.float_window_layout.insertWidget(0, ui.label_epn_{0}, 0)".format(cur_label_num)
                    exec(p1)

                ui.float_window.show()
            ui.new_tray_widget.lay.insertWidget(2, ui.list2, 0)
            MainWindow.hide()
            self.h_mode.setText('&Hide')
            ycord = ui.float_window_dim[1]
            if ycord < 0:
                ycord = 32
            ui.float_window.setGeometry(
                ui.float_window_dim[0], ycord, 
                ui.float_window_dim[2], ui.float_window_dim[3]
                )
            ui.list2.setFlow(QtWidgets.QListWidget.LeftToRight)
            ui.list2.setMaximumWidth(16777215)
            if ui.list2.isHidden():
                ui.list2.show()
                self.status_playlist = False
            else:
                self.status_playlist = True
            #ui.list2.setViewMode(QtWidgets.QListWidget.IconMode)
            #ui.list2.setFlow(QtWidgets.QListWidget.LeftToRight)
            #ui.list2.setMaximumWidth(screen_width)

            if not ui.list_with_thumbnail:
                ui.list2.setMaximumHeight(30)
            if ui.list2.count() > 0:
                r = ui.list2.currentRow()
                if r >= 0:
                    ui.list2.setCurrentRow(0)
                    ui.list2.setCurrentRow(r)
                    try:
                        thumb_path = ui.get_thumbnail_image_path(r, ui.epn_arr_list[r])
                        logger.info("thumbnail path = {0}".format(thumb_path))
                        if os.path.exists(thumb_path):
                            ui.videoImage(thumb_path, thumb_path, thumb_path, '')
                    except Exception as e:
                        logger.info('Error in getting Thumbnail: {0}, --line--17659--'.format(e))
        else:
            self.d_vid.setText('&Detach Video')
            if str(ui.idw) == str(int(ui.tab_5.winId())) or not ui.idw:
                ui.gridLayout.addWidget(ui.tab_5, 0, 1, 1, 1)
            elif str(ui.idw) == str(int(ui.label_new.winId())):
                ui.vertical_layout_new.insertWidget(0, ui.label_new)
                ui.label_new.show()
            elif str(ui.idw) == str(int(ui.label.winId())):
                pass
            else:
                r = ui.current_thumbnail_position[0]
                c = ui.current_thumbnail_position[1]
                cur_label = cur_label_num
                if cur_label >= 0:
                    p6 = "ui.gridLayout2.addWidget(ui.label_epn_"+str(cur_label)+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
                    exec(p6)
                    p1 = "ui.label_epn_{0}.show()".format(cur_label_num)
                    exec(p1)
                    p2 = "ui.label_epn_{0}.setMinimumSize(QtCore.QSize({1}, {2}))".format(
                        str(cur_label_num), str(self.initial_width), str(self.initial_height)
                        )
                    exec(p2)

                if ui.mpvplayer_val.processId() > 0:
                    try:
                        new_cnt = cur_label_num + ui.list2.count()
                        new_new_cnt = ui.cur_row + ui.list2.count()
                        p1 = "ui.label_epn_{0}.setTextColor(QtCore.Qt.green)".format(new_cnt)
                        exec(p1)
                        p1 = "ui.label_epn_{0}.toPlainText()".format(new_new_cnt)
                        txt = eval(p1)
                        try:
                            p1 = "ui.label_epn_{0}.setText('{1}')".format(new_cnt, txt)
                            exec(p1)
                        except Exception as e:
                            print(e, '--line--4597--')
                            try:
                                p1 = 'ui.label_epn_{0}.setText("{1}")'.format(new_cnt, txt)
                                exec(p1)
                            except Exception as e:
                                print(e)
                        p1 = "ui.label_epn_{0}.setAlignment(QtCore.Qt.AlignCenter)".format(new_cnt)
                        exec(p1)
                    except Exception as e:
                        print(e)
                    QtCore.QTimer.singleShot(1000, partial(ui.update_thumbnail_position, context='attach_video'))
                else:
                    QtCore.QTimer.singleShot(1000, ui.update_thumbnail_position)
            if ui.float_window.width() != screen_width and ui.float_window.height() != screen_height:
                ui.float_window_dim = [
                    ui.float_window.pos().x(), ui.float_window.pos().y(), 
                    ui.float_window.width(), ui.float_window.height()
                ]
            ui.float_window.hide()
            if self.status_playlist:
                ui.list2.show()
            else:
                ui.list2.hide()
            self.h_mode.setText('&Hide')
            ui.list2.setFlow(QtWidgets.QListWidget.TopToBottom)
            ui.list2.setMaximumWidth(ui.width_allowed)
            print("list1 width is {0}".format(ui.list1.width()))
            ui.list2.setMaximumHeight(16777215)
            #ui.list2.setMaximumWidth(screen_width)
            ui.verticalLayout_50.insertWidget(0, ui.list2, 0)
            QtWidgets.QApplication.processEvents()
            MainWindow.show()
            if ui.layout_mode == 'Default':
                MainWindow.showMaximized()
                
    def _hide_mode(self):
        txt = self.h_mode.text()
        if not ui.float_window.isHidden():
            ui.float_window.hide()
            self.h_mode.setText('&Show')
        elif self.d_vid.text().lower() == '&attach video':
            ui.float_window.show()
            self.h_mode.setText('&Hide')
        else:
            if txt == '&Hide':
                MainWindow.hide()
                self.h_mode.setText('&Show')
            elif txt == '&Show':
                self.h_mode.setText('&Hide')
                if ui.music_mode_dim_show:
                    MainWindow.showNormal()
                    MainWindow.setGeometry(
                        ui.music_mode_dim[0], ui.music_mode_dim[1], 
                        ui.music_mode_dim[2], ui.music_mode_dim[3]
                        )
                    MainWindow.show()
                else:
                    MainWindow.showMaximized()


class SystemAppIndicator(QtWidgets.QSystemTrayIcon):

    def __init__(self, parent=None, ui_widget=None, home=None, window=None, logr=None):
        global ui, MainWindow, logger
        QtWidgets.QSystemTrayIcon.__init__(self, parent)
        ui = parent
        MainWindow = window
        logger = logr
        icon_img = os.path.join(home, 'src', 'tray.png')
        self.right_menu = RightClickMenuIndicator(ui_widget=ui_widget,
                                                  window=window, logr=logr)
        self.setContextMenu(self.right_menu)

        self.activated.connect(self.onTrayIconActivated)
        self.p = QtGui.QPixmap(24, 24)
        self.p.fill(QtGui.QColor("transparent"))
        painter	= QtGui.QPainter(self.p)
        if os.path.exists(icon_img):
            self.setIcon(QtGui.QIcon(icon_img))
        else:
            self.setIcon(QtGui.QIcon(""))
        self.full_scr = 1
        del painter
    
    def mouseMoveEvent(self, event):
        pos = event.pos()
        print(pos)

    def onTrayIconActivated(self, reason):
        print(reason, '--reason--')
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if not ui.float_window.isHidden():
                ui.float_window.hide()
                self.right_menu.h_mode.setText('&Show')
            elif self.right_menu.d_vid.text().lower() == '&attach video':
                ui.float_window.show()
                self.right_menu.h_mode.setText('&Hide')
            else:
                if MainWindow.isHidden():
                    self.right_menu.h_mode.setText('&Hide')
                    if ui.music_mode_dim_show:
                        MainWindow.showNormal()
                        MainWindow.setGeometry(
                            ui.music_mode_dim[0], ui.music_mode_dim[1], 
                            ui.music_mode_dim[2], ui.music_mode_dim[3])
                        MainWindow.show()
                    else:
                        MainWindow.showMaximized()
                else:
                    MainWindow.hide()
                    self.right_menu.h_mode.setText('&Show')
