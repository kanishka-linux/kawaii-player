class LoginManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkPasswordExists();
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        // Setup password button
        const setupBtn = document.getElementById('setup-password-btn');
        setupBtn.addEventListener('click', () => this.showSetupModal());

        // Setup form
        const setupForm = document.getElementById('setup-form');
        setupForm.addEventListener('submit', (e) => this.handlePasswordSetup(e));

        // Close modal
        const closeBtn = document.getElementById('close-setup-modal');
        closeBtn.addEventListener('click', () => this.hideSetupModal());

        // Close modal on backdrop click
        const modal = document.getElementById('setup-modal');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideSetupModal();
            }
        });

        // Password confirmation validation
        const confirmPassword = document.getElementById('confirm-password');
        confirmPassword.addEventListener('input', () => this.validatePasswordMatch());
    }

    async checkPasswordExists() {
        try {
            const response = await fetch('/api/auth/check-password-exists');
            const data = await response.json();
            
            if (!data.exists) {
                document.getElementById('setup-section').style.display = 'block';
            }
        } catch (error) {
            console.error('Error checking password existence:', error);
            // Show setup section if we can't determine password existence
            document.getElementById('setup-section').style.display = 'block';
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const loginBtn = document.getElementById('login-btn');
        const btnText = loginBtn.querySelector('.btn-text');
        const btnSpinner = loginBtn.querySelector('.btn-spinner');
        const errorMessage = document.getElementById('error-message');
        
        // Get form data
        const formData = new FormData(e.target);
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        // Validate input
        if (!credentials.username || !credentials.password) {
            this.showError('Please enter both username and password');
            return;
        }

        // Show loading state
        this.setButtonLoading(loginBtn, btnText, btnSpinner, true);
        this.hideError();

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store auth token if provided
                                // Store auth token if provided
                if (data.token) {
                    localStorage.setItem('adminToken', data.token);
                }
                
                // Store session info
                sessionStorage.setItem('adminAuthenticated', 'true');
                
                // Redirect to admin panel
                const pathParts = window.location.pathname.split('/');
                const redirectTo = pathParts[pathParts.length - 1]; // Gets last part
                
                // Redirect based on URL
                if (redirectTo === 'admin') {
                    window.location.href = '/admin';
                } else if (redirectTo === 'browse') {
                    window.location.href = '/browse';
                } else {
                    // Fallback to admin if unclear
                    window.location.href = '/admin';
                }
            } else {
                this.showError(data.message || 'Invalid username or password');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Login failed. Please check your connection and try again.');
        } finally {
            this.setButtonLoading(loginBtn, btnText, btnSpinner, false);
        }
    }

    async handlePasswordSetup(e) {
        e.preventDefault();
        
        const setupBtn = document.getElementById('setup-btn');
        const btnText = setupBtn.querySelector('.btn-text');
        const btnSpinner = setupBtn.querySelector('.btn-spinner');
        
        // Get form data
        const formData = new FormData(e.target);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');

        // Validate passwords
        if (password !== confirmPassword) {
            this.showSetupError('Passwords do not match');
            return;
        }

        if (password.length < 6) {
            this.showSetupError('Password must be at least 6 characters long');
            return;
        }

        // Show loading state
        this.setButtonLoading(setupBtn, btnText, btnSpinner, true);
        this.hideSetupError();

        try {
            const response = await fetch('/api/auth/setup-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showSetupSuccess('Password created successfully! You can now login.');
                
                // Hide setup section and close modal after delay
                setTimeout(() => {
                    this.hideSetupModal();
                    document.getElementById('setup-section').style.display = 'none';
                    
                    // Focus on username field
                    document.getElementById('username').focus();
                }, 2000);
            } else {
                this.showSetupError(data.message || 'Failed to create password');
            }
        } catch (error) {
            console.error('Password setup error:', error);
            this.showSetupError('Failed to create password. Please try again.');
        } finally {
            this.setButtonLoading(setupBtn, btnText, btnSpinner, false);
        }
    }

    validatePasswordMatch() {
        const password = document.getElementById('setup-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        const confirmInput = document.getElementById('confirm-password');
        
        if (confirmPassword && password !== confirmPassword) {
            confirmInput.style.borderColor = '#e53e3e';
            this.showSetupError('Passwords do not match');
        } else {
            confirmInput.style.borderColor = '#e1e5e9';
            this.hideSetupError();
        }
    }

    showSetupModal() {
        document.getElementById('setup-modal').style.display = 'flex';
        document.getElementById('setup-password').focus();
    }

    hideSetupModal() {
        document.getElementById('setup-modal').style.display = 'none';
        document.getElementById('setup-form').reset();
        this.hideSetupError();
    }

    setButtonLoading(button, textElement, spinnerElement, isLoading) {
        button.disabled = isLoading;
        textElement.style.display = isLoading ? 'none' : 'inline';
        spinnerElement.style.display = isLoading ? 'inline' : 'none';
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    hideError() {
        document.getElementById('error-message').style.display = 'none';
    }

    showSetupError(message) {
        const errorElement = document.getElementById('setup-error-message');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        errorElement.className = 'error-message';
    }

    showSetupSuccess(message) {
        const errorElement = document.getElementById('setup-error-message');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        errorElement.className = 'success-message';
    }

    hideSetupError() {
        document.getElementById('setup-error-message').style.display = 'none';
    }
}

// Initialize login manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});
