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
import sqlite3
import datetime
from PyQt5 import QtWidgets
from player_functions import open_files, send_notification

try:
    try:
        import taglib
        SONG_TAGS = 'taglib'
    except Exception as err:
        print(err, '--6--')
        import mutagen
        SONG_TAGS = 'mutagen'
except Exception as err:
    print(err, '--10--')
    SONG_TAGS = None

print(SONG_TAGS, '--tagging-module--')

class MediaDatabase():

    def __init__(self, home=None, logger=None, music_ext=None, video_ext=None):
        self.home = home
        self.logger = logger
        self.music_ext = music_ext
        self.video_ext = video_ext
        self.ui = None
        
    def set_ui(self, ui):
        self.ui = ui
        
    def import_video_dir(self):
        m = []
        o = []
        video = []
        p = []
        vid = []
        if os.path.isfile(os.path.join(self.home, 'local.txt')):
            lines_dir = open_files(os.path.join(self.home, 'local.txt'), True)
            for lines_d in lines_dir:
                video[:] = []
                lines_d = lines_d.strip()
                dirn = os.path.normpath(lines_d)

                video.append(dirn)
                for r, d, f in os.walk(dirn):
                    for z in d:
                        if not z.startswith('.'):
                            video.append(os.path.join(r, z))
                        else:
                            o.append(os.path.join(r, z))

                print(len(m))
                j = 0
                lines = []
                for i in video:
                    if os.path.exists(i):
                        n = os.listdir(i)
                        p[:] = []
                        for k in n:
                            file_ext = k.rsplit('.', 1)[-1]
                            if file_ext.lower() in self.video_ext:
                                p.append(os.path.join(i, k))
                        if p:
                            r = i
                            vid.append(str(r))
                            j = j+1
        return vid
    
    def get_video_db(self, music_db, queryType, queryVal):
        conn = sqlite3.connect(music_db)
        cur = conn.cursor()    
        q = queryType
        qVal = str(queryVal)
        print(music_db)
        error_occured = False
        if q.lower() == "directory":
            if not qVal:
                cur.execute('SELECT distinct Title, Directory FROM Video order by Title')
            else:
                qr = 'SELECT distinct EP_NAME, Path FROM Video Where Directory=? order by EPN'
                cur.execute(qr, (qVal, ))
        elif q.lower() == "bookmark":
            print(q)
            qr = 'SELECT EP_NAME, Path FROM Video Where Title=?'
            cur.execute(qr, (qVal, ))
        elif q.lower() == "history":
            print(q)
            qr = 'SELECT distinct Title, Directory FROM Video Where FileName like ? order by Title'
            qv = '#'+'%'
            self.logger.info('qv={0};qr={1}'.format(qv, qr))
            cur.execute(qr, (qv, ))
        elif q.lower() == "search":
            qVal = '%'+qVal+'%'
            qr = 'SELECT EP_NAME, Path From Video Where EP_NAME like ? or Directory like ? order by Directory'
            self.logger.info('qr={0};qVal={1}'.format(qr, qVal))
            cur.execute(qr, (qVal, qVal, ))
        elif q.lower() == 'recent':
            cur.execute('SELECT distinct Title, Directory FROM Video order by Title')
        else:
            cat_type = self.ui.category_dict.get(q.lower())
            if not cat_type:
                cat_type = self.ui.category_dict['others']
                self.logger.info('Category {} not Available Hence sending Others --123---'.format(q))
            if not qVal:
                try:
                    cur.execute('SELECT distinct Title, Directory FROM Video Where Category=? order by Title', (cat_type,))
                except Exception as err:
                    self.logger.info(err)
                    error_occured = True
                    rows = [('none','none')]
        if not error_occured:
            rows = cur.fetchall()
            if q.lower() in ['history', 'recent']:
                rows_access = []
                rows_not_access = []
                new_arr = []
                for i in rows:
                    if os.path.exists(i[1]):
                        m = os.listdir(i[1])
                        for ii in m:
                            if '.' in ii:
                                _, ext = ii.rsplit('.', 1)
                                file_path = os.path.join(i[1], ii)
                                if ext in self.ui.video_type_arr:
                                    if q.lower() == 'history':
                                        access_time = self.ui.history_dict_obj.get(file_path)
                                        if access_time:
                                            tp = [file_path, access_time[1]]
                                        else:
                                            tp = [file_path, os.path.getatime(file_path)]
                                    else:
                                        tp = [file_path, os.path.getctime(file_path)]
                                    new_arr.append(tp)
                        if new_arr:
                            new_arr = sorted(new_arr, key=lambda x: x[1], reverse=True)
                            ntp = [i, new_arr[0][1]]
                            self.logger.debug(ntp)
                            #self.logger.debug(new_arr)
                        else:
                            ntp = [i, 0]
                            self.logger.error(ntp)
                        rows_access.append(ntp)
                    else:
                        rows_not_access.append(i)
                    new_arr[:] = []
                if rows_access:
                    rows_access = sorted(rows_access, key=lambda x: x[1], reverse=True)
                    rows_access = [i[0] for i in rows_access]
                rows[:] = []
                rows = rows_access + rows_not_access
        conn.commit()
        conn.close()
        return rows

    def create_update_video_db(self, video_db, video_file, video_file_bak,
                               update_progress_show=None):
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Wait..Updating Video Database')
            QtWidgets.QApplication.processEvents()

        lines = self.import_video(video_file, video_file_bak)
        print(len(lines))
        lines.sort()
        if os.path.exists(video_db):
            j = 0
            w = []
            epn_cnt = 0
            dir_cmp = []
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            for i in lines:
                i = i.strip()
                if i:
                    w[:] = []
                    i = os.path.normpath(i)
                    di, na = os.path.split(i)
                    ti = os.path.basename(di)
                    pa = i
                    if j == 0:
                        dir_cmp.append(di)
                    else:
                        tmp = dir_cmp.pop()
                        if tmp == di:
                            epn_cnt = epn_cnt + 1
                        else:
                            epn_cnt = 0
                        dir_cmp.append(di)
                    if 'movie' in di.lower():
                        category = self.ui.category_dict['movies']
                    elif 'anime' in di.lower():
                        category = self.ui.category_dict['anime']
                    elif 'cartoon' in di.lower():
                        category = self.ui.category_dict['cartoons']
                    elif 'tv shows' in di.lower() or 'tv-shows' in di.lower():
                        category = self.ui.category_dict['tv shows']
                    else:
                        category = self.ui.category_dict['others']
                    w = [ti, di, na, na, pa, epn_cnt, category]
                    try:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?)', w)
                        self.logger.info("Inserting:", w)
                    except:
                        self.logger.info(w)
                        self.logger.info("Duplicate")
                    j = j+1
        else:
            j = 0
            w = []
            dir_cmp = []
            epn_cnt = 0
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            cur.execute('''CREATE TABLE Video(Title text, Directory text, FileName text, EP_NAME text, Path text primary key, EPN integer, Category integer)''')
            for i in lines:
                i = i.strip()
                if i:
                    w[:] = []
                    i = os.path.normpath(i)
                    di, na = os.path.split(i)
                    ti = os.path.basename(di)
                    pa = i

                    if j == 0:
                        dir_cmp.append(di)
                    else:
                        tmp = dir_cmp.pop()
                        if tmp == di:
                            epn_cnt = epn_cnt + 1
                        else:
                            epn_cnt = 0
                        dir_cmp.append(di)
                    if 'movie' in di.lower():
                        category = self.ui.category_dict['movies']
                    elif 'anime' in di.lower():
                        category = self.ui.category_dict['anime']
                    elif 'cartoon' in di.lower():
                        category = self.ui.category_dict['cartoons']
                    elif 'tv shows' in di.lower() or 'tv-shows' in di.lower():
                        category = self.ui.category_dict['tv shows']
                    else:
                        category = self.ui.category_dict['others']
                    w = [ti, di, na, na, pa, epn_cnt, category]
                    try:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?)', w)
                        self.logger.info('inserted: {0}<-->{1}'.format(w, j))
                        j = j+1
                    except Exception as e:
                        self.logger.error('Escaping: {0} <---> {1}'.format(e, w))
        conn.commit()
        conn.close()
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Update Complete!')
            print('--191---update-complete--')
            QtWidgets.QApplication.processEvents()
    
    def adjust_video_dict_mark(self, epname, path, rownum=None):
        dir_name, file_name = os.path.split(path)
        plist = [epname, path]
        self.logger.info('214----{0}-----database.py--'.format(plist))
        if rownum is not None and dir_name in self.ui.video_dict:
            self.ui.video_dict[dir_name][rownum] = plist
            
    def alter_table_and_update(self, version):
        if version <= (2, 0, 0, 0) and version > (0, 0, 0, 0):
            msg = 'Video Database Updating. Please Wait!'
            send_notification(msg)
            conn = sqlite3.connect(os.path.join(self.home, 'VideoDB', 'Video.db'))
            cur = conn.cursor()
            try:
                cur.execute('ALTER TABLE Video ADD COLUMN Category integer')
                conn.commit()
                conn.close()
                
                conn = sqlite3.connect(os.path.join(self.home, 'VideoDB', 'Video.db'))
                cur = conn.cursor()
                cur.execute('SELECT Path FROM Video')
                rows = cur.fetchall()
                for i in rows:
                    self.logger.info('Databse Schema Changed updating Entries::{0}'.format(i))
                    if i:
                        path = i[0].lower()
                        di, na = os.path.split(i[0])
                        if 'movie' in di.lower():
                            category = self.ui.category_dict['movies']
                        elif 'anime' in di.lower():
                            category = self.ui.category_dict['anime']
                        elif 'cartoon' in di.lower():
                            category = self.ui.category_dict['cartoons']
                        elif 'tv shows' in di.lower() or 'tv-shows' in di.lower():
                            category = self.ui.category_dict['tv shows']
                        else:
                            category = self.ui.category_dict['others']
                        qr = 'Update Video Set Category=? Where Path=?'
                        cur.execute(qr, (category, i[0]))
            except Exception as err:
                print(err, 'Column Already Exists')
            conn.commit()
            conn.close()
            
    def update_video_count(self, qType, qVal, rownum=None):
        qVal = qVal.replace('"', '')
        qVal = str(qVal)
        conn = sqlite3.connect(os.path.join(self.home, 'VideoDB', 'Video.db'))
        cur = conn.cursor()
        self.logger.info('{0}:{1}:{2}::::::database.py:::240'.format(qType, qVal, rownum))
        if qType == "mark":
            #qVal = '"'+qVal+'"'
            #cur.execute("Update Music Set LastPlayed=? Where Path=?", (datetime.datetime.now(), qVal))
            self.logger.info("----------"+qVal)
            cur.execute('Select FileName, EP_NAME from Video Where Path=?', (qVal, ))
            r = cur.fetchall()
            self.logger.info(r)
            for i in r:
                fname = i[0]
                epName = i[1]
                break

            if not fname.startswith('#'):
                fname = '#'+fname
                epName = '#'+epName
            #cur.execute("Update Music Set Playcount=? Where Path=?", (incr, qVal))
            qr = 'Update Video Set FileName=?, EP_NAME=? Where Path=?'
            cur.execute(qr, (fname, epName, qVal))
        elif qType == "unmark":    
            self.logger.info("----------"+qVal)
            cur.execute('Select FileName, EP_NAME from Video Where Path=?', (qVal, ))
            r = cur.fetchall()

            self.logger.info(r)
            for i in r:
                fname = i[0]
                epName = i[1]
                break

            if fname.startswith('#'):
                fname = fname.replace('#', '', 1)
                epName = epName.replace('#', '', 1)
            qr = 'Update Video Set FileName=?, EP_NAME=? Where Path=?'
            cur.execute(qr, (fname, epName, qVal))

        self.logger.info("Number of rows updated: %d" % cur.rowcount)
        conn.commit()
        conn.close()
        
        if qType == 'mark' or qType == 'unmark':
            self.adjust_video_dict_mark(epName, qVal, rownum)
        
    def update_on_start_video_db(self, video_db, video_file, video_file_bak,
                                 video_opt, update_progress_show=None):
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Wait..Updating Video Database')
            QtWidgets.QApplication.processEvents()
        m_files = self.import_video(video_file, video_file_bak)
        try:
            self.logger.debug('--fetching--')
            conn = sqlite3.connect(video_db)
            cur = conn.cursor()
            cur.execute('SELECT Path FROM Video')
            rows = cur.fetchall()
            conn.commit()
            conn.close()
            self.logger.debug('--fetch complete--')
        except Exception as e:
            self.logger.error('{0}::{1}'.format(e, '--database-corrupted--21010--'))
            return 0
        m_files_old = []
        for i in rows:
            m_files_old.append((i[0]))

        l1 = len(m_files)
        l2 = len(m_files_old)
        m = list(set(m_files)-set(m_files_old))+list(set(m_files_old)-set(m_files))
        m.sort()

        m_files.sort()
        m_files_old.sort()
        print(l1)
        print(l2)
        print(len(m))
        w = []
        dict_epn = {}
        conn = sqlite3.connect(video_db)
        cur = conn.cursor()
        for i in m:
            i = i.strip()
            if i:
                w[:] = []
                i = os.path.normpath(i)
                di, na = os.path.split(i)
                ti = os.path.basename(di)
                pa = i
                if 'movie' in di.lower():
                    category = self.ui.category_dict['movies']
                elif 'anime' in di.lower():
                    category = self.ui.category_dict['anime']
                elif 'cartoon' in di.lower():
                    category = self.ui.category_dict['cartoons']
                elif 'tv shows' in di.lower() or 'tv-shows' in di.lower():
                    category = self.ui.category_dict['tv shows']
                else:
                    category = self.ui.category_dict['others']
                cur.execute('SELECT Path FROM Video Where Path=?', (i,))
                rows = cur.fetchall()
                if di in dict_epn:
                    epn_cnt = dict_epn.get(di)
                else:
                    cur.execute('SELECT Path FROM Video Where Directory=?', (di,))
                    rows1 = cur.fetchall()
                    epn_cnt = len(rows1)
                    dict_epn.update({di:epn_cnt})
                w = [ti, di, na, na, pa, epn_cnt, category]
                if video_opt == "UpdateAll":
                    if os.path.exists(i) and not rows:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?)', w)
                        self.logger.info("Not Inserted, Hence Inserting File = "+i)
                        self.logger.info(w)
                        epn_cnt += 1
                        dict_epn.update({di:epn_cnt})
                    elif not os.path.exists(i) and rows:
                        cur.execute('Delete FROM Video Where Path=?', (i,))
                        self.logger.info('Deleting File From Database : '+i)
                        self.logger.info(w)
                        epn_cnt -= 1
                        dict_epn.update({di:epn_cnt})
                elif video_opt == "Update":
                    if os.path.exists(i) and not rows:
                        self.logger.info(i)
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?)', w)
                        self.logger.info("Not Inserted, Hence Inserting File = "+i)
                        self.logger.info(w)
                        epn_cnt += 1
                        dict_epn.update({di:epn_cnt})

        conn.commit()
        conn.close()
        if (update_progress_show is None or update_progress_show) and self.ui:
            QtWidgets.QApplication.processEvents()
            self.ui.text.setText('Updating Complete')
            QtWidgets.QApplication.processEvents()

    def import_video(self, video_file, video_file_bak):
        m = []
        o = []
        music = []
        p = []
        m_files = []
        if os.path.isfile(os.path.join(self.home, 'local.txt')):
            lines_dir = open_files(os.path.join(self.home, 'local.txt'), True)
            for lines_d in lines_dir:
                if not lines_d.startswith('#'):
                    music[:] = []
                    lines_d = lines_d.strip()
                    lines_d = os.path.normpath(lines_d)
                    dirn = lines_d
                    self.logger.debug('checking::dirn={0}'.format(dirn))
                    if os.path.exists(dirn):
                        self.logger.debug('exists::dirn={0}'.format(dirn))
                        music.append(dirn)
                        for r, d, f in os.walk(dirn):
                            for z in d:
                                if not z.startswith('.'):
                                    music.append(os.path.join(r, z))
                                else:
                                    o.append(os.path.join(r, z))

                        print(len(music))
                        j = 0
                        lines = []
                        for i in music:
                            if os.path.exists(i):
                                try:
                                    n = os.listdir(i)
                                except Exception as err:
                                    self.logger.error(err)
                                    n = []
                                p[:] = []
                                for k in n:
                                    file_ext = k.rsplit('.', 1)[-1]
                                    if file_ext.lower() in self.video_ext:
                                        p.append(os.path.join(i, k))
                                        path = os.path.join(i, k)
                                        if os.path.isfile(path):
                                            m_files.append(path)
                                if p:
                                    r = i
                                    lines.append(r)
                                    j = j+1
        return list(set(m_files))

    def get_music_db(self, music_db, queryType, queryVal):
        conn = sqlite3.connect(music_db)
        cur = conn.cursor()
        q = queryType
        qVal = str(queryVal)
        #if '"' in qVal:
        #	qVal = qVal.replace('"', '')
        if q == "Artist":
            if not qVal:
                cur.execute('SELECT Distinct Artist FROM Music order by Artist')
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Artist="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Artist=?'
                cur.execute(qr, (qVal, ))
        elif q == "Album":
            if not qVal:
                cur.execute('SELECT Distinct Album FROM Music order by Album')
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Album="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Album=?'
                #print(qr, qVal)
                cur.execute(qr, (qVal, ))
        elif q == "Title":
            if not qVal:
                cur.execute('SELECT Distinct Title FROM Music order by Title')
            else:
                qr = 'SELECT Artist, Title, Path FROM Music Where Title=?'
                cur.execute(qr, (qVal, ))
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Title="'+qVal+'"')
        elif q == "Directory":
            print(q)
            if not qVal:
                cur.execute('SELECT Distinct Directory FROM Music order by Directory')
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Directory="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Directory=?'
                cur.execute(qr, (qVal, ))
        elif q == "Playlist":
            print(q)
            if not qVal:
                cur.execute('SELECT Playlist FROM Music')
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Playlist="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Playlist=?'
                cur.execute(qr, (qVal, ))
        elif q == "Fav-Artist":
            print(q)
            if not qVal:
                cur.execute("SELECT Distinct Artist FROM Music Where Favourite='yes'")
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Artist="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Artist=?'
                cur.execute(qr, (qVal, ))
        elif q == "Fav-Album":
            print(q)
            if not qVal:
                cur.execute("SELECT Distinct Album FROM Music Where Favourite='yes'")
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Album="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Album=?'
                cur.execute(qr, (qVal, ))
        elif q == "Fav-Directory":
            print(q)
            if not qVal:
                cur.execute("SELECT Distinct Directory FROM Music Where Favourite='yes'")
            else:
                #cur.execute('SELECT Artist, Title, Path FROM Music Where Directory="'+qVal+'"')
                qr = 'SELECT Artist, Title, Path FROM Music Where Directory=?'
                cur.execute(qr, (qVal, ))
        elif q == "Last 50 Most Played":
            print(q)
            cur.execute("SELECT Artist, Title, Path FROM Music order by Playcount desc limit 50")
        elif q == "Last 50 Newly Added":
            print(q)
            cur.execute("SELECT Artist, Title, Path FROM Music order by Modified desc limit 50")
        elif q == "Last 50 Played":
            print(q)
            cur.execute("SELECT Artist, Title, Path FROM Music order by LastPlayed desc limit 50")
        elif q == "Search":
            print(q)
            qr = 'SELECT Artist, Title, Path, Album FROM Music Where Artist like ? or Title like ? or Album like ? order by Title'
            #qr = 'SELECT Artist FROM Music Where Artist like "'+ '%'+str(qVal)+'%'+'"'
            #print(qr)
            qv = '%'+str(qVal)+'%'
            self.logger.info('{0} <----> {1}'.format(qr, qv))
            cur.execute(qr, (qv, qv, qv, ))

        rows = cur.fetchall()
        #print(rows)
        conn.commit()
        conn.close()
        return rows

    def update_music_count(self, qType, qVal):
        qVal = qVal.replace('"', '')
        qVal = str(qVal)
        conn = sqlite3.connect(os.path.join(self.home, 'Music', 'Music.db'))
        cur = conn.cursor()
        if qType == "count":    
            #qVal = '"'+qVal+'"'
            #cur.execute("Update Music Set LastPlayed=? Where Path=?", (datetime.datetime.now(), qVal))
            self.logger.info("----------"+qVal)
            cur.execute('Select Playcount, Title from Music Where Path=?', (qVal,))
            r = cur.fetchall()
            self.logger.info(r)
            if not r:
                incr = 1
            else:
                self.logger.info(r)
                for i in r:
                    self.logger.info("count")
                    self.logger.info(i[0])
                    incr = int(i[0])+1

            #cur.execute("Update Music Set Playcount=? Where Path=?", (incr, qVal))
            try:
                qr = 'Update Music Set LastPlayed=?, Playcount=? Where Path=?'
                q1 = datetime.datetime.now()
                #qVal = '"'+qVal+'"'
                cur.execute(qr, (q1, incr, qVal))
            except Exception as err:
                print(err)
                qr = 'Update Music Set LastPlayed=?, Playcount=? Where Path="'+qVal+'"'
                q1 = datetime.datetime.now()
                #qVal = '"'+qVal+'"'
                cur.execute(qr, (q1, incr))
        elif qType == "fav":
            tmp = str(self.ui.list3.currentItem().text())
            if tmp == "Artist":
                qr = 'Update Music Set Favourite="yes" Where Artist=?'
                cur.execute(qr, (qVal, ))
            elif tmp == "Album":
                qr = 'Update Music Set Favourite="yes" Where Album=?'
                cur.execute(qr, (qVal, ))
            elif tmp == "Directory":
                qr = 'Update Music Set Favourite="yes" Where Directory=?'
                cur.execute(qr, (qVal, ))
        self.logger.info("Number of rows updated: %d" % cur.rowcount)
        conn.commit()
        conn.close()

    def create_update_music_db(self, music_db, music_file, music_file_bak,
                               update_progress_show=None):
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Wait..Tagging')
            QtWidgets.QApplication.processEvents()
        f = open(music_file, 'w')
        f.close()
        lines = self.import_music(music_file, music_file_bak)
        if os.path.exists(music_db):
            conn = sqlite3.connect(music_db)
            cur = conn.cursor()
            for k in lines:
                j = k.split('	')[0]
                i = j.strip()
                w = self.get_tag_lib(str(i))
                try:
                    cur.execute('INSERT INTO Music VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', w)
                    #print("Inserting")
                except:
                    self.logger.info('Duplicate: {0}'.format(w))
                    #self.logger.info("Duplicate")
        else:
            t = 0
            conn = sqlite3.connect(music_db)
            cur = conn.cursor()
            cur.execute('''CREATE TABLE Music(Title text, Artist text, Album text, Directory text, Path text primary key, Playlist text, Favourite text, FavouriteOpt text, Playcount integer, Modified timestamp, LastPlayed timestamp)''')
            for k in lines:
                j = k.split('	')[0]
                i = j.strip()
                w = self.get_tag_lib(str(i))
                try:
                    cur.execute('INSERT INTO Music VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', w)
                    t = t+1
                    if (update_progress_show is None or update_progress_show) and self.ui:
                        self.ui.text.setText('Wait..Tagging '+str(t))
                        QtWidgets.QApplication.processEvents()
                except:
                    print("Escaping")
        conn.commit()
        conn.close()
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Complete Tagging '+str(t))
            QtWidgets.QApplication.processEvents()

    def get_tag_lib(self, path):
        if SONG_TAGS:
            if SONG_TAGS == 'mutagen':
                t = mutagen.File(path, easy=True)
            elif SONG_TAGS == 'taglib':
                t = taglib.File(path)
        else:
            t = {}
        m = []
        tags = t.tags
        ar1 = 'Unknown'
        al1 = 'Unknown'
        ti1 = os.path.basename(path)
        self.logger.info(tags)
        try:
            if tags:
                if SONG_TAGS == 'mutagen':
                    if 'artist' in tags:
                        if tags['artist']:
                            ar1 = tags['artist'][0]
                    if 'album' in tags:
                        if tags['album']:
                            al1 = tags['album'][0]
                    if 'title' in tags:
                        if tags['title']:
                            ti1 = tags['title'][0]
                elif SONG_TAGS == 'taglib':
                    if 'ARTIST' in tags:
                        if tags['ARTIST']:
                            ar1 = tags['ARTIST'][0]
                    if 'ALBUM' in tags:
                        if tags['ALBUM']:
                            al1 = tags['ALBUM'][0]
                    if 'TITLE' in tags:
                        if tags['TITLE']:
                            ti1 = tags['TITLE'][0]
            else:
                self.logger.info('Error No Tags: {0}'.format(path))
        except Exception as e:
            print(e, '---20001')

        if ar1 == 'Unknown' or al1 == 'Unknown':
            self.logger.info('Error Artist={0}:Album={1}:Path={2}'.format(ar1, al1, path))

        dir1, raw_title = os.path.split(path)

        r = ti1+':'+ar1+':'+al1

        m.append(str(ti1))
        m.append(str(ar1))
        m.append(str(al1))
        m.append(str(dir1))
        m.append(str(path))
        m.append('')
        m.append('')
        m.append('')
        m.append(0)
        m.append(os.path.getmtime(path))
        m.append(datetime.datetime.now())
        return m

    def update_on_start_music_db(self, music_db, music_file, music_file_bak,
                                 update_progress_show=None):
        m_files = self.import_music(music_file, music_file_bak)
        try:
            conn = sqlite3.connect(music_db)
            cur = conn.cursor()
            cur.execute('SELECT Path, Modified FROM Music')
            rows = cur.fetchall()
            conn.commit()
            conn.close()
        except Exception as e:
            print(e, '--database-corrupted--21369---')
            return 0
        m_files_old = []
        for i in rows:
            j = i[0]+'	'+(str(i[1])).split('.')[0]
            m_files_old.append(str(j))
        
        l1 = len(m_files)
        l2 = len(m_files_old)
        m = list(set(m_files)-set(m_files_old))+list(set(m_files_old)-set(m_files))
        m_files.sort()
        m_files_old.sort()
        print("************")

        print("_______________")
        self.logger.info(m)
        self.logger.info(m.sort())
        self.logger.info(len(m))
        self.logger.info(len(m_files))
        self.logger.info(len(m_files_old))
        conn = sqlite3.connect(music_db)
        cur = conn.cursor()
        for k in m:
            j = k.split('	')
            i = str(j[0])

            cur.execute('SELECT Path FROM Music Where Path=?', (i, ))
            rows = cur.fetchall()

            if os.path.exists(i) and (k in m_files) and not rows:
                w = self.get_tag_lib(i)
                cur.execute('INSERT INTO Music VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', w)
            elif os.path.exists(i) and rows and (k in m_files):
                print("File Modified")
                cur.execute('Delete FROM Music Where Path=?', (i, ))
                self.logger.info('Deleting File From Database : '+i)
                w = self.get_tag_lib(i)
                cur.execute('INSERT INTO Music VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', w)
            elif not os.path.exists(i) and rows:
                cur.execute('Delete FROM Music Where Path=?', (i, ))
                self.logger.info('Deleting File From Database : '+i)
            elif os.path.exists(i) and not rows:
                cur.execute('Delete FROM Music Where Path=?', (i, ))
                self.logger.info('Deleting File From Database : '+i)

        conn.commit()
        conn.close()

    def import_music(self, music_file, music_file_bak):
        m = []
        o = []
        music = []
        p = []
        m_files = []
        if os.path.isfile(os.path.join(self.home, 'local.txt')):
            lines_dir = open_files(os.path.join(self.home, 'local.txt'), True)
            for lines_d in lines_dir:
                if not lines_d.startswith('#'):
                    music[:] = []
                    lines_d = os.path.normpath(lines_d.strip())
                    dirn = lines_d
                    music.append(dirn)
                    for r, d, f in os.walk(dirn):
                        for z in d:
                            if not z.startswith('.'):
                                music.append(os.path.join(r, z))
                            else:
                                o.append(os.path.join(r, z))

                    self.logger.debug(len(music))
                    j = 0
                    lines = []
                    for i in music:
                        if os.path.exists(i):
                            try:
                                n = os.listdir(i)
                            except Exception as err:
                                self.logger.error(err)
                                n = []
                            p[:] = []
                            for k in n:
                                file_ext = k.rsplit('.', 1)[-1]
                                if file_ext.lower() in self.music_ext:
                                    p.append(os.path.join(i, k))
                                    path = os.path.join(i, k)
                                    if os.path.isfile(path):
                                        s = (path+'	'+(str(os.path.getmtime(path))).split('.')[0])
                                        m_files.append(s)
                            if p:
                                r = i
                                lines.append(r)
                                j = j+1
        return list(set(m_files))
