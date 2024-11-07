import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

class AuthManager:
    def __init__(self):
        """Initialize authentication manager"""
        self.users_file = 'users.json'
        self.default_admin = {
            'admin': {
                'password': self.hash_password('admin'),
                'role': 'admin',
                'created_at': datetime.utcnow().isoformat()
            }
        }
        self.users = self.load_users()

    def load_users(self) -> Dict:
        """Load users from file or create default admin"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            else:
                self.save_users(self.default_admin)
                return self.default_admin
        except Exception as e:
            print(f"Error loading users: {str(e)}")
            return self.default_admin

    def save_users(self, users: Dict) -> bool:
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving users: {str(e)}")
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user"""
        try:
            if username in self.users:
                stored_password = self.users[username].get('password')
                if stored_password and stored_password == self.hash_password(password):
                    return True
            return False
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False

    def create_user(self, username: str, password: str, role: str = 'user') -> bool:
        """Create new user"""
        try:
            if username in self.users:
                return False
            
            self.users[username] = {
                'password': self.hash_password(password),
                'role': role,
                'created_at': datetime.utcnow().isoformat()
            }
            return self.save_users(self.users)
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            if self.authenticate(username, old_password):
                self.users[username]['password'] = self.hash_password(new_password)
                return self.save_users(self.users)
            return False
        except Exception as e:
            print(f"Error changing password: {str(e)}")
            return False

    def get_user_role(self, username: str) -> Optional[str]:
        """Get user role"""
        try:
            if username in self.users:
                return self.users[username].get('role')
            return None
        except Exception as e:
            print(f"Error getting user role: {str(e)}")
            return None

def render_login():
    """Render login interface"""
    st.title("Login")

    # Initialize auth manager
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()

    # Login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if st.session_state.auth_manager.authenticate(username, password):
                st.session_state.user = username
                st.session_state.role = st.session_state.auth_manager.get_user_role(username)
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    # Show default credentials for demo
    st.info("Default credentials: admin/admin")

def render_user_management():
    """Render user management interface"""
    st.title("User Management")

    # Check admin access
    if not hasattr(st.session_state, 'role') or st.session_state.role != 'admin':
        st.error("Access denied")
        return

    # Create new user
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        
        if st.form_submit_button("Create User"):
            if st.session_state.auth_manager.create_user(new_username, new_password, role):
                st.success("User created successfully!")
            else:
                st.error("Username already exists")

    # List users
    st.subheader("Users")
    users = st.session_state.auth_manager.users
    for username, user_data in users.items():
        with st.expander(f"User: {username}"):
            st.write(f"Role: {user_data['role']}")
            st.write(f"Created: {user_data['created_at']}")

def check_auth():
    """Check if user is authenticated"""
    if not hasattr(st.session_state, 'user'):
        render_login()
        return False
    return True
