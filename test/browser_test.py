import unittest
import sys
import os
from PyQt5 import QtWidgets

class TestBrowser(unittest.TestCase):
	
	def test_browser(self):
		from kawaii_player import Ui_MainWindow,MainWindowWidget
		app = QtWidgets.QApplication(sys.argv)
		MainWindow = MainWindowWidget()
		ui = Ui_MainWindow()
		ui.setupUi(MainWindow)
		ui.buttonStyle()
		ui.reviewsWeb(
			srch_txt='mushishi',review_site='tvdb',action='context_menu')
		MainWindow.show()
		app.exec_()
		
		
if __name__ == '__main__':
	global ui
	BASEDIR,BASEFILE = os.path.split(os.path.abspath(__file__))
	parent_basedir,__ = os.path.split(BASEDIR)
	print(parent_basedir)
	sys.path.insert(0,parent_basedir)
	k_dir = os.path.join(parent_basedir,'kawaii_player')
	sys.path.insert(0,k_dir)
	unittest.main()
