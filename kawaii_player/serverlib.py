import os
import re
import importlib as imp
import shutil
import hashlib
from player_functions import open_files, write_files, ccurl, send_notification

try:
    import libtorrent as lt
    from stream import get_torrent_info_magnet
except Exception as err:
    print(err, '--11--')
    notify_txt = 'python3 bindings for libtorrent are broken\
                  Torrent Streaming feature will be disabled'
    send_notification(notify_txt, code=0)
    
class ServerLib:
    
    def __init__(self, ui_widget=None, hm=None, base=None, tmp=None, logr=None):
        global ui, home, TMPDIR, BASEDIR, logger
        ui = ui_widget
        home = hm
        BASEDIR = base
        TMPDIR = tmp
        logger = logr
        
    def get_file_name_from_bookmark(self, site, site_option,
                                    name, row, epnArrList):
        file_name_mkv = ''
        file_name_mp4 = ''
        
        new_epn = epnArrList[row].replace('#', '', 1).strip()
        if '	' in new_epn:
            new_epn = new_epn.split('	')[0]
            
        new_epn = new_epn.replace('/', '-')
        new_epn = new_epn.replace('"', '')
        new_epn = re.sub('"|.mkv|.mp4', '', new_epn)
        if new_epn.startswith('.'):
            new_epn = new_epn[1:]
        
        if (site.lower() != 'video' and site.lower() != 'music' 
                and site.lower() != 'local' and site.lower() != 'playlists' 
                and site.lower() != 'none'):
            title = name
            new_epn_mkv = new_epn+'.mkv'
            new_epn_mp4 = new_epn+'.mp4'
            file_name_mkv = os.path.join(ui.default_download_location,
                                         title, new_epn_mkv)
            file_name_mp4 = os.path.join(ui.default_download_location,
                                         title, new_epn_mp4)
        elif (site.lower() == 'playlists' or (site.lower() == 'music' 
                and site_option.lower().startswith('playlist'))):
            title = name
            st = epnArrList[row].split('	')[1]
            st = st.replace('"', '')
            if 'youtube.com' in st:
                new_epn_mkv = new_epn+'.mp4'
                new_epn_mp4 = new_epn+'.mp4'
                file_name_mkv = os.path.join(ui.default_download_location,
                                             title, new_epn_mkv)
                file_name_mp4 = os.path.join(ui.default_download_location,
                                             title, new_epn_mp4)
            else:
                new_epn_mkv = os.path.basename(st)
                new_epn_mp4 = new_epn_mkv
                file_name_mkv = st
                file_name_mp4 = st
        elif (site.lower() == 'video' or site.lower() == 'music' 
                or site.lower() == 'local' or site.lower() == 'none'):
            file_name_mkv = epnArrList[row].split('	')[1]
            file_name_mp4 = epnArrList[row].split('	')[1]
        
        if os.path.exists(file_name_mp4):
            return file_name_mp4
        elif os.path.exists(file_name_mkv):
            return file_name_mkv
        else:
            return 0
    
    def options_from_bookmark(self, site, site_option,
                              search_term, search_exact=None):
        original_path_name = []
        bookmark = False
        music_opt = ''
        video_opt = ''
        opt = ''
        status = site_option
        siteName = site_option
        new_dir_path = None
        new_name = 'Not Available'
        send_list_direct = False
        new_epnArrList = []
        if site.lower() == 'bookmark':
            bookmark = True
            status = site_option
            if status == "all":
                status = "bookmark"
            else:
                book_path = os.path.join(home, 'Bookmark')
                m = os.listdir(book_path)
                for i in m:
                    i = i.replace('.txt', '')
                    if i.lower() == site_option.lower():
                        status = i
                        break
        m = []
        new_video_local_stream = False
        print(bookmark, status, '--15627--')
        opt = 'history'
        bookmark_path = os.path.join(home, 'Bookmark', status+'.txt')
        if bookmark and os.path.isfile(bookmark_path):
            line_a = open_files(bookmark_path, True)
            logger.info(line_a)
            r = 0
            book_arr = []
            if search_term:
                for k, i in enumerate(line_a):
                    j = i.strip()
                    if j:
                        j = i.split(':')
                        if j:
                            print(j)
                            if search_term.lower() in j[5].lower():
                                site = j[0]
                                r = k
                                print(site, r)
                                site_option = j[1]
                                bookmark = False
                                break
            else:
                for i in line_a:
                    j = i.strip()
                    if j:
                        j = i.split(':')
                        if j:
                            book_arr.append(j[5].strip())
            if search_term:
                tmp = line_a[r]
                tmp = tmp.strip()
                tmp1 = tmp.split(':')
                site = tmp1[0]
                if site.lower() == "music" or site.lower() == "video":
                    opt = "Not Defined"
                    if site.lower() == "music":
                        music_opt = tmp1[1]
                    else:
                        video_opt = tmp1[1]
                else:
                    opt = tmp1[1]
                pre_opt = tmp1[2]
                siteName = tmp1[2]
                base_url = int(tmp1[3])
                embed = int(tmp1[4])
                name = tmp1[5]
                new_name = name
                if site.lower() == "local":
                    name_path = name
                video_local_stream = False
                logger.info(name)
                if len(tmp1) > 6:
                    if tmp1[6] == "True":
                        finalUrlFound = True
                    else:
                        finalUrlFound = False
                    if tmp1[7] == "True":
                        refererNeeded = True
                    else:
                        refererNeeded = False
                    if len(tmp1) >= 9:
                        if tmp1[8] == "True":
                            video_local_stream = True
                        else:
                            video_local_stream = False
                    if len(tmp1) >= 10:
                        new_dir_path = tmp1[9]
                        if os.name == 'nt':
                            if len(tmp1) == 11:
                                new_dir_path = new_dir_path + ':' + tmp1[10]
                    print(finalUrlFound)
                    print(refererNeeded)
                    
                else:
                    refererNeeded = False
                    finalUrlFound = False
                    
                logger.info(site + ":"+opt)
            else:
                site = 'None'
                original_path_name = [i for i in book_arr]
        
        site_var = None
        criteria = []
        print(bookmark, status, site, opt, '--15713--')
        if (not site.lower().startswith("playlist") and site.lower() != "music" 
                and site.lower() != "video" and site.lower()!= "local" 
                and site.lower() != "none"):
            for i in ui.addons_option_arr:
                if site.lower() == i.lower():
                    site = i
                    break
            plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
            if os.path.exists(plugin_path):
                if site_var:
                    del site_var
                    site_var = ''
                module = imp.import_module(site, plugin_path)
                site_var = getattr(module, site)(TMPDIR)
                if site_var:
                    criteria = site_var.getOptions() 
                    print(criteria)
                    tmp = criteria[-1]
                    if tmp.lower() == 'newversion':
                        criteria.pop()
                        ui.options_mode = 'new'
                        tmp = criteria[-1]
                    if tmp == 'LocalStreaming':
                        criteria.pop()
                        video_local_stream = True
                        new_video_local_stream = True
            else:
                return 0
                
        genre_num = 0
        if (site.lower() !="local" and site.lower() != "music" 
                and site.lower() != "subbedanime" and site.lower() != "dubbedanime" 
                and not site.lower().startswith("playlist") and site.lower() != "video" 
                and site.lower() != 'none'):
            
            t_opt = 'history'
            opt = t_opt
            
            if t_opt == "history":
                genre_num = 0
                opt = t_opt
                file_path = os.path.join(home, 'History', site, 'history.txt')
                if os.path.isfile(file_path):
                    lines = open_files(file_path, True)
                    lins = open_files(file_path, True)
                    list1_items = []
                    original_path_name[:] = []
                    for i in lins:
                        i = i.strip()
                        j = i
                        if '	' in i:
                            i = i.split('	')[0]
                        original_path_name.append(j)
                    if new_video_local_stream and ui.stream_session:
                        handle = ui.get_torrent_handle(search_term)
                        if handle is not None:
                            ui.torrent_handle = handle
            else:
                opt = t_opt
                try:
                    if video_local_stream:
                        new_video_local_stream = True
                        history_folder = os.path.join(home, 'History', site)
                        if os.path.exists(history_folder):
                            m = site_var.getCompleteList(
                                t_opt, ui.list6, ui.progress, 
                                ui.tmp_download_folder, history_folder
                                )
                            if ui.stream_session:
                                handle = ui.get_torrent_handle(search_term)
                                if handle is not None:
                                    ui.torrent_handle = handle
                    else:
                        m = site_var.getCompleteList(t_opt, 0)
                except Exception as e:
                    print(e)
                    return 0
                original_path_name[:] = []
                for i in m:
                    i = i.strip()
                    if '	' in i:
                        j = i.split('	')[0]
                    else:
                        j = i
                    original_path_name.append(i)
        elif site.lower() == "subbedanime" or site.lower() == "dubbedanime":
            code = 2
            siteName = site_option
            if site_var:
                criteria = site_var.getOptions()
                for i in criteria:
                    if siteName.lower() == i.lower():
                        siteName = i
                        break 
            opt = "history"
            original_path_name[:] = []
            if opt == "history":
                    file_path = os.path.join(home, 'History', site, siteName, 'history.txt')
                    if os.path.isfile(file_path):
                        lines = open_files(file_path, True)
                        original_path_name[:] = []
                        for i in lines:
                            i = i.strip()
                            if '	' in i:
                                j = i.split('	')[0]
                            else:
                                j = i
                            original_path_name.append(i)
        elif site.lower() == "music":
            music_dir = os.path.join(home, 'Music')
            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            if not os.path.exists(music_db):
                ui.media_data.create_update_music_db(
                    music_db, music_file, music_file_bak,
                    update_progress_show=False
                    )
            music_opt = site_option
            print(music_opt)
            if music_opt:
                music_opt = music_opt[0].upper()+music_opt[1:]
                if '-' in music_opt:
                    tmp = music_opt.split('-', 1)
                    sub_tmp = tmp[1]
                    music_opt = tmp[0]+'-'+sub_tmp[0].upper()+sub_tmp[1:]
            artist = []
            epnArrList = []
            if music_opt.lower().startswith("playlist"):
                pls = os.path.join(home, 'Playlists')
                if os.path.exists(pls):
                    m = os.listdir(pls)
                    for i in m:
                        artist.append(i)
            else:
                """
                if search_exact and music_opt.lower() != 'directory':
                    m = ui.media_data.get_music_db(music_db, music_opt, search_term)
                    for i in m:
                        artist.append(i[1]+'	'+i[2]+'	'+i[0])
                    send_list_direct = True
                else:
                """
                m = ui.media_data.get_music_db(music_db, music_opt, "")
                for i in m:
                    artist.append(i[0])
            if send_list_direct:
                print('exact search on')
                new_epnArrList = [i for i in artist]
            else:
                original_path_name[:] = []
                if (music_opt.lower() == "artist" or music_opt.lower() == "album" or music_opt.lower() == "title" 
                        or music_opt.lower() == "fav-artist" or music_opt.lower() == "fav-album"):
                    for i in artist:
                        original_path_name.append(i)
                elif music_opt.lower() == "directory" or music_opt.lower() == "fav-directory":
                    for i in artist:
                        original_path_name.append(i)
                        i = os.path.basename(i)
                elif music_opt.lower().startswith("playlist"):
                    for i in artist:
                        original_path_name.append(i.replace('.txt', '')+'	'+os.path.join(home, 'Playlists', i))
            #print(original_path_name)
        elif site.lower() == "video":
            video_dir = os.path.join(home, 'VideoDB')
            video_db = os.path.join(video_dir, 'Video.db')
            video_file = os.path.join(video_dir, 'Video.txt')
            video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
            if not os.path.exists(video_db):
                ui.media_data.create_update_video_db(
                    video_db, video_file, video_file_bak,
                    update_progress_show=False
                    )
            if not bookmark:
                video_opt = site_option                
            print('----video-----opt', video_opt)
            if video_opt.lower() == 'update' or video_opt.lower() == 'updateall':
                video_opt = 'Available'
            print('----video-----opt', video_opt)
            opt = video_opt
            artist = []
            m = []
            if not bookmark:
                if video_opt.lower() == "available":
                    m = ui.media_data.get_video_db(video_db, "Directory", "")
                elif video_opt.lower() == "history":
                    m = ui.media_data.get_video_db(video_db, "History", "")
                else:
                    m = ui.media_data.get_video_db(video_db, video_opt, "")
            else:
                book_file = os.path.join(home, 'Bookmark', status+'.txt')
                if os.path.exists(book_file):
                    line_a = open_files(book_file, True)
                    m = []
                    for i in line_a:
                        i = i.strip()
                        try:
                            new_name = i.split(':')[5]
                            try:
                                new_dir = i.split(':')[9]
                            except:
                                new_dir = new_name
                            logger.info('{0}-{1}-{2}'.format(search_term, new_name, new_dir))
                            if search_term and search_term in new_name.lower():
                                original_path_name.append(new_name+'	'+new_dir)
                                m1 = ui.media_data.get_video_db(video_db, "Directory", new_dir)
                                for i in m1:
                                    m.append(i[0]+'	'+i[1]+'	'+new_name)
                                logger.info(m)
                                logger.info('---14226---')
                                video_opt = 'directory'
                            elif not search_term:
                                original_path_name.append(new_name+'	'+new_dir)
                        except Exception as e:
                            print(e)
                    send_list_direct = True
                    #site = 'bookmark'
            if not send_list_direct:
                for i in m:
                    artist.append(i[0]+'	'+i[1])
            else:
                new_epnArrList = [i for i in m]
                print('direct match:')
            #original_path_name[:] = []
            logger.info(artist)
            if (video_opt.lower() != "update" and video_opt.lower() != "updateall") and not send_list_direct:
                for i in artist:
                    ti = i.split('	')[0]
                    di = i.split('	')[1]
                    if os.path.exists(di):
                        if ti.lower().startswith('season') or ti.lower().startswith('special'):
                            new_di, new_ti = os.path.split(di)
                            logger.info('new_di={0}-{1}'.format(new_di, new_ti))
                            new_di = os.path.basename(new_di)
                            ti = new_di+'-'+ti
                            original_path_name.append(ti+'	'+di)
                        else:
                            original_path_name.append(i)
                original_path_name = sorted(
                    original_path_name,
                    key=lambda x: x.split('	')[0].lower()
                    )
        elif site.lower().startswith("playlist"):
            pls = os.path.join(home, 'Playlists')
            if os.path.exists(pls):
                m = os.listdir(pls)
                for i in m:
                    j = i.replace('.txt', '')
                    original_path_name.append(j+'	'+os.path.join(pls, i))
        logger.info(original_path_name)
        print('--------14243-----------')
        if search_term:
            if not send_list_direct:
                epnArrList = self.listfound_from_bookmark(
                    site, site_option, search_term, original_path_name,
                    search_exact=search_exact)
            else:
                epnArrList = new_epnArrList
            if site.lower() == 'video':
                ret_tuple = (epnArrList, site, video_opt, False, siteName)
            elif site.lower() == 'music':
                ret_tuple = (epnArrList, site, music_opt, False, siteName)
            elif site.lower().startswith('playlist'):
                ret_tuple = (epnArrList, site, 'none', False, siteName)
            else:
                ret_tuple = (epnArrList, site, opt, new_video_local_stream, siteName)
            return ret_tuple
        else:
            return original_path_name
        
    def listfound_from_bookmark(
            self, site, site_option, search_term, 
            original_path_name, search_exact=None):
        site_var = None
        bookmark = False
        status = site_option
        logger.info('\n{0}:{1}:{2}\n --473--serverlib'.format(site,site_option,search_term))
        if site.lower() == 'bookmark':
            bookmark = True
            status = site_option
            if status.lower() == 'all':
                status = 'bookmark'
            else:
                m = os.listdir(os.path.join(home, 'Bookmark'))
                for i in m:
                    i = i.lower().replace('.txt', '')
                    if i == site_option.lower():
                        status = i
                        break
        m = []
        search_term = search_term.lower()
        epnArrList = []
        new_dir_path = None
        new_name = 'Not Available'
        bookmark_path = os.path.join(home, 'Bookmark', status+'.txt')
        if bookmark and os.path.isfile(bookmark_path):
            line_a = open_files(bookmark_path, True)
            r = 0
            for k, i in enumerate(line_a):
                j = i.strip()
                if j:
                    j = i.split(':')
                    if j:
                        if search_term in j[5].lower():
                            site = j[0]
                            r = k
                            break
            tmp = line_a[r]
            tmp = tmp.strip()
            tmp1 = tmp.split(':')
            site = tmp1[0]
            if site.lower() == "music" or site.lower() == "video":
                opt = "Not Defined"
                if site.lower() == "music":
                    music_opt = tmp1[1]
                else:
                    video_opt = tmp1[1]
            else:
                opt = tmp1[1]
            pre_opt = tmp1[2]
            siteName = tmp1[2]
            base_url = int(tmp1[3])
            embed = int(tmp1[4])
            name = tmp1[5]
            new_name = name
            if site.lower() == "local":
                name_path = name
            video_local_stream = False
            logger.info(name)
            if len(tmp1) > 6:
                if tmp1[6] == "True":
                    finalUrlFound = True
                else:
                    finalUrlFound = False
                if tmp1[7] == "True":
                    refererNeeded = True
                else:
                    refererNeeded = False
                if len(tmp1) >= 9:
                    if tmp1[8] == "True":
                        video_local_stream = True
                    else:
                        video_local_stream = False
                if len(tmp1) >= 10:
                    new_dir_path = tmp1[9]
                print(finalUrlFound)
                print(refererNeeded)
                print(video_local_stream)
            else:
                refererNeeded = False
                finalUrlFound = False
                
            logger.info(site + ":"+opt)
        site_var = None
        logger.info('--16069----')
        if (not site.lower().startswith("playlist") and site.lower() != "music"
                and site.lower() != "video" and site.lower() != "local"
                and site.lower() != "none"):
            logger.info('search_term={0}'.format(search_term))
            if search_term:
                epnArrList = []
                for i in ui.addons_option_arr:
                    if site.lower() == i.lower():
                        site = i
                        break
                plugin_path = os.path.join(home, 'src', 'Plugins', site+'.py')
                
                if os.path.exists(plugin_path):
                    logger.info('plugin_path={0}'.format(plugin_path))
                    if site_var:
                        del site_var
                        site_var = ''
                    module = imp.import_module(site, plugin_path)
                    site_var = getattr(module, site)(TMPDIR)
                    siteName = site_option
                    if site_var:
                        if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                            criteria = site_var.getOptions()
                            for i in criteria:
                                if siteName.lower() == i.lower():
                                    siteName = i
                                    break 
                else:
                    return 0
                    
                for i, value in enumerate(original_path_name):
                    search_field = value.lower()
                    if search_exact:
                        if '	' in search_field:
                            search_field = search_field.split('	')[0]
                    logger.info('search_field={0}'.format(search_field))
                    if ((search_term in search_field and not search_exact) 
                            or (search_term == search_field and search_exact)):
                        cur_row = i
                        new_name_with_info = original_path_name[cur_row].strip()
                        extra_info = ''
                        logger.info('cur_row={0}, new_name={1}'.format(i, new_name_with_info))
                        if '	' in new_name_with_info:
                            name = new_name_with_info.split('	')[0]
                            extra_info = new_name_with_info.split('	')[1]
                        else:
                            name = new_name_with_info
                        
                        if site.lower() == 'subbedanime' or site.lower() == 'dubbedanime':
                            hist_site = os.path.join(home, 'History', site, siteName, name)
                        else:
                            hist_site = os.path.join(home, 'History', site, name)
                            
                        hist_epn = os.path.join(hist_site, 'Ep.txt')
                        logger.info(hist_epn)
                        if os.path.exists(hist_epn):
                            lines = open_files(hist_epn, True)
                            m = []
                            for i in lines:
                                i = i.strip()
                                j = i.split('	')
                                if len(j) == 1:
                                    epnArrList.append(i+'	'+i+'	'+name)
                                elif len(j) >= 2:
                                    epnArrList.append(i+'	'+name)
                            picn = os.path.join(hist_site, 'poster.jpg')
                            fanart = os.path.join(hist_site, 'fanart.jpg')
                            thumbnail = os.path.join(hist_site, 'thumbnail.jpg')
                            sum_file = os.path.join(hist_site, 'summary.txt')
                            summary = ui.get_summary_history(sum_file)
        elif site.lower() == "music":
            art_n = search_term
            music_dir = os.path.join(home, 'Music')
                                
            music_db = os.path.join(home, 'Music', 'Music.db')
            music_file = os.path.join(home, 'Music', 'Music.txt')
            music_file_bak = os.path.join(home, 'Music', 'Music_bak.txt')
            
            music_opt = site_option
            if music_opt:
                music_opt = music_opt[0].upper()+music_opt[1:]
                if '-' in music_opt:
                    tmp = music_opt.split('-', 1)
                    sub_tmp = tmp[1]
                    music_opt = tmp[0]+'-'+sub_tmp[0].upper()+sub_tmp[1:]
            artist = []
            logger.info(original_path_name)
            hash_srch = None
            hash_dir = None
            if search_term.endswith('.hash'):
                hash_srch = search_term.rsplit('.', 1)[0]
                logger.debug(hash_srch)
            for index, value in enumerate(original_path_name):
                if music_opt.lower() == 'directory' or music_opt.lower() == 'fav-directory':
                    search_field = os.path.basename(value).lower()
                    if hash_srch:
                        hash_dir = bytes(value, 'utf-8')
                else:
                    search_field = value.lower()
                    if hash_srch:
                        if music_opt.lower().startswith('playlist'):
                            hash_dir = bytes(value.split('\t')[1], 'utf-8')
                        else:
                            hash_dir = bytes(value.split('\t')[0], 'utf-8')
                #logger.debug(value)
                if hash_srch and hash_dir:
                    h = hashlib.sha256(hash_dir)
                    hash_val = h.hexdigest()
                    if hash_val == hash_srch:
                        search_term = search_field
                    else:
                        continue
                
                if ((search_term in search_field and not search_exact) or 
                        (search_term == search_field and search_exact)):
                    if '	' in value.lower():
                        art_n = value.split('	')[0]
                    else:
                        art_n = value.strip()
                    if music_opt.lower() == "directory":
                        art_n = value
                    if music_opt.lower() == "fav-directory":
                        art_n = value
                    if music_opt.lower() == "playlist" or music_opt.lower() == "playlists":
                        pls = value.split('	')[0]
                        m = open_files(os.path.join(home, 'Playlists', pls), True)
                        for i in m:
                            i = i.replace('\n', '')
                            if i:
                                j = i.split('	')
                                i1 = j[0]
                                i2 = j[1]
                                try:
                                    i3 = j[2]
                                except:
                                    i3 = "None"
                                artist.append(i1+'	'+i2+'	'+i3)
                    else:
                        music_opt = music_opt[0].upper()+music_opt[1:]
                        if '-' in music_opt:
                            tmp = music_opt.split('-', 1)
                            sub_tmp = tmp[1]
                            music_opt = tmp[0]+'-'+sub_tmp[0].upper()+sub_tmp[1:]
                        m = ui.media_data.get_music_db(music_db, music_opt, art_n)
                        for i in m:
                            artist.append(i[1]+'	'+i[2]+'	'+i[0])
                    if (search_term == search_field and search_exact):
                        print('exact match:')
                        break
            epnArrList[:] = []
            for i in artist:
                epnArrList.append((i))
        elif site.lower().startswith("playlist"):
            epnArrList = []
            for index, value in enumerate(original_path_name):
                search_field = value.lower().split('	')[0]
                if ((search_term in  search_field and not search_exact) or 
                        (search_term == search_field and search_exact)):
                    pls = value.split('	')[0]
                    file_path = os.path.join(home, 'Playlists', str(pls))
                    if os.path.exists(file_path):
                        lines = open_files(file_path, True)
                        k = 0
                        for i in lines:
                            i = i.strip()
                            if i:
                                if not search_exact:
                                    i = i+'##'+pls
                                epnArrList.append(i)
        elif site.lower() == "video":
            epnArrList = []
            hash_srch = None
            if search_term.endswith('.hash'):
                hash_srch = search_term.rsplit('.', 1)[0]
                logger.debug(hash_srch)
            for index, value in enumerate(original_path_name):
                if '	' in value.lower():
                    art_n = value.split('	')[0]
                else:
                    art_n = value.strip()
                search_field = art_n.lower()
                if hash_srch:
                    hash_dir = bytes(value.split('\t')[1], 'utf-8')
                    h = hashlib.sha256(hash_dir)
                    hash_val = h.hexdigest()
                    if hash_val == hash_srch:
                        search_term = search_field
                    else:
                        continue
                if ((search_term in  search_field and not search_exact) or 
                        (search_term == search_field and search_exact)):
                    
                    name = art_n
                    video_dir = os.path.join(home, 'VideoDB')
                    logger.info('{0}--search-client--'.format(art_n))
                    video_db = os.path.join(video_dir, 'Video.db')
                    video_file = os.path.join(video_dir, 'Video.txt')
                    video_file_bak = os.path.join(video_dir, 'Video_bak.txt')
                    
                    artist = []
                    if not bookmark:
                        video_opt = site_option[0].upper()+site_option[1:]
                        print(video_opt, '---15112----')
                        if video_opt.lower() == "update" or video_opt.lower() == "updateall":
                            video_opt = "Available"
                        n_art_n = original_path_name[index].split('	')[-1]
                        m = ui.media_data.get_video_db(video_db, "Directory", n_art_n)
                        logger.info('{0}--{1}--search-client--14534--'.format(art_n, n_art_n))
                    else:
                        try:
                            new_dir_path = search_field.split('	')[-1]
                        except Exception as e:
                            print(e)
                        logger.info(new_dir_path)
                        if new_dir_path is not None:
                            if new_dir_path.lower() != 'none':
                                m = ui.media_data.get_video_db(
                                        video_db, "Directory", new_dir_path)
                            else:
                                m = ui.media_data.get_video_db(
                                        video_db, "Bookmark", art_n)
                        else:
                            m = ui.media_data.get_video_db(
                                    video_db, "Bookmark", art_n)
                        
                    for i in m:
                        artist.append(i[0]+'	'+i[1]+'	'+art_n)
                    
                    for i in artist:
                        epnArrList.append((i))
                    dir_path = os.path.join(home, 'Local', art_n)
                    if os.path.exists(dir_path):
                        picn = os.path.join(home, 'Local', art_n, 'poster.jpg')
                        thumbnail = os.path.join(home, 'Local', art_n, 'thumbnail.jpg')
                        fanart = os.path.join(home, 'Local', art_n, 'fanart.jpg')
                        summary1 = os.path.join(home, 'Local', art_n, 'summary.txt')
                        if os.path.exists(summary1):
                            summary = open_files(summary1, False)
                        else:
                            summary = "Not Available"
                    if (search_term == search_field and search_exact):
                        print('Exact Match:')
                        break
        return epnArrList
    
    def record_torrent(self, item, hist_folder):
        tmp_dir = TMPDIR
        name = ''
        if not os.path.exists(hist_folder):
            os.makedirs(hist_folder)
        if item.startswith('http') or os.path.isfile(item):
            home = hist_folder
            name1 = os.path.basename(item).replace('.torrent', '')
            torrent_dest1 = os.path.join(tmp_dir, name1+'.torrent')
            if not os.path.exists(torrent_dest1):
                if item.startswith('http'):
                    ccurl(item+'#'+'-o'+'#'+torrent_dest1)
                else:
                    shutil.copy(item, torrent_dest1)
            if os.path.exists(torrent_dest1):
                info = lt.torrent_info(torrent_dest1)
                name = info.name()
                torrent_dest = os.path.join(home, name+'.torrent')
                shutil.copy(torrent_dest1, torrent_dest)
            logger.info(name)
        elif item.startswith('magnet:'):
            torrent_handle, stream_session, info = get_torrent_info_magnet(
                item, tmp_dir, self, ui.progress, tmp_dir)
            torrent_file = lt.create_torrent(info)
            home = hist_folder
            name = info.name()
            torrent_dest = os.path.join(home, name+'.torrent')
            with open(torrent_dest, "wb") as f:
                f.write(lt.bencode(torrent_file.generate()))
            torrent_handle.pause()
            stream_session.pause()
            ui.stop_torrent_forcefully()
        if name:
            torrent_dest = os.path.join(home, name+'.torrent')
            info = lt.torrent_info(torrent_dest)
            file_arr = []
            for f in info.files():
                file_path = f.path
                file_path = os.path.basename(file_path)	
                file_arr.append(file_path)
            if file_arr:
                hist_path = os.path.join(home, 'history.txt')
                if not os.path.isfile(hist_path):
                    hist_dir, last_field = os.path.split(hist_path)
                    if not os.path.exists(hist_dir):
                        os.makedirs(hist_dir)
                    f = open(hist_path, 'w').close()
                if os.path.isfile(hist_path):
                    if (os.stat(hist_path).st_size == 0):
                        write_files(hist_path, name, line_by_line=True)
                    else:
                        lines = open_files(hist_path, True)
                        line_list = []
                        for i in lines:
                            i = i.strip()
                            line_list.append(i)
                        if name not in line_list:
                            write_files(hist_path, name, line_by_line=True)
                
                hist_site = os.path.join(hist_folder, name)
                if not os.path.exists(hist_site):
                    try:
                        os.makedirs(hist_site)
                        hist_epn = os.path.join(hist_site, 'Ep.txt')
                        write_files(hist_epn, file_arr, line_by_line=True)
                        torrent_extra = os.path.join(hist_site, 'title.torrent')
                        shutil.copy(torrent_dest, torrent_extra)
                    except Exception as e:
                        print(e)
        return name

    def epn_return_from_bookmark(self, tmp_bookmark, from_client=None):
        """
        tmp_bookmark = site+'&'+opt+'&'+siteName+'&'+name+'&'+
        str(video_local_stream)+'&'+str(row)+'&'+str(epn)
        """
        param_dict = ui.get_parameters_value(m='mirrorNo', c='category')
        mirrorNo = param_dict['mirrorNo']
        category = param_dict['category']
        tmp_arr = tmp_bookmark.split('&')
        logger.info(tmp_arr)
        clnt = from_client
        print(clnt, '--from--client--')
        logger.info(tmp_bookmark)
        si_te = tmp_arr[0]
        op_t = tmp_arr[1]
        site_name = tmp_arr[2]
        if len(tmp_arr) == 7:
            na_me = tmp_arr[3]
            if tmp_arr[4] == 'False':
                vi_deo_local_stream = False
            else:
                vi_deo_local_stream = True
            row = int(tmp_arr[5])
            ep_n = tmp_arr[6]
        elif len(tmp_arr) > 7:
            new_tmp_arr = tmp_arr[3:]
            row_index = -1
            local_stream_index = -1
            for i, j in enumerate(new_tmp_arr):
                if j.isnumeric():
                    row = int(j)
                    row_index = i
                if j.lower() == 'true' or j.lower() == 'false':
                    if j.lower() == 'false':
                        vi_deo_local_stream = False
                    else:
                        vi_deo_local_stream = True
                    local_stream_index = i
            if local_stream_index >= 0:
                na_me = '&'.join(new_tmp_arr[:-(len(new_tmp_arr)-local_stream_index)])
            if row_index >= 0:
                ep_n = '&'.join(new_tmp_arr[(row_index+1):])
            logger.info('\n{0}:{1}--879\n'.format(na_me, ep_n))
        finalUrl = ''
        plugin_path = os.path.join(home, 'src', 'Plugins', si_te+'.py')
        if os.path.exists(plugin_path):
            module = imp.import_module(si_te, plugin_path)
            si_te_var = getattr(module, si_te)(TMPDIR)
            
        if si_te in ["SubbedAnime", "DubbedAnime"]:
            if si_te == "SubbedAnime" and si_te_var:
                try:
                    finalUrl = si_te_var.getFinalUrl(
                        na_me, ep_n, mirrorNo,
                        ui.client_quality_val, site_name, category) 
                except Exception as err:
                    print(err, '--863--')
                    return 0
            elif si_te == "DubbedAnime" and si_te_var:
                try:
                    finalUrl = si_te_var.getFinalUrl(
                        na_me, ep_n, mirrorNo,
                        ui.client_quality_val, site_name, category) 
                except Exception as err:
                    print(err, '--872--')
                    return 0
        else:
            try:
                if vi_deo_local_stream:
                    if ui.https_media_server:
                        https_val = 'https'
                    else:
                        https_val = 'http'
                    finalUrl = https_val+"://"+ui.local_ip+':'+str(ui.local_port)+'/'
                    print(finalUrl, '=finalUrl--torrent--')
                    if ui.torrent_serve_thread.isRunning():
                        if ui.torrent_status_thread.isRunning():
                            get_next = 'Next'
                            if ui.torrent_handle.file_priority(row):
                                t_list = ui.stream_session.get_torrents()
                                logger.info('--18035---')
                                for i in t_list:
                                    old_name = i.name()
                                    logger.info('--check--{0}'.format(old_name))
                                    if old_name == na_me:
                                        get_next = 'Get Next'
                                        logger.info(get_next)
                                        break
                            finalUrl, ui.torrent_status_thread, ui.stream_session, ui.torrent_handle = ui.start_torrent_stream(
                                na_me, row, ui.local_ip+':'+str(ui.local_port),
                                get_next, ui.torrent_download_folder,
                                ui.stream_session, site_name=si_te, from_client=from_client)
                        else:
                            finalUrl, ui.torrent_status_thread, ui.stream_session, ui.torrent_handle = ui.start_torrent_stream(
                                na_me, row, ui.local_ip+':'+str(ui.local_port), 'Next',
                                ui.torrent_download_folder, ui.stream_session,
                                site_name=si_te, from_client=from_client)
                    else:
                        finalUrl, ui.torrent_serve_thread, ui.torrent_status_thread, ui.stream_session, ui.torrent_handle = ui.start_torrent_stream(
                            na_me, row, ui.local_ip+':'+str(ui.local_port), 'First Run', 
                            ui.torrent_download_folder, ui.stream_session, 
                            site_name=si_te, from_client=from_client)
                    ui.torrent_handle.set_upload_limit(ui.torrent_upload_limit)
                    ui.torrent_handle.set_download_limit(ui.torrent_download_limit)
                else:
                    finalUrlT = si_te_var.getFinalUrl(na_me, ep_n, mirrorNo, ui.client_quality_val)
                    logger.info("finalUrl:::::16704::::{0}:::\n".format(finalUrlT))
                    if isinstance(finalUrlT, list):
                        finalUrl = finalUrlT[0]
                    else:
                        finalUrl = finalUrlT
            except Exception as e:
                print(e)
        return finalUrl
