import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import streamlit as st

class AuthSystem:
    def __init__(self):
        self.users_file = "users.json"
        self.sessions_file = "sessions.json"
        self.load_users()
        self.load_sessions()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        """Load users from file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
        except:
            self.users = {}
    
    def save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except:
            pass
    
    def load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
            else:
                self.sessions = {}
        except:
            self.sessions = {}
    
    def save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except:
            pass
    
    def register_user(self, username: str, email: str, password: str, full_name: str = "") -> bool:
        """Register a new user"""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password": self._hash_password(password),
            "email": email,
            "full_name": full_name,
            "created_at": datetime.now().isoformat(),
            "profile": {
                "age": "",
                "gender": "",
                "phone": "",
                "address": ""
            },
            "health_history": []
        }
        
        self.save_users()
        return True
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session token"""
        if username not in self.users:
            return None
        
        if self.users[username]["password"] != self._hash_password(password):
            return None
        
        # Create session token
        session_token = hashlib.sha256(f"{username}{datetime.now()}".encode()).hexdigest()
        self.sessions[session_token] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        self.save_sessions()
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[str]:
        """Validate session token and return username"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        expires_at = datetime.fromisoformat(session["expires_at"])
        
        if datetime.now() > expires_at:
            del self.sessions[session_token]
            self.save_sessions()
            return None
        
        return session["username"]
    
    def logout(self, session_token: str):
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self.save_sessions()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user data"""
        return self.users.get(username)
    
    def update_user_profile(self, username: str, profile_data: Dict) -> bool:
        """Update user profile"""
        if username not in self.users:
            return False
        
        self.users[username]["profile"].update(profile_data)
        self.save_users()
        return True
    
    def add_health_record(self, username: str, health_data: Dict) -> bool:
        """Add health record to user history"""
        if username not in self.users:
            return False
        
        health_record = {
            **health_data,
            "timestamp": datetime.now().isoformat(),
            "id": len(self.users[username]["health_history"]) + 1
        }
        
        self.users[username]["health_history"].append(health_record)
        self.save_users()
        return True
    
    def get_health_history(self, username: str) -> List[Dict]:
        """Get user's health history"""
        if username not in self.users:
            return []
        
        return self.users[username]["health_history"]
    
    def export_user_data(self, username: str) -> Optional[Dict]:
        """Export all user data"""
        if username not in self.users:
            return None
        
        user_data = self.users[username].copy()
        # Remove sensitive password hash
        user_data.pop("password", None)
        
        return user_data
    
    def import_user_data(self, username: str, data: Dict) -> bool:
        """Import user data (for backup restoration)"""
        if username not in self.users:
            return False
        
        # Only import non-sensitive data
        if "profile" in data:
            self.users[username]["profile"] = data["profile"]
        
        if "health_history" in data:
            self.users[username]["health_history"] = data["health_history"]
        
        self.save_users()
        return True

# Initialize auth system
auth = AuthSystem()

def login_page():
    """Display login page"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .login-title {
            text-align: center;
            font-size: 2.2rem;
            margin-bottom: 2rem;
            font-weight: 600;
            color: white;
        }
        .stTextInput > div > div > input {
            background-color: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.5);
            color: white;
        }
        .stTextInput > div > div > input::placeholder {
            color: rgba(0,0,0,0.7) !important;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h2 class="login-title">🏥 Login</h2>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            if st.form_submit_button("🚀 Login", type="primary", use_container_width=True):
                if username and password:
                    session_token = auth.authenticate_user(username, password)
                    if session_token:
                        st.session_state.session_token = session_token
                        st.session_state.current_user = username
                        st.session_state.current_page = "landing"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.error("⚠️ Please fill in all fields")
        
        st.markdown("---")
        st.markdown("**New user?**")
        if st.button("📝 Create Account", use_container_width=True):
            st.session_state.current_page = "register"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def register_page():
    """Display registration page"""
    st.markdown("""
    <style>
        .register-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .register-title {
            text-align: center;
            font-size: 2.2rem;
            margin-bottom: 2rem;
            font-weight: 600;
            color: white;
        }
        .stTextInput > div > div > input {
            background-color: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.5);
            color: white;
        }
        .stTextInput > div > div > input::placeholder {
            color: rgba(0,0,0,0.7) !important;
            font-weight: 500;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h2 class="register-title">📝 Register</h2>', unsafe_allow_html=True)
        
        with st.form("register_form"):
            username = st.text_input("👤 Username", placeholder="Choose a username")
            email = st.text_input("📧 Email", placeholder="Enter your email")
            full_name = st.text_input("📛 Full Name", placeholder="Enter your full name")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
            
            if st.form_submit_button("🚀 Create Account", type="primary", use_container_width=True):
                if all([username, email, password, confirm_password]):
                    if password != confirm_password:
                        st.error("❌ Passwords do not match")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        if auth.register_user(username, email, password, full_name):
                            st.success("✅ Account created successfully! Please login.")
                            st.session_state.registration_success = True
                        else:
                            st.error("❌ Username already exists")
                else:
                    st.error("⚠️ Please fill in all fields")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Navigation buttons outside form
        st.markdown("---")
        
        # Show login button if registration was successful
        if st.session_state.get('registration_success'):
            st.success("🎉 Registration successful! You can now login.")
            if st.button("🔑 Go to Login", type="primary", use_container_width=True):
                st.session_state.current_page = "login"
                st.session_state.registration_success = False
                st.rerun()
        else:
            st.markdown("**Already have an account?**")
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()

def check_authentication():
    """Check if user is authenticated"""
    if 'session_token' not in st.session_state:
        return False
    
    username = auth.validate_session(st.session_state.session_token)
    if username:
        st.session_state.current_user = username
        return True
    else:
        # Session expired, clear it
        st.session_state.pop('session_token', None)
        st.session_state.pop('current_user', None)
        return False

def logout_user():
    """Logout current user"""
    if 'session_token' in st.session_state:
        auth.logout(st.session_state.session_token)
        st.session_state.pop('session_token', None)
        st.session_state.pop('current_user', None)
        st.session_state.current_page = "login"
        st.rerun()
