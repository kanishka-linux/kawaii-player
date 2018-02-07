import os


class WidgetStyleSheet:
    
    def __init__(self, ui_widet, hm, base, dsession=None):
        global gui, home, BASEDIR, desktop_session
        gui = ui_widet
        home = hm
        BASEDIR = base
        if dsession is None:
            desktop_session = os.getenv('DESKTOP_SESSION')
            if desktop_session:
                desktop_session = desktop_session.lower()
            else:
                desktop_session = 'lxde'
        else:
            desktop_session = dsession
            
    def change_list2_style(self, mode=None):
        if isinstance(mode, bool):
            gui.list_with_thumbnail = mode
        if gui.player_theme in ['default', 'transparent', 'mix']:
            if gui.list_with_thumbnail:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                QListWidget:item {height: 128px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
            else:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}
                QListWidget:item {height: 30px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
        elif gui.player_theme == 'system':
            gui.list2.setAlternatingRowColors(True)
            if gui.list_with_thumbnail:
                gui.list2.setStyleSheet("""QListWidget{
                border-radius:3px;
                }
                
                QListWidget:item {
                height: 128px;
                }
                QListWidget:item:selected:active {
                background:rgba(0, 0, 0, 20%);
                color: green;
                }
                """)
            else:
                gui.list2.setStyleSheet("""QListWidget{
                border-radius:3px;
                }
                
                QListWidget:item {
                height: 30px;
                }
                QListWidget:item:selected:active {
                background:rgba(0, 0, 0, 20%);
                color: green;
                }
                """)
        elif gui.player_theme == 'dark':
            if gui.list_with_thumbnail:
                gui.list2.setStyleSheet("""QListWidget{
                color:white;background:rgb(56,60,74);
                }
                
                QListWidget:item {
                height: 128px;
                }
                QListWidget:item:selected:active {
                background:rgba(0, 0, 0, 20%);
                color: green;
                }
                """)
            else:
                gui.list2.setStyleSheet("""QListWidget{
                color:white;background:rgb(56,60,74);
                }
                
                QListWidget:item {
                height: 30px;
                }
                QListWidget:item:selected:active {
                background:rgba(0, 0, 0, 20%);
                color: green;
                }
                """)
            
    def apply_stylesheet(self, widget=None, theme=None):
        if not widget and (theme is None or theme in ['default', 'transparent', 'mix']):
            gui.dockWidget_3.setStyleSheet("""
                font:bold 12px;color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);""")
            gui.tab_6.setStyleSheet("""font:bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);""")
            try:
                if desktop_session.lower() != 'plasma':
                    gui.tab_2.setStyleSheet("""font:bold 12px;color:white;
                    background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);""")
            except NameError as e:
                print(e)
            gui.tab_5.setStyleSheet("""font:bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);""")
            """
            gui.btnWebClose.setStyleSheet("font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;")
            gui.btnWebHide.setStyleSheet("font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;")
            gui.btnWebPrev.setStyleSheet("font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;")
            gui.btnWebNext.setStyleSheet("font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;")
            """
            gui.btnOpt.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;""")
            gui.go_opt.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;""")
            gui.text.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%)""")
            gui.text_save_btn.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 60%);border:rgba(0, 0, 0, 30%);border-radius:3px""")
            gui.search_on_type_btn.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 60%);border:rgba(0, 0, 0, 30%);border-radius:3px""")
            gui.goto_epn.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 25%);border:rgba(0, 0, 0, 30%);border-radius:3px;""")
            gui.line.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;""")
            gui.frame.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 25%);border:rgba(0, 0, 0, 30%);border-radius:3px;""")
            gui.frame1.setStyleSheet("""font: bold 11px;color:white;
                background:rgba(0, 0, 0, 60%);border:rgba(0, 0, 0, 30%);border-radius:3px;""")
            
            gui.torrent_frame.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);""")
            gui.float_window.setStyleSheet("""font: bold 12px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);""")
            gui.player_opt.setStyleSheet("""font:bold 11px;color:white;
                background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;height:20px""")
            for frame in [gui.frame2, gui.frame_web]:
                frame.setStyleSheet("""
                    QFrame{background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);}
                    QPushButton{border-radius:0px;}
                    QPushButton::hover{background-color: yellow;color: black;}
                    QPushButton:pressed{background-color: violet;}
                    QLabel{background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);}
                    QComboBox {
                    selection-color:yellow;
                    }
                    QComboBox::hover{background-color: yellow;color: black;}
                    QComboBox::drop-down {
                    width: 47px;
                    border: 0px;
                    color:black;
                    }
                    QComboBox::focus {
                    color:yellow;
                    }
                    QComboBox::down-arrow {
                    width: 2px;
                    height: 2px;
                    }
                    """)
            gui.player_opt.setStyleSheet("""
            QFrame{background:rgba(0, 0, 0, 0%);border:rgba(0, 0, 0, 0%);}
            QPushButton{border-radius:0px;max-height:30px;}
            QPushButton::hover{background-color: yellow;color: black;}
            QPushButton:pressed{background-color: violet;}""")

            gui.btn1.setStyleSheet("""QComboBox {
            min-height:30px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            selection-color:yellow;
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::focus {
            color:yellow;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")
            
            gui.btnAddon.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            selection-color:yellow;
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::focus {
            color:yellow;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")
            gui.comboView.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            padding: 1px 1px 1px 1px;
            font:bold 12px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")
            gui.slider.setStyleSheet("""QSlider:groove:horizontal {
            height: 8px;
            border:rgba(0, 0, 0, 30%);
            background:rgba(0, 0, 0, 30%);
            margin: 2px 0;
            }
            QSlider:handle:horizontal {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
            border: 1px solid #5c5c5c;
            width: 2px;
            margin: -2px 0; 
            border-radius: 3px;
            }
            QToolTip {
            font : Bold 10px;
            color: white;
            background:rgba(157, 131, 131, 80%)
            }
            """)
            gui.list1.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius:3px;
            }
            
            QListWidget:item {
            height: 30px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.list_poster.setStyleSheet("""
            QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 50%);border:rgba(0, 0, 0, 50%);
            }
            
            QListWidget:item {
            height: 256px;
            width: 128px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 60%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            
            """)
            gui.list4.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.list5.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.list6.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.scrollArea.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.scrollArea1.setStyleSheet("""QListWidget{
            font: Bold 12px;color:white;
            background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: yellow;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            if gui.list_with_thumbnail:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}
                QListWidget:item {height: 128px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
            else:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}
                QListWidget:item {height: 30px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
            gui.list3.setStyleSheet("""QListWidget{
            font: bold 12px;color:white;background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 30%);border-radius: 3px;
            }
            QListWidget:item {
            height: 30px;
            }
            QListWidget:item:selected:active {
            background:rgba(0, 0, 0, 20%);
            color: violet;
            }
            QListWidget:item:selected:inactive {
            border:rgba(0, 0, 0, 30%);
            }
            QMenu{
                font: 12px;color:black;background-image:url('1.png');
            }
            """)
            gui.progress.setStyleSheet("""QProgressBar{
            font: bold 12px;
            color:white;
            background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 1%) ;
            border-radius: 1px;
            text-align: center;}
            
            QProgressBar:chunk {
            background-color: rgba(255, 255, 255, 30%);
            width: 10px;
            margin: 0.5px;
            }}""")
            
            gui.progressEpn.setStyleSheet("""QProgressBar{
            font: bold 12px;
            color:white;
            background:rgba(0, 0, 0, 30%);
            border:rgba(0, 0, 0, 1%) ;
            border-radius: 1px;
            text-align: center;
            }
            
            QProgressBar:chunk {
            background-color: rgba(255, 255, 255, 30%);
            width: 10px;
            margin: 0.5px;
            }}""")
            try:
                if desktop_session.lower() != 'plasma':
                    gui.btnWebReviews.setStyleSheet("""QComboBox {
                    min-height:0px;
                    max-height:50px;
                    border-radius: 3px;
                    font-size:10px;
                    padding: 1px 1px 1px 1px;
                    font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
                    }
                    QComboBox::drop-down {
                    width: 47px;
                    border: 0px;
                    color:white;
                    }
                    QComboBox::down-arrow {
                    width: 2px;
                    height: 2px;
                    }""")
            except NameError as e:
                print(e)
        
            gui.btn30.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")

            gui.btn2.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")

            gui.btn3.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")
            
            gui.btn10.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""") 
            
            gui.chk.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            font-size:9px;
            padding: 1px 1px 1px 1px;
            font:bold 12px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""") 

            gui.comboBox20.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")

            gui.comboBox30.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")

            gui.btnOpt.setStyleSheet("""QComboBox {
            min-height:20px;
            max-height:63px;
            border-radius: 3px;
            font-size:10px;
            padding: 1px 1px 1px 1px;
            font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
            }
            QComboBox::drop-down {
            width: 47px;
            border: 0px;
            color:black;
            }
            QComboBox::down-arrow {
            width: 2px;
            height: 2px;
            }""")
            
            gui.label_torrent_stop.setStyleSheet("""
            QToolTip {
            font : Bold 10px;
            color: white;
            background:rgba(157, 131, 131, 80%)
            }
                """)
            
            gui.label_down_speed.setStyleSheet("""
            QToolTip {
            font : Bold 10px;
            color: white;
            background:rgba(157, 131, 131, 80%)
            }
                """)
            
            gui.label_up_speed.setStyleSheet("""
            QToolTip {
            font : Bold 10px;
            color: white;
            background:rgba(157, 131, 131, 80%)
            }""")
        elif widget == gui.list2 and (theme is None or theme in ['default', 'transparent', 'mix']):
            if gui.list_with_thumbnail:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}
                QListWidget:item {height: 128px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
            else:
                gui.list2.setStyleSheet("""QListWidget{font: bold 12px;
                color:white;background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}
                QListWidget:item {height: 30px;}
                QListWidget:item:selected:active {background:rgba(0, 0, 0, 20%);
                color: violet;}
                QListWidget:item:selected:inactive {border:rgba(0, 0, 0, 30%);}
                QMenu{font: 12px;color:black;
                background-image:url('1.png');}""")
        elif theme == 'system':
            if widget == gui.list2:
                gui.list2.setAlternatingRowColors(True)
                if gui.list_with_thumbnail:
                    gui.list2.setStyleSheet("""QListWidget{
                    border-radius:3px;
                    }
                    
                    QListWidget:item {
                    height: 128px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
                else:
                    gui.list2.setStyleSheet("""QListWidget{
                    border-radius:3px;
                    }
                    
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
            else:
                gui.progressEpn.setStyleSheet("""QProgressBar{
                text-align: center;
                }
                """)
                gui.list_poster.setStyleSheet("""
                QListWidget:item {
                height: 256px;
                width:128px;
                }
                """)
                gui.VerticalLayoutLabel_Dock3.setSpacing(0)
                gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
                for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6]:
                    widget.setAlternatingRowColors(True)
                    widget.setStyleSheet("""QListWidget{
                    border-radius:3px;
                    }
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 10%);
                    color: green;
                    }
                    """)
                gui.list2.setAlternatingRowColors(True)
                if gui.list_with_thumbnail:
                    gui.list2.setStyleSheet("""QListWidget{
                    border-radius:3px;
                    }
                    
                    QListWidget:item {
                    height: 128px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
                else:
                    gui.list2.setStyleSheet("""QListWidget{
                    border-radius:3px;
                    }
                    
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
        elif theme == 'dark':
            if widget == gui.list2:
                if gui.list_with_thumbnail:
                    gui.list2.setStyleSheet("""QListWidget{
                    color:white;background:rgb(56,60,74);
                    }
                    
                    QListWidget:item {
                    height: 128px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
                else:
                    gui.list2.setStyleSheet("""QListWidget{
                    color:white;background:rgb(56,60,74);
                    }
                    
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
            else:
                for widget in [gui.line, gui.text, gui.frame1, gui.frame, gui.torrent_frame, gui.float_window]: 
                    widget.setStyleSheet("""
                    color:white;background:rgb(56,60,74);border:rgb(56,60,74);
                    """)
                    
                for frame in [gui.frame2, gui.frame_web, gui.dockWidget_3]:
                    frame.setStyleSheet("""
                        QFrame{color:white;background:rgb(56,60,74);border:rgb(56,60,74);}
                        QPushButton{color:white;background:rgb(56,60,74); max-height:30px;border:rgba(0, 0, 0, 30%);border-radius:3px;}
                        QPushButton::hover{background-color: yellow;color: black;}
                        QPushButton:pressed{background-color: violet;}
                        QLineEdit{color:white;background:rgb(56,60,74); max-height:30px;border:rgba(0, 0, 0, 30%);border-radius:3px;}
                        QComboBox {
                        selection-color:yellow;color:black;background:rgb(56,60,74);
                        border:rgba(0, 0, 0, 30%);border-radius:3px;
                        }
                        QComboBox::hover{background-color: yellow;color: black;}
                        QComboBox::drop-down {
                        width: 47px;
                        border: 2px;
                        color:black;
                        }
                        QComboBox::focus {
                        color:yellow;
                        }
                        QComboBox::down-arrow {
                        width: 2px;
                        height: 2px;
                        }""")
                gui.player_opt.setStyleSheet("""
                    QFrame{color:white;background:rgb(56,60,74);}
                    QPushButton{max-height:30px;border:rgba(0, 0, 0, 30%);border-radius:3px;}
                    QPushButton::hover{background-color: yellow;color: black;}
                    QPushButton:pressed{background-color: violet;}""")
               
                gui.tab_6.setStyleSheet("""color:white;
                    background:rgb(56,60,74);border:rgb(56,60,74);""")
                gui.tab_5.setStyleSheet("""color:white;
                    background:rgb(56,60,74);border:rgb(56,60,74);""")
                
                gui.progress.setStyleSheet("""QProgressBar{
                background:rgb(56,60,74);
                color:white;
                border-radius: 1px;
                text-align: center;}
                QProgressBar:chunk {
                background-color: rgb(56,60,74);
                width: 10px;
                margin: 0.5px;
                }}
                """)
                
                gui.progressEpn.setStyleSheet("""QProgressBar{
                background:rgb(56,60,74);
                color:white;
                border-radius: 1px;
                text-align: center;
                }
                
                QProgressBar:chunk {
                background-color: rgb(56,60,74);
                width: 10px;
                margin: 0.5px;
                }}""")
                
                gui.list_poster.setStyleSheet("""
                QListWidget{
                color:white;background:rgb(56,60,74);border:rgb(56,60,74);
                }
                QListWidget:item {
                height: 256px;
                width:128px;
                }
                """)
                gui.VerticalLayoutLabel_Dock3.setSpacing(0)
                gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
                for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6]:
                    widget.setStyleSheet("""QListWidget{
                    color:white;background:rgb(56,60,74);border:rgb(56,60,74);
                    }
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 10%);
                    color: green;
                    }
                    """)
                if gui.list_with_thumbnail:
                    gui.list2.setStyleSheet("""QListWidget{
                    color:white;background:rgb(56,60,74);border:rgb(56,60,74);
                    }
                    
                    QListWidget:item {
                    height: 128px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
                else:
                    gui.list2.setStyleSheet("""QListWidget{
                    color:white;background:rgb(56,60,74);border:rgb(56,60,74);
                    }
                    
                    QListWidget:item {
                    height: 30px;
                    }
                    QListWidget:item:selected:active {
                    background:rgba(0, 0, 0, 20%);
                    color: green;
                    }
                    """)
