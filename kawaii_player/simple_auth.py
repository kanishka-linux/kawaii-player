import json
import os
import hashlib
import secrets
import datetime
from http.cookies import SimpleCookie
import uuid
from functools import wraps

class SimpleAuthManager:
    def __init__(self, ui):
        self.ui = ui
        self.password_file = ui.password_file
        self.session_file = ui.session_file
        self.session_expiry_in_hours = ui.session_expiry
        self.password_data = None
        self.active_sessions = {}
        self.load_password_data()
        self.load_sessions()
    
    def load_password_data(self):
        """Load password data from file"""
        try:
            if os.path.exists(self.password_file):
                with open(self.password_file, 'r') as f:
                    self.password_data = json.load(f)
        except Exception as e:
            print(f"Error loading password data: {e}")
            self.password_data = None
    
    def load_sessions(self):
        """Load active sessions from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    self.active_sessions = json.load(f)
                self.cleanup_expired_sessions()
        except Exception as e:
            print(f"Error loading sessions: {e}")
            self.active_sessions = {}
    
    def save_password_data(self, data):
        """Save password data to file"""
        try:
            with open(self.password_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.password_data = data
            return True
        except Exception as e:
            print(f"Error saving password data: {e}")
            return False
    
    def save_sessions(self):
        """Save active sessions to file"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.active_sessions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving sessions: {e}")
            return False
    
    def hash_password(self, password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{password}{salt}".encode('utf-8')
        hashed = hashlib.sha256(combined).hexdigest()
        
        # Additional rounds for security
        for _ in range(1000):
            hashed = hashlib.sha256(hashed.encode('utf-8')).hexdigest()
        
        return hashed, salt
    
    def password_exists(self):
        """Check if admin password is configured"""
        return self.password_data and 'hashed_password' in self.password_data
    
    def create_password(self, password):
        """Create and store hashed password"""
        try:
            hashed_password, salt = self.hash_password(password)
            
            password_data = {
                'username': 'admin',
                'hashed_password': hashed_password,
                'salt': salt,
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            return self.save_password_data(password_data)
        except Exception as e:
            print(f"Error creating password: {e}")
            return False
    
    def validate_credentials(self, username, password):
        """Validate username and password"""
        try:
            if not self.password_exists():
                return False
            
            if username != 'admin':
                return False
            
            stored_salt = self.password_data['salt']
            hashed_password, _ = self.hash_password(password, stored_salt)
            
            return hashed_password == self.password_data['hashed_password']
        except Exception as e:
            print(f"Error validating credentials: {e}")
            return False
    
    def create_session(self):
        """Create a new session"""
        session_id = str(uuid.uuid4())
        session_data = {
            'username': 'admin',
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': (datetime.datetime.now() + datetime.timedelta(hours=self.session_expiry_in_hours)).isoformat(),
            'last_accessed': datetime.datetime.now().isoformat()
        }
        self.active_sessions[session_id] = session_data
        self.save_sessions()
        return session_id
    
    def validate_session(self, session_id):
        """Validate session and update last accessed time"""
        if not session_id or session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        expires_at = datetime.datetime.fromisoformat(session_data['expires_at'])
        
        if datetime.datetime.now() > expires_at:
            del self.active_sessions[session_id]
            self.save_sessions()
            return False
        
        session_data['last_accessed'] = datetime.datetime.now().isoformat()
        self.save_sessions()
        return True
    
    def remove_session(self, session_id):
        """Remove session (logout)"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.save_sessions()
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            expires_at = datetime.datetime.fromisoformat(session_data['expires_at'])
            if current_time > expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            self.save_sessions()

# Helper functions for handlers
def get_session_id(handler):
    """Extract session ID from cookies or headers"""
    cookies = SimpleCookie()
    cookie_header = handler.headers.get('Cookie')
    if cookie_header:
        cookies.load(cookie_header)
        if 'adminSession' in cookies:
            return cookies['adminSession'].value
    
    session_id = handler.headers.get('X-Admin-Session', '')
    if session_id:
        return session_id
    
    return None

def send_json_response(handler, data, status_code=200, set_cookie=None):
    """Send JSON response with optional cookie"""
    response_data = json.dumps(data).encode('utf-8')
    
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(response_data)))
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Session')
    
    if set_cookie:
        handler.send_header('Set-Cookie', set_cookie)
    
    handler.end_headers()
    handler.wfile.write(response_data)

def clear_session_cookie():
    """Clear session cookie"""
    cookies = SimpleCookie()
    cookies['adminSession'] = ''
    cookies['adminSession']['path'] = '/'
    cookies['adminSession']['max-age'] = 0
    cookies['adminSession']['httponly'] = True
    return cookies['adminSession'].OutputString()

def set_session_cookie(session_id, max_age=86400):
    """Set session cookie"""
    cookies = SimpleCookie()
    cookies['adminSession'] = session_id
    cookies['adminSession']['path'] = '/'
    cookies['adminSession']['max-age'] = max_age
    cookies['adminSession']['httponly'] = True
    
    if os.environ.get('HTTPS') == 'true':
        cookies['adminSession']['secure'] = True
    
    return cookies['adminSession'].OutputString()

def get_request_body(handler):
    """Get and parse request body"""
    try:
        content_length = int(handler.headers.get('Content-Length', 0))
        if content_length > 0:
            body = handler.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        return {}
    except Exception as e:
        print(f"Error parsing request body: {e}")
        return {}

def require_admin_auth(handler_instance, ui):
    # Clean up expired sessions
    if ui.pc_to_pc_casting == "slave":
        return False

    ui.auth_manager.cleanup_expired_sessions()
    
    # Check if password is configured
    if not ui.auth_manager.password_exists():
        send_json_response(handler_instance, {
            'success': False,
            'message': 'Admin password not configured',
            'requiresSetup': True
        }, 401)
        return True
    
    # Get and verify session
    session_id = get_session_id(handler_instance)
    if not session_id:
        send_json_response(handler_instance, {
            'success': False,
            'message': 'Authentication required',
            'redirectTo': '/login'
        }, 401)
        return True
    
    if not ui.auth_manager.validate_session(session_id):
        send_json_response(handler_instance, {
            'success': False,
            'message': 'Invalid or expired session',
            'redirectTo': '/login'
        }, 401, clear_session_cookie())
        return True
    
    # Authentication successful
    return False

# Auth route handlers
def handle_auth_routes(handler, method, path, ui):
    """Handle authentication-related routes"""
    if path == '/api/auth/check-password-exists' and method == 'GET':
        handle_check_password_exists(handler, ui)
        return True
    elif path == '/api/auth/verify' and method == 'GET':
        handle_verify_session(handler, ui)
        return True
    elif path == '/api/auth/setup-password' and method == 'POST':
        handle_setup_password(handler, ui)
        return True
    elif path == '/api/auth/login' and method == 'POST':
        handle_login(handler, ui)
        return True
    elif path == '/api/auth/logout' and method == 'POST':
        handle_logout(handler, ui)
        return True
    elif path in ['/login', '/login/browse', '/login/admin'] and method == 'GET':
        serve_login_page(handler, ui, path)
        return True
    
    return False

def handle_check_password_exists(handler, ui):
    """Handle password existence check"""
    exists = ui.auth_manager.password_exists()
    send_json_response(handler, {'exists': exists})

def handle_verify_session(handler, ui):
    """Handle session verification"""
    session_id = get_session_id(handler)
    if session_id and ui.auth_manager.validate_session(session_id):
        send_json_response(handler, {
            'success': True,
            'user': {'username': 'admin', 'role': 'admin'}
        })
    else:
        send_json_response(handler, {
            'success': False,
            'message': 'Invalid session'
        }, 401, clear_session_cookie())

def handle_setup_password(handler, ui):
    """Handle password setup"""
    try:
        data = get_request_body(handler)
        password = data.get('password', '')
        
        if not password or len(password) < 6:
            send_json_response(handler, {
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }, 400)
            return
        
        if ui.auth_manager.password_exists():
            send_json_response(handler, {
                'success': False,
                'message': 'Admin password already configured'
            }, 400)
            return
        
        if ui.auth_manager.create_password(password):
            send_json_response(handler, {
                'success': True,
                'message': 'Admin password created successfully'
            })
        else:
            send_json_response(handler, {
                'success': False,
                'message': 'Error creating password'
            }, 500)
    
    except Exception as e:
        print(f"Setup password error: {e}")
        send_json_response(handler, {
            'success': False,
            'message': 'Error creating password'
        }, 500)

def handle_login(handler, ui):
    """Handle login request"""
    try:
        data = get_request_body(handler)
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            send_json_response(handler, {
                'success': False,
                'message': 'Username and password are required'
            }, 400)
            return
        
        if not ui.auth_manager.password_exists():
            send_json_response(handler, {
                'success': False,
                'message': 'Admin password not configured',
                'requiresSetup': True
            }, 400)
            return
        
        if not ui.auth_manager.validate_credentials(username, password):
            send_json_response(handler, {
                'success': False,
                'message': 'Invalid username or password'
            }, 401)
            return
        
        session_id = ui.auth_manager.create_session()
        cookie = set_session_cookie(session_id)
        
        send_json_response(handler, {
            'success': True,
            'message': 'Login successful',
            'sessionId': session_id
        }, 200, cookie)
    
    except Exception as e:
        print(f"Login error: {e}")
        send_json_response(handler, {
            'success': False,
            'message': 'Login error'
        }, 500)

def handle_logout(handler, ui):
    """Handle logout request"""
    session_id = get_session_id(handler)
    if session_id:
        ui.auth_manager.remove_session(session_id)
    
    cookie = clear_session_cookie()
    send_json_response(handler, {
        'success': True,
        'message': 'Logged out successfully'
    }, 200, cookie)

def serve_login_page(handler, ui, path):
    """Serve login page"""
    try:

        html_path = os.path.join(ui.basedir, 'web', 'login.html')
        with open(html_path, 'rb') as f:
            content = f.read()
        
        handler.send_response(200)
        handler.send_header('Content-Type', 'text/html')
        handler.send_header('Content-Length', str(len(content)))
        handler.end_headers()
        handler.wfile.write(content)
    except FileNotFoundError:
        handler.send_error(404, "Login page not found")
    except Exception as e:
        handler.send_error(500, f"Error serving login page: {e}")
