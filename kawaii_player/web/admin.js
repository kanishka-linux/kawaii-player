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
        this.availableCategories = [];
        this.availableLabels = [];
        // UPDATED: Add mtime sorting option
        this.currentSortBy = 'title'; // 'title' or 'recently-added'
        this.currentSortOrder = 'asc'; // 'asc' or 'desc'
        this.currentCategoryFilter = 'all';
        this.currentLabelFilter = 'all';

        this.init();
    }

    // Enhanced attribute escaping for HTML attributes
    escapeHtmlAttribute(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    // Safe JSON encoding for HTML attributes
    safeJsonEncode(obj) {
        return this.escapeHtmlAttribute(JSON.stringify(obj));
    }

    // Add this method to the AdminPanel class to save category preference
    saveCategoryPreference(category) {
        try {
            localStorage.setItem('bulkMetadataCategoryPreference', category);
        } catch (error) {
            console.warn('Failed to save category preference:', error);
        }
    }

    // Add this method to get saved category preference
    getCategoryPreference() {
        try {
            return localStorage.getItem('bulkMetadataCategoryPreference') || 'anime';
        } catch (error) {
            console.warn('Failed to get category preference:', error);
            return 'anime'; // Default fallback
        }
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
        this.setupMobileSidebar();
        // Search functionality
        
        // In setupEventListeners(), update search listeners:
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.currentSearchTerm = e.target.value;
            
            // Use backend filtering if category/label filters are active
            const needsBackendFiltering = this.currentCategoryFilter !== 'all' || 
                                         this.currentLabelFilter !== 'all';
            
            if (needsBackendFiltering) {
                this.loadFilteredTitles();
            } else {
                this.applyFilters();
            }
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

        // UPDATED: Sort and filter event listeners with mtime support
        document.getElementById('sort-by').addEventListener('change', (e) => {
            this.currentSortBy = e.target.value;
            this.applyFilters();
        });

        document.getElementById('sort-order').addEventListener('change', (e) => {
            this.currentSortOrder = e.target.value;
            this.applyFilters();
        });

        document.getElementById('category-filter').addEventListener('change', (e) => {
            this.currentCategoryFilter = e.target.value;
            this.loadFilteredTitles();
        });

        document.getElementById('label-filter').addEventListener('change', (e) => {
            this.currentLabelFilter = e.target.value;
            this.loadFilteredTitles();
        });

        document.getElementById('clear-sort-filter-btn').addEventListener('click', () => {
            this.clearSortAndFilters();
        });

    }

    // NEW: Add this method to AdminPanel class
    
    // UPDATED: Enhanced mobile sidebar functionality
    
    setupMobileSidebar() {
        const toggleBtn = document.getElementById('mobile-sidebar-toggle');
        const sidebar = document.querySelector('.filters-sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const container = document.querySelector('.main-area');
        const closeBtn = document.getElementById('sidebar-close');

        if (toggleBtn && sidebar && overlay) {
            // Initialize sidebar state based on screen size
            const initializeSidebar = () => {
                if (window.innerWidth >= 1024) {
                    // Desktop: Show sidebar by default
                    sidebar.classList.add('open');
                    overlay.classList.remove('active');
                    toggleBtn.classList.add('active');
                    document.body.classList.add('sidebar-open');
                    if (container) container.classList.add('sidebar-open');
                } else {
                    // Mobile/Tablet: Hide sidebar by default
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                    toggleBtn.classList.remove('active');
                    document.body.classList.remove('sidebar-open');
                    if (container) container.classList.remove('sidebar-open');
                }
            };

            // Initialize immediately
            initializeSidebar();

            // Toggle sidebar function
            const toggleSidebar = () => {
                const isOpen = sidebar.classList.contains('open');
                
                if (isOpen) {
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                    toggleBtn.classList.remove('active');
                    document.body.classList.remove('sidebar-open');
                    if (container) container.classList.remove('sidebar-open');
                } else {
                    sidebar.classList.add('open');
                    overlay.classList.add('active');
                    toggleBtn.classList.add('active');
                    document.body.classList.add('sidebar-open');
                    if (container) container.classList.add('sidebar-open');
                }
            };

            // Event listeners
            toggleBtn.addEventListener('click', toggleSidebar);
            
            if (closeBtn) {
                closeBtn.addEventListener('click', toggleSidebar);
            }

            overlay.addEventListener('click', () => {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
                toggleBtn.classList.remove('active');
                document.body.classList.remove('sidebar-open');
                if (container) container.classList.remove('sidebar-open');
            });

            // Handle window resize
            window.addEventListener('resize', initializeSidebar);
        }
    }

    // UPDATED: Clear all sort and filter settings including sort-by
    clearSortAndFilters() {
        this.currentSortBy = 'title';
        this.currentSortOrder = 'asc';
        this.currentCategoryFilter = 'all';
        this.currentLabelFilter = 'all';
        
        // Update UI controls
        document.getElementById('sort-by').value = 'title';
        document.getElementById('sort-order').value = 'asc';
        document.getElementById('category-filter').value = 'all';
        document.getElementById('label-filter').value = 'all';
        
        this.applyFilters();
    }

    // Existing method - no changes needed
    populateFilterDropdowns() {
        // Populate category filter
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.innerHTML = '<option value="all">All Categories</option>';
            this.availableCategories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                categoryFilter.appendChild(option);
            });
        }

        // Populate label filter
        const labelFilter = document.getElementById('label-filter');
        if (labelFilter) {
            labelFilter.innerHTML = '<option value="all">All Labels</option>';
            this.availableLabels.forEach(label => {
                const option = document.createElement('option');
                option.value = label;
                option.textContent = label;
                labelFilter.appendChild(option);
            });
        }
    }

    // UPDATED: Sort titles with mtime support
    sortTitles(titles) {
        const sorted = [...titles];
        
        sorted.sort((a, b) => {
            let comparison = 0;
            
            if (this.currentSortBy === 'title') {
                comparison = a.title.localeCompare(b.title, undefined, { 
                    numeric: true, 
                    sensitivity: 'base' 
                });
            } else if (this.currentSortBy === 'recently-added') {
                // Sort by mtime (modification time) - raw values
                const aTime = a.mtime || 0;
                const bTime = b.mtime || 0;
                comparison = bTime - aTime; // Most recent first by default
            }
            
            // Apply sort order
            return this.currentSortOrder === 'desc' ? -comparison : comparison;
        });
        
        return sorted;
    }

    // Existing method - no changes needed
    filterTitles(titles) {
        let filtered = [...titles];
        
        // Filter by category
        if (this.currentCategoryFilter !== 'all') {
            filtered = filtered.filter(title => {
                const category = title.category || '';
                return category.toLowerCase() === this.currentCategoryFilter.toLowerCase();
            });
        }
        
        // Filter by label
        if (this.currentLabelFilter !== 'all') {
            filtered = filtered.filter(title => {
                const labels = title.labels || '';
                const labelArray = labels.split(',').map(l => l.trim().toLowerCase());
                return labelArray.includes(this.currentLabelFilter.toLowerCase());
            });
        }
        
        return filtered;
    }

    
    setupTitleEventListeners() {
        // Clean up existing listeners first
        this.cleanupTitleEventListeners();

        // Handle checkbox changes - FIXED selector
        document.querySelectorAll('.title-item input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (event) => {
                const hash = event.target.dataset.hash;
                const titleElement = event.target.closest('.title-item');
                const title = titleElement.dataset.title;
                this.toggleTitleSelection(hash, title);
            });
        });

        // Handle title info clicks - FIXED selector
        document.querySelectorAll('.title-info').forEach(titleInfo => {
            titleInfo.addEventListener('click', (event) => {
                const index = parseInt(titleInfo.dataset.index);
                const hash = titleInfo.dataset.hash;
                const titleElement = titleInfo.closest('.title-item');
                const title = titleElement.dataset.title;
                this.saveTitleIndexAndShowDetails(index, hash, title);
            });
        });

        // Handle edit button clicks - FIXED selector
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

    cleanupTitleEventListeners() {
        // Remove existing event listeners to prevent memory leaks
        document.querySelectorAll('.title-item input[type="checkbox"]').forEach(checkbox => {
            // Clone and replace to remove all event listeners
            const newCheckbox = checkbox.cloneNode(true);
            checkbox.parentNode.replaceChild(newCheckbox, checkbox);
        });
        
        document.querySelectorAll('.title-info').forEach(titleInfo => {
            const newTitleInfo = titleInfo.cloneNode(true);
            titleInfo.parentNode.replaceChild(newTitleInfo, titleInfo);
        });
        
        document.querySelectorAll('.btn-edit').forEach(button => {
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
        });
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

    async loadFilteredTitles() {
        try {
            this.showLoading();
            
            // Check if both category and label filters are 'all' or not present
            const categoryIsAll = !this.currentCategoryFilter || this.currentCategoryFilter === 'all';
            const labelIsAll = !this.currentLabelFilter || this.currentLabelFilter === 'all';
            
            if (categoryIsAll && labelIsAll) {
                // Use original endpoint with no query params
                const response = await fetch('/series-data');
                if (!response.ok) {
                    throw new Error(`Failed to load titles: ${response.status} ${response.statusText}`);
                }
                
                const { titles, available_categories, available_labels } = await response.json();
                
                if (titles.error) {
                    throw new Error(titles.error);
                }
                
                // Update local data
                this.titles = titles;
                this.availableCategories = available_categories;
                this.availableLabels = available_labels;
                
                // Apply any remaining client-side filters (search, series info)
                this.applyFilters();
                
            } else {
                // Build query parameters for backend filtering
                const params = new URLSearchParams();
                
                // Add category filter
                if (!categoryIsAll) {
                    params.append('category', this.currentCategoryFilter);
                }
                
                // Add label filter
                if (!labelIsAll) {
                    params.append('label', this.currentLabelFilter);
                }
                
                // Make backend call with filters
                const response = await fetch(`/series-data?${params.toString()}`);
                if (!response.ok) {
                    throw new Error(`Failed to load filtered titles: ${response.status} ${response.statusText}`);
                }
                
                const { titles, available_categories, available_labels } = await response.json();
                
                if (titles.error) {
                    throw new Error(titles.error);
                }
                
                // Update local data
                this.titles = titles;
                this.availableCategories = available_categories;
                this.availableLabels = available_labels;
                
                // Render the filtered results (no client-side filtering needed for category/label)
                this.renderTitles(titles);
                this.updateFilterStatus(titles.length);
                this.updateLabelStyles();
            }
            
        } catch (error) {
            this.showError('Failed to load titles: ' + error.message);
        }
    }

    // Existing method - no changes needed
    
    applyFilters() {
        // Clear localStorage state
        this.clearLocalStorageState();
        
        // Check if we need backend filtering (category or label filters)
        const needsBackendFiltering = this.currentCategoryFilter !== 'all' || 
                                     this.currentLabelFilter !== 'all';
        
        if (needsBackendFiltering) {
            // Use backend filtering
            this.loadFilteredTitles();
            return;
        }
        
        // Continue with client-side filtering for search and series info
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
        
        // Apply sorting
        filtered = this.sortTitles(filtered);
        
        this.renderTitles(filtered);
        this.updateLabelStyles();
        this.updateFilterStatus(filtered.length);
    }

    // UPDATED: Update filter status display with mtime sort support
    updateFilterStatus(filteredCount) {
        const totalCount = this.titles.length;
        let statusParts = [];
        
        // Add search status
        if (this.currentSearchTerm) {
            statusParts.push(`Search: "${this.currentSearchTerm}"`);
        }
        
        // Add series info filter status
        if (this.currentSeriesInfoFilter !== 'all') {
            const hasInfoCount = this.titles.filter(t => t.has_series_info).length;
            const noInfoCount = totalCount - hasInfoCount;
            
            if (this.currentSeriesInfoFilter === 'has-info') {
                statusParts.push(`With series info (${hasInfoCount})`);
            } else if (this.currentSeriesInfoFilter === 'no-info') {
                statusParts.push(`Without series info (${noInfoCount})`);
            }
        }
        
        // Add category filter status
        if (this.currentCategoryFilter !== 'all') {
            statusParts.push(`Category: ${this.currentCategoryFilter}`);
        }
        
        // Add label filter status
        if (this.currentLabelFilter !== 'all') {
            statusParts.push(`Label: ${this.currentLabelFilter}`);
        }
        
        // UPDATED: Add sort status with mtime support
        let sortLabel = 'Title';
        let orderLabel = this.currentSortOrder === 'desc' ? 'Z-A' : 'A-Z';
        
        if (this.currentSortBy === 'recently-added') {
            sortLabel = 'Recently Added';
            orderLabel = this.currentSortOrder === 'desc' ? 'Oldest First' : 'Newest First';
        }
        
        statusParts.push(`Sort: ${sortLabel} (${orderLabel})`);
        
        // Display status
        if (statusParts.length > 1 || this.currentSortBy !== 'title' || this.currentSortOrder !== 'asc') {
            const message = `${statusParts.join(' • ')} | Showing ${filteredCount} of ${totalCount} titles`;
            this.showFilterMessage(message);
        } else {
            this.hideFilterMessage();
        }
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

    
    // Existing method - no changes needed
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
            <button class="clear-filter-btn" onclick="admin.clearAllFilters()">Clear All</button>
        `;
    }

    // UPDATED: Clear all filters including sort-by
    clearAllFilters() {
        // Clear search
        this.clearLocalStorageState();
        document.getElementById('search-input').value = '';
        this.currentSearchTerm = '';
        
        // Clear series info filter
        this.currentSeriesInfoFilter = 'all';
        this.updateNoInfoButton(false);
        
        // Clear sort and filters
        this.clearSortAndFilters();
        
        this.applyFilters();
        this.hideFilterMessage();
        this.updateLabelStyles();
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
            
            this.showUpdateProgress('Request successfully submitted, it may take some time to reflect the data');
            
            // Small delay to show completion message
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Reload the titles after update
            await this.loadTitles();
            
            this.showSuccessMessage('Video collection updated request submitted successfully!');
            
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
            
            const response = await fetch('/series-data');
            if (!response.ok) {
                throw new Error(`Failed to load titles: ${response.status} ${response.statusText}`);
            }
            
            const { titles, available_categories, available_labels } = await response.json();
            this.titles = titles;
            this.availableCategories = available_categories;
            this.availableLabels = available_labels;
            
            if (this.titles.error) {
                throw new Error(this.titles.error);
            }

            // Populate filter dropdowns after loading data
            this.populateFilterDropdowns();
            
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
        setTimeout(() => {
            this.restoreToSavedIndex();
        }, 2000);
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

    // FOCUSED: Clear only the specific localStorage items
    clearLocalStorageState() {
        try {
            // Clear the specific items that need to be removed
            localStorage.removeItem('adminReturnToIndex');
            localStorage.removeItem('adminShouldScrollToIndex');
        } catch (error) {
            console.warn('Error clearing localStorage:', error);
        }
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
            const checkbox = item.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = true;
            }
            item.classList.add('selected');
        });
        this.updateBulkEditButton();
    }

    deselectAllTitles() {
        this.selectedTitles.clear();
        document.querySelectorAll('.title-item input[type="checkbox"]').forEach(checkbox => {
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
            'tv shows': 'tv shows',
            'movies': 'movies',
            'cartoons': 'cartoons',
            'anime movies': 'anime movies'
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

        const actualTitleName = title.title;
        this.currentTitle = title;
        
        // Show the panel immediately with loading state
        document.getElementById('details-title').textContent = `${actualTitleName}`;
        const detailsPanel = document.getElementById('details-panel');
        detailsPanel.classList.add('active');
        
        // Prevent body scroll on mobile
        if (window.innerWidth <= 768) {
            document.body.style.overflow = 'hidden';
        }
        
        // Show loading state in details content
        const detailsContent = document.getElementById('details-content');
        detailsContent.innerHTML = this.generateLoadingDetailsHTML();
        
        try {
            const requestBody = {
                title: actualTitleName,
                directory_hash: directoryHash
            };
            
            const response = await fetch('/title-details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const responseText = await response.text();
            let detailsData;
            try {
                detailsData = JSON.parse(responseText);
            } catch (parseError) {
                throw new Error(`Invalid JSON response: ${parseError.message}`);
            }
            
            if (detailsData.error) {
                throw new Error(detailsData.error);
            }
            
            const generatedHTML = this.generateDetailsHTML(detailsData);
            detailsContent.innerHTML = generatedHTML;
            
            // Setup episode selection listeners
            this.setupEpisodeSelectionListeners();
            
        } catch (error) {
            console.error('Error loading title details:', error);
            detailsContent.innerHTML = this.generateErrorDetailsHTML(error.message);
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
                <button class="btn btn-primary" 
                        data-directory-hash="${this.escapeHtml(this.currentTitle?.directory_hash || '')}"
                        data-title="${this.escapeHtml(this.currentTitle?.title || '')}"
                        onclick="admin.showTitleDetailsHandler(event)">
                    Retry
                </button>
            </div>
        `;
    }

    showTitleDetailsHandler(event) {
        // Extract data from button's data attributes
        const button = event.target;
        const directoryHash = button.dataset.directoryHash;
        const title = button.dataset.title;
        
        // Call the original method with extracted parameters
        this.showTitleDetails(directoryHash, title);
    }

    setupEpisodeSelectionListeners() {
        // Existing episode checkbox listeners...
        document.querySelectorAll('.episode-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const path = e.target.dataset.path;
                if (e.target.checked) {
                    this.selectedEpisodes.add(path);
                } else {
                    this.selectedEpisodes.delete(path);
                }
                this.updateSelectionUI();
                this.updateMovieMetadataButtons(); // NEW: Add this line
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

    generateDetailsHTML(detailsData) {
        console.log('Generating HTML for data:', detailsData); // Debug log
        
        let html = '';


        // Section 2: Episodes (matches your .details-section structure)
        html += `
            <div class="details-section">
                <h4>Episodes</h4>
                <div class="episode-controls">
                    <button class="btn btn-small btn-secondary" 
                            data-series-title="${this.escapeHtml(detailsData.title)}"
                            onclick="admin.selectAllEpisodes(event)">
                        Select All
                    </button>
                    <button class="btn btn-small btn-secondary" 
                            data-series-title="${this.escapeHtml(detailsData.title)}"
                            onclick="admin.deselectAllEpisodes(event)">
                        Deselect All
                    </button>
                    <button class="btn btn-small btn-primary" 
                            onclick="admin.editMultiplePaths()" 
                            disabled>
                        Edit Selected
                    </button>
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
                            <button class="btn btn-small btn-edit" 
                                    data-episode-path="${this.escapeHtml(episodePath)}"
                                    data-episode-title="${this.escapeHtml(episodeTitle)}"
                                    data-series-title="${this.escapeHtml(detailsData.title)}"
                                    onclick="admin.openSinglePathEditModal(event)">
                                Edit
                            </button>
                        </div>
                    </div>
                `;
            });
        } else {
            html += `
                <div class="no-episodes">
                    <div class="no-episodes-message">
                        <h5>⚠️ No Episodes Found</h5>
                        <p>This title exists in the database but no video files were found.</p>
                        <p>This could mean:</p>
                        <ul>
                            <li>Video files have been moved or deleted</li>
                            <li>The directory path has changed</li>
                            <li>Storage is not accessible</li>
                        </ul>
                    </div>
                    <div class="stale-entry-actions">
                        <button class="btn btn-warning btn-delete-stale" 
                                data-db-title="${this.escapeHtml(detailsData.title)}"
                                onclick="admin.handleDeleteStaleEntry(event)">
                            🗑️ Delete Stale Entry
                        </button>
                        <div class="delete-help">
                            <small>This will remove the database entry for this title since no video files exist.</small>
                        </div>
                    </div>
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;

        // Section 3: Series Information (IMPROVED STYLING)
        html += `
            <div class="details-section">
                <h4>Series Information</h4>
        `;

        console.log('Series info check:', {
            has_series_info: detailsData.has_series_info,
            series_info: detailsData.series_info
        }); // Debug log

        let detailsPartiallyAvailable = false;
        if (detailsData.series_info && !detailsData.series_info.summary) {
            detailsPartiallyAvailable = true;
        }

        let category = detailsData.series_info?.category || "anime";

        if (detailsData.series_info)  {
            const series = detailsData.series_info;
            console.log('Rendering series info:', series); // Debug log
            
            html += `<div class="series-info-grid">`;
            
            // Generate series fields using improved grid layout
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
                        <div class="series-field-row">
                            <span class="field-label-inline">${field.label}:</span>
                            <span class="field-value-inline">${this.escapeHtml(series[field.key])}</span>
                        </div>
                    `;
                }
            });
            
            // Summary field (special handling for longer text)
            if (series.summary) {
                html += `
                    <div class="series-field-full">
                        <div class="field-label-block">Summary:</div>
                        <div class="field-value-block">${this.escapeHtml(series.summary)}</div>
                    </div>
                    <div class="custom-fetch-actions">
                        <button class="btn btn-warning"
                            data-original-title="${this.escapeHtml(detailsData.title)}"
                            data-episode-count="${episodes.length}"
                            onclick="admin.openCustomFetchModal(event, ${episodes.length})">

                            🔄 Try Custom Fetch
                        </button>
                    </div>
                `;
            }
            
            // Poster image
            if (series.image_poster_large) {
                html += `
                    <div class="series-field-full">
                        <div class="field-label-block">Poster:</div>
                        <div class="field-value-block">
                            <img src="${this.escapeHtml(series.image_poster_large)}" 
                                 alt="Series Poster" 
                                 class="series-poster"
                                 onerror="this.style.display='none'">
                        </div>
                    </div>
                `;
            }
            
            html += `</div>`; // Close series-info-grid
            
        } 

        if (!detailsData.series_info || detailsPartiallyAvailable) {
            console.log('No series info available'); // Debug log
            html += `
            
                <div class="no-series-info">
                    <p>No series information available for this title.</p>
                    <div class="series-actions">
                        <button class="btn btn-small btn-primary" 
                                data-directory-hash="${this.escapeHtml(this.currentTitle?.directory_hash)}"
                                data-title="${this.escapeHtml(detailsData.title)}"
                                data-category="${this.escapeHtml(category)}"
                                onclick="admin.fetchSeriesMetadata(event)">
                            Fetch Metadata
                        </button>
                        <button class="btn btn-small btn-secondary" 
                                data-directory-hash="${this.escapeHtml(this.currentTitle?.directory_hash)}"
                                data-title="${this.escapeHtml(detailsData.title)}"
                                onclick="admin.editTitleHandler(event)">
                            Add Manually
                        </button>
                    </div>
                </div>

                <div class="no-series-info">
                    <p>No series information available for this title.</p>
                    <p>Fetch metadata separately for each episode/file in case each file is a separate movie.</p>
                    <p>Use this option when your folder contains individual movie files rather than episodes of a series. Each selected file will be treated as a standalone movie and searched for its own metadata.</p>
                    <div class="series-actions">
                        <button class="btn btn-small btn-info" onclick="admin.fetchMovieMetadataQuick()" disabled id="fetch-movie-metadata-quick-btn">
                            Quick Fetch (Anime Movies)
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="admin.fetchMovieMetadata()" disabled id="fetch-movie-metadata-btn">
                            Custom Fetch
                        </button>
                        <span class="movie-metadata-note">Select files above to enable these options</span>
                    </div>
                </div>
            `;
        }

        html += `
            </div>
        `; // Close details-section

        return html;
    }


    openCustomFetchModal(event) {
            const titleName = event.target.dataset.originalTitle;
            const episodeCount = event.target.dataset.episodeCount;
    
            console.log(`Title: ${titleName}, Episodes: ${episodeCount}`);
            const modalHTML = `
                <div id="custom-fetch-modal" class="details-panel active metadata-modal">
                    <div class="details-header">
                        <h3>Custom Metadata Fetch - ${this.escapeHtml(titleName)}</h3>
                        <button class="details-close" onclick="admin.closeCustomFetchModal()">&times;</button>
                    </div>
 
                    <div class="details-content metadata-content">
                        <div class="metadata-modal-body">
                            <!-- Left Column - Form -->
                            <div class="metadata-form-section">
                                <div class="edit-info">
                                    <strong>Custom Series Fetch:</strong> Enter a custom search term to find better series metadata.
                                    This will fetch series-level information that applies to all ${episodeCount} episodes.
                                </div>
                                
                                <form id="custom-fetch-form" onsubmit="admin.submitCustomFetch(event)">
                                    <!-- Hidden input for original title -->
                                    <input type="hidden" id="original-title" value="${this.escapeHtml(titleName)}">
          
                                    <div class="details-section">
                                        <h4>Search Settings</h4>
                 
                                        <div class="series-field">
                                            <span class="field-label">Custom Search Title:</span>
                                            <input type="text" id="custom-search-title" value="${this.escapeHtml(titleName)}" required class="field-input">
                                            <div class="field-help">Enter the exact series title you want to search for</div>
                                        </div>
                     
                                        <div class="form-row-details">
                                            <div class="series-field">
                                                <span class="field-label">Category:</span>
                                                <select id="custom-category" required class="field-input">
                                                    <option value="anime">Anime</option>
                                                    <option value="anime movies">Anime Movies</option>
                                                    <option value="tv shows">TV Shows</option>
                                                    <option value="movies">Movies</option>
                                                    <option value="cartoons">Cartoons</option>
                                                </select>
                                            </div>
                                            
                                            <div class="series-field">
                                                <span class="field-label">Use Cache:</span>
                                                <select id="custom-use-cache" class="field-input">
                                                    <option value="yes">Yes</option>
                                                    <option value="no">No (Fresh fetch)</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
          
                                    <div class="details-section">
                                        <h4>Target Series</h4>
                                        <div class="selected-episodes-info" style="background: #f8f9fa; padding: 15px; border-radius: 6px; border: 1px solid #e9ecef;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                <strong>Series: ${this.escapeHtml(titleName)}</strong>
                                                <span class="episode-count-badge" style="background: #007bff; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                                                    ${episodeCount} episodes
                                                </span>
                                            </div>
                                            <p style="margin: 0; font-size: 14px; color: #666;">
                                                Series-level metadata will be fetched and applied to all episodes in this series.
                                            </p>
                                        </div>
                                    </div>
                      
                                    <div class="form-actions-details">
                                        <button type="button" class="btn btn-secondary" onclick="admin.closeCustomFetchModal()">Cancel</button>
                                        <button type="submit" class="btn btn-primary">Start Custom Fetch</button>
                                    </div>
                                </form>
                            </div>
            
                            <!-- Right Column - Results -->
                            <div class="metadata-results-section">
                                <div class="details-section">
                                    <h4>Results</h4>
                                    <div class="results-summary">
                                        <span>Processed: <span id="custom-total-count">0</span></span> |
                                        <span>Success: <span id="custom-success-count">0</span></span> |
                                        <span>Failed: <span id="custom-fail-count">0</span></span>
                                    </div>
                                    <div id="results-container" class="results-container">
                                        <div class="results-placeholder">Results will appear here...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Prevent body scroll (consistent with your other modals)
            document.body.style.overflow = 'hidden';
            
            // Set focus to search input
            document.getElementById('custom-search-title').focus();
        }

    // Add the close method to match your pattern
    closeCustomFetchModal() {
        const modal = document.getElementById('custom-fetch-modal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }

    // NEW: Add the delete stale entry handler method
    async handleDeleteStaleEntry(event) {
        const button = event.target;
        const titleName = button.dataset.dbTitle;

        console.log('Deleting stale entry:', { titleName });

        // Show detailed confirmation dialog
        const confirmed = confirm(
            `⚠️ DELETE STALE ENTRY WARNING ⚠️\n\n` +
            `This will permanently delete the database entry for:\n"${titleName}"\n\n` +
            `This action will:\n` +
            `• Remove the title from the database\n` +
            `• Delete all associated episode records\n` +
            `• Remove series information and metadata\n` +
            `• Clean up thumbnails and cached data\n\n` +
            `This is recommended when video files no longer exist.\n\n` +
            `This action cannot be undone!\n\n` +
            `Are you sure you want to continue?`
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            this.showUpdateProgress('Deleting stale entry... This may take a moment.', false);
            
            // Prepare request data for stale entry deletion
            const requestData = {
                action: "delete_series_info",
                db_title: titleName,
                reason: "stale_entry" // Optional: helps backend understand the context
            };
            
            console.log('Sending delete stale entry request:', requestData);
            
            const response = await fetch('/admin/series-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Delete stale entry response:', result);
            
            if (result.success) {
                this.hideUpdateProgress();
                
                // Close details panel
                this.closeDetailsPanel();
                
                // Clear any selections
                this.selectedTitles.clear();
                this.selectedEpisodes.clear();
                this.updateBulkEditButton();
                
                // Refresh the titles list
                await this.loadTitles();
                
                // Show success message
                const message = result.message || `Successfully deleted stale entry for "${titleName}"`;
                this.showSuccessMessage(message);
                
                // Clear saved index since the item is deleted
                this.clearSavedIndex();
                
            } else {
                throw new Error(result.error || 'Delete operation failed');
            }
            
        } catch (error) {
            console.error('Delete stale entry error:', error);
            this.hideUpdateProgress();
            this.showErrorMessage('Failed to delete stale entry: ' + error.message);
        }
    }

    disableCustomFetchForm(disabled) {
        const form = document.getElementById('custom-fetch-form');
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, select, button');
        inputs.forEach(input => {
            input.disabled = disabled;
        });
        
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = disabled ? 'Processing...' : 'Start Custom Fetch';
        }
    }

    updateCustomFetchCounters(successCount, failCount) {
        const successEl = document.getElementById('custom-success-count');
        const failEl = document.getElementById('custom-fail-count');
        const totalEl = document.getElementById('custom-total-count');
        
        if (successEl) successEl.textContent = successCount;
        if (failEl) failEl.textContent = failCount;
        if (totalEl) totalEl.textContent = successCount + failCount;
    }

    async submitCustomFetch(event) {
        event.preventDefault();
        
        const customTitle = document.getElementById('custom-search-title').value.trim();
        const originalTitle = document.getElementById('original-title').value.trim();  // Get from hidden input
        const category = document.getElementById('custom-category').value;
        const useCache = document.getElementById('custom-use-cache').value;
        
        if (!customTitle) {
            alert('Please enter a custom search title');
            return;
        }
        
        // Clear results using existing method
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = '<div class="processing-status">Processing custom fetch...</div>';
        }
        
        // Disable form
        this.disableCustomFetchForm(true);
        
        try {
            let successCount = 0;
            let failCount = 0;
            
            // Process the series (not individual episodes)
            try {
                const requestData = {
                    suggested_title: customTitle,        // User's custom search term
                    series_type: category,
                    use_cache: useCache,
                    media_type: "video",
                    db_title: originalTitle,             // Original title from hidden input
                    series_title: originalTitle          // Original title from hidden input
                };
                
                const response = await fetch('/fetch_series_metadata', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    successCount++;
                    this.addResultItem(originalTitle, result.data, true);  // Use original title for display
                } else {
                    failCount++;
                    this.addResultItem(originalTitle, null, false, result.error || 'Unknown error');
                }
                
                this.updateCustomFetchCounters(successCount, failCount);
                
            } catch (error) {
                failCount++;
                this.addResultItem(originalTitle, null, false, error.message);
                this.updateCustomFetchCounters(successCount, failCount);
            }
            
            // Re-enable form
            this.disableCustomFetchForm(false);
            
            // Show completion message
            if (successCount > 0) {
                this.showMessage(`Custom fetch completed successfully!`, 'success');
                setTimeout(() => {
                    this.refreshCurrentTitle();
                }, 2000);
            } else {
                this.showMessage(`Custom fetch failed: ${failCount} errors`, 'error');
            }
            
        } catch (error) {
            console.error('Custom fetch error:', error);
            this.disableCustomFetchForm(false);
            alert(`Error during custom fetch: ${error.message}`);
        }
    }

    // NEW: Update movie metadata buttons based on selection
    updateMovieMetadataButtons() {
        const selectedCount = this.selectedEpisodes.size;
        const quickBtn = document.getElementById('fetch-movie-metadata-quick-btn');
        const customBtn = document.getElementById('fetch-movie-metadata-btn');
        
        if (quickBtn) {
            quickBtn.disabled = selectedCount === 0;
            if (selectedCount > 0) {
                quickBtn.textContent = `Quick Fetch (${selectedCount} files)`;
            } else {
                quickBtn.textContent = 'Quick Fetch (Anime Movies)';
            }
        }
        
        if (customBtn) {
            customBtn.disabled = selectedCount === 0;
            if (selectedCount > 0) {
                customBtn.textContent = `Custom Fetch (${selectedCount} files)`;
            } else {
                customBtn.textContent = 'Custom Fetch';
            }
        }
    }

    // UPDATED: Fetch series metadata using directory_hash
    async fetchSeriesMetadata(event) {
        const button = event.target;
        const directoryHash = button.dataset.directoryHash;
        const titleName = button.dataset.title;
        const category = button.dataset.category;
        console.log('Fetching metadata for:', { directoryHash, titleName, category });

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
                series_type: category, // Default to anime, could be made configurable
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
    selectAllEpisodes(event) {
        const button = event.target;
        const seriesTitle = button.dataset.seriesTitle;
    
        // Your existing select all logic here
        console.log('Selecting all episodes for:', seriesTitle);

        const checkboxes = document.querySelectorAll('.episode-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            this.selectedEpisodes.add(checkbox.dataset.path);
        });
        this.updateSelectionUI();
    }

    deselectAllEpisodes(event) {
        const button = event.target;
        const seriesTitle = button.dataset.seriesTitle;
    
        // Your existing deselect all logic here
        console.log('Deselecting all episodes for:', seriesTitle);

        const checkboxes = document.querySelectorAll('.episode-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            this.selectedEpisodes.delete(checkbox.dataset.path);
        });
        this.updateSelectionUI();
    }

    openSinglePathEditModal(event) {
        const button = event.target;
        const videoPath = button.dataset.episodePath;
        const episodeTitle = button.dataset.episodeTitle;
        const seriesTitle = button.dataset.seriesTitle;
        
        // Your existing edit logic here
        console.log('Editing episode:', {
            path: videoPath,
            episode: episodeTitle,
            series: seriesTitle
        });
        const modalHTML = `
            <div id="edit-modal" class="details-panel active">
                <div class="details-header">
                    <h3>Edit Single Episode</h3>
                    <button class="details-close" onclick="admin.closeEditModal()">&times;</button>
                </div>
                
                <div class="details-content">
                    <div class="edit-info">
                        Editing individual episode title.
                    </div>
                    
                    <form id="edit-form" onsubmit="admin.submitSinglePathEdit(event)">
                        <input type="hidden" id="video-path" value="${this.escapeHtml(videoPath)}">
                        
                        <div class="details-section">
                            <h4>Series Information</h4>
                            <div class="series-field">
                                <span class="field-label">Series Title:</span>
                                <input type="text" id="path-series-title" value="${this.escapeHtml(seriesTitle)}" placeholder="Enter series title" required class="field-input">
                            </div>
                            <h4>Episode Information</h4>
                            <div class="series-field">
                                <span class="field-label">Episode Title:</span>
                                <input type="text" id="path-new-ep-title" value="${this.escapeHtml(episodeTitle)}" placeholder="Enter episode title" required class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Episode Path:</span>
                                <div class="field-value path-display">${this.escapeHtml(videoPath)}</div>
                            </div>
                        </div>

                        <div class="form-actions-details">
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Cancel</button>
                            <button type="submit" class="btn btn-primary">Update Episode</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.style.overflow = 'hidden';
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
            <div id="edit-modal" class="details-panel active">
                <div class="details-header">
                    <h3>Edit Multiple Episodes</h3>
                    <button class="details-close" onclick="admin.closeEditModal()">&times;</button>
                </div>
                
                <div class="details-content">
                    <div class="edit-info">
                        Editing ${pathsToSend.length} episode(s). Only the title will be updated.
                    </div>
                    
                    <form id="edit-form" onsubmit="admin.submitMultiplePathsEdit(event)">
                        
                        <div class="details-section">
                            <h4>Episode Information</h4>
                            <div class="series-field">
                                <span class="field-label">New Title:</span>
                                <input type="text" id="paths-new-title" placeholder="Enter new title for all selected episodes" required class="field-input">
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Selected Episodes (${pathsToSend.length})</h4>
                            <div class="episode-list">
                                ${pathsToSend.map(path => `
                                    <div class="episode-item">
                                        <div class="episode-details">
                                            <div class="episode-path">${this.escapeHtml(path)}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="form-actions-details">
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">Cancel</button>
                            <button type="submit" class="btn btn-primary">Update All</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.style.overflow = 'hidden';
    }

    

    openBulkMetadataModal(selectedTitles) {
    const savedCategory = this.getCategoryPreference();

    const modalHTML = `
        <div id="metadata-modal" class="details-panel active metadata-modal">
            <div class="details-header">
                <h3>Fetch Metadata for ${selectedTitles.length} Titles</h3>
                <button class="details-close" onclick="admin.closeBulkMetadataModal()">&times;</button>
            </div>

            <div class="details-content metadata-content">
                <div class="metadata-modal-body">
                    <!-- Left side: Form -->
                    <div class="metadata-form-section">
                        <form id="metadata-form" onsubmit="admin.submitBulkMetadata(event)">
                            <input type="hidden" id="selected-titles-metadata" value='${this.safeJsonEncode(selectedTitles)}'>
                            
                            <div class="details-section">
                                <h4>Metadata Settings</h4>
                                <div class="series-field">
                                    <span class="field-label">Category:</span>
                                    <select id="metadata-category" required class="field-input">
                                        <option value="">Select Category</option>
                                        <option value="anime" ${savedCategory === 'anime' ? 'selected' : ''}>Anime</option>
                                        <option value="anime movies" ${savedCategory === 'anime movies' ? 'selected' : ''}>Anime Movies</option>
                                        <option value="tv shows" ${savedCategory === 'tv shows' ? 'selected' : ''}>TV Shows</option>
                                        <option value="movies" ${savedCategory === 'movies' ? 'selected' : ''}>Movies</option>
                                        <option value="cartoons" ${savedCategory === 'cartoons' ? 'selected' : ''}>Cartoons</option>
                                    </select>
                                </div>
                                
                                <div class="checkbox-field">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="use-cache">
                                        <span>Use cached data if available</span>
                                    </label>
                                </div>
                            </div>

                            <div class="details-section">
                                <h4>Provide Exact Search Terms</h4>
                                <div class="titles-metadata-list">
                                    ${selectedTitles.map((title, index) => `
                                        <div class="title-metadata-item">
                                            <div class="series-field">
                                                <span class="field-label">Original:</span>
                                                <div class="field-value">${this.escapeHtml(title)}</div>
                                            </div>
                                            <div class="series-field">
                                                <span class="field-label">Search Term:</span>
                                                <input type="text" id="search-title-${index}"
                                                       value="${this.escapeHtml(title)}"
                                                       placeholder="Enter exact title for search"
                                                       data-original-title="${this.escapeHtml(title)}"
                                                       required class="field-input">
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>

                            <div class="form-actions-details">
                                <button type="button" class="btn btn-secondary" onclick="admin.closeBulkMetadataModal()">Cancel</button>
                                <button type="submit" class="btn btn-primary">Fetch Metadata</button>
                            </div>
                        </form>
                    </div>

                    <!-- Right side: Results -->
                    <div class="metadata-results-section">
                        <div class="details-section">
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
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    document.body.style.overflow = 'hidden';
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
        const useCache = document.getElementById('use-cache').checked ? "yes" : "no";

        // Save the category preference when form is submitted
        if (category) {
            this.saveCategoryPreference(category);
    }
        
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
                        from_cache: useCache
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

    editTitleHandler(event) {
        // Get data from the button's data attributes
        const button = event.target;
        const directoryHash = button.dataset.directoryHash;
        const titleName = button.dataset.title;
        console.log('Editing title:', titleName, 'Hash:', directoryHash);
        this.editTitle(directoryHash, titleName)
    }
   
    async editTitle(directoryHash, titleName) {
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
    // Update the handleBulkEdit method to remove the placeholder message
    handleBulkEdit() {
        const selectedTitles = Array.from(this.selectedTitles);
        if (selectedTitles.length === 0) {
            alert('Please select at least one title for bulk editing.');
            return;
        }

        // Convert directory hashes to title objects for display
        const selectedTitleObjects = selectedTitles.map(hash => {
            const title = this.titles.find(t => t.directory_hash === hash);
            return title ? { title: title.title, directory_hash: title.directory_hash } : null;
        }).filter(title => title !== null);

        this.openBulkEditModal(selectedTitleObjects);
    }

    // UPDATED: Single title edit modal using details-panel structure with ALL fields
    
    // UPDATED: Single title edit modal with soft delete button
    openEditModal(directoryHash, titleName, seriesData, episodesList) {
        const title = this.titles.find(t => t.directory_hash === directoryHash);
        if (!title) return;

        const series = seriesData || {};
        const pathsToSend = episodesList || [];
        
        // Get existing values or defaults for new fields
        const multiAudio = series.multi_audio === 'yes' || series.multi_audio === true;
        const multiSubtitle = series.multi_subtitle === 'yes' || series.multi_subtitle === true;
        const ignore = series.ignore === 'yes' || series.ignore === true;
        const labels = series.labels || '';
        const category = series.category || '';
        const collectionName = series.collection_name || '';
        
        const modalHTML = `
            <div id="edit-modal" class="details-panel active">
                <div class="details-header">
                    <h3>Edit: ${this.escapeHtml(titleName)}</h3>
                    <button class="details-close" onclick="admin.closeEditModal()">&times;</button>
                </div>
                
                <div class="details-content">
                    <div class="edit-info">
                        Editing ${pathsToSend.length} episode(s). Empty fields will not be updated.
                    </div>
                    
                    <form id="edit-form" onsubmit="admin.submitEdit(event)">
                        <input type="hidden" id="original-title" value="${this.escapeHtml(titleName)}">
                        <input type="hidden" id="directory-hash" value="${this.escapeHtml(directoryHash)}">
                        
                        <div class="details-section">
                            <h4>Video Information</h4>
                            <div class="series-field">
                                <span class="field-label">New Title:</span>
                                <input type="text" id="new-title" value="${this.escapeHtml(titleName)}" placeholder="Enter new title" class="field-input">
                            </div>
                            
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">Category:</span>
                                    <input type="text" id="category" value="${this.escapeHtml(category)}" placeholder="e.g., anime, tv shows, movies" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Collection Name:</span>
                                    <input type="text" id="collection-name" value="${this.escapeHtml(collectionName)}" placeholder="Collection or series name" class="field-input">
                                </div>
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Labels:</span>
                                <input type="text" id="labels" value="${this.escapeHtml(labels)}" placeholder="Comma-separated labels" class="field-input">
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Media Properties</h4>
                            
                            <div class="form-row-details">
                                <div class="checkbox-field">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="multi-audio" ${multiAudio ? 'checked' : ''}>
                                        <span>Multi-Audio</span>
                                    </label>
                                </div>
                                
                                <div class="checkbox-field">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="multi-subtitle" ${multiSubtitle ? 'checked' : ''}>
                                        <span>Multi-Subtitle</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Collection Settings</h4>
                            <div class="checkbox-field special-ignore">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="ignore" ${ignore ? 'checked' : ''}>
                                    <span>Ignore (Don't include in video collection)</span>
                                </label>
                                <div class="field-help">
                                    When checked, this title will be excluded from the main video collection display.
                                </div>
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Series Information</h4>
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">DB Title:</span>
                                    <input type="text" id="db-title" value="${this.escapeHtml(series.db_title || '')}" placeholder="Database title" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Display Title:</span>
                                    <input type="text" id="display-title" value="${this.escapeHtml(series.title || '')}" placeholder="Display title" class="field-input">
                                </div>
                            </div>
                            
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">English Title:</span>
                                    <input type="text" id="english-title" value="${this.escapeHtml(series.english_title || '')}" placeholder="English title" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Year:</span>
                                    <input type="number" id="year" value="${series.year || ''}" placeholder="Release year" class="field-input">
                                </div>
                            </div>
                            
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">Total Episodes:</span>
                                    <input type="number" id="episodes" value="${series.episodes || ''}" placeholder="Total episodes" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Score:</span>
                                    <input type="number" step="0.1" id="score" value="${series.score || ''}" placeholder="Rating score" class="field-input">
                                </div>
                            </div>
                            
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">Rank:</span>
                                    <input type="number" id="rank" value="${series.rank || ''}" placeholder="Ranking" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Popularity:</span>
                                    <input type="number" id="popularity" value="${series.popularity || ''}" placeholder="Popularity rank" class="field-input">
                                </div>
                            </div>
                            
                            <div class="form-row-details">
                                <div class="series-field">
                                    <span class="field-label">Type:</span>
                                    <input type="text" id="type" value="${this.escapeHtml(series.type || '')}" placeholder="e.g., TV, Movie, OVA, Special" class="field-input">
                                </div>
                                <div class="series-field">
                                    <span class="field-label">Duration:</span>
                                    <input type="text" id="duration" value="${this.escapeHtml(series.duration || '')}" placeholder="Episode duration" class="field-input">
                                </div>
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Genres:</span>
                                <input type="text" id="genres" value="${this.escapeHtml(series.genres || '')}" placeholder="Comma-separated genres" class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">External ID:</span>
                                <input type="number" id="external-id" value="${series.external_id || ''}" placeholder="External database ID" class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Poster Image:</span>
                                <input type="text" id="image-poster" value="${this.escapeHtml(series.image_poster_large || '')}" placeholder="Poster image URL or path" class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Summary:</span>
                                <textarea id="summary" rows="4" placeholder="Series summary" class="field-input">${this.escapeHtml(series.summary || '')}</textarea>
                            </div>
                        </div>

                        <div class="form-actions-details">
                            <button type="button" class="btn btn-secondary" onclick="admin.closeEditModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                Save Changes
                            </button>
                            <button type="button" class="btn btn-soft-delete soft-delete-btn" 
                                    data-directory-hash="${this.escapeHtml(directoryHash)}"
                                    data-title-name="${this.escapeHtml(titleName)}"
                                    onclick="admin.handleSoftDeleteSingle(event)">
                                Soft Delete
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.style.overflow = 'hidden';
    }


    // NEW: Handle soft delete for single title
    async handleSoftDeleteSingle(event) {
        const button = event.target;
        const directoryHash = button.dataset.directoryHash;
        const titleName = button.dataset.titleName;
    
        // Your existing soft delete logic here
        console.log('Soft deleting:', { directoryHash, titleName });

        // Show confirmation dialog with detailed warning
        const confirmed = confirm(
            `⚠️ SOFT DELETE WARNING ⚠️\n\n` +
            `This will soft delete: "${titleName}"\n\n` +
            `This action will:\n` +
            `• Remove all episodes from the database\n` +
            `• Delete series information\n` +
            `• Clean up thumbnails and metadata\n` +
            `• Files will remain on disk (manual deletion required)\n\n` +
            `This action cannot be undone!\n\n` +
            `Are you absolutely sure you want to continue?`
        );
        
        if (!confirmed) {
            return;
        }
        
        // Third confirmation with text input
        const userInput = prompt(
            `Please type "DELETE" (in capital letters) to confirm the soft deletion of:\n\n"${titleName}"`
        );
        
        if (userInput !== "DELETE") {
            alert("Soft delete cancelled. You must type 'DELETE' exactly to confirm.");
            return;
        }
        
        try {
            this.showUpdateProgress('Performing soft delete... This may take a moment.', false);
            
            // Prepare request data according to your contract
            const requestData = {
                action: "soft-delete",
                title: titleName,
                directory_hash: directoryHash
            };
            
            console.log('Sending soft delete request:', requestData);
            
            const response = await fetch('/admin/series-soft-delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Soft delete response:', result);
            
            if (result.success) {
                this.hideUpdateProgress();
                this.closeEditModal();
                
                // Close details panel if open
                const detailsPanel = document.getElementById('details-panel');
                if (detailsPanel && detailsPanel.classList.contains('active')) {
                    this.closeDetailsPanel();
                }
                
                // Clear any selections
                this.selectedTitles.clear();
                this.selectedEpisodes.clear();
                this.updateBulkEditButton();
                
                // Refresh the titles list
                await this.loadTitles();
                
                // Show success message
                const message = result.message || `Successfully soft deleted "${titleName}"`;
                this.showSuccessMessage(message);
                
                // Clear saved index since the item is deleted
                this.clearSavedIndex();
                
            } else {
                throw new Error(result.error || 'Soft delete failed');
            }
            
        } catch (error) {
            console.error('Soft delete error:', error);
            this.hideUpdateProgress();
            this.showErrorMessage('Soft delete failed: ' + error.message);
        }
    }

    // Update the openBulkEditModal method to include the new fields
    
    // UPDATED: Bulk edit modal using details-panel structure
    openBulkEditModal(selectedTitles) {
        if (selectedTitles.length === 0) {
            alert('Please select titles to edit');
            return;
        }
        console.log(selectedTitles)

        const modalHTML = `
            <div id="bulk-edit-modal" class="details-panel active">
                <div class="details-header">
                    <h3>Bulk Edit ${selectedTitles.length} Titles</h3>
                    <button class="details-close" onclick="admin.closeBulkEditModal()">&times;</button>
                </div>
                
                <div class="details-content">
                    <div class="edit-info">
                        Editing ${selectedTitles.length} titles. Only filled fields will be updated. Empty fields will be ignored.
                    </div>
                    
                    <form id="bulk-edit-form" onsubmit="admin.submitBulkEdit(event)">
                        <input type="hidden" id="selected-items" value='${this.safeJsonEncode(selectedTitles)}'>
                        <div class="details-section">
                            <h4>Video Information</h4>
                            
                            <div class="series-field">
                                <span class="field-label">Category:</span>
                                <input type="text" id="bulk-category" placeholder="e.g., anime, tv shows, movies" class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Collection Name:</span>
                                <input type="text" id="bulk-collection-name" placeholder="Collection or series name" class="field-input">
                            </div>
                            
                            <div class="series-field">
                                <span class="field-label">Labels:</span>
                                <input type="text" id="bulk-labels" placeholder="Comma-separated labels" class="field-input">
                            </div>
 
                            <div class="series-field">
                                <span class="field-label">Poster Image:</span>
                                <input type="text" id="bulk-image-poster" placeholder="Link to image" class="field-input">
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Media Properties</h4>
                            
                            <div class="form-row-details">
                                <div class="checkbox-field">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="bulk-multi-audio">
                                        <span>Multi-Audio</span>
                                    </label>
                                </div>
                                
                                <div class="checkbox-field">
                                    <label class="checkbox-label">
                                        <input type="checkbox" id="bulk-multi-subtitle">
                                        <span>Multi-Subtitle</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Collection Settings</h4>
                            <div class="checkbox-field special-ignore">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="bulk-ignore">
                                    <span>Ignore (Don't include in video collection)</span>
                                </label>
                                <div class="field-help">
                                    When checked, selected titles will be excluded from the main video collection display.
                                </div>
                            </div>
                        </div>

                        <div class="details-section">
                            <h4>Selected Titles</h4>
                            <div class="episode-list">
                                ${selectedTitles.map(title => `
                                    <div class="episode-item">
                                        <div class="episode-details">
                                            <div class="episode-name">${this.escapeHtml(title.title)}</div>
                                            <div class="episode-path">ID: ${this.escapeHtml(title.directory_hash)}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <div class="form-actions-details">
                            <button type="button" class="btn btn-secondary" onclick="admin.closeBulkEditModal()">Cancel</button>
                            <button type="submit" class="btn btn-primary">Apply Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.style.overflow = 'hidden';
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

    closeBulkEditModal() {
        const modal = document.getElementById('bulk-edit-modal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }

    // UPDATED: Submit edit with checkbox handling
    async submitEdit(event) {
        event.preventDefault();
        
        const selectedPathsElement = document.getElementById('selected-paths');
        const selectedPathsValue = selectedPathsElement ? selectedPathsElement.value : '[]';
        
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
            directory_hash: document.getElementById('directory-hash').value,
            selected_paths: selectedPaths,
            new_title: document.getElementById('new-title').value.trim()
        };
        
        // Add text fields
        const textFields = ['category', 'collection-name', 'labels'];
        textFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            const value = element ? element.value.trim() : '';
            if (value) {
                const fieldName = fieldId.replace('-', '_');
                formData[fieldName] = value;
            }
        });
        
        // Add checkbox values - always include these to ensure they can be unset
        const checkboxFields = ['multi-audio', 'multi-subtitle', 'ignore'];
        checkboxFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                const fieldName = fieldId.replace('-', '_');
                formData[fieldName] = element.checked ? 'yes' : 'no';
            }
        });
        
        // Add existing series fields - only if not empty
        const existingFields = [
            'db-title', 'display-title', 'english-title', 'year', 'episodes', 
            'score', 'rank', 'popularity', 'type', 'duration', 'genres', 
            'external-id', 'image-poster', 'summary'
        ];
        
        existingFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            const value = element ? element.value.trim() : '';
            if (value) {
                const fieldName = fieldId.replace('-', '_');
                formData[fieldName] = value;
            }
        });

        console.log("Form data to send:", formData);

        try {
            this.showUpdateProgress('Updating...');
            
            const response = await fetch('/admin/series-update', {
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
            new_ep_title: document.getElementById('path-new-ep-title').value.trim(),
            new_series_title: document.getElementById('path-series-title').value.trim()
        };

        console.log("Single path form data to send:", formData); // Debug log

        try {
            this.showUpdateProgress('Updating episode...');
            
            const response = await fetch('/admin/series-update', {
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
            
            const response = await fetch('/admin/series-update', {
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

    // NEW: Movie metadata methods
    fetchMovieMetadata() {
        if (this.selectedEpisodes.size === 0) {
            alert('Please select at least one movie file for metadata fetching.');
            return;
        }

        // Get movie details for selected files
        const selectedMovieData = [];
        const episodeElements = document.querySelectorAll('.episode-checkbox:checked');
        
        episodeElements.forEach(checkbox => {
            const episodeItem = checkbox.closest('.episode-item');
            const movieName = episodeItem.querySelector('.episode-name').textContent;
            const moviePath = checkbox.dataset.path;
            
            selectedMovieData.push({
                path: moviePath,
                title: movieName
            });
        });

        this.openMovieMetadataModal(selectedMovieData);
    }

    // NEW: Quick fetch for anime movies
    
    async fetchMovieMetadataQuick() {
        if (this.selectedEpisodes.size === 0) {
            alert('Please select at least one movie file for metadata fetching.');
            return;
        }

        // Get movie details for selected files
        const selectedMovieData = [];
        const episodeElements = document.querySelectorAll('.episode-checkbox:checked');
        
        const selectedMovieTitles = [];
        episodeElements.forEach(checkbox => {
            const episodeItem = checkbox.closest('.episode-item');
            const movieName = episodeItem.querySelector('.episode-name').textContent;
            const moviePath = checkbox.dataset.path;
            
            selectedMovieData.push({
                path: moviePath,
                title: movieName
            });

            selectedMovieTitles.push(movieName);
        });

        const confirmed = confirm(`Fetch metadata for "${selectedMovieTitles}"?\n\nThis will search for series information online.`);
        if (!confirmed) return;

        console.log("Quick fetching movie metadata for:", selectedMovieData);

        // Show progress indicator with results container
        this.showQuickFetchProgressWithResultsContainer(selectedMovieData.length);

        let successCount = 0;
        let failCount = 0;

        try {
            // Process each movie file
            for (let i = 0; i < selectedMovieData.length; i++) {
                const movie = selectedMovieData[i];
                
                try {
                    console.log(`Processing movie ${i + 1}/${selectedMovieData.length}: ${movie.title}`);
                    
                    // Update progress before processing
                    this.updateQuickFetchProgress(i, selectedMovieData.length, successCount, failCount, `Processing: ${movie.title}`);
                    
                    // Prepare the request data
                    const requestData = {
                        suggested_title: "",
                        series_type: "anime movies",
                        single_episode_title: movie.title,
                        single_episode_path: movie.path,
                        use_cache: "yes",
                        media_type: "video"
                    };

                    // Make the API call
                    const response = await fetch('/fetch_series_metadata', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestData)
                    });

                    const result = await response.json();
                    console.log(`Result for ${movie.title}:`, result);

                    if (result.success) {
                        successCount++;
                        // USE EXISTING addResultItem METHOD
                        this.addResultItem(movie.title, result.data, true);
                    } else {
                        failCount++;
                        // USE EXISTING addResultItem METHOD
                        this.addResultItem(movie.title, null, false, result.error || 'Unknown error');
                    }

                    // Update progress after processing
                    this.updateQuickFetchProgress(i + 1, selectedMovieData.length, successCount, failCount, 
                        i + 1 === selectedMovieData.length ? 'Completed!' : `Processed: ${movie.title}`);

                    // Small delay between requests
                    if (i < selectedMovieData.length - 1) {
                        await new Promise(resolve => setTimeout(resolve, 500));
                    }

                } catch (error) {
                    console.error(`Error processing ${movie.title}:`, error);
                    failCount++;
                    // USE EXISTING addResultItem METHOD
                    this.addResultItem(movie.title, null, false, error.message);
                    
                    this.updateQuickFetchProgress(i + 1, selectedMovieData.length, successCount, failCount, 
                        `Error: ${movie.title}`);
                }
            }

            // Refresh the current view if there were successes
            if (successCount > 0) {
                setTimeout(() => {
                    this.refreshCurrentTitle();
                }, 3000);
            }

        } catch (error) {
            console.error("Error in quick fetch:", error);
            this.hideQuickFetchProgress();
            this.showErrorMessage(`Error during quick fetch: ${error.message}`);
        }
    }

    // NEW: Open movie metadata modal
    openMovieMetadataModal(selectedMovies) {
        const savedCategory = this.getCategoryPreference();

        const modalHTML = `
            <div id="movie-metadata-modal" class="details-panel active metadata-modal">
                <div class="details-header">
                    <h3>Fetch Movie Metadata for ${selectedMovies.length} Movies</h3>
                    <button class="details-close" onclick="admin.closeMovieMetadataModal()">&times;</button>
                </div>

                <div class="details-content metadata-content">
                    <div class="metadata-modal-body">
                        <!-- Left side: Form -->
                        <div class="metadata-form-section">
                            <form id="movie-metadata-form" onsubmit="admin.submitMovieMetadata(event)">
                                <input type="hidden" id="selected-movies-metadata" value='${this.safeJsonEncode(selectedMovies)}'>
                                
                                <div class="details-section">
                                    <h4>Metadata Settings</h4>
                                    <div class="series-field">
                                        <span class="field-label">Category:</span>
                                        <select id="movie-metadata-category" required class="field-input">
                                            <option value="">Select Category</option>
                                            <option value="anime movies" ${savedCategory === 'anime movies' ? 'selected' : 'selected'}>Anime Movies</option>
                                            <option value="movies" ${savedCategory === 'movies' ? 'selected' : ''}>Movies</option>
                                            <option value="anime" ${savedCategory === 'anime' ? 'selected' : ''}>Anime</option>
                                            <option value="cartoons" ${savedCategory === 'cartoons' ? 'selected' : ''}>Cartoons</option>
                                            <option value="tv shows" ${savedCategory === 'tv shows' ? 'selected' : ''}>TV Shows</option>
                                        </select>
                                    </div>
                                    
                                    <div class="checkbox-field">
                                        <label class="checkbox-label">
                                            <input type="checkbox" id="movie-use-cache" checked>
                                            <span>Use cached data if available</span>
                                        </label>
                                    </div>
                                </div>

                                <div class="details-section">
                                    <h4>Movie Search Terms</h4>
                                    <div class="movie-info-note">
                                        <p><strong>Note:</strong> Each file will be treated as an individual movie. Provide the exact movie title for best results.</p>
                                    </div>
                                    <div class="titles-metadata-list">
                                        ${selectedMovies.map((movie, index) => `
                                            <div class="title-metadata-item">
                                                <div class="series-field">
                                                    <span class="field-label">File:</span>
                                                    <div class="field-value">${this.escapeHtml(movie.title)}</div>
                                                </div>
                                                <div class="series-field">
                                                    <span class="field-label">Movie Title:</span>
                                                    <input type="text" id="movie-title-${index}"
                                                           value="${this.escapeHtml(movie.title)}"
                                                           placeholder="Enter exact movie title for search"
                                                           data-movie-path="${this.escapeHtml(movie.path)}"
                                                           required class="field-input">
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>

                                <div class="form-actions-details">
                                    <button type="button" class="btn btn-secondary" onclick="admin.closeMovieMetadataModal()">Cancel</button>
                                    <button type="submit" class="btn btn-primary">Fetch Movie Metadata</button>
                                </div>
                            </form>
                        </div>

                        <!-- Right side: Results -->
                        <div class="metadata-results-section">
                            <div class="details-section">
                                <h4>Results</h4>
                                <div class="results-summary" id="movie-results-summary">
                                    <span id="movie-success-count">0</span> successful,
                                    <span id="movie-fail-count">0</span> failed
                                </div>
                                <div class="results-container" id="results-container">
                                    <div class="results-placeholder">
                                        Results will appear here as movie metadata is fetched...
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        document.body.style.overflow = 'hidden';
    }

    // NEW: Close movie metadata modal
    closeMovieMetadataModal() {
        const modal = document.getElementById('movie-metadata-modal');
        if (modal) {
            modal.remove();
            document.body.style.overflow = '';
        }
    }

    // NEW: Submit movie metadata
    async submitMovieMetadata(event) {
        event.preventDefault();
        
        const selectedMoviesElement = document.getElementById('selected-movies-metadata');
        const selectedMoviesValue = selectedMoviesElement ? selectedMoviesElement.value : '[]';
        
        let selectedMovies;
        try {
            selectedMovies = JSON.parse(selectedMoviesValue);
        } catch (e) {
            console.error("Error parsing selected movies:", e);
            selectedMovies = [];
        }
        
        const category = document.getElementById('movie-metadata-category').value;
        const useCache = document.getElementById('movie-use-cache').checked ? "yes" : "no";

        // Save the category preference
        if (category) {
            this.saveCategoryPreference(category);
        }
        
        // Collect movie titles for each file
        const movieMappings = [];
        selectedMovies.forEach((movie, index) => {
            const titleInput = document.getElementById(`movie-title-${index}`);
            if (titleInput) {
                movieMappings.push({
                    movie_path: movie.path,
                    original_title: movie.title,
                    single_episode_title: titleInput.value.trim()
                });
            }
        });

        console.log("Processing movie metadata for:", movieMappings);

        // Clear results and show processing
        this.clearMovieResults();
        this.disableMovieForm(true);

        try {
            let successCount = 0;
            let failCount = 0;

            // Process each movie
            for (const mapping of movieMappings) {
                try {
                    console.log(`Processing movie: ${mapping.single_episode_title}`);
                    
                    // Prepare the request data
                    const requestData = {
                        suggested_title: "",
                        series_type: category,
                        single_episode_title: mapping.single_episode_title,
                        single_episode_path: mapping.movie_path,
                        use_cache: useCache,
                        media_type: "video"
                    };

                    console.log("Sending request:", requestData);

                    // Make the API call
                    const response = await fetch('/fetch_series_metadata', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestData)
                    });

                    const result = await response.json();
                    console.log(`Result for ${mapping.single_episode_title}:`, result);

                    if (result.success) {
                        successCount++;
                        // USE EXISTING addResultItem METHOD
                        this.addResultItem(mapping.single_episode_title, result.data, true);
                    } else {
                        failCount++;
                        // USE EXISTING addResultItem METHOD
                        this.addResultItem(mapping.single_episode_title, null, false, result.error || 'Unknown error');
                    }

                    // Update counters (if this method exists, otherwise remove)
                    if (typeof this.updateMovieResultCounters === 'function') {
                        this.updateMovieResultCounters(successCount, failCount);
                    }

                } catch (error) {
                    console.error(`Error processing ${mapping.single_episode_title}:`, error);
                    failCount++;
                    // USE EXISTING addResultItem METHOD
                    this.addResultItem(mapping.single_episode_title, null, false, error.message);
                    
                    // Update counters (if this method exists, otherwise remove)
                    if (typeof this.updateMovieResultCounters === 'function') {
                        this.updateMovieResultCounters(successCount, failCount);
                    }
                }
            }

            console.log(`Movie metadata fetch completed. Success: ${successCount}, Failed: ${failCount}`);

            // Re-enable form
            this.disableMovieForm(false);

            // Refresh the current view if there were successes
            if (successCount > 0) {
                setTimeout(() => {
                    this.refreshCurrentTitle();
                }, 2000);
            }

        } catch (error) {
            console.error("Error in movie metadata submission:", error);
            this.disableMovieForm(false);
            alert(`Error during movie metadata fetch: ${error.message}`);
        }
    }

    // NEW: Movie result management methods
    clearMovieResults() {
        const container = document.getElementById('movie-results-container');
        if (container) {
            container.innerHTML = '<div class="results-placeholder">Processing...</div>';
        }
        this.updateMovieResultCounters(0, 0);
    }

    addMovieResult(movieTitle, status, data) {
        const container = document.getElementById('movie-results-container');
        if (!container) return;

        // Remove placeholder if it exists
        const placeholder = container.querySelector('.results-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const resultHTML = `
            <div class="result-item ${status}">
                <div class="result-header">
                    <span class="result-status ${status}">${status === 'success' ? '✓' : '✗'}</span>
                    <span class="result-title">${this.escapeHtml(movieTitle)}</span>
                </div>
                <div class="result-details">
                    ${status === 'success' ? 
                        `<div class="success-details">Metadata fetched successfully</div>` :
                        `<div class="error-details">Error: ${this.escapeHtml(data)}</div>`
                    }
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', resultHTML);
        container.scrollTop = container.scrollHeight;
    }

    updateMovieResultCounters(successCount, failCount) {
        const successElement = document.getElementById('movie-success-count');
        const failElement = document.getElementById('movie-fail-count');
        
        if (successElement) successElement.textContent = successCount;
        if (failElement) failElement.textContent = failCount;
    }

    disableMovieForm(disabled) {
        const form = document.getElementById('movie-metadata-form');
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, button[type="submit"]');
        inputs.forEach(input => {
            input.disabled = disabled;
        });

        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.textContent = disabled ? 'Processing...' : 'Fetch Movie Metadata';
        }
    }

    // NEW: Quick fetch progress methods (continued)
    
    // MODIFIED: Show progress with results-container (to match your existing method)
    showQuickFetchProgressWithResultsContainer(totalCount) {
        const existing = document.getElementById('quick-fetch-progress');
        if (existing) existing.remove();
        
        const progressDiv = document.createElement('div');
        progressDiv.id = 'quick-fetch-progress';
        progressDiv.className = 'quick-fetch-progress';
        progressDiv.innerHTML = `
            <div class="progress-overlay"></div>
            <div class="progress-content">
                <div class="progress-header">
                    <h4>Quick Fetch Progress</h4>
                    <button onclick="admin.hideQuickFetchProgress()" class="close-btn">&times;</button>
                </div>
                <div class="progress-status" id="quick-progress-status">
                    Initializing...
                </div>
                <div class="progress-stats">
                    <span id="quick-progress-current">0</span> of <span id="quick-progress-total">${totalCount}</span> processed
                    | <span id="quick-progress-success">0</span> successful
                    | <span id="quick-progress-failed">0</span> failed
                </div>
                <div class="progress-bar">
                    <div id="quick-progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="results-section">
                    <h5>Results:</h5>
                    <div id="results-container" class="results-container">
                        <!-- Results will use existing addResultItem method -->
                    </div>
                </div>
                <div class="progress-actions">
                    <button onclick="admin.hideQuickFetchProgress()" class="btn btn-primary">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(progressDiv);
    }

    updateQuickFetchProgress(current, total, success, failed) {
        const currentEl = document.getElementById('quick-progress-current');
        const successEl = document.getElementById('quick-progress-success');
        const failedEl = document.getElementById('quick-progress-failed');
        const fillEl = document.getElementById('quick-progress-fill');
        
        if (currentEl) currentEl.textContent = current;
        if (successEl) successEl.textContent = success;
        if (failedEl) failedEl.textContent = failed;
        if (fillEl) {
            const percentage = (current / total) * 100;
            fillEl.style.width = `${percentage}%`;
        }
    }

    showQuickFetchResults(results, successCount, failCount) {
        const progressDiv = document.getElementById('quick-fetch-progress');
        if (!progressDiv) return;
        
        const resultsHTML = `
            <div class="progress-content">
                <div class="progress-header">
                    <h4>Quick Fetch Results</h4>
                    <button onclick="admin.hideQuickFetchProgress()" class="close-btn">&times;</button>
                </div>
                <div class="progress-stats final">
                    Completed: ${successCount} successful, ${failCount} failed
                </div>
                
                <div class="results-list">
                    ${results.map(result => `
                        <div class="result-item ${result.status}">
                            ${result.status === 'success' && result.data && result.data.image_poster_large ? 
                                `<img class="result-poster" src="${result.data.image_poster_large}" alt="${this.escapeHtml(result.movie)} Poster" onerror="this.style.display='none';">` : 
                                ''
                            }
                            <div class="result-content">
                                <span class="result-icon">${result.status === 'success' ? '✓' : '✗'}</span>
                                <span class="result-movie">${this.escapeHtml(result.movie)}</span>
                                ${result.status === 'failed' ? 
                                    `<span class="result-error">${this.escapeHtml(result.error)}</span>` : 
                                    '<span class="result-success">Success</span>'
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="progress-actions">
                    <button onclick="admin.hideQuickFetchProgress()" class="btn btn-primary">Close</button>
                </div>
            </div>
        `;
        
        progressDiv.innerHTML = resultsHTML;
    }

    hideQuickFetchProgress() {
        const progressDiv = document.getElementById('quick-fetch-progress');
        if (progressDiv) {
            progressDiv.remove();
        }
    }

    // NEW: Refresh current title method
    refreshCurrentTitle() {
        if (this.currentTitle) {
            this.showTitleDetails(this.currentTitle.directory_hash, this.currentTitle.title);
        }
    }

    // Update the submitBulkEdit method to send array of structs
    async submitBulkEdit(event) {
        event.preventDefault();
        
        const selectedItemsElement = document.getElementById('selected-items');
        const selectedItemsValue = selectedItemsElement ? selectedItemsElement.value : '[]';
        
        let selectedItems;
        try {
            selectedItems = JSON.parse(selectedItemsValue);
        } catch (e) {
            console.error("Error parsing selected items:", e);
            this.showErrorMessage('Error processing selected titles');
            return;
        }
        
        if (selectedItems.length === 0) {
            this.showErrorMessage('No titles selected for bulk update');
            return;
        }
        
        // Collect update fields from form
        const updateFields = {};
        
        // Add text fields only if they have values
        const textFields = [
            { id: 'bulk-category', key: 'category' },
            { id: 'bulk-collection-name', key: 'collection_name' },
            { id: 'bulk-labels', key: 'labels' },
            { id: 'bulk-image-poster', key: 'image_poster_large' }
        ];
        
        textFields.forEach(field => {
            const element = document.getElementById(field.id);
            const value = element ? element.value.trim() : '';
            if (value) {
                updateFields[field.key] = value;
            }
        });
        
        // Add ignore checkbox - always include to allow unsetting
        const ignoreElement = document.getElementById('bulk-ignore');
        if (ignoreElement) {
            updateFields.ignore = ignoreElement.checked ? 'yes' : 'no';
        }
        
        // Check if at least one field is being updated
        const hasUpdates = Object.keys(updateFields).length > 0;
        
        if (!hasUpdates) {
            this.showErrorMessage('Please fill at least one field to update');
            return;
        }
        
        // Build array of structs - each item gets its own struct with update fields
        const bulkUpdateData = selectedItems.map(item => ({
            // Identification fields
            title: item.title,
            directory_hash: item.directory_hash,
            // Update fields (same for all items in bulk update)
            ...updateFields
        }));
        
        // Final request structure
        const formData = {
            action: 'bulk_update',
            updates: bulkUpdateData  // Array of structs
        };
        
        console.log("Bulk update form data:", formData);
        console.log("Updates array structure:", bulkUpdateData);
        
        // Show confirmation dialog
        const fieldCount = Object.keys(updateFields).length;
        const confirmed = confirm(
            `This will update ${fieldCount} field(s) for ${selectedItems.length} selected title(s).\n\n` +
            'This action cannot be undone.\n\n' +
            'Do you want to continue?'
        );
        
        if (!confirmed) {
            return;
        }

        try {
            this.showUpdateProgress('Updating selected titles...', false);
            
            const response = await fetch('/admin/series-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.hideUpdateProgress();
                this.closeEditModal();
                
                // Clear selections and refresh
                this.selectedTitles.clear();
                this.updateBulkEditButton();
                
                await this.loadTitles();
                
                const message = result.message || `Successfully updated ${selectedItems.length} title(s)`;
                this.showSuccessMessage(message);
                
            } else {
                throw new Error(result.error || 'Bulk update failed');
            }
            
        } catch (error) {
            console.error('Bulk update error:', error);
            this.hideUpdateProgress();
            this.showErrorMessage('Bulk update failed: ' + error.message);
        }
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
        messageDiv.style.zIndex = '10000';
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
