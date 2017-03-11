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


from setuptools import setup
import os
import shutil

if os.name == 'posix':
	install_dependencies = ['PyQt5','pycurl','bs4','Pillow','mutagen','lxml','youtube_dl']
elif os.name == 'nt':
	install_dependencies = ['PyQt5','pycurl','bs4','Pillow','mutagen','lxml','youtube_dl','certifi']
setup(
    name='kawaii-player',
    version='1.1.0',
    license='GPLv3',
    author='kanishka-linux',
    author_email='kanishka.linux@gmail.com',
    url='https://github.com/kanishka-linux/kawaii-player',
    long_description="README.md",
    packages=['kawaii_player','kawaii_player.Plugins'],
    include_package_data=True,
    entry_points={'gui_scripts':['kawaii-player = kawaii_player.kawaii_player:main'],'console_scripts':['kawaii-player-console = kawaii_player.kawaii_player:main']},
    package_data={'kawaii_player':['tray.png','default.jpg','kawaii-player.desktop','input.conf','kawaii-player-start','1.png','Instructions','playlist.html']},
    install_requires=install_dependencies,
    description="A Audio/Video manager, multimedia player and portable media server",
)
