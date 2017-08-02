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

from bs4 import BeautifulSoup
from player_functions import ccurl

class MusicArtist():

    def __init__(self):
        self.hdr = ''

    def getContentUnicode(self, content):
        if isinstance(content, bytes):
            print("I'm byte")
            try:
                content = str((content).decode('utf-8'))
            except:
                content = str(content)
        else:
            print(type(content))
            content = str(content)
            print("I'm unicode")
        return content

    def search(self, name, name_url):
        if not name_url:
            name = name.replace(' ', '+')
            url = "http://www.last.fm/search?q="+name
        else:
            url = name_url
        wiki = ""
        if not name_url:
            content = ccurl(url)
            soup = BeautifulSoup(content, 'lxml')

            link = soup.findAll('div', {'class':'row clearfix'})
            for i in link:
                j = i.findAll('a')
                for k in j:
                    try:
                        url = k['href']
                        if '?q=' not in url:
                            logger.info(url)
                            name = k.text
                            break
                    except:
                        pass

        if url.startswith('http'):
            url = url
        else:
            url = "http://www.last.fm" + url

        img_url = url+'/+images'
        wiki_url = url + '/+wiki'
        content = ccurl(wiki_url)
        soup = BeautifulSoup(content, 'lxml')
        link = soup.find('div', {'class':'wiki-content'})

        if link:
            wiki = link.text

        content = ccurl(img_url)
        soup = BeautifulSoup(content, 'lxml')
        link = soup.findAll('ul', {'class':'image-list'})
        img = []
        for i in link:
            j = i.findAll('img')
            for k in j:
                l = k['src']
                u1 = l.rsplit('/', 2)[0]
                u2 = l.split('/')[-1]
                u = u1 + '/770x0/'+u2
                img.append(u)
        img = list(set(img))
        print(len(img))
        img.append(wiki)
        return img
