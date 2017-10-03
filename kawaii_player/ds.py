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

class CustomList:
    
    def __init__(self):
        self.mylist = []
        self.index = -1
        self.ptr = -1
        
    def add_item(self, item):
        self.mylist.append(item)
        self.index = len(self.mylist) - 1
            
    
    def remove_item(self, item=None, index=None):
        if item is not None:
            try:
                i = self.mylist.index(item)
                del self.mylist[i]
                self.index = len(self.mylist) - 1
            except Exception as err:
                print(err, '--456--')
        elif index is not None:
            if isinstance(index, int):
                if index < len(self.mylist):
                    del self.mylist[index]
                    self.index = len(self.mylist) - 1
                    
    def get_prev(self):
        item = None
        if self.mylist:
            if self.ptr == -1:
                self.ptr = self.index
            else:
                self.ptr -= 1
            if self.ptr < len(self.mylist) and self.ptr >= 0:
                item = self.mylist[self.ptr]
            else:
                self.ptr = -1
        return item
        
    def get_next(self):
        item = None
        if self.mylist:
            if self.ptr == -1:
                self.ptr = 0
            else:
                self.ptr += 1
            if self.ptr < len(self.mylist) and self.ptr >= 0:
                item = self.mylist[self.ptr]
            else:
                self.ptr = -1
        return item
        
    def get_total(self):
        return self.index
        
    def get_ptr(self):
        return self.ptr
        
    def get_item(self, item=None, index=None):
        val = None
        if item is not None:
            try:
                i = self.mylist.index(item)
                val = self.mylist[i]
                self.ptr = i
            except Exception as err:
                print(err, '--83--')
        elif index is not None:
            if isinstance(index, int):
                if index < len(self.mylist) and index >=0:
                    val = self.mylist[index]
                    self.ptr = index
        elif self.mylist:
            val = self.mylist[-1]
            self.ptr = self.index
        return val
        
    def get_list(self):
        return self.mylist
        
    def clear(self):
        self.mylist.clear()
        self.index = -1
        self.ptr = -1
                
