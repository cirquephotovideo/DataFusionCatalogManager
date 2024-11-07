import requests
import logging
from typing import Dict, List, Optional, Tuple
import json
import os

class HeyGenService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize HeyGen service"""
        # Load config if not provided
        if not api_key:
            config = self.load_config()
            api_key = config.get('api_key')

        self.api_key = api_key
        self.base_url = "https://api.heygen.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        } if api_key else {}

    def load_config(self) -> Dict:
        """Load HeyGen configuration from file"""
        try:
            with open('heygen_config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'api_key': '',
                'default_avatar': 'anna',
                'default_voice': 'en-US-1',
                'default_language': 'en',
                'video_settings': {
                    'resolution': '1080p',
                    'format': 'mp4',
                    'background': 'gradient',
                    'animation_style': 'apple_style',
                    'transitions': ['fade', 'slide', 'zoom'],
                    'effects': ['blur', 'float', '3d_rotate']
                },
                'scene_templates': {
                    'product_showcase': {
                        'background': 'gradient',
                        'camera_movement': 'smooth_pan',
                        'lighting': 'studio',
                        'product_animation': '3d_rotate'
                    },
                    'feature_highlight': {
                        'background': 'blur',
                        'zoom_effect': true,
                        'text_animation': 'float',
                        'highlight_color': '#007AFF'
                    },
                    'technical_specs': {
                        'background': 'minimal',
                        'layout': 'grid',
                        'animation': 'slide_in',
                        'icon_style': 'outlined'
                    }
                }
            }

    def create_product_video(self, product_data: Dict, template: str = 'product_showcase',
                           custom_settings: Optional[Dict] = None) -> Tuple[bool, str]:
        """Create product video using HeyGen API with advanced animations"""
        try:
            if not self.api_key:
                return False, "API key is required"

            # Load config
            config = self.load_config()
            template_settings = config['scene_templates'].get(template, {})
            
            # Merge custom settings
            if custom_settings:
                template_settings.update(custom_settings)

            # Prepare scenes
            scenes = []

            # Intro Scene
            scenes.append({
                "type": "intro",
                "duration": 5,
                "background": {
                    "type": template_settings.get('background', 'gradient'),
                    "colors": ["#000000", "#1E1E1E"],
                    "animation": "wave"
                },
                "elements": [
                    {
                        "type": "text",
                        "content": product_data.get('name', ''),
                        "animation": "float",
                        "style": "modern"
                    },
                    {
                        "type": "image",
                        "url": product_data.get('main_image', ''),
                        "animation": template_settings.get('product_animation', '3d_rotate')
                    }
                ]
            })

            # Feature Highlights
            if product_data.get('features'):
                scenes.append({
                    "type": "features",
                    "duration": len(product_data['features']) * 3,
                    "background": {
                        "type": "blur",
                        "source": product_data.get('main_image', '')
                    },
                    "elements": [
                        {
                            "type": "feature_list",
                            "items": product_data['features'],
                            "animation": "slide_in",
                            "highlight_color": template_settings.get('highlight_color', '#007AFF')
                        }
                    ]
                })

            # Technical Specifications
            if product_data.get('specifications'):
                scenes.append({
                    "type": "specs",
                    "duration": 8,
                    "background": {
                        "type": "minimal",
                        "color": "#FFFFFF"
                    },
                    "elements": [
                        {
                            "type": "spec_grid",
                            "items": product_data['specifications'],
                            "animation": "fade_in",
                            "icon_style": template_settings.get('icon_style', 'outlined')
                        }
                    ]
                })

            # Closing Scene
            scenes.append({
                "type": "outro",
                "duration": 4,
                "background": {
                    "type": "gradient",
                    "colors": ["#1E1E1E", "#000000"],
                    "animation": "wave"
                },
                "elements": [
                    {
                        "type": "cta",
                        "content": "Learn More",
                        "animation": "pulse",
                        "style": "modern"
                    }
                ]
            })

            # Create video request
            data = {
                "scenes": scenes,
                "settings": {
                    "resolution": config['video_settings']['resolution'],
                    "format": config['video_settings']['format'],
                    "quality": "premium",
                    "transitions": config['video_settings']['transitions'],
                    "effects": config['video_settings']['effects']
                }
            }

            # Send request to HeyGen
            response = requests.post(
                f"{self.base_url}/videos",
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                video_data = response.json()
                return True, video_data.get('video_url', '')
            else:
                return False, f"Video creation failed: {response.text}"

        except Exception as e:
            logging.error(f"Error creating video: {str(e)}")
            return False, f"Error creating video: {str(e)}"

    # ... (rest of the methods remain the same)
