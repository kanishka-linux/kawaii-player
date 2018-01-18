import os
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from player_functions import ccurl

class PlayerWidget(QtWidgets.QWidget):

    def __init__(self, parent, ui=None, logr=None, tmp=None):
        super(PlayerWidget, self).__init__(parent)
        global MainWindow, logger, TMPDIR, screen_width, screen_height
        self.cycle_pause = 0
        self.ui = ui
        MainWindow = parent
        logger = logr
        TMPDIR = tmp
        self.mpvplayer = None
        self.player_val = None
        self.ui.total_seek = 0
        self.dblclk = False
        self.arrow_timer = QtCore.QTimer()
        self.arrow_timer.timeout.connect(self.arrow_hide)
        self.arrow_timer.setSingleShot(True)

        self.mplayer_OsdTimer = QtCore.QTimer()
        self.mplayer_OsdTimer.timeout.connect(self.osd_hide)
        self.mplayer_OsdTimer.setSingleShot(True)

        self.seek_timer = QtCore.QTimer()
        self.seek_timer.timeout.connect(self.seek_mplayer)
        self.seek_timer.setSingleShot(True)
        self.mplayer_aspect_msg = False
        
        param_dict_val = self.ui.get_parameters_value(sw='screen_width',
                                                      sh='screen_height')
        screen_width = param_dict_val['screen_width']
        screen_height = param_dict_val['screen_height']
    
    def set_mpvplayer(self, player=None, mpvplayer=None):
        if mpvplayer:
            self.mpvplayer = mpvplayer
        else:
            self.mpvplayer = self.ui.mpvplayer_val
        if player:
            self.player_val = player
        else:
            self.player_val = self.ui.player_val
        
    def seek_mplayer(self):
        if self.player_val == "mplayer":
            t = bytes('\n'+"seek " + str(self.ui.total_seek)+'\n', 'utf-8')
            self.mpvplayer.write(t)
            self.ui.total_seek = 0

    def osd_hide(self):
        if self.player_val == 'mplayer':
            self.mpvplayer.write(b'\n osd 0 \n')
        else:
            self.mpvplayer.write(b'\n set osd-level 0 \n')

    def arrow_hide(self):
        if self.player_val == "mplayer" or self.player_val == "mpv":
            self.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
            self.setFocus()
        print("arrow hide")

    def frameShowHide(self):
        if MainWindow.isFullScreen() and self.ui.tab_6.isHidden():
            if self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
                self.ui.frame_timer.start(2000)
            else:
                self.ui.frame_timer.stop()
                self.ui.frame_timer.start(2000)
    
    def mouseReleaseEvent(self, event):
        pass
        """
        if event.button() == QtCore.Qt.LeftButton and not self.dblclk:
            if self.mpvplayer.processId() > 0:
                logger.debug('{0}:{1}'.format(event.type(), 'left-click'))
                if self.player_val == 'mplayer':
                    self.mpvplayer.write(b'\n pausing_toggle osd_show_progression \n')
                elif self.player_val == 'mpv':
                    self.mpvplayer.write(b'\n cycle pause \n')
        """
        
    def mouseDoubleClickEvent(self, event):
        if not self.ui.force_fs:
            self.player_fs()
        else:
            wd = self.width()
            ht = self.height()
            if wd == screen_width and ht == screen_height:
                self.player_fs()
            else:
                self.player_fs(mode='fs')
        
    def mouseMoveEvent(self, event):
        self.setFocus()
        pos = event.pos()
        if self.ui.auto_hide_dock and not self.ui.dockWidget_3.isHidden():
            self.ui.dockWidget_3.hide()
        if not self.ui.float_window.isHidden() and self.ui.new_tray_widget.remove_toolbar:
            if self.ui.float_timer.isActive():
                self.ui.float_timer.stop()
            if self.ui.new_tray_widget.cover_mode.text() == self.ui.player_buttons['up']:
                wid_height = int(self.ui.float_window.height()/3)
            else:
                wid_height = int(self.ui.float_window.height())
            self.ui.new_tray_widget.setMaximumHeight(wid_height)
            self.ui.new_tray_widget.show()
            self.ui.float_timer.start(1000)
        if (self.player_val == "mplayer" or self.player_val == "mpv"):
            if self.arrow_timer.isActive():
                self.arrow_timer.stop()
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            self.arrow_timer.start(2000)
        if MainWindow.isFullScreen():
            ht = self.height()
            if pos.y() <= ht and pos.y() > ht - 5 and self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
                self.ui.frame1.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            elif pos.y() <= ht-32 and not self.ui.frame1.isHidden():
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if site != "Music" and self.ui.tab_6.isHidden() and self.ui.list2.isHidden() and self.ui.tab_2.isHidden():
                    self.ui.frame1.hide()
                    self.ui.gridLayout.setSpacing(5)

    def ccurl_head(self, url, rfr_url):
        print("------------ccurlHead------------")
        if rfr_url:
            content = ccurl(url+'#'+'-Ie'+'#'+rfr_url)
        else:
            content = ccurl(url+'#'+'-I')
        return content

    def url_resolve_size(self, url, rfr_url):
        m = []
        content = self.ccurl_head(url, rfr_url)
        n = content.split('\n')
        k = 0
        for i in n:
            i = re.sub('\r', '', i)
            if i and ':' in i:
                p = i.split(': ', 1)
                if p:
                    t = (p[0], p[1])
                else:
                    t = (i, "None")
                m.append(t)
                k = k+1
            else:
                t = (i, '')
                m.append(t)
        d = dict(m)
        print(d)
        result = int(int(d['Content-Length'])/(1024*1024))
        return result

    def set_slider_val(self, val):
        t = self.ui.slider.value()
        t = t+val
        self.ui.slider.setValue(t)
    
    def player_fs(self, mode=None):
        param_dict_val = self.ui.get_parameters_value(idw='idw', sw='screen_width',
                                                      sh='screen_height')
        idw = param_dict_val['idw']
        screen_width = param_dict_val['screen_width']
        screen_height = param_dict_val['screen_height']
        if not idw or idw == str(int(self.winId())):
            if not MainWindow.isHidden():
                param_dict = self.ui.get_parameters_value(
                    wgt='wget', vl='video_local_stream')
                wget = param_dict['wget']
                video_local_stream = param_dict['video_local_stream']
                
                if not MainWindow.isFullScreen() or mode == 'fs':
                    if os.name == 'nt' and self.ui.web_review_browser_started:
                        self.ui.detach_fullscreen = True
                        MainWindow.hide()
                        self.ui.tray_widget.right_menu._detach_video()
                        if not self.ui.float_window.isFullScreen():
                            self.ui.float_window.showFullScreen()
                            self.ui.tab_5.setFocus()
                    else:
                        if not self.ui.tab_6.isHidden():
                            self.ui.fullscreen_mode = 1
                        elif not self.ui.float_window.isHidden():
                            self.ui.fullscreen_mode = 2
                        else: 
                            self.ui.fullscreen_mode = 0
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.superGridLayout.setSpacing(0)
                        self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.text.hide()
                        self.ui.label.hide()
                        self.ui.frame1.hide()
                        self.ui.tab_6.hide()
                        self.ui.goto_epn.hide()
                        #self.ui.btn20.hide()
                        
                        if wget.processId() > 0 or video_local_stream:
                            self.ui.progress.hide()
                            if not self.ui.torrent_frame.isHidden():
                                self.ui.torrent_frame.hide()
                        self.ui.list2.hide()
                        self.ui.list6.hide()
                        self.ui.list1.hide()
                        self.ui.frame.hide()
                        self.ui.dockWidget_3.hide()
                        self.show()
                        self.setFocus()
                        if not self.ui.tab_2.isHidden():
                            self.ui.tab_2.hide()
                        if (self.player_val == "mplayer" or self.player_val == "mpv"):
                            MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
                        MainWindow.showFullScreen()
                else:
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.gridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                    self.ui.list2.show()
                    self.ui.btn20.show()
                    if wget.processId() > 0 or video_local_stream:
                        self.ui.progress.show()
                    self.ui.frame1.show()
                    if self.player_val == "mplayer" or self.player_val == "mpv":
                        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    if not self.ui.force_fs:
                        MainWindow.showNormal()
                        MainWindow.showMaximized()
                    param_dict = self.ui.get_parameters_value(tl='total_till')
                    total_till = param_dict['total_till']
                    if total_till != 0 or self.ui.fullscreen_mode == 1:
                        self.ui.tab_6.show()
                        self.ui.list2.hide()
                        self.ui.goto_epn.hide()
                    if self.ui.btn1.currentText().lower() == 'youtube':
                        self.ui.list2.hide()
                        self.ui.goto_epn.hide()
                        self.ui.tab_2.show()
            else:
                if self.ui.detach_fullscreen:
                    self.ui.detach_fullscreen = False
                    self.ui.tray_widget.right_menu._detach_video()
                    self.ui.tab_5.setFocus()
                else:
                    if not self.ui.float_window.isHidden():
                        if not self.ui.float_window.isFullScreen():
                            self.ui.float_window.showFullScreen()
                        else:
                            self.ui.float_window.showNormal()
        else:
            param_dict = self.ui.get_parameters_value(t='tab_6_size_indicator')
            tab_6_size_indicator = param_dict['tab_6_size_indicator']
            #if tab_6_size_indicator:
            #    tab_6_size_indicator.pop()
            tab_6_size_indicator.append(self.ui.tab_6.width())
            self.ui.set_parameters_value(tab_6=tab_6_size_indicator)
            param_dict = self.ui.get_parameters_value(
                wgt='wget', icn='iconv_r_indicator', i='iconv_r',
                cl='cur_label_num', fl='fullscr')
            wget = param_dict['wget']
            iconv_r_indicator = param_dict['iconv_r_indicator']
            iconv_r = param_dict['iconv_r']
            cur_label_num = param_dict['cur_label_num']
            fullscr = param_dict['fullscr']
            if not MainWindow.isHidden():
                if self.ui.video_mode_index == 5:
                    pass
                else:
                    if iconv_r_indicator:
                        iconv_r = iconv_r_indicator[0]
                    fullscr = 1 - fullscr
                    self.ui.set_parameters_value(iconv=iconv_r, fullsc=fullscr)
                    widget = "self.ui.label_epn_"+str(cur_label_num)
                    col = (cur_label_num%iconv_r)
                    row = 2*int(cur_label_num/iconv_r)
                    new_pos = (row, col)
                    print(new_pos)
                    if not MainWindow.isFullScreen():
                        cur_label = self.ui.list2.currentRow()
                        p1 = "self.ui.gridLayout2.indexOf(self.ui.label_epn_{0})".format(cur_label)
                        index = eval(p1)
                        print(index, '--index--')
                        self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                        self.ui.tab_6.hide()
                        p1 = "self.ui.gridLayout.addWidget({0}, 0, 1, 1, 1)".format(widget)
                        exec(p1)
                        p2="self.ui.label_epn_"+str(cur_label_num)+".setMaximumSize(QtCore.QSize("+str(screen_width)+", "+str(screen_height)+"))"
                        exec(p2)
                        self.ui.gridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.superGridLayout.setContentsMargins(0, 0, 0, 0)
                        self.ui.gridLayout1.setContentsMargins(0, 0, 0, 0)
                        self.ui.gridLayout2.setContentsMargins(0, 0, 0, 0)
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.gridLayout1.setSpacing(0)
                        self.ui.gridLayout2.setSpacing(0)
                        self.ui.superGridLayout.setSpacing(0)
                        MainWindow.showFullScreen()
                    else:
                        w = float((self.ui.tab_6.width()-60)/iconv_r)
                        h = int(w/self.ui.image_aspect_allowed)
                        width=str(int(w))
                        height=str(int(h))
                        r = self.ui.current_thumbnail_position[0]
                        c = self.ui.current_thumbnail_position[1]
                        cur_label = self.ui.list2.currentRow()
                        p6="self.ui.gridLayout2.addWidget(self.ui.label_epn_"+str(cur_label)+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
                        exec(p6)
                        QtWidgets.QApplication.processEvents()
                        MainWindow.showNormal()
                        MainWindow.showMaximized()

                        p1="self.ui.label_epn_"+str(cur_label_num)+".y()"
                        yy=eval(p1)
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
                        QtWidgets.QApplication.processEvents()
                        p1="self.ui.label_epn_"+str(cur_label_num)+".setFocus()"
                        exec(p1)
                        QtCore.QTimer.singleShot(1000, self.ui.update_thumbnail_position)
            else:
                if not self.ui.float_window.isHidden():
                    if not self.ui.float_window.isFullScreen():
                        cur_label = self.ui.list2.currentRow()
                        p1 = "self.ui.gridLayout2.indexOf(self.ui.label_epn_{0})".format(cur_label)
                        index = eval(p1)
                        print(index, '--index--')
                        self.ui.current_thumbnail_position = self.ui.gridLayout2.getItemPosition(index)
                        self.ui.float_window.showFullScreen()
                    else:
                        self.ui.float_window.showNormal()

    def player_quit(self, msg=None):
        self.ui.player_stop.clicked.emit()
        
    def load_external_sub(self, mode=None):
        if mode is None:
            fname = QtWidgets.QFileDialog.getOpenFileNames(
                    MainWindow, 'Select Subtitle file', self.ui.last_dir)
            if fname:
                logger.info(fname)
                if fname[0]:
                    self.ui.last_dir, file_choose = os.path.split(fname[0][0])
                    title_sub = fname[0][0]
                    if self.player_val == "mplayer":
                        txt = '\nsub_load '+'"'+title_sub+'"\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer.write(txt_b)
                    else:
                        txt = '\nsub_add '+'"'+title_sub+'" select\n'
                        txt_b = bytes(txt, 'utf-8')
                        logger.info("{0} - {1}".format(txt_b, txt))
                        self.mpvplayer.write(txt_b)
            self.ui.acquire_subtitle_lock = False
        elif mode == 'network':
            site = self.ui.get_parameters_value(st='site')['site']
            if site.lower() == 'myserver':
                title_sub = self.ui.final_playing_url + '.subtitle'
                if self.player_val == "mplayer":
                    txt = '\nsub_load '+'"'+title_sub+'"\n'
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    self.mpvplayer.write(txt_b)
                else:
                    txt = '\nsub_add '+'"'+title_sub+'" select\n'
                    txt_b = bytes(txt, 'utf-8')
                    logger.info("{0} - {1}".format(txt_b, txt))
                    self.mpvplayer.write(txt_b)
            else:
                logger.warn('Not Allowed')
                
    def player_quit_old(self, msg=None):
        quitReally = "yes"
        self.ui.set_parameters_value(quit_r=quitReally)
        if not msg:
            self.mpvplayer.write(b'\n quit \n')
        param_dict_val = self.ui.get_parameters_value(idw='idw', sw='screen_width',
                                                      sh='screen_height')
        idw = param_dict_val['idw']
        screen_width = param_dict_val['screen_width']
        screen_height = param_dict_val['screen_height']
        if not idw or idw == str(int(self.winId())):
            #self.ui.player_stop.clicked.emit()
            #return 0
            self.ui.player_play_pause.setText(self.ui.player_buttons['play'])
            param_dict = self.ui.get_parameters_value(
                wgt='wget', vl='video_local_stream', sh='show_hide_titlelist',
                sc='show_hide_cover', icn='iconv_r_indicator',
                tab_6_sz='tab_6_size_indicator', screen_width='screen_width')
            wget = param_dict['wget']
            video_local_stream = param_dict['video_local_stream']
            show_hide_titlelist = param_dict['show_hide_titlelist']
            show_hide_cover = param_dict['show_hide_cover']
            iconv_r_indicator = param_dict['iconv_r_indicator']
            tab_6_size_indicator = param_dict['tab_6_size_indicator']
            screen_width = param_dict['screen_width']
            logger.info(
                '{0}-{1}-{2}-{3}-{4}'.format(
                wget, video_local_stream, show_hide_titlelist, show_hide_cover, iconv_r_indicator))
            if video_local_stream:
                tmp_pl = os.path.join(TMPDIR, 'player_stop.txt')
                f = open(tmp_pl, 'w')
                f.close()
            if not MainWindow.isHidden():
                if self.ui.tab_6.isHidden() and self.ui.tab_2.isHidden():
                    self.ui.tab_5.showNormal()
                    self.ui.tab_5.hide()
                    if show_hide_titlelist == 1:
                        self.ui.list1.show()
                    if show_hide_cover == 1:
                        self.ui.label.show()
                        self.ui.text.show()
                    if show_hide_titlelist == 1:
                        self.ui.list2.show()
                    self.ui.list2.setFocus()
                elif not self.ui.tab_6.isHidden():
                    self.ui.gridLayout.addWidget(self.ui.tab_6, 0, 1, 1, 1)
                    #self.ui.tab_5.setMinimumSize(0, 0)
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.tab_6.setMaximumSize(10000, 10000)
                    tab_6_size_indicator.append(screen_width-40)
                    #self.ui.frame1.hide()
                    self.ui.tab_5.hide()
                    if iconv_r_indicator:
                        iconv_r = iconv_r_indicator[0]
                    else:
                        iconv_r = 5
                    self.ui.set_parameters_value(thumb_indicator='empty',
                                                 iconv=iconv_r, tab_6=tab_6_size_indicator)
                    QtWidgets.QApplication.processEvents()
                    #num = self.ui.list2.currentRow()
                    ##self.ui.thumbnail_label_update_epn()
                    self.ui.scrollArea1.verticalScrollBar().setValue(0)
                    self.ui.frame2.show()
                    self.ui.frame1.show()
                    self.ui.labelFrame2.show()
                    self.ui.thumbnail_label_update_epn()
                    QtWidgets.QApplication.processEvents()
                    QtCore.QTimer.singleShot(1000, self.ui.update_thumbnail_position)
                if wget:
                    if wget.processId() > 0:
                        self.ui.progress.show()
                if MainWindow.isFullScreen():
                    self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    self.ui.frame1.show()
                    MainWindow.showNormal()
                    MainWindow.showMaximized()
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    self.ui.gridLayout.setSpacing(5)
                    self.ui.superGridLayout.setSpacing(0)
                    self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                if not self.ui.tab_2.isHidden():
                    MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
                    self.ui.list2.hide()
                    self.ui.goto_epn.hide()
                    self.ui.list1.hide()
                    self.ui.frame.hide()
            else:
                if not self.ui.float_window.isHidden():
                    if self.ui.float_window.isFullScreen():
                        self.ui.float_window.showNormal()
        else:
            param_dict = self.ui.get_parameters_value(t='tab_6_size_indicator')
            tab_6_size_indicator = param_dict['tab_6_size_indicator']
            #if tab_6_size_indicator:
            #    tab_6_size_indicator.pop()
            tab_6_size_indicator.append(self.ui.tab_6.width())
            self.ui.set_parameters_value(tab_6=tab_6_size_indicator)
            param_dict = self.ui.get_parameters_value(
                wgt='wget', icn='iconv_r_indicator', i='iconv_r',
                cl='cur_label_num')
            wget = param_dict['wget']
            iconv_r_indicator = param_dict['iconv_r_indicator']
            iconv_r = param_dict['iconv_r']
            cur_label_num = param_dict['cur_label_num']
            if not MainWindow.isHidden():
                col = (cur_label_num%iconv_r)
                row = 2*int(cur_label_num/iconv_r)
                new_pos = (row, col)
                print(new_pos)
                if iconv_r_indicator:
                    iconv_r = iconv_r_indicator[0]
                    self.ui.set_parameters_value(iconv=iconv_r)
                if self.ui.video_mode_index == 5:
                    pass
                else:
                    if '	' in self.ui.epn_arr_list[cur_label_num]:
                        nameEpn = (str(self.ui.epn_arr_list[cur_label_num])).split('	')[0]
                    else:
                        nameEpn = os.path.basename(self.ui.epn_arr_list[cur_label_num])
                    if nameEpn.startswith('#'):
                        nameEpn = nameEpn.replace('#', ui.check_symbol, 1)
                    length_1 = self.ui.list2.count()
                    q3="self.ui.label_epn_"+str(length_1+cur_label_num)+".setText(nameEpn)"
                    exec (q3)
                    q3="self.ui.label_epn_"+str(length_1+cur_label_num)+".setAlignment(QtCore.Qt.AlignCenter)"
                    exec(q3)
                    if MainWindow.isFullScreen():
                        w = float((self.ui.tab_6.width()-60)/iconv_r)
                        h = int(w/self.ui.image_aspect_allowed)
                        width=str(int(w))
                        height=str(int(h))
                        r = self.ui.current_thumbnail_position[0]
                        c = self.ui.current_thumbnail_position[1]
                        p6="self.ui.gridLayout2.addWidget(self.ui.label_epn_"+str(cur_label_num)+", "+str(r)+", "+str(c)+", 1, 1, QtCore.Qt.AlignCenter)"
                        exec(p6)
                        QtWidgets.QApplication.processEvents()
                        p2="self.ui.label_epn_"+str(cur_label_num)+".setMaximumSize(QtCore.QSize("+width+", "+height+"))"
                        p3="self.ui.label_epn_"+str(cur_label_num)+".setMinimumSize(QtCore.QSize("+width+", "+height+"))"
                        exec(p2)
                        exec(p3)
    
                        self.ui.gridLayout.setSpacing(5)
                        self.ui.superGridLayout.setContentsMargins(5, 5, 5, 5)
                        if wget:
                            if wget.processId() > 0:
                                self.ui.goto_epn.hide()
                                self.ui.progress.show()
                        self.ui.frame2.show()
                        MainWindow.showNormal()
                        MainWindow.showMaximized()
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
                        QtCore.QTimer.singleShot(1000, self.ui.update_thumbnail_position)
                    else:
                        self.ui.thumbnail_label_update()
                        QtWidgets.QApplication.processEvents()
                        QtWidgets.QApplication.processEvents()
                        p1="self.ui.label_epn_"+str(cur_label_num)+".y()"
                        yy=eval(p1)
                        self.ui.scrollArea1.verticalScrollBar().setValue(yy)
            else:
                if not self.ui.float_window.isHidden():
                    if not self.ui.float_window.isFullScreen():
                        pass
                    else:
                        self.ui.float_window.showNormal()
                    
    def keyPressEvent(self, event):
        if (event.modifiers() == QtCore.Qt.ControlModifier
                and event.key() == QtCore.Qt.Key_Right):
            self.ui.list2.setFocus()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(10)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +10 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 10
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +10 \n')
            #self.frameShowHide()
        elif event.key() == QtCore.Qt.Key_1:
            self.mpvplayer.write(b'\n add chapter -1 \n')
        elif event.key() == QtCore.Qt.Key_2:
            self.mpvplayer.write(b'\n add chapter 1 \n')
        elif event.key() == QtCore.Qt.Key_3:
            self.mpvplayer.write(b'\n cycle ass-style-override \n')
        elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_V):
            self.mpvplayer.write(b'\n cycle ass-vsfilter-aspect-compat \n')
        elif event.key() == QtCore.Qt.Key_Left:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-10)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek -10 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 10
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -10 \n')
            #self.frameShowHide()
        elif event.key() == QtCore.Qt.Key_BracketRight:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek +90 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek +90 \n')
        elif event.key() == QtCore.Qt.Key_BracketLeft:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek -5 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek -5 \n')
        elif event.key() == QtCore.Qt.Key_0:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n volume +5 \n')
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n add ao-volume +5 \n')
        elif event.key() == QtCore.Qt.Key_9:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n volume -5 \n')
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n add ao-volume -5 \n')
        elif event.key() == QtCore.Qt.Key_A:
            self.ui.mpvplayer_aspect_cycle = (self.ui.mpvplayer_aspect_cycle + 1) % 5
            aspect_val = self.ui.mpvplayer_aspect.get(str(self.ui.mpvplayer_aspect_cycle))
            logger.info('aspect:{0}::value:{1}'.format(self.ui.mpvplayer_aspect_cycle, aspect_val))
            if aspect_val == '-1':
                show_text_val = 'Original Aspect'
            elif aspect_val == '0':
                show_text_val = 'Aspect Ratio Disabled'
            else:
                show_text_val = aspect_val
            if self.player_val == 'mpv':
                msg = '\n set video-aspect "{0}" \n'.format(aspect_val)
                self.mpvplayer.write(bytes(msg, 'utf-8'))
                txt_osd = '\n show-text "{0}" \n'.format(show_text_val)
                self.mpvplayer.write(bytes(txt_osd, 'utf-8'))
            elif self.player_val == 'mplayer':
                self.mplayer_aspect_msg = True
                if self.mpvplayer.processId() > 0:
                    if self.ui.final_playing_url in self.ui.history_dict_obj:
                        seek_time, acc_time, sub_id, audio_id, rem_quit = self.ui.history_dict_obj.get(self.ui.final_playing_url)
                        rem_quit = 1
                        self.ui.history_dict_obj.update({self.ui.final_playing_url:[seek_time, acc_time, sub_id, audio_id, rem_quit]})
                    self.mpvplayer.kill()
        elif event.key() == QtCore.Qt.Key_N:
            self.mpvplayer.write(b'\n playlist_next \n')
        elif event.key() == QtCore.Qt.Key_L:
            #self.ui.tab_5.setFocus()
            self.ui.playerLoopFile(self.ui.player_loop_file)
        elif event.key() == QtCore.Qt.Key_End:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n seek 99 1 \n')
            else:
                self.mpvplayer.write(b'\n osd-msg-bar seek 100 absolute-percent \n')
        elif event.key() == QtCore.Qt.Key_P:
            if self.ui.frame1.isHidden():
                self.ui.gridLayout.setSpacing(0)
                self.ui.frame1.show()
            else:
                self.ui.gridLayout.setSpacing(5)
                self.ui.frame1.hide()
        elif event.key() == QtCore.Qt.Key_Space:
            txt = self.ui.player_play_pause.text()
            if txt == self.ui.player_buttons['play']:
                self.ui.player_play_pause.setText(self.ui.player_buttons['pause'])
            elif txt == self.ui.player_buttons['pause']:
                self.ui.player_play_pause.setText(self.ui.player_buttons['play'])
                self.ui.mplayer_pause_buffer = False
                self.ui.mplayer_nop_error_pause = False
                buffering_mplayer = "no"
                self.ui.set_parameters_value(bufm=buffering_mplayer)
            if self.ui.frame_timer.isActive:
                self.ui.frame_timer.stop()
            if self.ui.mplayer_timer.isActive():
                self.ui.mplayer_timer.stop()
            if self.player_val == "mplayer":
                if MainWindow.isFullScreen():
                    site = self.ui.get_parameters_value(s='site')['site']
                    if (site != "Music" and self.ui.tab_6.isHidden()
                            and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                        self.ui.frame1.hide()
                self.mpvplayer.write(b'\n pausing_toggle osd_show_progression \n')
            else:
                param_dict = self.ui.get_parameters_value(
                    ps='pause_indicator', mpv='mpv_indicator', s='site')
                pause_indicator = param_dict['pause_indicator']
                mpv_indicator = param_dict['mpv_indicator']
                site = param_dict['site']
                if not pause_indicator:
                    self.mpvplayer.write(b'\n set pause yes \n')
                    if MainWindow.isFullScreen():
                        self.ui.gridLayout.setSpacing(0)
                        self.ui.frame1.show()
                    pause_indicator.append("Pause")
                else:
                    self.mpvplayer.write(b'\n set pause no \n')
                    if MainWindow.isFullScreen():
                        if (site != "Music" and self.ui.tab_6.isHidden()
                                and self.ui.list2.isHidden() and self.ui.tab_2.isHidden()):
                            self.ui.frame1.hide()
                    pause_indicator.pop()
                    if mpv_indicator:
                        mpv_indicator.pop()
                        cache_empty = 'no'
                        self.ui.set_parameters_value(
                            cache_val=cache_empty, mpv_i=mpv_indicator)
        elif event.key() == QtCore.Qt.Key_Up:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(60)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +60 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 60
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +60 \n')
        elif event.key() == QtCore.Qt.Key_Down:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-60)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"): 
                    self.mpvplayer.write(b'\n seek -60 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 60
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -60 \n')
        elif event.key() == QtCore.Qt.Key_PageUp:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(300)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek +300 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek + 300
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek +300 \n')
        elif event.key() == QtCore.Qt.Key_PageDown:
            if self.player_val == "mplayer":
                txt = '\n osd 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.set_slider_val(-300)
                param_dict = self.ui.get_parameters_value(st='site')
                site = param_dict['site']
                if (site == "Local" or site == "None" or site == "PlayLists" 
                        or site == "Music" or site == "Video"):
                    self.mpvplayer.write(b'\n seek -300 \n')
                else:
                    self.ui.total_seek = self.ui.total_seek - 300
                    r = "Seeking "+str(self.ui.total_seek)+'s'
                    self.ui.progressEpn.setFormat(r)
                    if self.seek_timer.isActive():
                        self.seek_timer.stop()
                    self.seek_timer.start(500)
                    self.frameShowHide()
            else:
                txt = '\n set osd-level 1 \n'
                self.mpvplayer.write(bytes(txt, 'utf-8'))
                self.mpvplayer.write(b'\n osd-msg-bar seek -300 \n')
        elif event.key() == QtCore.Qt.Key_O:
            if self.player_val == 'mplayer':
                self.mpvplayer.write(b'\n osd \n')
            else:
                self.mpvplayer.write(b'\n cycle osd-level \n')
        elif event.key() == QtCore.Qt.Key_M:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n osd_show_property_text ${filename} \n')
            else:
                self.mpvplayer.write(b'\n show-text "${filename}" \n')
        elif event.key() == QtCore.Qt.Key_I:
            if self.player_val == "mpv":
                self.mpvplayer.write(b'\n show_text ${file-size} \n')
            else:
                self.set_slider_val(-300)
                param_dict = self.ui.get_parameters_value(st='rfr_url')
                rfr_url = param_dict['rfr_url']
                logger.info(self.ui.final_playing_url)
                logger.info(rfr_url)
                if self.ui.total_file_size:
                    sz = str(self.ui.total_file_size)+' MB'
                else:
                    if (self.ui.final_playing_url.startswith('http') 
                            and self.ui.final_playing_url.endswith('.mkv')):
                        self.ui.total_file_size = self.url_resolve_size(
                            self.ui.final_playing_url, rfr_url)
                        sz = str(self.ui.total_file_size)+' MB'
                    else:
                        self.ui.total_file_size = 0
                        sz = str(0)
                t = bytes('\n'+'osd_show_text '+'"'+sz+'"'+' 4000'+'\n', 'utf-8')
                logger.info(t)
                self.mpvplayer.write(t)
        elif event.key() == QtCore.Qt.Key_E:
            if self.player_val == "mplayer" and MainWindow.isFullScreen():
                w = self.width()
                w = w + (0.05*w)
                h = self.height()
                h = h + (0.05*h)
                self.setMaximumSize(w, h)
            else:
                self.mpvplayer.write(b'\n add video-zoom +0.01 \n')
        elif event.key() == QtCore.Qt.Key_W:
            if self.player_val == "mplayer" and MainWindow.isFullScreen():
                w = self.width()
                w = w - (0.05*w)
                h = self.height()
                h = h - (0.05*h)
                self.setMaximumSize(w, h)
            else:
                self.mpvplayer.write(b'\n add video-zoom -0.01 \n')
        elif event.key() == QtCore.Qt.Key_R:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n sub_pos -1 \n')
            else:
                self.mpvplayer.write(b'\n add sub-pos -1 \n')
        elif event.key() == QtCore.Qt.Key_T:
            if self.player_val == "mplayer":
                self.mpvplayer.write(b'\n sub_pos +1 \n')
            else:
                self.mpvplayer.write(b'\n add sub-pos +1 \n')
        elif (event.modifiers() == QtCore.Qt.ShiftModifier 
                and event.key() == QtCore.Qt.Key_J):
            #self.ui.load_external_sub()
            self.load_external_sub()
        elif (event.modifiers() == QtCore.Qt.ControlModifier 
                and event.key() == QtCore.Qt.Key_J):
            #self.ui.load_external_sub()
            self.load_external_sub(mode='network')
        elif event.key() == QtCore.Qt.Key_J:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer.write(b'\n sub_select \n')
                self.mpvplayer.write(b'\n get_property sub \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer.write(b'\n cycle sub \n')
                self.mpvplayer.write(b'\n print-text "SUB_KEY_ID=${sid}" \n')
                self.mpvplayer.write(b'\n show-text "${sid}" \n')
        elif event.key() == QtCore.Qt.Key_K:
            if self.player_val == "mplayer":
                if not self.mplayer_OsdTimer.isActive():
                    self.mpvplayer.write(b'\n osd 1 \n')
                else:
                    self.mplayer_OsdTimer.stop()
                self.mpvplayer.write(b'\n switch_audio \n')
                self.mpvplayer.write(b'\n get_property switch_audio \n')
                self.mplayer_OsdTimer.start(5000)
            else:
                self.mpvplayer.write(b'\n cycle audio \n')
                self.mpvplayer.write(b'\n print-text "AUDIO_KEY_ID=${aid}" \n')
                self.mpvplayer.write(b'\n show-text "${aid}" \n')
        elif event.key() == QtCore.Qt.Key_F:
            if not self.ui.force_fs:
                self.player_fs()
            else:
                wd = self.width()
                ht = self.height()
                if wd == screen_width and ht == screen_height:
                    self.player_fs()
                else:
                    self.player_fs(mode='fs')
        elif event.key() == QtCore.Qt.Key_Period:
            self.ui.mpvNextEpnList()
        elif event.key() == QtCore.Qt.Key_Comma:
            self.ui.mpvPrevEpnList()
        elif (event.modifiers() == QtCore.Qt.ControlModifier
                and event.key() == QtCore.Qt.Key_Q):
            quitReally = "yes"
            self.ui.set_parameters_value(quit_r=quitReally)
            msg = '"Stop After current file"'
            msg_byt = bytes('\nshow-text {0}\n'.format(msg), 'utf-8')
            self.mpvplayer.write(msg_byt)
        elif (event.modifiers() == QtCore.Qt.ShiftModifier
                and event.key() == QtCore.Qt.Key_Q):
            quitReally = "yes"
            self.ui.set_parameters_value(quit_r=quitReally)
            self.ui.playerStop(msg='remember quit')
        elif event.key() == QtCore.Qt.Key_Q:
            self.player_quit()
        #super(PlayerWidget, self).keyPressEvent(event)
