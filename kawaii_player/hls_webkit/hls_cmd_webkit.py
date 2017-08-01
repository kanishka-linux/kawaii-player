"""
Copyright (C) 2017 kanishka-linux kanishka.linux@gmail.com

This file is part of hlspy.

hlspy is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

hlspy is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with hlspy.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import os
import subprocess

if getattr(sys, 'frozen', False):
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(sys.executable))
else:
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(__file__))
sys.path.insert(0, BASEDIR)


from PyQt5 import QtWidgets
from hls_engine_webkit import BrowseUrlT

def define_path(file_name):
    hd, tl = os.path.split(file_name)
    file_path = os.path.join(os.getcwd(), tl)
    if hd:
        if os.path.exists(hd) and tl:
            file_path = file_name
    return file_path

def main():
    app = QtWidgets.QApplication(sys.argv)
    option_arr = [
        '--set-cookie-file=file.txt', '--use-cookie-file=file.txt', 
        '--cookie-end-pt=LAST_COOKIE_ID', 
        '--cookie-domain-name=select cookie from particular domain name', 
        '--user-agent=UA', '--tmp-dir=', '--output=out.html', '--js-file=file.js', 
        '--wait-for-cookie', '--print-request (print requested urls)', 
        '--select-request=(print selected request)', 
        '--print-cookies', '--default-block (enable default adblock)', 
        '--timeout=IN_SECONDS', '--block-request=', '--show-window', 
        '--show-window=wxh', '--grab-window=image.png', '--print-pdf=web.pdf', 
        '--set-html=', '--set-html-path=', '--get-link='
        ]
    launcher_template = """#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name={0}
Exec={1}
Terminal=false
NoDisplay=false
"""
    home = os.path.join(os.path.expanduser('~'), '.config', 'hlspy_webkit')
    if not os.path.exists(home):
        os.makedirs(home)
    url = sys.argv[-1]
    if url.startswith('--'):
        url = sys.argv[1]
    set_cookie = end_point = domain_name = user_agent = t_dir = use_cookie = None
    out_file = js_file = block_request = select_request = window_dim = print_pdf = None
    wait_for_cookie = print_request = print_cookies = default_block = False
    show_window = js_progress = False
    grab_window = set_html = set_html_path = get_link = js_raw = None
    js_progress_log = None
    timeout = 0
    for  j, i in enumerate(sys.argv):
        if i.startswith('--set-cookie-file='):
            set_cookie = i.split('=')[1]
        elif i.startswith('--use-cookie-file='):
            use_cookie = i.split('=')[1]
        elif i.startswith('--cookie-end-pt='):
            end_point = i.split('=')[1]
        elif i.startswith('--cookie-domain-name='):
            domain_name = i.split('=')[1]
        elif i.startswith('--user-agent='):
            user_agent = i.split('=')[1]
        elif i.startswith('--tmp-dir='):
            t_dir = i.split('=')[1]
        elif i.startswith('--js-file='):
            js_file = i.split('=')[1]
        elif i.startswith('--output='):
            print(i.split('='))
            out_file = i.split('=')[1]
            if out_file:
                if out_file.lower() == 'false' or out_file.lower() == 'true':
                    out_file = False
        elif i.startswith('--wait-for-cookie'):
            wait_for_cookie = True
        elif i.startswith('--print-request'):
            print_request = True
        elif i.startswith('--print-cookies'):
            print_cookies = True
        elif i.startswith('--timeout='):
            timeout = int(i.split('=')[1])
        elif i.startswith('--block-request='):
            block_request = i.split('=')[1]
        elif i.startswith('--default-block'):
            default_block = True
        elif i.startswith('--show-window'):
            show_window = True
            if '=' in i:
                window_val = i.split('=')[1]
                window_dim = '500'
                if window_val.lower() == 'true':
                    show_window = True
                elif window_val.lower() == 'false':
                    show_window = False
                else:
                    window_dim = window_val
        elif i.startswith('--js-progress'):
            if i.startswith('--js-progress-log='):
                js_progress_log = i.split('=')[1]
            else:
                js_progress = True
                if '=' in i:
                    js_val = i.split('=')[1]
                    if js_val.lower() == 'true':
                        js_progress = True
                    elif js_val.lower() == 'false':
                        js_progress = False
        elif i.startswith('--select-request='):
            select_request = i.split('=')[1]
        elif i.startswith('--grab-window'):
            grab_window = 'image.png'
            if '=' in i:
                grab_window = i.split('=')[1]
        elif i.startswith('--print-pdf'):
            print_pdf = 'web.pdf'
            if '=' in i:
                print_pdf = i.split('=')[1]
        elif i.startswith('--set-html'):
            set_html = i.split('=')[1]
        elif i.startswith('--get-link'):
            get_link = i.split('=')[1]
        elif i.startswith('--set-html-path'):
            set_html_path = i.split('=')[1]
        elif i.startswith('--js-raw'):
            js_raw = i.split('=')[1]
        elif i.startswith('--help'):
            for i in option_arr:
                print(i)
            sys.exit(0)
        elif i.startswith('--create-launcher='):
            launcher_name = i.split('=')[1]
            launcher_exec = ''
            for k, l in enumerate(sys.argv):
                #print(k, l)
                if k == 0:
                    if l == '__init__.py':
                        launcher_exec = 'hlspy'
                    else:
                        launcher_exec = l
                else:
                    if not l.startswith('--create-launcher='):
                        launcher_exec = launcher_exec + ' ' + l
                        
            edit_template = launcher_template.format(launcher_name, launcher_exec)
            
            if launcher_name and launcher_exec:
                launch_home = os.path.join(home, launcher_name+'.desktop')
                with open(launch_home, 'wb') as f:
                    f.write(edit_template.encode('utf-8'))
        elif i.startswith('--launch'):
            launcher_name = os.path.join(home, sys.argv[j+1] + '.desktop')
            if os.path.isfile(launcher_name):
                if sys.platform == 'linux':
                    subprocess.Popen(['xdg-open', launcher_name])
                    sys.exit(0)
                else:
                    with open(launcher_name, 'r') as f:
                        lines = f.readlines()
                    for l in lines:
                        if l.startswith('Exec='):
                            cmd = (l.replace('Exec=', '', 1).strip()).split(' ')
                            print(cmd, '--170--')
                            subprocess.Popen(cmd)
                            sys.exit(0)
            
    if t_dir is None:
        t_dir = home
    if set_cookie is not None:
        set_cookie = define_path(set_cookie)
        if os.path.isfile(set_cookie):
            os.remove(set_cookie)
        
    if use_cookie:
        use_cookie = define_path(use_cookie)
    
    if js_file:
        js_file = define_path(js_file)
    
    if set_html_path:
        set_html_path = define_path(set_html_path)
    
    if out_file:
        out_file = define_path(out_file)
    
    if print_pdf:
        print_pdf = define_path(print_pdf)
    
    if grab_window:
        grab_window = define_path(grab_window)
    
    if domain_name is None:
        if url.startswith('http'):
            domain_name = url.split('/')[2]
        else:
            domain_name = url
        domain_name = domain_name.replace('www.', '', 1)
    print(domain_name)
    if user_agent is None:
        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'
        
        
    web = BrowseUrlT(url=url, set_cookie=set_cookie, use_cookie=use_cookie, 
            end_point=end_point, domain_name=domain_name, user_agent=user_agent, 
            tmp_dir=t_dir, js_file=js_file, out_file=out_file, 
            wait_for_cookie=wait_for_cookie, print_request=print_request, 
            print_cookies=print_cookies, timeout=timeout, block_request=block_request, 
            default_block=default_block, select_request=select_request, 
            show_window=show_window, window_dim=window_dim, grab_window=grab_window, 
            print_pdf=print_pdf, set_html=set_html, set_html_path=set_html_path, 
            get_link=get_link, js_raw=js_raw, js_progress=js_progress, 
            js_progress_log=js_progress_log)
            
    ret = app.exec_()
    sys.exit(ret)

if __name__ == "__main__":
    main()
