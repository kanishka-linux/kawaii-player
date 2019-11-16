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
import urllib.parse
import subprocess
from io import BytesIO
try:
    import pycurl
except Exception as err:
    print(err)


USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:60.0) Gecko/20100101 Firefox/60.0'


def wget_string(url, dest, get_lib, rfr=None):
    hdr = USER_AGENT
    if  get_lib == 'pycurl' or get_lib == 'curl':
        if not rfr:
            command = ccurl_string_get(url, '-D', dest, download_manager=True)
        else:
            extra = rfr+'#'+dest
            command = ccurl_string_get(url, '-De', extra, download_manager=True)
    elif get_lib == 'wget':
        if not rfr:
            command = wget_string_get(url, dest, '-D', '', '', download_manager=True)
        else:
            command = wget_string_get(url, dest, '-De', rfr, '', download_manager=True)
    command = ' '.join(command)
    return command


def ccurl_string_get(url, opt, extra, download_manager=None):
    hdr = USER_AGENT
    if download_manager:
        hdr = '"'+hdr+'"'
        url = '"'+url+'"'
        if '#' not in extra:
            extra = '"'+extra+'"'
    if os.name == 'nt' and not download_manager:
        url = url.replace('&', '^&')
    url = url.replace(' ', '%20')
    if not opt and not extra:
        command = ["curl", "-L", "-A", hdr, url]
    elif opt == '-L':
        command = ["curl", "-A", hdr, url]
    elif opt == '-H':
        command = ["curl", "-I", "-A", hdr, url]
    elif opt == '-e':
        command = ["curl", '-L', "-A", hdr, "-e", extra, url]
    elif opt == '-o':
        if '#' in extra:
            picn, cookie = extra.split('#')
            command = ["curl", '-L', "-A", hdr, '-b', cookie, "-o", picn, url]
        else:
            picn = extra
            command = ["curl", '-L', "-A", hdr, "-o", picn, url]
    elif opt == '-D':
        command = ["curl", '-L', "-A", hdr, "-o", extra, url]
    elif opt == '-De':
        rfr, dst = extra.split('#')
        if download_manager:
            rfr = '"'+rfr+'"'
            dst = '"'+dst+'"'
        command = ["curl", '-L', "-A", hdr, '-e', rfr, "-o", dst, url]
    elif opt == '-b':
        command = ["curl", '-L', "-A", hdr, '-b', extra, url]
    elif opt == '-c':
        command = ["curl", '-L', "-A", hdr, '-c', extra, url]
    elif opt == '-bc':
        command = ["curl", '-L', "-A", hdr, '-c', extra, '-b', extra, url]
    elif opt == '-I':
        command = ["curl", '-L', "-I", "-A", hdr, url]
    elif opt == '-Ie':
        command = ["curl", '-L', "-I", "-A", hdr, '-e', extra, url]
    elif opt == '-Ib':
        command = ["curl", '-L', "-I", "-A", hdr, '-b', extra, url]
    elif opt == '-d':
        command = ["curl", '-L', "-A", hdr, '-d', extra, url]
    elif opt == '-postfile':
        command = ["curl", '-X', 'POST', '-d', '@{}'.format(extra), '-A', hdr, url]
    ver_peer = url.split('/')
    if len(ver_peer) > 3:
        ver_peer_get = ver_peer[3]
        if ver_peer_get.startswith('abs_path=') or ver_peer_get.startswith('master_abs_path='):
            if '-k' not in command:
                command.append('-k')
    command.append('-g')
    #command.append('-C -')
    #print(command)
    return command


def wget_string_get(url, dest, opt, extra, tmp_log, download_manager=None):
    hdr = USER_AGENT
    if download_manager:
        hdr = '"'+hdr+'"'
        url = '"'+url+'"'
        dest = '"'+dest+'"'
        if extra:
            extra = '"'+extra+'"'
    if os.name == 'nt' and not download_manager:
        url = url.replace('&', '^&')
    if not opt and not extra and dest:
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, url, "-O", dest]
    elif opt == '-L':
        command = ["wget", "--max-redirect=0", "--read-timeout=60", "--user-agent="+hdr, url, "-O", dest]
    elif opt == '-e':
        rfr = '--referer='+extra
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, rfr, url, "-O", dest]
    elif opt == '-o':
        if '#' in extra:
            picn, cookie = extra.split('#')
            ck = '--load-cookies='+cookie
            command = ["wget", "--read-timeout=60", ck, "--user-agent="+hdr, url, "-O", picn]
        else:
            if extra:
                command = ["wget", "--read-timeout=60", "--user-agent="+hdr, url, "-O", extra]
            else:
                command = ["wget", "--read-timeout=60", "--user-agent="+hdr, url, "-O", dest]
    elif opt == '-D':
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, url, "-O", dest]
    elif opt == '-De':
        rfr = '--referer='+extra
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, rfr, url, "-O", dest]
    elif opt == '-b':
        ck = '--load-cookies='+extra
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, ck, url, "-O", dest]
    elif opt == '-bc' or opt == '-c':
        sk = '--save-cookies='+extra
        command = ["wget", "--read-timeout=60", "--cookies=on", "--keep-session-cookies", 
                   sk, "--user-agent="+hdr, url, "-O", dest]
    elif opt == '-I':
        command = ["wget", '-o', tmp_log, "--server-response", "--spider", 
                   "--read-timeout=60", "--user-agent="+hdr, url]
    elif opt == '-H':
        command = ["wget", "--max-redirect=0", '-o', tmp_log, "--server-response", 
                   "--spider", "--read-timeout=60", "--user-agent="+hdr, url]
    elif opt == '-Ie':
        rfr = '--referer='+extra
        command = ["wget", '-o', tmp_log, "--server-response", "--spider", 
                   "--read-timeout=60", "--user-agent="+hdr, rfr, url]
    elif opt == '-Ib':
        ck = '--load-cookies='+extra
        command = ["wget", '-o', tmp_log, "--server-response", "--spider", 
                   "--read-timeout=60", "--user-agent="+hdr, ck, url]
    elif opt == '-d':
        post = '--post-data='+'"'+extra+'"'
        command = ["wget", "--read-timeout=60", "--user-agent="+hdr, post, url, "-O", dest]
    if os.name == 'nt':
        command.append('--no-check-certificate')
    command.append('-c')
    ver_peer = url.split('/')
    if len(ver_peer) > 3:
        ver_peer_get = ver_peer[3]
        if ver_peer_get.startswith('abs_path') and '&pl_id=' in ver_peer_get:
            if '--no-check-command' not in command:
                command.append('--no-check-certificate')
    return command


def getContentUnicode(content):
    if isinstance(content, bytes):
        try:
            content = str((content).decode('utf-8'))
        except:
            content = str(content)
    else:
        content = str(content)
    return content

def ccurlCmd(url, external_cookie=None, user_auth=None, verify_peer=None,
             curl_opt=None, out_file=None, referer=None, post_data=None):
    hdr = USER_AGENT
    if 'youtube.com' in url:
        hdr = 'Mozilla/5.0 (Linux; Android 4.4.4; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'

    print(url)
    if curl_opt:
        legacy = False
    else:
        curl_opt = ''
        picn_op = ''
        rfr = ''
        nUrl = url
        postfield = ''
        legacy = True
    extra = ''
    if not external_cookie:
        cookie_file = ''
    else:
        cookie_file = external_cookie
    if '#' in url and legacy:
        curl_opt = nUrl.split('#')[1]
        url = nUrl.split('#')[0]
        print(curl_opt, url, '----------------------------------')
        if curl_opt == '-o':
            picn_op = nUrl.split('#')[2]
            if cookie_file:
                extra = picn_op+'#'+cookie_file
            else:
                extra = picn_op
        elif curl_opt == '-Ie' or curl_opt == '-e':
            rfr = nUrl.split('#')[2]
            extra = rfr
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
              or curl_opt == '-Ib' or curl_opt == '-c'):
            cookie_file = nUrl.split('#')[2]
            extra = cookie_file
        elif curl_opt == '-d':
            post = nUrl.split('#')[2]
            post = post.replace('"', '')
            post = post.replace("'", '')
            extra = post
    else:
        wrong_param = False
        if curl_opt == '-o':
            if out_file:
                picn_op = extra = out_file
                if cookie_file:
                    extra = picn_op+'#'+cookie_file
            else:
                wrong_param = True
        elif curl_opt == '-Ie' or curl_opt == '-e':
            if referer:
                rfr = extra = referer
            else:
                wrong_param = True
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
               or curl_opt == '-Ib' or curl_opt == '-c'):
            if external_cookie:
                cookie_file = extra = external_cookie
            else:
                wrong_param = True
        elif curl_opt == '-d' or curl_opt == '-postfile':
            if post_data:
                post = extra = post_data
            else:
                wrong_param = True
        if wrong_param:
            print('--wrong parameters--')
            return ''
            
    print("\ndebug info for ccurlCmd url ={0} \n curl_opt = {1} \n extra = {2}\n".format(url, curl_opt, extra))
    command = ccurl_string_get(url, curl_opt, extra)
    if user_auth is not None:
        command.append('--user')
        command.append(user_auth)
    if verify_peer is False:
        if '-k' not in command:
            command.append('-k')
    content = ''
    print(' '.join(command))
    try:
        if os.name == 'posix':
            content = subprocess.check_output(command)
        else:
            content = subprocess.check_output(command, shell=True)
    except Exception as e:
        print(e, '--ccurl--error--')
    content = getContentUnicode(content)
    return content


def read_file_complete(file_path):
    if os.path.exists(file_path):
        content = ''
        try:
            f = open(file_path, 'r')
            content = f.read()
            f.close()
        except UnicodeDecodeError as e:
            try:
                print(e)
                f = open(file_path, encoding='utf-8', mode='r')
                content = f.read()
                f.close()
            except UnicodeDecodeError as e:
                print(e)
                f = open(file_path, encoding='ISO-8859-1', mode='r')
                content = f.read()
                f.close()
        except Exception as e:
            print(e)
            content = "Can't Decode"
    else:
        content = 'Not Able to Download'
    return content


def ccurlWget(url, external_cookie=None, user_auth=None, verify_peer=None,
              curl_opt=None, out_file=None, referer=None, post_data=None):
    hdr = USER_AGENT
    if 'youtube.com' in url:
        hdr = 'Mozilla/5.0 (Linux; Android 4.4.4; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'
    print(url)
    if curl_opt:
        legacy = False
    else:
        curl_opt = ''
        picn_op = ''
        rfr = ''
        nUrl = url
        postfield = ''
        legacy = True
    extra = ''
    if not external_cookie:
        cookie_file = ''
    else:
        cookie_file = external_cookie
    if '#' in url and legacy:
        curl_opt = nUrl.split('#')[1]
        url = nUrl.split('#')[0]
        print(curl_opt, url, '----------------------------------')
        if curl_opt == '-o':
            picn_op = nUrl.split('#')[2]
            if cookie_file:
                extra = picn_op+'#'+cookie_file
            else:
                extra = picn_op
        elif curl_opt == '-Ie' or curl_opt == '-e':
            rfr = nUrl.split('#')[2]
            extra = rfr
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
              or curl_opt == '-Ib' or curl_opt == '-c'):
            cookie_file = nUrl.split('#')[2]
            extra = cookie_file
        elif curl_opt == '-d':
            post = nUrl.split('#')[2]
            post = post.replace('"', '')
            post = post.replace("'", '')
            extra = post
    else:
        wrong_param = False
        if curl_opt == '-o':
            if out_file:
                picn_op = extra = out_file
                if cookie_file:
                    extra = picn_op+'#'+cookie_file
            else:
                wrong_param = True
        elif curl_opt == '-Ie' or curl_opt == '-e':
            if referer:
                rfr = extra = referer
            else:
                wrong_param = True
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
               or curl_opt == '-Ib' or curl_opt == '-c'):
            if external_cookie:
                cookie_file = extra = external_cookie
            else:
                wrong_param = True
        elif curl_opt == '-d':
            if post_data:
                post = extra = post_data
            else:
                wrong_param = True
        if wrong_param:
            print('--wrong parameters--')
            return ''
            
    tmp_dst = os.path.join(os.path.expanduser('~'), '.config', 'kawaii-player', 'tmp')
    if not os.path.exists(tmp_dst):
        os.makedirs(tmp_dst)
    tmp_html = os.path.join(tmp_dst, 'tmp_wget.html')
    tmp_log = os.path.join(tmp_dst, 'tmp_wget_log.txt')
    command = wget_string_get(url, tmp_html, curl_opt, extra, tmp_log)
    if user_auth is not None:
        try:
            user_name = user_auth.split(':')[0]
            user_passwd = user_auth.split(':')[1]
            command.append('--http-user='+user_name)
            command.append('--http-password='+user_passwd)
        except Exception as e:
            print(e)
    if verify_peer is False:
        if '--no-check-certificate' not in command:
                command.append('--no-check-certificate')
    content = ''
    #print(' '.join(command))
    try:
        if curl_opt != '-L' and curl_opt != '-d':
            if os.name == 'posix':
                subprocess.call(command)
            else:
                subprocess.call(command, shell=True)
    except Exception as e:
        print(e, '--wget--error--')

    if '-I' in curl_opt:
        if os.path.exists(tmp_log):
            content = read_file_complete(tmp_log)
        if '[following]' in content:
            content = content.replace(' [following]', '\n')
    elif curl_opt == '-L':
        content = ccurl(url+'#'+'-L')
    elif curl_opt == '-d':
        content = ccurl(url+'#'+'-d'+'#'+extra)
    else:
        if os.path.exists(tmp_html):
            content = read_file_complete(tmp_html)

    if os.path.exists(tmp_html):
        os.remove(tmp_html)
    if os.path.exists(tmp_log):
        os.remove(tmp_log)
    if '-I' in curl_opt:
        pass
    elif curl_opt == '-d':
        print('hello')
    return content


def ccurl(url, external_cookie=None, user_auth=None, verify_peer=None,
          curl_opt=None, out_file=None, referer=None, post_data=None,
          hdr_data=None):
    hdr = USER_AGENT
    if 'youtube.com' in url:
        hdr = 'Mozilla/5.0 (Linux; Android 4.4.4; SM-G928X Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.83 Mobile Safari/537.36'
    print(url)
    c = pycurl.Curl()
    if not external_cookie:
        cookie_file = ''
    else:
        cookie_file = external_cookie
    if curl_opt:
        legacy = False
    else:
        curl_opt = ''
        picn_op = ''
        rfr = ''
        nUrl = url
        postfield = ''
        legacy = True
    if hdr_data and isinstance(hdr_data, dict) and len(hdr_data) > 0:
        c.setopt(c.HTTPHEADER, [k+': '+v for k,v in hdr_data.items()])
    else:
        c.setopt(c.USERAGENT, hdr)
    if '#' in url and legacy:
        curl_opt = nUrl.split('#')[1]
        url = nUrl.split('#')[0]
        print(curl_opt, url, '----------------------------------')
        if curl_opt == '-o':
            picn_op = nUrl.split('#')[2]
        elif curl_opt == '-Ie' or curl_opt == '-e':
            rfr = nUrl.split('#')[2]
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
              or curl_opt == '-Ib' or curl_opt == '-c'):
            cookie_file = nUrl.split('#')[2]
        elif curl_opt == '-d':
            post = nUrl.split('#')[2]
            if '&' in post:
                postfield = post
            else:
                post = post.replace('"', '')
                post = post.replace("'", '')
                post1 = post.split('=')[0]
                post2 = post.split('=')[1]
                post_data = {str(post1):str(post2)}
                postfield = urllib.parse.urlencode(post_data)
            print(postfield, '--postfields--')
    else:
        wrong_param = False
        if curl_opt == '-o':
            if out_file:
                picn_op = out_file
            else:
                wrong_param = True
        elif curl_opt == '-Ie' or curl_opt == '-e':
            if referer:
                rfr = referer
            else:
                wrong_param = True
        elif (curl_opt == '-Icb' or curl_opt == '-bc' or curl_opt == '-b' 
               or curl_opt == '-Ib' or curl_opt == '-c'):
            if external_cookie:
                cookie_file = external_cookie
            else:
                wrong_param = True
        elif curl_opt == '-d':
            if post_data:
                post = post_data.replace('"', '')
                post = post_data.replace("'", '')
                post1 = post.split('=')[0]
                post2 = post.split('=')[1]
                post_data = {str(post1):str(post2)}
                postfield = urllib.parse.urlencode(post_data)
            else:
                wrong_param = True
        if wrong_param:
            print('--wrong parameters--')
            return ''
                
    url = str(url)
    try:
        c.setopt(c.URL, url)
    except UnicodeEncodeError as e:
        print(e, '--409--')
        c.setopt(c.URL, url.encode('utf-8'))
    storage = BytesIO()
    if os.name == 'nt':
        ca_cert = get_ca_certificate()
        if ca_cert:
            c.setopt(c.CAINFO, ca_cert)
        else:
            pass
    if verify_peer is False:
        c.setopt(c.SSL_VERIFYPEER, False)
    if curl_opt == '-o':
        c.setopt(c.FOLLOWLOCATION, True)
        if cookie_file:
            c.setopt(c.COOKIEFILE, cookie_file)
        try:
            f = open(picn_op, 'wb')
            c.setopt(c.WRITEDATA, f)
        except Exception as err:
            print(err, 'not able to write file')
            return 0
        try:
            ver_peer = url.split('/')
            if len(ver_peer) > 3 and os.name != 'nt':
                ver_peer_get = ver_peer[3]
                if (ver_peer_get.startswith('abs_path') or
                        ver_peer_get.startswith('master_abs_path')):
                    c.setopt(c.SSL_VERIFYPEER, False)
                    c.setopt(c.SSL_VERIFYHOST, False)
            c.perform()
            c.close()
        except Exception as err:
            print('failure in obtaining image try again', err)
        f.close()
    else:
        if curl_opt == '-I':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.NOBODY, 1)
            c.setopt(c.HEADERFUNCTION, storage.write)
        elif curl_opt == '-Ie':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(pycurl.REFERER, rfr)
            c.setopt(c.NOBODY, 1)
            c.setopt(c.HEADERFUNCTION, storage.write)
        elif curl_opt == '-e':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(pycurl.REFERER, rfr)
            c.setopt(c.WRITEDATA, storage)
        elif curl_opt == '-IA':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.NOBODY, 1)
            c.setopt(c.HEADERFUNCTION, storage.write)
        elif curl_opt == '-Icb':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.NOBODY, 1)
            c.setopt(c.HEADERFUNCTION, storage.write)
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            c.setopt(c.COOKIEJAR, cookie_file)
            c.setopt(c.COOKIEFILE, cookie_file)
        elif curl_opt == '-Ib':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.NOBODY, 1)
            c.setopt(c.HEADERFUNCTION, storage.write)
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            c.setopt(c.COOKIEFILE, cookie_file)
        elif curl_opt == '-bc':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.WRITEDATA, storage)
            c.setopt(c.COOKIEJAR, cookie_file)
            c.setopt(c.COOKIEFILE, cookie_file)
        elif curl_opt == '-L':
            c.setopt(c.WRITEDATA, storage)
        elif curl_opt == '-H':
            if hdr_data and isinstance(hdr_data, dict) and len(hdr_data) > 0:
                #c.setopt(c.HEADER, True)
                c.setopt(c.WRITEDATA, storage)
            else:
                c.setopt(c.NOBODY, 1)
                c.setopt(c.HEADERFUNCTION, storage.write)
        elif curl_opt == '-d':
            c.setopt(c.WRITEDATA, storage)
            c.setopt(c.POSTFIELDS, postfield)
        elif curl_opt == '-postfile':
            c.setopt(c.POST, 1)
            c.setopt(c.HTTPPOST, [("parameters",(c.FORM_FILE, post_data))])
            c.setopt(c.WRITEDATA, storage)
        elif curl_opt == '-b':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.WRITEDATA, storage)
            c.setopt(c.COOKIEFILE, cookie_file)
        elif curl_opt == '-c':
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.WRITEDATA, storage)
            c.setopt(c.COOKIEJAR, cookie_file)
        else:
            c.setopt(c.FOLLOWLOCATION, True)
            c.setopt(c.WRITEDATA, storage)
        try:
            if user_auth is not None:
                c.setopt(c.HTTPAUTH, c.HTTPAUTH_BASIC)
                c.setopt(c.USERPWD, user_auth)
            
            ver_peer = url.split('/')
            if len(ver_peer) > 3 and os.name != 'nt':
                ver_peer_get = ver_peer[3]
                if (ver_peer_get.startswith('abs_path') and
                        '&pl_id=' in ver_peer_get and verify_peer is not False):
                    c.setopt(c.SSL_VERIFYPEER, False)
            c.perform()
            c.close()
            content = storage.getvalue()
            content = getContentUnicode(content)
        except Exception as err:
            print(err, 'curl failure try again', '--523--')
            content = ''
        return content


def get_ca_certificate():
    ca_cert = ''
    if os.name == 'nt':
        try:
            import certifi
            ca_cert = certifi.where()
        except Exception as e:
            print(e)
    return ca_cert
