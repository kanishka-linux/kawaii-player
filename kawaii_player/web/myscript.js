/*

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

*/

var _player = document.getElementById("player"),
    _playlist = document.getElementById("playlist"),
    _site_value = document.getElementById("site"),
    _stop = document.getElementById("stop"),
    _loop = document.getElementById("loop"),
    _next = document.getElementById("next"),
    _play = document.getElementById("play"),
    _title = document.getElementById("title"),
    _title_music = document.getElementById("title_music"),
    _img_id = document.getElementById("img-id"),
    _img_info = document.getElementById("img-info"),
    _shuffle = document.getElementById("shuffle"),
    _m3u = document.getElementById("m3u"),
    _logout = document.getElementById("logout"),
    //_home = document.getElementById("home"),
    _remote = document.getElementById("remote_btn"),
    _opt_ok = document.getElementById("opt_ok"),
    _opt_val_ok = document.getElementById("opt_val_ok"),
    _opt_val = document.getElementById("opt_val"),
    _seek_10 = document.getElementById("seek10"),
    _seek_10_ = document.getElementById("seek_10"),
    _seek_60 = document.getElementById("seek60"),
    _seek_60_ = document.getElementById("seek_60"),
    _seek_5m = document.getElementById("seek5m"),
    _seek_5m_ = document.getElementById("seek_5m"),
    _vol_5 = document.getElementById("vol5"),
    _vol_5_ = document.getElementById("vol_5"),
    _toggle_master = document.getElementById("toggle_master"),
    _fullscreen = document.getElementById("fullscreen"),
    _selection_site = document.getElementById("selection_site"),
    _minimal = document.getElementById("minimal"),
    _display_option = document.getElementById("display_option"),
    _buttons_div = document.getElementById("buttons_div"),
    _empty_btn = document.getElementById("empty_btn"),
    _custom_pls = document.getElementById("custom_pls"),
    _pls_custom = document.getElementById("pls_custom"),
    _create_playlist = document.getElementById("create_playlist"),
    _only_playlist = document.getElementById("only_playlist"),
    _playlist_custom = document.getElementById("playlist_custom"),
    _show_player = document.getElementById("show_player"),
    _hide_player = document.getElementById("hide_player"),
    _toggle_subtitle = document.getElementById("toggle_subtitle"),
    _toggle_audio = document.getElementById("toggle_audio"),
    _remote_val = 'off',
    _clicked_index = 0,
    _old_height = '480',
    _playlist_selected_element = "";
    _drag_start_y = 0;
    _get_torrent_status = "";
    _status_command = "";
    _final_url = "";
    _final_name = "";
    _subtitle_status = "off";
    show_image = false;
    _prev = document.getElementById("prev");
    _custom_context = document.getElementById("context-menu-bar");
    _custom_context_menu_playlist = document.getElementById("custom_context_menu_playlist");
    _playlist_context_menu = document.getElementById("playlist_context_menu");
    pls_arr = [];
    last_position_scrollbar = 0;
    _old_playlist_selected_color = 'white';
    _show_thumbnails = false;
    _old_queue_selected_color = 'white';
    _queue_selected_element = "";
    _video_section = document.getElementById("video_section");
    _player_control_info = document.getElementById("player_control_info")
    _player_control_image = document.getElementById("player_control_image")
    _player_progress = document.getElementById("player_progress")
    _player_progress_status = null;
    _aspect_ratio = 16/9;
    _top_xy = [0,0];
    _minimize_control_bar = true;
    _hide_options = false;
    _remote_control_buttons = document.getElementById("remote_control_buttons");
    _player_dimensions = ["640", "480"];
    _queue_context = document.getElementById("context-menu-bar-custom");
    _custom_context_menu_playlist_queue = document.getElementById("custom_context_menu_playlist_queue");
    _first_select = document.getElementById("first_select");
    _second_select = document.getElementById("second_select");
    _third_select = document.getElementById("third_select");
    _search_text_top = document.getElementById("search_text_top");
    _current_working_m3u = "";
    _top_menu_bar = document.getElementById('top_menu_bar');
    _top_menu_bar_sub = document.getElementById('top_menu_bar_sub');
    _hide_top_bar = true;
    _player_start_time = document.getElementById('player_start_time');
    _player_end_time = document.getElementById('player_end_time');
    _btn_minimize = document.getElementById("btn_minimize");
    _mydatalist = document.getElementById("mydatalist");
    _clicked_num = '1';
    _clicked_element = null;
    _remote_control_status = null;
    _can_play_sync = false;
    _remote_queue_value = 0;
    _btn_minmax_topbar = document.getElementById('btn_minmax_topbar')
// functions

function hide_control_bar(){
    var r = document.getElementById("player_control_progress");
    r.style.visibility = "hidden";
    var u = document.getElementById("btn_maximize");
    u.style.visibility = "visible";
    var v = document.getElementById("btn_to_top");
    v.style.visibility = "visible";
    _minimize_control_bar = true;
    if (_player_progress_status){
        clearInterval(_player_progress_status);
        _player_progress_status = null;
    }
}

function show_control_bar(){
    var u = document.getElementById("btn_maximize");
    u.style.visibility = "hidden";
    var v = document.getElementById("btn_to_top");
    v.style.visibility = "hidden";
    var r = document.getElementById("player_control_progress");
    r.style.visibility = "visible";
    _minimize_control_bar = false;
    if (!_player_progress_status && _remote_val == 'off'){
        _player_progress_status = setInterval(update_progress_bar, 1000);
    }
}

function goto_last_position(event){
    window.scrollTo(_top_xy[0], _top_xy[1]);
}

function hide_show_topbar(){
        w = window.innerWidth;
        if (w < 450){
            _top_menu_bar.style.display = 'block';
            _top_menu_bar_sub.style.display = 'block';
        }else{
            _top_menu_bar.style.display = 'grid';
            _top_menu_bar_sub.style.display = 'grid';
        }
        _hide_top_bar = false;
        _btn_minmax_topbar.style.display = 'none';
}

function max_min_top_bar(){
    console.log(_hide_top_bar, _top_menu_bar_sub.style.display);
    _hide_top_bar = true;
    w = window.innerWidth;
    _top_menu_bar.style.display = 'none';
    _btn_minmax_topbar.style.display = 'block';
}

function top_bar_change_layout(){
    w = window.innerWidth;
    if (w < 450){
        _top_menu_bar.style.display = 'block';
        _top_menu_bar_sub.style.display = 'block';
    }else{
        _top_menu_bar.style.display = 'grid';
        _top_menu_bar_sub.style.display = 'grid';
    }
    if (_hide_top_bar){
        _top_menu_bar.style.display = 'none';
    }
}

function menu_clicked(e){
    var playlist = e;
    var pl = _playlist_selected_element;
    console.log(pl.getAttribute('data-mp3'),pl.getAttribute('data-num'),pl.title);
    var new_url = 'add_to_playlist='+playlist+'&'+pl.title+'&'+pl.getAttribute('data-mp3');
    console.log(new_url);
    var client = new getRequest();
	client.get(new_url, function(response) {
	console.log(response);
	_title.innerHTML = response;
	})
    pl.style.backgroundColor = _old_playlist_selected_color;
}

//function contextmenu_mouseout(e){
//    _custom_context.style.display = "none";
//    var pl = _playlist_selected_element;
//    pl.style.backgroundColor = _old_playlist_selected_color;
//}

function menu_clicked_playlist(e){
    var playlist = _only_playlist.value;
    if(playlist == 'select_existing_playlist' || playlist == null || !playlist){
		playlist = 'Default';
	}
	console.log(playlist);
    var pl = _playlist_selected_element;
    //console.log(pl.getAttribute('data-mp3'),pl.getAttribute('data-num'),pl.innerHTML);
    var new_url = 'add_to_playlist='+playlist+'&'+pl.title+'&'+pl.getAttribute('data-mp3');
    //console.log(new_url);
    var client = new getRequest();
	client.get(new_url, function(response) {
	console.log(response);
	
	})
    
    if (e == 'hide') {
        _custom_context.style.display = "none";
    } else{
        _title.innerHTML = response;
    }
    pl.style.backgroundColor = _old_playlist_selected_color;
    window.scrollTo(_top_xy[0], _top_xy[1]);
}

function hide_extra_info(e){
    var elm = document.getElementById("queue_info");
    elm.hidden = "hidden";
}

function menu_clicked_playnow(e){
    _custom_context.style.display = "none";
    var pl = _playlist_selected_element;
    playlistItemClick(pl,'playlist');
    pl.style.backgroundColor = _old_playlist_selected_color;
    
}

function menu_clicked_queue(e){
    var playlist = _only_playlist.value;
    pls_val = false;
    if(playlist == null || !playlist){
        var new_opt = document.createElement("option");
        new_opt.text = 'Select Existing Playlist';
        new_opt.value = 'select_existing_playlist';
        _only_playlist.appendChild(new_opt);
	}else{
        _only_playlist.value = 'select_existing_playlist';
    }
	console.log(playlist);
    click_to_add_to_playlist(_playlist_selected_element);
    
    if (e == 'hide') {
        _custom_context.style.display = "none";
    }   
    _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
}



function menu_clicked_playnow_queue(e){
    _queue_context.style.display = "none";
    playlistItemClick(_queue_selected_element,'queue_context');
    _queue_selected_element.style.backgroundColor = _old_queue_selected_color;
}

function menu_clicked_hide_queue(e){
    _queue_context.style.display = "none";
    _queue_selected_element.style.backgroundColor = _old_queue_selected_color;
}

function menu_clicked_remove_queue(e){
    if (_remote_val == 'on'){
        var index = 0;
        var first = _playlist_custom.firstChild;
        while(first){
            if (first == _queue_selected_element){
                break
            }
            first = first.nextSibling;
            index += 1;
        }
        var req_val = 'queue_remove_item_'+index.toString();
        var client = new getRequest();
        client.get(req_val, function(response) {
        console.log(response);
        _remote_queue_value -= 1;
	})}
    _playlist_custom.removeChild(_queue_selected_element);
    if (e == 'hide') {
        _queue_context.style.display = "none";
    }  
}


function _delete_pls(e){
	console.log(e);
	pls_name = _only_playlist.value;
	var z = confirm("Are you sure want to delete playlist: "+pls_name);
	console.log(z);
	if(z){
		if(pls_name && pls_name != "select_existing_playlist"){
			var new_url = 'delete_playlist='+pls_name;
			var client = new getRequest();
			client.get(new_url, function(response) {
			console.log(response);
			_title.innerHTML = response;
			console.log('ya');
            _only_playlist.remove(_only_playlist.selectedIndex);
            var site_tmp = document.getElementById('site_option')
            var pls_tmp = 'PlayLists:'+pls_name+';'
            site_tmp.innerHTML = site_tmp.innerHTML.replace(pls_tmp, '');
			})
		}
		else{
			_title.innerHTML = 'Not deleted: Invalid Playlist';
		}
		
	}
	else{
		_title.innerHTML = 'Not deleted: Invalid playlist';
	}
    _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
}


function show_thumbnails_image(e){
    _custom_context.style.display = "none";
    _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
    var pl = _custom_context_menu_playlist;
    var r = pl.firstChild;
    k = 0
    while(r){
        var node = r.nodeName;
        var txt = r.innerHTML;
        if (node == 'LI'){
            txt = txt.trim();
        }else{
            txt = null;
        }
        if (txt){
            console.log(txt);
            if (txt == 'Show Thumbnails'){
                r.innerHTML = 'Hide Thumbnails';
                _show_thumbnails = true;
                break;
            }else if (txt == 'Hide Thumbnails'){
                r.innerHTML = 'Show Thumbnails';
                _show_thumbnails = false;
                break
            }
        }
        r = r.nextSibling;
        k += 1;
    }
    
    if (_show_thumbnails){
        var client = new getRequest();
		client.get('show_thumbnails', function(response) {
        console.log(response);
	})
    }else{
        var client = new getRequest();
		client.get('hide_thumbnails', function(response) {
        console.log(response);
	})
    }
    add_remove_image_node_to_playlist();
}

function show_thumbnails_image_set(e){
    var pl = _custom_context_menu_playlist;
    var r = pl.firstChild;
    k = 0
    while(r){
        var node = r.nodeName;
        var txt = r.innerHTML;
        if (node == 'LI'){
            txt = txt.trim();
        }else{
            txt = null;
        }
        if (txt){
            console.log(txt);
            if (txt == 'Show Thumbnails'){
                if (_show_thumbnails){
                    r.innerHTML = 'Hide Thumbnails';
                }
                break;
            }else if (txt == 'Hide Thumbnails'){
                if (!_show_thumbnails){
                    r.innerHTML = 'Show Thumbnails';
                }
                break
            }
        }
        r = r.nextSibling;
        k += 1;
    }
    
    add_remove_image_node_to_playlist();
}

function add_remove_image_node_to_playlist(){
    console.log('add_remove_image_node_to_playlist');
    console.log(_show_thumbnails);
    
    var r = document.getElementById("playlist");
    var first = r.firstChild;
    while(first){
        //console.log(r.nodeName);
        if (first.nodeName == "LI"){
            a = first.title;
            b = first.getAttribute("data-mp3");
            first.innerHTML = "";
            if (_show_thumbnails){
                img_div = add_thumbnail_to_playlist(a, b, 0);
            }else{
                img_div = add_thumbnail_to_playlist(a, b, 1);
            }
            first.appendChild(img_div);
            //console.log(a, b);
        }
        first = first.nextSibling;
    }
     
}

_playlist_custom.addEventListener("click", function (e) {
    if (e.target && e.target.nodeName === "LI") {
        
        
        if (_remote_val == 'on'){
        var child = e.target
		
		}
		var selected = _playlist_custom.querySelector(".selected");
    if (selected) {
        selected.classList.remove("selected");
    }
		console.log(e.target);
		//_title.innerHTML = e.target.innerHTML;
    }
});

function menu_clicked_hide(e){
    _custom_context.style.display = "none";
    _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
}

function menu_clicked_remove(e){
	var site_val = _first_select.value.toLowerCase();
	var opt = _second_select.value;
	var pl = _playlist_selected_element;
	if(site_val == 'playlists' && opt != null){
		console.log(site_val,opt)
		var playlist = opt;
		console.log(pl.getAttribute('data-mp3'),pl.getAttribute('data-num'),pl.innerHTML);
		var new_url = 'remove_from_playlist='+playlist+'&'+pl.getAttribute('data-num');
		console.log(new_url);
		var client = new getRequest();
		client.get(new_url, function(response) {
		console.log(response);
		_title.innerHTML = response;
		})
		r = document.getElementById('playlist');
		first = pl.nextSibling;
		var num = parseInt(pl.getAttribute('data-num'));
		r.removeChild(pl);
		while(first){
			first.setAttribute('data-num',num);
			num = num +1;
			first = first.nextSibling;
		}
	}
    if (e == 'hide') {
        _custom_context.style.display = "none";
    }  
}

function torrent_status(val){
	var new_url = 'get_torrent_info';
	if (val == 'status' || _status_command == 'status'){
		new_url = 'get_torrent_info';
	}
	else if(val == 'status_all' || _status_command == 'status_all') {
		new_url = 'get_all_torrent_info';
	}
	//console.log(val,new_url);
	var client = new getRequest();
	client.get(new_url, function(response) {
	//console.log(response);
	_title.innerHTML = response;
	})
}

function remote_control_update(){
    var new_url = 'get_remote_control_status';
    var client = new getRequest();
	client.get(new_url, function(response) {
	console.log(response);
    if (response.indexOf('::') >= 0){
            var arr_val = response.split('::');
            var total = arr_val[0];
            var cur_time = arr_val[1];
            var index_row = arr_val[2];
            var queue_list = parseInt(arr_val[3]);
            
            dur_int = parseInt(total);
            _player_progress.max = dur_int;
            dur_val = human_readable_time(dur_int);
            
            cur_int = parseInt(cur_time);
            _player_progress.value = cur_int;
            cur_val = human_readable_time(cur_int);
            
            _player_start_time.innerHTML = cur_val+ '/' + dur_val;
            
            if (_clicked_num != index_row){
                _clicked_num = index_row;
                first = _playlist.firstChild;
                var data_num = 1;
                clickedElement = null;
                while(first){
                    data_num = first.getAttribute('data-num');
                    if (data_num === _clicked_num){
                        clickedElement = first;
                        break;
                    }
                    first = first.nextSibling;
                }
                
                var selected = _playlist.querySelector(".selected");
                if (selected) {
                    selected.classList.remove("selected");
                }
                if (clickedElement){
                    clickedElement.classList.add("selected");
                    document.title = _clicked_num+" "+clickedElement.title;
                    _final_url = clickedElement.getAttribute('data-mp3');
                    _player_control_info.innerHTML = document.title;
                    _player_control_image.src = _final_url + '.image'
                    _player.src = _final_url;
                    _player.poster = _final_url + '.image'
                    
                    var tmp_name = clickedElement.innerHTML;
    
                    var win_width = window.innerWidth;
                    if (_show_thumbnails){
                        if (win_width <= 640){
                            _title.innerHTML = document.title;
                            _title.style.textAlign = 'center';
                        }else{
                            _title.innerHTML = tmp_name;
                            _title.style.textAlign = 'left';
                        }
                    }else{
                        _title.innerHTML = document.title;
                        _title.style.textAlign = 'left';
                    }
                    console.log('_can_play_sync');
                    console.log(_can_play_sync);
                    if(_can_play_sync){
                        var client = new getRequest();
                        client.get('playpause_pause', function(response) {
                        console.log(response);
                        })
                    }
                    
                    
                }
            }else if(queue_list != _remote_queue_value){
                var clickedElement = _playlist_custom.firstChild;
                if (clickedElement){
                    document.title = clickedElement.getAttribute('data-num')+" "+clickedElement.title;
                    _final_url = clickedElement.getAttribute('data-mp3');
                    _player_control_info.innerHTML = document.title;
                    _player_control_image.src = _final_url + '.image'
                    _player.src = _final_url;
                    _player.poster = _final_url + '.image'
                    
                    var tmp_name = clickedElement.innerHTML;
    
                    var win_width = window.innerWidth;
                    if (_show_thumbnails){
                        if (win_width <= 640){
                            _title.innerHTML = document.title;
                            _title.style.textAlign = 'center';
                        }else{
                            _title.innerHTML = tmp_name;
                            _title.style.textAlign = 'left';
                        }
                    }else{
                        _title.innerHTML = document.title;
                        _title.style.textAlign = 'left';
                    }
                    _playlist_custom.removeChild(clickedElement);
                    _remote_queue_value -= 1;
                }
            }
            
    }
	})
}

function human_readable_time(time)
{   
    var hrs = Math.floor(time / 3600);
    var mins = Math.floor((time % 3600) / 60);
    var secs = time % 60;
    var ret = "";
    if (hrs > 0) {
        ret += hrs + ":" + (mins < 10 ? "0" : "");
    }
    ret += mins + ":" + (secs < 10 ? "0" : "");
    ret += secs;
    return ret;
}

function update_progress_bar(){
    total = _player.duration;
    cur_time = _player.currentTime;
    //console.log(total, cur_time);
    if (total && cur_time){
        dur_int = parseInt(_player.duration);
        _player_progress.max = dur_int;
        dur_val = human_readable_time(dur_int);
        
        cur_int = parseInt(_player.currentTime);
        _player_progress.value = cur_int;
        cur_val = human_readable_time(cur_int);
        
        _player_start_time.innerHTML = cur_val+ '/' + dur_val;
        //console.log(val);
        //_player_progress.setAttribute('data-label', val);
    }else{
        _player_progress.max = 0;
        _player_progress.value = 0;
        _player_start_time.innerHTML = "00:00:00";
    }
}

function searchFunction(e, mode){
    mode = parseInt(mode);
    console.log('mode == ', mode);
	if(e.keyCode==13){
        if (mode == 0){
            var z = document.getElementById("type_search");
            var site = document.getElementById("site");
        }else{
            var z = _search_text_top;
            var site = _first_select;
        }
        var site_val = site.value.toLowerCase();
		console.log(z.value);
		if (z.value.length == 0){
            z.value = 'abc';
        }
		if (z.value.startsWith("torrent:")){
			new_val = z.value.replace("torrent:","");
			if (new_val.startsWith('http') || new_val.startsWith('magnet')){
				new_url = 'get_torrent=' + btoa(new_val);
				if (new_val.startsWith('magnet')){
					_title.innerHTML = 'Wait for few minutes..Magnet links may take time.';
				}
				else{
					_title.innerHTML = 'Wait..Getting Torrent';
				}
				var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
                if (response.startsWith('OK:')){
                    file_name = response.split(':')[1];
                    var new_opt = document.createElement('option');
                    var txt = file_name;
                    if (txt.length > 30){
                        txt = txt.slice(0,28)+ '..'
                    }
                    if (txt){
                        new_opt.text = txt;
                        new_opt.value = file_name;
                        new_opt.title = file_name;
                        _third_select.appendChild(new_opt);
                        _first_select.value = 'torrent';
                        siteChangeTop()
                        //_second_select.value = 'history';
                        //optChangeTop();
                        //_third_select.value = file_name;
                        _title.innerHTML = 'Got Torrent: Go To Torrent->History'
                    }
                }else{
                    _title.innerHTML = 'Failed Fetching Torrent';
                }
				
				})
			}
			else{
				if (site_val == 'torrent'){
					new_val = z.value.replace("torrent:","");
					if (new_val == 'stop'){
						new_url = 'stop_torrent';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						if (_get_torrent_status){
							console.log(_get_torrent_status,'--get--torrent--status--');
							clearInterval(_get_torrent_status);
							//_title.innerHTML = 'Stopped Status updating';
							_get_torrent_status = "";
						}
						else{
							console.log(_get_torrent_status,'--get-torrent-status--');
							console.log('nothing to stop');
						}
						})
					}
					else if(new_val == 'delete'){
                        if (mode == 0){
                            option_val = document.getElementById("opt_val");
                        }else{
                            option_val = _third_select;
                        }
						console.log(option_val.value);
						if (option_val != null && option_val != ''){
							new_url = 'get_torrent='+btoa('delete&'+option_val.value)
							var client = new getRequest();
							client.get(new_url, function(response) {
							console.log(response);
							_title.innerHTML = response;
                            _third_select.remove(_third_select.selectedIndex);
						})
						}
					}
					else if (new_val == 'status'){
						if(!_get_torrent_status || _get_torrent_status == null){
							torrent_status(new_val);
							_get_torrent_status = setInterval(torrent_status,5000,new_val);
						}
						else{
							console.log('Already updating');
						}
						_status_command = new_val;
					}
					else if (new_val == 'status_all'){
						if(!_get_torrent_status || _get_torrent_status == null){
							torrent_status(new_val);
							_get_torrent_status = setInterval(torrent_status,5000,new_val);
						}
						else{
							console.log('Already updating');
						}
						_status_command = new_val;
					}
					else if (new_val == 'status_stop'){
						if (_get_torrent_status){
							console.log(_get_torrent_status,'--get--torrent--status--');
							clearInterval(_get_torrent_status);
							_title.innerHTML = 'Stopped Status updating';
							_get_torrent_status = "";
						}
						else{
							console.log(_get_torrent_status,'--get-torrent-status--');
							console.log('nothing to stop');
						}
					}
					else if (new_val == 'pause_all'){
						new_url = 'torrent_all_pause';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
					else if (new_val == 'pause'){
						new_url = 'torrent_pause';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
					else if (new_val == 'resume'){
						new_url = 'torrent_resume';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
					else if (new_val == 'resume_all'){
						new_url = 'torrent_all_resume';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
					else if (new_val == 'remove'){
						new_url = 'torrent_remove';
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
					else if (new_val.startsWith('d:') || new_val.startsWith('u:')){
						if (new_val.indexOf('::') >=0){
							new_val = new_val.replace('::','&')
						}
						new_val = new_val.replace(/:/g,'=')
						new_url = 'set_torrent_speed='+new_val;
						var client = new getRequest();
						client.get(new_url, function(response) {
						console.log(response);
						_title.innerHTML = response;
						})
					}
				}else{
                    _title.innerHTML = 'Please Select Torrent Section First Before Issueing Torrent Commands';
                }
			}
			z.value = '';
		}
		else if(z.value.startsWith("create_playlist:")){
			var new_z = z.value.replace("create_playlist:","");
			if (new_z != null){
				var new_url = "create_playlist="+new_z;
				var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
				_title.innerHTML = response;
			})
			}
			z.value = '';
		}
        else if(z.value.startsWith("clear:")){
			var new_z = z.value.replace("clear:","");
			if (new_z != null && new_z.toLowerCase() == 'playlist_history'){
				var new_url = "clear_playlist_history";
				var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
				_title.innerHTML = response;
			})
			}else if (new_z != null && new_z.toLowerCase() == 'cache'){
				var new_url = "clear_all_cache";
				var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
				_title.innerHTML = response;
			})
			}
			z.value = '';
		}
		else if(z.value.startsWith("save_playlist:")){
			var new_z = z.value.replace("save_playlist:","");
			first = _playlist.firstChild;
			var new_url = "save_playlist="+new_z;
			dict = {};
			while(first){
				num = first.getAttribute('data-num');
				data = first.getAttribute('data-mp3');
				title = first.title;
				dict[num] = {'title':title,'data':data};
				first = first.nextSibling;
			}
			//console.log(JSON.stringify(dict));
			var client = new postRequest();
				client.post(new_url,dict,function(response) {
					console.log(response);
					_title.innerHTML = response;
			})
			z.value = '';
		}
		else if(z.value.startsWith("update:")){
			var new_z = z.value.replace("update:","");
			if (new_z != null && (new_z == 'video' || new_z == 'music')){
				if (new_z == 'video'){var new_url = "update_video";}
				else{ var new_url = "update_music";}
				_title.innerHTML = 'Wait updating...';
				var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
				_title.innerHTML = response;
			})
			}
			else{
				_title.innerHTML = 'wrong command, not allowed';
			}
			z.value = '';
		}
		else if(z.value.startsWith("quality:")){
			var new_z = z.value.replace("quality:","");
			var new_url = "quality="+new_z;
			dict = {};
			var client = new getRequest();
				client.get(new_url,function(response) {
					console.log(response);
					_title.innerHTML = response;
			})
			z.value = '';
		}
		else if(z.value.startsWith("playbackengine:")){
			var new_z = z.value.replace("playbackengine:","");
			var new_url = "playbackengine="+new_z;
			dict = {};
			var client = new getRequest();
				client.get(new_url,function(response) {
					console.log(response);
					_title.innerHTML = response;
			})
			z.value = '';
		}
		else if(z.value.startsWith("sub:")){
			var new_z = z.value.replace("sub:","");
			if (new_z == 'on'){
				_subtitle_status = "on";
				_title.innerHTML = 'Subtitle Turned On. Now restart the video again. <br>Make sure that ffmpeg is installed on the server.';
			}
			else if (new_z == 'off'){
				_subtitle_status = "off";
				while(_player.firstChild){_player.removeChild(_player.firstChild);}
				_title.innerHTML = 'Subtitle Turned Off';
			}
			else if (new_z == 'reload'){
				_subtitle_status = "on";
				_title.innerHTML = 'Trying to reload subtitle for current track again';
				var new_url = _final_url+'.reload.subtitle';
				get_subtitle(new_url);
			}
			z.value = '';
		}
		else if(z.value.startsWith("yt:")){
            if (mode == 0){
                _site_value_new = _site_value;
            }else{
                _site_value_new = _first_select;
            }
			if (_site_value_new.value.toLowerCase() == 'playlists'){
				var new_z = z.value.replace("yt:","");
                if (mode == 0){
                    var pls_name = document.getElementById('opt');
                }else{
                    var pls_name = _second_select;
                }
				if ((new_z && pls_name) || (new_z == 'audio' || new_z == 'audiovideo')){
					_title.innerHTML = 'wait..';
					if (new_z == 'd'){
						var title_name = _final_name.replace('YouTube - ','')
						var new_url = _final_url+'&&'+pls_name.value+'&name='+title_name+'.download';
					}
					else if (new_z == 'getsub'){
						var new_url = _final_url+'.getsub';
					}
					else if (new_z.startsWith('d:')) {
						new_z = new_z.replace('d:','');
						var new_url = 'youtube_url='+new_z+'&&'+pls_name.value+'.download';
					}
					else{
						var new_url = 'youtube_url='+new_z+'&&'+pls_name.value;
					}
					var client = new getRequest();
					client.get(new_url, function(response) {
					console.log(response);
					_title.innerHTML = response;
                    if (mode == 1){
                        optChangeTop();
                    }
					if (new_z == 'getsub'){
						if (response.toLowerCase() == 'got subtitle'){
							get_subtitle(_final_url+'.subtitle');
						}
					}
					})
				}
				else{
					_title.innerHTML = 'wrong command, no playlist was selected';
				}
			}
			else {
				_title.innerHTML = 'First Select proper playlist';
			}
			z.value = '';
		}
        else if(z.value.startsWith("ytq:")){
            if (mode == 0){
                _site_value_new = _site_value;
            }else{
                _site_value_new = _first_select;
            }
            var new_z = z.value.replace("ytq:","");
            var new_url = 'youtube_quick='+new_z;
            var client = new getRequest();
            _title.innerHTML = 'Wait!';
            client.get(new_url, function(response) {
            console.log(response);
            _title.innerHTML = response;
            })
        }else{
			
            if (mode == 0){
                site = document.getElementById("site");
                site_val = site.value;
            }else{
                site = _first_select;
                site_val = _first_select.value;
            }
			st = "site="+site.value.toLowerCase();
            if (mode == 0){
                option = document.getElementById("opt");
                opt_val = option.value;
            }else{
                option = _second_select;
                opt_val = _second_select.value;
            }
            
			opt = "&opt="+option.value.toLowerCase();
            if (mode == 0){
                srch = "&s="+z.value.replace(" ","+");
            }else{
                srch = "&s="+_search_text_top.value.replace(" ","+");
            }
			opt = opt.replace(/" "/g,"+")
			console.log(opt);
			srch_val = srch.toLowerCase();
			if (srch_val.indexOf(".m3u") >=0 || srch_val.indexOf(".pls") >=0){
				console.log(srch_val);
			}
			else{
				srch = srch+'.m3u';
			}
			new_url = st+opt+srch;
			console.log(new_url);
            _current_working_m3u = new_url;
			var client = new getRequest();
			client.get(new_url, function(response) {
			m = response.split('\n');
			r = document.getElementById('playlist')
			while(r.firstChild){r.removeChild(r.firstChild);}
			var indx = 1;
			for(i=1;i<m.length-1;i+=2){
				var a = m[i].substring(10,500);
                a = a.trim();
                if (a.startsWith('-')){
                    a = a.slice(1, 500);
                    a = a.trim();
                }
				var b = m[i+1];
				var new_opt = document.createElement('li');
				new_opt.setAttribute('data-mp3',b);
				new_opt.setAttribute('draggable','true');
				new_opt.setAttribute('ondragstart','drag_start(event)');
				new_opt.setAttribute('ondrop','on_drop(event)');
				new_opt.setAttribute('ondragover','drag_over(event)');
				new_opt.setAttribute('ondragend','drag_end(event)');
				new_opt.setAttribute('ondragenter','drag_enter(event)');
				new_opt.setAttribute('ondragleave','drag_leave(event)');
				new_opt.setAttribute('data-num',indx.toString());
                new_opt.setAttribute('title', a);
                if (_show_thumbnails){
                    img_div = add_thumbnail_to_playlist(a, b, 0);
                }else {
                    img_div = add_thumbnail_to_playlist(a, b, 1);
                    
                }
                new_opt.appendChild(img_div);
				r.appendChild(new_opt);
				indx += 1;
				}
			})
            if (mode == 1){
                if (site_val.toLowerCase() == 'playlists'){
                    for(i=0; i<pls_arr.length; i++){
                        if (z.value.toLowerCase() === pls_arr[i].toLowerCase()){
                            _second_select.value = pls_arr[i];
                            break;
                            
                        }
                    }
                }
            }
        }
        z.value = '';
	}
    
}

function _sync_pls(){
	new_z = _only_playlist.value;
	if (new_z != null && new_z != 'select_existing_playlist'){
		var new_url = "save_playlist="+new_z;
		dict = {};
		first = _playlist_custom.firstChild;
		i = 1;
		while(first){
			num = i.toString();
			data = first.getAttribute('data-mp3');
			title = first.title;
			dict[num] = {'title':title,'data':data};
			first = first.nextSibling;
			i += 1;
		}
		var client = new postRequest();
			client.post(new_url,dict,function(response) {
				console.log(response);
				_title.innerHTML = response;
		})
	}else{
        _title.innerHTML = 'Plese Select Existing Playlist first in which you have to save items';
    }
}

function show_player_window(){
	var client = new getRequest();
	client.get('show_player_window', function(response) {
	console.log(response);
	})
}

function hide_player_window(){
	var client = new getRequest();
	client.get('hide_player_window', function(response) {
	console.log(response);
	})    
}

function toggle_subtitle_player(){
	var client = new getRequest();
	client.get('toggle_subtitle', function(response) {
	console.log(response);
	})    
}

function toggle_audio_player(){
	var client = new getRequest();
	client.get('toggle_audio', function(response) {
	console.log(response);
	})    
}

function goto_previous_chapter(){
	var client = new postRequest();
    let data = {'param': 'click', 'widget': 'btn_chapter_minus'};
	client.post('sending_web_command', data, function(response) {
	console.log(response);
	})
}

function goto_next_chapter(){
	var client = new postRequest();
    let data = {'param': 'click', 'widget': 'btn_chapter_plus'};
	client.post('sending_web_command', data, function(response) {
	console.log(response);
	})
}

function toggle_fullscreen_window(){
	var client = new postRequest();
    let data = {'param': 'click', 'widget': 'btn_fs_window'};
	client.post('sending_web_command', data, function(response) {
	console.log(response);
	})
}

function show_video_stats(){
	var client = new postRequest();
    let data = {'param': 'click', 'widget': 'btn_show_stat'};
	client.post('sending_web_command', data, function(response) {
	console.log(response);
	})
}

function show_video_stats(){
	var client = new postRequest();
    let data = {'param': 'click', 'widget': 'btn_show_stat'};
	client.post('sending_web_command', data, function(response) {
	console.log(response);
	})
}

function change_aspect_ratio(){
    let aspect_ratio = document.getElementById("aspect_ratio").value;
    if(aspect_ratio == ""){
        console.log("no aspect ratio selected");
    }else{
	    var client = new postRequest();
        let data = {'param': 'click', 'widget': aspect_ratio};
	    client.post('sending_web_command', data, function(response) {
	    console.log(response);
	})
    }
}

function change_playback_engine(){
    let playback_engine = document.getElementById("playback_engine").value;
    if(playback_engine == ""){
        console.log("playback engine not changed");
    }else{
	    var new_url = "playbackengine="+playback_engine+"&mode="+_toggle_master.innerHTML;
		var client = new getRequest();
		client.get(new_url,function(response) {
			console.log(response);
			_title.innerHTML = response;
		})
    }
}


function apply_video_category(){
    let video_label = document.getElementById("video_label").value;
    if(video_label == ""){
        _title.innerHTML = "No label selected";
    }else{
        let pls_nodes = document.getElementById("playlist");
        let pls_arr = []
        for(let i=0;i<pls_nodes.children.length;i++)
        {pls_arr.push(pls_nodes.children[i].getAttribute("data-mp3"))
        }
	    var client = new postRequest();
        let data = {'category': video_label, 'playlist': pls_arr};
	    client.post('modify_category', data, function(response) {
	    console.log(response);
        _title.innerHTML = response;
	})
    }
}

function rename_video_title(){

    let select = document.getElementById("third_select");
    let index = select.selectedIndex;
    let title = "";
    if(index >= 0){
        title = select[index].text;
    }
    let prompt_val = prompt("Enter New Title:", title)
	if(prompt_val != null && prompt_val != ''){
        let pls_nodes = document.getElementById("playlist");
        let pls_arr = []
        for(let i=0;i<pls_nodes.children.length;i++)
        {pls_arr.push(pls_nodes.children[i].getAttribute("data-mp3"))
        }
	    var client = new postRequest();
        let data = {'title': prompt_val, 'playlist': pls_arr};
	    client.post('rename_title', data, function(response) {
	    console.log(response);
        _title.innerHTML = response;
	})
    }else{
        _title.innerHTML = "nothing entered";
    }
}

function cast_url(){
    let prompt_val = prompt("Enter URL:", "")
    if(prompt_val != null && prompt_val != ''){
        var new_url = 'youtube_quick='+prompt_val;
        var client = new getRequest();
        _title.innerHTML = 'Wait!';
        client.get(new_url, function(response) {
            console.log(response);
            _title.innerHTML = response;
        })
    } else {
        _title.innerHTML = "nothing entered";
    }
}

function fetch_poster(mode){

    console.log(mode)
    let select = document.getElementById("third_select");
    let index = select.selectedIndex;
    let title = "";
    if(index >= 0){
        title = select[index].text;
    }
    let prompt_val = prompt("Enter URL of the poster:", "")
	if(prompt_val != null && prompt_val != ''){
	    var client = new postRequest();
        let data = {'url': prompt_val, 'title': title, 'mode': mode, 'site_option': 'video'};
	    client.post('fetch-posters', data, function(response) {
	    console.log(response);
        _title.innerHTML = response;
	})
    }else{
        _title.innerHTML = "nothing entered";
    }
}


function optChange(){
	var x = document.getElementById("opt").value.toLowerCase();
	x = x.replace(/" "/g,"+");
	console.log(x);
	var y = document.getElementById("site").value.toLowerCase();
	if(y.startsWith('playlists')){
		var new_url = 'site='+y+'&opt='+x+'&s=&exact.m3u';
        _current_working_m3u = new_url;
		var client = new getRequest();
		client.get(new_url, function(response) {
		m = response.split('\n');
		r = document.getElementById('playlist')
		while(r.firstChild){r.removeChild(r.firstChild);}
		var indx = 1;
		for(i=1;i<m.length-1;i+=2){
			var a = m[i].substring(10,500);
            a = a.trim();
            if (a.startsWith('-')){
                a = a.slice(1, 500);
                a = a.trim();
            }
			var b = m[i+1];
			var new_opt = document.createElement('li');
			new_opt.setAttribute('data-mp3',b);
			new_opt.setAttribute('data-num',indx.toString());
			new_opt.setAttribute('draggable','true');
			new_opt.setAttribute('ondragstart','drag_start(event)');
			new_opt.setAttribute('ondrop','on_drop(event)');
			new_opt.setAttribute('ondragover','drag_over(event)');
			new_opt.setAttribute('ondragend','drag_end(event)');
			new_opt.setAttribute('ondragenter','drag_enter(event)');
			new_opt.setAttribute('ondragleave','drag_leave(event)');
            new_opt.setAttribute('title', a);
            if (_show_thumbnails){
                img_div = add_thumbnail_to_playlist(a, b, 0);
            }else{
                img_div = add_thumbnail_to_playlist(a, b, 1);
            }
            new_opt.appendChild(img_div);
			r.appendChild(new_opt);
			indx += 1;
			}
		})
		_display_option.style.display = "none";
		
	}else{
		var z = 'site='+y+'&opt='+x;
		var client = new getRequest();
        var colon_present = false;
        if (y == 'video' || y == 'music'){
            colon_present = true;
        }
		client.get(z, function(response) {
		//console.log(response);
		m = response.split('\n');
		//console.log(m);
		r = document.getElementById('opt_val');
		while(r.firstChild){r.removeChild(r.firstChild);}
		for(i=0;i<m.length;i++){
			var new_opt = document.createElement('option');
			var txt = m[i];
            if (colon_present){
                txt = txt.split('::::')[0]
            }
            if (txt.length > 30){
                txt = txt.slice(0,28)+ '..'
            }
			if (txt){
                new_opt.text = txt;
                if (colon_present){
                    new_opt.value = m[i].split('::::')[1];
                    new_opt.title = m[i].split('::::')[0];
                }else{
                    new_opt.value = m[i];
                    new_opt.title = m[i];
                }
                //console.log(i,txt);
                r.appendChild(new_opt);
                //new_opt.style.overflow = 'auto';
            }
		}
		_display_option.style.display = "grid";
		r.hidden = "";
		_opt_val_ok.hidden = "";
		
		})
	}
	var z = document.getElementById("type_search");
	z.value = "";
}

function optChangeTop(){
	var x = _second_select.value.toLowerCase();
	x = x.replace(/" "/g,"+");
	console.log(x);
	var y = _first_select.value.toLowerCase();
    console.log(_first_select.value, _second_select.value, _third_select.value);
	if(y.startsWith('playlists')){
        x = _second_select.value;
		var new_url = 'site='+y+'&opt='+x+'&s=&exact.m3u';
        _current_working_m3u = new_url;
		var client = new getRequest();
		client.get(new_url, function(response) {
		m = response.split('\n');
		r = document.getElementById('playlist')
		while(r.firstChild){r.removeChild(r.firstChild);}
		var indx = 1;
		for(i=1;i<m.length-1;i+=2){
			var a = m[i].substring(10,500);
            a = a.trim();
            if (a.startsWith('-')){
                a = a.slice(1, 500);
                a = a.trim();
            }
			var b = m[i+1];
			var new_opt = document.createElement('li');
			new_opt.setAttribute('data-mp3',b);
			new_opt.setAttribute('data-num',indx.toString());
			new_opt.setAttribute('draggable','true');
			new_opt.setAttribute('ondragstart','drag_start(event)');
			new_opt.setAttribute('ondrop','on_drop(event)');
			new_opt.setAttribute('ondragover','drag_over(event)');
			new_opt.setAttribute('ondragend','drag_end(event)');
			new_opt.setAttribute('ondragenter','drag_enter(event)');
			new_opt.setAttribute('ondragleave','drag_leave(event)');
            new_opt.setAttribute('title', a);
            if (_show_thumbnails){
                img_div = add_thumbnail_to_playlist(a, b, 0);
            }else{
                img_div = add_thumbnail_to_playlist(a, b, 1);
            }
            new_opt.appendChild(img_div);
			r.appendChild(new_opt);
			indx += 1;
			}
		})
        _third_select.innerHTML = "";
        var new_opt = document.createElement('option');
        new_opt.text = 'Not Required';
        new_opt.value = 'nothing';
        new_opt.title = 'nothing';
        new_opt.disabled = true;
        _third_select.appendChild(new_opt);
		
	}else{
		var z = 'site='+y+'&opt='+x;
		var client = new getRequest();
		client.get(z, function(response) {
		m = response.split('\n');
        console.log(response);
        _third_select.innerHTML = "";
        _mydatalist.innerHTML = "";
		//while(_third_select.firstChild){_third_select.removeChild(_third_select.firstChild);}
        if (_first_select.value.toLowerCase() === 'playlists' || !response){
            var new_opt = document.createElement('option');
            if(!response){
                new_opt.text = 'Nothing Available';
            }else{
                new_opt.text = 'Not Required';
            }
            new_opt.value = 'nothing';
            new_opt.title = 'nothing';
            new_opt.disabled = true;
            _third_select.appendChild(new_opt);
            
        } 
        win_width = window.innerWidth;
        var colon_present = false;
        if (y == 'video' || y == 'music'){
            colon_present = true;
        }
		for(i=0;i<m.length;i++){
			var new_opt = document.createElement('option');
            var new_opt_data = document.createElement('option');
			var txt = m[i];
            if (colon_present){
                txt = txt.split('::::')[0]
            }
            if (win_width <= 640){
                if (txt.length > 30){
                    txt = txt.slice(0,28)+ '..'
                }
            }
			if (txt){
                new_opt.text = new_opt_data.text = txt;
                if (colon_present){
                    new_opt.value = m[i].split('::::')[1];
                    new_opt.title = new_opt_data.title = new_opt_data.value = m[i].split('::::')[0];
                }else{
                    new_opt.value = new_opt_data.value = m[i];
                    new_opt.title = new_opt_data.title = m[i];
                }
                _third_select.appendChild(new_opt);
                _mydatalist.append(new_opt_data);
            }
		}
        console.log(_first_select.value, _second_select.value, _third_select.value);
        if(_first_select.value != 'select' && _second_select.value != 'select_category' && _second_select.value.toLowerCase() != 'playlists' && _third_select.value != "nothing"){
            optValChangeTop();
        }
		})
        
	}
}


function add_thumbnail_to_playlist(a, b, mode){
    width = window.innerWidth;
    img_div = document.createElement('div');
    img_div.setAttribute('id', 'img-id');
    img_opt = document.createElement('img');
    if (mode == 0){
        img_opt.setAttribute('src', b+'.image');
    }else{
        img_opt.setAttribute('src', '');
    }
    console.log(width, '----');
    width_length = 128;
    if (width > 350){
        img_opt.setAttribute('width', '128');
    }else{
        width_length = width/3
        img_opt.setAttribute('width', (width_length).toString());
    }
    img_opt.style.float = 'left';
    img_div.appendChild(img_opt)
    img_opt.style.margin = "0px 4px 0px 0px";
    img_info = document.createElement('div');
    img_info.setAttribute('id', 'img-info');
    
    if (width <= 480 && mode == 0){
        if (width > 350){
            img_info.style.maxWidth = '128px';
            if (a.length > 45){
                a = a.slice(0, 45)+ '..';
            }
        }else{
            img_info.style.maxWidth = width_length.toString() + 'px';
            if (a.length > 30){
                a = a.slice(0, 30)+ '..';
            }
        }
        img_info.style.margin = "0px 0px 0px 4px";
    }else{
        img_info.style.maxWidth = '256px';
        img_info.style.margin = "0px 0px 0px 4px";
    }
    img_info.innerHTML = a;
    img_info.style.float = 'left';
    //img_info.style.textAlign = 'justify';
    img_div.appendChild(img_info)
    img_div.style.overflow = 'auto';
    return img_div;
}

function drag_start(e){
	console.log(e.target.getAttribute('data-num'));
	e.dataTransfer.effectAllowed='move';
    e.dataTransfer.setData("link", e.target.getAttribute('data-mp3'));
    e.dataTransfer.setData("num", e.target.getAttribute('data-num'));
    e.dataTransfer.setData("text", e.target.innerHTML);
    e.dataTransfer.setData("title", e.target.title);
    e.dataTransfer.setData("node", e.target);
    e.dataTransfer.setDragImage(e.target,0,0);
    _drag_start_y = e.clientY;
}

function custom_drop(e){
    try{
		e.target.style.border = "";}
	catch(err){
		console.log(err);
	}
	console.log('---on--drop---')
	console.log(e);
	e.preventDefault();
	 var link_ = e.dataTransfer.getData("link");
	 var num_ = e.dataTransfer.getData("num");
	 var text_ = e.dataTransfer.getData("text");
	 var node_ = e.dataTransfer.getData("node");
     var title_drop = e.dataTransfer.getData("title");
	// console.log(link_);
	
	// console.log(text_);
	var num_target = e.target.getAttribute('data-num');
    var new_opt = document.createElement('li');
	console.log(node_);
    console.log(num_,num_target);
	new_opt.innerHTML = text_;
	new_opt.setAttribute('data-mp3',link_);
	new_opt.setAttribute('draggable','true');
	new_opt.setAttribute('ondragstart','drag_start(event)');
	new_opt.setAttribute('ondrop','custom_drop(event)');
	new_opt.setAttribute('ondragover','drag_over(event)');
	new_opt.setAttribute('ondragend','drag_end(event)');
	new_opt.setAttribute('ondragenter','drag_enter(event)');
	new_opt.setAttribute('ondragleave','drag_leave(event)');
	new_opt.setAttribute('data-num',num_target);
    new_opt.setAttribute('title',title_drop);
	if (parseInt(num_) >= parseInt(num_target)){
		_playlist_custom.insertBefore(new_opt,e.target);
	}
	else{
		if (e.target.nextSibling){
			_playlist_custom.insertBefore(new_opt,e.target.nextSibling);
		}
		else{
			_playlist_custom.appendChild(new_opt);
		}
	}
	first = _playlist_custom.firstChild;
     e.stopPropagation();
     //console.log(e.target);
     indx = 1;
     while(first){
		cnt_indx = first.getAttribute('data-num');
		if(cnt_indx == num_){
			first.setAttribute('data-num','-1');
			first = first.nextSibling;
		}
		else{
			first.setAttribute('data-num',indx.toString());
			first = first.nextSibling;
			indx = indx +1; 
		}
	}
	first = _playlist_custom.firstChild;
	while(first){
		cnt_indx = first.getAttribute('data-num');
		if(cnt_indx == '-1'){
			_playlist_custom.removeChild(first);
			break;
		}
		first = first.nextSibling;
	}
    
}

function click_to_add_to_playlist(e){
	console.log('---click on add to playlist--')
	console.log(e);
    var link_ = e.getAttribute("data-mp3");
    var text_ = e.innerHTML;
	var data_num = e.getAttribute("data-num");
    var new_opt = document.createElement('li');
	new_opt.innerHTML = text_;
	new_opt.setAttribute('data-mp3',link_);
	new_opt.setAttribute('draggable','true');
    
    new_opt.setAttribute('ondragstart','drag_start(event)');
	new_opt.setAttribute('ondrop','custom_drop(event)');
	new_opt.setAttribute('ondragover','drag_over(event)');
	new_opt.setAttribute('ondragend','drag_end(event)');
	new_opt.setAttribute('ondragenter','drag_enter(event)');
	new_opt.setAttribute('ondragleave','drag_leave(event)');
    
    new_opt.setAttribute('data-num', data_num)
    new_opt.setAttribute('title', e.title);
	_playlist_custom.appendChild(new_opt);
    
    if (_remote_val == 'on'){
        var req_val = 'queueitem_'+data_num;
        var client = new getRequest();
        client.get(req_val, function(response) {
        console.log(response);
        _remote_queue_value += 1;
	})}
}

function create_playlist_dynamically(mode){
    var plsmenu = document.getElementById("playlist_context_menu_items");
    while(plsmenu.firstChild){plsmenu.removeChild(plsmenu.firstChild);}
    var plsname = "";
    for (var i = 0; i < pls_arr.length; i++){
        plsname = pls_arr[i];
        var pls_entry = document.createElement('li');
        pls_entry.setAttribute('id', 'playlist_context_menu_item');
        pls_entry.setAttribute('label', plsname);
        pls_entry.setAttribute('onclick', 'playlist_contextmenu_clicked(label)');
        pls_entry.setAttribute('style', 'margin:4px;padding:4px;')
        pls_entry.setAttribute('onmouseover', 'playlist_hover_in(this)')
        pls_entry.setAttribute('onmouseout', 'playlist_hover_out(this)')
        pls_entry.innerHTML = plsname;
        plsmenu.appendChild(pls_entry);
        pls_entry.label = plsname;
    }
    var pls_entry = document.createElement('li');
    pls_entry.setAttribute('id', 'playlist_context_menu_item');
    pls_entry.setAttribute('label', 'hide');
    pls_entry.setAttribute('onclick', 'playlist_contextmenu_clicked(label)');
    pls_entry.setAttribute('style', 'margin:4px;padding:4px;')
    pls_entry.setAttribute('onmouseover', 'playlist_hover_in(this)')
    pls_entry.setAttribute('onmouseout', 'playlist_hover_out(this)')
    pls_entry.innerHTML = 'Hide';
    pls_entry.label = 'hide';
    plsmenu.appendChild(pls_entry);
    if (mode == 1){
        create_playlist_select_options(pls_arr, 1);
    }
    
}

function menu_clicked_add_to_playlist(e){
    _custom_context.style.display = "none";
    var plsmenu = document.getElementById("playlist_context_menu_items");
    var r = plsmenu.firstChild;
    r = r.innerHTML;
    console.log(r);
    if (plsmenu.firstChild == null || !plsmenu.firstChild || !r || r == null){
        create_playlist_dynamically(1);
    }
    _playlist_context_menu.style.display = "block";
    _playlist_context_menu.style.left = (e.pageX-10)+"px";
    _playlist_context_menu.style.top = (e.pageY-10)+"px";
    //window.scrollTo(_top_xy[0], _top_xy[1]);
}

function playlist_contextmenu_clicked(label){
    console.log(label);
    if (label != 'hide'){
        _only_playlist.value = label;
        menu_clicked_playlist('hide');
    }
    _playlist_context_menu.style.display = "none";
    _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
}

function playlist_hover_in(e){
    e.style.backgroundColor = '#dcdcdc';
    e.style.color = 'black';
    //console.log(e.innerHTML);
}

function playlist_hover_out(e){
    e.style.backgroundColor = '#fff';
    e.style.color = '#0066aa';
    //console.log(e.innerHTML);
}

function _create_custom_playlist(e){
    if (e == 'hide'){
        _custom_context.style.display = "none";
        _playlist_selected_element.style.backgroundColor = _old_playlist_selected_color;
    }
    var prompt_val = prompt("Enter Playlist Name:", "myplaylist")
	if(prompt_val != null && prompt_val != ''){
            console.log(prompt_val)
			var new_url = "create_playlist="+prompt_val;
			var client = new getRequest();
				client.get(new_url, function(response) {
				console.log(response);
                if (response == '1:OK'){
                    _title.innerHTML = 'playlist successfully created';
                    var client = new getRequest();
                    client.get('get_all_playlist', function(response) {
                        console.log(response);
                        pls_arr.push(prompt_val);
                        create_playlist_select_options(response, 0);
                        create_playlist_dynamically(0);
                        var site_tmp = document.getElementById('site_option')
                        site_tmp.innerHTML = site_tmp.innerHTML+';PlayLists:'+prompt_val+';'
                        //onDocReady()
                    })
                }else if (response == '2:WRONG'){
                    _title.innerHTML = 'file already exists; choose different name';
                }else {
                    _title.innerHTML = 'wrong pparameters';
                }
			})
	}else{
        _title.innerHTML = 'No Input Given';
    }
    
}

function drag_start_remove(e){
	e.dataTransfer.effectAllowed='move';
	var node = e.target;
	e.target.parentNode.removeChild(node);
}

function on_drop(e){
	try{
		e.target.style.border = "";}
	catch(err){
		console.log(err);
	}
	console.log('---on--drop---')
	console.log(e);
	e.preventDefault();
	 var link_ = e.dataTransfer.getData("link");
	 var num_ = e.dataTransfer.getData("num");
	 var text_ = e.dataTransfer.getData("text");
	 var node_ = e.dataTransfer.getData("node");
     var title_drop = e.dataTransfer.getData("title");
	// console.log(link_);
	
	// console.log(text_);
	var num_target = e.target.getAttribute('data-num');
    var new_opt = document.createElement('li');
	console.log(node_);
    console.log(num_,num_target);
	new_opt.innerHTML = text_;
	new_opt.setAttribute('data-mp3',link_);
	new_opt.setAttribute('draggable','true');
	new_opt.setAttribute('ondragstart','drag_start(event)');
	new_opt.setAttribute('ondrop','on_drop(event)');
	new_opt.setAttribute('ondragover','drag_over(event)');
	new_opt.setAttribute('ondragend','drag_end(event)');
	new_opt.setAttribute('ondragenter','drag_enter(event)');
	new_opt.setAttribute('ondragleave','drag_leave(event)');
	new_opt.setAttribute('data-num',num_target);
    new_opt.setAttribute('title',title_drop);
	if (parseInt(num_) >= parseInt(num_target)){
		_playlist.insertBefore(new_opt,e.target);
	}
	else{
		if (e.target.nextSibling){
			_playlist.insertBefore(new_opt,e.target.nextSibling);
		}
		else{
			_playlist.appendChild(new_opt);
		}
	}
	first = _playlist.firstChild;
     e.stopPropagation();
     //console.log(e.target);
     indx = 1;
     while(first){
		cnt_indx = first.getAttribute('data-num');
		if(cnt_indx == num_){
			first.setAttribute('data-num','-1');
			first = first.nextSibling;
		}
		else{
			first.setAttribute('data-num',indx.toString());
			first = first.nextSibling;
			indx = indx +1; 
		}
	}
	first = _playlist.firstChild;
	while(first){
		cnt_indx = first.getAttribute('data-num');
		if(cnt_indx == '-1'){
			_playlist.removeChild(first);
			break;
		}
		first = first.nextSibling;
	}
	var site_val = _first_select.value.toLowerCase();
	var opt = _second_select.value;
	console.log(opt,'--opt--');
	if (site_val == 'playlists' && opt != null && opt){
		new_url = 'change_playlist_order='+opt+'&'+num_+'&'+num_target;
		var client = new getRequest(new_url);
		client.get(new_url, function(response) {
		console.log(response);
		_title.innerHTML = response;
		})
	}
}

function drag_over(e){
	//console.log(e.target);
	e.preventDefault();
}

function drag_end(e){
	//console.log(e.target,'---drag--end--');
	e.preventDefault();
}

function drag_enter(e){
	console.log('drag----enter');
	e.preventDefault();
	
	console.log(_drag_start_y,e.clientY);
	if (_drag_start_y >= e.clientY){
		try{
			e.target.style.borderTop = "1px solid #cccccc";}
		catch(err){
			console.log(err);
		}
	}
	else{
		try{
			e.target.style.borderBottom = "1px solid #cccccc";}
		catch(err){
			console.log(err);
		}
	}
}

function drag_leave(e){
	//console.log(e.target,'drag--leave--');
	e.preventDefault();
	try{
		e.target.style.border = "";}
	catch(err){
		console.log(err);
	}
}

function onDocReady(){
	var old_var= _remote.innerHTML;
	var x = document.getElementById("site").value;
	console.log(x);
	var y = document.getElementById("site_option");
	var z = y.innerHTML;
	var w = z.split(';');
    var user_agent = window.navigator.userAgent.toLowerCase();
    //if (user_agent.indexOf('android')>=0){
    //    _buttons_div.style.height = '64px';
    //}
	console.log(w);
	if (w[0].toLowerCase() == 'remotefield:false'){
		_remote.style.display = "none";
		_empty_btn.style.display = "block";
		_empty_btn.innerHTML = "--";
		
	}else if (w[0].toLowerCase() == 'remotefield:true'){
		_remote.style.display = "block";
		_empty_btn.style.display = "none";
		_empty_btn.innerHTML = "--";
		}
	
	if (w[1].toLowerCase() == 'remotecontrol:false'){
		_remote.innerHTML = 'R:Off';
		_remote_val = 'off';
		_remote_control_buttons.style.display = "none";
	}else if (w[1].toLowerCase() == 'remotecontrol:true'){
		_remote.innerHTML = 'R:On';
		_remote_val = 'on';
		_remote_control_buttons.style.display = "block";
		}
	if (w[2].toLowerCase() == 'thumbnails:true' || (user_agent.indexOf('android')>=0 && user_agent.indexOf('chrome')>=0)){
        _show_thumbnails = true;
        show_thumbnails_image_set('True');
    }else{
        _show_thumbnails = false;
        show_thumbnails_image_set('False');
    }
    
    if (w[3].toLowerCase() == 'webcontrol:master'){
		_toggle_master.innerHTML = 'Master';
	}else if (w[3].toLowerCase() == 'webcontrol:slave'){
        _toggle_master.innerHTML = 'Slave';
		}
  
    if (w[4].startsWith("categories:")){
        let categories = w[4].split(":")[1].split(",");
        let cat_select = document.getElementById("video_label");
        for(let i in categories){
            let label = categories[i];
            var new_opt = document.createElement("option");
            new_opt.text = label;
            new_opt.value = label;
            cat_select.appendChild(new_opt);
        }
        
	}
    
	var x = document.getElementById("site").value;
	console.log(x);
	
	var cur_url = window.location.href;
	if (cur_url.indexOf('site=') >= 0){
		var site_split = cur_url.split('&');
		var site_opt = (site_split[0]).split('=')[1];
		x = site_opt;
		document.getElementById("site").value = x;
	}
	if (cur_url.indexOf('opt=') >= 0){
		var opt_split = cur_url.split('&');
		var opt_opt = (opt_split[1]).split('=')[1];
		op = 'opt_opt='+opt_opt
		if (opt_opt.indexOf('%20') >= 0){
			opt_opt = opt_opt.replace('%20',' ')
			}
		console.log(op);
	}
	var a = x.toLowerCase();
	var req = document.getElementById("opt");
	req.innerHTML = "";
    _second_select.innerHTML = "";
    pls_arr.length = 0;
	for(i=0;i<w.length;i++){
		j = w[i].toLowerCase().split(':')[0];
		m = w[i].split(':');
		if (m[0].toLowerCase() == 'playlists'){
			pls_arr.push(m[1]);
		}
		if(j.indexOf(x) >=0){
			console.log(j);
			k=w[i].split(":");
			l=j.split(":");
			var new_opt = document.createElement("option");
			new_opt.text = k[1].substring(0,45);
			new_opt.value = k[1];
			req.appendChild(new_opt);
			console.log(new_opt.value+' :created');
			}
		}
	var z1 = document.getElementById("opt");
	z1.value = opt_opt;
	var z = document.getElementById("type_search");
	z.hidden = "";
	//_selection_site.hidden = "hidden";
	w = window.innerWidth;
	if(w <= 640)
		{_player.width=(w-30).toString();
        _video_section.style.width = _player.width +'px';
        _buttons_div.style.width = _player.width+ 'px';
		_player.height=parseInt((1/_aspect_ratio)*w).toString();
		console.log(screen.width);}
    else{
        var new_width = w*0.6;
        _player.width = new_width.toString();
        _video_section.style.width = _player.width + 'px';
        _buttons_div.style.width = _player.width+ 'px';
        _player.height=parseInt((1/_aspect_ratio)*new_width).toString();
        }
    pls_arr.sort()
	console.log(pls_arr);
	
	//r = document.getElementById('menu_playlist')
	//while(r.firstChild){r.removeChild(r.firstChild);}
	//for(i=0;i<pls_arr.length;i+=1){
	//	var new_opt = document.createElement('menuitem');
	//	new_opt.setAttribute('label',pls_arr[i]);
	//	new_opt.setAttribute('onclick','menu_clicked(label)');
	//	r.appendChild(new_opt);
	//	}
    _first_select.value = "select";
    first_child = _first_select.firstChild;
    if (first_child.value === 'select'){
        first_child.disabled = true;
    }
    var new_opt = document.createElement("option");
    new_opt.text = "Select Category";
    new_opt.value = "select_category";
    new_opt.disabled = true;
    _second_select.appendChild(new_opt);
    create_playlist_select_options(pls_arr, 1);
	while(_player.firstChild){_player.removeChild(_player.firstChild);}
    hide_alternate_menu_buttons();
    top_bar_change_layout();
    _top_menu_bar.style.display = 'none';
    //max_min_top_bar();
    
    
}

function siteChange(){
	var x = document.getElementById("site").value;
	console.log(x);
	var y = document.getElementById("site_option");
	var z = y.innerHTML;
	var w = z.split(';');
	console.log(w);
	var a = x.toLowerCase();
	var req = document.getElementById("opt");
	req.innerHTML = "";
	for(i=0;i<w.length;i++){
		//console.log(w[i])
		j = w[i].toLowerCase().split(':')[0];
		if(j.indexOf(x) >= 0){
			console.log(j);
			k=w[i].split(":");
			l=j.split(":");
			console.log(l[0].concat(k[1]));
			var new_opt = document.createElement("option");
			new_opt.text = k[1].substring(0,45);
			new_opt.value = k[1];
			req.appendChild(new_opt);
			}
		}
	var z = document.getElementById("type_search");
	z.hidden = "";
	z.value = "";
}


function siteChangeTop(){
	var x = _first_select.value;
	console.log(x);
	var y = document.getElementById("site_option");
	var z = y.innerHTML;
	var w = z.split(';');
	console.log(w);
	var a = x.toLowerCase();
	_second_select.innerHTML = "";
    var new_opt = document.createElement("option");
    new_opt.text = 'Select Category';
    new_opt.value = 'select_category';
    new_opt.disabled = true;
    _second_select.appendChild(new_opt);
	for(i=0;i<w.length;i++){
		//console.log(w[i])
		j = w[i].toLowerCase().split(':')[0];
		if(j.indexOf(x) >= 0){
			console.log(j);
			k=w[i].split(":");
			l=j.split(":");
			console.log(l[0].concat(k[1]));
			var new_opt = document.createElement("option");
			new_opt.text = k[1].substring(0,45);
			new_opt.value = k[1];
			_second_select.appendChild(new_opt);
			}
		}
    if (_first_select.value.toLowerCase() == 'playlists'){
        _mydatalist.innerHTML = "";
        for(i = 0; i<=pls_arr.length;i++){
            new_opt = document.createElement('option');
            new_opt.value = new_opt.text = new_opt.title = pls_arr[i];
            _mydatalist.appendChild(new_opt);
        }
    }
    if (_first_select.value != 'select' && _second_select.value != 'select_category'){
        optChangeTop();
    }
}

function optValChange(){
	var x = document.getElementById("site").value.toLowerCase();
	var y = document.getElementById("opt").value.toLowerCase();
	var z = document.getElementById("opt_val").value;
	console.log(z)
    if (x == 'video' || x == 'music'){
        var new_url = 'site='+x+'&opt='+y+'&s='+z+'.hash'+'&exact.m3u';
    }else{
        var new_url = 'site='+x+'&opt='+y+'&s='+z+'&exact.m3u';
    }
    _current_working_m3u = new_url;
	var client = new getRequest();
	client.get(new_url, function(response) {
	//console.log(response);
	m = response.split('\n');
	r = document.getElementById('playlist')
	//console.log(m)
	while(r.firstChild){r.removeChild(r.firstChild);}
	var indx = 1;
	for(i=1;i<m.length-1;i+=2){
		var a = m[i].substring(10,500);
        a = a.trim();
        if (a.startsWith('-')){
            console.log('startswith -----');
            a = a.slice(1, 500);
            a = a.trim();
        }
		var b = m[i+1];
		var new_opt = document.createElement('li');
		new_opt.setAttribute('data-mp3',b);
		new_opt.setAttribute('data-num',indx.toString());
		new_opt.setAttribute('draggable','true');
		new_opt.setAttribute('ondragstart','drag_start(event)');
		new_opt.setAttribute('ondrop','on_drop(event)');
		new_opt.setAttribute('ondragover','drag_over(event)');
		new_opt.setAttribute('ondragend','drag_end(event)');
		new_opt.setAttribute('ondragenter','drag_enter(event)');
		new_opt.setAttribute('ondragleave','drag_leave(event)');
		new_opt.setAttribute('width','100%');
        new_opt.setAttribute('title', a);
        if (_show_thumbnails){
            img_div = add_thumbnail_to_playlist(a, b, 0);
            new_opt.appendChild(img_div);
        }else{
            img_div = add_thumbnail_to_playlist(a, b, 1);
            new_opt.appendChild(img_div);
        }
		r.appendChild(new_opt);
		indx += 1;
		}
	})
	//window.location.href = new_url;
	document.getElementById("type_search").value = ""; 
}


function optValChangeTop(){
	var x = _first_select.value.toLowerCase();
	var y = _second_select.value.toLowerCase();
	var z = _third_select.value;
	console.log(z)
    if (x == 'video' || x == 'music'){
        var new_url = 'site='+x+'&opt='+y+'&s='+z+'.hash'+'&exact.m3u';
    }else{
        var new_url = 'site='+x+'&opt='+y+'&s='+z+'&exact.m3u';
    }
    _current_working_m3u = new_url;
	var client = new getRequest();
	client.get(new_url, function(response) {
	m = response.split('\n');
	r = document.getElementById('playlist')
	while(r.firstChild){r.removeChild(r.firstChild);}
	var indx = 1;
	for(i=1;i<m.length-1;i+=2){
		var a = m[i].substring(10,500);
        a = a.trim();
        if (a.startsWith('-')){
            console.log('startswith -----');
            a = a.slice(1, 500);
            a = a.trim();
        }
		var b = m[i+1];
		var new_opt = document.createElement('li');
		new_opt.setAttribute('data-mp3',b);
		new_opt.setAttribute('data-num',indx.toString());
		new_opt.setAttribute('draggable','true');
		new_opt.setAttribute('ondragstart','drag_start(event)');
		new_opt.setAttribute('ondrop','on_drop(event)');
		new_opt.setAttribute('ondragover','drag_over(event)');
		new_opt.setAttribute('ondragend','drag_end(event)');
		new_opt.setAttribute('ondragenter','drag_enter(event)');
		new_opt.setAttribute('ondragleave','drag_leave(event)');
		new_opt.setAttribute('width','100%');
        new_opt.setAttribute('title', a);
        if (_show_thumbnails){
            img_div = add_thumbnail_to_playlist(a, b, 0);
            new_opt.appendChild(img_div);
        }else{
            img_div = add_thumbnail_to_playlist(a, b, 1);
            new_opt.appendChild(img_div);
        }
		r.appendChild(new_opt);
		indx += 1;
		}
	})
}

function get_subtitle(src){
	while(_player.firstChild){_player.removeChild(_player.firstChild);}
	var new_opt = document.createElement('track');
	new_opt.setAttribute('kind','captions');
	new_opt.setAttribute('label','English');
	new_opt.setAttribute('srclang','en');
	new_opt.setAttribute('src',src);
	new_opt.setAttribute('default','');
	_player.appendChild(new_opt);
	_player.textTracks[0].mode = 'showing';
}

function check_extension(url){
    var music_file_status = false;
    if (url.indexOf('abs_path=') >= 0){
        var base_dec = url.split('abs_path=')[1]
        if (base_dec.indexOf('/') >= 0){
            base_arr_index = base_dec.lastIndexOf('/');
            base_dec = base_dec.slice(0, base_arr_index);
        }
        if (base_dec.indexOf('&pl_id=') >= 0){
            base_dec = url.split('&pl_id=')[0];
        }
        base_dec = atob(base_dec)
        if ((base_dec.endsWith('.mp3') || base_dec.endsWith('.flac'))){
           music_file_status = true
           var preloadLink = document.createElement("link");
            preloadLink.href = url;
            preloadLink.rel = "preload";
            preloadLink.as = "audio";
            preloadLink.type = "audio/mpeg";
            document.head.appendChild(preloadLink);
            console.log('--preloading-------');
        }
    }
    return music_file_status;
}

function playlistItemClick(clickedElement,mode) {
    if (mode != 'queue' && mode != 'queue_context'){
        var selected = _playlist.querySelector(".selected");
        console.log(mode)
        if (selected) {
            selected.classList.remove("selected");
        }
        clickedElement.classList.add("selected");
    }
	var new_src = clickedElement.getAttribute("data-mp3");
	_final_url = new_src;
	_final_name = clickedElement.innerHTML;
    _clicked_element = clickedElement;
	_clicked_num = clickedElement.getAttribute("data-num");
	var tmp_name = clickedElement.innerHTML;
    
    var win_width = window.innerWidth;
    document.title = _clicked_num+" "+clickedElement.title;
    _player_control_info.innerHTML = document.title;
    _player_control_image.src = _final_url + '.image'
    _player.poster = _final_url + '.image'
    //_img_id.src = "";
    //_img_info.innerHTML = "";
    if (_show_thumbnails){
        if (win_width <= 640){
            _title.innerHTML = document.title;
            _title.style.textAlign = 'center';
        }else{
            _title.innerHTML = tmp_name;
            _title.style.textAlign = 'left';
        }
    }else{
        _title.innerHTML = document.title;
        _title.style.textAlign = 'left';
    }
    //console.log(_title.style.textAlign);
	_clicked_index = parseInt(_clicked_num);
    if (_remote.innerHTML == 'R:Off'){
		_player.src = new_src;
		if (_subtitle_status == 'on'){
			get_subtitle(new_src+".subtitle");
		}
		_player.play();
        if(!_player_progress_status || _player_progress_status == null){
            _player_progress_status = setInterval(update_progress_bar, 1000);
        }else{
            clearInterval(_player_progress_status);
            _player_progress_status = setInterval(update_progress_bar, 1000);
        }
        if(win_width <= 640){
            new_width = (win_width-30).toString();
            _player.width = new_width.toString();
            _video_section.style.width = new_width + 'px';
            //_buttons_div.style.width = new_width+ 'px';
            _player.height=parseInt((1/_aspect_ratio)*new_width).toString();
            
            console.log(screen.width);
            console.log(win_width);
            
        }
	}
	else{
		
		if (mode == 'nextplay' || mode == 'playlist'){
		new_indx = 'playlist_'+(_clicked_index-1).toString();
		var client = new getRequest();
			client.get(new_indx, function(response) {
			console.log(response);
			})
		
		}else if (mode == 'next' || mode == 'prev'){
			var client = new getRequest();
			if (mode == 'next'){
			client.get('playnext', function(response) {
			console.log(response);
			r = response.split(':')[1];
			gotoChildNode(r);
			})
			}else if (mode == 'prev'){
				client.get('playprev', function(response) {
				console.log(response);
				r = response.split(':')[1];
				gotoChildNode(r);
			})
			} 
		}
		_player.src = new_src
		console.log(new_src)
        if (!_remote_control_status || _remote_control_status==null){
            _remote_control_status = setInterval(remote_control_update, 1000);
        }
	}
	
	if (_first_select.value.toLowerCase() == 'torrent'){
		if(!_get_torrent_status || _get_torrent_status == null){
			torrent_status('status');
			_get_torrent_status = setInterval(torrent_status,5000);
		}
		else{
			console.log('Already updating');
		}
	}
	
    if (mode == 'queue'){
        _playlist_custom.removeChild(clickedElement);
    }
    
    
}

function playNext() {
    var playlist = _only_playlist.value;
    var select_pls = false;
    console.log('--playNext--')
    console.log(playlist)
    if(playlist == 'select_existing_playlist' || playlist == 'Queue' || _pls_custom.hidden){
		select_pls = true;
	}
    console.log(select_pls)
    var queue = false;
    if (select_pls){
        var pls_custom_child = _playlist_custom.firstChild;
        if (pls_custom_child){
            playlistItemClick(pls_custom_child, 'queue');
            queue = true;
        }
    }
    if (!queue){
        console.log(_player.loop,'----------1039------playNext--')
        var selected = _playlist.querySelector("li.selected");
        if (_remote_val == 'on'){_clicked_index = _clicked_index + 1}
        if (selected && selected.nextSibling) {
            if (_loop.innerHTML == '\u21BA'){
                playlistItemClick(selected,'nextplay');
            }
            else{
                playlistItemClick(selected.nextSibling,'nextplay');
            }
        }
        else{
            var first = _playlist.firstChild;
            console.log(first);
            playlistItemClick(first,'nextplay');
        }
    }
}

_shuffle.addEventListener("click", function () {
    if (_current_working_m3u.startsWith('site')){
        var new_url = _current_working_m3u.replace('.m3u', '')+'&shuffle.m3u';
    }else{
        new_url = 'stream_shuffle.m3u';
    }
	var client = new getRequest();
	client.get(new_url, function(response) {
	console.log(response);
	
	m = response.split('\n');
	r = document.getElementById('playlist')
	console.log(m)
	while(r.firstChild){r.removeChild(r.firstChild);}
	var indx = 1;
	for(i=1;i<m.length-1;i+=2){
		var a = m[i].substring(10,100);
        a = a.trim();
        if (a.startsWith('-')){
            a = a.slice(1, 500);
            a = a.trim();
        }
		var b = m[i+1];
		var new_opt = document.createElement('li');
		new_opt.setAttribute('data-mp3',b);
		new_opt.setAttribute('data-num',indx.toString());
		new_opt.setAttribute('draggable','true');
		new_opt.setAttribute('ondragstart','drag_start(event)');
		new_opt.setAttribute('ondrop','on_drop(event)');
		new_opt.setAttribute('ondragover','drag_over(event)');
		new_opt.setAttribute('ondragend','drag_end(event)');
		new_opt.setAttribute('ondragenter','drag_enter(event)');
		new_opt.setAttribute('ondragleave','drag_leave(event)');
        new_opt.setAttribute('title', a);
        if (_show_thumbnails){
            img_div = add_thumbnail_to_playlist(a, b, 0);
        }else{
            img_div = add_thumbnail_to_playlist(a, b, 1);
        }
        new_opt.appendChild(img_div);
		r.appendChild(new_opt);
		indx += 1;
		}
	})
	
	
});

function populate_playlist_only(response, mode){
    //console.log(response);
    if (mode == 0){
        m = response.split('\n');
    }else if (mode == 1){
        m = response
    }
	r = document.getElementById('playlist')
	//console.log(m)
	while(r.firstChild){r.removeChild(r.firstChild);}
	var indx = 1;
	for(i=1;i<m.length-1;i+=2){
		var a = m[i].substring(10,500);
        a = a.trim();
        if (a.startsWith('-')){
            console.log('startswith -----');
            a = a.slice(1, 500);
            a = a.trim();
        }
		var b = m[i+1];
		var new_opt = document.createElement('li');
		new_opt.setAttribute('data-mp3',b);
		new_opt.setAttribute('data-num',indx.toString());
		new_opt.setAttribute('draggable','true');
		new_opt.setAttribute('ondragstart','drag_start(event)');
		new_opt.setAttribute('ondrop','on_drop(event)');
		new_opt.setAttribute('ondragover','drag_over(event)');
		new_opt.setAttribute('ondragend','drag_end(event)');
		new_opt.setAttribute('ondragenter','drag_enter(event)');
		new_opt.setAttribute('ondragleave','drag_leave(event)');
        new_opt.setAttribute('title', a);
        if (_show_thumbnails){
            img_div = add_thumbnail_to_playlist(a, b, 0);
        }else{
            img_div = add_thumbnail_to_playlist(a, b, 1);
        }
        new_opt.appendChild(img_div);
		r.appendChild(new_opt);
		indx += 1;
		}
}

function populate_playlist(new_url){
	var client = new getRequest();
	client.get(new_url, function(response) {
        populate_playlist_only(response, 0);
	})
}
function toggle_master_slave(){
    var client = new getRequest();
	client.get('toggle_master_slave', function(response) {
        var txt = response.toLowerCase();
        console.log(txt);
        if (txt == 'master'){
            _toggle_master.innerHTML = 'Master';
        }else if (txt == 'slave'){
            _toggle_master.innerHTML = 'Slave';
        }
	})
}
_m3u.addEventListener("click", function () {
	/*
    if (_current_working_m3u.startsWith('site')){
        var new_url = _current_working_m3u;
    }else{
        new_url = 'stream_continue.m3u';
    }
    window.location.href = new_url;*/
    first = _playlist.firstChild;
    var new_url = "get_playlist_in_m3u";
    dict = {};
    while(first){
        num = first.getAttribute('data-num');
        data = first.getAttribute('data-mp3');
        title = first.title;
        dict[num] = {'title':title,'data':data};
        first = first.nextSibling;
    }
    var client = new postRequest();
        client.post(new_url,dict,function(response) {
            window.location.href = response;
    })
});

_remote.addEventListener("click", function () {
	
	var old_var= _remote.innerHTML;
    if (old_var == 'R:Off'){
            if (_player_progress_status){
                clearInterval(_player_progress_status);
                _player_progress_status = null;
            }
            if (!_remote_control_status || _remote_control_status==null){
                _remote_control_status = setInterval(remote_control_update, 1000);
            }
			var client = new getRequest();
			client.get('remote_on.htm', function(response) {
			console.log(response);
            if (response.toLowerCase() == 'remote control set true'){
                _remote.innerHTML = 'R:On';
                _remote_val = 'on'
                _remote_control_buttons.style.display = "block";
                _remote_control_buttons.style.visibility = "visible";
                _title.innerHTML = "Remote control enabled. Refresh the playlist";
            }else{
                _title.innerHTML = "Remote control is not enabled on server. First enable this feature on server";
            }
	})
		}
	else {
		_remote.innerHTML = 'R:Off';
		_remote_val = 'off';
        if (_remote_control_status){
            clearInterval(_remote_control_status);
            _remote_control_status = null;
        }
        if(!_player_progress_status || _player_progress_status == null){
        _player_progress_status = setInterval(update_progress_bar, 1000);
        }
        //_can_play_sync = false;
		var client = new getRequest();
			client.get('remote_off.htm', function(response) {
			console.log(response);
            _remote_control_buttons.style.visibility = "hidden";
            _remote_control_buttons.style.display = "none";
            _title.innerHTML = "Remote control disabled.";
            
	})
	}
});

/*_home.addEventListener("click", function () {
    window.location.href = 'stream_continue.htm';
});*/

_logout.addEventListener("click", function () {
    window.location.href = 'logout';
});

function stop_on_click(){
    _can_play_sync = false;
	if (_remote_val == 'off'){
        _player.pause();
        _player.src = "";
        if (_player_progress_status){
            clearInterval(_player_progress_status);
            _player_progress_status = null;
            _player_progress.value = 0;
            _player_start_time.innerHTML = "00:00:00";
        }
    }else{
    var client = new getRequest();
		client.get('playerstop', function(response) {
			console.log(response);
            if (_remote_control_status){
                clearInterval(_remote_control_status);
                _remote_control_status = null;
            }
	})
    
	}
}

_seek_10.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek10', function(response) {
	console.log(response);
	})}
});

_seek_10_.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek_10', function(response) {
	console.log(response);
	})}
});

_seek_60.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek60', function(response) {
	console.log(response);
	})}
});

_seek_60_.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek_60', function(response) {
	console.log(response);
	})}
});

_seek_5m.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek5m', function(response) {
	console.log(response);
	})}
});

_seek_5m_.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('seek_5m', function(response) {
	console.log(response);
	})}
});


_vol_5.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('volume5', function(response) {
	console.log(response);
	})}
});

_vol_5_.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('volume_5', function(response) {
	console.log(response);
	})}
});

_fullscreen.addEventListener("click", function () {
	if (_remote_val == 'on'){
	var client = new getRequest();
	client.get('fullscreen', function(response) {
	console.log(response);
	})}
});

function prev_on_click(){
	var selected = _playlist.querySelector("li.selected");
	if (_remote_val == 'on'){_clicked_index = _clicked_index - 1}
    if (selected && selected.previousSibling) {
		playlistItemClick(selected.previousSibling,'prev');
		//_title.innerHTML = selected.previousSibling.innerHTML;
    }
    
}

function get_next_playlist(){
    var client = new getRequest();
	client.get('get_next_playlist', function(response) {
    populate_playlist_only(response, 0);
	})
}

function get_last_playlist(){
    var client = new getRequest();
	client.get('get_last_playlist', function(response) {
    populate_playlist_only(response, 0);
	})
}

function play_last_item_from_playlist(){
    var client = new getRequest();
	client.get('play_last_item_0', function(response) {
        console.log(response);
	})
}

function get_first_playlist(){
    var client = new getRequest();
	client.get('get_first_playlist', function(response) {
    populate_playlist_only(response, 0);
	})
}

function get_previous_playlist(){
    console.log('get_previous')
    var client = new getRequest();
	client.get('get_previous_playlist', function(response) {
    populate_playlist_only(response, 0);
	})
}

function next_on_click(){
	var selected = _playlist.querySelector("li.selected");
	if (_remote_val == 'on'){_clicked_index = _clicked_index + 1;}
    if (selected && selected.nextSibling) {
			playlistItemClick(selected.nextSibling,'next');
			//_title.innerHTML = selected.nextSibling.innerHTML;
		} else {
		var first = _playlist.firstChild;
		console.log('----next---');
		console.log(first);
		console.log('----next---');
		playlistItemClick(first,'next');
		//_title.innerHTML = first.innerHTML;
	}
	
}

function play_on_click(){
	var selected = _playlist.querySelector("li.selected");
    
    if (_remote_val == 'on'){
		var client = new getRequest();
		client.get('playpause', function(response) {
			console.log(response);
			r = response.split(':')[1];
			gotoChildNode(r);
	})
	}else{
		if (_player.readyState == 4){
			if (_player.paused){_player.play();}
			else{_player.pause()}
		} else {
			if (selected){playlistItemClick(selected,'play');}
			else{
			var first = _playlist.firstChild;
			console.log(first);
			playlistItemClick(first,'play');
			//_title.innerHTML = first.innerHTML;
			}
			}
		}
}


function gotoChildNode(num){
	var selected = _playlist.querySelector(".selected");
	if (!selected){
		selected = _playlist.firstChild;
	}
	var _data_num_cur = selected.getAttribute('data-num');
	var new_num = (parseInt(num)+1).toString();
	var _next = "";
	var _prev = "";
	if (parseInt(new_num) > parseInt(_data_num_cur)){
		_next = "next";
	}else if (parseInt(new_num) < parseInt(_data_num_cur)) {
		_prev = "prev";
		}
	console.log(new_num,_data_num_cur);
	if(_next || _prev){
		console.log(">>");
		var _pls = selected;
		_data_num = _pls.getAttribute('data-num');
		while((_data_num != new_num) && (_pls != null)){
				if (_next){
					_pls = _pls.nextSibling;
					console.log(">");
				}else if(_prev){
					_pls = _pls.previousSibling;
					console.log("<");
				}
				_data_num = _pls.getAttribute('data-num');
				
		}
		_title.innerHTML = _data_num+' '+ _pls.innerHTML;
		if (selected) {
			selected.classList.remove("selected");
		}
		_pls.classList.add("selected");
	}
}

function start_loop(mode){
    var old_var= _loop.innerHTML;
    if (old_var == 'Lock'){
			_loop.innerHTML = _btn_minimize.innerHTML = '\u21BA';
			_player.loop = "loop";
		}
	else {
		_loop.innerHTML = 'Lock';
		_player.loop = "";
        _btn_minimize.innerHTML = '--';
	}
	if (_remote_val == 'on'){
		var client = new getRequest();
		client.get('lock', function(response) {
			console.log(response);
		// do something with response
	})
	}
}

_opt_ok.addEventListener("click", function () {
  optChange();
  document.getElementById("type_search").value = "";  
});

function hide_alternate_menu_buttons(){
	if (_hide_options){
        _hide_options = false;
        _selection_site.style.display="grid";
		_display_option.style.display="grid";
		//_selection_site.style.visibility="visible";
		//_display_option.style.visibility="visible";
        //_selection_site.hidden = "";
        //_display_option.hidden = "";
        }
        
	else{
        _hide_options = true;
        _selection_site.style.display="none";
		_display_option.style.display="none";
		//_selection_site.style.visibility="hidden";
		//_display_option.style.visibility="hidden";
        //_selection_site.hidden = "hidden";
        //_display_option.hidden = "hidden";
		}
}

_opt_val_ok.addEventListener("click", function () {
  optValChange();
  
});

function create_playlist_select_options(response, mode){
    if (mode == 0){
        var w = response.split('\n');
    }else if (mode == 1){
        var w = response;
    }
    w.sort()
    console.log(w);
    req = document.getElementById("only_playlist");
    old_pls = ''
    if (req){
        old_pls = req.value;
    }
    req.innerHTML = '';
    for(i=0;i<w.length;i++){
        if (i == 0){
            var new_opt = document.createElement("option");
            new_opt.text = 'Select Existing Playlist';
            new_opt.value = 'select_existing_playlist';
            req.appendChild(new_opt);
        }
        k = w[i];
        var new_opt = document.createElement("option");
        new_opt.text = k.substring(0,45);
        new_opt.value = k;
        req.appendChild(new_opt);
    }
    if (old_pls){
        req.value = old_pls;
    }
}

_custom_pls.addEventListener("click", function () {
	if(_pls_custom.hidden){
		
		var client = new getRequest();
		client.get('get_all_playlist', function(response) {
			create_playlist_select_options(response, 0);
		})
		_pls_custom.hidden = "";
	} 
	else{
		_pls_custom.hidden = "hidden";
	}
  
});

function _clear_pls_button(){
    r = document.getElementById('playlist_custom')
    while(r.firstChild){r.removeChild(r.firstChild);}
}

window.onscroll = function () {
    if (pageYOffset >= 200) {
        if (_minimize_control_bar){
            document.getElementById('player_control_progress').style.visibility = "hidden";
            document.getElementById("btn_maximize").style.visibility = "visible";
            document.getElementById("btn_to_top").style.visibility = "visible";
        }else{
            document.getElementById('player_control_progress').style.visibility = "visible";
            document.getElementById("btn_maximize").style.visibility = "hidden";
            document.getElementById("btn_to_top").style.visibility = "hidden";
        }
        if (_hide_top_bar){
            _top_menu_bar.style.display = 'none';
        }
    }else{
        //document.getElementById("btn_to_top").style.visibility = "hidden";
        //document.getElementById("btn_maximize").style.visibility = "hidden";
        //document.getElementById('player_control_progress').style.visibility = "hidden";
        if (_hide_top_bar){
            _top_menu_bar.style.display = 'none';
            }
        }
};

function back_to_top(){
    _top_xy = [window.pageXOffset, window.pageYOffset];    
    window.scrollTo(0, 0);
}


function playback_started(){
    if(_remote_val == 'off'){
        _can_play_sync = false;
    }else{
        _can_play_sync = true;
        var client = new getRequest();
		client.get('playpause_play', function(response) {
        console.log(response);
        })
        _player.play();
        
    }
}

function player_can_play(){
    if (_remote_val == 'on' && _can_play_sync){
        var client = new getRequest();
		client.get('playpause_play', function(response) {
        console.log(response);
        })
        _player.play();
    }
}

function playNext_decide(){
    if (_remote_val == 'off'){
        playNext();
    }
}

window.addEventListener("resize", resizeWindowEvent);
_player.addEventListener("ended", playNext_decide);
_player.addEventListener("playing", playback_started);
_player.addEventListener("canplaythrough", player_can_play);
_playlist.addEventListener("click", function (e) {
    var target = e.target;
    var req_node = get_clicked_node(target);
    
    if (req_node) {
        _top_xy = [window.pageXOffset, window.pageYOffset];
        if (_remote_val == 'on'){
            var child = req_node;
		}
        if( !_pls_custom.hidden){
            click_to_add_to_playlist(req_node)
        }else{
            playlistItemClick(req_node,'playlist');
        }
    }
});

_player_progress.addEventListener("click", function(e){
    val = _player_progress.getBoundingClientRect();
    console.log(val);
    x = val['x'];
    w = val['width'];
    console.log(x, w)
    var time_diff = 0;
    if (_player.duration){
        new_val = parseInt(((e.pageX - x)/w)*_player.duration);
        _player.currentTime = new_val;
        _player_progress.value = new_val;
        console.log(new_val);
    }
    
    
    if (_remote_val == 'on'){
        new_val = (((e.pageX - x)/w)*100).toFixed(2);
        var seek_val = "seek_abs_"+new_val.toString();
        console.log(seek_val);
		var client = new getRequest();
		client.get(seek_val, function(response) {
			console.log(response);
            response = response.replace('seek ', '');
            seek_val = parseInt(response.split('/')[0]);
            seek_total = parseInt(response.split('/')[1]);
            _player_progress.value = seek_val;
            _player_progress.max = seek_total;
            seek_start = human_readable_time(seek_val);
            seek_end = human_readable_time(seek_total);
            _player_start_time.innerHTML = seek_start + '/' + seek_end;
            //_player_progress.title = seek_start;
		// do something with response
	})
	}
});

_player_progress.addEventListener("mousemove", function(e){
    val = _player_progress.getBoundingClientRect();
    //console.log(val);
    x = val['x'];
    w = val['width'];
    //console.log(x, w)
    var time_diff = 0;
    if (_player.duration){
        new_val = parseInt(((e.pageX - x)/w)*_player.duration);
        _player_progress.title = human_readable_time(new_val);
        //console.log(new_val);
    }
    
    
    if (_remote_val == 'on' && !_player.duration){
        new_val = parseInt(((e.pageX - x)/w)*parseInt(_player_progress.max));
        _player_progress.title = human_readable_time(new_val);
	}
});


function get_clicked_node(target){
    var req_node = target;
    console.log(target);
    console.log(target.parentNode);
    if (target && (target.nodeName == "IMG" || target.nodeName == "DIV")){
        req_node = target.parentNode;
        if (req_node.nodeName == "IMG" || req_node.nodeName == "DIV"){
            req_node = req_node.parentNode;
        }
    }else if (target && target.nodeName == "LI"){
        req_node = target;
    }
    
    if (req_node.nodeName != "LI"){
        req_node = null;
    }
    
    return req_node;
}

_playlist.addEventListener("contextmenu", function (e) {
    var target = e.target;
    var req_node = get_clicked_node(target);
    
    if (req_node) {
		_playlist_selected_element = req_node;
        e.preventDefault();
        var ctxMenu = document.getElementById('context-menu-bar');
        ctxMenu.style.display = "block";
        ctxMenu.style.left = (e.pageX - 10)+"px";
        ctxMenu.style.top = (e.pageY - 10)+"px";
        last_position_scrollbar = e.pageY;
        _top_xy = [window.pageXOffset, window.pageYOffset];
        _old_playlist_selected_color = _playlist_selected_element.style.backgroundColor
        _playlist_selected_element.style.backgroundColor = '#dcdcdc';
        
    }
});

_playlist_custom.addEventListener("contextmenu", function (e) {
    var target = e.target;
    var req_node = get_clicked_node(target);
    
    if (req_node) {
		_queue_selected_element = req_node;
        e.preventDefault();
        var ctxMenu = document.getElementById('context-menu-bar-custom');
        ctxMenu.style.display = "block";
        ctxMenu.style.left = (e.pageX - 10)+"px";
        ctxMenu.style.top = (e.pageY - 10)+"px";
        _top_xy = [window.pageXOffset, window.pageYOffset];
        _old_queue_selected_color = _queue_selected_element.style.backgroundColor
        _queue_selected_element.style.backgroundColor = '#dcdcdc';
        
    }
});

/*_player.addEventListener('mouseover', function(e){
    console.log('hover');
    _player.controls = true;
});

_player.addEventListener('mouseout', function(e){
    console.log('hover');
    _player.controls = false;
});*/

var getRequest = function() {
    this.get = function(url, callbak) {
        var http_req = new XMLHttpRequest();
        http_req.onreadystatechange = function() { 
            if (http_req.readyState == 4 && http_req.status == 200)
                {callbak(http_req.responseText);}
        }

        http_req.open( "GET", url, true );            
        http_req.send( null );
    }
};

var postRequest = function() {
    this.post = function(url, params,callbak) {
        var http_req = new XMLHttpRequest();
        http_req.onreadystatechange = function() { 
            if (http_req.readyState == 4 && http_req.status == 200)
                {callbak(http_req.responseText);}
        }
		//http_req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        http_req.open( "POST", url, true );            
        http_req.send(JSON.stringify(params));
    }
};

function resizeWindowEvent(){
	w = window.innerWidth;
    h = window.innerHeight;
	if(w <= 640){
        _player.width=(w-30).toString();
        _video_section.style.width = _player.width + 'px';
        _buttons_div.style.width = _player.width+ 'px';
        _player.height=parseInt((1/_aspect_ratio)*w).toString();
		console.log(screen.width);
        console.log(_player.width);
        if (_show_thumbnails){
            add_remove_image_node_to_playlist();
        }
    }else {
        var new_width = w - 30;
        if (new_width > 1000){
            new_width = new_width*0.6;
        } 
        _player.width = new_width.toString();
        _video_section.style.width = new_width + 'px';
        _buttons_div.style.width = new_width+ 'px';
        _player.height=parseInt((1/_aspect_ratio)*new_width).toString();
        if (_show_thumbnails){
            add_remove_image_node_to_playlist();
        }
    }
    top_bar_change_layout();
}

onDocReady();
