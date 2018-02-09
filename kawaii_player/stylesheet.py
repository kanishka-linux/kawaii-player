import os


class WidgetStyleSheet:
    
    def __init__(self, ui_widet, hm, base, mw, dsession=None):
        global gui, home, BASEDIR, desktop_session, MainWindow
        gui = ui_widet
        home = hm
        BASEDIR = base
        MainWindow = mw
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
        if gui.list_with_thumbnail:
            height = '128px'
        else:
            height = '30px'
        if gui.player_theme in ['default', 'transparent', 'mix']:
            gui.list2.setStyleSheet("""
                QListWidget{{font: bold 12px;
                color:{1};background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}}
                QListWidget:item {{height: {0};}}
                QListWidget:item:selected:active {{background:rgba(0, 0, 0, 20%);
                color: {2};}}
                QListWidget:item:selected:inactive {{border:rgba(0, 0, 0, 30%);}}
                QMenu{{font: 12px;color:black;
                background-image:url('1.png');}}
                """.format(height, gui.list_text_color, gui.list_text_color_focus))
        elif gui.player_theme == 'system':
            gui.list2.setAlternatingRowColors(True)
            gui.list2.setStyleSheet("""QListWidget{{
                border-radius:3px;
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {1};
                }}
                """.format(height, gui.list_text_color_focus))
        elif gui.player_theme == 'dark':
            gui.list2.setStyleSheet("""
                QListWidget{{
                color:{1};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {2};
                }}
                QMenu{{
                color: white;
                background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 2px;
                }}
                QMenu::item{{
                color: white;
                background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 4px; margin: 2px 2px 2px 10px;
                }}
                QMenu::item:selected{{
                color: white;
                background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                }}
                """.format(height, gui.list_text_color, gui.list_text_color_focus))
                
    def qmenu_style(self, widget):
        widget.setStyleSheet("""
            QMenu{
            color: white;
            background: rgb(56,60,74);border: rgba(0,0,0, 30%);
            padding: 2px;
            }
            QMenu::item{
            color: white;
            background:rgb(56,60,74);border: rgba(0,0,0, 30%);
            padding: 4px; margin: 2px 2px 2px 10px;
            }
            QMenu::item:selected{
            color: white;
            background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
            }
            """)
                
    def webStyle(self, web):
        global desktop_session, gui
        try:
            if desktop_session.lower() != 'plasma':
                if gui.player_theme == 'dark':
                    web.setStyleSheet(
                        """
                        QMenu{
                        color: white;
                        background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                        padding: 2px;
                        }
                        QMenu::item{
                        color: white;
                        background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                        padding: 2px; margin: 2px 2px 2px 10px;
                        }
                        QMenu::item:selected{
                        color: white;
                        background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                        }
                        """)
                else:
                    web.setStyleSheet(
                        """QMenu{color:black;
                        background-image:url('1.png');}""")
        except NameError as e:
            print(e)
            desktop_session = 'lxde'
            
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
            gui.slider.setStyleSheet("""
                QSlider:groove:horizontal {
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
            gui.list_poster.setStyleSheet("""
                QListWidget{{
                font: Bold 12px;color:{0};
                background:rgba(0, 0, 0, 50%);border:rgba(0, 0, 0, 50%);
                }}
                QListWidget:item {{
                height: 256px;
                width: 128px;
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 60%);
                color: {1};
                }}
                QListWidget:item:selected:inactive {{
                border:rgba(0, 0, 0, 30%);
                }}
                QMenu{{
                    font: 12px;color:black;background-image:url('1.png');
                }}
                """.format(gui.thumbnail_text_color, gui.thumbnail_text_color_focus))
            for widget in [gui.scrollArea, gui.scrollArea1]:
                widget.setStyleSheet("""
                    QListWidget{
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
            for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6]:
                widget.setStyleSheet("""
                    QListWidget{{
                    font: bold 12px;color:{0};background:rgba(0, 0, 0, 30%);
                    border:rgba(0, 0, 0, 30%);border-radius: 3px;
                    }}
                    QListWidget:item {{
                    height: 30px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 20%);
                    color: {1};
                    }}
                    QListWidget:item:selected:inactive {{
                    border:rgba(0, 0, 0, 30%);
                    }}
                    QMenu{{
                        font: 12px;color:black;background-image:url('1.png');
                    }}
                    """.format(gui.list_text_color, gui.list_text_color_focus))
            if gui.list_with_thumbnail:
                ht = '128px'
            else:
                ht = '30px'
            gui.list2.setStyleSheet(
                """
                QListWidget{{font: bold 12px;
                color:{1};background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}}
                QListWidget:item {{height: {0};}}
                QListWidget:item:selected:active {{background:rgba(0, 0, 0, 20%);
                color: {2};}}
                QListWidget:item:selected:inactive {{border:rgba(0, 0, 0, 30%);}}
                QMenu{{font: 12px;color:black;
                background-image:url('1.png');}}
                """.format(ht, gui.list_text_color, gui.list_text_color_focus))
            for widget in [gui.progress, gui.progressEpn]:
                widget.setStyleSheet("""QProgressBar{
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
            
            for widget in ([gui.btn1, gui.btnAddon, gui.comboView,
                            gui.btn30, gui.btn2, gui.btn3, gui.btn10,
                            gui.chk, gui.comboBox20, gui.comboBox30,
                            gui.btnOpt]):
                widget.setStyleSheet("""
                    QComboBox {
                    min-height:20px;
                    max-height:63px;
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
            
            for widget in [gui.label_torrent_stop, gui.label_down_speed, gui.label_up_speed]:
                widget.setStyleSheet("""
                QToolTip {
                font : Bold 10px;
                color: white;
                background:rgba(157, 131, 131, 80%)
                }
                """)
        elif widget == gui.list2 and (theme is None or theme in ['default', 'transparent', 'mix']):
            if gui.list_with_thumbnail:
                ht = '128px'
            else:
                ht = '30px'
            gui.list2.setStyleSheet("""
                QListWidget{{font: bold 12px;
                color:{1};background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}}
                QListWidget:item {{height: {0};}}
                QListWidget:item:selected:active {{background:rgba(0, 0, 0, 20%);
                color: {2};}}
                QListWidget:item:selected:inactive {{border:rgba(0, 0, 0, 30%);}}
                QMenu{{font: 12px;color:black;
                background-image:url('1.png');}}
                """.format(ht, gui.list_text_color, gui.list_text_color_focus))
        elif theme == 'system':
            if widget == gui.list2:
                if gui.list_with_thumbnail:
                    ht = '128px'
                else:
                    ht = '30px'
                gui.list2.setAlternatingRowColors(True)
                gui.list2.setStyleSheet("""QListWidget{{
                border-radius:3px;
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {1};
                }}
                """.format(ht, gui.list_text_color_focus))
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
                    widget.setStyleSheet("""QListWidget{{
                    border-radius:3px;
                    }}
                    QListWidget:item {{
                    height: 30px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 10%);
                    color: {0};
                    }}
                    """.format(gui.list_text_color_focus))
                gui.list2.setAlternatingRowColors(True)
                if gui.list_with_thumbnail:
                    ht = '128px'
                else:
                    ht = '30px'
                gui.list2.setAlternatingRowColors(True)
                gui.list2.setStyleSheet("""QListWidget{{
                border-radius:3px;
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {1};
                }}
                """.format(ht, gui.list_text_color_focus))
        elif theme == 'dark':
            #gui.list_text_color = 'lightgray'
            #gui.thumbnail_text_color = 'lightgray'
            if gui.list_with_thumbnail:
                height = '128px'
            else:
                height = '30px'
            gui.list2.setStyleSheet("""QListWidget{{
                color:{1};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {2};
                }}
                QMenu{{
                color: white;
                background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 2px;
                }}
                QMenu::item{{
                color: {1};
                background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 4px; margin: 2px 2px 2px 10px;
                }}
                QMenu::item:selected{{
                color: {2};
                background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                }}
                """.format(height, gui.list_text_color, gui.list_text_color_focus))
            if widget != gui.list2:
                for widget_item in ([gui.line, gui.text, gui.frame1, gui.frame,
                                gui.torrent_frame, gui.float_window,
                                gui.search_on_type_btn, gui.tab_6, gui.tab_5]): 
                    if widget_item == gui.tab_6:
                        alpha = '20%'
                    else:
                        alpha = '30%'
                    widget_item.setStyleSheet("""
                        color:{color};
                        background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});
                        """.format(alpha=alpha, color=gui.list_text_color))
                for frame in [gui.frame2, gui.frame_web, gui.dockWidget_3, gui.goto_epn]:
                    bg = '30%'
                    if frame == gui.dockWidget_3:
                        qbtn = '50%'
                    else:
                        qbtn = '10%'
                    frame.setStyleSheet("""
                        QFrame{{color:white;background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});}}
                        QPushButton{{color:{color};background:rgba(0,0,0,{btn});border:rgba(0,0,0,{btn});max-height:30px;}}
                        QPushButton::hover{{background-color: yellow;color: black;}}
                        QPushButton:pressed{{background-color: violet;}}
                        QLineEdit{{color:white;background:rgba(0,0,0,10%);
                        max-height:30px;border:rgba(0, 0, 0, 10%);}}
                        QLabel{{color:{color};background:rgba(0,0,0,10%);
                        max-height:30px;border:rgba(0, 0, 0, 10%);}}
                        QComboBox {{
                        color: {color};
                        selection-color:yellow;background:rgba(0,0,0,{btn});
                        border:rgba(0, 0, 0, 10%);
                        }}
                        QComboBox::hover{{background-color: rgba(0,0,0,60%);color: {color};}}
                        QComboBox::drop-down {{
                        width: 47px;
                        border: 2px;
                        color:white;
                        }}
                        QComboBox::focus {{
                        background-color:rgba(0,0,0,60%);color: {focus};
                        }}
                        QComboBox::down-arrow {{
                        width: 2px;
                        height: 2px;
                        }}""".format(
                            alpha=bg, btn=qbtn, color=gui.list_text_color,
                            focus=gui.list_text_color_focus)
                        )
                gui.player_opt.setStyleSheet("""
                    QFrame{color:white;background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);}
                    QPushButton{max-height:30px;border:rgba(0, 0, 0, 30%)}
                    QPushButton::hover{background-color: yellow;color: black;}
                    QPushButton:pressed{background-color: violet;}""")
                
                for widget in [gui.progress, gui.progressEpn]:
                    widget.setStyleSheet("""QProgressBar{
                    color:white;
                    background:rgba(0, 0, 0, 30%);
                    border:rgba(0, 0, 0, 1%) ;
                    border-radius: 1px;
                    text-align: center;}
                    
                    QProgressBar:chunk {
                    background-color:rgba(0,0,0,30%);
                    width: 10px;
                    margin: 0.5px;
                    }}""")
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
                gui.list_poster.setStyleSheet("""
                    QListWidget{{
                    color:{0};
                    background:rgba(0, 0, 0, 35%);border:rgba(0, 0, 0, 35%);
                    }}
                    QListWidget:item {{
                    height: 256px;
                    width:128px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 30%);
                    color: {1};
                    }}
                    QMenu{{
                    color: white;
                    background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 2px;
                    }}
                    QMenu::item{{
                    color: {0};
                    background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 4px; margin: 2px 2px 2px 10px;
                    }}
                    QMenu::item:selected{{
                    color: {1};
                    background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                    }}
                    """.format(gui.thumbnail_text_color, gui.thumbnail_text_color_focus))
                gui.VerticalLayoutLabel_Dock3.setSpacing(0)
                gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
                for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6]:
                    widget.setStyleSheet("""QListWidget{{
                    color:{0};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                    }}
                    QListWidget:item {{
                    height: 30px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 20%);
                    color: {1};
                    }}
                    QListWidget:item:selected:focus {{
                    background:rgba(0, 0, 0, 20%);
                    color: {1};
                    }}
                    QMenu{{
                    color: white;
                    background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 2px;
                    }}
                    QMenu::item{{
                    color: {0};
                    background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 4px; margin: 2px 2px 2px 10px;
                    }}
                    QMenu::item:selected{{
                    color: {1};
                    background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                    }}
                    """.format(gui.list_text_color, gui.list_text_color_focus))
