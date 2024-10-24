import json
import os
import hashlib
import secrets
from typing import Dict, Optional, List
from datetime import datetime, timedelta

class UserService:
    def __init__(self):
        self.users_file = "users.json"
        self.sessions_file = "sessions.json"
        self._load_data()

    def _load_data(self):
        """Load users and sessions from files"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {
                "admin": {
                    "password_hash": self._hash_password("admin"),
                    "role": "admin",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                }
            }
            self._save_users()

        if os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'r') as f:
                self.sessions = json.load(f)
        else:
            self.sessions = {}
            self._save_sessions()

    def _save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def _save_sessions(self):
        """Save sessions to file"""
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Create a new user"""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        self._save_users()
        return True

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        if username not in self.users:
            return False
        
        return self.users[username]["password_hash"] == self._hash_password(password)

    def login(self, username: str, password: str) -> Optional[str]:
        """Login user and return session token"""
        if not self.verify_password(username, password):
            return None
        
        # Update last login
        self.users[username]["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        # Create session
        token = self._generate_session_token()
        self.sessions[token] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        self._save_sessions()
        
        return token

    def logout(self, token: str):
        """Logout user by removing session"""
        if token in self.sessions:
            del self.sessions[token]
            self._save_sessions()

    def verify_session(self, token: str) -> Optional[Dict]:
        """Verify session token and return user info"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        if datetime.fromisoformat(session["expires_at"]) < datetime.now():
            del self.sessions[token]
            self._save_sessions()
            return None
        
        username = session["username"]
        return {
            "username": username,
            "role": self.users[username]["role"]
        }

    def get_users(self) -> List[Dict]:
        """Get list of all users"""
        return [{
            "username": username,
            "role": data["role"],
            "created_at": data["created_at"],
            "last_login": data["last_login"]
        } for username, data in self.users.items()]

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if username not in self.users or username == "admin":
            return False
        
        del self.users[username]
        self._save_users()
        
        # Remove any active sessions for this user
        for token, session in list(self.sessions.items()):
            if session["username"] == username:
                del self.sessions[token]
        self._save_sessions()
        
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if not self.verify_password(username, old_password):
            return False
        
        self.users[username]["password_hash"] = self._hash_password(new_password)
        self._save_users()
        return True

    def change_role(self, username: str, new_role: str) -> bool:
        """Change user role"""
        if username not in self.users or username == "admin":
            return False
        
        self.users[username]["role"] = new_role
        self._save_users()
        return True
