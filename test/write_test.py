import unittest
import sys
import os
import time

class TestWrite(unittest.TestCase):
    
    def test_write_line_by_line_list(self):
        content = ['This', 'is', 'Test', 'Case']
        self.assertIsNone(write_files(test_file, content, line_by_line=True, mode='test'))
        
    def test_write_append(self):
        content = 'append this line'
        self.assertIsNone(write_files(test_file, content, line_by_line=True, mode='test'))
        
    def test_write_block(self):
        content = 'write this line'
        self.assertIsNone(write_files(test_file, content, line_by_line=False, mode='test'))
    
if __name__ == '__main__':
    global home, test_file
    BASEDIR, BASEFILE = os.path.split(os.path.abspath(__file__))
    parent_basedir, __ = os.path.split(BASEDIR)
    sys.path.insert(0, parent_basedir)
    k_dir = os.path.join(parent_basedir, 'kawaii_player')
    sys.path.insert(0, k_dir)
    from player_functions import write_files, get_home_dir
    home = get_home_dir(mode='test')
    if not os.path.exists(home):
        os.makedirs(home)
    tmp_dir = os.path.join(home, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    test_file = os.path.join(tmp_dir, 'write_test.txt')
    print(test_file)
    unittest.main()
