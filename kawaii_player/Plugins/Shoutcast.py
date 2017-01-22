import sys
import urllib
import pycurl
from io import StringIO,BytesIO
import re
import random
import subprocess
from subprocess import check_output
from bs4 import BeautifulSoup
import os
import os.path
from subprocess import check_output
import shutil
import json
from player_functions import ccurl,naturallysorted


class Shoutcast():
	def __init__(self,tmp):
		self.hdr = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'
		self.tmp_dir = tmp
	def getOptions(self):
			criteria = ['History','Genre']
			return criteria
		
	def getFinalUrl(self,name,epn,mir,quality):
		return epn
		
	def process_page(self,content):
		content = re.sub(r'\\',"-",content)
		#print(content)
		#f = open('/tmp/tmp.txt','w')
		#f.write(content)
		#f.close()
		try:
			l = json.loads(content)
		except:
			o = re.findall('{[^}]*}',content)
			l = []
			for i in o:
				print(i)
				try:
					j = json.loads(i)
					print(j['ID'],j['Name'])
					l.append(j)
				except:
					pass
					print('----------------------error---------------')
		s = []
		for i in l:
			try:
				#print(i['ID'],i['Name'],i['Bitrate'],i['Listeners'])
				s.append(i['Name'].replace('/','-')+'	id='+str(i['ID'])+'\nBitrate='+str(i['Bitrate'])+'\nListeners='+str(i['Listeners'])+'\n')
			except:
				pass
		return s
		
	def search(self,name):
		strname = str(name)
		print(strname)
		if name.lower() == 'tv':
			m = self.getCompleteList(name.upper(),1)
		else:
			url = "https://www.shoutcast.com/Home/BrowseByGenre"
			#content = ccurl(url,name,1)
			post = "genrename="+name
			content = ccurl(url+'#'+'-d'+'#'+post)
			m = self.process_page(content)
		return m
		
	def getCompleteList(self,opt,genre_num):
		if opt == 'Genre' and genre_num == 0:
			url = "http://www.shoutcast.com/"
			#content = ccurl(url,"",1)
			content = ccurl(url)
			m = re.findall('Genre[^"]name[^"]*',content)
			#print m
			j = 0
			for i in m:
				m[j] = re.sub('Genre[^"]name=','',i)
				m[j] = re.sub("[+]|%20",' ',m[j])
				j = j+1
			m.sort()
			print(m)
			#n = ["History","Genre","TV"]
			n = ["History","Genre"]
			m = n + m
		elif opt == 'History':
			a =0
		elif opt == 'TV':
			name = []
			track = []
			aformat = []
			listeners = []
			bitrate = []
			idr = []
			url = "http://thugie.nl/streams.php"
			#content = ccurl(url,"",4)
			content = ccurl(url)
			soup = BeautifulSoup(content,'lxml')
			tmp = soup.prettify()
			#m = soup.findAll('div',{'class':'boxcenterdir fontstyle'})
			#soup = BeautifulSoup(tmp,'lxml')
			m = []
			links = soup.findAll('div',{'class':'dirOuterDiv1 clearFix'})
			for i in links:
				j = i.findAll('a')
				q = i.find_next('h2')
				g = i.find_next('h4')
				z = g.find_next('h4')
				for k in j:
					idr.append(k['href'].split('=')[-1][:-1])
				l = i.text
				n = re.findall('Station:[^"]*',l)
				p = re.sub('Playing','\nPlaying',n[0])
				p=p.rstrip()
				a = p.split('\n')
				name.append(a[0].split(":")[1])
				track.append(a[1].split(':')[1])
				aformat.append(q.text)
				listeners.append(g.text)
				bitrate.append(z.text)
			for i in range(len(idr)):
				m.append(name[i].strip().replace('/','-')+'-TV	id='+str(idr[i]).replace('\\','')+'\nBitrate='+str(bitrate[i])+'\nListeners='+str(listeners[i])+'\n')
		else:
			url = "https://www.shoutcast.com/Home/BrowseByGenre"
			#content = ccurl(url,opt,1)
			post = 'genrename='+opt
			content = ccurl(url+'#'+'-d'+'#'+post)
			m = self.process_page(content)
		print(opt,url)
		return m
	
	def getEpnList(self,name,opt,depth_list,extra_info,siteName,category):
		name_id = (re.search('id=[^\n]*',extra_info).group()).split('=')[1]
		#nm = name.rsplit('-',1)
		#name = nm[0]
		#name_id = nm[1]
		#name = nm[0]
		file_arr = []
		id_station = int(name_id)
		station_url = ''
		if opt == "TV" or '-TV' in name:
			url = "http://thugie.nl/streams.php?tunein="+str(id_station)
			#content = ccurl(url,'',1)
			content = ccurl(url)
			final = re.findall('http://[^\n]*',content)
			station_url = final[0].rstrip()
			if 'stream.nsv' not in station_url:
				#print "Hello" + station_url
				station_url = str(station_url.rstrip()+";stream.nsv")
			
			
		else:
			url = "https://www.shoutcast.com/Player/GetStreamUrl"
			#content = ccurl(url,id_station,2)
			post = 'station='+str(id_station)
			content = ccurl(url+'#-d#'+post)
			m = re.findall('http://[^"]*',content)
			station_url = str(m[0])
		file_arr.append(name+'	'+station_url+'	'+'NONE')
		#file_arr.append('No.jpg')
		#file_arr.append('Summary Not Available')
		record_history = True
		return (file_arr,'Summary Not Available','No.jpg',record_history,depth_list)
		

	def getNextPage(self,opt,pgn,genre_num,name):
		m = []
		return m
