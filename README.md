# Kawaii-Player

Kawaii-Player is Audio/Video manager and mutlimedia player (based on mpv and mplayer) with PC-To-PC casting feature, along with functionalities of portable media server and torrent streaming server. 

![kawaii-player](/Images/Video.png)


## Index

- [Features](#features)

- [Playing Mode](#playing-mode)

- [Thumbnail Mode](#thumbnail-mode)

- [Media Server](#media-server)

- [Peer to Peer Mode](#peer-to-peer-mode)

- [Universal Playlist Generation](#universal-playlist-generation)

- [Torrent Streaming Player](#torrent-streaming)

- [Using Web Interface](#using-web-interface)

- [Casting Support](#casting)

- [Remote Control](#remote-control)

- [YouTube Player](#youtube-support)

- [Minimal Music Player](#minimal-music-player)

- [Detached Video (Picture in Picture) Mode](#detached-video-mode)

- [Addons (Plugins) Structure](#addon-structure)

- [Dependencies and Installation](#dependencies-and-installation)

- [MPV Input IPC Server](#mpv-input-ipc-server)

- [Using VLC backend](#using-vlc-backend)

- [Troubleshooting](#troubleshooting)

- [Brief Documentation](#documentation)

- [Latest Stable Release](https://github.com/kanishka-linux/kawaii-player/releases/latest)

- [Contacts](#contacts)

- [Wiki](https://github.com/kanishka-linux/kawaii-player/wiki)


## Features

###### [Index](#index)

1.  Combine Audio-Video Player and Manager.

2.  Bookmark and categorize series in the library (like Watching, Incomplete, Interesting etc..).

3.  Audio-Video management functionalities using sqlite3.

4.  Custom Addons Support for viewing content of various sites directly on the player.

5.  Support for downloading fanart/posters and other information such as summary or biography from internet sites such as TVDB and last.fm.

6.  Thumbnail Grid Mode Support.

7.  Internal web browser with custom right click menu for manually downloading desired fanart and poster for library collection.

8.  System Tray Support (Current tray icon is temporary which may change in future).

9.  MPRIS2 support and integration with sound menu applet.

10. Custom Playlist and queueing support.

11. Remembers most of the last settings, and can opens up directly last watched series in the library.

12. Special Minimal Mode Music Player for listening only music (Available in System Tray context menu).

13. History Manager for both addons and local content.

14. mplayer/mpv internal player.

15. Better buffer management for mplayer on low bandwidth network.

16. Support for opening video in external players like vlc, smplayer or kodi.

17. [Torrent streaming player/server](#torrent-streaming)

18. [Media Server Capability](#media-server)

19. Headless Media Server mode using Xvfb

20. [Youtube wrapper using qtwebengine/qtwebkit](#youtube-support)

21. [Detached Video (Picture in Picture) Mode](#detached-video-mode)

22. [Universal Playlist Generation](#universal-playlist-generation)

23. [Web Interface for accessing media server content](#using-web-interface)

24. [PC-To-PC Casting](#casting)

25. [Browser-To-PC Casting](#casting)

26. [Remote Control using web interface](#remote-control)

27. [Peer to Peer Mode](#peer-to-peer-mode)

28. Available in three themes including dark and system theme (from v3.1 onwards).

29. [Gapless Playback of Network Streams](#gapless-playback)

30. [Live Seekbar Preview](#live-seekbar-preview)

## Playing Mode

###### [Index](#index)

![kawaii-player](/Images/playing.png)

Few more latest screenshots are available in release notes of [v3.1.1](https://github.com/kanishka-linux/kawaii-player/releases/tag/v3.1.1-0) and [v3.3.0](https://github.com/kanishka-linux/kawaii-player/releases/tag/v3.3.0-0)

## Thumbnail Mode

###### [Index](#index)

![kawaii-player](/Images/thumbnail.jpg)

Thumbnail Mode of the application is unique in the sense that users can directly watch video within the thumbnail itself by selecting **appropriate mode from 3 to 5**. In thumbnail mode users have option to change default generated thumbnail. 
Thumbnails of local video files are automatically generated with the help of 'ffmpegthumbnailer'. 


## Media Server

###### [Index](#index)



The media server functionality can be started by selecting **'More->Start Media Server'** option. By default media server will start on 'http://127.0.0.1:9001' i.e. default loop-back address of your machine. In order to use it as media server which can be accessed from any device on the same local network, you have to change this loop-back address '127.0.0.1' to your local network address which normally starts with '192.168.x.y'. User can check and change the default address from **'More->Preferences->Media Server'**. 

![kawaii-player](/Images/Web_New.png)


**A very simple web interface** (as shown above) has been provided for media server, from which users can access their audio/video collection managed by kawaii-player player. If your media server is '192.168.2.2:9001', then web interface can be opened at **192.168.2.2:9001/stream_continue.htm** or **192.168.2.2:9001/index.htm**. From this interface, users can generate universal playlist in m3u format which can be played by any media player on the local network, which supports http streaming such as mpv,vlc etc..and that too on any platform. If users don't want to open web interface then they can get the media server playlist directly on any player by opening url 'http://192.168.2.2:9001/stream_continue.m3u' from within the player itself, and the current media server playlist will be directly available in the player. Alternatively users can use curl or wget to get the playlist, and save it with extension '.m3u', which then can be opened with any player which recognizes the m3u format.

**Use like Streaming Radio:** The media server can be used similar to internet radio station without transcoding. It won't behave like exact internet streaming radio, but it can be made to mimic like one. If server address is set to '192.168.2.2:9001', then you should be able to access the current running file in the playlist at the address 'http://192.168.2.2:9001/'. If user will use this media server IP address in repeat (loop) mode on the client side, then the client will automatically play everything, which is being played by the kawaii-player in it's playlist. If mpv or mplayer are used as clients then their commands will looked like as below:

		$ mpv --loop http://192.168.2.2:9001/
		
		$ mplayer -loop 0 http://192.168.2.2:9001/
		

**Experimental Headless Mode using Xvfb:** It's possible to use the server in headless mode using xvfb. Users need to install **xvfb** first and then should run following command:
		
		(First set multimedia library path manually in *~/.config/kawaii-player/local.txt*)
		
		$ xvfb-run --server-args="-screen 0 640x480x16" kawaii-player --start-media-server --update-video-db --update-music-db
		
		In order to add user and password in headless mode append '--user {username} --password {password}' to above command.
		
		If openssl is installed then for generating ssl certificate append '--generate-ssl {Atleast 8-character length passphrase}' to the above command.

In local home network, if cookie and https is not enabled for media server then, one can access various media server playlists directly from vlc using simple urls.  

If url ends with .htm then media server will return html page which can be viewed with the help of browser. But if you attach '.m3u' or '.pls' to url then it will directly return the playlist which can be played by any player.If no extension is attached at the end, then m3u playlist will be sent to the client.

Urls which can access the media server have a very simple structure. Default url is **'/stream_continue.htm'** which will return current playlist viewable in browser, while **'/stream_continue.m3u'** will directly send playlist in m3u format. 
The kawaii-player player, has many sections like music,video,playlist etc..which are referred as site in url. Some of them have subsections like music has subsection artist,album etc..which you can see in the player. Now if you want to search for artist say 'yuki kajiura', then required url should look like **'/site=music&opt=artist&s=yuki+kajiura'.** If user will open this url using vlc then then they will directly get all songs of artist 'yuki kajiura' directly on vlc as m3u playlist, without even going to web browser. And as players such as vlc or mpv can play every format you throw at them, transcoding is not required at all on the client side,except on mobile platform. But on mobile platform also, most of the common formats can be easily played by mobile browsers and vlc without transcoding. If cookie is not enabled for this media server, then url entries of the playlist won't change in the local private network. Therefore, user can create various playlist and can use them with vlc or mpv (if playlists has mixed audio and video content) all the time; or they can use some native music player like audacious or clementine in case playlist contains only audio.

**Basic Authentication:** There is option for setting username and password for media server which is available in 'More' menu. Currently it supports authentication for only single user.

By Default, it doesn't use cookie based authentication. It can be enabled by changing 'MEDIA_SERVER_COOKIE' field to 'True', in 'other_options.txt' file. In cookie based authentication, one can't access the media server directly from normal player. Users need to use web browser to access the media server. And once playlist is generated from the browser, it can be played by any media player till the expiry of either cookies or playlist. Users can separately set the expiry field in **hours** for both cookies and playlist, in the 'other_options.txt' file. Default setting is 24 hours for both. If user will stop the server then playlist will be dead won't be usable any more, in case of cookie based authentication. Users can also use curl or wget via command line with appropriate fields for accessing media server playlists.

**HTTPS Support:** It's possible to enable HTTPS support, with the help of self signed certificate. Users can set 'HTTPS_ON' to 'True' in the other_options.txt. Once this field is set to True, the application can generate self signed certificate automatically in 'pem' format, if 'openssl' is installed and configured properly on the system. The application will only ask user to provide atleast eight character long passphrase. And afterward it will generate 'cert.pem' file automatically, which will be placed in '~/.config/kawaii-player' directory. Alternatively if user want to generate self signed certificate on their own, then they should generate the certificate in 'pem' format and rename it as 'cert.pem' and must place in the config directory, for the application to use while starting the media server function.

**Problems with self-signed certificate:** Once self-signed certificate is used, one has to access the media server using 'https' protocol instead of 'http'. And once we do that, every browser will start showing security warning to us. Therefore, users need to add the certificate in the exemption list of the browser, in order to visit the media server. From the point of view of encryption, there is no difference between self signed certicate and certificate signed by any other authority. But While surfing on the internet, one should stay away from sites using self signed certificate, unless you know what you are doing.
 
**Access From Outside network:** HTTPS support was mainly added to facilitate secure access of media server from outside the network. It is possible to access the media server from outside the network, by setting 'ACCESS_FROM_OUTSIDE_NETWORK' to 'True'. In order to use this feature, user needs to know how to do port forwarding. Once router is configured for port forwarding, all the incoming requests to your router will be forwarded to local media server.

**ACCESS_FROM_OUTSIDE_NETWORK** field has two parameters which are separated by colon. First parameter determines whether to allow access from outside or not, and second parameter allows changing the frequency of requests to opendns for determining your public IP. Therefore this field will look something like **'ACCESS_FROM_OUTSIDE_NETWORK=True:5'**, where 5 refers to 5 hours. It means after every five hours, the application will query opendns server for your public IP. In order to access from outside the local network, one needs to know public IP address of our machine. The application determines it by accessing 'https://diagnostic.opendns.com/myip' url, after certain specific interval decided by the user. Most of the users are allocated dynamic dns which is subject to change, hence it becomes necessary to know public IP of our machine after some specific interval, to detemine whether IP address has changed or not. 

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

Once https enabled, users will find that many media players might not play playlist generated from the browser due to self signed certificates. From popular players, vlc,kodi,mplayer,mpv can play self signed https streams well, but still their playing ability may vary. 

Note: Users need to use separate port number for media server and torrent streaming feature. Port number along with local IP for torrent streaming feature needs to be set in 'torrent_config.txt' (TORRENT_STREAM_IP field) and that of media server in 'other_options.txt' (LOCAL_STREAM_IP field). Default Settings: 'TORRENT_STREAM_IP=127.0.0.1:8001' and 'LOCAL_STREAM_IP=127.0.0.1:9001'. In default settings one can't access local media from another computer. Users need to change default loopback address to local ip address. Users have to set local IP address and port once only. If local IP address of the media server changes dynamically next time, then the kawaii-player application will try to find out new address automatically. If the application can't find new address then users have to manually change the config files again.

**From v3.1 onwards all of these settings can be set from settings/preferene box of the application. There is no need to fiddle with any of config files manually**

## Peer to Peer Mode

###### [Index](#index)

The portable nature of media server allows the application to work in peer to peer mode. The computer running the application can behave as client as well as server at the same time. If two computers A and B are running instance of kawaii-player, then they can share their libraries in streaming mode with each other without downloading locally. This functionality is available from version 2.2+ onwards. This functionality has been implemented as a special addon 'MyServer', which users can find in the Addons section. 

Steps Inovolved in P2P mode for two computers:

1. First add some items in the library (by clicking on the library button) and then update video and music section.

2. Then check and setup local IP address of both machines. (More->Settings)

3. Switch on media server functionality on both. (More->Start Media Server)

4. Goto Addons->MyServer->Login

5. Login requires IP address of the server that needs to be connected with (in the form http://192.168.2.3/ , if https is enabled for the server then write address accordingly). It will also ask for username and password. Users can leave username/password field blank if it has been not set for the server. Once the login is successful message is displayed, click on the login again to navigate through library of server. 

6. It is possible for Media servers to broadcast themselves(Option is available in **more** menu), so that other clients can discover it automatically by switching on their discover functionality (Addons->MyServer->Discover: on client side). In this case users don't have to remember the IP address of the server. Server can also send custom broadcast message which can help clients to identify it properly - if there are multiple servers running. Clients can get list of servers in the application itself along with broadcast message, after that they will have to choose which server to connect to. For security reasons server is allowed to broadcast itself only in the local network.

7. Broadcast Message needs to be entered into **'BROADCAST_MESSAGE='** field in **.config/kawaii-player/other_options.txt** configuration file. If the field is not there then create it on a newline.

8. It is possible to setup upload speed in KB for the server (The upload speed will be same for all connected clients). Right click on playlist (rightmost column), and select 'Set Upload Speed'. There is no way to setup download speed - if the server is running as a client of another server. Streaming of media is handled by mpv/mplayer, hence download speed can't be controlled externally.

9. If user wants better security then turn on HTTPS and cookies for every server by editing **other_options.txt** file. Username/password can be set from GUI itself from **more** menu. Look into media server section for more details.

10. If client does not want to share its library and it just want to access library of the server, then there is no need for the client to switch on its media server functionality.

What is the use case of p2p mode? 

It allows users to decentralize their collection and at the same time it allows easy sharing of media (in streaming mode) between multiple computers running different operating systems. This peer to peer mode has been made only for personal use within network.

## Universal Playlist Generation

###### [Index](#index)

Universal playlist generation is the by-product of the way media server is implemented in this application. Media server of this application, allows creation of playlist in either m3u or pls format, on the fly, which can be played on any client supporting http streaming. (For more details about playlist creation, see Media Server Section.) This playlist can be anything from local audio, local video, some youtube urls, internet radio stations or addon urls or even torrent streams, or any mix of various media formats. (While creating playlist of mixed media format and content, torrent streams should not be mixed with them. Torrent streams should be in separate playlist.) As the playlist can be played on any client which supports http streaming, users do not have to attach themselves to particular client application specified by media server for accessing their files. They can use any client of their choice for playing playlist, from any platform. 

Recommanded media players for playing playlist of mixed content: mpv,mplayer,vlc,kodi { or kawaii-player :) }

For audio only content: audacious, clementine or any client that can play m3u files. (audacious can directly read metadata from streaming audio, hence it's much better choice for streaming audio) 

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
	
	7. Getting playlist with curl and directly playing it with mpv
		
		$ curl -L 'http://192.168.3.2:9001/site=music&opt=artist&s=yuki+kajiura' -o playlist.m3u && mpv playlist.m3u
		
	8. Getting playlist with curl and directly playing it with mplayer
		
		$ curl -L 'http://192.168.3.2:9001/site=music&opt=artist&s=yuki+kajiura' -o playlist.m3u && mplayer -playlist playlist.m3u

Playlist generated using curl (or from web interface) can be opened with most of the desktop media players.

On Android devices, user should use vlc latest nightly build. vlc available in fdroid is very old, and it's current stable android version is also far behind desktop version when it comes to playing network streams of all audio/video format. But it's latest nightly build version starting with 2.1, can play most of the video formats including **mkv/mp4** streams streamed by kawaii-player media server. It can also play streaming **flac** audio files. Currently it is the best **open and free** option available for Android for playing audio/video media server files without transcoding. Sometimes if it fails to play streaming files, then user can easily download those files on their Android device using web interface. and can play the files natively.

Another popular open and free Android client is Kodi, which can also play most of the popular files over network without transcoding, since it's media playback engine is based on mplayer. But playing playlist directly is somewhat cumbersome in kodi. Kodi also do not allow opening external url directly. Therefore, users first need to save playlist locally using android web browser, and then need to add it's path to kodi's music/video library. After updating kodi's library, one can see m3u files in it's music/video library which users can play without any more hassle. 

Performance of vlc or kodi on android devices also depends on the hardware of the device. Depending on the hardware of mobile device, sometimes they might play every kind of network stream you throw at them, while sometimes they won't play even a simple video.

Note: Once user logs out from cookie and password enabled session, he/she can't search anything within the server without logging in again. But the generated playlist can be played by any player till the expiry of playlist even after log out. Expiry period for playlist can be set in other_options.txt file (COOKIE_PLAYLIST_EXPIRY_LIMIT field) in hours.


## Torrent Streaming

###### [Index](#index)

It is possible to play audio/video torrent directly with this player similar to any streaming media. By default the torrent will stream at *'http://127.0.0.1:8001'*, which is loop-back address of your local machine. User can change this default streaming IP address to local ip address of their machine which normally starts with something like *192.168.x.y*, (from settings/preference box), if they want to access the torrent stream remotely.

In 'torrent_config.txt' you can set some other fields like upload , download rate in (KBps) and default download location.

For opening torrents within this player, goto Addons->Torrent->Open and enter torrent file name or torent url or magnet link inside the input dialog box, and then select appropriate entry which will appear in either Title list or Playlist. Your list of visited torrents will be accessible from the 'History' section. 

This feature is based on libtorrent-rasterbar {which is being used by bittorrent clients like qBittorrent and deluge} and it's python3 bindings. If you've installed latest version of libtorrent-rasterbar then python3 bindings are included along with it. In systems where older version of libtorrent-rasterbar is installed, users need to install python3-libtorrent to use this feature.  

Once Torrent streaming will start, a progress bar will appear to the right side, which will show basic information about torrent.
If user will click on this progress bar then they will get controls for stopping torrent and for setting upload/download speed.

If torrent contains multiple files then users can enqueue the desired files by selecting appropriate entry in Playlist column and pressing 'key ctrl+q'.

**Using Web Interface for managing and accessing Torrent Streaming server remotely:**

![kawaii-player](/Images/Web.png)

(**Old Web interface** showing running of three torrents fetched from **archive.org**. One of them being played directly in the browser. It means users can send some torrent http/magnet link from browser to the server, which will be then streamed back to the user) 

First, set up ip address and port properly for both media server and torrent streaming in *'other_options.txt'* and *'torrent_config.txt'* files (Make sure that port number is different in both the files. By default media server port is 9001 and that of torrent streaming server is 8001). Then start media server and open web interface. In web ui, user will find a text box for searching media within the server. This *search box* can be used for controlling torrent streaming on the media server with the help of text commands. Following are the list of commands which can be used for controlling behaviour of torrent:

	1. For adding torrent to the server, Once torrent info is fetched, it will be available in *Torrent->History* section
		
		$ torrent:torrent_magnet_or_http_link 
		
	2. Stopping Torrent Completely
	
		$ torrent:stop
		
	3. Remove Torrent From Session
	
		$ torrent:remove
		
	4. delete torrent and all it's associated files kept in default torrent download location as specified in *'torrent_config.txt'*
	
		$ torrent:delete  
		
	5. Status of Torrents
	
		$ torrent:status (show status of current running torrent, default behaviour)
		$ torrent:status_all (show status of all active torrents)
		$ torrent:status_stop (stop showing status)
		
	6. Set up download/upload speed for individual torrents.
	
		$ torrent:d:download_speed_in_KB::u:upload_speed_in_KB (e.g. torrent:d:100::u:90)
		
	7. Torrent pause and resume
	
		$ torrent:pause
		$ torrent:pause_all
		$ torrent:resume
		$ torrent:resume_all

HTML5 compliant torrent video streams can be easily played within web browser. For other video formats user can generate m3u playlist from web ui containing torrent stream information in the form of playlist, which then can be opened and play with the help of any popular media players like mpv or vlc.

## Using Web Interface

###### [Index](#index)

![kawaii-player](/Images/Web_Small.png)

Web Interface, contains a search text box which can be used to send text commands to media server. All these commands are listed below:

        $ create_playlist:playlist_name (This will create custom empty playlist with name *playlist_name* on the server, if it has already not been created)
        $ save_playlist:playlist_name (This will save and sync current playing playlist and it's order in separate playlist with name *playlist_name* if it has not been created already. It's useful feature, if user want to save some random search result as playlist)
        $ update:video (will update video section)
        $ update:music (will update music section)
        $ clear:playlist_history (clear playlist navigation history)
        $ clear:cahe (clear video/music/playlist cache along with playlist navigation history)
    
        $ sub:on (Turn on subtitle if ffmpeg is installed on server)
        $ sub:off (Turn off subtitles)
        $ sub:reload (Reload subtitles, if subtitles are not visible even after turning on. It is useful in torrent streaming.)
    
        $ torrent:torrent_magnet_or_http_link (for adding torrent to the server, Once torrent info is fetched, it will be available in *History* section of *Torrent*)
        $ torrent:stop (It will stop the torrent session)
        $ torrent:remove (remove torrent from session)
        $ torrent:delete (delete torrent and all it's associated files kept in default torrent download location as specified in *'torrent_config.txt'*) 
        $ torrent:status (will show status of current running torrent)
        $ torrent:status_all (show status of all running torrents)
        $ torrent:status_stop (will stop showing status)
        $ torrent:d:download_speed_in_KB::u:upload_speed_in_KB (sets up upload and download speed locally for specific torrent. Eg, *torrent:d:90::u:80* will set download speed to 90KB and upload speed to 80KB)
        $ torrent:pause
        $ torrent:pause_all
        $ torrent:resume
        $ torrent:resume_all
        
        $ yt:youtube_link (send youtube link to server playlist)
        $ yt:audio (play only audio)
        $ yt:audiovideo (regular video)
        $ quality:{sd,hd,best}
        $ yt:d (download for offline viewing on server)
        $ yt:d:youtube_link (add link to server playlist and download for offline viewing on server)
        $ yt:getsub (get subtitle if available)
        
        Youtub-Quick-command
        $ ytq:{any link supported by ytdl or torrent http/magnet link}

        Change-playback engine
        $ playbackengine:libmpv/libvlc etc.. (It will restart the application)
    
* **About Playlist Support:** Web Interface allows creation and manipulation of playlists. It also supports navigation through playlist history for the current session. The playlist, which is displayed on the web interface also provides contextmenu that provides variety of options. This contextmenu is shown on right clicking any playlist entry. On android firefox, users have to press playlist entry to see the contextmenu. On android chrome, users have to press the thumbnail image to see the contextmenu.

* **Get M3U:** User can click on the *'Get M3U'* button to generate universal playlist in M3U format, which can be played on any device and on most of the popular clients that support http streaming. User can save the playlist or can directly open it with their favourite media player application. If Firefox is directly playing the playlist, then it might be due to some external web plugin. For example, during installation of vlc, it can also install web plugin for firefox. Users need to disable such plugin to get the playlist, or they can simply open the url **without '.htm' extension** from within the vlc itself, if 'https' and cookie are not enabled. vlc can easily deal with basic username and password based authentication.

* **About Subtitle Support:** It requires installation of ffmpeg on the server. ffmpeg is required for extracting and converting subtiles to WebVTT format which can be displayed in the browser. Server will first scan for subtitles in the video folder. If it does not find subtitle there then it will try to extract subtitle from the video itself if it's in mkv format. Subtitles support can be switched on by using command 'sub:on' or 'sub:reload'. Subtitles will be displayed as captions and won't be embedded into streaming video using transcoding, hence this method won't put strain on the server. In case of streaming mkv files, **Chromium** can play most of them well without subtitle; hence in such cases users can switch on subtitle support. **Firefox** does not support playing mkv files, hence switching on subtitle on it will be useful only for HTML5 compatible video formats. 

* **About Youtube-Quick (ytq:) command:** (Available in version 2.8+) the ytq command will send any url or torrent link to the the application without asking anything and will start playing the video instantly using mpv/mplayer and youtube-dl. Torrent http/magnet links will be played using torrent streaming engine of the application. All the casted url's will be temporarily saved in 'TMP_PLAYLIST' - which users can save later on. Torrents will be saved in 'Torrent->History' section. Users can control quality using 'quality:' command.



## Casting

###### [Index](#index)

#### PC To PC Casting

PC To PC Casting in the context of kawaii-player means ability to cast (send) videos/playlist from one computer to another computer running kawaii-player. Following are important aspects of this feature.
    
    * Casting single file or entire playlist from one computer (Master) 
    
      to another computer (Slave) running kawaii-player.
      
    * Automatic loading of subtitle (if subtitle name matches the file name)
    
    * Ability to send external subtitle file from master to slave
    
    * Ability to queue items
    
    * Ability to open web interface of slave from internal browser of master,
    
      which contains multiple other options to control playback activity on slave.
    
**How to enable PC-To-PC casting feature?**

    * Install kawaii-player on two computers say master and slave.
    
    * On master, enable master mode: Preferences->Other->PC To PC Casting->Master.
    
    * On Slave, enable slave mode: Preferences->Other->PC To PC Casting->Slave
    
    * On Slave, enable remote control: Preferences->Media Server->Turn On Remote Control
    
    * Start media server on both.
    
    * Select any playlist of master. From its contextmenu, start casting files
      
      or playlist from master to slave. Users only need to setup slave address,
      
      when it is prompted by the application, or they can change slave address
      
      from contextmenu itself.
      
After following above steps, on Master, users will find new contextmenu as shown below from which they can cast items to other Slave computers running kawaii-player.

![casting-menu](https://user-images.githubusercontent.com/17716871/39094384-1d5fd91e-464c-11e8-892f-38e2aa540c54.png)

Above contextmenu has 'Show More Controls' option. This option will open up web interface of slave within master using internal browser. It will allow master to control other playback activities on slave. Following is a screenshot with qtwebengine as browser backend. If internal browser is not working as expected (most probably with qtwebkit backend) then users can open up web interface of slave using any external browser of choice.

![Remote-Control](https://user-images.githubusercontent.com/17716871/39094637-61d22e86-4650-11e8-902c-25f09b978283.png)
    
For more details on PC-To-PC casting feature, refer [the issue](https://github.com/kanishka-linux/kawaii-player/issues/15)

From v3.6 onwards, kawaii-player will contain a separate slave control box, so that users don't have to open up web interface. Control box can be found at 'Preferences->Slave'.

#### Browser to PC Casting

The computer running kawaii-player can be used as youtube-casting or torrent-casting device. Users can directly send youtube video/playlist links using web interface to the application with the help of text commands mentioned in the [Using Web Interface](#using-web-interface) section, which will be then played using mpv/mplayer and youtube-dl. If the computer running the application is connected to TV then user can directly view the content on TV. Same is with torrent http/magnet links. Users can preserve everything which has been played into local playlist. Users need to enable **remote-control** mode to use these features, without which everything you click might start playing in the browser if it's html5 compatible. The playing instance can be easily controlled using web-based remote.

Explanation for some casting commands:

* **yt:** command: First users have to select some playlist using web interface and then this command will send some url which will be then saved to that playlist. Users then have to click on the playlist entry manually to make it play on the server.

* **torrent:** command: First select Torrent section from web interface, then this command will send torrent http/magnet link to the application. Users then have to go to Torrent->History section and click on the required item to make it start playing.

* **ytq:** command: (Available in version 2.8+ onwards) Users can send any ytdl supported link/direct link or torrent magnet/http link to the application, which will be then played instantly without asking anything.

About casting extensions:

Experimental casting extension is available for both firefox and chromium [here](https://github.com/kanishka-linux/Extensions).  This extension will add icon and context menu for casting to kawaii-player. Users just have to setup server ip address initially by clicking on the extension icon. After that users are free to go anywhere on the web and then they can cast supported links (including torrent magnet links) directly to the kawaii-player using either context menu or top icon. Therefore, users don’t have to enter text commands manually for casting. Playback of the video can be controlled using web interface.  

For using remote control, see the following section.

## Remote Control

###### [Index](#index)

![kawaii-player](/Images/Remote.png)

(Web Based Remote Control for controlling the player)

* Remote Control can be activated by selecting **'More->Turn On Remote Control'**, (or user can directly add **'REMOTE_CONTROL=True'** field in the file **'~/.config/kawaii-player/other_options.txt'**). Then user needs to start the media server and access the web interface as per instructions written in [Media Server](#media-server) section. Once user will open the web interface, they can see new button labeled **'R:Off'**. Clicking the button, will enable remote control mode. After enabling remote control mode, the buttons in web interface will be utilized for remote controlling current playing instance of kawaii-player.

* For best experience, use latest version of mpv. Some commands pertaining to volume control won't work on old version.

* There are two types of control buttons in the web interface. One set of buttons is directly below the playing video, which are used to control playback inside the web interface. While second group of buttons which is organised in grid pattern is used for controlling the application remotely. If remote control mode is not enabled, then all the buttons will be utilized for controlling various playback activities on the web interface. 

* About First, Last, Next, Prev buttons: These buttons on the web interface will allow users to navigate various playlists which they have accessed during the session. In order to clear playlist navigation history, use 'clear:playlist_history' command.

## YouTube Support

###### [Index](#index)

![kawaii-player](/Images/yt.jpg)

This player provides a wrapper around youtube site using qtwebengine. If your GNU/linux distro does not package qtwebengine, then it will fallback to qtwebkit, which is slower compared to qtwebengine for rendering web pages. Users need to install youtube-dl for directly playing youtube videos on this player. In this wrapper users will get complete functionality of youtube site, but with better control over video and playlist. Users can add any youtube video url into the local playlist or they can import entire youtube playlist as local playlist. It also supports offline mode, if users have fluctuating internet connection. Before using offline mode users need to add youtube url into local playlist.

youtube-dl gets outdated quickly, hence there is an option provided in the player to fetch it's current version automatically if it fails to play videos. In order to use this feature user needs to add *'YTDL_PATH=automatic'* in *'other_options.txt'* file.

Even though, the wrapper has been written for YouTube site, the framework that has been created can be used with any youtube-dl supported site from version 2.8+ onwards. Using internal web browser, users can go to any youtube-dl supported website (using either duckduckgo or google), then right click the required link and play it with kawaii-player.

## Minimal Music Player

###### [Index](#index)

![kawaii-player](/Images/Music.png)

It supports certain MPRIS D-bus functionalities. Therefore if you have created global keyboard shortcuts for play/pause,Next,Previous or Stop then they can work with this player also. Make sure python-dbus is installed on system to use this feature.

It is not very powerful music organizer, but provide certain decent functionalities. When using with mplayer, it's cpu usage is just 1-2 % which makes it very ideal for low end machines.

In Music section only audio will be played and video will be suppressed.

## Detached Video Mode

###### [Index](#index)

![kawaii-player](/Images/Detached_Mode.png)

The Player contains Detached video mode, which can be activated by right clicking tray icon and selecting appropriate entry.
In this mode, video will be detached from the main application window and can float anywhere on the desktop. By default it has titlebar, which users can remove by activating frameless mode from system tray context menu. Users can make this detached video of any size and can position it anywhere on the desktop which will remain above all the windows.

**Fun-Fact:** When I was implementing detached video mode, I had no idea that I was basically implementing picture-in-picture mode. I was initially inspired by an amazing tooltip widget available in gmusicbrowser from which we can control media player. But such type of tooltip widgets became difficult to implement as many gnu/linux desktops stopped supporting old style tray widgets with tooltip in favour of app-indicators. So reluctantly, I developed detached video mode that will work on every desktop which later on I came to know that, is called as picture-in-picture mode.

## Addon Structure

###### [Index](#index)

In this player, a weak addon structure has been created, so that one can write addon for viewing video contents of various sites directly on this player. Addons are needed to copy into folder *'~/.config/kawaii-player/src/Plugins'*, which are loaded automatically when player starts.


## Gapless Playback

###### [Index](#index)

From v3.3+ onwards, kawaii-player supports gapless (or almost gapless) mode for playback of network (http) streams on experimental basis. In this mode kawaii-player will start process of fetching/buffering next network stream before playback of previous stream has ended. This mode is useful when media server of kawaii-player is being accessed by another kawaii-player client in p2p mode. It is also useful for prefetching and buffering ytdl supported links. At the moment, it is not applicable to addons.

How to enable gapless mode?

Goto **Preferences->Player**. There users will find three options on gapless playback. Enable them and read tooltips on them for more details.

For using this feature with ytdl, set YTDL path to automatic or write full path of ytdl (in preferences->Other). By doing this application will disable internal ytdl hook of mpv. mpv allows prefetching of network streams in playlist, but it won't resolve and prefetch ytdl links beforehand. kawaii-player will try to resolve the link to the second url, with the help of ytdl, after half of first stream has played and then will give resolved link to mpv for prefetching and buffering.

## Live Seekbar Preview

###### [Index](#index)

![preview](https://user-images.githubusercontent.com/17716871/38348503-d3f7647a-38bf-11e8-818b-8642d509e2f2.png)

1. Live seekbar preview is available from v3.4.0+ onwards.
    * Two Modes: slow and fast
        * slow mode will try to show preview in stop-motion manner.
        * fast mode will generate faster thumbnail preview by skipping some intermediate previews.
    * Available in two styles: tooltip and float widget
        * Tooltip style is available only in higher qt version (may be in v5.7+). It has somewhat fluctuating performance depending on window manager and system theme.
        * Float widget style has consistent performance on every platform and window manager, on which it has been tested. So, float widget style is recommanded for preview.
    * Once seekbar is focused, users can use keyboard shortcuts ctrl+right and ctrl+left to seek preview +/- 5 seconds, without changing current seek position of video.
    
    How to enable this feature?
    
    Go to Preferences->Player. There users will find options related to live preview. Select options, then start video and after that hover mouse pointer over seekbar to see live preview. If there are some problems in displayed preview images, consider clearing cache folder (option available in Title List ContextMenu).

## Dependencies and Installation

###### [Index](#index)

###### [Latest Stable Release](https://github.com/kanishka-linux/kawaii-player/releases/latest)

1. For Arch Linux users, PKGBUILD is available in arch folder.

		1. First install pytaglib from AUR
		2. Create package from PKGBUILD using command 'makepkg -s' and then install using 'sudo pacman -U'.

2. Arch Users can also get package from AUR. [Latest release](https://aur.archlinux.org/packages/kawaii-player/), thanks to **Nocipher** and [git-version](https://aur.archlinux.org/packages/kawaii-player-git/), thanks to **SolarAquarion**.

3. For Ubuntu or Debian based distros.
	
	- Users can directly go to Release section, download appropriate .deb package, and install it using
 
			sudo apt install ./kawaii-player-<version>.deb

	- If a user wants to install the application directly from source:
		
			$ git clone https://github.com/kanishka-linux/kawaii-player
             
             (or directly fetch tar.bz2 or .zip from release section and extract it,
              if user wants stable release)
             
			$ cd kawaii-player/ubuntu
            
			$ python3 create_deb.py
		
			The above steps will create a .deb package from latest source, which users can install using apt.
				
	- Specifying the path to the .deb is important when installing, otherwise apt will look for the package `kawaii‑player‑<version>.deb` online instead of the working directory.
	
	- PyQt5 available in ubuntu repository is normally older compared to latest release and packages QtWebKit (which has been deprecated since Qt-5.6) instead of QtWebEngine. If user wants to try the application with latest PyQt5 version with QtWebEngine as browser backend, then they should install the application first as per the steps given above and then they should use following command to install PyQt5 using pip (only possible for 64-bit systems).
	
			$ sudo pip3 install PyQt5 sip
		
		Once PyQt5 installed using pip3 then user needs to change *'BROWSER_BACKEND=QTWEBKIT'* to *'BROWSER_BACKEND=QTWEBENGINE'* in *'~/.config/kawaii-player/other_options.txt'* file.
	
		- If PyQt5 installation using pip3 is giving some problem then user can remove it using following command
	
				$ sudo pip3 uninstall PyQt5 sip
		
			and then change '*BROWSER_BACKEND*' to '*QTWEBKIT*' in '*other_options.txt*' file.

3. Using self contained binary for 64-bit gnu/linux systems:
	
	Grab *'gnu.linux.x86_64-bin.7z'* package from latest stable release section, extract it, go to the extracted folder, open terminal in it and execute following commands, to directly open the application:
	
		$ chmod +x kawaii_player
		$ ./kawaii_player
        
    kawaii-player from version 2.0 onwards contains headless browser supporting both qtwebkit and qtwebengine as backend. It is important for working of some particular kind of addons. In 64 bit binary, the included headless browser supports only qtwebkit as backend (as available in ubuntu 16.04 LTS). Users can activate it using command:
    
        $ chmod +x hls_cmd_webkit

	The 64-bit binary is built against Ubuntu 16.04 LTS as base and contains all python based dependencies. Users will have to install only non-python based dependencies like mpv/mplayer/ffmpegthumbnailer externally using their native package manager.

    + Note : From v3.6 onwards, self contained binary won't be made available for gnu/linux distros. Users are advised to use either setup.py and install dependencies manually, or ask their distro maintainers to provide package for their distro by looking at either setup.py, or deb/AUR package.

4. **Using setup.py** (Common method for all including gnu/linux, windows and other unix like systems): 
		
		(first install python3, python3-setuptools)
        
		$ git clone https://github.com/kanishka-linux/kawaii-player 
        
        (or directly fetch tar.bz2 or .zip from stable release section and extract it)
        
		$ cd kawaii-player
        
		$ python setup.py sdist (or python3 setup.py sdist)
        
		$ cd dist
        
		$ sudo pip3 install 'pkg_available_in_directory' 
        
        (or pip install 'pkg_available_in_directory')
        
        Note: use sudo depending on whether user wants to install the package
        
              system-wide or not.
              
        Note: use pip or pip3 depending on what is available on your system.
	
	pip3 will essentially install most of the python-based dependencies along with the package. Users only have to install non-python based dependencies such as mplayer/mpv,ffmpegthumbnailer,libtorrent and curl/wget manually. On windows ffmpegthumbnailer is not available, hence thumbnails will be generated by either mpv or mplayer itself.
	**From non-python dependencies, users need to install atleast mpv (or mplayer) as playback engine; and atleast curl (or wget) for fetching web pages apart from default pycurl, in case there is some problem with pycurl.**
	
	If pycurl doesn't work or can't be installed, then users should edit **Preferences->Other->Get Library** to either 'curl' or 'wget'.
	
	**Note:** GNU/Linux distro users have to install PyQt5 and other python based dependencies (as listed below) using their native package manually in this method.
	
	Once application is installed, launch the application using command **kawaii-player** or **kawaii-player-console** from the terminal.

5. Tips for Windows users.

    If users find that some python dependencies (particularly pycurl and lxml) can't be installed properly, then they should grab appropriate binaries of these packages from [gohlke's site](http://www.lfd.uci.edu/~gohlke/pythonlibs/). Once all python based dependencies are installed, users need to install non-python dependencies like mpv/mplayer or curl/wget. In order to install these non-python packages, just grab binaries of these packages from official sites, extract them and add their path to window's system path. If users are finding some difficulty in setting path variable, then they can just dump all these extracted non-python binaries i.e. mpv/mplayer and curl/wget to the location '~/.config/kawaii-player/src/'; once it is done the application will automatically recognize them. Python3-libtorrent as a binary is not available on PyPI, hence users will have to build and install it from source, in order to use torrent-streaming feature.
    
    **Directly using self contained binary:** 
    
    kawaii-player from v2.5+ onwards is being released with experimental binary for 64-bit windows 10. This binary packs all the python based dependencies (except python3-libtorrent) along with mpv and curl. Just grab the binary for windows from release section, extract it, go to extracted folder and then click on **kawaii_player** file to launch the application. In **~\.config\kawaii-player\other_options.txt** file, windows users have to change 'Preferences->Other->Get Library' to 'curl' from pycurl, if it is not already curl. Users can also change 'YTDL_PATH=DEFAULT' to 'YTDL_PATH=AUTOMATIC', that will grab updated youtube-dl automatically, for playing youtube videos. On windows youtube-dl requires 'msvc 2010 redistributable package (x86)' - which they have to install from microsoft's website.

6. Tips for macOs users (Installing dependencies).

        $ brew install mpv mplayer ffmpeg wget openssl terminal-notifier libtorrent-rasterbar socat
        
        $ pip3 install lxml bs4 Pillow mutagen PyOpenGL PyQt5 sip PyQtWebEngine
        
        $ PYCURL_SSL_LIBRARY=openssl LDFLAGS="-L/usr/local/opt/openssl/lib" CPPFLAGS="-I/usr/local/opt/openssl/include" pip3 install --no-cache-dir pycurl
    
    Support for macOS has been added from v3.9+ onwards. Once dependencies are installed, use git master branch and install package manually using setup.py as mentiond in the common method above. 
    
    After opening the application go to **Preferences->Config**, check **Use this config file** and add/modify vo=libmpv and ao=coreaudio. Users can modify other parameters also as per need and then need to save changes, before playing any video.
    
    kawaii-player has beent tested only with macOS Mojave. On macOS, kawaii-player (v3.9) will open separate window for the video, since OSX does not support window embedding of foreign processes. Therefore playing video within thumbnails won't work along with varios thumbnail modes and detached video mode. However, rest of the features like video library management, torrent streaming, pc-to-pc casting, media server, remote control etc.. will work as expected. Support for macOS is in experimental stage.

    **Update:** From v4.0+ onwards, it is posiible to embed video within kawaii-player application on macOS, by using **libmpv** as backend. Select **libmpv** from sidebar, and restart the application. Make sure that libmpv is located somewhere in the system path.

    Note: If libtorrent-rasterbar is not working for torrent streaming, then edit brew formula and update download url location (point it to libtorrent-rasterbar v1.1.12), and then install it from source. 

# Dependencies

###### [Index](#index)

**Minimum Dependencies on GNU/Linux:** 

- python3 {Main Language, version 3.5+}

- python-pyqt5 {Main GUI Builder, version 5.5+}

- python-pillow {For Image Processing}

- python-beautifulsoup4 {For scraping webpage}

- python-lxml {Internal parser used in beautifulsoup4 for advance features}

- python-pycurl (or curl or wget alternative) {Main library for fetching web pages}

- pytaglib or mutagen (required for Tagging of audio files)

- sqlite3 (for managing local music and video database, Addons are not managed by it. Addons are managed using files.)

- mpv (or libmpv - from v4.0+) or mplayer. (for playing media)

- python-opengl (when using libmpv as backend, from v4.0+)

- ffmpegthumbnailer(Thumbnail Generator for Local Files) {not required from v4.0+}

- socat {for using mpv ipc server mode}

**For extra features such as Youtube support, torrent streaming, MPRIS D-Bus support, desktop notifications and HTTPS:**

- libtorrent-rasterbar {For Torrent Streaming Support}

- python3-libtorrent {in case python3 bindings for libtorrent are not included in libtorrent-rasterbar}

- youtube-dl {for YouTube Support}

- python3-dbus {for MPRIS DBus support}

- libnotify {required for Desktop Notification}

- curl or wget {In case pycurl doesn't work}

- openssl {for enabling HTTPS}

- ffmpeg {for extracting and converting subtitles}

- xvfb {for using the application in headless mode}

- pympv {if using latest libmpv api}

- python-vlc {for using libvlc as playback engine, useful mainly for Raspberry-Pi 4+ models}

- vlc {for using vlc/cvlc binary as playback engine, useful mainly for Raspberry-Pi 4+ models}

**Dependencies installation in Arch**

sudo pacman -S python python-pyqt5 qt5-webengine python-dbus python-pycurl python-pillow python-beautifulsoup4 python-lxml curl libnotify mpv mplayer ffmpegthumbnailer sqlite3 libtorrent-rasterbar youtube-dl wget python-mutagen socat

**Dependencies installation in Ubuntu 16.04+**

sudo apt install python3 python3-pyqt5 python3-pycurl python3-pil python3-bs4 python3-lxml python3-taglib curl wget libnotify-bin mpv mplayer ffmpegthumbnailer sqlite3 python3-libtorrent youtube-dl python3-dbus.mainloop.pyqt5 python3-pyqt5.qtwebkit python3-dbus python3-mutagen

**Dependencies installation in Fedora 25+**

first enable rpmfusion repository

dnf install mpv mplayer ffmpegthumbnailer python3-qt5 python3-qt5-webkit python3-pycurl python3-lxml python3-beautifulsoup4 python3-pytaglib python3-mutagen rb_libtorrent-python3 curl wget libnotify python3-dbus python3-pillow

## MPV Input IPC Server

MPV has deprecated slave mode, so in order to use mpv binary as playback engine one has to use mpv-input-ipc-server which works somewhat similar to slave mode. One has to pull changes from latest source to use this feature.

In `other_options.txt` file add `MPV_INPUT_IPC_SERVER=True` and restart player. Then select mpv/MPV as playback engine. After that one will be able to use mpv binary as it is.

One needs to have `socat` installed on the system. It is tested only on ArchLinux and OSX. This feature is not supported on Windows for now.

## Using VLC Backend

Users can use vlc as a backend if required (latest commit).

Users can select vlc/cvlc/libvlc as backend.

For using `libvlc`, one needs to install python-vlc

```
pip install python-vlc
```

For using vlc/cvlc, only vlc binary needs to be installed on the system

Featurewise vlc backend haven't reached parity with mpv backend. So many mpv based features won't work with vlc.

The functionality has been added mainly to work with Raspberry-pi 4, and control playback via web interface;
since, VLC provides good hardware accelerated video experience on RPi.

## Setup New Config Directory

(This feature is available only in the latest changes.)

Create `~/.config/kawaii-player/new_home.txt` file. And add new directory location for config directory, after that restart player.

One needs to copy manually all config files and directory to new location in the beginning, otherwise application will recreate all configs considering config folder as empty.

## Troubleshooting

###### [Index](#index)

1. If user has installed the Application using .deb or .pkg.tar.xz package or using PKGBUILD, and somehow application launcher in the menu is not working, then open terminal and launch the application using command 'kawaii-player' or 'python -B /usr/share/kawaii-player/kawaii_player.py' or 'python3 -B /usr/share/kawaii-player/kawaii_player.py'.

2. If addons are not working after some time or fanart/poster are not fetched properly, then try clearing the cache directory **'~/.config/kawaii-player/tmp/'**. If users have some problems in using qtwebengine, then try clearing cache directory for qtwebengine **'~/.config/kawaii-player/Cache/'**.

3. If application is crashing after certain update, then it might be possible that it may be due to incompatibility or mismatch between addons of different versions, or certain configuration issues or addition/deletion of certain addons. In such cases remove config file **'~/.config/kawaii-player/src/config.txt'** manually, and then restart the application. If removing only config file doesn't work then remove both addons directory **'~/.config/kawaii-player/src/'** and config file **'~/.config/kawaii-player/src/config.txt'** manually, and then restart the application.

4. In order to update addons manually , download or clone the github kawaii_player directory, then go to github 'kawaii_player/Plugins' directory, and simply copy content of 'Plugins' directory into '~/.config/kawaii-player/src/Plugins'.

5. In Plsma 5.8+, the application does not close even after clicking on close button on title bar or using ALT+F4. Therefore, plasma users have to exit application by right clicking the tray icon and selecting the exit option, or using exit button in player itself. Tray icon remains hidden in the plasma panel, which users need to first un-hide by manually adjusting plasma tray settings. 

6. On Windows if 'lxml' or 'pycurl' can't be installed using pip then try finding binary available for it from other sources on the internet.

7. On Windows, If fetching of web pages is very slow using pycurl, then install curl or wget and change pycurl to 'curl' or 'wget' in 'other_options.txt' file located in '~\.config\kawaii-player' folder.

8. If the application is installed using setup.py script then it will install two launching scripts kawaii-player (gui script) and kawaii-player-console (console script). On windows, media server was not working properly if the application was opened with gui_script. When application was opened with console script i.e. kawaii-player-console, then media server functionality was working properly, once application was allowed access through windows firewall. There is basically no difference in kawaii-player and kawaii-player-console scripts, only difference is that in kawaii-player-console, terminal will remain open behind the gui.

9. The application creates configuration folder '~/.config/kawaii-player'. Make sure that the application has write permission to create folders and sub-folders within config directory. Thumbnails generated by ffmpegthumbnailer are also stored in the config directory, hence make sure that ffmpegthumbnailer also has write access to the directory. If you are using **selinux**, then configure it properly. 

10. If media server has been started properly, but it can't be accessed, then first check your firewall settings, and allow access to media server port from other computers/devices.

11. If there is screen tearing issue in LXDE,XFCE or Openbox based distro, then try using **compton** as compositing manager and autostart it with script containing **'compton --backend glx --vsync opengl -b'**.

12. If there is screen tearing in fullscreen video in ubuntu unity, then install ccsm (compizconfig settings manager) and try toggling option **'ccsm->composite->undirect-fullscreen-window'**

13. Library paths are set in '~/.config/kawaii-player/local.txt' file. If there is a problem setting it from GUI, then directly enter paths in **'local.txt'** file.

14. If there is some problem with mpv/mplayer video playback, then try changing video output driver (vo) to gl or opengl, in the configuration files of mpv/mplayer. mpv config file is: '.config/mpv/config'; mplayer config file is: '.mplayer/config'. Users can also check other available video drivers using command 'mpv/mplayer -vo help'. In mpv v.28+, opengl has been replaced with gpu. 

15. If there are some other problems, then turn on logging by setting 'LOGGING' to 'ON', in other_options.txt. It will create 'kawaii-player.log' file in '~/.config/kawaii-player/tmp' folder. Users can analyse the log on their own or can post the log on github issues section. Or alternatively users can post console output if application was started from console.

16. when accessing media-server if browser does not redirect properly due to cookies then clear browser cookie cache or disable media server cookies.

## Documentation

###### [Index](#index)

If everything goes well and users are able to open the player, then they will come across Three Columns.

First Column, At the Leftmost, is the 'Settings' column. Just click on the library, and add paths to your media. You can choose either mpv or mplayer. Default is mpv.

In this player, mplayer functionality relating to it's buffer management has been tweaked a little bit. If users are on low bandwidth network and mplayer goes out of cache, then it keep on stuttering but does not pause and at that time it's difficult to pause it manually also. Therefore in this application, a small wrapper has been written around mplayer, so that as soon as it goes out of cache, it will pause to fill the cache upto 1% of it's allocated capacity. When it stops for filling the buffer, users can pause it manually for larger duration. mpv doesn't have any such problem.

If users are still not satisfied with mpv or mplayer, then they can also launch any of the external player such as vlc,smplayer or kodi. Currently the kawaii-player supports only these three external players apart from mpv and mplayer, which are internal.

Middle column, is the “Title Column”, It will consists of name of the series.
Last Column to the extreme right, is the “Playlist column”, which will contain playlist items which will be played sequentially in the default mode, you will just have to select entry and press enter or double click.

### Library Management:

* It tries to be a simple media manager for both audio and video, along with powerful playing capabilities of mpv and mplayer. 

* If your video collection has been placed in separate folders having names - Anime, TV Shows, Movies and Cartoons i.e. default categories, then it will categorize the collection automatically and rest will be placed in Others. If users need more categories then they have the option to create new one. Users can easily rename title entries and playlist entries. 

* If a TV Show has multiple seasons, then the application can recognize a folder as a separate season, if it's name starts with 'Season'. For example consider folder structure, *Anime->Mushishi->Season 1* and *Anime->Mushishi->Season 2*. If the folder structure is organized like this, then the application will show entries as **Mushishi-Season 1** and **Mushishi-Season 2**, in the video Anime Section.

* If users are not satisfied with default categorization, then they can create their own categories like Music Video, Anime Movies, Cartoon Movies, Hollywood movies etc.. from the title list contextmenu, and then can add desired titles to them.

* The video section contains two update options i.e. Update and UpdateAll. The **Update** option will add new entries to the database without deleting older one, while **UpdateAll** option will remove all the unreachable links from the database. If users frequently attach and remove external hard drives to laptop/desktops, then it is advisable to use only **Update** option, as it will preserve non-reachable links.

* The Video section, also contains two options **Directory and Available**. The Directory option will list the entire video collection, while the Available option will list only reachable videos.

* Users can get fanart/posters/summary for the entire collection. If appropriate match is not found then users can directly go to sites such as TVDB/TMDB directly using internal browser and can grab the content. The browser's internal contextmenu has been tweaked to facilitate getting required information. Anime watchers can get access to popular Anime review sites directly within the application, from which they can grab some information for their collection (users can enable this feature by setting 'ANIME_REVIEW_SITE=True' in *'~/.config/kawaii-player/other_options.txt'* file). Users will also get to select various background image modes, that will change aspect ratio of the background image (i.e. fanart of any item) instantly (shortcuts ctrl+0 to ctrl+9). 

* The application can manage history/bookmarks and watch/unwatch status properly. It also supports playlist creation with mixed content. 

* In custom playlist containg videos, do not contain artist field. However, users can add artist to any playlist entry when renaming using F2. When renaming, use '**::**' to delimit title of video from artist name. Once artist name is set, the application can grab information from last.fm profile of the artist (if *GET_MUSIC_METADATA* field is set to *True* in other_options.txt file).


### KeyBoard Shortcuts:

Once video is opened, if it not focussed then take mouse pointer over the video. It will set focus on the video. Once the video is focussed, most of the mpv and mplayer shortcuts will work. There is no volume slider, users have to use keys 0 and 9 or external global volume keys. If user has setup d-bus shortcut keys for play/pause/next/previous then they will also work.

There is no fullscreen button. People have to use keyboard shortcut(f:fullscreen) or double click.

kawaii-player from v3.1 onwards almost fully supports all of mpv's default keybindings. Users can also change keybindings from settings/preference box of the application. 

for mplayer set aspect in ~/.mplayer/config, all the properties of the mplayer global config file will be taken by the internal mplayer.

Some important parameters that user should set in '~/.mplayer/config' are as follows:

        aspect="16:9"

        ass=true

        cache=100000

        cache-min=0.001

        cache-seek-min=0.001 

        prefer-ipv4=yes

        ao=pulse

        vo=gl

Users can change the parameters as per their choice.

Similarly, most of the properties of mpv global config file '~/.config/mpv/config/' will work with this player. If possible you should add following line in mpv config file.

        ao=pulse 

        vo=opengl {or anything that works on your system} {opengl has been replaced with gpu in mpv v0.28}

        cache-secs=120

### Some global Shortcuts:

* Shift + L : show/hide Player

* shift + G : show/hide Settings column

* Shift + F: fullscreen Application not the player

* Ctrl + X : show/hide Browser

* Ctrl + Z : show/hide Thumbnail mode for Title list (Thumbnail Mode is memory consuming, hence use it carefully if you have very big library collection)

* Shift + Z : show/hide Thumbnail mode for playlist column.

* Escape : show/hide Everything

* Right,Left: set focus alternate between Option column, Title column and Playlist column (If Player is not Playing Anything)

* Ctrl+0 to Ctrl+9 : Change aspect ratio of background image

* F1 : Thumbnail Wall Mode

### Title Column:(if Title list is focussed)

* ctrl + h : show history (history of watched series)

* Delete : delete particular item from database

* ctrl + r : randomize the list(if you want random series)

* ctrl + t : sort the Title List

* ctrl+Right : Get Info from TVDB with duckduckgo as backend 

* ctrl+Left : Get Info from TMDB with duckduckgo as backend 

* ctrl+UP : Get Info from TVDB with google as backend

* ctrl+Down: Get Info from TMDB with google as backend

* Alt+1 : Get info from TVDB directly without using any search engine backend

* Alt+2 : Get info from TMDB directly without using any search engine backend

* F2 : Rename Title of the entry in the database.

### Playlist Column:(If playlist column is focussed)

* Ctrl+ q : queue the item

* Delete : delete particular entry

* 1 – 9 : select mirror Number (up to 9, if available)

* w : toggle watch/unwatch

* Ctrl+o : start offline mode (If offline mode is already activated then pressing 'o' will enqueue items for offline viewing)

* Left: show title list if it's hidden

* Return: play the item and hide title list but keep the playlist visible

* BackSpace: Go To title list if title list is hidden

* PgUp: Move Entry UP

* PgDown: Move Entry Down

* Ctrl+Up : Move to first entry

* Ctrl+Down: Move to last entry

* F2 : Rename entry

* F3 : Rename in Group 

Group rename pattern is: New_common_name_{start_pt-end_pt}. 

Eg. If there are 26 episodes in the list and user want to rename all of them, then select the first entry, press F3 and in the dialog box input 'Episode-S01EP{01-26}'. It will rename episodes in the database. If user wants to rename episodes from 5'th entry, then they should select fifth entry, press F3 and input 'Episode-S01EP{05-26}'

### Thumbnail Mode:

* '=' (Remember '+' key) : increase size of Thumbnails

* '-' : decrease size of Thumbnails

### Summary Text Browser

* Ctrl+A : to select and save save edited summary.

### Other Things for convenience:

1. Please Enable Vertical Scrolling of Touchpad, because there are no scrollbars in this application, because they were looking very ugly in the total setup.

   In LXDE you can insert following command in autostart file to enable vertical scrolling

	synclient VertEdgeScroll=1

2. In LXDE, for setting global shortcuts for: Play,Pause,Next,Previous; assign keyboard shortcuts to following commands in Openbox lxde-rc.xml.

	1. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.PlayPause'
	
	2. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next'

	3. bash -c 'player=$(qdbus-qt4 org.mpris.* | grep MediaPlayer2 | head -n 1); qdbus-qt4 $player /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous'


3. It is possible also to change default background image by simply replacing '~/.config/kawaii-player/default.jpg' with another wallpaper of your choice and rename it to 'default.jpg'. If there are more images in the configuration directory containing 'default' string, then it means they are derivative images of the default.jpg and users should remove those derivative images also. This default image is important only when appropriate Fanart is not found. Once a fanart is found for particular entry, the default background image will change to new one. 

4. Instead of pycurl, it's possible to use directly either curl or wget for fetching web pages. Users need to edit 'GET_LIBRARY' field in the '~/.config/kawaii-player/other_options.txt' and change it to either 'curl' or 'wget'. 

5. By default, the background image follows fit to height mode by keeping the original aspect ratio of the image. If user wants to change it to fit to screen or fit to width then they should try Ctrl+1 or Ctrl+2 global key combination. Users can also try Ctrl+0 to Ctrl+9 shortcuts, to experiment with various available background image modes. Users can't change background mode of default wallpaper image. Default background image will always follow fit to screen mode.

## Contacts

###### [Index](#index)

New Issues can be opened at:

[Issue Tracker](https://github.com/kanishka-linux/kawaii-player/issues)

If users have some other queries or want to give feedback then they can use following e-mail:

[E-mail](mailto:kanishka.linux@gmail.com)
