import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

class WhatsAppService:
    def __init__(self, phone_number_id: str, access_token: str, verify_token: str):
        """Initialize WhatsApp service"""
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.api_version = 'v17.0'
        self.api_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook"""
        if mode and token:
            if mode == 'subscribe' and token == self.verify_token:
                return challenge
        return None

    def process_webhook(self, data: Dict) -> Dict:
        """Process incoming WhatsApp webhook"""
        try:
            if data.get('object') == 'whatsapp_business_account':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        if change.get('value', {}).get('messages'):
                            for message in change['value']['messages']:
                                # Extract message details
                                message_details = {
                                    'from': message.get('from'),
                                    'timestamp': message.get('timestamp'),
                                    'type': message.get('type')
                                }

                                # Handle different message types
                                if message.get('type') == 'text':
                                    message_details['text'] = message.get('text', {}).get('body', '')
                                elif message.get('type') == 'audio':
                                    message_details['audio'] = message.get('audio', {})
                                
                                return message_details
        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}")
        return {}

    def send_message(self, to: str, message: str) -> bool:
        """Send WhatsApp message"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'text',
                'text': {'body': message}
            }
            
            response = requests.post(
                f"{self.api_url}/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return True
            else:
                logging.error(f"Error sending message: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {str(e)}")
            return False

    def send_template_message(self, to: str, template_name: str, language: str, components: List[Dict]) -> bool:
        """Send template message"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': to,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {
                        'code': language
                    },
                    'components': components
                }
            }
            
            response = requests.post(
                f"{self.api_url}/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return True
            else:
                logging.error(f"Error sending template message: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending WhatsApp template message: {str(e)}")
            return False

    def mark_message_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'status': 'read',
                'message_id': message_id
            }
            
            response = requests.post(
                f"{self.api_url}/messages",
                headers=headers,
                json=data
            )
            
            return response.status_code == 200
                
        except Exception as e:
            logging.error(f"Error marking message as read: {str(e)}")
            return False

    def get_media_url(self, media_id: str) -> Optional[str]:
        """Get media URL from media ID"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f"https://graph.facebook.com/{self.api_version}/{media_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get('url')
            return None
                
        except Exception as e:
            logging.error(f"Error getting media URL: {str(e)}")
            return None

    def download_media(self, url: str) -> Optional[bytes]:
        """Download media from URL"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.content
            return None
                
        except Exception as e:
            logging.error(f"Error downloading media: {str(e)}")
            return None
