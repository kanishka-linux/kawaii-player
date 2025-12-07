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
import shutil
import sqlite3
import datetime
import hashlib
import uuid
import urllib
import base64
from typing import Optional, List, Tuple

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from player_functions import open_files, send_notification

try:
    try:
        import mutagen
        SONG_TAGS = 'mutagen'
    except Exception as err:
        print(err, '--6--')
        import taglib
        SONG_TAGS = 'taglib'
except Exception as err:
    print(err, '--10--')
    SONG_TAGS = None

print(SONG_TAGS, '--tagging-module--')


class DatabaseMigrationThreadOnStartUp(QtCore.QThread):

    mysignal = pyqtSignal(str)

    def __init__(self, db_instance, db_path):
        QtCore.QThread.__init__(self)
        global ui
        self.db_instance = db_instance
        self.db_path = db_path
        self.mysignal.connect(update_text_widget)
        ui = db_instance.ui

    def __del__(self):
        self.wait()

    def run(self):
        paths = self.db_instance.get_videos_without_checksum(self.db_path)
        count = len(paths)
        for i, file_path in enumerate(paths):
            checksum = self.db_instance.calculate_file_checksum(file_path)
            if checksum and self.db_instance.update_checksum(self.db_path, file_path, checksum):
                print(f"successfully updated, file: {file_path}, checksum: {checksum}")
            else:
                print(f"failed to update sha, file: {file_path}, checksum: {checksum}")
            self.mysignal.emit(f"finished Migrating {i}/{count}:: {file_path}::{checksum}")

class DatabaseMigrationWorker(QtCore.QThread):

    mysignal = pyqtSignal(str)

    def __init__(self, db_instance, db_path, video_file, video_file_bak):
        QtCore.QThread.__init__(self)
        global ui
        self.db_instance = db_instance
        self.db_path = db_path
        self.mysignal.connect(update_text_widget)
        ui = db_instance.ui
        self.video_file = video_file
        self.video_file_bak = video_file_bak

    def __del__(self):
        self.wait()

    def migrate_thumbnails(self, old_path, media_path):
        thumbnail_dir = os.path.join(ui.home_folder, 'thumbnails', 'thumbnail_server')

        thumb_name_bytes_old = bytes(old_path, 'utf-8')
        h = hashlib.sha256(thumb_name_bytes_old)
        thumb_name_old = h.hexdigest()

        thumb_name_bytes_new = bytes(media_path, 'utf-8')
        h = hashlib.sha256(thumb_name_bytes_new)
        thumb_name_new = h.hexdigest()

        thumb_path_old = os.path.join(thumbnail_dir, thumb_name_old+'.jpg')
        if os.path.exists(thumb_path_old):
            thumb_path_new = os.path.join(thumbnail_dir, thumb_name_new+'.jpg')
            shutil.move(thumb_path_old, thumb_path_new)
            print(f"thumbnail moved from {thumb_path_old} -> {thumb_path_new}")

        for pixel in ['480px', '128px', 'label']:
            thumb_path_old = os.path.join(thumbnail_dir, pixel+'.'+thumb_name_old+'.jpg')
            if os.path.exists(thumb_path_old):
                thumb_path_new = os.path.join(thumbnail_dir, pixel+'.'+thumb_name_new+'.jpg')
                shutil.move(thumb_path_old, thumb_path_new)
                print(f"thumbnail moved from {thumb_path_old} -> {thumb_path_new}")

    def update(self, media_path):
        checksum = self.db_instance.calculate_file_checksum(media_path)
        old_path = None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                    SELECT Path from Video
                    WHERE file_checksum = ?
                    """, (checksum,))
            result = [row[0] for row in cursor.fetchall()]
            print(result)
            if result:
                old_path = result[0]

            conn.commit()
            conn.close()
        except Exception as err:
            print(f"error migrating thumbnails: {err}")
            conn.close()

        # media_path is new_path
        # old_path stored in db against the checksum
        if old_path and old_path != media_path:
            self.migrate_thumbnails(old_path, media_path)

            directory, _  = os.path.split(media_path)
            # Update Path pointing to new path
            # but with same checksum
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                UPDATE Video
                SET Path = ?, Directory = ?
                WHERE file_checksum = ?
                """, (media_path, directory, checksum))
                conn.commit()
                conn.close()
            except Exception as err:
                print(f"error updating path={media_path} for a given chhecksum={checksum}: {err}")
                conn.close()
        # If no old_path, means no entry exists for the
        # checksum, then try to update media_path with the its
        # checksum
        elif old_path is None:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE Video
                    SET file_checksum = ?
                    WHERE Path = ?
                    """, (checksum, media_path))

                conn.commit()
                conn.close()
            except Exception as err:
                print(f"error updating checksum={checksum} for a given path={media_path}: {err}")
                conn.close()
        return checksum

    def run(self):
        m_files = self.db_instance.import_video(self.video_file, self.video_file_bak)
        count = len(m_files)

        try:
            for i, media_path in enumerate(m_files):
                try:
                    checksum = self.update(media_path)
                    self.mysignal.emit(f"finished Migrating {i}/{count}:: {media_path}::{checksum}")
                except sqlite3.IntegrityError as e:
                    print(e, f"skip: {media_path}")
                    pass

        except Exception as err:
            print(err, "db-error")

@pyqtSlot(str)
def update_text_widget(info):
    ui.text.setText(info)

class MediaDatabase():

    def __init__(self, home=None, logger=None):
        self.home = home
        self.logger = logger
        self.ui = None
        self.db_worker = None
        
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
                            if file_ext.lower() in self.ui.video_type_arr:
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
        rows = [('none','none')]
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
        elif q.lower() == "search":
            qVal = '%'+qVal+'%'
            qr = 'SELECT EP_NAME, Path From Video Where EP_NAME like ? or Directory like ? order by Directory'
            self.logger.info('qr={0};qVal={1}'.format(qr, qVal))
            cur.execute(qr, (qVal, qVal, ))
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
        if not error_occured:
            rows = cur.fetchall()
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
                    metadata_file = os.path.join(di, "metadata.txt")
                    if os.path.exists(metadata_file):
                        content = open(metadata_file, "r").read()
                        content_lines = content.split("\n")
                        metadata = [(i.split(":")[0].lower(), i.split(":", 1)[-1].strip()) for i in content_lines if ":" in i]
                        metadata_dict = dict(metadata)
                        ti = metadata_dict.get("title")
                    else:
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

                    checksum = self.calculate_file_checksum(pa)
                    w = [ti, di, na, na, pa, epn_cnt, category, checksum]
                    try:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?, ?)', w)
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

                    checksum = self.calculate_file_checksum(pa)
                    w = [ti, di, na, na, pa, epn_cnt, category, checksum]
                    try:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?, ?)', w)
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
            

    def migrate_database(self, old_version, column_name):
        print(f"version upgrade detected  from {old_version} to {self.ui.version_number}, running migration")
        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')
        table_name = "Video"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]

            if column_name not in columns:
                if column_name == "file_checksum":
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} Text Default ''"
                    cursor.execute(alter_sql)
                    title_index_sql = "CREATE INDEX index_title ON Video (Title)"
                    cursor.execute(title_index_sql)
                    directory_index_sql = "CREATE INDEX index_dir ON Video (Directory)"
                    cursor.execute(directory_index_sql)
                    checksum_index_sql = "CREATE INDEX index_checksum ON Video (file_checksum)"
                    cursor.execute(checksum_index_sql)
                    conn.commit()
                    print(f"Column '{column_name}' added successfully to table '{table_name}'")

                    self.thread = DatabaseMigrationThreadOnStartUp(self, db_path)
                    self.thread.start()
                    #paths = self.get_videos_without_checksum(db_path)
                    #for file_path in paths:
                    #    checksum = self.calculate_file_checksum(file_path)
                    #    if checksum and self.update_checksum(db_path, file_path, checksum):
                    #        print(f"successfully updated, file: {file_path}, checksum: {checksum}")
                    #    else:
                    #        print(f"failed to update sha, file: {file_path}, checksum: {checksum}")

            else:
                print(f"Column '{column_name}' already exists in table '{table_name}'")

        except sqlite3.Error as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

    def calculate_file_checksum(self, file_path: str, chunk_size: int = 1024*1024) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        h = hashlib.blake2s()

        try:
            with open(file_path, 'rb') as file:
                buf = file.read(chunk_size)
                h.update(buf)
            return h.hexdigest()

        except (IOError, OSError, PermissionError) as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def get_videos_without_checksum(self, db_path: str) -> List[str]:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT Path
                FROM Video
                WHERE file_checksum IS NULL OR file_checksum = ''
                ORDER BY Path
            """)

            result = [row[0] for row in cursor.fetchall()]

            return result
        except sqlite3.Error as e:
            print(f"Error fetching videos without checksum: {e}")
            return []
        finally:
            conn.close()

    def update_checksum(self, db_path: str, file_path: str, sha: str) -> bool:
        """Update checksum column in database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            cursor.execute("""
                UPDATE Video SET file_checksum = ? WHERE Path = ?
            """, (sha, file_path))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"  ✗ Update error: {e}")
            return False

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

    def mark_episode_as_watched(self, file_path: str) -> bool:
        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            cursor.execute("""
                UPDATE Video SET EP_NAME = '#' || EP_NAME
                WHERE path = ?
                AND EP_NAME NOT LIKE '#%'
            """, (file_path,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            print(f"  ✗ Update error: {e}")
            return False

    def fetch_recently_added(self, count = 500) -> List[Tuple[str, str]]:
        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            cursor.execute("""
                select distinct Directory, Title from Video
            """)

            rows  = [(row[1], row[0]) for row in cursor.fetchall()]

            # Sort by when directory was last modified
            # with recent first
            sorted_rows = sorted(
                    rows, key=lambda x: os.path.getmtime(x[1]),
                    reverse=True)

            conn.commit()
            conn.close()
            return sorted_rows[:count]
        except Exception as e:
            conn.close()
            print(f"  ✗ Fetch error: {e}")
            return [("", "")]

    def fetch_recently_accessed(self) -> List[Tuple[str, str]]:
        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            cursor.execute("""
                select distinct Directory, Title from Video
                where EP_NAME like '#%'
            """)

            rows  = [(row[1], row[0]) for row in cursor.fetchall()]

            # Sort by when directory was last modified
            # with recent first
            sorted_rows = sorted(
                    rows, key=lambda x: os.path.getatime(x[1]),
                    reverse=True)

            conn.commit()
            conn.close()
            return sorted_rows
        except Exception as e:
            conn.close()
            print(f"  ✗ Fetch error: {e}")
            return [("", "")]

    def toggle_watch_status(self, file_path: str) -> str:
        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        ep_name = ""
        cursor.execute('SELECT EP_NAME from Video Where Path=?', (file_path, ))
        result = [row[0] for row in cursor.fetchall()]
        if result:
            ep_name = result[0]
            if ep_name.startswith("#"):
                ep_name = ep_name.replace("#", "")
            else:
                ep_name = f"#{ep_name}"
            try:
                cursor.execute("""
                    UPDATE Video SET EP_NAME = ? WHERE path = ?
                """, (ep_name, file_path))
                conn.commit()
                conn.close()
            except Exception as e:
                conn.close()
                print(f"  ✗ Update error: {e}")

        if ep_name.startswith("#"):
            ep_name = ep_name.replace("#", "✅", 1)
        return ep_name

    def create_series_info_table(self):

        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS series_info (
            id TEXT PRIMARY KEY,
            db_title TEXT NOT NULL,
            title TEXT NOT NULL,
            english_title TEXT,
            genres TEXT,
            year INTEGER,
            episodes INTEGER,
            image_poster_large TEXT,
            external_id INTEGER,
            summary TEXT,
            score REAL,
            rank INTEGER,
            popularity INTEGER,
            type TEXT,
            duration TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create indexes for better search performance
        create_indexes_sql = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_entered_title ON series_info(db_title);",
            "CREATE INDEX IF NOT EXISTS idx_year ON series_info(year);",
            "CREATE INDEX IF NOT EXISTS idx_genres ON series_info(genres);",
            "CREATE INDEX IF NOT EXISTS idx_external_id ON series_info(external_id);"
        ]

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            # Create the table
            cursor.execute(create_table_sql)

            # Create indexes
            for index_sql in create_indexes_sql:
                cursor.execute(index_sql)

            conn.commit()
            print("Table 'series_info' and indexes created successfully!")

        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

        finally:
            conn.close()

    def insert_series_data(self, title, series_data):

        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')

        insert_sql = """
        INSERT INTO series_info (
            id, db_title, title, english_title,
            genres, year, episodes, image_poster_large,
            external_id, summary, score, rank,
            popularity, type, duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        update_sql = """
        UPDATE series_info SET
            title = ?, english_title = ?, genres = ?, year = ?,
            episodes = ?, image_poster_large = ?, external_id = ?,
            summary = ?, score = ?, rank = ?, popularity = ?,
            type = ?, duration = ?
        WHERE db_title = ?
        """

        get_existing_id_sql = "SELECT id FROM series_info WHERE db_title = ?"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            # Generate UUID for the record
            record_id = str(uuid.uuid4())

            # Prepare data tuple
            data_tuple = (
                record_id,
                title,
                series_data.get('title'),
                series_data.get('title_english'),
                ', '.join(series_data.get('genres', [])) if series_data.get('genres') else None,
                series_data.get('year'),
                series_data.get('episodes'),
                series_data.get('image_poster_large'),
                series_data.get('id'),
                series_data.get('synopsis'),
                series_data.get('score'),
                series_data.get('rank'),
                series_data.get('popularity'),
                series_data.get('type'),
                series_data.get('duration'),
            )

            cursor.execute(insert_sql, data_tuple)
            conn.commit()

            print(f"\nInserted anime: {title} => {series_data.get('title')} with ID: {record_id}\n")
            return record_id
        except sqlite3.IntegrityError as e:
            # Check if it's a unique constraint error on db_title
            if "UNIQUE constraint failed" in str(e) and "db_title" in str(e):
                try:
                    # Get the existing record ID
                    cursor.execute(get_existing_id_sql, (title,))
                    existing_record = cursor.fetchone()
                    existing_id = existing_record[0] if existing_record else None

                    # Prepare data tuple for UPDATE (without id and db_title)
                    update_data_tuple = (
                        series_data.get('title'),
                        series_data.get('title_english'),
                        ', '.join(series_data.get('genres', [])) if series_data.get('genres') else None,
                        series_data.get('year'),
                        series_data.get('episodes'),
                        series_data.get('image_poster_large'),
                        series_data.get('id'),
                        series_data.get('synopsis'),
                        series_data.get('score'),
                        series_data.get('rank'),
                        series_data.get('popularity'),
                        series_data.get('type'),
                        series_data.get('duration'),
                        title  # WHERE clause parameter
                    )

                    # Execute UPDATE
                    cursor.execute(update_sql, update_data_tuple)
                    conn.commit()

                    print(f"\nUpdated anime: {title} => {series_data.get('title')} with existing ID: {existing_id}\n")
                    return existing_id

                except sqlite3.Error as update_error:
                    print(f"Error updating data: {update_error}")
                    return None

        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            return None

        finally:
            conn.close()

    def search_filtered_anime_parameterized(self, limit, excluded_categories=None, excluded_title_keywords=None):

        db_path = os.path.join(self.home, 'VideoDB', 'Video.db')

        if excluded_categories is None:
            excluded_categories = [
                        'tv shows','documentaries', 'cartoons',
                        'music videos', 'extras', 'movies',
                        'extra'
                    ]

        if excluded_title_keywords is None:
            excluded_title_keywords = ['sample', 'pv', 'extras', 'oped', 'nced', 'specials', 'op & ed']

        # Build the query dynamically
        category_placeholders = ','.join(['?' for _ in excluded_categories])
        title_conditions = ' AND '.join(['LOWER(Title) NOT LIKE ?' for _ in excluded_title_keywords])

        query = f"""
        SELECT distinct Title FROM Video
        WHERE LOWER(Category) NOT IN ({category_placeholders})
        AND ({title_conditions})
        ORDER BY Title
        limit ?;
        """

        # Prepare parameters
        params = excluded_categories + [f'%{keyword}%' for keyword in excluded_title_keywords] + [limit]

        results = []
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:

            cursor.execute(query, params)
            results = [row[0] for row in cursor.fetchall()]

        except sqlite3.Error as e:
            print(f"Error executing parameterized query: {e}")

        finally:
            conn.close()
        return  results

    def fetch_series_metadata(self, title: str) -> dict:
        response_data = {}
        conn = sqlite3.connect(os.path.join(self.home, 'VideoDB', 'Video.db'))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        qr = """
            select * from series_info where db_title = ?
            """
        cur.execute(qr, (title, ))
        rows = [row for row in cur.fetchall()]
        if rows:
            data = dict(rows[0])

            response_data = {
                "success": True,
                "data": data
            }
        else:
            qr = """
            select Path from Video where Title= ? limit 1;
            """
            cur.execute(qr, (title,))
            rows = [row for row in cur.fetchall()]
            if rows:
                data = dict(rows[0])
                file_path = data['Path']
                response_data = {
                        "success": True,
                        "data": {
                                "title": title,
                                "image_poster_large":  self.build_url_from_file_path(file_path, "image"),
                                "summary": "NA"
                            }
                        }

        conn.commit()
        conn.close()
        return response_data

    def fetch_music_metadata(self, title: str, category: str) -> dict:
        response_data = {}
        if category in ["Artist", "Directory", "Album"]:
            qr = f"select Path from Music where {category}= ? limit 1;"
        else:
            return {}

        conn = sqlite3.connect(os.path.join(self.home, 'Music', 'Music.db'))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(qr, (title,))
        rows = [row for row in cur.fetchall()]
        if rows:
            data = dict(rows[0])
            file_path = data['Path']
            response_data = {
                    "success": True,
                    "data": {
                            "title": title,
                            "image_poster_large":  self.build_url_from_file_path(file_path, "image"),
                            "summary": "NA"
                        }
                    }

        conn.commit()
        conn.close()
        return response_data


    def build_url_from_file_path(self, file_path, file_type):
        file_name = os.path.basename(file_path)
        file_name_saitized = urllib.parse.quote(file_name.replace("/", "-"))
        encoded_path = str(base64.b64encode(bytes(file_path, 'utf-8')), 'utf-8')
        url = f"/abs_path={encoded_path}/{file_name_saitized}"
        if  file_type == "image":
            url = f"{url}.image"
        return url

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

    def migrate_based_on_checksum(self, video_db, video_file, video_file_bak,
                                 video_opt, update_progress_show=None):
        if (update_progress_show is None or update_progress_show) and self.ui:
            self.ui.text.setText('Wait..Migrating Video Database')
            QtWidgets.QApplication.processEvents()
        if self.db_worker is None:
            self.db_worker = DatabaseMigrationWorker(self, video_db, video_file, video_file_bak)
            self.db_worker.start()
        elif isinstance(self.db_worker, DatabaseMigrationWorker) and not self.db_worker.isRunning():
            self.db_worker = DatabaseMigrationWorker(self, video_db, video_file, video_file_bak)
            self.db_worker.start()
        

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
                metadata_file = os.path.join(di, "metadata.txt")
                if os.path.exists(metadata_file):
                    content = open(metadata_file, "r").read()
                    content_lines = content.split("\n")
                    metadata = [(i.split(":")[0].lower(), i.split(":", 1)[-1].strip()) for i in content_lines if ":" in i]
                    metadata_dict = dict(metadata)
                    ti = metadata_dict.get("title")
                else:
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
                checksum = self.calculate_file_checksum(pa)
                w = [ti, di, na, na, pa, epn_cnt, category, checksum]
                if video_opt == "UpdateAll":
                    if os.path.exists(i) and not rows:
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?, ?)', w)
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
                        cur.execute('INSERT INTO Video VALUES(?, ?, ?, ?, ?, ?, ?, ?)', w)
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
                                    if file_ext.lower() in self.ui.video_type_arr:
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
                tag_file = mutagen.File(path, easy=True)
            elif SONG_TAGS == 'taglib':
                tag_file = taglib.File(path)
        else:
            t = {}
        m = []
        if tag_file is not None:
            tags = tag_file.tags
        else:
            tags = None
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
                                if file_ext.lower() in self.ui.music_type_arr:
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
