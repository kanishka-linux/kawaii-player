class AdminPanel {
    constructor() {
        this.titles = [];
        this.selectedTitles = new Set();
        this.selectedEpisodes = new Set();
        this.currentTitle = null;
        this.currentSearchTerm = '';
        this.currentSeriesInfoFilter = 'all';
        this.currentEditPaths = null;
        this.currentHighlightedIndex = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTitles();

        // Restore to saved index after page load
        setTimeout(() => {
            this.restoreToSavedIndex();
        }, 2000);
    }
    
    handleBulkMetadata() {
        const selectedTitles = Array.from(this.selectedTitles);
        if (selectedTitles.length === 0) {
            alert('Please select at least one title for metadata fetching.');
            return;
        }

        // Convert directory hashes to title objects
        const selectedTitleObjects = selectedTitles.map(hash => {
            const title = this.titles.find(t => t.directory_hash === hash);
            return title ? title.title : null;
        }).filter(title => title !== null);

        this.openBulkMetadataModal(selectedTitleObjects);
    }

    handleUpdateCollection() {
        // Show confirmation dialog
        const confirmed = confirm(
            'This will scan for new videos and update the collection.\n\n' +
            'This process may take some time depending on your collection size.\n\n' +
            'Do you want to continue?'
        );
        
        if (!confirmed) {
            return;
        }
        
        this.updateVideoCollection();
    }

    setupEventListeners() {
        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.currentSearchTerm = e.target.value;
            this.applyFilters();
        });

        document.getElementById('search-btn').addEventListener('click', () => {
            const searchTerm = document.getElementById('search-input').value;
            this.currentSearchTerm = searchTerm;
            this.applyFilters();
        });

        document.getElementById('clear-btn').addEventListener('click', () => {
            document.getElementById('search-input').value = '';
            this.currentSearchTerm = '';
            this.applyFilters();
        });

        // Bulk actions
        document.getElementById('select-all-btn').addEventListener('click', () => {
            this.selectAllTitles();
        });

        document.getElementById('deselect-all-btn').addEventListener('click', () => {
            this.deselectAllTitles();
        });

        document.getElementById('bulk-edit-btn').addEventListener('click', () => {
            this.handleBulkEdit();
        });

        // Details panel
        document.getElementById('close-details').addEventListener('click', () => {
            this.closeDetailsPanel();
        });

        // Enter key for search
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.currentSearchTerm = e.target.value;
                this.applyFilters();
            }
        });

        // For bulk-metadata fetch
        document.getElementById('bulk-metadata-btn').addEventListener('click', () => {
            this.handleBulkMetadata();
        });

        // Add this new event listener for update collection
        document.getElementById('update-collection-btn').addEventListener('click', () => {
            this.handleUpdateCollection();
        });

        // Add this new event listener for no info filter
        document.getElementById('filter-no-info-btn').addEventListener('click', () => {
            this.toggleNoInfoFilter();
        });

        const mobileBackBtn = document.getElementById('mobile-back-btn');
        if (mobileBackBtn) {
            mobileBackBtn.addEventListener('click', () => {
                this.closeDetailsPanel();
            });
        }
    }

    setupTitleEventListeners() {
        // Handle checkbox changes
        document.querySelectorAll('.title-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (event) => {
                const hash = event.target.dataset.hash;
                const titleElement = event.target.closest('.title-item');
                const title = titleElement.dataset.title;
                this.toggleTitleSelection(hash, title);
            });
        });

        // Handle title info clicks
        document.querySelectorAll('.title-info').forEach(titleInfo => {
            titleInfo.addEventListener('click', (event) => {
                const index = parseInt(titleInfo.dataset.index);
                const hash = titleInfo.dataset.hash;
                const titleElement = titleInfo.closest('.title-item');
                const title = titleElement.dataset.title;
                this.saveTitleIndexAndShowDetails(index, hash, title);
            });
        });

        // Handle edit button clicks
        document.querySelectorAll('.btn-edit').forEach(button => {
            button.addEventListener('click', (event) => {
                event.stopPropagation();
                const index = parseInt(button.dataset.index);
                const hash = button.dataset.hash;
                const titleElement = button.closest('.title-item');
                const title = titleElement.dataset.title;
                this.saveIndexAndEditTitle(index, hash, title);
            });
        });
    }

    closeDetailsPanel() {
        console.log("closing...")
        const detailsPanel = document.getElementById('details-panel');
        detailsPanel.classList.remove('active');
        
        // Restore body scroll on mobile
        if (window.innerWidth <= 768) {
            document.body.style.overflow = '';
        }
        
        this.currentTitle = null;
        this.selectedEpisodes.clear();

        // Restore to saved index
        setTimeout(() => {
            this.restoreToSavedIndex();
        }, 350);
        
        setTimeout(() => {
            if (!detailsPanel.classList.contains('active')) {
                const detailsContent = document.getElementById('details-content');
                detailsContent.innerHTML = '';
            }
        }, 300);
    }

    toggleNoInfoFilter() {
        if (this.currentSeriesInfoFilter === 'no-info') {
            // If already filtering by no-info, reset to all
            this.currentSeriesInfoFilter = 'all';
            this.updateNoInfoButton(false);
        } else {
            // Filter by no-info
            this.currentSeriesInfoFilter = 'no-info';
            this.updateNoInfoButton(true);
        }
        
        this.applyFilters();
        this.showFilterStatus();
    }

    // Enhanced version that shows count in button text
    updateNoInfoButton(isActive) {
        const button = document.getElementById('filter-no-info-btn');
        if (button) {
            const noInfoCount = this.titles.filter(t => !t.has_series_info).length;
            
            if (isActive) {
                button.classList.add('active');
                button.textContent = 'Show All';
            } else {
                button.classList.remove('active');
                button.textContent = `No Info Only (${noInfoCount})`;
            }
        }
    }

    // Update the existing applyFilters method
    applyFilters() {
        let filtered = [...this.titles];
        
        // Apply search filter
        if (this.currentSearchTerm) {
            filtered = filtered.filter(title =>
                title.title.toLowerCase().includes(this.currentSearchTerm.toLowerCase())
            );
        }
        
        // Apply series info filter
        if (this.currentSeriesInfoFilter === 'has-info') {
            filtered = filtered.filter(title => title.has_series_info === true);
        } else if (this.currentSeriesInfoFilter === 'no-info') {
            filtered = filtered.filter(title => title.has_series_info === false);
        }
        
        this.renderTitles(filtered);
        this.updateLabelStyles();
    }

    // Update the existing showFilterStatus method
    showFilterStatus() {
        const totalCount = this.titles.length;
        const hasInfoCount = this.titles.filter(t => t.has_series_info).length;
        const noInfoCount = totalCount - hasInfoCount;
        
        let message = '';
        if (this.currentSeriesInfoFilter === 'has-info') {
            message = `Showing only titles WITH series info (${hasInfoCount} of ${totalCount})`;
        } else if (this.currentSeriesInfoFilter === 'no-info') {
            message = `Showing only titles WITHOUT series info (${noInfoCount} of ${totalCount})`;
        }
        
        if (message) {
            this.showFilterMessage(message);
        } else {
            this.hideFilterMessage();
        }
    }

    showFilterMessage(message) {
        let statusDiv = document.getElementById('filter-status-message');
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'filter-status-message';
            statusDiv.className = 'filter-status-message';
            
            const controlsSection = document.querySelector('.controls');
            controlsSection.appendChild(statusDiv);
        }
        
        statusDiv.style.display = 'flex';
        statusDiv.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
            <button class="clear-filter-btn" onclick="admin.clearSeriesInfoFilter()">Clear Filter</button>
        `;
    }

    hideFilterMessage() {
        const statusDiv = document.getElementById('filter-status-message');
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }

    // Update the existing clearSeriesInfoFilter method
    clearSeriesInfoFilter() {
        this.currentSeriesInfoFilter = 'all';
        this.updateNoInfoButton(false);
        this.applyFilters();
        this.hideFilterMessage();
        this.updateLabelStyles();
    }

    updateLabelStyles() {
        // This method can be used to update visual indicators if needed
    }

    // Update the existing toggleSeriesInfoFilter method (for clickable labels)
    toggleSeriesInfoFilter(hasInfo) {
        if (hasInfo) {
            // Clicked on "Has Series Info"
            if (this.currentSeriesInfoFilter === 'has-info') {
                this.currentSeriesInfoFilter = 'all';
                this.updateNoInfoButton(false);
            } else {
                this.currentSeriesInfoFilter = 'has-info';
                this.updateNoInfoButton(false);
            }
        } else {
            // Clicked on "No Series Info"
            if (this.currentSeriesInfoFilter === 'no-info') {
                this.currentSeriesInfoFilter = 'all';
                this.updateNoInfoButton(false);
            } else {
                this.currentSeriesInfoFilter = 'no-info';
                this.updateNoInfoButton(true);
            }
        }
        
        this.applyFilters();
        this.showFilterStatus();
    }

    // Enhanced version with better progress tracking
    async updateVideoCollection() {
        try {
            this.showUpdateProgress('Updating video collection... This may take a while.');
            
            // Change to GET request
            const response = await fetch('/update_video', {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error(`Update failed: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.text(); // /update_video likely returns text
            
            this.showUpdateProgress('Collection update completed! Reloading data...');
            
            // Small delay to show completion message
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Reload the titles after update
            await this.loadTitles();
            
            this.showSuccessMessage('Video collection updated successfully!');
            
        } catch (error) {
            console.error('Update collection error:', error);
            this.showErrorMessage('Failed to update collection: ' + error.message);
        }
    }

    // Add enhanced progress display methods
    showCollectionUpdateProgress(message) {
        const existing = document.getElementById('collection-update-progress');
        if (existing) existing.remove();
        
        const progressDiv = document.createElement('div');
        progressDiv.id = 'collection-update-progress';
        progressDiv.className = 'collection-update-progress';
        progressDiv.innerHTML = `
            <div class="progress-content">
                <div class="progress-spinner"></div>
                <div class="progress-message">${this.escapeHtml(message)}</div>
                <div class="progress-note">Please wait, this process may take several minutes...</div>
            </div>
        `;
        
        document.body.appendChild(progressDiv);
    }

    hideCollectionUpdateProgress() {
        const progress = document.getElementById('collection-update-progress');
        if (progress) {
            progress.remove();
        }
    }

    async loadTitles() {
        try {
            this.showLoading();
            
            const response = await fetch('/admin-data');
            if (!response.ok) {
                throw new Error(`Failed to load titles: ${response.status} ${response.statusText}`);
            }
            
            this.titles = await response.json();
            
            if (this.titles.error) {
                throw new Error(this.titles.error);
            }
            
            this.renderTitles();
            this.updateNoInfoButton(this.currentSeriesInfoFilter === 'no-info');
        } catch (error) {
            this.showError('Failed to load titles: ' + error.message);
        }
    }

    // UPDATED: Render titles with directory_hash in click handlers
    
    renderTitles(titlesToRender = null) {
        const container = document.getElementById('titles-list');
        const titles = titlesToRender || this.titles;

        if (titles.length === 0) {
            container.innerHTML = '<div class="loading">No titles found</div>';
            return;
        }

        container.innerHTML = titles.map((title, index) => `
            <div class="title-item" 
                 data-title="${this.escapeHtml(title.title)}" 
                 data-hash="${this.escapeHtml(title.directory_hash)}" 
                 data-index="${index}" 
                 id="title-index-${index}">
                <input type="checkbox" class="title-checkbox" 
                       ${this.selectedTitles.has(title.directory_hash) ? 'checked' : ''}
                       data-hash="${this.escapeHtml(title.directory_hash)}">
                
                <div class="title-info" 
                     data-index="${index}" 
                     data-hash="${this.escapeHtml(title.directory_hash)}">
                    <div class="title-name">${this.escapeHtml(title.title)}</div>
                    <div class="title-meta">
                        <span class="episode-count">${title.episode_count} episodes</span>
                        <span class="series-indicator ${title.has_series_info ? 'has-series' : 'no-series'}">
                            ${title.has_series_info ? 'Has Series Info' : 'No Series Info'}
                        </span>
                    </div>
                </div>
                
                <div class="title-actions">
                    <button class="btn btn-edit" 
                            data-index="${index}" 
                            data-hash="${this.escapeHtml(title.directory_hash)}">
                        Edit
                    </button>
                </div>
            </div>
        `).join('');

        this.setupTitleEventListeners();
        this.updateBulkEditButton();
    }

    // Save title index for restoration
    saveCurrentIndex(index) {
        console.log('=== SAVING TITLE INDEX ===');
        console.log('Saving index:', index);
        
        localStorage.setItem('adminReturnToIndex', index.toString());
        localStorage.setItem('adminShouldScrollToIndex', 'true');
        
        console.log('Index saved to localStorage');
        console.log('==========================');
    }

    // Restore and scroll to saved index
    restoreToSavedIndex() {
        console.log('=== RESTORING TO SAVED INDEX ===');
        
        const shouldScroll = localStorage.getItem('adminShouldScrollToIndex');
        const savedIndex = localStorage.getItem('adminReturnToIndex');
        
        console.log('Should scroll:', shouldScroll);
        console.log('Saved index:', savedIndex);
        
        if (shouldScroll === 'true' && savedIndex !== null) {
            const index = parseInt(savedIndex);
            console.log('Scrolling to index:', index);
            
            this.scrollToIndex(index);
            //this.clearSavedIndex();
            return true;
        }
        
        console.log('No saved index to restore');
        return false;
    }

    // Scroll to specific index within titles container with proper offset
    
    scrollToIndex(index) {
        console.log('Scrolling to index:', index);
        
        const titleElement = document.getElementById(`title-index-${index}`);
        const titlesContainer = document.getElementById('titles-list');
        
        if (titleElement && titlesContainer) {
            const elementTop = titleElement.offsetTop;
            const bulkEditHeight = 60;
            const additionalOffset = 20;
            const totalOffset = bulkEditHeight + additionalOffset;
            
            titlesContainer.scrollTo({
                top: Math.max(0, elementTop - totalOffset),
                behavior: 'smooth'
            });
            
            // Highlight by index (clears previous automatically)
            this.highlightElementByIndex(index);
        }
    }

    // Clear saved index
    clearSavedIndex() {
        console.log('Clearing saved index from localStorage');
        localStorage.removeItem('adminReturnToIndex');
        localStorage.removeItem('adminShouldScrollToIndex');
    }

    // Add highlight effect to element
    
    // Highlight element by index
    highlightElementByIndex(index) {
        console.log('=== HIGHLIGHTING BY INDEX ===');
        console.log('Previous highlighted index:', this.currentHighlightedIndex);
        console.log('New index to highlight:', index);
        
        // Clear previous highlight
        this.clearPreviousHighlight();
        
        // Find and highlight new element
        const element = document.getElementById(`title-index-${index}`);
        if (element) {
            // Store the new highlighted index
            this.currentHighlightedIndex = index;
            
            // Apply highlight
            element.style.backgroundColor = '#e3f2fd';
            element.style.transition = 'background-color 0.3s ease';
            
            console.log('Highlight applied to index:', index);
        } else {
            console.warn('Element not found for index:', index);
        }
        
        console.log('=============================');
    }

    // Clear all existing highlights
    clearAllHighlights() {
        console.log("clear high..")
        if (this.currentHighlightedElement) {
            this.currentHighlightedElement.style.backgroundColor = '';
            this.currentHighlightedElement.style.transition = '';
            this.currentHighlightedElement = null;
        }
    }

    // Clear highlight from previous index
    clearPreviousHighlight() {
        console.log('Clearing previous highlight');
        
        if (this.currentHighlightedIndex !== null) {
            console.log('Clearing highlight from index:', this.currentHighlightedIndex);
            
            const previousElement = document.getElementById(`title-index-${this.currentHighlightedIndex}`);
            if (previousElement) {
                previousElement.style.backgroundColor = '';
                previousElement.style.transition = '';
                console.log('Previous highlight cleared');
            } else {
                console.warn('Previous highlighted element not found for index:', this.currentHighlightedIndex);
            }
        }
        
        this.currentHighlightedIndex = null;
    }

    // Save index and show details
    saveTitleIndexAndShowDetails(index, directoryHash, titleName) {
        this.saveCurrentIndex(index);

        // Highlight the clicked element (stays until another click)
        const titleElement = document.getElementById(`title-index-${index}`);
        if (titleElement) {
            this.highlightElementByIndex(index);
        }

        this.showTitleDetails(directoryHash, titleName);
    }

    // Save index and edit title
    saveIndexAndEditTitle(index, directoryHash, titleName) {
        this.saveCurrentIndex(index);
        this.highlightElementByIndex(index);
        this.editTitle(directoryHash, titleName);
    }

    // UPDATED: Toggle title selection using directory_hash
    toggleTitleSelection(directoryHash, titleName) {
        if (this.selectedTitles.has(directoryHash)) {
            this.selectedTitles.delete(directoryHash);
        } else {
            this.selectedTitles.add(directoryHash);
        }
        this.updateBulkEditButton();
        this.updateTitleItemSelection(directoryHash);
    }

    updateTitleItemSelection(directoryHash) {
        const titleItem = document.querySelector(`[data-hash="${this.escapeHtml(directoryHash)}"]`);
        if (titleItem) {
            if (this.selectedTitles.has(directoryHash)) {
                titleItem.classList.add('selected');
            } else {
                titleItem.classList.remove('selected');
            }
        }
    }

    selectAllTitles() {
        const visibleTitles = document.querySelectorAll('.title-item');
        visibleTitles.forEach(item => {
            const directoryHash = item.dataset.hash;
            this.selectedTitles.add(directoryHash);
            const checkbox = item.querySelector('.title-checkbox');
            checkbox.checked = true;
            item.classList.add('selected');
        });
        this.updateBulkEditButton();
    }

    deselectAllTitles() {
        this.selectedTitles.clear();
        document.querySelectorAll('.title-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('.title-item').forEach(item => {
            item.classList.remove('selected');
        });
        this.updateBulkEditButton();
    }

    getCategorySeriesType(category) {
        const categoryMapping = {
            'anime': 'anime',
            'tv': 'tv',
            'movies': 'movie',
            'cartoons': 'cartoon'
        };
        return categoryMapping[category] || 'anime';
    }

    // Add this helper method for closing bulk metadata modal
    closeBulkMetadataModal() {
        const modal = document.getElementById('metadata-modal');
        if (modal) {
            modal.remove();
        }
    }

    
        updateBulkEditButton() {
        const bulkEditBtn = document.getElementById('bulk-edit-btn');
        const bulkMetadataBtn = document.getElementById('bulk-metadata-btn');
        const selectedCount = this.selectedTitles.size;
        
        if (selectedCount > 0) {
            bulkEditBtn.disabled = false;
            bulkEditBtn.textContent = `Bulk Edit (${selectedCount})`;
            
            // Add this for bulk metadata button
            if (bulkMetadataBtn) {
                bulkMetadataBtn.disabled = false;
                bulkMetadataBtn.textContent = `Fetch Metadata (${selectedCount})`;
            }
        } else {
            bulkEditBtn.disabled = true;
            bulkEditBtn.textContent = 'Bulk Edit';
            
            // Add this for bulk metadata button
            if (bulkMetadataBtn) {
                bulkMetadataBtn.disabled = true;
                bulkMetadataBtn.textContent = 'Fetch Metadata';
            }
        }
    }

    // UPDATED: Show title details using directory_hash as unique identifier
    async showTitleDetails(directoryHash, titleName = null) {
        // Find title by directory_hash (unique identifier)
        const title = this.titles.find(t => t.directory_hash === directoryHash);
        if (!title) {
            console.error('Title not found with directory_hash:', directoryHash);
            return;
        }

        // Use the actual title from the found object
        const actualTitleName = title.title;
        console.log('Showing details for title:', actualTitleName, 'hash:', directoryHash); // Debug log

        this.currentTitle = title;
        
        // Show the panel immediately with loading state
        document.getElementById('details-title').textContent = `${actualTitleName} - Details`;
        document.getElementById('details-panel').classList.add('active');
        
        // Show loading state in details content
        const detailsContent = document.getElementById('details-content');
        detailsContent.innerHTML = this.generateLoadingDetailsHTML();
        
        try {
            // UPDATED: Use POST request with title and directory_hash in body
            const requestBody = {
                title: actualTitleName,
                directory_hash: directoryHash
            };
            
            console.log('POST request body:', requestBody); // Debug log
            
            const response = await fetch('/title-details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            console.log('Response status:', response.status); // Debug log
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Get and log the raw response
            const responseText = await response.text();
            console.log('Raw response:', responseText); // Debug log
            
            // Parse JSON
            let detailsData;
            try {
                detailsData = JSON.parse(responseText);
                console.log('Parsed details data:', detailsData); // Debug log
            } catch (parseError) {
                console.error('JSON parse error:', parseError);
                throw new Error(`Invalid JSON response: ${parseError.message}`);
            }
            
            if (detailsData.error) {
                throw new Error(detailsData.error);
            }
            
            // Generate and display the details HTML with fetched data
            const generatedHTML = this.generateDetailsHTML(detailsData);
            console.log('Generated HTML length:', generatedHTML.length); // Debug log
            
            detailsContent.innerHTML = generatedHTML;
            
            // Setup episode selection listeners
            this.setupEpisodeSelectionListeners();
            
            console.log('Details panel updated successfully'); // Debug log
            
        } catch (error) {
            console.error('Error loading title details:', error);
            detailsContent.innerHTML = this.generateErrorDetailsHTML(error.message);
        }

        const mobileBackBtn = document.getElementById('mobile-back-btn');
        if (mobileBackBtn) {
            mobileBackBtn.addEventListener('click', () => {
                this.closeDetailsPanel();
            });
        }
    }

    // Generate loading state HTML
    generateLoadingDetailsHTML() {
        return `
            <div class="details-loading">
                <h3>Loading Details...</h3>
                <div class="loading-spinner"></div>
                <p>Fetching episode information...</p>
            </div>
        `;
    }

    // Generate error state HTML
    generateErrorDetailsHTML(errorMessage) {
        return `
            <div class="details-error">
                <h3>Error Loading Details</h3>
                <p>Failed to load episode details: ${this.escapeHtml(errorMessage)}</p>
                <button class="btn btn-primary" onclick="admin.showTitleDetails('${this.escapeHtml(this.currentTitle?.directory_hash || '')}', '${this.escapeHtml(this.currentTitle?.title || '')}')">
                    Retry
                </button>
            </div>
        `;
    }

    setupEpisodeSelectionListeners() {
        // Add event listeners for episode checkboxes
        document.querySelectorAll('.episode-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const path = e.target.dataset.path;
                if (e.target.checked) {
                    this.selectedEpisodes.add(path);
                } else {
                    this.selectedEpisodes.delete(path);
                }
                this.updateSelectionUI();
            });
        });
    }

    updateSelectionUI() {
        const selectedCount = this.selectedEpisodes.size;
        const editButton = document.querySelector('.episode-controls .btn-primary');
        if (editButton) {
            if (selectedCount > 0) {
                editButton.textContent = `Edit Selected (${selectedCount})`;
                editButton.disabled = false;
            } else {
                editButton.textContent = 'Edit Selected';
                editButton.disabled = true;
            }
        }
    }

    // UPDATED: Generate details HTML to match your CSS structure
    generateDetailsHTML(detailsData) {
        console.log('Generating HTML for data:', detailsData); // Debug log
        
        let html = '';

        // Section 1: Title Only (matches your .details-section)
        html += `
            <div class="details-section">
                <h4>${this.escapeHtml(detailsData.title || 'Unknown Title')}</h4>
            </div>
        `;

        // Section 2: Episodes (matches your .details-section structure)
        html += `
            <div class="details-section">
                <h4>Episodes</h4>
                <div class="episode-controls">
                    <button class="btn btn-small btn-secondary" onclick="admin.selectAllEpisodes('${this.escapeHtml(detailsData.title)}')">Select All</button>
                    <button class="btn btn-small btn-secondary" onclick="admin.deselectAllEpisodes('${this.escapeHtml(detailsData.title)}')">Deselect All</button>
                    <button class="btn btn-small btn-primary" onclick="admin.editMultiplePaths()" disabled>Edit Selected</button>
                </div>
                <div class="episode-list">
        `;

        // Handle episodes data - check multiple possible formats
        let episodes = [];
        if (detailsData.episodes && Array.isArray(detailsData.episodes)) {
            episodes = detailsData.episodes;
        } else if (detailsData.videos && Array.isArray(detailsData.videos)) {
            episodes = detailsData.videos;
        } else if (detailsData.episode_list && Array.isArray(detailsData.episode_list)) {
            episodes = detailsData.episode_list;
        }

        console.log('Episodes to display:', episodes); // Debug log

        if (episodes && episodes.length > 0) {
            episodes.forEach((episode, index) => {
                const episodePath = episode.path || episode.file_path || episode.video_path || `unknown_path_${index}`;
                const episodeTitle = episode.title || episode.name || episode.filename || `Episode ${index + 1}`;
                
                html += `
                    <div class="episode-item">
                        <input type="checkbox" class="episode-checkbox" data-path="${this.escapeHtml(episodePath)}">
                        <div class="episode-details">
                            <div class="episode-name">${this.escapeHtml(episodeTitle)}</div>
                            <div class="episode-path">${this.escapeHtml(episodePath)}</div>
                        </div>
                        <div class="episode-actions">
                            <button class="btn btn-small btn-edit" onclick="admin.editSinglePath('${this.escapeHtml(episodePath)}', '${this.escapeHtml(episodeTitle)}')">
                                Edit
                            </button>
                        </div>
                    </div>
                `;
            });
        } else {
            html += '<div class="no-episodes">No episodes found</div>';
        }

        html += `
                </div>
            </div>
        `;

        // Section 3: Series Information (FIXED to match your CSS)
        html += `
            <div class="details-section">
                <h4>Series Information</h4>
        `;

        console.log('Series info check:', {
            has_series_info: detailsData.has_series_info,
            series_info: detailsData.series_info
        }); // Debug log

        if (detailsData.series_info) {
            const series = detailsData.series_info;
            console.log('Rendering series info:', series); // Debug log
            
            html += `<div class="series-info">`;
            
            // Generate series fields using your CSS structure
            const seriesFields = [
                { key: 'db_title', label: 'DB Title' },
                { key: 'title', label: 'Display Title' },
                { key: 'english_title', label: 'English Title' },
                { key: 'year', label: 'Year' },
                { key: 'episodes', label: 'Episodes' },
                { key: 'score', label: 'Score' },
                { key: 'rank', label: 'Rank' },
                { key: 'popularity', label: 'Popularity' },
                { key: 'type', label: 'Type' },
                { key: 'duration', label: 'Duration' },
                { key: 'genres', label: 'Genres' }
            ];
            
            seriesFields.forEach(field => {
                if (series[field.key]) {
                    html += `
                        <div class="series-field">
                            <div class="field-label">${field.label}:</div>
                            <div class="field-value">${this.escapeHtml(series[field.key])}</div>
                        </div>
                    `;
                }
            });
            
            // Summary field (special handling for longer text)
            if (series.summary) {
                html += `
                    <div class="series-field">
                        <div class="field-label">Summary:</div>
                        <div class="field-value">${this.escapeHtml(series.summary)}</div>
                    </div>
                `;
            }
            
            // Poster image
            if (series.image_poster_large) {
                html += `
                    <div class="series-field">
                        <div class="field-label">Poster:</div>
                        <div class="field-value">
                            <img src="${this.escapeHtml(series.image_poster_large)}" 
                                 alt="Series Poster" 
                                 style="max-width: 200px; max-height: 300px; border-radius: 4px;"
                                 onerror="this.style.display='none'">
                        </div>
                    </div>
                `;
            }
            
            html += `</div>`; // Close series-info
            
        } else {
            console.log('No series info available'); // Debug log
            html += `
                <div class="no-series-info">
                    <p>No series information available for this title.</p>
                    <div style="margin-top: 15px;">
                        <button class="btn btn-small btn-primary" onclick="admin.fetchSeriesMetadata('${this.escapeHtml(this.currentTitle?.directory_hash)}', '${this.escapeHtml(detailsData.title)}')">
                            Fetch Metadata
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="admin.editTitle('${this.escapeHtml(this.currentTitle?.directory_hash)}', '${this.escapeHtml(detailsData.title)}')">
                            Add Manually
                        </button>
                    </div>
                </div>
            `;
        }

        html += `
            </div>
        `; // Close details-section

        return html;
    }

    // UPDATED: Fetch series metadata using directory_hash
    async fetchSeriesMetadata(directoryHash, titleName) {
        const title = this.titles.find(t => t.directory_hash === directoryHash);
        if (!title) {
            console.error('Title not found with directory_hash:', directoryHash);
            return;
        }

        const actualTitleName = title.title;
        const confirmed = confirm(`Fetch metadata for "${actualTitleName}"?\n\nThis will search for series information online.`);
        if (!confirmed) return;

        try {
            this.showUpdateProgress('Fetching metadata...');
            
            const requestData = {
                db_title: actualTitleName,
                suggested_title: actualTitleName,
                series_type: 'anime', // Default to anime, could be made configurable
                media_type: "video",
                from_cache: "no"
            };
            
            const response = await fetch('/fetch_series_metadata', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`Fetch failed: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                this.showSuccessMessage('Metadata fetched successfully!');
                // Refresh the details panel
                await this.showTitleDetails(directoryHash, actualTitleName);
                // Refresh the main titles list
                await this.loadTitles();
            } else {
                throw new Error('No metadata found for this title');
            }
            
        } catch (error) {
            console.error('Metadata fetch error:', error);
            this.showErrorMessage('Failed to fetch metadata: ' + error.message);
        }
    }

    closeDetailsPanel() {
        document.getElementById('details-panel').classList.remove('active');
        this.currentTitle = null;
        this.selectedEpisodes.clear();
    }

    // Episode selection methods
    selectAllEpisodes(titleName) {
        const checkboxes = document.querySelectorAll('.episode-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedEpisodes.add(checkbox.dataset.path);
        });
        this.updateSelectionUI();
    }

    deselectAllEpisodes(titleName) {
        const checkboxes = document.querySelectorAll('.episode-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            this.selectedEpisodes.delete(checkbox.dataset.path);
        });
        this.updateSelectionUI();
    }

    // FIXED: Single path edit
    editSinglePath(path, currentTitle) {
        this.openSinglePathEditModal(path, currentTitle);
    }

    openSinglePathEditModal(videoPath, currentTitle) {
        const modalHTML = `
            <div id="edit-modal" class="modal">
                <div class="modal-content">
                    <span class="close" onclick="admin.closeEditModal()">&times;</span>
                    <h3>Edit Single Episode</h3>
                    <p class="edit-info">Editing individual episode title.</p>
                    
                    <form id="edit-form" onsubmit="admin.submitSinglePathEdit(event)">
                        <input type="hidden" id="video-path" value="${this.escapeHtml(videoPath)}">
                        
                        <div class="form-section">
                            <h4>Episode Information</h4>
                            <div class="form-group">
                                <label for="path-new-title">Episode Title:</label>
                                <input type="text" id="path-new-title" value="${this.escapeHtml(currentTitle)}" placeholder="Enter episode title" required>
                            </div>
                            
                            <div class="form-group">
                                <label>Episode Path:</label>
                                <div class="path-display">${this.escapeHtml(videoPath)}</div>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Update Episode</button>
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('edit-modal').style.display = 'block';
    }

    // FIXED: Multiple paths edit
    editMultiplePaths() {
        if (this.selectedEpisodes.size === 0) {
            alert('Please select at least one episode to edit.');
            return;
        }

        // Convert Set to Array properly
        const selectedPaths = Array.from(this.selectedEpisodes);
        console.log("Selected paths for multiple edit:", selectedPaths); // Debug log
        
        this.openMultiplePathsEditModal(selectedPaths);
    }

    // FIXED: Remove escapeHtml from JSON string
    openMultiplePathsEditModal(selectedPaths) {
        const pathsToSend = selectedPaths || [];
        console.log("Paths to send in modal:", pathsToSend); // Debug log
        
        this.currentEditPaths = pathsToSend;

        const modalHTML = `
            <div id="edit-modal" class="modal">
                <div class="modal-content">
                    <span class="close" onclick="admin.closeEditModal()">&times;</span>
                    <h3>Edit Multiple Episodes</h3>
                    <p class="edit-info">Editing ${pathsToSend.length} episode(s). Only the title will be updated.</p>
                    
                    <form id="edit-form" onsubmit="admin.submitMultiplePathsEdit(event)">
                        
                        <div class="form-section">
                            <h4>Episode Information</h4>
                            <div class="form-group">
                                <label for="paths-new-title">New Title:</label>
                                <input type="text" id="paths-new-title" placeholder="Enter new title for all selected episodes" required>
                            </div>
                        </div>

                        <div class="selected-episodes">
                            <h4>Selected Episodes (${pathsToSend.length}):</h4>
                            <div class="episode-list">
                                ${pathsToSend.map(path => `
                                    <div class="episode-item">
                                        <span class="episode-path">${this.escapeHtml(path)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Update All</button>
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('edit-modal').style.display = 'block';
    }

    openBulkMetadataModal(selectedTitles) {
        const modalHTML = `
            <div id="metadata-modal" class="modal">
                <div class="modal-content metadata-modal-content">
                    <span class="close" onclick="admin.closeBulkMetadataModal()">&times;</span>
                    <h3>Fetch Metadata for ${selectedTitles.length} Titles</h3>
                    
                    <div class="metadata-modal-body">
                        <!-- Left side: Form -->
                        <div class="metadata-form-section">
                            <p class="edit-info">Select category and provide exact titles for metadata fetching.</p>
                            
                            <form id="metadata-form" onsubmit="admin.submitBulkMetadata(event)">
                                <input type="hidden" id="selected-titles-metadata" value='${JSON.stringify(selectedTitles)}'>
                                
                                <div class="form-section">
                                    <h4>Metadata Settings</h4>
                                    <div class="form-group">
                                        <label for="metadata-category">Category:</label>
                                        <select id="metadata-category" required>
                                            <option value="">Select Category</option>
                                            <option value="anime">Anime</option>
                                            <option value="tv">TV Shows</option>
                                            <option value="movies">Movies</option>
                                            <option value="cartoons">Cartoons</option>
                                        </select>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label>
                                            <input type="checkbox" id="use-cache" checked> Use cached data if available
                                        </label>
                                    </div>
                                </div>

                                <div class="selected-titles-metadata">
                                    <h4>Selected Titles - Provide Exact Search Terms:</h4>
                                    <div class="titles-metadata-list">
                                        ${selectedTitles.map((title, index) => `
                                            <div class="title-metadata-item">
                                                <div class="original-title">
                                                    <strong>Original:</strong> ${this.escapeHtml(title)}
                                                </div>
                                                <div class="search-title-input">
                                                    <label for="search-title-${index}">Search Term:</label>
                                                    <input type="text" id="search-title-${index}" 
                                                           value="${this.escapeHtml(title)}" 
                                                           placeholder="Enter exact title for search"
                                                           data-original-title="${this.escapeHtml(title)}"
                                                           required>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>

                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">Fetch Metadata</button>
                                    <button type="button" class="btn btn-secondary" onclick="admin.closeBulkMetadataModal()">Cancel</button>
                                </div>
                            </form>
                        </div>
                        
                        <!-- Right side: Results -->
                        <div class="metadata-results-section">
                            <h4>Results</h4>
                            <div class="results-summary" id="results-summary">
                                <span id="success-count">0</span> successful, 
                                <span id="fail-count">0</span> failed
                            </div>
                            <div class="results-container" id="results-container">
                                <div class="results-placeholder">
                                    Results will appear here as metadata is fetched...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('metadata-modal').style.display = 'block';
    }

    async submitBulkMetadata(event) {
        event.preventDefault();
        
        const selectedTitlesElement = document.getElementById('selected-titles-metadata');
        const selectedTitlesValue = selectedTitlesElement ? selectedTitlesElement.value : '[]';
        
        let selectedTitles;
        try {
            selectedTitles = JSON.parse(selectedTitlesValue);
        } catch (e) {
            console.error("Error parsing selected titles:", e);
            selectedTitles = [];
        }
        
        console.log(selectedTitles)
        const category = document.getElementById('metadata-category').value;
        const useCache = document.getElementById('use-cache').checked;
        
        // Collect search terms for each title
        const titleMappings = [];
        selectedTitles.forEach((originalTitle, index) => {
            const searchInput = document.getElementById(`search-title-${index}`);
            if (searchInput) {
                titleMappings.push({
                    original_title: originalTitle,
                    search_title: searchInput.value.trim()
                });
            }
        });

        console.log("Processing bulk metadata for:", titleMappings);

        // Clear results and show processing
        this.clearResults();
        this.disableForm(true);

        try {
            let successCount = 0;
            let failCount = 0;
            const totalCount = titleMappings.length;
            
            // Process each title individually by calling existing endpoint
            for (let i = 0; i < titleMappings.length; i++) {
                const mapping = titleMappings[i];
                
                this.updateProcessingStatus(`Processing ${i + 1} of ${totalCount}: ${mapping.search_title}`);
                
                try {
                    const requestData = {
                        db_title: mapping.original_title,
                        suggested_title: mapping.search_title,
                        series_type: this.getCategorySeriesType(category),
                        media_type: "video",
                        from_cache: "no"
                    };
                    
                    console.log(`Fetching metadata for: ${mapping.original_title} -> ${mapping.search_title}`);
                    
                    const response = await fetch('/fetch_series_metadata', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestData)
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        if (result.success && result.data) {
                            successCount++;
                            console.log(`Success for: ${mapping.original_title}`);
                            
                            // Add to results display
                            this.addResultItem(mapping.original_title, result.data, true);
                        } else {
                            failCount++;
                            console.log(`Failed for: ${mapping.original_title}`);
                            this.addResultItem(mapping.original_title, null, false, 'No data returned');
                        }
                    } else {
                        failCount++;
                        console.log(`HTTP error for: ${mapping.original_title}`);
                        this.addResultItem(mapping.original_title, null, false, `HTTP ${response.status}`);
                    }
                    
                    // Update summary
                    this.updateResultsSummary(successCount, failCount);
                    
                    // Small delay between requests
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                } catch (error) {
                    failCount++;
                    console.error(`Error processing ${mapping.original_title}:`, error);
                    this.addResultItem(mapping.original_title, null, false, error.message);
                    this.updateResultsSummary(successCount, failCount);
                }
            }
            
            this.updateProcessingStatus('Completed! You can close this dialog.');
            this.disableForm(false);
            
            // Refresh the main titles list
            await this.loadTitles();
            this.selectedTitles.clear();
            this.updateBulkEditButton();
            
        } catch (error) {
            this.showErrorMessage('Bulk metadata fetch failed: ' + error.message);
            this.disableForm(false);
        }
    }

    // Add these methods for metadata-fetch
    clearResults() {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = '<div class="processing-status">Starting metadata fetch...</div>';
        }
        this.updateResultsSummary(0, 0);
    }

    updateProcessingStatus(message) {
        const container = document.getElementById('results-container');
        if (container) {
            const statusEl = container.querySelector('.processing-status');
            if (statusEl) {
                statusEl.textContent = message;
            }
        }
    }

    addResultItem(originalTitle, data, success, errorMessage = '') {
        const container = document.getElementById('results-container');
        if (!container) return;
        
        // Remove processing status if it exists
        const statusEl = container.querySelector('.processing-status');
        if (statusEl) {
            statusEl.remove();
        }
        
        const resultItem = document.createElement('div');
        resultItem.className = `result-item ${success ? 'success' : 'failure'}`;
        
        if (success && data) {
            const title = data.title || 'Unknown Title';
            const poster = data.image_poster_large || '';
            
            resultItem.innerHTML = `
                <div class="result-content">
                    <div class="result-poster">
                        ${poster ? `<img src="${this.escapeHtml(poster)}" alt="Poster" onerror="this.style.display='none'">` : '<div class="no-poster">No Image</div>'}
                    </div>
                    <div class="result-details">
                        <div class="result-original">${this.escapeHtml(originalTitle)}</div>
                        <div class="result-fetched">${this.escapeHtml(title)}</div>
                        <div class="result-status success">✓ Success</div>
                    </div>
                </div>
            `;
        } else {
            resultItem.innerHTML = `
                <div class="result-content">
                    <div class="result-details">
                        <div class="result-original">${this.escapeHtml(originalTitle)}</div>
                        <div class="result-error">✗ ${this.escapeHtml(errorMessage)}</div>
                    </div>
                </div>
            `;
        }
        
        container.appendChild(resultItem);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    updateResultsSummary(successCount, failCount) {
        const successCountEl = document.getElementById('success-count');
        const failCountEl = document.getElementById('fail-count');
        
        if (successCountEl) successCountEl.textContent = successCount;
        if (failCountEl) failCountEl.textContent = failCount;
    }

    disableForm(disabled) {
        const form = document.getElementById('metadata-form');
        if (form) {
            const inputs = form.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = disabled;
            });
        }
    }

    // UPDATED: Edit title using directory_hash
   
    async editTitle(directoryHash, titleName) {
        console.log('Editing title:', titleName, 'Hash:', directoryHash);
        
        // Find the title to check if it has series info
        const title = this.titles.find(t => t.directory_hash === directoryHash);
        if (!title) {
            this.showErrorMessage('Title not found');
            return;
        }
        
        let seriesData = null;
        let episodesList = null;
        
        // If title has series info, fetch the details
        if (title.has_series_info) {
            try {
                console.log('Title has series info, fetching details...');
                this.showUpdateProgress('Loading series information...');
                
                const response = await fetch('/title-details', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        title: titleName,
                        directory_hash: directoryHash
                    })
                });
                
                if (response.ok) {
                    const detailsData = await response.json();
                    if (detailsData && !detailsData.error) {
                        seriesData = detailsData.series_info || null;
                        episodesList = detailsData.episodes || null;
                        console.log('Fetched series data:', seriesData);
                    }
                }
            } catch (error) {
                console.warn('Failed to fetch series info for editing:', error);
                // Continue without series data
            }
            
            // Hide progress indicator
            this.hideUpdateProgress();
        }
        
        // Open the edit modal with series data
        this.openEditModal(directoryHash, titleName, seriesData, episodesList);
    }

    // UPDATED: Handle bulk edit (Type 4 - Multiple titles bulk update)
    handleBulkEdit() {
        const selectedTitles = Array.from(this.selectedTitles);
        if (selectedTitles.length === 0) {
            alert('Please select at least one title for bulk editing.');
            return;
        }

        // Convert directory hashes to title names for display
        const selectedTitleNames = selectedTitles.map(hash => {
            const title = this.titles.find(t => t.directory_hash === hash);
            return title ? title.title : null;
        }).filter(title => title !== null);

        this.openBulkEditModal(selectedTitleNames);
    }

    // UPDATED: Open edit modal with directory_hash
    
    
    // UPDATED: Open edit modal with directory_hash
    openEditModal(directoryHash, titleName, seriesData, episodesList) {
        const title = this.titles.find(t => t.directory_hash === directoryHash);
        if (!title) return;

        const series = seriesData || {};
        const pathsToSend = episodesList || [];
        console.log(series)
        
        const modalHTML = `
            <div id="edit-modal" class="modal">
                <div class="modal-content">
                    <span class="close" onclick="admin.closeEditModal()">&times;</span>
                    <h3>Edit: ${this.escapeHtml(titleName)}</h3>
                    <p class="edit-info">Editing ${pathsToSend.length} episode(s). Empty fields will not be updated.</p>
                    
                    <form id="edit-form" onsubmit="admin.submitEdit(event)">
                        <input type="hidden" id="original-title" value="${this.escapeHtml(titleName)}">
                        <input type="hidden" id="directory-hash" value="${this.escapeHtml(directoryHash)}">
                        
                        <div class="form-section">
                            <h4>Video Information</h4>
                            <div class="form-group">
                                <label for="new-title">New Title:</label>
                                <input type="text" id="new-title" value="${this.escapeHtml(titleName)}" placeholder="Enter new title">
                            </div>
                        </div>

                        <div class="form-section">
                            <h4>Series Information</h4>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="db-title">DB Title:</label>
                                    <input type="text" id="db-title" value="${this.escapeHtml(series.db_title || '')}" placeholder="Database title">
                                </div>
                                <div class="form-group">
                                    <label for="display-title">Display Title:</label>
                                    <input type="text" id="display-title" value="${this.escapeHtml(series.title || '')}" placeholder="Display title">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="english-title">English Title:</label>
                                    <input type="text" id="english-title" value="${this.escapeHtml(series.english_title || '')}" placeholder="English title">
                                </div>
                                <div class="form-group">
                                    <label for="year">Year:</label>
                                    <input type="number" id="year" value="${series.year || ''}" placeholder="Release year">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="episodes">Total Episodes:</label>
                                    <input type="number" id="episodes" value="${series.episodes || ''}" placeholder="Total episodes">
                                </div>
                                <div class="form-group">
                                    <label for="score">Score:</label>
                                    <input type="number" step="0.1" id="score" value="${series.score || ''}" placeholder="Rating score">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="rank">Rank:</label>
                                    <input type="number" id="rank" value="${series.rank || ''}" placeholder="Ranking">
                                </div>
                                <div class="form-group">
                                    <label for="popularity">Popularity:</label>
                                    <input type="number" id="popularity" value="${series.popularity || ''}" placeholder="Popularity rank">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="type">Type:</label>
                                    <input type="text" id="type" value="${this.escapeHtml(series.type || '')}" placeholder="e.g., TV, Movie, OVA, Special">
                                </div>
                                <div class="form-group">
                                    <label for="duration">Duration:</label>
                                    <input type="text" id="duration" value="${this.escapeHtml(series.duration || '')}" placeholder="Episode duration">
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="genres">Genres:</label>
                                <input type="text" id="genres" value="${this.escapeHtml(series.genres || '')}" placeholder="Comma-separated genres">
                            </div>
                            
                            <div class="form-group">
                                <label for="external-id">External ID:</label>
                                <input type="number" id="external-id" value="${series.external_id || ''}" placeholder="External database ID">
                            </div>
                            
                            <div class="form-group">
                                <label for="image-poster">Poster Image:</label>
                                <input type="text" id="image-poster" value="${this.escapeHtml(series.image_poster_large || '')}" placeholder="Poster image URL or path">
                            </div>
                            
                            <div class="form-group">
                                <label for="summary">Summary:</label>
                                <textarea id="summary" rows="4" placeholder="Series summary">${this.escapeHtml(series.summary || '')}</textarea>
                            </div>
                        </div>

                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">Update</button>
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('edit-modal').style.display = 'block';
    }

    // Type 4: Bulk edit modal (multiple titles - future implementation)
    openBulkEditModal(selectedTitles) {
        const modalHTML = `
            <div id="edit-modal" class="modal">
                <div class="modal-content">
                    <span class="close" onclick="admin.closeEditModal()">&times;</span>
                    <h3>Bulk Edit: ${selectedTitles.length} Titles</h3>
                    <p class="edit-info" style="color: #e74c3c; font-weight: bold;">
                        ⚠️ Bulk title updates will be implemented after database migration for category/label/ignore fields.
                    </p>
                    
                    <div class="selected-titles">
                        <h4>Selected Titles:</h4>
                        <ul>
                            ${selectedTitles.map(title => `<li>${this.escapeHtml(title)}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div style="padding: 20px; background: #f8f9fa; border-radius: 4px; margin: 20px 0;">
                        <h4>Coming Soon:</h4>
                        <ul>
                            <li>Bulk category assignment</li>
                            <li>Bulk label assignment</li>
                            <li>Bulk ignore flag setting</li>
                        </ul>
                        <p style="margin-top: 15px; font-style: italic;">
                            These features require database migration to add new columns to the Video table.
                        </p>
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Close</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.getElementById('edit-modal').style.display = 'block';
    }

    closeEditModal() {
        const modal = document.getElementById('edit-modal');
        if (modal) {
            modal.remove();
        }
        // Reset stored paths when modal is closed
        this.currentEditPaths = null;
        // Clear saved scroll position since user cancelled
        localStorage.removeItem('adminScrollPosition');
    }

    // UPDATED: Submit edit with directory_hash
    async submitEdit(event) {
        event.preventDefault();
        
        const selectedPathsElement = document.getElementById('selected-paths');
        const selectedPathsValue = selectedPathsElement ? selectedPathsElement.value : '[]';
        
        console.log("Selected paths value:", selectedPathsValue); // Debug log
        
        let selectedPaths;
        try {
            selectedPaths = JSON.parse(selectedPathsValue);
        } catch (e) {
            console.error("Error parsing selected paths:", e);
            selectedPaths = [];
        }
        
        const formData = {
            action: 'update_title',
            original_title: document.getElementById('original-title').value,
            directory_hash: document.getElementById('directory-hash').value, // Include directory_hash
            selected_paths: selectedPaths,
            new_title: document.getElementById('new-title').value.trim()
        };
        
        // Add series fields - only if not empty
        const fields = [
            'db-title', 'display-title', 'english-title', 'year', 'episodes', 
            'score', 'rank', 'popularity', 'type', 'duration', 'genres', 
            'external-id', 'image-poster', 'summary'
        ];
        
        fields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            const value = element ? element.value.trim() : '';
            if (value) {
                const fieldName = fieldId.replace('-', '_');
                formData[fieldName] = value;
            }
        });

        console.log("Form data to send:", formData); // Debug log

        try {
            this.showUpdateProgress('Updating...');
            
            const response = await fetch('/admin-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('Update failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.showUpdateProgress('Update successful! Reloading data...');
                this.closeEditModal();
                await this.loadTitles();
                this.showSuccessMessage(result.message || 'Update completed successfully');
            } else {
                throw new Error(result.error || 'Update failed');
            }
            
        } catch (error) {
            this.showErrorMessage('Update failed: ' + error.message);
        }
    }

    // Type 2: Submit single path edit
    async submitSinglePathEdit(event) {
        event.preventDefault();
        
        const formData = {
            action: 'update_single_path',
            video_path: document.getElementById('video-path').value,
            new_title: document.getElementById('path-new-title').value.trim()
        };

        console.log("Single path form data to send:", formData); // Debug log

        try {
            this.showUpdateProgress('Updating episode...');
            
            const response = await fetch('/admin-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('Update failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.closeEditModal();
                await this.loadTitles();
                this.showSuccessMessage(result.message || 'Episode updated successfully');
                // Refresh details panel if it's open
                if (this.currentTitle) {
                    await this.showTitleDetails(this.currentTitle.directory_hash, this.currentTitle.title);
                }
            } else {
                throw new Error(result.error || 'Update failed');
            }
            
        } catch (error) {
            this.showErrorMessage('Update failed: ' + error.message);
        }
    }

    // Type 3: Submit multiple paths edit
    async submitMultiplePathsEdit(event) {
        event.preventDefault();
        
        const videoPaths = this.currentEditPaths || [];
        console.log("Using stored paths:", videoPaths.length, "episodes"); // Debug log
        
        if (videoPaths.length === 0) {
            this.showErrorMessage("No episodes selected for editing.");
            this.currentEditPaths = null; // Reset on error
            return;
        }
        
        const formData = {
            action: 'update_multiple_paths',
            video_paths: videoPaths,
            new_title: document.getElementById('paths-new-title').value.trim()
        };

        console.log("Multiple paths form data to send:", formData.video_paths.length, "paths"); // Debug log

        try {
            this.showUpdateProgress('Updating multiple episodes...');
            
            const response = await fetch('/admin-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('Update failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                // SUCCESS: Reset everything
                this.currentEditPaths = null;
                this.closeEditModal();
                await this.loadTitles();
                this.showSuccessMessage(result.message || 'Episodes updated successfully');
                this.selectedEpisodes.clear();
                this.updateSelectionUI();
                if (this.currentTitle) {
                    await this.showTitleDetails(this.currentTitle.directory_hash, this.currentTitle.title);
                }
            } else {
                throw new Error(result.error || 'Update failed');
            }
            
        } catch (error) {
            // ERROR: Reset and show error
            this.currentEditPaths = null;
            this.showErrorMessage('Update failed: ' + error.message);
        }
    }

        // Type 4: Submit bulk edit (placeholder for future)
    async submitBulkEdit(event) {
        event.preventDefault();
        
        // This will be implemented after database migration
        this.showErrorMessage('Bulk edit will be implemented after database migration for category/label/ignore fields.');
    }

    
    showUpdateProgress(message, autoHide = true) {
        const existing = document.getElementById('update-progress');
        if (existing) existing.remove();
        
        const progressDiv = document.createElement('div');
        progressDiv.id = 'update-progress';
        progressDiv.className = 'update-progress';
        progressDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <span>${this.escapeHtml(message)}</span>
        `;
        document.body.appendChild(progressDiv);
        
        // Only auto-hide if specified (default true for backward compatibility)
        if (autoHide) {
            setTimeout(() => {
                if (progressDiv.parentNode) {
                    progressDiv.remove();
                }
            }, 3000);
        }
    }
    
    hideUpdateProgress() {
        const existing = document.getElementById('update-progress');
        if (existing) {
            existing.remove();
        }
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        const existing = document.getElementById('admin-message');
        if (existing) existing.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.id = 'admin-message';
        messageDiv.className = `admin-message ${type}`;
        messageDiv.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        document.body.insertBefore(messageDiv, document.body.firstChild);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }

    showLoading() {
        document.getElementById('titles-list').innerHTML = '<div class="loading">Loading titles...</div>';
    }

    showError(message) {
        const container = document.getElementById('titles-list');
        container.innerHTML = `<div class="error">${this.escapeHtml(message)}</div>`;
    }

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize admin panel when page loads
let admin;
document.addEventListener('DOMContentLoaded', () => {
    admin = new AdminPanel();
});
