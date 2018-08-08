"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of aclh.

aclh is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

aclh is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with aclh.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging

class Logging:
    
    def __init__(self, name, file_name_log, TMPDIR):
        logging.basicConfig(level=logging.DEBUG)
        formatter_fh = logging.Formatter('%(asctime)-15s::%(module)s:%(funcName)s: %(levelname)-7s - %(message)s')
        formatter_ch = logging.Formatter('%(levelname)s::%(module)s::%(funcName)s: %(message)s')
        fh = logging.FileHandler(file_name_log)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter_ch)
        fh.setFormatter(formatter_fh)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
    
    def get_logger(self):
        return self.logger
    
    def info(self, *args):
        args_list = [str(i) for i in args]
        args_str = '; '.join(args_list)
        self.logger.info(args_str)
        
    def debug(self, *args):
        args_list = [str(i) for i in args]
        args_str = '; '.join(args_list)
        self.logger.debug(args_str)
        
    def warning(self, *args):
        args_list = [str(i) for i in args]
        args_str = '; '.join(args_list)
        self.logger.warning(args_str)
        
    def error(self, *args):
        args_list = [str(i) for i in args]
        args_str = '; '.join(args_list)
        self.logger.error(args_str)
        
    def set_level(self, level):
        level = level.lower()
        if level == 'info':
            self.logger.setLevel(logging.INFO)
        elif level == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif level in ['warning', 'warn']:
            self.logger.setLevel(logging.WARNING)
        elif level == 'error':
            self.logger.setLevel(logging.ERROR)
        
