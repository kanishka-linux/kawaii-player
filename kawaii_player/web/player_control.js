// || PLAYER CONTROL PAGE JAVASCRIPT

// ===========================
// CONFIGURATION
// ===========================
const CONFIG = {
    BASE_URL: window.location.origin,
    SYNC_INTERVAL: 1000, // 1 second for master/slave mode
    AUTO_HIDE_ALERT: 2000 // 2 seconds
};

// ===========================
// STATE MANAGEMENT
// ===========================
const state = {
    mode: 'in-browser', // 'in-browser', 'master', or 'slave'
    seriesId: null,
    currentEpisode: null,
    episodes: [],
    seriesInfo: null,
    playing: false,
    currentTime: 0,
    duration: 0,
    volume: 75,
    syncInterval: null,
    previousIndex: -1,
    loop: false,
    firstPlay: true,
    subtitleBlobUrls: [],
    loadedAudioTracks: [],
    currentAudioElement: null,
    transcodeJob: null,
    transcodeStatusInterval: null
};

// ===========================
// UTILITY FUNCTIONS
// ===========================

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    
    const icons = {
        info: 'ℹ️',
        success: '✓',
        warning: '⚠️',
        error: '✗'
    };
    
    alert.innerHTML = `
        <span class="alert-icon">${icons[type]}</span>
        <span class="alert-message">${message}</span>
        <button class="alert-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.remove();
    }, CONFIG.AUTO_HIDE_ALERT);
}

/**
 * Format time in MM:SS or HH:MM:SS
 */
function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get URL parameters
 */
function getURLParams() {
    const params = new URLSearchParams(window.location.search);
    
    // Extract series ID from URL path: /series/{seriesId}/playercontrol
    
    const pathMatch = window.location.pathname.match(/\/series\/([^\/]+)/);
    if (pathMatch) {
        seriesId = pathMatch[1];
    }
    
    return {
        seriesId: seriesId,
        episodeNumber: parseInt(params.get('ep') || params.get('episode') || '1'),
        mode: params.get('mode') || 'in-browser'
    };
}

/**
 * Update URL without reloading page
 */
function updateURL(seriesId, episodeNumber, mode) {
    const url = new URL(window.location);
    url.searchParams.set('series', seriesId);
    url.searchParams.set('ep', episodeNumber);
    url.searchParams.set('mode', mode);
    window.history.pushState({}, '', url);
}

// ===========================
// API FUNCTIONS
// ===========================

/**
 * Fetch series details
 */
/**
 * Fetch series details
 */
async function fetchSeriesDetails(seriesId) {
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/title-details/${seriesId}`);
        if (!response.ok) throw new Error('Failed to fetch series details');
        const data = await response.json();
        
        // Transform API response to match our expected format
        const transformedData = {
            title: data.title || data.series_info?.title || 'Unknown Series',
            dir_hash: data.dir_hash,
            english_title: data.series_info?.english_title,
            poster: data.series_info?.image_poster_large,
            score: data.series_info?.score,
            year: data.series_info?.year,
            directory: data.series_info?.directory,
            genres: data.series_info?.genres ? data.series_info.genres.split(',').map(g => g.trim()) : [],
            summary: data.series_info?.summary || '',
            category: data.series_info?.category,
            episodes: (data.episodes || []).map((ep, index) => ({
                number: index + 1,
                name: ep.name || `Episode ${index + 1}`,
                path: ep.url,
                actual_path: ep['path'],
                thumbnail: ep['image-url'],
                description: '',
                duration: '',
                watched: false,
                epn_number: ep['epn-number']
            }))
        };
        
        return transformedData;
    } catch (error) {
        console.error('Error fetching series details:', error);
        showAlert('Failed to load series details', 'error');
        return null;
    }
}

/**
 * Get remote control status (for master/slave mode)
 */
async function getRemoteControlStatus() {
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/get_remote_control_status`);
        if (!response.ok) throw new Error('Failed to get remote status');
        const text = await response.text();
        
        // Parse response: total::current_time::index::queue_list::title::backend::queueChanged
        const parts = text.split('::');
        return {
            total: parseFloat(parts[0]) || 0,
            currentTime: parseFloat(parts[1]) || 0,
            index: parseInt(parts[2]) || 0,
            queueList: parts[3] || '',
            title: parts[4] || '',
            backend: parts[5] || 'libmpv',
            queueChanged: parts[6] === 'true'
        };
    } catch (error) {
        console.error('Error getting remote status:', error);
        return null;
    }
}

/**
 * Send remote command
 */
async function sendRemoteCommand(endpoint) {
    try {
        const response = await fetch(`${CONFIG.BASE_URL}${endpoint}`);
        return response.ok;
    } catch (error) {
        console.error('Error sending remote command:', error);
        showAlert('Failed to send command', 'error');
        return false;
    }
}

/**
 * Send POST command
 */
async function sendPostCommand(endpoint, data) {
    try {
        const response = await fetch(`${CONFIG.BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.ok;
    } catch (error) {
        console.error('Error sending POST command:', error);
        showAlert('Failed to send command', 'error');
        return false;
    }
}

// ===========================
// THEME MANAGEMENT
// ===========================

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light';
    } else {
        document.documentElement.removeAttribute('data-theme');
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark';
    }
}

function toggleTheme() {
    const html = document.documentElement;
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    const currentTheme = html.getAttribute('data-theme');
    
    if (currentTheme === 'dark') {
        html.removeAttribute('data-theme');
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark';
        localStorage.setItem('theme', 'light');
    } else {
        html.setAttribute('data-theme', 'dark');
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light';
        localStorage.setItem('theme', 'dark');
    }
}

function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ===========================
// MODE MANAGEMENT
// ===========================
async function switchMode(newMode) {
    console.log('Switching to mode:', newMode);
    
    state.mode = newMode;
    document.body.setAttribute('data-mode', newMode);
    
    // Update active mode button
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-mode') === newMode) {
            btn.classList.add('active');
        }
    });
    
    // Show/hide appropriate UI elements
    const videoPlayerContainer = document.getElementById('videoPlayerContainer');
    const thumbnailArea = document.getElementById('thumbnailArea');
    const connectionStatus = document.getElementById('connectionStatus');
    const inBrowserControls = document.querySelectorAll('.in-browser-only');
    const masterSlaveControls = document.querySelectorAll('.master-slave-only');
    
    if (newMode === 'in-browser') {
        const response = await fetch(`${CONFIG.BASE_URL}/remote_off.htm`);
        videoPlayerContainer.classList.remove('hidden');
        thumbnailArea.classList.add('hidden');
        connectionStatus.classList.add('hidden');
        inBrowserControls.forEach(el => el.classList.remove('hidden'));
        masterSlaveControls.forEach(el => el.classList.add('hidden'));
        
        stopRemoteSync();
        initBrowserPlayer();
    } else {
        const response = await fetch(`${CONFIG.BASE_URL}/remote_on.htm`);
        videoPlayerContainer.classList.add('hidden');
        thumbnailArea.classList.remove('hidden');
        connectionStatus.classList.remove('hidden');
        inBrowserControls.forEach(el => el.classList.add('hidden'));
        masterSlaveControls.forEach(el => el.classList.remove('hidden'));
        
        stopBrowserPlayer();
        startRemoteSync();

        console.log(state.seriesInfo, state.seriesInfo.directory)

        const playlistUrl = `/site=video&opt=available&s=${state.seriesInfo.dir_hash}&exact.m3u`;
        await fetch(`${CONFIG.BASE_URL}${playlistUrl}`);
        console.log('Playlist loaded:', playlistUrl);
        
        const response1 = await fetch(`${CONFIG.BASE_URL}/toggle_master_slave`);
        const text = await response1.text();
        const actualMode = text.toLowerCase().trim();
        // Update status text based on mode
        const statusText = document.getElementById('statusText');
        if (newMode === 'master' && actualMode == "master") {
            statusText.textContent = '🖥️ Desktop Player Connected (Master Mode)';
        } else if (newMode === 'slave' && actualMode == "slave"){
            statusText.textContent = '📺 Desktop Player Connected (Slave Mode)';
        } else {
            console.log('📺 Mismatch', newMode, actualMode, "toggling again");
            const response2 = await fetch(`${CONFIG.BASE_URL}/toggle_master_slave`);
            const text2 = await response2.text();
            const actualMode2 = text2.toLowerCase().trim();
            statusText.textContent = `🖥️ Desktop Player Connected (${capitalizeFirstLetter(actualMode2)} Mode)`;
        }
    }
    
    if (state.seriesId && state.currentEpisode) {
        //updateURL(state.seriesId, state.currentEpisode.number, newMode);
    }
    
    const modeText = newMode === 'in-browser' ? 'In Browser' : 
                     newMode === 'master' ? 'Master' : 'Slave';
    //showAlert(`Switched to ${modeText} mode`, 'success');
}


// ===========================
// BROWSER PLAYER MANAGEMENT
// ===========================

function initBrowserPlayer() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (!videoPlayer || !state.currentEpisode) return;
    
    // Set video source
    const videoSource = document.getElementById('videoSource');
    const videoPath = state.currentEpisode.path || '';
    videoSource.src = videoPath;
    videoPlayer.load();
    
    // Add event listeners
    videoPlayer.addEventListener('timeupdate', updateProgress);
    videoPlayer.addEventListener('loadedmetadata', () => {
        state.duration = videoPlayer.duration;
        document.getElementById('totalTime').textContent = formatTime(state.duration);
    });
    videoPlayer.addEventListener('play', () => {
        state.playing = true;
        updatePlayPauseButton();
    });
    videoPlayer.addEventListener('pause', () => {
        state.playing = false;
        updatePlayPauseButton();
    });
}

function stopBrowserPlayer() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (videoPlayer) {
        videoPlayer.pause();
        videoPlayer.removeEventListener('timeupdate', updateProgress);
    }
}

function loadTranscodedVideo(url, keepProgressUI = false) {
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSource = document.getElementById('videoSource');
    
    const currentTime = videoPlayer.currentTime;
    const wasPlaying = !videoPlayer.paused;
    
    // Switch to transcoded URL
    videoSource.src = `${CONFIG.BASE_URL}${url}`;
    videoPlayer.load();
    
    // Restore playback position
    videoPlayer.addEventListener('loadedmetadata', function onLoaded() {
        videoPlayer.currentTime = currentTime;
        if (wasPlaying) {
            videoPlayer.play();
        }
        videoPlayer.removeEventListener('loadedmetadata', onLoaded);
    });
    
    // Only reset UI if transcode is complete
    if (!keepProgressUI) {
        const transcodeBtn = document.getElementById('transcodeBtn');
        const cancelBtn = document.getElementById('cancelTranscodeBtn');
        const progressDiv = document.getElementById('transcodeProgress');
        
        transcodeBtn.disabled = false;
        cancelBtn.style.display = 'none';
        progressDiv.style.display = 'none';
        
        state.transcodeJob = null;
        clearTranscodeJob();
    }
}

function saveTranscodeJob() {
    if (state.transcodeJob) {
        localStorage.setItem('transcodeJob', JSON.stringify({
            ...state.transcodeJob,
            seriesId: state.seriesId,
            episodeNumber: state.currentEpisode.number
        }));
    }
}

function clearTranscodeJob() {
    localStorage.removeItem('transcodeJob');
}

function loadTranscodeJob() {
    const saved = localStorage.getItem('transcodeJob');
    if (!saved) return null;
    
    try {
        return JSON.parse(saved);
    } catch {
        return null;
    }
}

function updateProgress() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (!videoPlayer) return;
    
    state.currentTime = videoPlayer.currentTime;
    state.duration = videoPlayer.duration;
    
    const progressFill = document.getElementById('progressFill');
    const currentTimeEl = document.getElementById('currentTime');
    
    const percentage = (state.currentTime / state.duration) * 100;
    progressFill.style.width = `${percentage}%`;
    currentTimeEl.textContent = formatTime(state.currentTime);
}

// ===========================
// REMOTE SYNC (MASTER/SLAVE)
// ===========================

function startRemoteSync() {
    if (state.syncInterval) {
        clearInterval(state.syncInterval);
    }
    
    state.syncInterval = setInterval(async () => {
        const status = await getRemoteControlStatus();
        if (status) {
            updateRemoteStatus(status);
        }
    }, CONFIG.SYNC_INTERVAL);
    
    // Initial fetch
    getRemoteControlStatus().then(status => {
        if (status) updateRemoteStatus(status);
    });
}

function stopRemoteSync() {
    if (state.syncInterval) {
        clearInterval(state.syncInterval);
        state.syncInterval = null;
        statusDetail.textContent = `• Sync stopped`;
    }
}

function updateRemoteStatus(status) {
    state.currentTime = status.currentTime;
    state.duration = status.total;
    
    // Check if episode changed (index is 1-based from remote)
    if (status.index !== state.previousIndex) {
        state.previousIndex = status.index;
        
        // Find episode by number (status.index is already 1-based)
        const newEpisode = state.episodes.find(ep => ep.number === status.index);
        if (newEpisode) {
            state.currentEpisode = newEpisode;
            
            // Update episode title
            document.getElementById('currentEpisodeTitle').textContent = `Episode ${newEpisode.number}: ${newEpisode.name || ''}`;
            document.getElementById('currentEpisodeDescription').textContent = newEpisode.description || '';
            
            // Update thumbnail
            const thumbnailImage = document.getElementById('thumbnailImage');
            if (newEpisode.thumbnail) {
                thumbnailImage.src = newEpisode.thumbnail;
            } else if (state.seriesInfo?.poster) {
                thumbnailImage.src = state.seriesInfo.poster;
            }
            
            // Re-render episode list to update active state
            renderEpisodes();
            
            console.log('Episode changed to:', newEpisode.number);
        }
    }
    
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    const currentTimeEl = document.getElementById('currentTime');
    const totalTimeEl = document.getElementById('totalTime');
    
    const percentage = (status.currentTime / status.total) * 100;
    progressFill.style.width = `${percentage}%`;
    currentTimeEl.textContent = formatTime(status.currentTime);
    totalTimeEl.textContent = formatTime(status.total);
    
    // Update status text
    const statusDetail = document.getElementById('statusDetail');
    statusDetail.textContent = `Engine: ${status.backend} • Last sync: just now`;
}

// ===========================
// EPISODE MANAGEMENT
// ===========================
function renderEpisodes() {
    const container = document.getElementById('episodeListContainer');
    container.innerHTML = '';
    
    if (!state.episodes || state.episodes.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px 0;">No episodes available</p>';
        return;
    }
    
    state.episodes.forEach((episode, index) => {
        const episodeNumber = episode.number || (index + 1);
        const isActive = state.currentEpisode && 
                        (state.currentEpisode.number === episodeNumber || 
                         state.currentEpisode.path === episode.path);
        const isWatched = episode.watched || false;
        
        const episodeEl = document.createElement('div');
        episodeEl.className = `episode-item ${isActive ? 'active' : ''}`;
        episodeEl.onclick = () => playEpisode(episodeNumber);
        
        // Handle thumbnail
        let thumbnailContent = '📺';
        if (episode.thumbnail && episode.thumbnail !== '/mp4.image') {
            thumbnailContent = `<img src="${episode.thumbnail}" alt="Episode ${episodeNumber}">`;
        }
        
        episodeEl.innerHTML = `
            <div class="episode-thumbnail">
                ${thumbnailContent}
            </div>
            <div class="episode-details">
                <div class="episode-number">EPISODE ${episodeNumber}</div>
                <div class="episode-name">${episode.name || `Episode ${episodeNumber}`}</div>
                <div class="episode-duration">${isActive ? `${formatTime(state.currentTime)} / ${formatTime(state.duration)}` : (episode.duration || '')}</div>
            </div>
            <div class="episode-status">${isActive ? '▶' : (isWatched ? '✓' : '')}</div>
        `;
        
        container.appendChild(episodeEl);
    });
    
    // Update episode count
    document.getElementById('episodeCount').textContent = `${state.episodes.length} episode${state.episodes.length !== 1 ? 's' : ''}`;
}

function playEpisode(episodeNumber) {
    const episode = state.episodes.find(ep => ep.number === episodeNumber);
    if (!episode) {
        showAlert('Episode not found', 'error');
        return;
    }
    
    state.currentEpisode = episode;

    // Clear audio and subtitle tracks when switching episodes
    if (state.mode === 'in-browser') {
        clearAllTracks();
    }

    // Update UI
    document.getElementById('currentEpisodeTitle').textContent = `Episode ${episode.number}: ${episode.name || ''}`;
    document.getElementById('currentEpisodeDescription').textContent = episode.description || '';
    
    // Update thumbnail if in master/slave mode
    if (state.mode !== 'in-browser') {
        const thumbnailImage = document.getElementById('thumbnailImage');
        if (episode.thumbnail && episode.thumbnail !== '/mp4.image') {
            thumbnailImage.src = episode.thumbnail;
        } else if (state.seriesInfo?.poster) {
            thumbnailImage.src = state.seriesInfo.poster;
        }
    }
    
    // Play based on mode
    if (state.mode === 'in-browser') {
        const videoPlayer = document.getElementById('videoPlayer');
        const videoSource = document.getElementById('videoSource');
        // Use the path from API (starts with /)
        videoSource.src = episode.path || '';
        videoPlayer.load();
        videoPlayer.play().catch(err => {
            console.error('Playback error:', err);
            showAlert('Failed to play video', 'error');
        });
    } else {
        // Play item in desktop player (0-indexed)
        // sendRemoteCommand(`/playlist_${episodeNumber - 1}`);
        sendRemoteCommand(`/playlist_${episode.epn_number}`);
    }
    
    // Update URL
    if (state.seriesId) {
        //updateURL(state.seriesId, episodeNumber, state.mode);
    }
    
    // Re-render episodes
    renderEpisodes();
}

function playNextEpisode() {
    if (!state.currentEpisode) return;
    
    const currentIndex = state.episodes.findIndex(ep => ep.number === state.currentEpisode.number);
    if (currentIndex < state.episodes.length - 1) {
        playEpisode(state.episodes[currentIndex + 1].number);
    } else {
        showAlert('This is the last episode', 'info');
    }
}

function playPreviousEpisode() {
    if (!state.currentEpisode) return;
    
    const currentIndex = state.episodes.findIndex(ep => ep.number === state.currentEpisode.number);
    if (currentIndex > 0) {
        playEpisode(state.episodes[currentIndex - 1].number);
    } else {
        showAlert('This is the first episode', 'info');
    }
}

// ===========================
// PLAYBACK CONTROLS
// ===========================

function togglePlayPause() {
    if (state.mode === 'in-browser') {
        const videoPlayer = document.getElementById('videoPlayer');
        // Check if video is not loaded but transcode is ongoing
        if (state.transcodeJob && !videoPlayer.src) {
            // Load the transcoding video
            loadTranscodedVideo(state.transcodeJob.url, true);
            return;
        }
        
        // Check if paused and no source - might need to reload transcode
        if (videoPlayer.paused && (!videoPlayer.src || videoPlayer.src === '')) {
            if (state.transcodeJob && state.transcodeJob.url) {
                loadTranscodedVideo(state.transcodeJob.url, true);
            }
            return;
        }
        if (videoPlayer.paused) {
            videoPlayer.play();
        } else {
            videoPlayer.pause();
        }
    } else {
        if (state.firstPlay && state.currentEpisode) {
            // First play: use playlist command to start the episode
            state.firstPlay = false;
            sendRemoteCommand(`/playlist_${state.currentEpisode.epn_number}`);
            console.log('First play: loading episode', state.currentEpisode.epn_number);
        } else {
            sendRemoteCommand('/playpause');
        }
        if (!state.syncInterval) {
            startRemoteSync();
        }
    }
}

function stopPlayback() {
    if (state.mode === 'in-browser') {
        clearAllTracks()
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.pause();
        videoPlayer.currentTime = 0;
    } else {
        sendRemoteCommand('/playerstop');
        stopRemoteSync();
    }
}

function toggleLoop() {
    if (state.mode === 'in-browser') {
        const videoPlayer = document.getElementById('videoPlayer');
        state.loop = !state.loop;
        videoPlayer.loop = state.loop;
        showAlert(state.loop ? 'Loop enabled' : 'Loop disabled', 'success');
    } else {
        sendRemoteCommand('/lock');
        showAlert('Loop toggled', 'success');
    }
}

function seek(seconds) {
    if (state.mode === 'in-browser') {
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.currentTime += seconds;
    } else {
        const command = seconds > 0 ? `seek_${Math.abs(seconds)}` : `seek_${Math.abs(seconds)}`;
        sendRemoteCommand(`/${command}`);
    }
}

function updatePlayPauseButton() {
    const icon = document.getElementById('playPauseIcon');
    const text = document.getElementById('playPauseText');
    
    if (state.playing) {
        icon.textContent = '⏸';
        text.textContent = 'Pause';
    } else {
        icon.textContent = '▶';
        text.textContent = 'Play';
    }
}

// ===========================
// VOLUME CONTROLS (IN-BROWSER)
// ===========================

function adjustVolume(delta) {
    if (state.mode === 'in-browser') {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;
        
        state.volume = Math.max(0, Math.min(100, state.volume + delta));
        videoPlayer.volume = state.volume / 100;
    } else {
        // Master/Slave mode
        const absValue = Math.abs(delta);
        const command = delta > 0 ? `/volume${absValue}` : `/volume_${absValue}`;
        sendRemoteCommand(command);
        state.volume = Math.max(0, Math.min(100, state.volume + delta));
    }
}

function toggleMute() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (!videoPlayer) return;
    
    videoPlayer.muted = !videoPlayer.muted;
}

function toggleFullscreen() {
    const videoPlayer = document.getElementById('videoPlayer');
    if (!videoPlayer) return;
    
    if (!document.fullscreenElement) {
        videoPlayer.requestFullscreen().catch(err => {
            showAlert('Fullscreen failed', 'error');
        });
    } else {
        document.exitFullscreen();
    }
}

// ===========================
// MASTER/SLAVE CONTROLS
// ===========================

async function toggleAudio() {
    await sendRemoteCommand('/toggle_audio');
}

async function toggleSubtitle() {
    await sendRemoteCommand('/toggle_subtitle');
}

async function changeChapter(direction) {
    const widget = direction > 0 ? 'btn_chapter_plus' : 'btn_chapter_minus';
    await sendPostCommand('/sending_web_command', { param: 'click', widget });
}

async function toggleDesktopFullscreen() {
    await sendPostCommand('/sending_web_command', { param: 'click', widget: 'btn_fs_window' });
}

async function showVideoStats() {
    await sendPostCommand('/sending_web_command', { param: 'click', widget: 'btn_show_stat' });
}

async function showPlayerWindow() {
    await sendRemoteCommand('/show_player_window');
}

async function hidePlayerWindow() {
    await sendRemoteCommand('/hide_player_window');
}

async function changeAspectRatio() {
    const select = document.getElementById('aspectRatioSelect');
    const value = select.value;
    const widgetMap = {
        'original': 'btn_aspect_original',
        'disable': 'btn_aspect_disable',
        '4_3': 'btn_aspect_4_3',
        '16_9': 'btn_aspect_16_9',
        '235': 'btn_aspect_235'
    };
    
    if (widgetMap[value]) {
        await sendPostCommand('/sending_web_command', { param: 'click', widget: widgetMap[value] });
    }
}

async function changePlaybackEngine() {
    const select = document.getElementById('playbackEngineSelect');
    const engine = select.value;
    const mode = state.mode === 'master' ? 'master' : 'slave';
    
    await sendRemoteCommand(`/playbackengine=${engine}&mode=${mode}`);
    showAlert(`Playback engine changed to ${engine}`, 'success');
}

async function castURL() {
    const url = prompt('Enter URL to cast:');
    if (url) {
        await sendRemoteCommand(`/youtube_quick=${url}`);
        state.firstPlay = false;
        showAlert('URL casted', 'success');
    }
}

async function renameTitle() {
    const newTitle = prompt('Enter new title:');
    if (newTitle && state.seriesInfo) {
        await sendPostCommand('/rename_title', {
            title: newTitle,
            playlist: state.episodes.map(ep => ep.path),
            db_title: state.seriesInfo.title
        });
        showAlert('Title renamed', 'success');
    }
}

async function fetchPoster() {
    if (state.seriesInfo) {
        await sendPostCommand('/fetch-posters', {
            url: '',
            title: state.seriesInfo.title,
            mode: 'poster',
            site_option: ''
        });
        showAlert('Fetching poster...', 'info');
    }
}

async function fetchFanart() {
    if (state.seriesInfo) {
        await sendPostCommand('/fetch-posters', {
            url: '',
            title: state.seriesInfo.title,
            mode: 'fanart',
            site_option: ''
        });
        showAlert('Fetching fanart...', 'info');
    }
}

async function applyCategory() {
    const select = document.getElementById('categorySelect');
    const category = select.value;
    
    if (category && state.episodes.length > 0) {
        await sendPostCommand('/modify_category', {
            category,
            playlist: state.episodes.map(ep => ep.path)
        });
        showAlert(`Category set to ${category}`, 'success');
    }
}

// ===========================
// PROGRESS BAR INTERACTION
// ===========================
function initProgressBar() {
    const progressBar = document.getElementById('progressBar');
    
    progressBar.addEventListener('click', (e) => {
        const rect = progressBar.getBoundingClientRect();
        const x = rect.x;
        const w = rect.width;
        const clickX = e.pageX;
        
        if (state.mode === 'in-browser') {
            const videoPlayer = document.getElementById('videoPlayer');
            if (videoPlayer.duration) {
                const newTime = parseInt(((clickX - x) / w) * videoPlayer.duration);
                videoPlayer.currentTime = newTime;
                console.log('Seek to:', newTime);
            }
        } else {
            // Master/Slave mode - seek to absolute percentage
            if (state.duration) {
                const percentage = (((clickX - x) / w) * 100).toFixed(2);
                const seekCommand = `/seek_abs_${percentage}`;
                sendRemoteCommand(seekCommand);
                console.log('Seek command:', seekCommand);
            }
        }
    });
}

// ===========================
// BACK TO TOP BUTTON
// ===========================

function initBackToTop() {
    const backToTop = document.getElementById('backToTop');
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });
    
    backToTop.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// ===========================
// TRACK LOADING (IN-BROWSER)
// ===========================

async function loadSubtitles() {
    if (!state.currentEpisode?.actual_path) {
        showAlert('No video path available', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/series/${state.seriesId}/subtitle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentEpisode.actual_path })
        });
        
        const data = await response.json();
        
        if (data.success && data.tracks.length > 0) {
            cleanupSubtitles();
            
            const select = document.getElementById('subtitleSelect');
            select.innerHTML = '<option value="">Subtitles: Off</option>';
            
            const videoPlayer = document.getElementById('videoPlayer');
            
            data.tracks.forEach((track, index) => {
                const blob = new Blob([track.content], { type: 'text/vtt' });
                const blobUrl = URL.createObjectURL(blob);
                state.subtitleBlobUrls.push(blobUrl);
                
                const trackElement = document.createElement('track');
                trackElement.kind = 'subtitles';
                trackElement.label = track.title || track.language.toUpperCase();
                trackElement.srclang = track.language;
                trackElement.src = blobUrl;
                trackElement.id = `subtitle-${index}`;
                if (index === 0) trackElement.default = true;
                
                videoPlayer.appendChild(trackElement);
                
                const option = document.createElement('option');
                option.value = index;
                option.textContent = track.title || track.language.toUpperCase();
                select.appendChild(option);
            });
            
            showAlert(`Loaded ${data.tracks.length} subtitle tracks`, 'success');
        } else {
            showAlert('No subtitles available', 'info');
        }
    } catch (error) {
        console.error('Error loading subtitles:', error);
        showAlert('Failed to load subtitles', 'error');
    }
}

async function loadAudioTracks() {
    if (!state.currentEpisode?.actual_path) {
        showAlert('No video path available', 'error');
        return;
    }

    const button = document.getElementById('loadAudioBtn');
    const originalText = button.innerHTML;

    try {
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<span>⏳</span><span>Loading...</span>';
 
        const response = await fetch(`${CONFIG.BASE_URL}/series/${state.seriesId}/audio`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: state.currentEpisode.actual_path })
        });

        const data = await response.json();

        if (data && data.success && data.tracks && data.tracks.length > 0) {
            state.loadedAudioTracks = data.tracks;
  
            const select = document.getElementById('audioSelect');
            select.innerHTML = '<option value="">Audio: Default</option>';

            data.tracks.forEach((track, index) => {
                const option = document.createElement('option');
                const label = track.transcoded ? ' (Transcoded)' : '';
                option.value = index;
                option.textContent = `${track.language.toUpperCase()} - ${track.channels}ch${label} - ${track.title}`;
                select.appendChild(option);
            });
            
            showAlert(`Loaded ${data.tracks.length} audio tracks`, 'success');
        } else {
            showAlert('No audio tracks available', 'info');
        }
    } catch (error) {
        console.error('Error loading audio tracks:', error);
        showAlert('Failed to load audio tracks', 'error');
    } finally {
        // Restore button state
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

function clearAllTracks() {
    // Clear subtitles
    cleanupSubtitles();
    
    // Clear audio
    if (state.currentAudioElement) {
        state.currentAudioElement.pause();
        state.currentAudioElement.remove();
        state.currentAudioElement = null;
    }
    state.loadedAudioTracks = [];
    
    // Clear transcode job
    stopTranscodeStatusPolling();
    state.transcodeJob = null;
    
    // Clear video player
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSource = document.getElementById('videoSource');
    
    if (videoPlayer) {
        videoPlayer.pause();
        videoPlayer.removeAttribute('src');
        videoPlayer.load(); // Force unload
    }
    
    if (videoSource) {
        videoSource.removeAttribute('src');
    }
    
    // Remove all subtitle tracks from video element
    const existingTracks = videoPlayer.querySelectorAll('track');
    existingTracks.forEach(track => track.remove());
    
    // Reset selectors
    const subtitleSelect = document.getElementById('subtitleSelect');
    const audioSelect = document.getElementById('audioSelect');
    
    if (subtitleSelect) {
        subtitleSelect.innerHTML = '<option value="">Subtitles: Off</option>';
    }
    
    if (audioSelect) {
        audioSelect.innerHTML = '<option value="">Audio: Default</option>';
    }
    
    // Reset transcode UI
    const transcodeBtn = document.getElementById('transcodeBtn');
    const cancelBtn = document.getElementById('cancelTranscodeBtn');
    const progressDiv = document.getElementById('transcodeProgress');
    
    if (transcodeBtn) {
        transcodeBtn.disabled = false;
        transcodeBtn.innerHTML = '<span>🔄</span><span>Transcode Video</span>';
    }
    
    if (cancelBtn) {
        cancelBtn.style.display = 'none';
    }
    
    if (progressDiv) {
        progressDiv.style.display = 'none';
    }
    
    console.log('Cleared all tracks and video for new episode');
}

function switchSubtitle(index) {
    const videoPlayer = document.getElementById('videoPlayer');
    const tracks = videoPlayer.textTracks;

    for (let i = 0; i < tracks.length; i++) {
        tracks[i].mode = 'disabled';
    }

    if (index !== '') {
        tracks[parseInt(index)].mode = 'showing';
    }
}

function switchAudio(index) {
    const videoPlayer = document.getElementById('videoPlayer');
    
    if (index === '') {
        // Switch back to video's built-in audio
        videoPlayer.muted = false;
        
        if (state.currentAudioElement) {
            state.currentAudioElement.pause();
            state.currentAudioElement.remove();
            state.currentAudioElement = null;
        }
        return;
    }

    const track = state.loadedAudioTracks[parseInt(index)];

    if (state.currentAudioElement) {
        state.currentAudioElement.pause();
        state.currentAudioElement.remove();
    }

    // Mute the video's built-in audio track
    videoPlayer.muted = true;

    const audio = new Audio(CONFIG.BASE_URL + track.url);
    audio.volume = videoPlayer.volume || 0.75;  // Use video volume or default
    audio.muted = false;  // External audio should NOT be muted

    const syncPlay = () => {
        audio.currentTime = videoPlayer.currentTime;
        audio.play();
    };
    const syncPause = () => audio.pause();
    const syncSeek = () => audio.currentTime = videoPlayer.currentTime;
    const syncVolume = () => {
        // Only sync volume level, NOT muted state
        audio.volume = videoPlayer.volume;
        // video stays muted, audio stays unmuted
    };

    videoPlayer.addEventListener('play', syncPlay);
    videoPlayer.addEventListener('pause', syncPause);
    videoPlayer.addEventListener('seeked', syncSeek);
    videoPlayer.addEventListener('volumechange', syncVolume);

    state.currentAudioElement = audio;

    if (!videoPlayer.paused) {
        audio.currentTime = videoPlayer.currentTime;
        audio.play();
    }
}

function cleanupSubtitles() {
    state.subtitleBlobUrls.forEach(url => URL.revokeObjectURL(url));
    state.subtitleBlobUrls = [];

    const videoPlayer = document.getElementById('videoPlayer');
    const tracks = videoPlayer.querySelectorAll('track');
    tracks.forEach(track => track.remove());
}

// ===========================
// VIDEO TRANSCODING
// ===========================

async function startTranscode() {
    clearAllTracks()
    if (!state.currentEpisode?.actual_path) {
        showAlert('No video path available', 'error');
        return;
    }
    
    const transcodeBtn = document.getElementById('transcodeBtn');
    const cancelBtn = document.getElementById('cancelTranscodeBtn');
    const progressDiv = document.getElementById('transcodeProgress');
    
    try {
        transcodeBtn.disabled = true;
        
        const response = await fetch(`${CONFIG.BASE_URL}/series/${state.seriesId}/transcode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                path: state.currentEpisode.actual_path,
                video_index: 0,
                audio_index: null
            })
        });
        
        const data = await response.json();
        
        if (data && data.success) {
            state.transcodeJob = {
                url: data.url,
                status: data.status
            };

            // Save to localStorage for persistence across refreshes
            saveTranscodeJob();
            
            // Load video IMMEDIATELY, even if still transcoding
            loadTranscodedVideo(data.url, true); // true = keep progress UI
            
            if (data.status === 'completed') {
                // Already transcoded, load immediately
                loadTranscodedVideo(data.url);
                showAlert('Video loaded (already transcoded)', 'success');
            } else {
                // Show progress UI
                progressDiv.style.display = 'block';
                cancelBtn.style.display = 'inline-flex';
                
                // Start polling for progress
                startTranscodeStatusPolling();
                
                showAlert('Transcoding started...', 'info');
            }
        } else {
            showAlert('Failed to start transcode', 'error');
            transcodeBtn.disabled = false;
        }
    } catch (error) {
        console.error('Error starting transcode:', error);
        showAlert('Failed to start transcode', 'error');
        transcodeBtn.disabled = false;
    }
}

function startTranscodeStatusPolling() {
    if (state.transcodeStatusInterval) {
        clearInterval(state.transcodeStatusInterval);
    }
    
    state.transcodeStatusInterval = setInterval(async () => {
        await checkTranscodeStatus();
    }, 2000); // Poll every 2 seconds
    
    // Check immediately
    checkTranscodeStatus();
}

async function checkTranscodeStatus() {
    if (!state.currentEpisode?.actual_path || !state.transcodeJob) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/series/${state.seriesId}/transcode/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                path: state.currentEpisode.actual_path,
                video_index: 0
            })
        });
        
        const data = await response.json();
        
        if (data && data.success) {
            updateTranscodeProgress(data);
            
            if (data.status === 'completed') {
                // Transcode finished
                stopTranscodeStatusPolling();
                loadTranscodedVideo(data.url);
                showAlert('Video transcoded successfully!', 'success');
            } else if (data.status === 'failed') {
                stopTranscodeStatusPolling();
                showAlert('Transcode failed', 'error');
            } else if (data.status === 'cancelled') {
                stopTranscodeStatusPolling();
                showAlert('Transcode cancelled', 'info');
            }
        }
    } catch (error) {
        console.error('Error checking transcode status:', error);
    }
}

function updateTranscodeProgress(data) {
    const statusEl = document.getElementById('transcodeStatus');
    const percentEl = document.getElementById('transcodePercent');
    const barEl = document.getElementById('transcodeBar');
    const etaEl = document.getElementById('transcodeEta');
    
    const progress = data.progress || 0;
    
    statusEl.textContent = 'Transcoding...';
    percentEl.textContent = `${progress}%`;
    barEl.style.width = `${progress}%`;
    
    if (data.eta) {
        etaEl.textContent = `ETA: ${data.eta}`;
    }
}

async function cancelTranscode() {
    if (!state.currentEpisode?.actual_path) {
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.BASE_URL}/series/${state.seriesId}/transcode/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                path: state.currentEpisode.actual_path,
                video_index: 0
            })
        });
        
        const data = await response.json();
        
        if (data && data.success) {
            stopTranscodeStatusPolling();
            clearTranscodeJob();
            showAlert('Transcode cancelled', 'info');
        }
    } catch (error) {
        console.error('Error cancelling transcode:', error);
        showAlert('Failed to cancel transcode', 'error');
    }
}

async function checkOngoingTranscode() {
    const savedTranscode = loadTranscodeJob();
    
    if (!savedTranscode) {
        return;
    }
    
    // Check if saved transcode matches current episode
    if (savedTranscode.seriesId !== state.seriesId || 
        savedTranscode.episodeNumber !== state.currentEpisode.number ||
        savedTranscode.episodePath !== state.currentEpisode.actual_path) {
        
        console.log('Saved transcode is for different episode, clearing...');
        clearTranscodeJob();
        return;
    }
    
    console.log('Found ongoing transcode job, restoring...');
    state.transcodeJob = savedTranscode;
    
    // Load the video
    loadTranscodedVideo(savedTranscode.url, true);
    
    // Show progress UI
    const progressDiv = document.getElementById('transcodeProgress');
    const cancelBtn = document.getElementById('cancelTranscodeBtn');
    const transcodeBtn = document.getElementById('transcodeBtn');
    
    progressDiv.style.display = 'block';
    cancelBtn.style.display = 'inline-flex';
    transcodeBtn.disabled = true;
    
    // Start polling to check status
    startTranscodeStatusPolling();
    
    showAlert('Resuming transcode playback...', 'info');
}

function stopTranscodeStatusPolling() {
    if (state.transcodeStatusInterval) {
        clearInterval(state.transcodeStatusInterval);
        state.transcodeStatusInterval = null;
    }
    
    const transcodeBtn = document.getElementById('transcodeBtn');
    const cancelBtn = document.getElementById('cancelTranscodeBtn');
    const progressDiv = document.getElementById('transcodeProgress');
    
    transcodeBtn.disabled = false;
    cancelBtn.style.display = 'none';
    progressDiv.style.display = 'none';
    
    state.transcodeJob = null;
}

// ===========================
// EVENT LISTENERS
// ===========================

function initEventListeners() {
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    
    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = `/series-details/${state.seriesId}`;
    });
    
    // Mode switcher
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-mode');
            switchMode(mode);
        });
    });
    
    // Playback controls
    document.getElementById('btnPlayPause').addEventListener('click', togglePlayPause);
    document.getElementById('btnStop').addEventListener('click', stopPlayback);
    document.getElementById('btnPrev').addEventListener('click', playPreviousEpisode);
    document.getElementById('btnNext').addEventListener('click', playNextEpisode);
    document.getElementById('btnLoop').addEventListener('click', toggleLoop);

    // Transcode controls (in-browser only)
    document.getElementById('transcodeBtn')?.addEventListener('click', startTranscode);
    document.getElementById('cancelTranscodeBtn')?.addEventListener('click', cancelTranscode);
    
    // Seek controls
    document.getElementById('btnSeek10Minus').addEventListener('click', () => seek(-10));
    document.getElementById('btnSeek10Plus').addEventListener('click', () => seek(10));
    document.getElementById('btnSeek60Minus').addEventListener('click', () => seek(-60));
    document.getElementById('btnSeek60Plus').addEventListener('click', () => seek(60));
    document.getElementById('btnSeek5mMinus').addEventListener('click', () => seek(-300));
    document.getElementById('btnSeek5mPlus').addEventListener('click', () => seek(300));

    // Track controls (in-browser only)
    document.getElementById('loadSubtitlesBtn')?.addEventListener('click', loadSubtitles);
    document.getElementById('loadAudioBtn')?.addEventListener('click', loadAudioTracks);
    document.getElementById('subtitleSelect')?.addEventListener('change', (e) => switchSubtitle(e.target.value));
    document.getElementById('audioSelect')?.addEventListener('change', (e) => switchAudio(e.target.value));

    // Volume controls (in-browser)
    document.getElementById('btnVolDown')?.addEventListener('click', () => adjustVolume(-5));
    document.getElementById('btnVolUp')?.addEventListener('click', () => adjustVolume(5));
    document.getElementById('btnMute')?.addEventListener('click', toggleMute);
    document.getElementById('btnFullscreen')?.addEventListener('click', () => {
        if (state.mode === 'in-browser') {
            toggleFullscreen();
        } else {
            // Master/Slave mode - fullscreen video
            sendRemoteCommand('/fullscreen');
        }
    });
    document.getElementById('btnSubtitle')?.addEventListener('click', () => {
        if (state.mode === 'in-browser') {
            // Toggle subtitle in browser
            const videoPlayer = document.getElementById('videoPlayer');
            const tracks = videoPlayer.textTracks;
            if (tracks.length > 0) {
                tracks[0].mode = tracks[0].mode === 'showing' ? 'hidden' : 'showing';
            }
        } else {
            toggleSubtitle();
        }
    });
    
    // Media controls (master/slave)
    document.getElementById('btnToggleAudio')?.addEventListener('click', toggleAudio);
    document.getElementById('btnToggleSubtitle')?.addEventListener('click', toggleSubtitle);
    document.getElementById('btnChapterPrev')?.addEventListener('click', () => changeChapter(-1));
    document.getElementById('btnChapterNext')?.addEventListener('click', () => changeChapter(1));
    
    // Display controls (master/slave)
    document.getElementById('btnDesktopFullscreen')?.addEventListener('click', toggleDesktopFullscreen);
    document.getElementById('btnShowStats')?.addEventListener('click', showVideoStats);
    document.getElementById('btnShowPlayer')?.addEventListener('click', showPlayerWindow);
    document.getElementById('btnHidePlayer')?.addEventListener('click', hidePlayerWindow);
    document.getElementById('aspectRatioSelect')?.addEventListener('change', changeAspectRatio);
    document.getElementById('playbackEngineSelect')?.addEventListener('change', changePlaybackEngine);
    
    // Advanced controls (master/slave)
    document.getElementById('btnCastUrl')?.addEventListener('click', castURL);
    document.getElementById('btnRename')?.addEventListener('click', renameTitle);
    document.getElementById('btnFetchPoster')?.addEventListener('click', fetchPoster);
    document.getElementById('btnFetchFanart')?.addEventListener('click', fetchFanart);
    document.getElementById('btnApplyCategory')?.addEventListener('click', applyCategory);
}

// ===========================
// INITIALIZATION
// ===========================
async function initialize() {
    console.log('Initializing player control page...');
    
    // Get URL parameters
    const params = getURLParams();
    console.log('URL params:', params);
    
    state.seriesId = params.seriesId;
    state.mode = params.mode;
    
    if (!state.seriesId) {
        console.error('No series ID found in URL');
        showAlert('No series ID provided. Please access this page from the series details page.', 'error');
        document.getElementById('loadingScreen').classList.add('hidden');
        
        // Update UI to show error
        document.getElementById('seriesTitle').textContent = 'Error: No Series ID';
        return;
    }
    
    console.log('Series ID:', state.seriesId);
    console.log('Starting mode:', state.mode);
    
    // Initialize theme
    initTheme();
    
    // Fetch series data
    console.log('Fetching series details...');
    const seriesData = await fetchSeriesDetails(state.seriesId);
    if (!seriesData) {
        document.getElementById('loadingScreen').classList.add('hidden');
        document.getElementById('seriesTitle').textContent = 'Error Loading Series';
        return;
    }
    
    console.log('Series data loaded:', seriesData);
    
    // Update state
    state.seriesInfo = seriesData;
    state.episodes = seriesData.episodes || [];
    
    if (state.episodes.length === 0) {
        console.warn('No episodes found');
        showAlert('No episodes available for this series', 'warning');
    }

    const savedEpisodeNumber = localStorage.getItem('selectedEpisodeNumber');
    let targetEpisodeNumber = params.episodeNumber;

    if (savedEpisodeNumber) {
        targetEpisodeNumber = parseInt(savedEpisodeNumber);
        //localStorage.removeItem('selectedEpisodeNumber'); // Clean up
        console.log('Using saved episode number:', targetEpisodeNumber);
    }

    // Find current episode by number or use first episode
    state.currentEpisode = state.episodes.find(ep => ep.number === targetEpisodeNumber) || state.episodes[0];

    if (!state.currentEpisode) {
        console.error('No episodes available');
        showAlert('No episodes available', 'error');
        document.getElementById('loadingScreen').classList.add('hidden');
        return;
    }

    console.log('Current episode:', state.currentEpisode);

    // Update UI
    document.getElementById('seriesTitle').textContent = seriesData.title || 'Unknown Series';
    document.getElementById('currentEpisodeTitle').textContent = `Episode ${state.currentEpisode.number}: ${state.currentEpisode.name || ''}`;
    document.getElementById('currentEpisodeDescription').textContent = state.currentEpisode.description || '';
    
    // Set thumbnail for master/slave mode
    const thumbnailImage = document.getElementById('thumbnailImage');
    if (state.currentEpisode.thumbnail && state.currentEpisode.thumbnail !== '/mp4.image') {
        thumbnailImage.src = state.currentEpisode.thumbnail;
        thumbnailImage.alt = `Episode ${state.currentEpisode.number} thumbnail`;
    } else if (seriesData.poster) {
        thumbnailImage.src = seriesData.poster;
        thumbnailImage.alt = seriesData.title;
    }

    await checkOngoingTranscode();
    
    // Render episodes
    renderEpisodes();
    
    // Initialize event listeners
    initEventListeners();
    initProgressBar();
    initBackToTop();
    
    // Initialize mode AFTER everything is set up
    console.log('Switching to mode:', state.mode);
    switchMode(state.mode);
    
    // Hide loading screen
    document.getElementById('loadingScreen').classList.add('hidden');
    console.log('Initialization complete');
}


// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
