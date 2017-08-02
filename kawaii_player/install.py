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
import platform
import sys
from os.path import expanduser

home_user = expanduser("~")
home = os.path.join(home_user, ".config", "kawaii-player")
nHome = os.path.join(home, 'src' )
pluginDir = os.path.join(nHome, 'Plugins')
if not os.path.exists(home):
    os.makedirs(home)

if not os.path.exists(nHome):
    os.makedirs(nHome)

if not os.path.exists(pluginDir):
    os.makedirs(pluginDir)


if os.path.exists(nHome):
    n = os.listdir(nHome)
    for i in n:
        k = os.path.join(nHome, i)
        if os.path.isfile(k):
            os.remove(k)

cwd = os.getcwd()
m = os.listdir(cwd)
for i in m:
    k = os.path.join(cwd, i)
    if os.path.isfile(k) and i != "install.py":
        shutil.copy(k, nHome)
    elif os.path.isdir(k) and i == "Plugins":
        p_dir_list = os.listdir(k)
        for j in p_dir_list:
            q = os.path.join(k, j)
            if os.path.isfile(q) and j != "installPlugins.py":
                shutil.copy(q, pluginDir)

f = open('kawaii-player.desktop', 'r')
lines = f.readlines()
f.close()
os_name = platform.platform()

os_name = os_name.lower()
print(os_name)
icon_path = os.path.join(nHome, 'tray.png')
icon_line = "Icon="+icon_path+'\n'
lines[4]=icon_line
if 'arch' in os_name:
    lines[5]="Exec=python "+nHome+'/kawaii_player.py '+'%u'+'\n'
else:
    lines[5]="Exec=python3 "+nHome+'/kawaii_player.py '+'%u'+'\n'
f = open(os.path.join(home, 'kawaii-player.desktop'), 'w')
for i in lines:
    f.write(i)
f.close()

picn = os.path.join(home, 'default.jpg')
if not os.path.exists(picn):
    shutil.copy('default.jpg', os.path.join(home, 'default.jpg'))
    
#dest_file = '/usr/share/applications/AnimeWatch.desktop'
dest_file = os.path.join(home_user, '.local', 'share', 'applications', 'kawaii-player.desktop')
print ('\nApplication Launcher Copying To:'+dest_file)

shutil.copy(os.path.join(home, 'kawaii-player.desktop'), dest_file)

print ("\nInstalled Successfully!\n")

print('If Application Launcher is not visible in Sound & Video or Multimedia, then manually copy '+home+'/kawaii-player.desktop to /usr/share/applications/ using "sudo"')

print ("\nIf You Are Running Ubuntu Unity then You'll have to either logout and login again or Reboot to see the kawaii-player Launcher in the Unity Dash Menu\n")
