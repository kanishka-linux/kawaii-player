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

def getContentUnicode(content):
    if isinstance(content, bytes):
        try:
            content = str((content).decode('utf-8'))
        except:
            content = str(content)
    else:
        content = str(content)
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
