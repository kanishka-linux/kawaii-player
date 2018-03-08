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
        if gui.font_bold:
            font_bold = 'bold'
        else:
            font_bold = ''
        if gui.player_theme in ['default', 'transparent', 'mix']:
            gui.list2.setStyleSheet("""
                QListWidget{{font: {bold};
                color:{1};background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius: 3px;}}
                QListWidget:item {{height: {0};}}
                QListWidget:item:selected:active {{background:rgba(0, 0, 0, 20%);
                color: {2};}}
                QListWidget:item:selected:inactive {{border:rgba(0, 0, 0, 30%);}}
                QMenu{{color:black;
                background-image:url('1.png');}}
                """.format(height, gui.list_text_color, gui.list_text_color_focus,bold=font_bold))
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
                font: {bold} {font};
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {2};
                }}
                
                QListWidget:item:inactive {{
                color:{1};background:rgba(0,0,0,0%);border:rgba(0,0,0,0%);
                font: {bold} {font};
                }}
                
                QMenu{{
                color: white;
                background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 2px;
                }}
                QMenu::item{{
                color: {1};
                font: {font};
                background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 4px; margin: 2px 2px 2px 10px;
                }}
                QMenu::item:selected{{
                color: {2};
                background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                }}
                """.format(height, gui.list_text_color, gui.list_text_color_focus,
                           bold=font_bold, font=gui.global_font)
                        )
                
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
        if gui.font_bold:
            font_bold = 'bold'
        else:
            font_bold = ''
        if not widget and (theme is None or theme in ['default', 'transparent', 'mix']):
            #gui.VerticalLayoutLabel_Dock3.setSpacing(0)
            alpha = '30%'
            qbtn = '10%'
            #gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
            for widget in [gui.tab_2, gui.tab_5, gui.tab_6, gui.go_opt,
                           gui.text, gui.text_save_btn, gui.search_on_type_btn,
                           gui.frame, gui.frame1, gui.torrent_frame, gui.float_window]:
                if widget in [gui.text_save_btn, gui.search_on_type_btn, gui.frame1]:
                    alpha = '60%'
                else:
                    alpha = '30%'
                if widget == gui.frame1:
                    font_size = '11px'
                    if not font_bold:
                        font_size = ''
                else:
                    font_size = ''
                widget.setStyleSheet("""
                    font:{bold} {font_size};color:{color};
                    background:rgba(0, 0, 0, {alpha});border:rgba(0, 0, 0, 30%);
                    """.format(alpha=alpha, bold=font_bold,
                               color=gui.list_text_color, font_size=font_size))
            for frame in [gui.frame2, gui.frame_web, gui.dockWidget_3,
                          gui.goto_epn, gui.btnWebReviews,
                          gui.frame_extra_toolbar.child_frame,
                          gui.frame_extra_toolbar.tab_frame,
                          gui.frame_extra_toolbar.subtitle_frame]:
                if frame == gui.dockWidget_3:
                    alpha = '40%'
                else:
                    alpha = '30%'
                if frame in [gui.frame_extra_toolbar.child_frame,
                            gui.frame_extra_toolbar.tab_frame,
                            gui.frame_extra_toolbar.subtitle_frame]:
                    label_alpha = '0%'
                    #min_height = 'height: 32px'
                    new_height = int(gui.frame_height/2.4)
                    min_height = 'height: {}px'.format(new_height)
                    gui.logger.debug('min-height-box={}'.format(min_height))
                else:
                    label_alpha = '30%'
                    min_height = ''
                frame.setStyleSheet("""
                    QFrame{{background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);}}
                    QPushButton{{
                        background:rgba(0, 0, 0, {alpha});border:rgba(0, 0, 0, {alpha});
                        color: {color}; font: {bold};
                        {min_height};
                        }}
                    QPushButton::hover{{background-color: yellow;color: black;}}
                    QPushButton:pressed{{background-color: violet;}}
                    QLineEdit{{
                        font:{bold};color:white;background:rgba(0,0,0,30%);
                        {min_height};border:rgba(0, 0, 0, 30%);}}
                    QTextEdit{{
                        font:{bold};color:{color};background:rgba(0,0,0,30%);
                        border:rgba(0, 0, 0, 30%);}}
                    QLabel{{
                        background:rgba(0, 0, 0, {label_alpha});
                        border:rgba(0, 0, 0, {label_alpha});color: {color}; font:{bold};
                        {min_height};
                        }}
                    QComboBox {{
                    selection-color:yellow;
                    border: rgba(0, 0, 0, 30%);
                    color: {color};
                    font: {bold};
                    background-color:rgba(0, 0, 0, {alpha});
                    max-height: 32px;
                    padding: 0px 0px 0px 4px;
                    }}
                    QComboBox QAbstractItemView{{
                        background-color: rgba(0,0,0,{alpha});
                        border-radius: 0px;
                        color: {color};
                        font: {bold};
                     }}
                    QComboBox::hover{{background-color: rgba(0, 0, 0, 50%);color: {focus};}}
                    QComboBox::drop-down {{
                    width: 22px;
                    border: 0px;
                    color:black;
                    }}
                    QComboBox::focus {{
                    color:{focus};
                    }}
                    QComboBox::focus {{
                        background-color:rgba(0,0,0,50%);color: {focus};
                    }}
                    
                    QComboBox::down-arrow {{
                    width: 2px;
                    height: 2px;
                    }}
                    
                    QSlider:groove:horizontal {{
                    height: 8px;
                    border:rgba(0, 0, 0, 30%);
                    background:rgba(0, 0, 0, 30%);
                    margin: 2px 0;
                    }}
                    QSlider:handle:horizontal {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 8px;
                    margin: -2px 0; 
                    border-radius: 3px;
                    }}
                    QToolTip {{
                    font : {bold} {size}px {font};
                    color: black;
                    background:rgb(54, 60, 74);
                    }}
                    
                    QCheckBox{{
                    color:{color};background:rgba(0,0,0,0%);
                    border:rgba(0, 0, 0, 10%); font: {bold} {font};
                    {min_height};
                    }}
                    QDoubleSpinBox{{
                    color:{color};background:rgba(0,0,0,{alpha});
                    border:rgba(0, 0, 0, 10%); font: {bold} {font};
                    {min_height};
                    }}
                    QDoubleSpinBox::up-button{{
                            max-height:32px;
                        }}
                    QDoubleSpinBox::down-button{{
                        max-height:32px;
                        }}
                    """.format(
                        color=gui.list_text_color, focus=gui.list_text_color_focus,
                        alpha=alpha, bold=font_bold, font=gui.global_font,
                        size=gui.global_font_size, label_alpha=label_alpha,
                        min_height=min_height
                        )
                    )
            gui.player_opt.setStyleSheet("""
                QFrame{background:rgba(0, 0, 0, 0%);border:rgba(0, 0, 0, 0%);}
                QPushButton{border-radius:0px;max-height:30px;}
                QPushButton::hover{background-color: yellow;color: black;}
                QPushButton:pressed{background-color: violet;}""")
            
            
            gui.settings_box.setStyleSheet("""
                    QFrame{{color:white;background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});}}
                    QTabWidget{{
                        color:{color};
                        border:rgba(0,0,0,{alpha});background:rgb(56,60,74);
                        background-color:rgba(0,0,0,{alpha});
                        }}
                    QTabWidget:pane {{
                        color:{color};font: {bold} {font};
                        border:rgba(0,0,0,{alpha});background:rgba(56,60,74, {alpha});
                    }}
                    
                    QTabBar {{
                        color:{color};font: {bold} {font};
                        border:rgba(0,0,0,{alpha});background:rgba(56,60,74, {alpha});
                        background-color:rgba(0,0,0,{alpha});
                    }}
                    
                    QTabBar:tab{{
                        color:{color};background:rgba(56,60,74, {alpha});
                    }}
                    
                    QTabBar:tab:selected{{
                        color:{color};background:rgba(0,0,0, 20%);
                    }}
                    
                    QListWidget{{
                        color:{color};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                        font: {bold} {font};
                    }}
                    QListWidget:item {{
                        height: 30px;
                    }}
                    QListWidget:item:selected:active {{
                        background:rgba(0, 0, 0, 20%);
                        color: {focus};
                    }}
                    
                    QPushButton{{color:{color};background:rgba(0,0,0,{btn});border:rgba(0,0,0,{btn});
                    max-height:40px; font: {bold};}}
                    QPushButton::hover{{background-color: yellow;color: black;}}
                    QPushButton:pressed{{background-color: violet;}}
                    QLineEdit{{color:{color};background:rgba(0,0,0,10%);
                    max-height:40px;border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                    QTextEdit{{color:{color};background:rgba(0,0,0,10%);
                    border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                    
                    QScrollBar{{ background: rgba(0,0,0,30%);
                    }}
                    
                    QScrollBar::handle{{ background: rgba(0,0,0, {btn});
                    border-radius:4px;
                    }}
                    
                    QScrollBar::add-line{{ background: rgba(0,0,0,0%);
                    }}
                    
                    QScrollBar::sub-line{{ background: rgba(0,0,0,0%);
                    }}
                    
                    QCheckBox{{color:{color};background:rgba(0,0,0,10%);
                        border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                    
                    QLabel{{color:{color};background:rgba(0,0,0,0%);
                    max-height:40px;border:rgba(0, 0, 0, 10%);font: {bold} {font};}}
                    QComboBox {{
                    color: {color};
                    selection-color:yellow;background:rgba(0,0,0,{btn});
                    border:rgba(0, 0, 0, 10%);
                    padding: 2px 0px 2px 4px;
                    font: {bold};
                    max-height: 40px;
                    }}
                    QComboBox QAbstractItemView{{
                        background-color: rgba(54,60,74);
                        border-radius: 0px;
                        color: {color};
                        font: {bold} {font};
                     }}
                    QComboBox::hover{{background-color: rgba(0,0,0,40%);color: {color};}}
                    QComboBox::drop-down {{
                    width: 22px;
                    border: 2px;
                    color:white;
                    }}
                    QComboBox::focus {{
                    background-color:rgba(0,0,0,40%);color: {focus};
                    }}
                    QComboBox::down-arrow {{
                    width: 2px;
                    height: 2px;
                    }}
                    """.format(
                        alpha=alpha, btn=qbtn, color=gui.list_text_color,
                        focus=gui.list_text_color_focus, bold=font_bold,
                        size=gui.global_font_size, font=gui.global_font)
                    )
            
            gui.slider.setStyleSheet("""
                QSlider:groove:horizontal {{
                height: 8px;
                border:rgba(0, 0, 0, 30%);
                background:rgba(0, 0, 0, 30%);
                margin: 2px 0;
                }}
                QSlider:handle:horizontal {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 2px;
                margin: -2px 0; 
                border-radius: 3px;
                }}
                QToolTip {{
                font : {bold} {size}px {font};
                color: {color};
                background:rgb(54, 60, 74);
                }}
                """.format(
                        color=gui.list_text_color, bold=font_bold,
                        size=gui.global_font_size+3, font=gui.global_font
                        )
                    )
            gui.list_poster.setStyleSheet("""
                QListWidget{{
                font: {bold};color:{0};
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
                """.format(gui.thumbnail_text_color, gui.thumbnail_text_color_focus, bold=font_bold))
            for widget in [gui.scrollArea, gui.scrollArea1]:
                widget.setStyleSheet("""
                    QListWidget{{
                    font: {bold} ;color:white;
                    background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);border-radius: 3px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 20%);
                    color: yellow;
                    }}
                    QListWidget:item:selected:inactive {{
                    border:rgba(0, 0, 0, 30%);
                    }}
                    QMenu{{
                        font: 12px;color:black;background-image:url('1.png');
                    }}
                    """.format(bold=font_bold))
            for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6]:
                if widget == gui.list3:
                    border = '0px'
                else:
                    border = '3px'
                widget.setStyleSheet("""
                    QListWidget{{
                    font: {bold};color:{0};background:rgba(0, 0, 0, 30%);
                    border:rgba(0, 0, 0, 30%);border-radius: {2};
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
                    """.format(gui.list_text_color, gui.list_text_color_focus, border,bold=font_bold))
            if gui.list_with_thumbnail:
                ht = '128px'
            else:
                ht = '30px'
            gui.list2.setStyleSheet(
                """
                QListWidget{{
                font: {bold}; color:{1};background:rgba(0, 0, 0, 30%);
                border:rgba(0, 0, 0, 30%);border-radius:3px;}}
                QListWidget:item {{height: {0};}}
                QListWidget:item:selected:active {{background:rgba(0, 0, 0, 20%);
                color: {2};}}
                QListWidget:item:selected:inactive {{border:rgba(0, 0, 0, 30%);}}
                QMenu{{font: 12px;color:black;
                background-image:url('1.png');}}
                """.format(ht, gui.list_text_color, gui.list_text_color_focus, bold=font_bold))
            for widget in [gui.progress, gui.progressEpn]:
                widget.setStyleSheet("""QProgressBar{{
                    font: {bold};
                    color:{color};
                    background:rgba(0, 0, 0, 30%);
                    border:rgba(0, 0, 0, 1%) ;
                    border-radius: 1px;
                    text-align: center;}}
                    
                    QProgressBar:chunk {{
                    background-color: rgba(255, 255, 255, 30%);
                    width: 10px;
                    margin: 0.5px;
                    }}""".format(bold=font_bold, color=gui.list_text_color))
            
            for widget in ([gui.btn30, gui.btn2, gui.btn3, gui.btn10,
                            gui.comboBox20, gui.comboBox30, gui.btnOpt]):
                widget.setStyleSheet("""
                    QComboBox {
                    min-height:30px;
                    max-height:63px;
                    padding: 1px 1px 1px 1px;
                    font:bold 10px;background:rgba(0, 0, 0, 30%);border:rgba(0, 0, 0, 30%);
                    selection-color:yellow;
                    }
                    QComboBox::drop-down {
                    width: 22px;
                    border: 0px;
                    color:black;
                    }
                    QComboBox::hover{background-color: lightgray;color: white;}
                    QComboBox::focus {
                        background-color:rgba(0,0,0,60%);color: white;
                    }
                    QComboBox::down-arrow {
                    width: 2px;
                    height: 2px;
                    }""")
            
            for widget in [gui.label_torrent_stop, gui.label_down_speed, gui.label_up_speed]:
                widget.setStyleSheet("""
                QToolTip {{
                font : {bold} {size}px {font};
                color: {color};
                background:rgb(56,60,74);
                }}
                """.format(bold=font_bold, font=gui.global_font,
                           size=gui.global_font_size+3, color=gui.list_text_color)
                        )
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
                #gui.VerticalLayoutLabel_Dock3.setSpacing(0)
                #gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
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
            alpha = '30%'
            qbtn = '10%'
            if gui.list_with_thumbnail:
                height = '128px'
            else:
                height = '30px'
            gui.list2.setStyleSheet("""QListWidget{{
                color:{1};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                font: {bold} ;
                }}
                QListWidget:item {{
                height: {0};
                }}
                QListWidget:item:selected:active {{
                background:rgba(0, 0, 0, 20%);
                color: {2};
                }}
                QListWidget:item:inactive {{
                    color:{1};background:rgba(0,0,0,0%);border:rgba(0,0,0,0%);
                    font: {bold} ;
                    }}
                QMenu{{
                color: white;
                background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 2px;
                }}
                QMenu::item{{
                font: {font};
                color: {1};
                background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                padding: 4px; margin: 2px 2px 2px 10px;
                }}
                QMenu::item:selected{{
                color: {2};
                background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                }}
                """.format(height, gui.list_text_color, gui.list_text_color_focus,
                           bold=font_bold, font=gui.global_font)
                        )
            if widget != gui.list2:
                for widget_item in ([gui.line, gui.text, gui.frame1, gui.frame,
                                gui.torrent_frame, gui.float_window,
                                gui.search_on_type_btn, gui.tab_6, gui.tab_5]): 
                    if widget_item == gui.tab_6:
                        alpha = '20%'
                    else:
                        alpha = '30%'
                    if widget == gui.frame1:
                        font_size = '11px'
                        if not font_bold:
                            font_size = ''
                    else:
                        font_size = ''
                    widget_item.setStyleSheet("""
                        color:{color};
                        font: {bold} {size};
                        background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});
                        """.format(alpha=alpha, color=gui.list_text_color, bold=font_bold, size=font_size))
                for frame in [gui.frame2, gui.frame_web, gui.dockWidget_3, gui.goto_epn,
                        gui.frame_extra_toolbar.child_frame, gui.frame_extra_toolbar.tab_frame,
                        gui.frame_extra_toolbar.subtitle_frame]:
                    bg = '30%'
                    if frame == gui.dockWidget_3:
                        qbtn = '50%'
                    else:
                        qbtn = '10%'
                    if frame in [gui.frame_extra_toolbar.child_frame,
                                 gui.frame_extra_toolbar.tab_frame,
                                 gui.frame_extra_toolbar.subtitle_frame]:
                        label_alpha = '0%'
                        new_height = int(gui.frame_height/2.4)
                        min_height = 'height: {}px'.format(new_height)
                        gui.logger.debug('min-height-box={}'.format(min_height))
                    else:
                        label_alpha = '10%'
                        min_height = 'max-height: 30px'
                        
                    frame.setStyleSheet("""
                        QFrame{{color:white;background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});}}
                        QPushButton{{color:{color};background:rgba(0,0,0,{btn});border:rgba(0,0,0,{btn});
                        {min_height}; font: {bold};}}
                        QPushButton::hover{{background-color: yellow;color: black;}}
                        QPushButton:pressed{{background-color: violet;}}
                        QLineEdit{{
                            color:white;background:rgba(0,0,0,10%);
                            {min_height};border:rgba(0, 0, 0, 10%); font: {bold}
                            }}
                        QLabel{{
                            color:{color};background:rgba(0,0,0,{label_alpha});
                            {min_height};border:rgba(0, 0, 0, {label_alpha});font: {bold};
                            }}
                        QComboBox {{
                        color: {color};
                        selection-color:yellow;background:rgba(0,0,0,{btn});
                        border:rgba(0, 0, 0, 10%);
                        padding: 2px 0px 2px 4px;
                        font: {bold};
                        }}
                        QComboBox::hover{{background-color: rgba(0,0,0,60%);color: {color};}}
                        QComboBox::drop-down {{
                        width: 22px;
                        border: 2px;
                        color:white;
                        }}
                        QComboBox QAbstractItemView{{
                        background-color: rgb(54,60,74);
                        border-radius: 0px;
                        color: {color};
                        font: {bold};
                        }}
                        QComboBox::focus {{
                        background-color:rgba(0,0,0,60%);color: {focus};
                        }}
                        QComboBox::down-arrow {{
                        width: 2px;
                        height: 2px;
                        }}
                        
                        QSlider:groove:horizontal {{
                            height: 8px;
                            border:rgba(0, 0, 0, 30%);
                            background:rgba(0, 0, 0, 30%);
                            margin: 2px 0;
                            }}
                        QSlider:handle:horizontal {{
                            background: qlineargradient(
                                x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                            border: 1px solid #5c5c5c;
                            width: 8px;
                            margin: -2px 0; 
                            border-radius: 3px;
                        }}
                        QSlider:QToolTip {{
                            font : {bold} {size}px {font};
                            color: {color};
                            background:rgb(56,60,74);
                            padding: 1px 2px 1px 2px;
                        }}
                        QCheckBox{{
                            color:{color};background:rgba(0,0,0,0%);
                            border:rgba(0, 0, 0, 10%); font: {bold} {font};
                            {min_height};
                            }}
                        QDoubleSpinBox{{
                            color:{color};background:rgba(0,0,0,{btn});
                            border:rgba(0, 0, 0, 10%); font: {bold} {font};
                            {min_height};
                            }}
                        QDoubleSpinBox::up-button{{
                            max-height:32px;
                            }}
                        QDoubleSpinBox::down-button{{
                            max-height:32px;
                            }}
                            
                        QSpinBox{{
                            color:{color};background:rgba(0,0,0,{btn});
                            border:rgba(0, 0, 0, 10%); font: {bold} {font};
                            {min_height};
                            }}
                        QSpinBox::up-button{{
                            max-height:32px;
                            }}
                        QSpinBox::down-button{{
                            max-height:32px;
                            }}
                        """.format(
                            alpha=bg, btn=qbtn, color=gui.list_text_color,
                            focus=gui.list_text_color_focus, bold=font_bold,
                            size=gui.global_font_size, font=gui.global_font,
                            label_alpha=label_alpha, min_height=min_height
                            )
                        )
                gui.player_opt.setStyleSheet("""
                    QFrame{color:white;background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);}
                    QPushButton{max-height:30px;border:rgba(0, 0, 0, 30%)}
                    QPushButton::hover{background-color: yellow;color: black;}
                    QPushButton:pressed{background-color: violet;}""")
                
                gui.settings_box.setStyleSheet("""
                        QFrame{{color:white;background:rgba(0,0,0,{alpha});border:rgba(0,0,0,{alpha});}}
                        QTabWidget{{
                            color:{color};
                            border:rgba(0,0,0,{alpha});background:rgb(56,60,74);
                            background-color:rgba(0,0,0,{alpha});
                            }}
                        QTabWidget:pane {{
                            color:{color};font: {bold} {font};
                            border:rgba(0,0,0,{alpha});background:rgba(56,60,74, {alpha});
                        }}
                        
                        QTabBar {{
                            color:{color};font: {bold} {font};
                            border:rgba(0,0,0,{alpha});background:rgba(56,60,74, {alpha});
                            background-color:rgba(0,0,0,{alpha});
                        }}
                        
                        QTabBar:tab{{
                            color:{color};background:rgba(56,60,74, {alpha});
                        }}
                        
                        QTabBar:tab:selected{{
                            color:{color};background:rgba(0,0,0, 20%);
                        }}
                        
                        QListWidget{{
                            color:{color};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                            font: {bold} {font};
                        }}
                        QListWidget:item {{
                            height: 30px;
                        }}
                        QListWidget:item:selected:active {{
                            background:rgba(0, 0, 0, 20%);
                            color: {focus};
                        }}
                        
                        QPushButton{{color:{color};background:rgba(0,0,0,{btn});border:rgba(0,0,0,{btn});
                        max-height:40px; font: {bold};}}
                        QPushButton::hover{{background-color: yellow;color: black;}}
                        QPushButton:pressed{{background-color: violet;}}
                        QLineEdit{{color:{color};background:rgba(0,0,0,10%);
                        max-height:40px;border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                        QTextEdit{{color:{color};background:rgba(0,0,0,10%);
                        border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                        
                        QCheckBox{{color:{color};background:rgba(0,0,0,10%);
                        border:rgba(0, 0, 0, 10%); font: {bold} {font};}}
                        
                        QScrollBar{{ background: rgba(0,0,0,30%);
                        }}
                        
                        QScrollBar::handle{{ background: rgba(54,60,74,30%);
                        border-radius:4px;
                        }}
                        
                        QScrollBar::add-line{{ background: rgba(0,0,0,0%);
                        }}
                        
                        QScrollBar::sub-line{{ background: rgba(0,0,0,0%);
                        }}
                        
                        QLabel{{color:{color};background:rgba(0,0,0,0%);
                        max-height:40px;border:rgba(0, 0, 0, 10%);font: {bold} {font};}}
                        QComboBox {{
                        color: {color};
                        selection-color:yellow;background:rgba(0,0,0,{btn});
                        border:rgba(0, 0, 0, 10%);
                        padding: 2px 0px 2px 4px;
                        font: {bold};
                        max-height: 40px;
                        }}
                        QComboBox QAbstractItemView{{
                        background-color: rgb(56,60,74);
                        border-radius: 0px;
                        border-color:rgb(56,60,74);
                        color: {color};
                        font: {bold} {font};
                        }}
                        QComboBox::hover{{background-color: rgba(0,0,0,40%);color: {color};}}
                        QComboBox::drop-down {{
                        width: 22px;
                        border: 2px;
                        color:white;
                        }}
                        QComboBox::focus {{
                        background-color:rgba(0,0,0,40%);color: {focus};
                        }}
                        QComboBox::down-arrow {{
                        width: 2px;
                        height: 2px;
                        }}""".format(
                            alpha=bg, btn=qbtn, color=gui.list_text_color,
                            focus=gui.list_text_color_focus, bold=font_bold,
                            size=gui.global_font_size, font=gui.global_font)
                        )
                
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
                gui.slider.setStyleSheet("""QSlider:groove:horizontal {{
                    height: 8px;
                    border:rgba(0, 0, 0, 30%);
                    background:rgba(0, 0, 0, 30%);
                    margin: 2px 0;
                    }}
                    QSlider:handle:horizontal {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    border: 1px solid #5c5c5c;
                    width: 2px;
                    margin: -2px 0; 
                    border-radius: 3px;
                    }}
                    QToolTip {{
                    font : {bold} {size}px {font};
                    color: {color};
                    background:rgb(56,60,74);
                    padding: 1px 2px 1px 2px;
                    }}
                    """.format(
                            alpha=bg, color=gui.list_text_color,
                            bold=font_bold, size=gui.global_font_size+3,
                            font=gui.global_font
                            )
                        )
                gui.list_poster.setStyleSheet("""
                    QListWidget{{
                    color:{0};
                    background:rgba(0, 0, 0, 35%);border:rgba(0, 0, 0, 35%);
                    font: {bold};
                    }}
                    QListWidget:item {{
                    height: 256px;
                    width:128px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 30%);
                    color: {1};
                    }}
                    QListWidget:item:inactive {{
                    color:{0};
                    background:rgba(0, 0, 0, 0%);border:rgba(0, 0, 0, 0%);
                    font: {bold};
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
                    """.format(gui.thumbnail_text_color, gui.thumbnail_text_color_focus, bold=font_bold))
                #gui.VerticalLayoutLabel_Dock3.setSpacing(0)
                #gui.VerticalLayoutLabel_Dock3.setContentsMargins(5, 5, 5, 5)
                for widget in [gui.list1, gui.list3, gui.list4, gui.list5, gui.list6, gui.player_menu]:
                    widget.setStyleSheet("""QListWidget{{
                    color:{0};background:rgba(0,0,0,30%);border:rgba(0,0,0,30%);
                    font: {bold};
                    }}
                    QListWidget:item {{
                    height: 30px;
                    }}
                    QListWidget:item:selected:active {{
                    background:rgba(0, 0, 0, 20%);
                    color: {1};
                    }}
                    
                    QListWidget:item:inactive {{
                    color:{0};background:rgba(0,0,0,0%);border:rgba(0,0,0,0%);
                    font: {bold};
                    }}
                    QMenu{{
                    color: {1};
                    background: rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 2px;
                    }}
                    QMenu::item{{
                    font: {font};
                    color: {0};
                    background:rgb(56,60,74);border: rgba(0,0,0, 30%);
                    padding: 4px; margin: 2px 2px 2px 10px;
                    }}
                    QMenu::item:selected{{
                    color: {1};
                    background:rgba(0, 0, 0, 20%);border: rgba(0,0,0, 30%);
                    }}
                    """.format(gui.list_text_color, gui.list_text_color_focus,
                               bold=font_bold, font=gui.global_font)
                            )
