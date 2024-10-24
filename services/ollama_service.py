import requests
import json
from typing import Dict, List, Optional
import subprocess

class OllamaService:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self._ensure_ollama_running()

    def _ensure_ollama_running(self):
        """Check if Ollama is running, if not start it"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code != 200:
                # Try to start Ollama
                subprocess.Popen(["ollama", "serve"])
        except:
            # Try to start Ollama
            subprocess.Popen(["ollama", "serve"])

    def list_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama"""
        try:
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": model_name}
            )
            return response.status_code == 200
        except:
            return False

    async def generate_scraping_rules(self, url: str, fields: List[str], model: str = "mistral") -> Dict:
        """Generate scraping rules using Ollama model"""
        prompt = f"""
        Generate web scraping rules for the following URL: {url}
        Fields to extract: {', '.join(fields)}
        
        Provide the rules in JSON format with:
        1. CSS selectors or XPath for each field
        2. Data cleaning rules
        3. Validation rules
        
        Format the response as:
        {{
            "selectors": {{
                "field_name": {{
                    "type": "css|xpath",
                    "path": "selector_path",
                    "attribute": "text|href|src|etc",
                    "cleaning": ["rule1", "rule2"],
                    "validation": ["rule1", "rule2"]
                }}
            }}
        }}
        """
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract JSON from the response
                response_text = result.get("response", "")
                try:
                    # Find JSON in the response
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                except:
                    pass
            
            return {}
        except:
            return {}

    async def analyze_webpage(self, url: str, html_content: str, model: str = "mistral") -> Dict:
        """Analyze webpage content to suggest fields for extraction"""
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
        
        Format the response as JSON:
        {{
            "suggested_fields": [
                {{
                    "name": "field_name",
                    "type": "text|number|image|etc",
                    "importance": "high|medium|low",
                    "description": "why this field is important"
                }}
            ]
        }}
        """
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract JSON from the response
                response_text = result.get("response", "")
                try:
                    # Find JSON in the response
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = response_text[start:end]
                        return json.loads(json_str)
                except:
                    pass
            
            return {}
        except:
            return {}
