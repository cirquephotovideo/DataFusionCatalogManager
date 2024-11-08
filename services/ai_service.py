from typing import Dict, List, Tuple, Optional
from models.database import SessionLocal, AIConfig, AIEnrichmentPrompt

class AIService:
    def __init__(self):
        self.genai_available = False
        self.openai_available = False
        
        # Try importing AI services
        try:
            import google.generativeai as genai
            self.genai = genai
            self.genai_available = True
        except ImportError:
            self.genai = None
        
        try:
            import openai
            self.openai = openai
            self.openai_available = True
        except ImportError:
            self.openai = None

    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return self.genai_available or self.openai_available

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available AI models"""
        models = {}
        
        if self.genai_available:
            models["Google"] = ["gemini-pro"]
            
        if self.openai_available:
            models["OpenAI"] = ["gpt-3.5-turbo", "gpt-4"]
            
        if not models:
            models["None"] = ["No AI services available"]
            
        return models

    async def generate_text(self, prompt: str, model_provider: str = "OpenAI", model_name: str = "gpt-3.5-turbo") -> Tuple[bool, str]:
        """Generate text using available AI service"""
        try:
            if not self.is_available():
                return False, "No AI services are available"

            if model_provider == "Google" and self.genai_available:
                return await self._generate_with_gemini(prompt)
            elif model_provider == "OpenAI" and self.openai_available:
                return await self._generate_with_openai(prompt, model_name)
            else:
                return False, f"Selected provider {model_provider} is not available"
        except Exception as e:
            return False, f"Error generating text: {str(e)}"

    async def _generate_with_gemini(self, prompt: str) -> Tuple[bool, str]:
        """Generate text using Google's Gemini"""
        try:
            model = self.genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return True, response.text
        except Exception as e:
            return False, f"Gemini error: {str(e)}"

    async def _generate_with_openai(self, prompt: str, model_name: str) -> Tuple[bool, str]:
        """Generate text using OpenAI"""
        try:
            response = await self.openai.ChatCompletion.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, f"OpenAI error: {str(e)}"
