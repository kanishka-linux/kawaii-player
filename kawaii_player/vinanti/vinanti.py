"""
Copyright (C) 2018 kanishka-linux kanishka.linux@gmail.com

This file is part of vinanti.

vinanti is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

vinanti is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with vinanti.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import asyncio
import urllib.parse
from urllib.parse import urlparse
import urllib.request
from functools import partial
from threading import Thread
from collections import OrderedDict
try:
    from vinanti.req import RequestObject
    from vinanti.log import log_function
except ImportError:
    from req import RequestObject
    from log import log_function
logger = log_function(__name__)


class Vinanti:
    
    def __init__(self, backend=None, block=True, log=False, group_task=False, **kargs):
        if backend is None:
            self.backend = 'urllib'
        else:
            self.backend = backend
        self.block = block
        if self.block is None:
            self.loop = None
        else:
            self.loop = asyncio.get_event_loop()
        self.tasks = OrderedDict()
        self.loop_nonblock_list = []
        self.log = log
        self.group_task = group_task
        if not self.log:
            logger.disabled = True
        self.global_param_list = ['method', 'hdrs', 'onfinished']
        if kargs:
            self.session_params = kargs
            self.method_global = self.session_params.get('method')
            self.hdrs_global = self.session_params.get('hdrs')
            self.onfinished_global = self.session_params.get('onfinished')
        else:
            self.session_params = {}
            self.method_global = 'GET'
            self.hdrs_global = None
            self.onfinished_global = None
        self.tasks_completed = {}
        self.tasks_timing = {}
        self.cookie_session = {}
        
    def clear(self):
        self.tasks.clear()
        self.tasks_completed.clear()
        self.loop_nonblock_list.clear()
        self.session_params.clear()
        self.method_global = 'GET'
        self.hdrs_global = None
        self.onfinished_global = None
    
    def tasks_count(self):
        return len(self.tasks_completed)
    
    def tasks_done(self):
        tasks_copy = self.tasks_completed.copy()
        count = 0
        for key, val in tasks_copy.items():
            if val:
                count += 1
        return count
        
    def tasks_remaining(self):
        tasks_copy = self.tasks_completed.copy()
        count = 0
        for key, val in tasks_copy.items():
            if not val:
                count += 1
        return count
    
    def __build_tasks__(self, urls, method, onfinished=None, hdrs=None, options_dict=None):
        self.tasks.clear()
        if options_dict is None:
            options_dict = {}
        if self.session_params:
            global_params = [method, hdrs, onfinished, options_dict]
            method, onfinished, hdrs, options_dict = self.set_session_params(*global_params)
        if self.block is None:
            req = None
            print(urls)
            if isinstance(urls, str):
                req = self.__get_request__(urls, hdrs, method, options_dict)
                return req
        else:
            task_dict = {}
            if not isinstance(urls, list):
                urls = [urls]
            for i, url in enumerate(urls):
                length = len(self.tasks)
                length_new = len(self.tasks_completed)
                task_list = [url, onfinished, hdrs, method, options_dict, length_new]
                task_dict.update({i:task_list})
                self.tasks.update({length:task_list})
                self.tasks_completed.update({length_new:False})
            if task_dict and not self.group_task:
                self.start(task_dict)
    
    def set_session_params(self, method, hdrs, onfinished, options_dict):
        if not method and self.method_global:
            method = self.method_global
        if not hdrs and self.hdrs_global:
            hdrs = self.hdrs_global.copy()
        if not onfinished and self.onfinished_global:
            onfinished = self.onfinished_global
        for key, value in self.session_params.items():
            if key not in options_dict and key not in self.global_param_list:
                options_dict.update({key:value})
        return method, onfinished, hdrs, options_dict
    
    def get(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'GET', onfinished, hdrs, kargs)
    
    def post(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'POST', onfinished, hdrs, kargs)
        
    def head(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'HEAD', onfinished, hdrs, kargs)
    
    def put(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'PUT', onfinished, hdrs, kargs)
        
    def delete(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'DELETE', onfinished, hdrs, kargs)
        
    def options(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'OPTIONS', onfinished, hdrs, kargs)
        
    def patch(self, urls, onfinished=None, hdrs=None, **kargs):
        return self.__build_tasks__(urls, 'PATCH', onfinished, hdrs, kargs)
    
    def function(self, urls, *args, onfinished=None):
        self.__build_tasks__(urls, 'FUNCTION', onfinished, None, args)
        
    def function_add(self, urls, *args, onfinished=None):
        length_new = len(self.tasks_completed)
        task_list = [urls, onfinished, None, 'FUNCTION', args, length_new]
        length = len(self.tasks)
        self.tasks.update({length:task_list})
        self.tasks_completed.update({length_new:False})
    
    def add(self, urls, onfinished=None, hdrs=None, method=None, **kargs):
        if self.session_params:
            global_params = [method, hdrs, onfinished, kargs]
            method, onfinished, hdrs, kargs = self.set_session_params(*global_params)
        if isinstance(urls, str):
            length = len(self.tasks)
            length_new = len(self.tasks_completed)
            task_list = [urls, onfinished, hdrs, method, kargs, length_new]
            self.tasks.update({length:task_list})
            self.tasks_completed.update({length_new:False})
            
    def __start_non_block_loop__(self, tasks_dict, loop):
        asyncio.set_event_loop(loop)
        tasks = []
        for key, val in tasks_dict.items():
            url, onfinished, hdrs, method, kargs, length = val
            tasks.append(asyncio.ensure_future(self.__start_fetching__(url, onfinished, hdrs, length, loop, method, kargs))) 
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
        
    def start(self, task_dict=None):
        logger.info(task_dict)
        if self.group_task:
            task_dict = self.tasks
        if self.block is True and task_dict:
            if not self.loop.is_running():
                self.__event_loop__(task_dict)
            else:
                logger.debug('loop running: {}'.format(self.loop.is_running()))
        elif self.block is False and task_dict:
            new_loop = asyncio.new_event_loop()
            loop_thread = Thread(target=self.__start_non_block_loop__, args=(task_dict, new_loop))
            self.loop_nonblock_list.append(loop_thread)
            self.loop_nonblock_list[len(self.loop_nonblock_list)-1].start()
                
    def __event_loop__(self, tasks_dict):
        tasks = []
        for key, val in tasks_dict.items():
            url, onfinished, hdrs, method, kargs, length = val
            tasks.append(asyncio.ensure_future(self.__start_fetching__(url, onfinished, hdrs, length, self.loop, method, kargs))) 
        self.loop.run_until_complete(asyncio.gather(*tasks))
    
    def __update_hdrs__(self, hdrs, netloc):
        if hdrs:
            hdr_cookie = hdrs.get('Cookie')
        else:
            hdr_cookie = None
        cookie = self.cookie_session.get(netloc)
        if cookie and not hdr_cookie:
            hdrs.update({'Cookie':cookie})
        elif cookie and hdr_cookie:
            if hdr_cookie.endswith(';'):
                new_cookie = hdr_cookie + cookie
            else:
                new_cookie = hdr_cookie + ';' + cookie
            hdrs.update({'Cookie':new_cookie})
        return hdrs
    
    def __get_request__(self, url, hdrs, method, kargs):
        n = urlparse(url)
        netloc = n.netloc
        old_time = self.tasks_timing.get(netloc)
        wait_time = kargs.get('wait')
        session = kargs.get('session')
        if session:
            hdrs = self.__update_hdrs__(hdrs, netloc)
            
        if old_time and wait_time:
            time_diff = time.time() - old_time
            while(time_diff < wait_time):
                logger.info('waiting in queue..{} for {}s'.format(netloc, wait_time))
                time.sleep(wait_time)
                time_diff = time.time() - self.tasks_timing.get(netloc)
        self.tasks_timing.update({netloc:time.time()})
        
        req_obj = None
        kargs.update({'log':self.log})
        if self.backend == 'urllib':
            req = RequestObject(url, hdrs, method, kargs)
            req_obj = req.process_request()
            if session:
                self.__update_session_cookies__(req_obj, netloc)
        return req_obj
        
    def __update_session_cookies__(self, req_obj, netloc):
        old_cookie = self.cookie_session.get(netloc)
        new_cookie = req_obj.session_cookies
        cookie = old_cookie
        if new_cookie and old_cookie:
            if new_cookie not in old_cookie:
                cookie = old_cookie + ';' + new_cookie
        elif not new_cookie and old_cookie:
            pass
        elif new_cookie and not old_cookie:
            cookie = new_cookie
        if cookie:
            self.cookie_session.update({netloc:cookie})
        
    async def __start_fetching__(self, url, onfinished, hdrs, task_num, loop, method, kargs):
        if isinstance(url, str):
            logger.info('\nRequesting url: {}\n'.format(url))
            future = loop.run_in_executor(None, self.__get_request__, url, hdrs, method, kargs)
        else:
            future = loop.run_in_executor(None, self.__complete_request__, url, hdrs, method, kargs)
        if onfinished:
            future.add_done_callback(partial(onfinished, task_num, url))
        response = await future
        self.tasks_completed.update({task_num:True})
        
    def __complete_request__(self, url, args, method, kargs):
        req_obj = url(*kargs)
        return req_obj
