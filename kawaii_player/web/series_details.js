/**
 * Series Details JavaScript Module
 * Handles fetching series data and rendering the details page
 */

class SeriesDetailsApp {
    constructor() {
        this.seriesId = null;
        this.seriesData = null;
        this.currentLabel = null;
        this.isUpdatingLabel = false;
        this.editMode = false;
        this.selectedEpisodes = new Set();
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

    initLabelSelector() {
      const currentLabel = this.seriesData?.series_info?.current_label || null;
      this.currentLabel = currentLabel;
      
      // Setup dropdown
      const select = document.getElementById('series-label-select');
      if (select) {
        select.value = currentLabel || '';
        select.addEventListener('change', (e) => {
          this.onLabelChange(e.target.value, this.seriesId);
        });
      }
      
      // Setup buttons
      const buttons = document.querySelectorAll('.label-btn-compact');
      buttons.forEach(btn => {
        const label = btn.dataset.label;
        if (label === currentLabel) btn.classList.add('active');
        
        btn.addEventListener('click', () => {
          this.onLabelChange(label, this.seriesId);
        });
        
        btn.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.onLabelChange(label, this.seriesId);
          }
        });
      });
    }

    async onLabelChange(newLabel, seriesId) {
      if (this.isUpdatingLabel || newLabel === this.currentLabel) return;
      
      const previousLabel = this.currentLabel;
      this.setLabelLoading(true, newLabel);
      
      try {
        const response = await fetch('/api/update-series-label', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({
            series_id: seriesId,
            label: newLabel || null
          })
        });
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          
          if (response.status === 401) {
            window.location.href = '/login';
            return;
          }
          
          throw new Error(
            errorData.error || 
            (response.status === 404 ? 'Series not found' : 'Failed to update label')
          );
        }
        
        this.currentLabel = newLabel;
        this.updateLabelUI(newLabel, previousLabel);
        this.showMessage('Success', 'Status updated!', 'success');
        
      } catch (error) {
        console.error('Label update error:', error);
        this.updateLabelUI(previousLabel, newLabel);
        this.currentLabel = previousLabel;
        this.showMessage('Error', error.message || 'Failed to update status', 'error');
        
      } finally {
        this.setLabelLoading(false, newLabel);
      }
    }

    updateLabelUI(newLabel, oldLabel) {
      const select = document.getElementById('series-label-select');
      if (select) select.value = newLabel || '';
      
      const buttons = document.querySelectorAll('.label-btn-compact');
      buttons.forEach(btn => {
        if (btn.dataset.label === newLabel) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    setLabelLoading(isLoading, targetLabel) {
      this.isUpdatingLabel = isLoading;
      
      const btn = document.querySelector(`.label-btn-compact[data-label="${targetLabel}"]`);
      if (btn) {
        btn.classList.toggle('loading', isLoading);
        btn.disabled = isLoading;
      }
      
      const select = document.getElementById('series-label-select');
      if (select) select.disabled = isLoading;
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
                ${this.renderFetchMediaButtons()}
                ${this.renderGenres(info)}
                ${this.renderSummary(info)}
                ${this.renderEpisodes(episodes)}
            </div>
        `;
        
        contentContainer.innerHTML = html;
        
        // Setup episode click handlers
        this.setupEpisodeHandlers();
        this.setupDeleteStaleEntryHandler();
        this.initLabelSelector();
        this.setupFetchMediaHandlers();
        this.setupPosterEditHandler();
    }

    setupPosterEditHandler() {
        const btn = document.getElementById('poster-edit-btn');
        if (!btn) return;
        
        btn.addEventListener('click', () => this.showChangePosterDialog());
    }

    
    showChangePosterDialog() {
        const currentTitle = this.seriesData?.series_info?.db_title || 
                             this.seriesData?.series_info?.title || '';
        const currentPosterUrl = this.seriesData?.series_info?.image_poster_large || '';
        
        const tpl = document.getElementById('tpl-change-poster-modal');
        const modalFragment = tpl.content.cloneNode(true);
        
        // Fill in dynamic content
        modalFragment.querySelector('.js-series-title').textContent = currentTitle;
        const urlInput = modalFragment.querySelector('.js-poster-url-input');
        urlInput.value = currentPosterUrl;
        
        // Append to body
        const container = document.createElement('div');
        container.id = 'change-poster-container';
        container.appendChild(modalFragment);
        document.body.appendChild(container);
        
        const dialog = container.querySelector('.fetch-modal-dialog');
        const overlayEl = container.querySelector('.fetch-modal-overlay');
        const cancelBtn = dialog.querySelector('.js-cancel-btn');
        const confirmBtn = dialog.querySelector('.js-confirm-btn');
        const browseBtn = dialog.querySelector('.js-browse-btn');
        const gridContainer = dialog.querySelector('.js-poster-grid-container');
        const gridStatus = dialog.querySelector('.js-poster-grid-status');
        const grid = dialog.querySelector('.js-poster-grid');
        
        const closeModal = () => {
            overlayEl.classList.remove('active');
            setTimeout(() => {
                if (container.parentNode) container.parentNode.removeChild(container);
            }, 200);
        };
        
        cancelBtn.addEventListener('click', closeModal);
        overlayEl.addEventListener('click', (e) => { if (e.target === overlayEl) closeModal(); });
        
        const escapeHandler = (e) => {
            if (e.key === 'Escape') { closeModal(); document.removeEventListener('keydown', escapeHandler); }
        };
        document.addEventListener('keydown', escapeHandler);
        
        urlInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                confirmBtn.click();
            }
        });
        
        // Browse Available Posters button
        browseBtn.addEventListener('click', async () => {
            const externalId = this.seriesData?.series_info?.external_id;
            if (!externalId) {
                gridContainer.style.display = 'block';
                gridStatus.style.display = 'block';
                gridStatus.textContent = 'No external ID available for this series';
                return;
            }
            
            gridContainer.style.display = 'block';
            gridStatus.style.display = 'block';
            gridStatus.textContent = 'Loading posters...';
            grid.innerHTML = '';
            browseBtn.disabled = true;
            
            try {
                const response = await fetch('/get_posters', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        external_id: externalId,
                        category: this.seriesData?.series_info?.category || ''
                    })
                });
                
                const result = await response.json();
                
                if (!result.success) {
                    gridStatus.textContent = result.error || 'Failed to load posters';
                    browseBtn.disabled = false;
                    return;
                }
                
                const posters = result.posters || [];
                
                if (posters.length === 0) {
                    gridStatus.textContent = result.message || 'No alternative posters available';
                    browseBtn.disabled = false;
                    return;
                }
                
                gridStatus.style.display = 'none';
                
                // Render thumbnails
                posters.forEach(url => {
                    const thumb = document.createElement('div');
                    thumb.className = 'poster-thumb';
                    thumb.innerHTML = `<img src="${this.escapeHtml(url)}" alt="Poster option" loading="lazy">`;
                    thumb.addEventListener('click', () => {
                        urlInput.value = url;
                        grid.querySelectorAll('.poster-thumb').forEach(t => t.classList.remove('selected'));
                        thumb.classList.add('selected');
                    });
                    grid.appendChild(thumb);
                });
                
                browseBtn.textContent = `🔄 Reload Posters (${posters.length} found)`;
                browseBtn.disabled = false;
                
            } catch (error) {
                console.error('Browse posters error:', error);
                gridStatus.textContent = 'Error loading posters: ' + error.message;
                browseBtn.disabled = false;
            }
        });
        
        // Update Poster (submit) button
        confirmBtn.addEventListener('click', async () => {
            const newUrl = urlInput.value.trim();
            if (!newUrl) {
                this.showMessage('Error', 'Please enter an image URL', 'error');
                return;
            }
            
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;
            urlInput.disabled = true;
            browseBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="fetch-loading-spinner"></span>Updating...';
            
            try {
                const response = await fetch('/fetch_image_poster', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        db_title: currentTitle,
                        img_url: newUrl,
                        media_type: 'video'
                    })
                });
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const result = await response.json();
                if (!result.success) throw new Error(result.error || 'Failed to update poster');
                
                closeModal();
                this.showMessage('Success', 'Poster updated!', 'success');
                setTimeout(() => location.reload(), 1200);
                
            } catch (error) {
                console.error('Change poster error:', error);
                this.showMessage('Error', error.message || 'Failed to update poster', 'error');
                confirmBtn.disabled = false;
                cancelBtn.disabled = false;
                urlInput.disabled = false;
                browseBtn.disabled = false;
                confirmBtn.innerHTML = 'Update Poster';
            }
        });
        
        setTimeout(() => { urlInput.focus(); urlInput.select(); }, 100);
    }

    renderFetchMediaButtons() {
      return `
        <div class="fetch-media-buttons">
          <button class="fetch-btn fetch-metadata-btn" id="fetch-metadata-btn" title="Fetch series metadata">
            <span class="fetch-icon">🔄</span>
            <span class="fetch-text">Fetch Metadata</span>
          </button>
          <button class="fetch-btn fetch-fanart-btn" id="fetch-fanart-btn" title="Fetch fanart image">
            <span class="fetch-icon">🎨</span>
            <span class="fetch-text">Fetch Fanart</span>
          </button>
          <button class="fetch-btn fetch-reset-episodes-btn" id="fetch-reset-episodes-btn" title="Reset episodes">
            <span class="fetch-icon">🗑️</span>
            <span class="fetch-text">Reset Episodes</span>
          </button>
          <button class="fetch-btn fetch-edit-episodes-btn" id="fetch-edit-episodes-btn" title="Edit episode titles">
            <span class="fetch-icon">✏️</span>
            <span class="fetch-text">Edit Episodes</span>
          </button>
        </div>
      `;
    }

    setupFetchMediaHandlers() {
      const metadataBtn = document.getElementById('fetch-metadata-btn');
      const fanartBtn = document.getElementById('fetch-fanart-btn');
      const resetEpisodesBtn = document.getElementById('fetch-reset-episodes-btn');
      const editEpisodesBtn = document.getElementById('fetch-edit-episodes-btn');
      
      if (metadataBtn) {
        metadataBtn.addEventListener('click', () => {
          this.showFetchMetadataDialog();
        });
      }
      
      if (fanartBtn) {
        fanartBtn.addEventListener('click', () => {
          this.showFetchMediaDialog('fanart');
        });
      }

      if (resetEpisodesBtn) {
        resetEpisodesBtn.addEventListener('click', () => {
            this.showResetEpisodesDialog();
        });
      }
      
      if (editEpisodesBtn) {
        editEpisodesBtn.addEventListener('click', () => this.toggleEditMode());
      }
    }

    toggleEditMode() {
        if (this.editMode) {
            this.exitEditMode();
        } else {
            this.enterEditMode();
        }
    }

    
    enterEditMode() {
        this.editMode = true;
        this.selectedEpisodes.clear();

        const episodesList = document.querySelector('.episodes-list');
        if (!episodesList) return;
        
        // Add edit-mode class to enable CSS-driven UI changes
        episodesList.classList.add('edit-mode');
        
        // Insert checkboxes into each episode row by cloning template
        const checkboxTpl = document.getElementById('tpl-episode-checkbox');
        document.querySelectorAll('.episode-item').forEach(item => {
            if (item.querySelector('.episode-checkbox-wrapper')) return; // already added
            const checkbox = checkboxTpl.content.cloneNode(true);
            const wrapper = checkbox.querySelector('.episode-checkbox-wrapper');
            const cb = checkbox.querySelector('.episode-edit-checkbox');
            cb.dataset.path = item.querySelector('.episode-watch-btn')?.dataset.episodePath || '';
            cb.addEventListener('change', () => this.onEpisodeCheckboxChange(cb));
            cb.addEventListener('click', (e) => e.stopPropagation());
            wrapper.addEventListener('click', (e) => e.stopPropagation());
            item.prepend(checkbox);
        });
        
        // Insert edit-controls bar above episodes list
        const controlsTpl = document.getElementById('tpl-edit-controls');
        const controls = controlsTpl.content.cloneNode(true);
        controls.querySelector('.js-select-all').addEventListener('click', () => this.selectAllEpisodesForEdit());
        controls.querySelector('.js-deselect-all').addEventListener('click', () => this.deselectAllEpisodesForEdit());
        controls.querySelector('.js-edit-selected').addEventListener('click', () => this.openEditSelectedModal());
        episodesList.parentNode.insertBefore(controls, episodesList);
        
        // Flip button label
        const btn = document.getElementById('fetch-edit-episodes-btn');
        if (btn) {
            btn.querySelector('.fetch-text').textContent = 'Cancel Edit';
            btn.querySelector('.fetch-icon').textContent = '✕';
            btn.classList.add('active');
        }
    }

    exitEditMode() {
        this.editMode = false;
        this.selectedEpisodes.clear();

        const episodesList = document.querySelector('.episodes-list');
        if (episodesList) {
            episodesList.classList.remove('edit-mode');
        }
        
        // Remove checkboxes
        document.querySelectorAll('.episode-checkbox-wrapper').forEach(el => el.remove());
        
        // Remove controls bar
        const controlsBar = document.querySelector('.edit-controls-bar');
        if (controlsBar) controlsBar.remove();
        
        // Restore button label
        const btn = document.getElementById('fetch-edit-episodes-btn');
        if (btn) {
            btn.querySelector('.fetch-text').textContent = 'Edit Episodes';
            btn.querySelector('.fetch-icon').textContent = '✏️';
            btn.classList.remove('active');
        }
    }

    onEpisodeCheckboxChange(checkbox) {
        const path = checkbox.dataset.path;
        if (!path) return;
        
        if (checkbox.checked) {
            this.selectedEpisodes.add(path);
        } else {
            this.selectedEpisodes.delete(path);
        }
        this.updateEditControlsBar();
    }

    updateEditControlsBar() {
        const count = this.selectedEpisodes.size;
        const countEl = document.querySelector('.edit-controls-bar .js-selected-count');
        const editBtn = document.querySelector('.edit-controls-bar .js-edit-selected');
        
        if (countEl) countEl.textContent = count;
        if (editBtn) editBtn.disabled = count === 0;
    }

    selectAllEpisodesForEdit() {
        document.querySelectorAll('.episode-edit-checkbox').forEach(cb => {
            cb.checked = true;
            if (cb.dataset.path) this.selectedEpisodes.add(cb.dataset.path);
        });
        this.updateEditControlsBar();
    }

    deselectAllEpisodesForEdit() {
        document.querySelectorAll('.episode-edit-checkbox').forEach(cb => cb.checked = false);
        this.selectedEpisodes.clear();
        this.updateEditControlsBar();
    }

    
    openEditSelectedModal() {
        if (this.selectedEpisodes.size === 0) return;
        
        const paths = Array.from(this.selectedEpisodes);
        const tpl = document.getElementById('tpl-edit-episodes-modal');
        const modalFragment = tpl.content.cloneNode(true);
        const overlay = modalFragment.querySelector('.fetch-modal-overlay');
        
        // Fill in episode count
        overlay.querySelector('.js-episode-count').textContent = paths.length;
        
        // Prepopulate inputs with current series title
        const currentTitle = this.seriesData?.series_info?.db_title || this.seriesData?.series_info?.title || '';
        overlay.querySelector('.js-title-only-input').value = currentTitle;
        overlay.querySelector('.js-both-title-input').value = currentTitle;
        
        // Append to body
        const container = document.createElement('div');
        container.id = 'edit-episodes-container';
        container.appendChild(modalFragment);
        document.body.appendChild(container);
        
        // Wire up controls
        const dialog = container.querySelector('.edit-episodes-dialog');
        const modeRadios = dialog.querySelectorAll('.js-mode-radio');
        const titleOnlySection = dialog.querySelector('.js-mode-title-only');
        const bothSection = dialog.querySelector('.js-mode-both');
        const titleOnlyInput = dialog.querySelector('.js-title-only-input');
        const bothTitleInput = dialog.querySelector('.js-both-title-input');
        const bothStartInput = dialog.querySelector('.js-both-start-input');
        const previewToggle = dialog.querySelector('.js-preview-toggle');
        const previewContent = dialog.querySelector('.js-preview-content');
        const previewRows = dialog.querySelector('.js-preview-rows');
        const cancelBtn = dialog.querySelector('.js-cancel-btn');
        const confirmBtn = dialog.querySelector('.js-confirm-btn');
        
        const updatePreview = () => {
            const mode = dialog.querySelector('.js-mode-radio:checked').value;
            let rows = '';
            if (mode === 'title-only') {
                const title = titleOnlyInput.value.trim() || '[Enter title]';
                paths.forEach(path => {
                    rows += `<tr><td>${this.escapeHtml(path)}</td><td>${this.escapeHtml(title)}</td></tr>`;
                });
            } else {
                const baseTitle = bothTitleInput.value.trim() || '[Enter title]';
                const start = parseInt(bothStartInput.value) || 1;
                paths.forEach((path, i) => {
                    const epNum = start + i;
                    const newName = `${baseTitle} - EP${epNum.toString().padStart(2, '0')}`;
                    rows += `<tr><td>${this.escapeHtml(path)}</td><td>${this.escapeHtml(newName)}</td></tr>`;
                });
            }
            previewRows.innerHTML = rows;
        };
        
        // Mode switch
        modeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                const mode = radio.value;
                titleOnlySection.style.display = mode === 'title-only' ? 'block' : 'none';
                bothSection.style.display = mode === 'both' ? 'block' : 'none';
                updatePreview();
            });
        });
        
        // Inputs trigger preview refresh
        [titleOnlyInput, bothTitleInput, bothStartInput].forEach(input => {
            input.addEventListener('input', updatePreview);
        });
        
        // Preview toggle
        previewToggle.addEventListener('click', () => {
            const isOpen = previewContent.style.display === 'block';
            previewContent.style.display = isOpen ? 'none' : 'block';
            previewToggle.textContent = isOpen ? '▶ Preview' : '▼ Preview';
            if (!isOpen) updatePreview();
        });
        
        // Close handlers
        const closeModal = () => {
            overlay.classList.remove('active');
            setTimeout(() => {
                if (container.parentNode) container.parentNode.removeChild(container);
            }, 200);
        };
        cancelBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
        const escapeHandler = (e) => {
            if (e.key === 'Escape') { closeModal(); document.removeEventListener('keydown', escapeHandler); }
        };
        document.addEventListener('keydown', escapeHandler);
        
        // Submit
        confirmBtn.addEventListener('click', async () => {
            const mode = dialog.querySelector('.js-mode-radio:checked').value;
            const formData = { 
                action: 'update_multiple_paths', 
                video_paths: paths,
                old_title: this.seriesData?.series_info?.db_title || '',
                source: 'series_details'
            };
            
            if (mode === 'title-only') {
                const newTitle = titleOnlyInput.value.trim();
                if (!newTitle) { this.showMessage('Error', 'Enter a title', 'error'); return; }
                formData.new_title = newTitle;
            } else {
                const baseTitle = bothTitleInput.value.trim();
                if (!baseTitle) { this.showMessage('Error', 'Enter a series title', 'error'); return; }
                const start = parseInt(bothStartInput.value) || 1;
                formData.new_title = baseTitle;
                formData.episode_ordered_names = paths.map((_, i) => {
                    const epNum = start + i;
                    return `EP${epNum.toString().padStart(2, '0')}`;
                });
            }
            
            confirmBtn.disabled = true;
            cancelBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="fetch-loading-spinner"></span>Updating...';
            
            try {
                const response = await fetch('/admin/series-update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify(formData)
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const result = await response.json();
                if (!result.success) throw new Error(result.error || 'Update failed');
                
                closeModal();
                this.showMessage('Success', result.message || 'Episodes updated!', 'success');
                setTimeout(() => location.reload(), 1200);
                
            } catch (error) {
                console.error('Edit episodes error:', error);
                this.showMessage('Error', error.message || 'Update failed', 'error');
                confirmBtn.disabled = false;
                cancelBtn.disabled = false;
                confirmBtn.innerHTML = 'Update Episodes';
            }
        });
        
        // Initial preview
        updatePreview();
        setTimeout(() => { titleOnlyInput.focus(); titleOnlyInput.select(); }, 100);
    }

    showResetEpisodesDialog() {
      const title = this.seriesData?.series_info?.db_title;

      const modalHtml = `
        <div class="fetch-modal-overlay active" id="reset-episodes-overlay">
          <div class="fetch-modal-dialog">
            <div class="fetch-modal-title">🗑️ Reset Episodes</div>
            <div class="fetch-modal-subtitle">This will reset all episodes for <strong>${this.escapeHtml(title)}</strong>. This action cannot be undone.</div>
            <div class="fetch-modal-buttons">
              <button class="fetch-modal-btn fetch-modal-btn-cancel" id="reset-episodes-cancel-btn">Cancel</button>
              <button class="fetch-modal-btn fetch-modal-btn-confirm" id="reset-episodes-confirm-btn" style="background:#e53935;">Reset Episodes</button>
            </div>
          </div>
        </div>
      `;

      const modalContainer = document.createElement('div');
      modalContainer.id = 'reset-episodes-container';
      modalContainer.innerHTML = modalHtml;
      document.body.appendChild(modalContainer);

      const overlay = document.getElementById('reset-episodes-overlay');
      const confirmBtn = document.getElementById('reset-episodes-confirm-btn');
      const cancelBtn = document.getElementById('reset-episodes-cancel-btn');

      const closeModal = () => {
        overlay.classList.remove('active');
        setTimeout(() => {
          const container = document.getElementById('reset-episodes-container');
          if (container?.parentNode) container.parentNode.removeChild(container);
        }, 200);
      };

      cancelBtn.addEventListener('click', closeModal);
      overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

      const escapeHandler = (e) => {
        if (e.key === 'Escape') { closeModal(); document.removeEventListener('keydown', escapeHandler); }
      };
      document.addEventListener('keydown', escapeHandler);

      confirmBtn.addEventListener('click', async () => {
        confirmBtn.disabled = true;
        cancelBtn.disabled = true;
        confirmBtn.innerHTML = '<span class="fetch-loading-spinner"></span>Resetting...';

        try {
          await this.resetSeriesEpisodes(title);
          closeModal();
          this.showMessage('Success', 'Episodes reset successfully!', 'success');
          setTimeout(() => location.reload(), 1500);
        } catch (error) {
          console.error('Reset episodes error:', error);
          this.showMessage('Error', error.message || 'Failed to reset episodes', 'error');
          confirmBtn.disabled = false;
          cancelBtn.disabled = false;
          confirmBtn.innerHTML = 'Reset Episodes';
        }
      });
    }

    async resetSeriesEpisodes(dbTitle) {
      const response = await fetch('/admin/series-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          action: 'reset_only_series_episodes',
          db_title: dbTitle,
          reason: 'reset_entry'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      if (!result.success) throw new Error(result.error || 'Reset episodes failed');
      return result;
    }

    showFetchMetadataDialog() {
      const title = this.seriesData?.series_info?.db_title || this.seriesData?.series_info?.title;
      const externalID = this.seriesData?.series_info?.external_id;
      const currentCategory = this.seriesData?.series_info?.category || 'anime';
      
      // Create modal HTML
      const modalHtml = `
        <div class="fetch-modal-overlay active" id="fetch-metadata-overlay">
          <div class="fetch-modal-dialog fetch-metadata-dialog">
            <div class="fetch-modal-title">🔄 Fetch Series Metadata</div>
            <div class="fetch-modal-subtitle">Update metadata for ${this.escapeHtml(title)}</div>
            
            <div class="fetch-modal-form">
              <div class="fetch-modal-form-group">
                <label class="fetch-modal-label">Search Title</label>
                <input 
                  type="text" 
                  class="fetch-modal-input" 
                  id="metadata-search-title" 
                  placeholder="Enter custom search title"
                  value="${this.escapeHtml(title)}"
                />
                <div class="fetch-modal-help">Enter the exact title to search for</div>
              </div>
              
              <div class="fetch-modal-form-group">
                <label class="fetch-modal-label">External ID (Optional)</label>
                <input 
                  type="number" 
                  class="fetch-modal-input" 
                  id="metadata-external-id" 
                  placeholder="e.g., 5114 (MyAnimeList ID)"
                  value="${this.escapeHtml(externalID)}"
                />
                <div class="fetch-modal-help">Leave empty to search by title</div>
              </div>
              
              <div class="fetch-modal-form-row">
                <div class="fetch-modal-form-group">
                  <label class="fetch-modal-label">Category</label>
                  <select class="fetch-modal-input" id="metadata-category">
                    <option value="anime" ${currentCategory === 'anime' ? 'selected' : ''}>Anime</option>
                    <option value="anime movies" ${currentCategory === 'anime movies' ? 'selected' : ''}>Anime Movies</option>
                    <option value="tv shows" ${currentCategory === 'tv shows' ? 'selected' : ''}>TV Shows</option>
                    <option value="movies" ${currentCategory === 'movies' ? 'selected' : ''}>Movies</option>
                    <option value="cartoons" ${currentCategory === 'cartoons' ? 'selected' : ''}>Cartoons</option>
                  </select>
                </div>
                
                <div class="fetch-modal-form-group">
                  <label class="fetch-modal-label">Use Cache</label>
                  <select class="fetch-modal-input" id="metadata-use-cache">
                    <option value="yes">Yes</option>
                    <option value="no">No (Fresh fetch)</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="fetch-modal-buttons">
              <button class="fetch-modal-btn fetch-modal-btn-cancel" id="metadata-cancel-btn">Cancel</button>
              <button class="fetch-modal-btn fetch-modal-btn-confirm" id="metadata-confirm-btn">Fetch Metadata</button>
            </div>
          </div>
        </div>
      `;
      
      // Add modal to page
      const body = document.body;
      const modalContainer = document.createElement('div');
      modalContainer.id = 'fetch-metadata-container';
      modalContainer.innerHTML = modalHtml;
      body.appendChild(modalContainer);
      
      // Get modal elements
      const overlay = document.getElementById('fetch-metadata-overlay');
      const searchTitleInput = document.getElementById('metadata-search-title');
      const externalIdInput = document.getElementById('metadata-external-id');
      const categorySelect = document.getElementById('metadata-category');
      const useCacheSelect = document.getElementById('metadata-use-cache');
      const confirmBtn = document.getElementById('metadata-confirm-btn');
      const cancelBtn = document.getElementById('metadata-cancel-btn');
      
      // Auto-focus input
      setTimeout(() => searchTitleInput.focus(), 100);
      
      // Cancel handler
      const closeModal = () => {
        overlay.classList.remove('active');
        setTimeout(() => {
          const container = document.getElementById('fetch-metadata-container');
          if (container && container.parentNode) {
            container.parentNode.removeChild(container);
          }
        }, 200);
      };
      
      cancelBtn.addEventListener('click', closeModal);
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
      });
      
      // Escape key to close
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          closeModal();
          document.removeEventListener('keydown', escapeHandler);
        }
      };
      document.addEventListener('keydown', escapeHandler);
      
      // Confirm handler
      confirmBtn.addEventListener('click', async () => {
        const searchTitle = searchTitleInput.value.trim();
        const externalId = externalIdInput.value.trim();
        const category = categorySelect.value;
        const useCache = useCacheSelect.value;
        
        // Validate - need either search title or external ID
        if (!searchTitle && !externalId) {
          this.showMessage('Error', 'Please enter a search title or external ID', 'error');
          return;
        }
        
        // Disable buttons and show loading
        confirmBtn.disabled = true;
        cancelBtn.disabled = true;
        searchTitleInput.disabled = true;
        externalIdInput.disabled = true;
        categorySelect.disabled = true;
        useCacheSelect.disabled = true;
        confirmBtn.innerHTML = '<span class="fetch-loading-spinner"></span>Fetching...';
        
        try {
          await this.fetchSeriesMetadata({
            searchTitle,
            externalId,
            category,
            useCache,
            dbTitle: title
          });
          
          closeModal();
          this.showMessage('Success', 'Metadata fetched successfully!', 'success');
          
          // Reload the page to show updated metadata
          setTimeout(() => {
            location.reload();
          }, 1500);
          
        } catch (error) {
          console.error('Fetch metadata error:', error);
          this.showMessage('Error', error.message || 'Failed to fetch metadata', 'error');
          
          // Re-enable form
          confirmBtn.disabled = false;
          cancelBtn.disabled = false;
          searchTitleInput.disabled = false;
          externalIdInput.disabled = false;
          categorySelect.disabled = false;
          useCacheSelect.disabled = false;
          confirmBtn.innerHTML = 'Fetch Metadata';
        }
      });
      
      // Enter key to confirm
      searchTitleInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          confirmBtn.click();
        }
      });
    }

    async fetchSeriesMetadata(options) {
      const { searchTitle, externalId, category, useCache, dbTitle } = options;
      
      const requestData = {
        db_title: dbTitle,
        suggested_title: searchTitle || "",
        series_type: category,
        use_cache: useCache,
        media_type: "video"
      };
      
      // Add external_id if provided
      if (externalId) {
        requestData.external_id = parseInt(externalId);
      }
      
      const response = await fetch('/fetch_series_metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || 
          `HTTP error! status: ${response.status}`
        );
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Metadata fetch failed');
      }
      
      return result;
    }

    showFetchMediaDialog(mode) {
      const title = this.seriesData?.series_info?.db_title;
      
      // Create modal HTML
      const modalHtml = `
        <div class="fetch-modal-overlay active" id="fetch-modal-overlay">
          <div class="fetch-modal-dialog">
            <div class="fetch-modal-title">${mode === 'poster' ? '🖼️ Fetch Poster' : '🎨 Fetch Fanart'}</div>
            <div class="fetch-modal-subtitle">Enter image URL/ or search word for ${this.escapeHtml(title)}. This image will be used as a backdrop for the series in the desktop client.</div>
            
            <div class="fetch-modal-form">
              <div class="fetch-modal-form-group">
                <label class="fetch-modal-label">Image URL/ Search Title</label>
                <input 
                  type="text" 
                  class="fetch-modal-input" 
                  id="fetch-url-input" 
                  placeholder="https://example.com/image.jpg OR title"
                  value="${this.escapeHtml(title)}"
                />
              </div>
            </div>
            
            <div class="fetch-modal-buttons">
              <button class="fetch-modal-btn fetch-modal-btn-cancel" id="fetch-cancel-btn">Cancel</button>
              <button class="fetch-modal-btn fetch-modal-btn-confirm" id="fetch-confirm-btn">Yes, Fetch</button>
            </div>
          </div>
        </div>
      `;
      
      // Add modal to page
      const body = document.body;
      const modalContainer = document.createElement('div');
      modalContainer.id = 'fetch-modal-container';
      modalContainer.innerHTML = modalHtml;
      body.appendChild(modalContainer);
      
      // Get modal elements
      const overlay = document.getElementById('fetch-modal-overlay');
      const urlInput = document.getElementById('fetch-url-input');
      const confirmBtn = document.getElementById('fetch-confirm-btn');
      const cancelBtn = document.getElementById('fetch-cancel-btn');
      
      // Auto-focus input
      setTimeout(() => urlInput.focus(), 100);
      
      // Cancel handler
      const closeModal = () => {
        overlay.classList.remove('active');
        setTimeout(() => {
          const container = document.getElementById('fetch-modal-container');
          if (container && container.parentNode) {
            container.parentNode.removeChild(container);
          }
        }, 200);
      };
      
      cancelBtn.addEventListener('click', closeModal);
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
      });
      
      // Escape key to close
      const escapeHandler = (e) => {
        if (e.key === 'Escape') {
          closeModal();
          document.removeEventListener('keydown', escapeHandler);
        }
      };
      document.addEventListener('keydown', escapeHandler);
      
      // Confirm handler
      confirmBtn.addEventListener('click', async () => {
        var url = urlInput.value.trim();
        
        // Validate URL
        if (!url) {
          url = title;
        }

        // Disable buttons and show loading
        confirmBtn.disabled = true;
        cancelBtn.disabled = true;
        urlInput.disabled = true;
        confirmBtn.innerHTML = '<span class="fetch-loading-spinner"></span>Fetching...';
        
        try {
          await this.fetchMediaContent(mode, url, title);
          closeModal();
          this.showMessage('Success', `${mode === 'poster' ? 'Poster' : 'Fanart'} fetch request submitted successfully!`, 'success');
        } catch (error) {
          console.error('Fetch error:', error);
          this.showMessage('Error', error.message || 'Failed to fetch media', 'error');
          confirmBtn.disabled = false;
          cancelBtn.disabled = false;
          urlInput.disabled = false;
          confirmBtn.innerHTML = 'Yes, Fetch';
        }
      });
      
      // Enter key to confirm
      urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          confirmBtn.click();
        }
      });
    }

    async fetchMediaContent(mode, url, title) {
      const response = await fetch('/fetch-posters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          title: title,
          url: url,
          mode: mode,  // 'poster' or 'fanart'
          site_option: 'video'
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || 
          (response.status === 400 ? 'Invalid URL or request' : `HTTP error! status: ${response.status}`)
        );
      }

      return { success: true };
    }

    // UPDATED: fetchSeriesMetadata method with series_sub_type:
    async fetchSeriesMetadata(options) {
      const { searchTitle, externalId, category, subType, useCache, dbTitle } = options;
      
      const requestData = {
        db_title: dbTitle,
        suggested_title: searchTitle || "",
        series_type: category,
        use_cache: useCache,
        media_type: "video"
      };
      
      // Add external_id if provided
      if (externalId) {
        requestData.external_id = parseInt(externalId);
      }
      
      // Add series_sub_type if provided
      if (subType) {
        requestData.series_sub_type = subType;
      }
      
      const response = await fetch('/fetch_series_metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || 
          `HTTP error! status: ${response.status}`
        );
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Metadata fetch failed');
      }
      
      return result;
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
                <button class="poster-edit-btn" id="poster-edit-btn" aria-label="Change poster image" title="Change poster image">
                    <span class="poster-edit-icon">✏️</span>
                    <span class="poster-edit-text">Change Image</span>
                </button>
            </div>
        `;
    }

    capitalizeWords(str) {
        return str.split(' ')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
              .join(' ');
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
            { label: 'Label', value: this.capitalizeWords(info.labels || 'unknown') },
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
            
            <!-- Label Selector Row -->
            <div class="info-row label-selector-row">
              <span class="info-label"></span>
            </div>
            
            <div class="label-selector-wrapper">
              <!-- Mobile: Dropdown -->
              <select id="series-label-select" class="label-select-mobile" data-series-id="${this.seriesId}">
                <option value="">Select Status</option>
                <option value="watching">📺 Watching</option>
                <option value="plan to watch">📋 Plan to Watch</option>
                <option value="completed">✅ Completed</option>
                <option value="incomplete">⏸️  Incomplete</option>
                <option value="dropped">❌ Dropped</option>
                <option value="interesting">⭐ Interesting</option>
              </select>
              
              <!-- Desktop: Buttons -->
              <div class="label-buttons-desktop">
                <button class="label-btn-compact" data-label="watching" data-series-id="${this.seriesId}" title="Currently watching">📺</button>
                <button class="label-btn-compact" data-label="plan to watch" data-series-id="${this.seriesId}" title="Plan to watch">📋</button>
                <button class="label-btn-compact" data-label="completed" data-series-id="${this.seriesId}" title="Completed">✅</button>
                <button class="label-btn-compact" data-label="incomplete" data-series-id="${this.seriesId}" title="Incomplete">⏸️</button>
                <button class="label-btn-compact" data-label="dropped" data-series-id="${this.seriesId}" title="Dropped">❌</button>
                <button class="label-btn-compact" data-label="interesting" data-series-id="${this.seriesId}" title="Interesting">⭐</button>
              </div>
            </div>
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
                        <br>
                        <button class="fetch-btn" id="delete-stale-entry-btn" title="Delete stale entry to refresh data">
                            <span class="fetch-icon">🗑️</span>
                            <span class="fetch-text">Delete Stale Entry</span>
                        </button>
                    </div>
                </div>
            `;
        }
        
        const episodeItems = episodes.map((episode, index) => {
            const episodeNumber = (episode['epn-number'] || index) + 1;
            const episodeName = episode.name || `Episode ${episodeNumber}`;
            const imageUrl = episode['image-url'] || '';
            const watched = episode.watched || false;
            const episodePath = episode.path || ''; 
            
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
                    
                    <div class="episode-actions">
                      ${imageUrl ? `<button class="thumbnail-preview-btn" data-episode="${episodeNumber}">Preview 🔄</button>` : ''}
                      <button class="episode-watch-btn ${watched ? 'watched' : ''}" data-episode="${episodeNumber}" data-episode-path="${this.escapeHtml(episodePath)}" title="${watched ? 'Mark as unwatched' : 'Mark as watched'}" aria-label="${watched ? 'Mark as unwatched' : 'Mark as watched'}">
                        ✓
                      </button>
                    </div>
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
        this.setupEpisodeWatchButtons();
    }

    setupDeleteStaleEntryHandler() {
        const btn = document.getElementById('delete-stale-entry-btn');
        if (!btn) return;

        btn.addEventListener('click', async () => {
            const titleName = this.seriesData?.series_info?.db_title;

            btn.disabled = true;
            btn.innerHTML = '<span class="fetch-icon">⏳</span><span class="fetch-text">Deleting...</span>';

            this.showMessage('Info', 'Deleting stale entry... This may take a moment.', 'info');

            try {
                const requestData = {
                    action: "delete_series_info",
                    db_title: titleName,
                    reason: "stale_entry"
                };

                const response = await fetch('/admin/series-update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify(requestData)
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                if (!result.success) throw new Error(result.error || 'Delete failed');

                this.showMessage('Success', 'Stale entry deleted successfully!', 'success');
                setTimeout(() => window.location.href = '/browse', 1500);

            } catch (error) {
                console.error('Delete stale entry error:', error);
                this.showMessage('Error', error.message || 'Failed to delete entry', 'error');
                btn.disabled = false;
                btn.innerHTML = '<span class="fetch-icon">🗑️</span><span class="fetch-text">Delete Stale Entry</span>';
            }
        });
    }

    setupThumbnailPreviews() {
        const previewBtns = document.querySelectorAll('.thumbnail-preview-btn');

        previewBtns.forEach(btn => {
            let currentInterval = 0; // Start at 0, will increment to 5 on first click

            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); // Prevent episode click

                const episodeActions = btn.parentElement;
                const episodeItem = episodeActions.closest('.episode-item');
                const img = episodeItem.querySelector('.episode-thumb-img');

                if (!img) {
                    console.warn('Image not found');
                    return;
                } 

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

    setupEpisodeWatchButtons() {
      const watchBtns = document.querySelectorAll('.episode-watch-btn');
      
      watchBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();  // Don't trigger episode play
          
          const episodeNumber = btn.dataset.episode;
          const episodePath = btn.dataset.episodePath;
          const isWatched = btn.dataset.watched === 'true' || btn.classList.contains('watched');
          
          this.toggleEpisodeWatch(episodeNumber, episodePath, isWatched);
        });
      });
    }

    // Toggle watch status
    async toggleEpisodeWatch(episodeNumber, episodePath, currentlyWatched) {
      const btn = document.querySelector(`.episode-watch-btn[data-episode="${episodeNumber}"]`);
      const newStatus = !currentlyWatched;  // Toggle: watched -> unwatched, unwatched -> watched
      
      // Show loading state
      btn.classList.add('loading');
      btn.disabled = true;
      
      try {
        const result = await this.toggleEpisodeWatchStatus(episodePath, newStatus);
        
        // Update UI
        this.updateEpisodeWatchUI(episodeNumber, newStatus, result.epName);
        
        // Show success message
        const message = newStatus ? 'Marked as watched!' : 'Marked as unwatched!';
        this.showMessage('Success', message, 'success');
        
      } catch (error) {
        console.error('Error updating episode watch status:', error);
        this.showMessage('Error', error.message || 'Failed to update watch status', 'error');
        
      } finally {
        // Remove loading state
        btn.classList.remove('loading');
        btn.disabled = false;
      }
    }

    // API call to toggle episode watch status
    async toggleEpisodeWatchStatus(episodePath, watched) {
      const response = await fetch('/api/toggle-episode-watch-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          path: episodePath,
          watched: watched
        })
      });
      
      if (!response.ok) {
        throw new Error(
          response.status === 400 ? 'Invalid request' : `HTTP error! status: ${response.status}`
        );
      }
      
      // 200 status = success
      const data = await response.json();
      return { success: true, epName: data.ep_name || null};
    }

    // Update UI after successful toggle
    
    updateEpisodeWatchUI(episodeNumber, watched, epName) {
      const btn = document.querySelector(`.episode-watch-btn[data-episode="${episodeNumber}"]`);
      const episodeItem = document.querySelector(`.episode-item[data-episode-number="${episodeNumber}"]`);
      const episodeTitle = episodeItem?.querySelector('.episode-title');

      if (epName && episodeTitle) {
        episodeTitle.textContent = this.escapeHtml(epName);
      }
      
      if (btn) {
        // Checkmark always visible, just change color/styling
        btn.textContent = '✓';
        btn.title = watched ? 'Mark as unwatched' : 'Mark as watched';
        btn.setAttribute('aria-label', watched ? 'Mark as unwatched' : 'Mark as watched');
        
        // Update button styling
        if (watched) {
          btn.classList.add('watched');
        } else {
          btn.classList.remove('watched');
        }
        
        // Update data attribute
        btn.dataset.watched = watched ? 'true' : 'false';
      }
      
      if (episodeItem) {
        // Update episode item data attribute
        episodeItem.dataset.watched = watched ? 'true' : 'false';
      }
    }

    playEpisode(episodeElement) {
        if (this.editMode) return;

        const episodeNumber = episodeElement.dataset.episodeNumber;
        const seriesId = episodeElement.dataset.seriesId;
        
        if (!episodeNumber || !seriesId) {
            console.error('Missing episode or series information');
            this.showMessage('Error', 'Unable to play episode', 'error');
            return;
        }

        localStorage.setItem('selectedEpisodeNumber', episodeNumber);
        
        // Navigate to series player page
        window.location.href = `/series/${seriesId}/playercontrol`;
    }
    
    setupBackButton() {
        const backBtn = document.getElementById('back-btn');

        if (backBtn) {
            backBtn.addEventListener('click', () => {

                const returnUrl = localStorage.getItem('browseReturnUrl');

                if (returnUrl) {
                    // Remove the stored values
                    localStorage.removeItem('browseReturnUrl');
                    const scrollPos = localStorage.getItem('browseScrollPosition');
                    localStorage.removeItem('browseScrollPosition');

                    // Navigate back
                    window.location.href = returnUrl;

                    // Restore scroll position after page loads
                    if (scrollPos) {
                        window.addEventListener('load', () => {
                            window.scrollTo(0, parseInt(scrollPos));
                        });
                    }
                } else {
                    window.location.href = `/browse`;
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
