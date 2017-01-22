import os
import sys
import shutil
import subprocess

BASEDIR,BASEFILE = os.path.split(os.path.abspath(__file__))
print(BASEDIR,BASEFILE,os.getcwd())

par_dir,cur_dir = os.path.split(BASEDIR)
src_dir = os.path.join(par_dir,'kawaii_player')

deb_config_dir = os.path.join(BASEDIR,'DEBIAN')
control_file = os.path.join(deb_config_dir,'control')

lines = open(control_file,'r').readlines() 
dest_dir = None

exec_file = os.path.join(BASEDIR,'kawaii-player')
desk_file = os.path.join(BASEDIR,'kawaii-player.desktop')
for i in lines:
	i = i.strip()
	if i.startswith('Version:'):
		version_num = i.replace('Version:','',1).strip()
		dest_dir = os.path.join(BASEDIR,'kawaii-player-'+version_num)
		break

usr_share = os.path.join(dest_dir,'usr','share','applications')
usr_bin = os.path.join(dest_dir,'usr','bin')
usr_share_kawaii = os.path.join(dest_dir,'usr','share','kawaii-player')

if dest_dir:
	if os.path.exists(dest_dir):
		shutil.rmtree(dest_dir)
	os.makedirs(dest_dir)
	os.makedirs(usr_share)
	os.makedirs(usr_bin)
	shutil.copytree(deb_config_dir,os.path.join(dest_dir,'DEBIAN'))
	shutil.copy(exec_file,usr_bin)
	shutil.copy(desk_file,usr_share)
	shutil.copytree(src_dir,usr_share_kawaii)
	subprocess.call(['dpkg-deb','--build',dest_dir])
	deb_pkg = os.path.basename(dest_dir)+'.deb'
	print('deb package created successfully in current directory. Now install the package using command: \n\nsudo gdebi {0}\n\n'.format(deb_pkg))
else:
	print('no version number in control file')
