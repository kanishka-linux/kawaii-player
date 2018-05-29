import re
import urllib.parse
from functools import partial
from vinanti import Vinanti
from bs4 import BeautifulSoup

class Backend:
    
    def __init__(self, hdrs):
        if hdrs:
            self.hdrs = hdrs
        else:
            self.hdrs = {'User-Agent':'Mozilla/5.0'}
        self.vnt = Vinanti(block=False, hdrs=self.hdrs, timeout=10)
    
    def search(self, nam, backend, onfinished, *args):
        if backend == 'g':
            self.get_glinks(nam, onfinished, *args)
        elif backend == 'ddg':
            self.get_ddglinks(nam, onfinished, *args)
    
    def get_ddglinks(self, nam, onfinished, *args):
        url = "https://duckduckgo.com/html/"
        params = {'q':'{} tvdb'.format(nam)}
        self.vnt.get(url, params=params, onfinished=partial(self.process_ddgsearch, onfinished, *args))
    
    def process_ddgsearch(self, onfinished, *args):
        m = []
        result = args[-1]
        soup = BeautifulSoup(result.html, 'lxml')
        div_val = soup.findAll('h2', {'class':'result__title'})
        for div_l in div_val:
            new_url = div_l.find('a')
            if 'href' in str(new_url):
                new_link = new_url['href']
                final_link = re.search('http[^"]*', new_link).group()
                if ('tvdb.com' in final_link and 'tab=episode' not in final_link 
                        and 'tab=seasonall' not in final_link):
                    m.append(urllib.parse.unquote(final_link))
                if m:
                    break
        onfinished(m.copy(), *args)
        
    def get_glinks(self, nam, onfinished, *args):
        url = "https://www.google.co.in/search"
        params = {'q':'{} tvdb'.format(nam)}
        self.vnt.get(url, params=params, onfinished=partial(self.process_gsearch, onfinished, *args))
    
    def process_gsearch(self, onfinished, *args):
        result = args[-1]
        soup = BeautifulSoup(result.html, 'html.parser')
        m = soup.findAll('a')
        links = []
        for i in m:
            if 'href' in str(i):
                x = urllib.parse.unquote(i['href'])
                y = ''
                if 'thetvdb.com' in x:
                    y = re.search('thetvdb.com[^"]*tab=series[^"]*', x)
                if y:
                    y = y.group()
                    y = 'https://'+y
                    y = urllib.parse.unquote(y)
                    y = y.replace(' ', '%20')
                    y = re.sub('\&sa[^"]*', '', y)
                    links.append(y)
        onfinished(links.copy(), *args)
