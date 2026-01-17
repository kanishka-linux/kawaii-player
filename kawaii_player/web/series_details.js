/**
 * Series Details JavaScript Module
 * Handles fetching series data and rendering the details page
 */

class SeriesDetailsApp {
    constructor() {
        this.seriesId = null;
        this.seriesData = null;
    }
    
    init() {
        // Get series ID from URL
        this.seriesId = this.getSeriesIdFromURL();
        
        if (!this.seriesId) {
            this.showError('Invalid series ID', 'No series ID found in URL');
            return;
        }
        
        // Fetch series details
        this.fetchSeriesDetails();
        
        // Setup back button
        this.setupBackButton();
    }
    
    getSeriesIdFromURL() {
        // Extract series ID from URL pathname
        // Expected format: /series/:id or /series-details/:id
        const pathParts = window.location.pathname.split('/');
        const seriesIndex = pathParts.indexOf('series') !== -1 ? pathParts.indexOf('series') : pathParts.indexOf('series-details');
        
        if (seriesIndex !== -1 && pathParts[seriesIndex + 1]) {
            return pathParts[seriesIndex + 1];
        }
        
        return null;
    }
    
    async fetchSeriesDetails() {
        try {
            const response = await fetch(`/title-details/${this.seriesId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Series not found');
                } else if (response.status === 401) {
                    // Redirect to login if unauthorized
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.seriesData = data;
            
            // Render the series details
            this.renderSeriesDetails();
            
        } catch (error) {
            console.error('Error fetching series details:', error);
            this.showError('Failed to load series', error.message);
        }
    }
    
    renderSeriesDetails() {
        const contentContainer = document.getElementById('series-content');
        const headerTitle = document.getElementById('header-title');
        
        if (!this.seriesData || !this.seriesData.series_info) {
            this.showError('Invalid data', 'Series data is not in expected format');
            return;
        }
        
        const info = this.seriesData.series_info;
        const episodes = this.seriesData.episodes || [];
        
        // Update page title and header
        document.title = `${info.title || info.db_title} - Series Details`;
        headerTitle.textContent = info.title || info.db_title;
        
        // Build the HTML
        const html = `
            <div class="left-column">
                ${this.renderPoster(info)}
                ${this.renderInfoBox(info)}
            </div>
            
            <div class="right-column">
                ${this.renderTitles(info)}
                ${this.renderGenres(info)}
                ${this.renderSummary(info)}
                ${this.renderEpisodes(episodes)}
            </div>
        `;
        
        contentContainer.innerHTML = html;
        
        // Setup episode click handlers
        this.setupEpisodeHandlers();
    }
    
    renderPoster(info) {
        const posterImage = info.image_poster_large || '';
        const score = info.score || 'N/A';
        
        return `
            <div class="series-poster">
                ${posterImage ? 
                    `<img src="${this.escapeHtml(posterImage)}" alt="${this.escapeHtml(info.title || info.db_title)}" onerror="this.parentElement.innerHTML='<div class=\\'series-poster-placeholder\\'>📺</div>'">` :
                    `<div class="series-poster-placeholder">📺</div>`
                }
                ${score !== 'N/A' ? `<div class="poster-score-badge">${score} ⭐</div>` : ''}
            </div>
        `;
    }
    
    renderInfoBox(info) {
        const fields = [
            { label: 'Type', value: info.type },
            { label: 'Year', value: info.year },
            { label: 'Episodes', value: info.episodes },
            { label: 'Duration', value: info.duration },
            { label: 'Score', value: info.score },
            { label: 'Rank', value: info.rank ? `#${info.rank}` : null },
            { label: 'Popularity', value: info.popularity ? `#${info.popularity}` : null },
            { label: 'Status', value: info.labels || 'Unknown' },
            { label: 'Available', value: info.episodes_available && info.episodes ? 
                `${info.episodes_available} / ${info.episodes}` : info.episodes_available }
        ];
        
        const rows = fields
            .filter(field => field.value !== undefined && field.value !== null && field.value !== '')
            .map(field => `
                <div class="info-row">
                    <span class="info-label">${field.label}</span>
                    <span class="info-value">${this.escapeHtml(String(field.value))}</span>
                </div>
            `).join('');
        
        return `
            <div class="series-info-box">
                ${rows}
            </div>
        `;
    }
    
    renderTitles(info) {
        const mainTitle = info.title || info.db_title;
        const englishTitle = info.english_title;
        
        return `
            <h1 class="series-main-title">${this.escapeHtml(mainTitle)}</h1>
            ${englishTitle ? `<p class="series-english-title">${this.escapeHtml(englishTitle)}</p>` : ''}
        `;
    }
    
    renderGenres(info) {
        if (!info.genres) return '';
        
        // Split genres by comma and create tags
        const genres = info.genres.split(',').map(g => g.trim()).filter(g => g);
        
        if (genres.length === 0) return '';
        
        const genreTags = genres.map(genre => 
            `<span class="genre-tag">${this.escapeHtml(genre)}</span>`
        ).join('');
        
        return `
            <div class="series-genres">
                ${genreTags}
            </div>
        `;
    }
    
    renderSummary(info) {
        if (!info.summary) return '';
        
        return `
            <div class="details-section">
                <h2 class="section-title">Synopsis</h2>
                <p class="series-summary">${this.escapeHtml(info.summary)}</p>
            </div>
        `;
    }
    
    renderEpisodes(episodes) {
        if (!episodes || episodes.length === 0) {
            return `
                <div class="details-section">
                    <h2 class="section-title">Episodes</h2>
                    <div class="empty-episodes">
                        <div class="empty-episodes-icon">📺</div>
                        <h3>No Episodes Available</h3>
                        <p>Episodes for this series are not yet available.</p>
                    </div>
                </div>
            `;
        }
        
        const episodeItems = episodes.map((episode, index) => {
            const episodeNumber = index + 1;
            const episodeName = episode.name || `Episode ${episodeNumber}`;
            const imageUrl = episode['image-url'] || '';
            
            return `
                <div class="episode-item" data-episode-number="${episodeNumber}" data-series-id="${this.seriesId}" tabindex="0" role="button" aria-label="Play ${episodeName}">
                    <div class="episode-thumbnail">
                        ${imageUrl ? 
                            `<img src="${this.escapeHtml(imageUrl)}" alt="${this.escapeHtml(episodeName)}" class="episode-thumb-img" data-base-url="${this.escapeHtml(imageUrl)}" onerror="this.parentElement.innerHTML='<div class=\\'episode-thumbnail-placeholder\\'>📺</div>'">` :
                            `<div class="episode-thumbnail-placeholder">📺</div>`
                        }
                    </div>
                    <div class="episode-details">
                        <div class="episode-number">Episode ${episodeNumber}</div>
                        <div class="episode-title">${this.escapeHtml(episodeName)}</div>
                    </div>
                    ${imageUrl ? `<button class="thumbnail-preview-btn" data-episode="${episodeNumber}">Preview 🔄</button>` : ''}
                </div>
            `;
        }).join('');
        
        return `
            <div class="details-section">
                <h2 class="section-title">Episodes (${episodes.length})</h2>
                <div class="episodes-list">
                    ${episodeItems}
                </div>
            </div>
        `;
    }
    
    setupEpisodeHandlers() {
        const episodeItems = document.querySelectorAll('.episode-item');
        
        episodeItems.forEach(item => {
            // Click handler
            item.addEventListener('click', (e) => {
                // Don't play if clicking the preview button
                if (e.target.classList.contains('thumbnail-preview-btn')) {
                    return;
                }
                this.playEpisode(item);
            });
            
            // Keyboard handler (Enter or Space)
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.playEpisode(item);
                }
            });
        });
        
        // Setup thumbnail preview buttons
        this.setupThumbnailPreviews();
    }

    setupThumbnailPreviews() {
        const previewBtns = document.querySelectorAll('.thumbnail-preview-btn');

        previewBtns.forEach(btn => {
            let currentInterval = 0; // Start at 0, will increment to 5 on first click

            btn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent episode click

                const img = btn.parentElement.querySelector('.episode-thumb-img');
                if (!img) return;

                const baseUrl = img.dataset.baseUrl;
                if (!baseUrl) return;

                // Increment interval: 5, 10, 15, ..., 95, 100, then back to 5
                currentInterval += 5;
                if (currentInterval > 100) {
                    currentInterval = 5;
                }

                // Update image URL
                const newUrl = `${baseUrl}.image_next_${currentInterval}`;
                img.src = newUrl;

                // Update button text to show current position
                btn.textContent = `${currentInterval}% 🔄`;

                // Handle image load error - reset to base
                img.onerror = () => {
                    img.src = baseUrl;
                    btn.textContent = 'Preview 🔄';
                    currentInterval = 0;
                };
            });
        });
    }
    
    playEpisode(episodeElement) {
        const episodeNumber = episodeElement.dataset.episodeNumber;
        const seriesId = episodeElement.dataset.seriesId;
        
        if (!episodeNumber || !seriesId) {
            console.error('Missing episode or series information');
            this.showMessage('Error', 'Unable to play episode', 'error');
            return;
        }
        
        // Navigate to series player page
        window.location.href = `/series/${seriesId}/playercontrol`;
    }
    
    setupBackButton() {
        const backBtn = document.getElementById('back-btn');
        
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                // Check if there's a referrer and it's from the same origin
                if (document.referrer && document.referrer.includes(window.location.origin)) {
                    window.history.back();
                } else {
                    // Default to browse page
                    window.location.href = '/browse';
                }
            });
        }
    }
    
    showError(title, message) {
        const contentContainer = document.getElementById('series-content');
        const headerTitle = document.getElementById('header-title');
        
        headerTitle.textContent = title;
        
        contentContainer.innerHTML = `
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h2>${this.escapeHtml(title)}</h2>
                <p>${this.escapeHtml(message)}</p>
                <button class="retry-btn" onclick="location.reload()">
                    🔄 Retry
                </button>
            </div>
        `;
    }
    
    showMessage(title, message, type = 'info') {
        // Create alert container if it doesn't exist
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'alert-container';
            document.body.appendChild(alertContainer);
        }
        
        const icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        };
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <span class="alert-icon">${icons[type] || icons.info}</span>
            <span class="alert-message">${this.escapeHtml(message)}</span>
            <button class="alert-close">×</button>
        `;
        
        // Add close functionality
        const closeBtn = alert.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            this.removeAlert(alert);
        });
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            this.removeAlert(alert);
        }, 5000);
    }
    
    removeAlert(alert) {
        if (alert && alert.parentNode) {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new SeriesDetailsApp();
    app.init();
});

// Handle online/offline status
window.addEventListener('online', () => {
    console.log('Connection restored');
});

window.addEventListener('offline', () => {
    console.log('Connection lost');
});

// Export for external use and testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SeriesDetailsApp };
} else {
    window.SeriesDetailsApp = SeriesDetailsApp;
}
