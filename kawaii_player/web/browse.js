/**
 * Browse Series JavaScript Module
 * Handles multiselect, form validation, and user interactions
 * Compatible with plain HTTP servers (no templating engine required)
 */

class AuthManager {
    static async checkAuthentication() {
        try {
            const response = await fetch('/api/auth/verify', {
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const data = await response.json();
                if (data.requiresSetup) {
                    window.location.href = '/login/browse';
                } else {
                    this.redirectToLogin();
                }
                return false;
            }

            return true;
        } catch (error) {
            console.error('Auth check error:', error);
            this.redirectToLogin();
            return false;
        }
    }

    static redirectToLogin() {
        window.location.href = '/login/browse';
    }
}

// MultiSelect Class for genre selection
class MultiSelect {
    constructor(selector, options = {}) {
        this.element = document.querySelector(selector);
        if (!this.element) return;
        
        this.options = {
            placeholder: options.placeholder || 'Select items',
            max: options.max || null,
            onChange: options.onChange || function() {},
            ...options
        };
        
        this.selectedItems = [];
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        this.createDropdown();
        this.bindEvents();
        this.updateDisplay();
        this.loadSelectedValues();
    }
    
    createDropdown() {
        // Hide original select
        this.element.style.display = 'none';
        
        // Create dropdown container
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'multiselect-dropdown';
        
        // Create display text
        this.displayText = document.createElement('div');
        this.displayText.className = 'multiselect-dropdown-text';
        this.displayText.textContent = this.options.placeholder;
        
        // Create arrow
        this.arrow = document.createElement('div');
        this.arrow.className = 'multiselect-dropdown-arrow';
        
        // Create dropdown list
        this.dropdownList = document.createElement('div');
        this.dropdownList.className = 'multiselect-dropdown-list';
        
        // Create items
        this.createItems();
        
        // Assemble dropdown
        this.dropdown.appendChild(this.displayText);
        this.dropdown.appendChild(this.arrow);
        this.dropdown.appendChild(this.dropdownList);
        
        // Insert after original select
        this.element.parentNode.insertBefore(this.dropdown, this.element.nextSibling);
    }
    
    createItems() {
        const options = Array.from(this.element.options).map(opt => ({
            value: opt.value,
            text: opt.textContent,
            selected: opt.selected
        }));
        
        options.forEach(option => {
            if (!option.value) return;
            
            const item = document.createElement('div');
            item.className = 'multiselect-dropdown-list-item';
            item.dataset.value = option.value;
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `genre-${option.value}`;
            checkbox.checked = option.selected || false;
            
            const label = document.createElement('label');
            label.setAttribute('for', `genre-${option.value}`);
            label.textContent = option.text;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            this.dropdownList.appendChild(item);
            
            if (option.selected) {
                this.selectedItems.push(option.value);
                item.classList.add('selected');
            }
        });
    }
    
    loadSelectedValues() {
        const selectedOptions = Array.from(this.element.selectedOptions);
        selectedOptions.forEach(option => {
            if (option.value && !this.selectedItems.includes(option.value)) {
                this.selectedItems.push(option.value);
                const item = this.dropdownList.querySelector(`[data-value="${option.value}"]`);
                if (item) {
                    item.classList.add('selected');
                    item.querySelector('input[type="checkbox"]').checked = true;
                }
            }
        });
        this.updateDisplay();
    }
    
    bindEvents() {
        // Toggle dropdown
        this.dropdown.addEventListener('click', (e) => {
            if (!e.target.closest('.multiselect-dropdown-list')) {
                this.toggle();
            }
        });
        
        // Item selection
        this.dropdownList.addEventListener('click', (e) => {
            const item = e.target.closest('.multiselect-dropdown-list-item');
            if (item) {
                this.toggleItem(item);
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target)) {
                this.close();
            }
        });
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        this.isOpen = true;
        this.dropdown.classList.add('open');
    }
    
    close() {
        this.isOpen = false;
        this.dropdown.classList.remove('open');
    }
    
    toggleItem(item) {
        const value = item.dataset.value;
        const checkbox = item.querySelector('input[type="checkbox"]');
        
        if (this.selectedItems.includes(value)) {
            // Unselect
            this.selectedItems = this.selectedItems.filter(v => v !== value);
            item.classList.remove('selected');
            checkbox.checked = false;
        } else {
            // Select
            if (this.options.max && this.selectedItems.length >= this.options.max) {
                BrowseApp.showMessage(`You can select maximum ${this.options.max} genres`, 'warning');
                return;
            }
            
            this.selectedItems.push(value);
            item.classList.add('selected');
            checkbox.checked = true;
        }
        
        this.updateDisplay();
        this.updateOriginalSelect();
        this.options.onChange(this.selectedItems, this.getSelectedTexts(), this.element);
    }
    
    updateDisplay() {
        if (this.selectedItems.length === 0) {
            this.displayText.textContent = this.options.placeholder;
            this.displayText.classList.remove('has-value');
        } else if (this.selectedItems.length === 1) {
            const selectedText = this.getSelectedTexts()[0];
            this.displayText.textContent = selectedText;
            this.displayText.classList.add('has-value');
        } else {
            this.displayText.textContent = `${this.selectedItems.length} genres selected`;
            this.displayText.classList.add('has-value');
        }
    }
    
    updateOriginalSelect() {
        Array.from(this.element.options).forEach(option => {
            option.selected = this.selectedItems.includes(option.value);
        });
        
        // Trigger change event for form validation
        this.element.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    getSelectedTexts() {
        return this.selectedItems.map(value => {
            const item = this.dropdownList.querySelector(`[data-value="${value}"]`);
            return item ? item.querySelector('label').textContent : value;
        });
    }
    
    // Public methods
    getSelectedValues() {
        return this.selectedItems;
    }
    
    setSelectedValues(values) {
        this.selectedItems = [...values];
        this.updateDisplay();
        this.updateOriginalSelect();
        
        const items = this.dropdownList.querySelectorAll('.multiselect-dropdown-list-item');
        items.forEach(item => {
            const value = item.dataset.value;
            const checkbox = item.querySelector('input[type="checkbox"]');
            if (values.includes(value)) {
                item.classList.add('selected');
                checkbox.checked = true;
            } else {
                item.classList.remove('selected');
                checkbox.checked = false;
            }
        });
    }
    
    destroy() {
        if (this.dropdown && this.dropdown.parentNode) {
            this.dropdown.parentNode.removeChild(this.dropdown);
        }
        this.element.style.display = '';
    }
}

// Form Validation Module
const FormValidator = {
    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
        
        // Focus the field for better UX
        field.focus();
    },
    
    clearFieldError(field) {
        field.classList.remove('error');
        
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    },
    
    clearAllErrors() {
        const errorFields = document.querySelectorAll('.error');
        const errorMessages = document.querySelectorAll('.field-error');
        
        errorFields.forEach(field => {
            field.classList.remove('error');
        });
        
        errorMessages.forEach(error => error.remove());
    },
    
    sanitizeInput(input) {
        // Basic XSS prevention
        return input
            .replace(/[<>]/g, '') // Remove < and >
            .replace(/javascript:/gi, '') // Remove javascript: protocol
            .replace(/on\w+=/gi, '') // Remove event handlers
            .replace(/data:/gi, '') // Remove data: protocol
            .trim();
    },
    
    validateEmail(email) {
        // Email validation using regex
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
        return emailRegex.test(email);
    },
    
    validateYearRange(fromYear, toYear) {
        const currentYear = new Date().getFullYear();
        
        // Validate individual years
        if (fromYear && (fromYear < 1900 || fromYear > currentYear + 5)) {
            return { 
                valid: false, 
                field: 'from',
                message: `Year must be between 1900 and ${currentYear + 5}` 
            };
        }
        
        if (toYear && (toYear < 1900 || toYear > currentYear + 5)) {
            return { 
                valid: false, 
                field: 'to',
                message: `Year must be between 1900 and ${currentYear + 5}` 
            };
        }
        
        // Validate range logic
        if (fromYear && toYear && fromYear > toYear) {
            return { 
                valid: false, 
                field: 'to',
                message: 'End year must be greater than or equal to start year' 
            };
        }
        
        return { valid: true };
    },
    
    validateSearchInput(input) {
        const sanitized = this.sanitizeInput(input);
        
        // Check for minimum length
        if (input.length > 0 && input.length < 2) {
            return {
                valid: false,
                message: 'Search must be at least 2 characters long'
            };
        }
        
        // Check for maximum length
        if (input.length > 100) {
            return {
                valid: false,
                message: 'Search must be less than 100 characters'
            };
        }
        
        // Check if sanitization changed the input
        if (sanitized !== input) {
            return {
                valid: false,
                message: 'Search contains invalid characters'
            };
        }
        
        return { valid: true };
    }
};

// Main Browse Application
const BrowseApp = {
    genresSelect: null,
    searchTimeout: null,
    
    init() {
        this.initMultiSelect();
        this.initFormValidation();
        this.initViewToggle();
        this.initSeriesCards();
        this.initPagination();
        this.initSearchInput();
    },
    
    initMultiSelect() {
        // Initialize multiselect for genres
        this.genresSelect = new MultiSelect('.js-multiselect', {
            placeholder: 'Select genres',
            max: 5,
            onChange: (values, texts, element) => {
                console.log('Genres changed:', values);
                
                // Validate genre selection count
                if (values.length > 5) {
                    this.showMessage('You can select maximum 5 genres', 'warning');
                }
            }
        });
    },
    
    initFormValidation() {
        const form = document.getElementById('browse-form');
        const yearFromSelect = document.querySelector('.js-year-from');
        const yearToSelect = document.querySelector('.js-year-to');
        const searchInput = document.getElementById('search');
        
        // Year range validation
        if (yearFromSelect && yearToSelect) {
            const validateYears = () => {
                const fromYear = parseInt(yearFromSelect.value);
                const toYear = parseInt(yearToSelect.value);
                
                FormValidator.clearFieldError(yearFromSelect);
                FormValidator.clearFieldError(yearToSelect);
                
                const validation = FormValidator.validateYearRange(fromYear, toYear);
                if (!validation.valid) {
                    const targetField = validation.field === 'from' ? yearFromSelect : yearToSelect;
                    FormValidator.showFieldError(targetField, validation.message);
                    return false;
                }
                return true;
            };
            
            // Auto-adjust year ranges for better UX
            yearFromSelect.addEventListener('change', () => {
                if (yearFromSelect.value && yearToSelect.value && 
                    parseInt(yearFromSelect.value) > parseInt(yearToSelect.value)) {
                    yearToSelect.value = yearFromSelect.value;
                }
                validateYears();
            });
            
            yearToSelect.addEventListener('change', () => {
                if (yearToSelect.value && yearFromSelect.value && 
                    parseInt(yearToSelect.value) < parseInt(yearFromSelect.value)) {
                    yearFromSelect.value = yearToSelect.value;
                }
                validateYears();
            });
        }
        
        // Form submission validation
        if (form) {
            form.addEventListener('submit', (e) => {
                FormValidator.clearAllErrors();
                let isValid = true;
                
                // Validate search input
                if (searchInput && searchInput.value.trim()) {
                    const validation = FormValidator.validateSearchInput(searchInput.value.trim());
                    
                    if (!validation.valid) {
                        FormValidator.showFieldError(searchInput, validation.message);
                        isValid = false;
                    }
                }
                
                // Validate year range
                if (yearFromSelect && yearToSelect) {
                    const fromYear = parseInt(yearFromSelect.value);
                    const toYear = parseInt(yearToSelect.value);
                    const validation = FormValidator.validateYearRange(fromYear, toYear);
                    
                    if (!validation.valid) {
                        const targetField = validation.field === 'from' ? yearFromSelect : yearToSelect;
                        FormValidator.showFieldError(targetField, validation.message);
                        isValid = false;
                    }
                }
                
                // Validate genre selection count
                if (this.genresSelect && this.genresSelect.getSelectedValues().length > 5) {
                    this.showMessage('You can select maximum 5 genres', 'warning');
                    isValid = false;
                }
                
                if (!isValid) {
                    e.preventDefault();
                    return false;
                }
                
                // Show loading state
                this.showLoadingState();
            });
        }
        
        // Clear filters functionality
        const clearBtn = document.querySelector('.js-clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                                this.clearAllFilters();
            });
        }
    },
    
    initViewToggle() {
        const viewToggles = document.querySelectorAll('.js-view-toggle');
        const seriesGrid = document.querySelector('.js-series-grid');
        
        viewToggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const view = toggle.dataset.view;
                
                // Update active state
                viewToggles.forEach(t => {
                    t.classList.remove('active');
                });
                toggle.classList.add('active');
                
                // Update grid view with smooth transition
                if (seriesGrid) {
                    seriesGrid.style.opacity = '0.7';
                    setTimeout(() => {
                        seriesGrid.className = view === 'list' ? 'list-view js-series-grid' : 'grid js-series-grid';
                        seriesGrid.style.opacity = '1';
                    }, 150);
                }
                
                // Save preference
                try {
                    localStorage.setItem('preferredView', view);
                } catch (e) {
                    console.warn('Could not save view preference:', e);
                }
            });
        });
        
        // Load saved view preference
        try {
            const savedView = localStorage.getItem('preferredView');
            if (savedView) {
                const savedToggle = document.querySelector(`[data-view="${savedView}"]`);
                if (savedToggle) {
                    savedToggle.click();
                }
            }
        } catch (e) {
            console.warn('Could not load view preference:', e);
        }
    },
    
    initSeriesCards() {
        const seriesCards = document.querySelectorAll('.series-card');
        
        seriesCards.forEach(card => {
            // Click handling
            card.addEventListener('click', (e) => {
                // Prevent navigation if clicking on interactive elements
                if (e.target.closest('button, a, input, select, .interactive')) {
                    return;
                }
                
                const seriesId = card.dataset.seriesId;
                if (seriesId) {
                    // Add loading state to clicked card
                    card.style.opacity = '0.7';
                    card.style.pointerEvents = 'none';
                    
                    window.location.href = `/series-details/${seriesId}`;
                }
            });
            
            // Add hover effects for better UX
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px)';
                card.style.transition = 'transform 0.2s ease';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
 
        // Clear filters functionality when empty series data 
        const clearBtn1 = document.querySelector('.js-clear-filters-not-found');
        if (clearBtn1) {
            clearBtn1.addEventListener('click', (e) => {
                e.preventDefault();
                                this.clearAllFilters();
            });
        }
    },
    
    initPagination() {
        const paginationLinks = document.querySelectorAll('.pagination a');
        
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Prevent double-clicking
                if (link.classList.contains('loading')) {
                    e.preventDefault();
                    return;
                }
                
                // Add loading state
                link.classList.add('loading');
                link.style.opacity = '0.6';
                link.style.pointerEvents = 'none';
                
                const originalText = link.textContent;
                link.textContent = 'Loading...';
                
                // Restore state if navigation fails
                setTimeout(() => {
                    link.classList.remove('loading');
                    link.style.opacity = '1';
                    link.style.pointerEvents = 'auto';
                    link.textContent = originalText;
                }, 5000);
            });
        });
    },
    
    initSearchInput() {
        const searchInput = document.getElementById('search');
        if (!searchInput) return;
        
        // Real-time validation with debouncing
        searchInput.addEventListener('input', () => {
            clearTimeout(this.searchTimeout);
            FormValidator.clearFieldError(searchInput);
            
            const value = searchInput.value.trim();
            
            // Real-time validation feedback
            if (value.length > 0) {
                const validation = FormValidator.validateSearchInput(value);
                if (!validation.valid) {
                    FormValidator.showFieldError(searchInput, validation.message);
                }
            }
        });
        
        // Prevent submission on Enter if validation fails
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const value = searchInput.value.trim();
                const validation = FormValidator.validateSearchInput(value);
                
                if (!validation.valid) {
                    e.preventDefault();
                    FormValidator.showFieldError(searchInput, validation.message);
                }
            }
        });
        
        // Clear search functionality
        const clearSearchBtn = document.createElement('button');
        clearSearchBtn.type = 'button';
        clearSearchBtn.className = 'search-clear-btn';
        clearSearchBtn.innerHTML = '✖';
        clearSearchBtn.style.display = searchInput.value ? 'block' : 'none';
        
        searchInput.parentNode.appendChild(clearSearchBtn);
        
        clearSearchBtn.addEventListener('click', () => {
            searchInput.value = '';
            searchInput.focus();
            FormValidator.clearFieldError(searchInput);
            clearSearchBtn.style.display = 'none';
        });
        
        searchInput.addEventListener('input', () => {
            clearSearchBtn.style.display = searchInput.value ? 'block' : 'none';
        });
    },

    clearAllFilters() {
        const form = document.getElementById('browse-form');
        if (!form) return;
        
        // Clear all validation errors first
        FormValidator.clearAllErrors();
        
        // Clear multiselect BEFORE form reset to prevent conflicts
        if (this.genresSelect) {
            this.genresSelect.setSelectedValues([]);
        }
        
        // Reset form fields
        form.reset();
        
        // Clear search input and its clear button
        const searchInput = document.getElementById('search');
        if (searchInput) {
            searchInput.value = '';
            const clearBtn = searchInput.parentNode.querySelector('.search-clear-btn');
            if (clearBtn) {
                clearBtn.style.display = 'none';
            }
            FormValidator.clearFieldError(searchInput);
        }
        
        // Clear all select elements explicitly
        const selects = form.querySelectorAll('select');
        selects.forEach(select => {
            if (!select.multiple) {
                select.selectedIndex = 0; // Reset to first option
            } else {
                // Clear multiple select options
                Array.from(select.options).forEach(option => {
                    option.selected = false;
                });
            }
            FormValidator.clearFieldError(select);
        });
        
        // Clear all input fields explicitly
        const inputs = form.querySelectorAll('input[type="text"], input[type="search"]');
        inputs.forEach(input => {
            input.value = '';
            FormValidator.clearFieldError(input);
        });
        
        // Update multiselect display after clearing
        if (this.genresSelect) {
            this.genresSelect.updateDisplay();
            this.genresSelect.updateOriginalSelect();
        }
        
        // Show loading state and submit
        this.showLoadingState();
        
        // Small delay to ensure all clearing is complete
        setTimeout(() => {
            form.submit();
        }, 100);
    },
    
    showLoadingState() {
        const submitBtn = document.querySelector('.js-apply-filters');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Loading...';
            
            // Store original text for potential restoration
            submitBtn.dataset.originalText = originalText;
        }
        
        // Show page loading indicator
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
            loadingScreen.style.opacity = '1';
        }
    },
    
    showMessage(message, type = 'info', duration = 5000) {
        // Create alert container if it doesn't exist
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'alert-container';
            
            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(alertContainer, container.firstChild);
            } else {
                document.body.appendChild(alertContainer);
            }
        }
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            <span class="alert-icon">${this.getAlertIcon(type)}</span>
            <span class="alert-message">${message}</span>
            <button class="alert-close">×</button>
        `;
        
        // Add close functionality
        const closeBtn = alert.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            this.removeAlert(alert);
        });
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after specified duration
        setTimeout(() => {
            this.removeAlert(alert);
        }, duration);
    },
    
    removeAlert(alert) {
        if (alert && alert.parentNode) {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 300);
        }
    },
    
    getAlertIcon(type) {
        const icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        };
        return icons[type] || icons.info;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AuthManager.checkAuthentication().then(isAuthenticated => {
        if (isAuthenticated) {
            BrowseApp.init();
        }
    }).catch(error => {
        console.error('Authentication check failed:', error);
        AuthManager.redirectToLogin();
    });
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, pause any ongoing operations
        clearTimeout(BrowseApp.searchTimeout);
    } else {
        // Page is visible again, resume operations
        console.log('Page is visible again');
    }
});

// Handle online/offline status
window.addEventListener('online', () => {
    BrowseApp.showMessage('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    BrowseApp.showMessage('You are currently offline', 'warning');
});

// Export for external use and testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BrowseApp, MultiSelect, FormValidator };
} else {
    window.BrowseApp = BrowseApp;
    window.MultiSelect = MultiSelect;
    window.FormValidator = FormValidator;
}
