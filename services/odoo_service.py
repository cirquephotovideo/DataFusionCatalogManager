import xmlrpc.client
import logging
import ssl
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class OdooService:
    def __init__(self, url: Optional[str] = None, db: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None, 
                 verify_ssl: bool = False):
        """Initialize Odoo connection"""
        # Load config if not provided
        if not all([url, db, username, password]):
            config = self.load_config()
            url = url or config.get('url')
            db = db or config.get('db')
            username = username or config.get('username')
            password = password or config.get('password')

        self.url = url.rstrip('/') if url else None
        self.db = db
        self.username = username
        self.password = password
        
        if self.url:
            # Create SSL context
            if not verify_ssl:
                self.ssl_context = ssl._create_unverified_context()
            else:
                self.ssl_context = ssl.create_default_context()
            
            # XML-RPC endpoints with SSL context
            self.common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common',
                context=self.ssl_context
            )
            self.models = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/object',
                context=self.ssl_context
            )

    def load_config(self) -> Dict:
        """Load Odoo configuration from file"""
        try:
            with open('odoo_config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'url': '',
                'db': '',
                'username': '',
                'password': ''
            }

    def test_connection(self) -> Tuple[bool, str]:
        """Test Odoo connection"""
        try:
            version = self.common.version()
            if not version:
                return False, "Could not get Odoo version information"

            uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not uid:
                return False, "Authentication failed"

            return True, f"Connected successfully to Odoo {version.get('server_version', 'Unknown')}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
