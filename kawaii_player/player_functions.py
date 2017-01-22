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
from tempfile import mkstemp,mkdtemp
import urllib
import pycurl
from io import StringIO,BytesIO
import subprocess
import re
from get_functions import wget_string,get_ca_certificate
from PyQt5 import QtWidgets,QtGui,QtCore
import logging
#if os.name == 'nt':
#import tkinter

def send_notification(txt,display=None):
	try:
		if os.name == 'posix':
			subprocess.Popen(['notify-send',txt])
			#qmsg_message(txt)
		elif os.name == 'nt' and display != 'posix':
			qmsg_message(txt)
	except Exception as e:
		print(e)

def qmsg_message(txt):
	print(txt)
	#root = tkinter.Tk()
	#width = root.winfo_screenwidth()
	#height = root.winfo_screenheight()
	#print(width,height,'--screen--tk--')
	msg = QtWidgets.QMessageBox()
	msg.setGeometry(0,0,50,20)
	#msg.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
	msg.setWindowModality(QtCore.Qt.NonModal)
	msg.setWindowTitle("Kawaii-Player MessageBox")
	
	msg.setIcon(QtWidgets.QMessageBox.Information)
	msg.setText(txt+'\n\n(Message Will Autohide in 5 seconds)')
	msg.show()
	
	frame_timer = QtCore.QTimer()
	frame_timer.timeout.connect(lambda x=0:frame_options(msg))
	frame_timer.setSingleShot(True)
	frame_timer.start(5000)
	msg.exec_()
	
def frame_options(box):
	box.hide()
	
def open_files(file_path,lines_read=True):
	if os.path.exists(file_path):
		if lines_read:
			lines = ''
			try:
				f = open(file_path,'r')
				lines = f.readlines()
				f.close()
			except UnicodeDecodeError as e:
				try:
					print(e)
					f = open(file_path,encoding='utf-8',mode='r')
					lines = f.readlines()
					f.close()
				except UnicodeDecodeError as e:
					print(e)
					f = open(file_path,encoding='ISO-8859-1',mode='r')
					lines = f.readlines()
					f.close()
			except Exception as e:
				print(e)
				print("Can't Decode")
		else:
			lines = ''
			try:
				f = open(file_path,'r')
				lines = f.read()
				f.close()
			except UnicodeDecodeError as e:
				try:
					print(e)
					f = open(file_path,encoding='utf-8',mode='r')
					lines = f.read()
					f.close()
				except UnicodeDecodeError as e:
					print(e)
					f = open(file_path,encoding='ISO-8859-1',mode='r')
					lines = f.read()
					f.close()
			except Exception as e:
				print(e)
				lines = "Can't Decode"
	else:
		if lines_read:
			lines = []
		else:
			lines = 'Not Available'
	return lines


def get_config_options(file_name,value_field):
	req_val = ''
	if os.path.exists(file_name):
		lines = open_files(file_name,True)
		for i in lines:
			try:
				i,j = i.split('=')
			except Exception as e:
				print(e,'wrong values in config file')
				return req_val
			j = j.strip()
			if str(i.lower()) == str(value_field.lower()):
				req_val = j
				break
	return req_val


def naturallysorted(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key)] 
	return sorted(l, key = alphanum_key)


def replace_all(text, di):
	for i, j in di.iteritems():
		text = text.replace(i, j)
	return text


def get_tmp_dir():
	TMPDIR = ''
	try:
		option_file = os.path.join(os.path.expanduser('~'),'.config','kawaii-player','other_options.txt')
		tmp_option = get_config_options(option_file,'TMP_REMOVE')
		if tmp_option:
			if tmp_option.lower() == 'no':
				TMPDIR = os.path.join(os.path.expanduser('~'),'.config','kawaii-player','tmp')
			else:
				TMPDIR = mkdtemp(suffix=None,prefix='kawaii-player_')
		else:
			TMPDIR = os.path.join(os.path.expanduser('~'),'.config','kawaii-player','tmp')
	except Exception as e:
		print(e,'--error-in--creating--TEMP--Directory--') 
		TMPDIR = os.path.join(os.path.expanduser('~'),'.config','kawaii-player','tmp')
	return TMPDIR


def set_logger(file_name,TMPDIR):
	file_name_log = os.path.join(TMPDIR,file_name)
	log_file = open(file_name_log, "w", encoding="utf-8")
	logging.basicConfig(level=logging.DEBUG)
	formatter = logging.Formatter('%(asctime)-15s: %(levelname)-7s - %(message)s')
	ch = logging.StreamHandler(log_file)
	ch.setLevel(logging.DEBUG)
	ch.setFormatter(formatter)
	log = logging.getLogger(__name__)
	log.addHandler(ch)
	return log


def write_files(file_name,content,line_by_line):
	tmp_new_file = os.path.join(os.path.expanduser('~'),'.config','kawaii-player','tmp','tmp_write.txt')
	file_exists = False
	write_operation = True
	if os.path.exists(file_name):
		file_exists = True
		shutil.copy(file_name,tmp_new_file)
		#print('copying ',file_name,' to ',tmp_new_file)
	try:
		if type(content) is list:
			bin_mode = False
			f = open(file_name,'w')
			j = 0
			for i in range(len(content)):
				fname = content[i].strip()
				if j == 0:
					try:
						f.write(fname)
					except UnicodeEncodeError as e:
						#print(e,file_name+' will be written in binary mode')
						bin_mode = True
						f.close()
						break
				else:
					try:
						f.write('\n'+fname)
					except UnicodeEncodeError as e:
						#print(e,file_name+' will be written in binary mode')
						bin_mode = True
						f.close()
						break
				j = j+1
			if not bin_mode:
				f.close()
			else:
				f = open(file_name,'wb')
				j = 0
				for i in range(len(content)):
					fname = content[i].strip()
					if j == 0:
						f.write(fname.encode('utf-8'))
					else:
						f.write(('\n'+fname).encode('utf-8'))
					j = j+1
				f.close()
		else:
			if line_by_line:
				content = content.strip()
				if not os.path.exists(file_name) or (os.stat(file_name).st_size == 0):
					f = open(file_name,'w')
					bin_mode = False
					try:
						f.write(content)
					except UnicodeEncodeError as e:
						#print(e,file_name+' will be written in binary mode')
						f.close()
						bin_mode = True
						
					if bin_mode:
						f = open(file_name,'wb')
						f.write(content.encode('utf-8'))
						f.close()
				else:
					f = open(file_name,'a')
					bin_mode = False
					try:
						f.write('\n'+content)
					except UnicodeEncodeError as e:
						#print(e,file_name+' will be written in binary mode')
						f.close()
						bin_mode = True
						
					if bin_mode:
						f = open(file_name,'ab')
						f.write(('\n'+content).encode('utf-8'))
						f.close()
			else:
				f = open(file_name, 'w')
				bin_mode = False
				try:
					f.write(content)
				except UnicodeEncodeError as e:
					#print(e,file_name+' will be written in binary mode')
					f.close()
					bin_mode = True
				if bin_mode:
					f = open(file_name,'wb')
					f.write(content.encode('utf-8'))
					f.close()
	except Exception as e:
		write_operation = False
		print(e,'error in handling file, hence restoring original')
		if file_exists:
			shutil.copy(tmp_new_file,file_name)
			#print('copying ',tmp_new_file,' to ',file_name)
	if os.path.exists(tmp_new_file):
		if write_operation:
			#print('write operation on '+file_name+' successful')
			#print('Debug:write operation successful')
			pass
		else:
			print('Debug:write operation failed hence restored original')
			#print('write operation on '+file_name+' failed hence original restored')


get_lib = get_config_options(
			os.path.join(os.path.expanduser('~'),'.config','kawaii-player','other_options.txt'),
			'GET_LIBRARY')


if get_lib.lower() == 'pycurl':
	from get_functions import ccurl
	print('--using pycurl--')
elif get_lib.lower() == 'curl':
	from get_functions import ccurlCmd as ccurl
	print('--using curl--')
elif get_lib.lower() == 'wget':
	from get_functions import ccurlWget as ccurl
	print('--using wget--')
else:
	from get_functions import ccurl
	print('--using default pycurl--')

		
		
		
