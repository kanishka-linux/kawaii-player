from PyQt5 import QtCore, QtWidgets

class QtGuiQWidgetScroll(QtWidgets.QScrollArea):
    
    def __init__(self, parent, uiwidget):
        super(QtGuiQWidgetScroll, self).__init__(parent)
        global ui
        ui = uiwidget
        self.position = {}
        if ui.list1.currentItem():
            self.cur_row = ui.list1.currentRow()
        else:
            self.cur_row = 0
        self.text_color = ui.thumbnail_text_color_dict[ui.thumbnail_text_color]
        self.text_color_focus = ui.thumbnail_text_color_dict[ui.thumbnail_text_color_focus]
        
    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        if ui.search_on_type_btn.isHidden():
            self.setFocus()
        
    def sizeAdjust(self, nextR, direction):
        #ui.list1.setCurrentRow(nextR)
        self.cur_row = nextR
        p1 = "ui.label_"+str(nextR)+".y()"
        try:
            yy=eval(p1)
            p1 = "ui.label_"+str(nextR)+".x()"
            xy=eval(p1)
            p1 = "ui.label_"+str(nextR)+".setFocus()"
            exec (p1)
            new_cnt = str(nextR+ui.list1.count())
            p1 = "ui.label_{0}".format(new_cnt)
            label_number = eval(p1)
            self.text_color = ui.thumbnail_text_color_dict[ui.thumbnail_text_color]
            self.text_color_focus = ui.thumbnail_text_color_dict[ui.thumbnail_text_color_focus]
            #label_number.setTextColor(self.text_color_focus)
            ui.setLabelTextStyle(label_number, ui.thumbnail_text_color_focus)
            txt = label_number.text()
            try:
                label_number.setText(txt)
            except Exception as e:
                print(e, '--line--4597--')
                try:
                    label_number.setText(txt)
                except Exception as e:
                    print(e)
            label_number.setAlignment(QtCore.Qt.AlignCenter)
        except:
            return 0
        if ui.icon_size_arr:
            iconv_r = ui.icon_poster_indicator[-1]
            hi = ui.icon_size_arr[1]
            wi = ui.icon_size_arr[0]
            if direction == "down":		
                prevR = nextR - iconv_r
            elif direction == "up":
                prevR = nextR + iconv_r
            elif direction == "forward":
                prevR = nextR - 1
            elif direction == "backward":
                prevR = nextR + 1
            if prevR >= 0 and prevR < ui.list1.count():
                ht1 = (0.6*int(hi))
                wd1 = (0.6*int(wi))
                ht = str(ht1)
                wd = str(wd1)
                new_cnt = str(prevR+ui.list1.count())
                p1 = "ui.label_{0}".format(new_cnt)
                label_number = eval(p1)
                #label_number.setTextColor(self.text_color)
                ui.setLabelTextStyle(label_number, ui.thumbnail_text_color)
                txt = label_number.text()
                try:
                    label_number.setText(txt)
                except Exception as e:
                    print(e, '--line--4597--')
                    try:
                        label_number.setText(txt)
                    except Exception as e:
                        print(e)
                label_number.setAlignment(QtCore.Qt.AlignCenter)
            elif prevR < 0:
                p1 = "ui.label_"+str(nextR)+".width()"
                wd1=eval(p1)
                p1 = "ui.label_"+str(nextR)+".height()"
                ht1=eval(p1)
                ht = str(0.6*ht1)
                wd = str(0.6*wd1)
                print("ht="+wd)
                print("wd="+wd)
        else:
            hi = ui.icon_size_arr[1]
            wi = ui.icon_size_arr[0]
            p1 = "ui.label_"+str(nextR)+".width()"
            wd1=eval(p1)
            p1 = "ui.label_"+str(nextR)+".height()"
            ht1=eval(p1)
            ht = str(0.6*ht1)
            wd = str(0.6*wd1)
            print("ht="+wd)
            print("wd="+wd)
        
        ui.scrollArea.verticalScrollBar().setValue(yy-ht1)
        ui.scrollArea.horizontalScrollBar().setValue(xy-wd1)
        item = ui.list1.item(self.cur_row)
        if item:
            ui.labelFrame2.setText('{0}. {1}'.format(self.cur_row+1, item.text()))
        
    def keyPressEvent(self, event):
        if self.cur_row >= ui.list1.count():
            self.cur_row = 0
        if event.key() == QtCore.Qt.Key_Equal:
            iconv_r_poster = ui.icon_poster_indicator[-1]
            if iconv_r_poster > 1:
                iconv_r_poster = iconv_r_poster - 1
                ui.icon_poster_indicator.append(iconv_r_poster)
            if not ui.scrollArea.isHidden():
                ui.next_page('zoom')
            elif not ui.scrollArea1.isHidden():
                ui.thumbnail_label_update()
            if iconv_r_poster > 1:
                w = float((ui.tab_6.width()-60)/iconv_r_poster)
                #h = float((9*w)/16)
                h = int(w/ui.image_aspect_allowed)
                width=str(int(w))
                height=str(int(h))
                ui.scrollArea1.verticalScrollBar().setValue((((ui.cur_row+1)/iconv_r_poster)-1)*h+((ui.cur_row+1)/iconv_r_poster)*10)
        elif event.key() == QtCore.Qt.Key_Minus:
            iconv_r_poster = ui.icon_poster_indicator[-1]
            iconv_r_poster += 1
            ui.icon_poster_indicator.append(iconv_r_poster)
            if not ui.scrollArea.isHidden():
                ui.next_page('zoom')
            elif not ui.scrollArea1.isHidden():
                ui.thumbnail_label_update()
            if iconv_r_poster > 1:
                w = float((ui.tab_6.width()-60)/iconv_r_poster)
                #h = float((9*w)/16)
                h = int(w/ui.image_aspect_allowed)
                width=str(int(w))
                height=str(int(h))
                ui.scrollArea1.verticalScrollBar().setValue((((ui.cur_row+1)/iconv_r_poster)-1)*h+((ui.cur_row+1)/iconv_r_poster)*10)
        elif event.key() == QtCore.Qt.Key_Left:
                nextR = self.cur_row - 1
                if nextR >=0:
                    self.sizeAdjust(nextR, "backward")
                else:
                    ui.btn1.setFocus()
                    ui.dockWidget_3.show()
        elif event.key() == QtCore.Qt.Key_Down:
            iconv_r = ui.icon_poster_indicator[-1]
            nextR = self.cur_row
            if nextR < 0:
                self.sizeAdjust(0, "down")
            else:
                nextR = self.cur_row + iconv_r
                if nextR < ui.list1.count():
                    self.sizeAdjust(nextR, "down")
                else:
                    self.sizeAdjust(nextR-iconv_r, "down")
        elif event.key() == QtCore.Qt.Key_Up:
            iconv_r = ui.icon_poster_indicator[-1]
            nextR = self.cur_row
            if nextR < 0:
                self.sizeAdjust(0, "up")
            else:
                nextR = self.cur_row - iconv_r
                if nextR >= 0:
                    self.sizeAdjust(nextR, "up")
                else:
                    self.sizeAdjust(nextR+iconv_r, "up")
        elif event.key() == QtCore.Qt.Key_Right:
            nextR = self.cur_row
            if nextR < 0:
                self.sizeAdjust(0, "forward")
            else:
                nextR = self.cur_row + 1
                if nextR < ui.list1.count():
                    self.sizeAdjust(nextR, "forward")
                else:
                    self.sizeAdjust(nextR-1, "forward")
        elif event.key() == QtCore.Qt.Key_Return:
            ui.list1.setCurrentRow(self.cur_row)
            #ui.listfound()
            if not ui.lock_process:
                ui.IconViewEpn()
                ui.scrollArea1.show()
                ui.scrollArea1.setFocus()
        elif event.text().isalnum():
            ui.focus_widget = ui.list1
            if ui.search_on_type_btn.isHidden():
                g = self.geometry()
                txt = event.text()
                ui.search_on_type_btn.setGeometry(g.x()+self.width()-ui.width_allowed, g.y(), ui.width_allowed, 32)
                ui.search_on_type_btn.show()
                ui.search_on_type_btn.clear()
                ui.search_on_type_btn.setText(txt)
            else:
                ui.search_on_type_btn.setFocus()
                txt = ui.search_on_type_btn.text()
                new_txt = txt+event.text()
                ui.search_on_type_btn.setText(new_txt)
        else:
            ui.logger.debug('key not recognized')
            super(QtGuiQWidgetScroll, self).keyPressEvent(event)
        
        
class QtGuiQWidgetScroll1(QtWidgets.QScrollArea):
    
    def __init__(self, parent, uiwidget):
        super(QtGuiQWidgetScroll1, self).__init__(parent)
        global ui
        ui = uiwidget
        self.text_color = ui.thumbnail_text_color_dict[ui.thumbnail_text_color]
        self.text_color_focus = ui.thumbnail_text_color_dict[ui.thumbnail_text_color_focus]
        
    def mouseMoveEvent(self, event):
        if ui.auto_hide_dock:
            ui.dockWidget_3.hide()
        self.setFocus()
        
    def sizeAdjust(self, nextR, direction):
        ui.list2.setCurrentRow(nextR)
        try:
            p1 = "ui.label_epn_"+str(nextR)+".y()"
            yy = eval(p1)
            p1 = "ui.label_epn_"+str(nextR)+".x()"
            xy = eval(p1)
            p1 = "ui.label_epn_"+str(nextR)+".setFocus()"
            exec (p1)
            new_cnt = str(nextR+ui.list2.count())
            self.text_color = ui.thumbnail_text_color_dict[ui.thumbnail_text_color]
            self.text_color_focus = ui.thumbnail_text_color_dict[ui.thumbnail_text_color_focus]
            p1 = "ui.label_epn_{0}".format(new_cnt)
            label_number = eval(p1)
            ui.setLabelTextStyle(label_number, ui.thumbnail_text_color_focus)
            txt = label_number.text()
            try:
                label_number.setText(txt)
            except Exception as e:
                print(e, '--line--4597--')
                try:
                    label_number.setText(txt)
                except Exception as e:
                    print(e)
            label_number.setAlignment(QtCore.Qt.AlignCenter)
        except Exception as e:
            print(e, '--line--4596--')
            return 0
        if ui.list2.count() > 1:
            if ui.icon_size_arr:
                iconv_r = ui.get_parameters_value(i='iconv_r')['iconv_r']
                hi = ui.icon_size_arr[1]
                wi = ui.icon_size_arr[0]
                if direction == "down":		
                    prevR = nextR - iconv_r
                elif direction == "up":
                    prevR = nextR + iconv_r
                elif direction == "forward":
                    prevR = nextR - 1
                elif direction == "backward":
                    prevR = nextR + 1
                if prevR >= 0 and prevR < ui.list2.count():
                    ht1 = (0.6*int(hi))
                    wd1 = (0.6*int(wi))
                    ht = str(ht1)
                    wd = str(wd1)
                    new_cnt = str(prevR+ui.list2.count())
                    p1 = "ui.label_epn_{0}".format(new_cnt)
                    label_number = eval(p1)
                    #label_number.setTextColor(self.text_color)
                    ui.setLabelTextStyle(label_number, ui.thumbnail_text_color)
                    txt = label_number.text()
                    try:
                        label_number.setText(txt)
                    except Exception as e:
                        print(e, '--line--4597--')
                        try:
                            label_number.setText(txt)
                        except Exception as e:
                            print(e, '--line--4643--')
                    label_number.setAlignment(QtCore.Qt.AlignCenter)
                elif prevR < 0:
                    p1 = "ui.label_epn_"+str(nextR)+".width()"
                    wd1=eval(p1)
                    p1 = "ui.label_epn_"+str(nextR)+".height()"
                    ht1=eval(p1)
                    ht = str(0.6*ht1)
                    wd = str(0.6*wd1)
                    print("ht="+wd)
                    print("wd="+wd)
            else:
                p1 = "ui.label_epn_"+str(nextR)+".width()"
                wd1 = eval(p1)
                p1 = "ui.label_epn_"+str(nextR)+".height()"
                ht1 = eval(p1)
                ht = str(0.6*ht1)
                wd = str(0.6*wd1)
            ui.scrollArea1.verticalScrollBar().setValue(yy-ht1)
            ui.scrollArea1.horizontalScrollBar().setValue(xy-wd1)
            site = ui.get_parameters_value(s='site')['site']
            if site != "PlayLists":
                ui.labelFrame2.setText(ui.list2.currentItem().text())
            else:
                ui.labelFrame2.setText((ui.list2.currentItem().text()).split('	')[0])
            ui.label.hide()
            ui.text.hide()
            
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Equal:
            param_dict = ui.get_parameters_value(i='iconv_r', ir='iconv_r_indicator')
            iconv_r = param_dict['iconv_r']
            iconv_r_indicator = param_dict['iconv_r_indicator']
            if iconv_r > 1:
                iconv_r = iconv_r-1
                if iconv_r_indicator:
                    iconv_r_indicator.pop()
                iconv_r_indicator.append(iconv_r)
                ui.set_parameters_value(iconv=iconv_r, iconvr=iconv_r_indicator)
            if not ui.scrollArea.isHidden():
                ui.next_page('not_deleted')
            elif not ui.scrollArea1.isHidden():
                ui.thumbnail_label_update_epn()
            if iconv_r > 1:
                w = float((ui.tab_6.width()-60)/iconv_r)
                #h = float((9*w)/16)
                h = int(w/ui.image_aspect_allowed)
                width=str(int(w))
                height=str(int(h))
                ui.scrollArea1.verticalScrollBar().setValue((((ui.cur_row+1)/iconv_r)-1)*h+((ui.cur_row+1)/iconv_r)*10)
        elif event.key() == QtCore.Qt.Key_Minus:
            param_dict = ui.get_parameters_value(i='iconv_r', ir='iconv_r_indicator')
            iconv_r = param_dict['iconv_r']
            iconv_r_indicator = param_dict['iconv_r_indicator']
            iconv_r = iconv_r+1
            if iconv_r_indicator:
                iconv_r_indicator.pop()
            iconv_r_indicator.append(iconv_r)
            ui.set_parameters_value(iconv=iconv_r, iconvr=iconv_r_indicator)
            if not ui.scrollArea.isHidden():
                ui.next_page('not_deleted')
            elif not ui.scrollArea1.isHidden():
                ui.thumbnail_label_update_epn()
            if iconv_r > 1:
                w = float((ui.tab_6.width()-60)/iconv_r)
                #h = float((9*w)/16)
                h = int(w/ui.image_aspect_allowed)
                width=str(int(w))
                height=str(int(h))
                ui.scrollArea1.verticalScrollBar().setValue((((ui.cur_row+1)/iconv_r)-1)*h+((ui.cur_row+1)/iconv_r)*10)
        if ui.mpvplayer_val.processId() == 0:
            if event.key() == QtCore.Qt.Key_Right:
                nextR = ui.list2.currentRow()
                if nextR < 0:
                    self.sizeAdjust(0, "forward")
                else:
                    nextR = ui.list2.currentRow()+1
                    if nextR < ui.list2.count():
                        self.sizeAdjust(nextR, "forward")
                    else:
                        self.sizeAdjust(nextR-1, "forward")
            elif event.key() == QtCore.Qt.Key_Left:
                nextR = ui.list2.currentRow()-1
                if nextR >=0:
                    self.sizeAdjust(nextR, "backward")
                else:
                    ui.btn1.setFocus()
                    ui.dockWidget_3.show()
            elif event.key() == QtCore.Qt.Key_Down:
                iconv_r = ui.get_parameters_value(i='iconv_r')['iconv_r']
                nextR = ui.list2.currentRow()
                if nextR < 0:
                    self.sizeAdjust(0, "down")
                else:
                    nextR = ui.list2.currentRow()+iconv_r
                    if nextR < ui.list2.count():
                        self.sizeAdjust(nextR, "down")
                    else:
                        self.sizeAdjust(nextR-iconv_r, "down")
            elif event.key() == QtCore.Qt.Key_Up:
                iconv_r = ui.get_parameters_value(i='iconv_r')['iconv_r']
                nextR = ui.list2.currentRow()
                if nextR < 0:
                    self.sizeAdjust(0, "up")
                else:
                    nextR = ui.list2.currentRow()-iconv_r
                    if nextR >= 0:
                        self.sizeAdjust(nextR, "up")
                    else:
                        self.sizeAdjust(nextR+iconv_r, "up")
            elif event.key() == QtCore.Qt.Key_Backspace:
                item = ui.list1.currentItem()
                if item:
                    ui.prev_thumbnails()
                    if ui.view_mode == 'thumbnail':
                        ui.scrollArea.setFocus()
            elif event.key() == QtCore.Qt.Key_Return:
                num = ui.list2.currentRow()
                txt_count = num + ui.list2.count()
                p1 = "ui.label_epn_{0}.text()".format(txt_count)
                txt = eval(p1)
                ui.thumbnail_label_number[:] = []
                ui.thumbnail_label_number = [num, txt]
                p1 = "ui.gridLayout2.indexOf(ui.label_epn_{0})".format(num)
                index = eval(p1)
                if ui.player_val == "libmpv":
                    ui.video_mode_index = 1
                ui.current_thumbnail_position = ui.gridLayout2.getItemPosition(index)
                exec_str = 'ui.label_epn_{0}.change_video_mode({1}, {2})'.format(num, ui.video_mode_index, num)
                exec(exec_str)
            elif event.text().isalnum():
                ui.focus_widget = ui.list2
                if ui.search_on_type_btn.isHidden():
                    g = self.geometry()
                    txt = event.text()
                    ui.search_on_type_btn.setGeometry(g.x()+self.width()-ui.width_allowed, g.y(), ui.width_allowed, 32)
                    ui.search_on_type_btn.show()
                    ui.search_on_type_btn.clear()
                    ui.search_on_type_btn.setText(txt)
                else:
                    ui.search_on_type_btn.setFocus()
                    txt = ui.search_on_type_btn.text()
                    new_txt = txt+event.text()
                    ui.search_on_type_btn.setText(new_txt)
            else:
                super(QtGuiQWidgetScroll1, self).keyPressEvent(event)
