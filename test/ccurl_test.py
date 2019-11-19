import unittest
import sys
import os
from get_functions import ccurl, ccurlCmd, ccurlWget

class TestCcurl(unittest.TestCase):
    
    url = 'https://www.google.com'
    
    def setUp(self):
        BASEDIR, BASEFILE = os.path.split(os.path.abspath(__file__))
        parent_basedir, __ = os.path.split(BASEDIR)
        print(parent_basedir)
        sys.path.insert(0, parent_basedir)
        k_dir = os.path.join(parent_basedir, 'kawaii_player')
        sys.path.insert(0, k_dir)
        
    def test_curl(self):
        self.assertTrue(ccurl(self.url))
    
    def test_curlcmd(self):
        self.assertTrue(ccurlCmd(self.url))
        
    def test_curlWget(self):
        self.assertTrue(ccurlWget(self.url))
        
if __name__ == '__main__':
    
    unittest.main()
