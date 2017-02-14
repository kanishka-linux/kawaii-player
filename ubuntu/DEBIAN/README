# Kawaii-Player

Kawaii-Player is Audio/Video manager and mutlimedia player (based on mpv and mplayer), along with functionalities of portable media server. It can be simply used as normal mutimedia frontend for mpv/mplayer, or it can be turned into portable media server on the fly. 

## Index

[Features](#features)

[Normal Mode](#normal-mode)

[Playing Mode](#playing-mode)

[Thumbnail Mode](#thumbnail-mode)

[Minimal Music Player](#minimal-music-player)

[Detached Video Mode](#detached-video-mode)

[Torrent Streaming Player] (#torrent-streaming)

[Media Server](#media-server)

[Universal Playlist Generation](#universal-playlist-generation)

[YouTube Player](#youtube-support)

[Addons (Plugins) Structure] (#addon-structure)

[Dependencies and Installation](#dependencies-and-installation)

[Troubleshooting](#troubleshooting)

[Brief Documentation](#documentation)

## Features

1.  Combine Audio-Video Player and Manager.

2.  Bookmark and categorize series in the library (like Watching, Incomplete, Interesting etc..).

3.  Good audio-video management functionalities using sqlite3.

4.  Custom Addons Support for viewing content of various sites directly on the player.

5.  Support for downloading fanart/posters and other information such as summary or biography from internet sites such as TVDB and last.fm.

6.  Thumbnail Grid Mode Support.

7.  Internal web browser with custom right click menu for manually downloading desired fanart and poster for library collection.

8.  System Tray Support (Current tray icon is temporary which may change in future).

9.  Proper MPRIS2 support and integration with sound menu applet.

10. Custom Playlist and queueing support.

11. Remembers most of the last settings, and can opens up directly last watched series in the library.

12. Special Minimal Mode Music Player for listening only music (Available in System Tray context menu).

13. Proper History Manager for both addons and local content.

14. Bookmark support for both Audio, Video and Addons.

15. mplayer/mpv internal player.

16. Better buffer management for mplayer on low bandwidth network.

17. Support for opening video in external players like vlc, smplayer or kodi.

18. Torrent streaming player.

19. Media Server capability.

20. Youtube wrapper using qtwebengine/qtwebkit.

21. Detached Video Mode.

22. Universal Playlist Generation.

## Normal Mode 
######[Index](#index)
![kawaii-player](/Images/Video.png)

## Playing Mode
######[Index](#index)
![kawaii-player](/Images/Watch.png)

It tries to be a simple media manager for your audio and video collection, along with powerful playing capabilities of mpv and mplayer. You can organise your collection properly into various groups and categories such as watching,incomplete etc.. You can create your own group also for any special category in the bookmark section.  It will also keep track of number of episodes that you have watched in a series. It will also manage history ,and you will have complete control over it.

You can fetch fanart and posters from TVDB website. If proper match is not found then you can directly go to the website using inbuilt browser. In the inbuilt browser right click has been tweaked, so that when when you find relevant url of fanart ,poster or anime; you can directly right click on the option to save it as fanart or poster or find anime info. In the same way you can find Episode Names or thumbnails of the TV shows. If you are in Music section then you can use the inbuilt browser to get artist information and poster directly from Last.fm, if default perfect match is not found.

User can make as many playlists as possible. It is possible to merge various playlists. Users can combine local audio, local video and external url into the playlist.

## Thumbnail Mode
######[Index](#index)
![kawaii-player](/Images/Thumbnail.png)

Users can see their entire collection in Thumbnail mode in Grid Layout, once your collection is ready with appropriate fanart or posters. Use this thumbnail mode if you have more than 2 GB of RAM. Otherwise your system may slow down. 

In thumbnail mode, Thumbnails of local video files are automatically generated with the help of 'ffmpegthumbnailer'.You can watch video in thumbnail itself by selecting right mode from 2 to 4. If you don't like generated thumbnail then you can change it by right clicking and selecting appropriate option from the context menu.

## Minimal Music Player
######[Index](#index)
![kawaii-player](/Images/Music.png)

It supports certain MPRIS D-bus functionalities. Therefore if you have created global keyboard shortcuts for play/pause,Next,Previous or Stop then they can work with this player also. Make sure python-dbus is installed on system to use this feature.

It is not very powerful music organizer, but provide certain decent functionalities. When using with mplayer, it's cpu usage is just 1-2 % which makes it very ideal for low end machines.

## Detached Video Mode
######[Index](#index)
![kawaii-player](/Images/Detached_Mode.png)

The Player contains Detached video mode, which can be activated by right clicking tray icon and selecting appropriate entry.
In this mode, video will be detached from the main application window and can float anywhere on the desktop. By default it has titlebar, which users can remove by activating frameless mode from system tray context menu. Users can make this detached video of any size and can position it anywhere on the desktop which will remain above all the windows. In lightweight desktop sessions like LXDE there is very simple sound menu applet which does not integrate music and any other extra functionalities. By using this mode, it is possible to use it as a system tray widget with many advance features with which you can quickly control your media (both audio and video) which is being played in the player, similar to sound menu applet of Unity or GNOME.

## Torrent Streaming
######[Index](#index)
It is possible to play audio/video torrent directly with this player similar to any streaming media. By default the torrent will stream at 'http://127.0.0.1:8001', which is loop-back address of your local machine. You can change this default streaming IP and port location by manually editing 'torrent_config.txt' file located in '~/.config/kawaii-player'. If you set 'TORRENT_STREAM_IP' field to your local network IP address which normally starts with something like '192.168.x.y' (You can check default ip using 'ifconfig' command), then it is possible to access the playing media from any device on your local network. For example, if the media is being played at computer A with TORRENT_STREAM_IP set to your default local ip address '192.168.1.1:8001', then you can access that media from computer B on the same network by simply connecting to 'http://192.168.2.1:8001'. If you have mplayer or mpv installed on computer B , then you can simply type the command 'mplayer http://192.168.2.1:8001' on that computer, to access the media which is being streamed on computer A. 

In 'torrent_config.txt' you can set some other fields like upload , download rate in (KBps) and default download location.

Now with inclusion of torrent streaming feature, it's possible to write addons based on torrenting capability.

For opening torrents within this player, goto Addons->Torrent->Open and enter torrent file name or torent url or magnet link inside the input dialog box, and then select appropriate entry which will appear in either Title list or Playlist. Your list of visited torrents will be accessible from the 'History' section. 

This feature is based on libtorrent-rasterbar {which is being used by bittorrent clients like qBittorrent and deluge} and it's python3 bindings. If you've installed latest version of libtorrent-rasterbar then python3 bindings are included along with it. In systems where older version of libtorrent-rasterbar is installed, users need to install python3-libtorrent to use this feature.  

Once Torrent streaming will start, a progress bar will appear to the right side, which will show basic information about torrent.
If user will click on this progress bar then they will get controls for stopping torrent and for setting upload/download speed.

If torrent contains multiple files then users can enqueue the desired files by selecting appropriate entry in Playlist column and pressing 'key q'.
 
Note: Key 'q' used on playing video will quit the playing instance, and the same key 'q' used on playlist column will queue the item.

## Media Server
######[Index](#index)
The media server functionality can be started by clicking 'More' button, and selecting 'Start Media Server' option. By default media server will start on 'http://127.0.0.1:9001' i.e. default loop-back address of your machine. In order to use it as media server which can be accessed from any device on the same local network, you have to change this loop-back address '127.0.0.1' to your local network address which normally starts with '192.168.x.y'. You can check, default local network address using cli tools like 'ifconfig' on any gnu/linux based systems. Once you know local network address of your server, then manually edit '~/.config/kawaii-player/other_options.txt' file and change the field "LOCAL_STREAM_IP" appropriately with local network address (or user can change it from settings menu). Once you've set up the 'LOCAL_STREAM_IP' field properly, then you should be able to access the current playlist on the kawaii-player, from any device on the network. 

For example, if server address is set to '192.168.1.1:9001', then you should be able to access the current running file in the playlist at the address 'http://192.168.1.1:9001/play' or 'http://192.168.2.1:9001/'. If user will use this media server IP address in repeat (loop) mode on the client side, then the client will automatically play everything, which is being played by the media server in it's playlist.


**A very simple web interface** has been provided for media server, from which users can access their audio/video collection managed by kawaii-player player. If your media server is '192.168.1.1:9001', then web interface can be opened at **192.168.1.1:9001/stream_continue.htm**. From this interface, users can generate universal playlist in m3u format which can be played by any media player on the local network, which supports http streaming such as mpv,vlc etc..and that too on any platform. If users don't want to open web interface then they can get the media server playlist directly on any player by opening url 'http://192.168.1.1:9001/stream_continue.m3u' from within the player itself, and the current media server playlist will be directly available in the player. Alternatively users can use curl or wget to get the playlist, and save it with extension '.m3u', which then can be opened with any player which recognizes the m3u format.

In local home network, if cookie and https is not enabled for media server then, one can access various media server playlists directly from vlc using simple urls.  

If url ends with .htm then media server will return html page which can be viewed with the help of browser. But if you attach '.m3u' or '.pls' to url then it will directly return the playlist which can be played by any player.If no extension is attached at the end, then m3u playlist will be sent to the client.

Urls which can access the media server have a very simple structure. Default url is **'/stream_continue.htm'** which will return current playlist viewable in browser, while **'/stream_continue.m3u'** will directly send playlist in m3u format. 
The kawaii-player player, has many sections like music,video,playlist etc..which are referred as site in url. Some of them have subsections like music has subsection artist,album etc..which you can see in the player. Now if you want to search for artist say 'yuki kajiura', then required url should look like **'/site=music&opt=artist&s=yuki+kajiura'.** If user will open this url using vlc then then they will directly get all songs of artist 'yuki kajiura' directly on vlc as m3u playlist, without even going to web browser. And as players such as vlc or mpv can play every format you throw at them, transcoding is not required at all on the client side,except on mobile platform. But on mobile platform also, most of the common formats can be easily played by mobile browsers and vlc without transcoding. If cookie is not enabled for this media server, then url entries of the playlist won't change in the local private network. Therefore, user can create various playlist and can use them with vlc or mpv (if playlists has mixed audio and video content) all the time; or they can use some native music player like audacious or clementine in case playlist contains only audio.

**Basic Authentication:** There is option for setting username and password for media server which is available in 'More' menu. Currently it supports authentication for only single user.

By Default, it doesn't use cookie based authentication. It can be enabled by changing 'MEDIA_SERVER_COOKIE' field to 'True', in 'other_options.txt' file. In cookie based authentication, one can't access the media server directly from normal player. Users need to use web browser to access the media server. And once playlist is generated from the browser, it can be played by any media player till the expiry of either cookies or playlist. Users can separately set the expiry field in **hours** for both cookies and playlist, in the 'other_options.txt' file. Default setting is 24 hours for both. If user will stop the server then playlist will be dead won't be usable any more, in case of cookie based authentication. Users can also use curl or wget via command line with appropriate fields for accessing media server playlists.

HTTPS Support: It's possible to enable HTTPS support, with the help of self signed certificate. Users can set 'HTTPS_ON' to 'True' in the other_options.txt. Once this field is set to True, the application can generate self signed certificate automatically in 'pem' format, if 'openssl' is installed and configured properly on the system. The application will only ask user to provide atleast eight character long passphrase. And afterward it will generate 'cert.pem' file automatically, which will be placed in '~/.config/kawaii-player' directory. Alternatively if user want to generate self signed certificate on their own, then they should generate the certificate in 'pem' format and rename it as 'cert.pem' and must place in the config directory i.e. '~/.config/kawaii-player', for the application to use while starting the media server function.

**Problems with self-signed certificate:** Once self-signed certificate is used, one has to access the media server using 'https' protocol instead of 'http'. And once we do that, every browser will start showing security warning to us. Therefore, users need to add the certificate in the exemption list of the browser, in order to visit the media server. From the point of view of encryption, there is no difference between self signed certicate and certificate signed by any other authority. But While surfing on the internet, one should stay away from sites using self signed certificate, unless you know what you are doing.
 
**Access From Outside network:** HTTPS support was mainly added to facilitate secure access of media server from outside the network. It is possible to access the media server from outside the network, by setting 'ACCESS_FROM_OUTSIDE_NETWORK' to 'True'. In order to use this feature, user needs to know how to do port forwarding. Once router is configured for port forwarding, all the incoming requests to your router will be forwarded to local media server.

'ACCESS_FROM_OUTSIDE_NETWORK' field has two parameters which are separated by colon. First parameter determines whether to allow access from outside or not, and second parameter allows changing the frequency of requests to opendns for determining your public IP. Therefore this field will look something like **'ACCESS_FROM_OUTSIDE_NETWORK=True:5'**, where 5 refers to 5 hours. It means after every five hours, the application will query opendns server for your public IP. In order to access from outside the local network, one needs to know public IP address of our machine. The application determines it by accessing 'https://diagnostic.opendns.com/myip' url, after certain specific interval decided by the user. Most of the users are allocated dynamic dns which is subject to change, hence it becomes necessary to know public IP of our machine after some specific interval, to detemine whether IP address has changed or not. 

Now the question is how to get our changed IP address from outside the network? Now-a-days, most people have access to some or other cloud service. The application can write changed IP address to any cloud based file determined by user. The other_options.txt file contains 'CLOUD_IP_FILE' field, which should be set to any cloud based file of any cloud based service as per users' preference. Whenever IP address of users' machine changes, the application will write the new IP address to the cloud file, which user can access from any location.

In order to access the server from outside the network, it is necessary to **enable both cookies and password for server**.

It is possible to access the media server with plain 'http' protocol from outside the network, but it's not advisable because of security reasons. User must set 'HTTPS_ON' field to 'True', if they want to access media server from outside.

In short, Recommanded settings for external access to media server are as follows.
		
		(First set username and password from 'more' menu and then make changes in other_options.txt as below)
		ACCESS_FROM_OUTSIDE_NETWORK=True:1
		CLOUD_IP_FILE=cloud_file_name(optional)
		HTTPS_ON=True
		MEDIA_SERVER_COOKIE=True
		COOKIE_EXPIRY_LIMIT=24
		COOKIE_PLAYLIST_EXPIRY_LIMIT=24 

Once https enabled, users will find that many media players might not play playlist generated from the browser due to self signed certificates. From popular players, vlc,kodi,mplayer,mpv can play self signed https streams well. vlc sometimes work and sometimes won't play anything. kodi plays playlist very well but can't handle redirection. mpv works perfectly with https streams in the playlist. kawaii-player player by default uses mpv as backend, hence generated playlist works well in it. mplayer can also play https streams along with redirection. In kawaii-player, playlist can be anything from audio, video, youtube urls or addons url or even torrent streams. If playlist contains youtube url, then the server will return url of the video stream with the help of youtube-dl. In case of torrent streams (yes, users can start torrent streams directly on the media server, from any client playlist, which will be streamed back to client again), media server will send you redirected url, since torrent streams will start on different port (default 8001) than that of media server port (default 9001). 

kawaii-player player is optimized for streaming specially, hence users might get good streaming experience with it. It also contains offline mode, which might be useful for downloading, media server content to client for offline viewing.


kawaii-player player allows user to start media server on the fly. Basically I never thought of it as 24x7 on media server. (Therefore, I can't tell about it's performance if it is used 24x7.). I wanted to create a portable media server which user can start at any time and anywhere for a brief period so as to share content with family members, friends or colleagues with the help of simple playlist or simple urls, without depending on any third party. And sometimes we just want to enjoy the content, which we have piled up on our working computer, from other devices quickly, without much set up. Creating web interface was not even on my mind, but later I found that web interface might be good for generating playlist, hence at last I created a very simple (but dry and boring) web interface just for easy playlist creation. Users can play media on the browser itself, but they won't be able to play all the media formats, because application does not use any kind of transcoding. Media server feature is implemented using python's inbuilt http.server module, hence it doesn't require any other external dependency.

Note: Users need to use separate port number for media server and torrent streaming feature. Port number along with local IP for torrent streaming feature needs to be set in 'torrent_config.txt' (TORRENT_STREAM_IP field) and that of media server in 'other_options.txt' (LOCAL_STREAM_IP field). Default Settings: 'TORRENT_STREAM_IP=127.0.0.1:8001' and 'LOCAL_STREAM_IP=127.0.0.1:9001'. In default settings one can't access local media from another computer. Users need to change default loopback address to local ip address. Users have to set local IP address and port once only. If local IP address of the media server changes dynamically next time, then the kawaii-player application will try to find out new address automatically. If the application can't find new address then users have to manually change the config files again.

## Universal Playlist Generation

Universal playlist generation is the by-product of the way media server is implemented in this application. Media server of this application, allows creation of playlist in either m3u or pls format, on the fly, which can be played on any client supporting http streaming. (For more details about playlist creation, see Media Server Section.) This playlist can be anything from local audio, local video, some youtube urls, internet radio stations or addon urls or even torrent streams, or any mix of various media formats. (While creating playlist of mixed media format and content, torrent streams should not be mixed with them. Torrent streams should be in separate playlist.) As the playlist can be played on any client which supports http streaming, users do not have to attach themselves to particular client application specified by media server for accessing their files. They can use any client of their choice for playing playlist, from any platform. 

Recommanded media players for playing playlist of mixed content: mpv,mplayer,vlc,kodi { or kawaii-player :) }

For Local audio only content: audacious, clementine or any client that can play m3u files. (audacious can directly read metadata from streaming audio, hence it's much better choice for streaming audio)

On Android: vlc,kodi

**Using curl for getting media server playlist:**

	consider media server ip:port combination is 192.168.3.2:9001
	
	1. Getting current playlist and saving it as playlist.m3u.
	
		$ curl -L http://192.168.3.2:9001/stream_continue -o playlist.m3u
	
	2. Getting current playlist with password enabled.
		
		$ curl -L --user username:password http://192.168.3.2:9001/stream_continue -o playlist.m3u
		
	3. Searching and getting custom playlist (e.g. From video category, search 'history' sub-section for 'mushishi' episodes):
	
		$ curl -L 'http://192.168.3.2:9001/site=video&opt=history&s=mushishi' -o playlist.m3u
		
	4. Getting playlist with cookie and password enabled.
	
		$ curl -L -c cookie.txt --user username:password http://192.168.3.2:9001/stream_continue {this command will establish session}
		
		$ curl -L -b cookie.txt --user username:password http://192.168.3.2:9001/stream_continue -o playlist.m3u {this command will get playlist}
		
	5. Accessing server with https and password enabled:
		
		$ curl -L -k --user username:password https://192.168.3.2:9001/stream_continue -o playlist.m3u
		
	6. Logout from terminal (with passwword, cookie and https enabled):
		
		$ curl -L -k --user username:password -b cookie.txt https://192.168.3.2:9001/logout {This will remove session cookies and client IP address from server}

Playlist generated using curl can be opened with any media player.

**Using Web Interface for getting playlist.**

Web interface can be opened at 'http://192.168.3.2:9001/stream_continue.htm'. It will allow user to search easily and create m3u playlists. It allows user to search only within kawaii-player media server collection. Once search results are displayed in the browser, user can click on the 'Get M3U' button to generate m3u playlist. User can save the playlist or can directly open it with their favourite media player application. If Firefox is directly playing the playlist, then it might be due to some external web plugin. For example, during installation of vlc, it can also install web plugin for firefox. Users need to disable such plugin to get the playlist, or they can simply open the url **without '.htm' extension** from within the vlc itself, if 'https' and cookie are not enabled. vlc can easily deal with username and password based authentication.

On Android devices, user should use vlc latest nightly build. vlc available in fdroid is very old, and it's current stable android version is also far behind desktop version when it comes to playing network streams of all audio/video format. But it's latest nightly build version starting with 2.1, can play most of the video formats including **mkv/mp4** streams streamed by kawaii-player media server. It can also play streaming **flac** audio files. Currently it is the best **open and free** option available for Android for playing audio/video media server files without transcoding. Sometimes if it fails to play streaming files, then user can easily download those files on their Android device using web interface. and can play the files natively.

Another popular open and free Android client is Kodi, which can also play most of the popular files over network without transcoding, since it's media playback engine is based on mplayer. But playing playlist directly is somewhat cumbersome in kodi. Kodi also do not allow opening external url directly. Therefore, users first need to save playlist locally using android web browser, and then need to add it's path to kodi's music/video library. After updating kodi's library, one can see m3u files in it's music/video library which users can play without any more hassle. 

Performance of vlc or kodi on android devices also depends on the hardware of the device. Depending on the hardware of mobile device, sometimes they might play every kind of network stream you throw at them, while sometimes they won't play even a simple video.

Note: Once user logs out from cookie and password enabled session, he/she can't search anything within the server without logging in again. But the generated playlist can be played by any player till the expiry of playlist even after log out. Expiry period for playlist can be set in other_options.txt file (COOKIE_PLAYLIST_EXPIRY_LIMIT field) in hours.


## YouTube Support
######[Index](#index)
![kawaii-player](/Images/YT.png)

This player provides a wrapper around youtube site using qtwebengine. If your GNU/linux distro does not package qtwebengine, then it will fallback to qtwebkit, which is slower compared to qtwebengine for rendering web pages. Users need to install youtube-dl for directly playing youtube videos on this player. In this wrapper users will get complete functionality of youtube site, but with better control over video and playlist. Users can add any youtube video url into the local playlist or they can import entire youtube playlist as local playlist. It also supports downloading youtube subtitles/captions (If available). If subtitles are availble and downloaded by the player, then usesrs need to press 'Shift+J' (Focus the player by taking mouse pointer over the playing video, before using this shortcut key combination) to load the subtitles into the player. It also supports offline mode, if users have fluctuating internet connection. Before using offline mode users need to add youtube url into local playlist.

## Addon Structure
######[Index](#index)
In this player, a weak addon structure has been created, so that one can write addon for viewing video contents of various sites directly on this player,similar to Kodi or Plex, so that you don't have to deal with horrible flash player of the web. 

## Dependencies and Installation
######[Index](#index)

1. For Arch Linux users, PKGBUILD is available in arch folder.

		1. First install pytaglib from AUR
		2. Create package from PKGBUILD using command 'makepkg -s' and then install using 'sudo pacman -U'.

2. Ubuntu or Debian based distro users can directly go to Release section or package directory,download appropriate .deb package and install it using
 
		sudo gdebi pkg_name.deb. 

   If 'gdebi' is not installed then install it using 

		'sudo apt-get install gdebi'. 

   If user want to install directly from source:
		
		$ git clone https://github.com/kanishka-linux/kawaii-player (or directly fetch tar.bz2 from release section and extract it, if user wants stable release)
		$ cd kawaii-player/ubuntu
		$ python3 create_deb.py
		
		Above three steps will create .deb package from latest source, which users can install using gdebi.
				
   **gdebi** will resolve all the dependencies while installing the package. Normally **dpkg -i** is used for installing .deb package in Debian based distros, but 'dpkg' won't install dependencies automatically, which users have to install manually as per instructions given below. Hence try to use **gdebi** for convenience.

3. **Using setup.py**: 
		
		$ git clone https://github.com/kanishka-linux/kawaii-player (or directly fetch tar.bz2 from release section and extract it,if user wants stable release)
		$ cd kawaii-player
		$ python setup.py sdist (or python3 setup.py sdist)
		$ cd dist
		$ sudo pip3 install 'pkg_available_in_directory' (or pip install 'pkg_available_in_directory')
	
	pip3 will essentially install most of the python-based dependencies along with the package. Users only have to install non-python based dependencies such as mplayer/mpv,ffmpegthumbnailer,libtorrent and curl/wget manually. On windows ffmpegthumbnailer is not available, hence thumbnails will be generated by either mpv or mplayer itself.
	**From non-python dependencies, users need to install atleast mpv (or mplayer) as playback engine; and atleast curl (or wget) for fetching web pages apart from default pycurl, in case there is some problem with pycurl.**
	
	If pycurl doesn't work or can't be installed, then users should edit other_options.txt file and set 'GET_LIBRARY' to either 'curl' or 'wget'.
	
	**Note:** GNU/Linux distros should install PyQt5 and other python based dependencies from their own repositories using their native package manager instead of using pip, in order to avoid conflicting files or other dependecies problems due to differing naming schemes of the package. They should remove or comment out the 'install_requires' field in the setup.py, before using this method.
	
	Once application is installed, launch the application using command **kawaii-player** or **kawaii-player-console** from the terminal.

4. Common Method: Users have to manually install all the dependencies listed below. Then they should clone the repository and go to kawaii_player. Open terminal in that directory and run 'python3 install.py' (or 'python install.py' if default python points to python3). Application launcher will be created in '~/.local/share/applications/'.
Or they can simply click (or execute using command line) **'kawaii-player-start'** shell script located in the directory to start the player directly **without copying files anywhere**.


#Dependencies
######[Index](#index)

**Minimum Dependencies on GNU/Linux:** 

python3 {Main Language, version 3.5+}

python-pyqt5 {Main GUI Builder, version 5.5+}

python-pillow {For Image Processing}

python-beautifulsoup4 {For scrapping webpage}

python-lxml {Internal parser used in beautifulsoup4 for advance features}

python-pycurl (or curl or wget alternative) {Main library for fetching web pages}

pytaglib or mutagen (required for Tagging of audio files)

sqlite3 (for managing local music and video database, Addons are not managed by it. Addons are managed using files.)

mpv or mplayer. (for playing media)

ffmpegthumbnailer(Thumbnail Generator for Local Files)

**For extra features such as Youtube support, torrent streaming, MPRIS D-Bus support, desktop notifications and HTTPS:**

libtorrent-rasterbar {For Torrent Streaming Support}

python3-libtorrent (for Ubuntu)

youtube-dl {for YouTube Support}

python3-dbus {for MPRIS DBus support}

libnotify {required for Desktop Notification}

curl or wget {In case pycurl doesn't work}

openssl {for enabling HTTPS}


**Dependencies installation in Arch for pyqt5 version.**

sudo pacman -S python python-pyqt5 qt5-webengine python-dbus python-pycurl python-urllib3 python-pillow python-beautifulsoup4 python-lxml python-psutil curl libnotify mpv mplayer ffmpegthumbnailer sqlite3 libtorrent-rasterbar youtube-dl wget

**Dependencies installation in Ubuntu 16.04**

sudo apt-get install python3 python3-pyqt5 python3-pycurl python3-urllib3 python3-pil python3-bs4 python3-lxml python3-psutil python3-taglib curl wget libnotify-bin mpv mplayer ffmpegthumbnailer sqlite3 python3-libtorrent youtube-dl python3-dbus.mainloop.pyqt5 python3-pyqt5.qtwebkit python3-dbus

## Troubleshooting
######[Index](#index)

1. If you've installed the Application using .deb or .pkg.tar.xz package or using PKGBUILD, and somehow application launcher in the menu is not working, then open terminal and launch the application using command 'anime-watch' or 'python -B /usr/share/kawaii-player/kawaii_player.py' or 'python3 -B /usr/share/kawaii-player/kawaii_player.py'.

2. If addons are not working after some time or fanart/poster are not fetched properly, then try clearing the cache directory '~/.config/kawaii-player/tmp/'. If users have some problems in using qtwebengine, then try clearing cache directory for qtwebengine '~/.config/kawaii-player/Cache/'.

3. If application is crashing after certain update, then it might be possible that it may be due to incompatibility or mismatch between addons of different versions, or certain configuration issues or addition/deletion of certain addons. In such cases remove config file '~/.config/kawaii-player/src/config.txt' manually, and then restart the application. If removing only config file doesn't work then remove both addons directory '~/.config/kawaii-player/src/' and config file '~/.config/kawaii-player/src/config.txt' manually, and then restart the application.

4. In order to update addons manually , download or clone the github kawaii_player directory, then go to github 'kawaii_player/Plugins' directory, and simply copy content of 'Plugins' directory into '~/.config/kawaii-player/src/Plugins'.

5. Sometimes application launcher does not launch the application because of some configuration issues in .desktop file. In such cases try changing 'Terminal=True' to 'Terminal=false' in the file '/usr/share/applications/kawaii-player.desktop'. If it does not solve the problem then open terminal and execute the command 'anime-watch' to see the error output.

6. In Plsma 5.8, the application does not close even after clicking on close button on title bar or using ALT+F4. Therefore, plasma users have to exit application by right clicking the tray icon and selecting the exit option, or using exit button in player itself. Tray icon remains hidden in the plasma panel, which users need to first un-hide by manually adjusting plasma tray settings. 

7. On Windows if 'lxml' or 'pycurl' can't be installed using pip then try finding binary available for it from other sources on the internet.

8. On Windows, If fetching of web pages is very slow using pycurl, then install curl or wget and change pycurl to 'curl' or 'wget' in 'other_options.txt' file located in '~\.config\kawaii-player' folder.

9. If the application is installed using setup.py script then it will install two launching scripts kawaii-player (gui script) and kawaii-player-console (console script). On windows, media server was not working properly if the application was opened with gui_script. When application was openened with console script i.e. kawaii-player-console, then media server functionality was working properly, once application was allowed access through windows firewall. There is basically no difference in kawaii-player and kawaii-player-console scripts, only difference is that in kawaii-player-console, terminal will remain openened behind the gui.

10. If there are some other problems, then turn on logging by setting 'LOGGING' to 'ON', in other_options.txt. It will create 'kawaii-player.log' file in '~/.config/kawaii-player/tmp' folder. Users can analyse the log on their own or can post the log on github issues section. Or alternatively users can post console output if application was started from console.

####Troubleshooting for common method

1. If Application Launcher in the menu is not working or programme is crashing then directly go to "~/.config/kawaii-player/src/", open terminal there and run "python3 kawaii_player.py" or "python kawaii_player.py" as per your default python setup. If there is some problem in installation, then you will get idea about it, whether it is missing dependency or something else, or you can report the error as per the message in terminal.

2. If you do not find application launcher in the menu then try copying manually "~/.config/kawaii-player/kawaii-player.desktop" to either "~/.local/share/applications/" or "/usr/share/applications/"

3. In LXDE, XFCE or Cinnamon ,any new entry of launcher in '~/.local/share/applications/' is instantly shown in Start Menu (In the case of this player, entry will be shown either in Multimedia or Sound & Video). In Ubuntu Unity you will have to either logout and login again or reboot to see the entry in Unity dash Menu.

## Documentation
######[Index](#index)

If everything goes well and if you are able to open the player, then you will come across Three Columns.

First Column, At the Leftmost, is the 'Settings' column. Just click on the library, and add paths to your media. You can choose either mpv or mplayer. Default is mpv.

I've little bit tweaked mplayer functionality especially relating to it's buffer management. If you are on low bandwidth network and mplayer goes out of cache, then it keep on stuttering but does not stop. But I've written small wrapper around mplayer, now as soon as it goes out of buffer, it will stop for 5 seconds. When it stops for filling the buffer, you can pause it manually for larger duration. In normal mplayer functioning, once it starts stuttering due to lack of cache, it is also difficult to pause manually. I really don't know, why developers of mplayer don't pay attention to this simple problem. In this regard, mpv has done really excellent job.
It's your choice which player to choose.

If you are still not satisfied with mpv or mplayer, then you can also launch any of the external player such as vlc,smplayer or kodi. Currently the kawaii-player supports only these three external players apart from mpv and mplayer, which are internal.

Middle column, is the “Title Column”, It will consists of name of the series.
Last Column to the extreme right, is the “Playlist column”, which will contain playlist items which will be played sequentially in the default mode, you will just have to select entry and press enter or double click.

###KeyBoard Shortcuts:

Once video is opened, if it not focussed then take mouse pointer over the video. It will set focus on the video. Once the video is focussed, most of the mpv and mplayer shortcuts will work. There is no volume slider, it's volume will be in sync with global volume. So global volume key will work. If you've setup d-bus shortcut keys for play/pause/next/previous then they will also work.

There is no fullscreen button. People have to use keyboard shortcut(f:fullscreen). It is not full fledge front end, the player has been written with different aim in mind. Therefore, i've tried to reduce buttons as much as possible so as not to clutter the interface, especially with respect to player. But if you still feel the need for more buttons or full fledged UI then you can select smplayer or vlc or kodi from settings menu instead of mpv or mplayer. 

###Player Shortcuts(once video is focussed, if it's not focussed take mouse pointer over the playing video):

q : quit

spacebar: play/pause

f : fullscreen

w : decrease size

e : increase size

r : move subtitle up

t : move subtitle down

i : show file size

j : toggle Subtitle

Shift+j: If available, Load external subtitles from folder '~/.config/kawaii-player/External-Subtitle'. (Staring name of external-subtitle file should match name in the playlist entry)

k : toggle audio

L : Show/Hide Player Controls

m : show video file name

. (remember '>' key) : next file in the playlist or queue

, (remember '<' key) : previous file in the playlist

right : 10s+

left  : 10s-

Up    : 60s+

Down  : 60s-

PgUp  : 300s+

PgDown : 300s-

] : 90s+

[ : 5s-

0 : volume up

9 : volume down 

a : change aspect ratio (works with mpv: default aspect is 16:9 for mpv)


for mplayer set aspect in ~/.mplayer/config, all the properties of the mplayer global config file will be taken by the internal mplayer.

Some important parameters that you should set in '~/.mplayer/config' are as follows:

http-header-fields="User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:43.0) Gecko/20100101 Firefox/43.0" {or any other user-agent}

aspect="16:9"

ass=true

cache=100000

cache-min=0.001

cache-seek-min=0.001 

prefer-ipv4=yes

ao=pulse

vo=gl

You can change the parameters as per your choice.

Similarly, most of the properties of mpv global config file '~/.mpv/config/' will work with this player. If possible you should add following line in mpv config file.

user-agent="Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:43.0) Gecko/20100101 Firefox/43.0" {or any other user-agent}

ao=pulse 

vo=opengl {or anything that works on your system}

cache-secs=120

###Some global Shortcuts:
Shift + L : show/hide Player

shift + G : show/hide Settings column

Shift + F: fullscreen Application not the player

Ctrl + X : show/hide Browser

Ctrl + Z : show/hide Thumbnail mode for Title list (Thumbnail Mode is memory consuming, hence use it carefully if you have very big library collection)

Shift + Z : show/hide Thumbnail mode for playlist column.

Escape : show/hide Everything

Right,Left: set focus alternate between Option column, Title column and Playlist column (If Player is not Playing Anything)

Ctrl+1 to Ctrl+8 : Change aspect ratio of background image

###Title Column:(if Title list is focussed)

h : show history (history of watched series)

Delete : delete particular item of history

r : randomize the list(if you want random series)

t : sort the Title List

PgUp: Move Entry UP

PgDown: Move Entry Down

ctrl+Right : Get Info from TVDB 

c : copy fanart

shift+c : copy summary

ctrl+c : copy poster

###Playlist Column:(If playlist column is focussed)

q : queue the item

Delete : delete particular entry

1 – 9 : select mirror Number (up to 9, if available)

s : select SD quality

h : select HD quality

b : select SD480p quality

w : toggle watch/unwatch

o : start offline mode (If offline mode is already activated then pressing 'o' will enqueue items for offline viewing)

Right: play the item within thumbnail located in the leftmost corner but keep both playlist and title list visible. (can be used as preview mode)

Left: show title list if it's hidden

Return: play the item and hide title list but keep the playlist visible

BackSpace: Go To title list if title list is hidden

PgUp: Move Entry UP

PgDown: Move Entry Down

Ctrl+Up : Move to first entry

Ctrl+Down: Move to last entry

F2 : Rename entry

###Thumbnail Mode:

'=' (Remember '+' key) : increase size of Thumbnails

'-' : decrease size of Thumbnails

###Summary Text Browser

Ctrl+A : to select and save save edited summary.

###Thumbnail mode occupies pretty good memory. If you want to get out of thumbnail mode and free up the memory then click 'close' button which is available in the mode.

###Apart from shortcuts:
You can explore Right click menu of both Playlist Column and Title List Column for getting TVDB, Last.fm profiles for your collection either manually or automatically. If you are getting some problem while setting profiles from TVDB or Last.fm , or having problems accessing addons,then empty the cache directory '~/.config/kawaii-player/tmp', This option is available with right click menu of Title List and Playlist column also.

###Other Things for convenience:

1. Please Enable Vertical Scrolling of Touchpad, because there are no scrollbars in this application, because they were looking very ugly in the total setup.

   In LXDE you can insert following command in autostart file to enable vertical scrolling

	synclient VertEdgeScroll=1

2. In LXDE, for setting global shortcuts for: Play,Pause,Next,Previous; assign keyboard shortcuts to following commands in Openbox lxde-rc.xml.

	1. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause'
	
	2. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next'

	3. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous'


3. It is possible also to change default background image by simply replacing '~/.config/kawaii-player/default.jpg' with another wallpaper of your choice and rename it to 'default.jpg'. This default image is important only when appropriate Fanart is not found. Once a fanart is found for particular entry, the default background image will change to it.

4. Instead of pycurl, it's possible to use directly either curl or wget for fetching web pages. Users need to edit 'GET_LIBRARY' field in the '~/.config/kawaii-player/other_options.txt' and change it to either 'curl' or 'wget'. 

5. If users want to remove temporary directory automatically once the programme quits, then they should edit 'TMP_REMOVE' field in the '~/.config/kawaii-player/other_options.txt' and change it to 'yes' from 'no'.

6. By default, the background image follows fit to screen mode without thinking about original aspect ratio of the image. If user want to change it to fit to width or fit to height without changing aspect ratio, then they should try Ctrl+2 or Ctrl+3 global key combination. Users can also try Ctrl+4 to Ctrl+8 shortcuts, to experiment with various available background image modes.

7. The project is continuation of my another project [AnimeWatch](https://github.com/kanishka-linux/AnimeWatch). Currently both projects share more or less same code base, hence addons and settings of AnimeWatch player will work as it is in kawaii-player.
If user wants to export settings of AnimeWatch to kawaii-player, then they should simply copy contents of folder '~/.config/AnimeWatch' to '~/.config/kawaii-player'.
