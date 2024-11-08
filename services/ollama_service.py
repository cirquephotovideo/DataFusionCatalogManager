import streamlit as st
from typing import List, Dict, Optional

class OllamaService:
    def __init__(self):
        self.available = False
        try:
            import requests
            self.requests = requests
            self.available = True
        except ImportError:
            self.requests = None

    def list_models(self) -> List[str]:
        """List available Ollama models"""
        if not self.available:
            return []
            
        try:
            response = self.requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json()
                return [model["name"] for model in models["models"]]
            return []
        except Exception:
            return []

    async def analyze_webpage(self, url: str, html_content: str, model_name: str) -> Optional[Dict]:
        """Analyze webpage using Ollama model"""
        if not self.available:
            return None
            
        try:
            prompt = f"""
            Analyze this webpage and suggest important fields to extract.
            URL: {url}
            
            Identify common e-commerce fields like:
            - Product names
            - Prices
            - SKUs
            - Descriptions
            - Images
            - Categories
            
            Format the response as JSON with suggested fields.
            """
            
            response = self.requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "system": "You are a web scraping expert."
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response")
            return None
        except Exception:
            return None

    async def generate_scraping_rules(self, url: str, fields: List[str], model_name: str) -> Optional[Dict]:
        """Generate scraping rules using Ollama model"""
        if not self.available:
            return None
            
        try:
            prompt = f"""
            Generate web scraping rules for URL: {url}
            Fields to extract: {', '.join(fields)}
            
            Provide CSS selectors or XPath for each field.
            Include data cleaning and validation rules.
            Format response as JSON with selectors and rules.
            """
            
            response = self.requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "system": "You are a web scraping expert."
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response")
            return None
        except Exception:
            return None
