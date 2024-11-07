import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

class AnythingLLMService:
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize AnythingLLM service"""
        # Load config if not provided
        if not all([api_url, api_key]):
            config = self.load_config()
            api_url = api_url or config.get('api_url')
            api_key = api_key or config.get('api_key')

        self.api_url = api_url.rstrip('/') if api_url else None
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        } if api_key else {}

    def load_config(self) -> Dict:
        """Load AnythingLLM configuration from file"""
        try:
            with open('anything_llm_config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'api_url': 'http://localhost:3001/api',
                'api_key': '',
                'mode': 'local',  # local or server
                'extension_enabled': False
            }

    def save_config(self, config: Dict) -> bool:
        """Save AnythingLLM configuration"""
        try:
            with open('anything_llm_config.json', 'w') as f:
                json.dump(config, f)
            return True
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
            return False

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection to AnythingLLM"""
        try:
            if not self.api_url or not self.api_key:
                return False, "API URL and key are required"

            response = requests.get(
                f"{self.api_url}/health",
                headers=self.headers
            )

            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"Connection failed: {response.text}"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def chat(self, message: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """Send chat message to AnythingLLM"""
        try:
            if not self.api_url or not self.api_key:
                return False, "API URL and key are required"

            data = {
                'message': message,
                'context': context or {}
            }

            response = requests.post(
                f"{self.api_url}/chat",
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                return True, response.json().get('response', '')
            else:
                return False, f"Chat failed: {response.text}"

        except Exception as e:
            return False, f"Chat error: {str(e)}"

    def get_extension_status(self) -> Tuple[bool, str]:
        """Check browser extension status"""
        try:
            if not self.api_url or not self.api_key:
                return False, "API URL and key are required"

            response = requests.get(
                f"{self.api_url}/extension/status",
                headers=self.headers
            )

            if response.status_code == 200:
                return True, "Extension connected"
            else:
                return False, "Extension not connected"

        except Exception as e:
            return False, f"Extension status error: {str(e)}"

    def generate_extension_key(self) -> Tuple[bool, str]:
        """Generate new browser extension API key"""
        try:
            if not self.api_url or not self.api_key:
                return False, "API URL and key are required"

            response = requests.post(
                f"{self.api_url}/extension/key",
                headers=self.headers
            )

            if response.status_code == 200:
                key = response.json().get('key')
                connection_string = f"{self.api_url}|{key}"
                return True, connection_string
            else:
                return False, f"Key generation failed: {response.text}"

        except Exception as e:
            return False, f"Key generation error: {str(e)}"

    def get_chat_history(self) -> Tuple[bool, List[Dict]]:
        """Get chat history"""
        try:
            if not self.api_url or not self.api_key:
                return False, []

            response = requests.get(
                f"{self.api_url}/chat/history",
                headers=self.headers
            )

            if response.status_code == 200:
                return True, response.json().get('history', [])
            else:
                return False, []

        except Exception as e:
            logging.error(f"Chat history error: {str(e)}")
            return False, []
