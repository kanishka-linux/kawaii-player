import os
import sys
import site
import shutil
import subprocess

BASEDIR,BASEFILE = os.path.split(os.path.abspath(__file__))
print(BASEDIR,BASEFILE,os.getcwd())

sitepkg = site.getsitepackages()[0]

par_dir,cur_dir = os.path.split(BASEDIR)

os.chdir(par_dir)

subprocess.call(["pip3", "wheel", "."])

whl = list(filter(lambda x: x.endswith(".whl"), os.listdir(par_dir)))[0]

whl_path = os.path.join(par_dir, whl)
shutil.copy(whl_path, BASEDIR)

os.chdir(BASEDIR)

subprocess.call(["unzip", whl])

mpv_so = list(filter(lambda x: x.endswith(".so"), os.listdir(BASEDIR)))[0]

mpv_so_file = os.path.join(BASEDIR, mpv_so)

extra_dir = os.path.join(BASEDIR, "kawaii_player")

shutil.rmtree(extra_dir)

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
lib_path = os.path.join(dest_dir, sitepkg[1:])
usr_share_kawaii = os.path.join(dest_dir,'usr','share','kawaii-player')

class DpkgDebError(Exception):
	pass

if dest_dir:
	if os.path.exists(dest_dir):
		shutil.rmtree(dest_dir)
	os.makedirs(dest_dir)
	os.makedirs(usr_share)
	os.makedirs(usr_bin)
	os.makedirs(lib_path)
	shutil.copytree(deb_config_dir,os.path.join(dest_dir,'DEBIAN'))
	shutil.copy(exec_file,usr_bin)
	shutil.copy(desk_file,usr_share)
	shutil.copy(mpv_so_file,lib_path)
	shutil.copytree(src_dir,usr_share_kawaii)
	dpkg_errcode = subprocess.call(['dpkg-deb','--build',dest_dir])
	deb_pkg = './'+os.path.basename(dest_dir)+'.deb'
	if not dpkg_errcode:
		if os.path.exists(deb_pkg):
			print('.deb package created successfully in current directory. Now install the package using command: \n\nsudo apt install {}\n\n'.format(deb_pkg))
		else:
			raise FileNotFoundError('{} not found'.format(deb_pkg))
	else:
		raise DpkgDebError
else:
	print('no version number in control file')
