"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of tvdb-async.

tvdb-async is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

tvdb-async is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with tvdb-async.  If not, see <http://www.gnu.org/licenses/>.
"""

def search_onfinished(func):
    def wrapper(*args, **kargs):
        search_dict, search_n_grab = func(*args, **kargs)
        if search_n_grab:
            new_url = None
            for key,value in search_dict.items():
                if value:
                    new_url = value[1]
                    break
            if new_url:
                args[0].getinfo(new_url, onfinished=args[1], eps=args[3])
        else:
            args[1](search_dict, *args)
    return wrapper

def process_episodes_onfinished(func):
    def wrapper(*args, **kargs):
        obj, info = func(*args, **kargs)
        if obj:
            if isinstance(info, str):
                args[1](obj, 'episode-info')
            else:
                args[1](obj, info)
    return wrapper
    
def process_seasons_onfinished(func):
    def wrapper(*args, **kargs):
        obj = func(*args, **kargs)
        if obj:
            args[1](obj, 'season-info')
    return wrapper
    
def process_page_onfinished(func):
    def wrapper(*args, **kargs):
        obj = func(*args, **kargs)
        if obj:
            args[1](obj, 'info')
    return wrapper

def process_artwork_onfinished(func):
    def wrapper(*args, **kargs):
        obj, title = func(*args, **kargs)
        if obj:
            args[1](obj, title)
    return wrapper
