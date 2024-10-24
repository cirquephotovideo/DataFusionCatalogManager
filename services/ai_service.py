import google.generativeai as genai
import openai
from typing import Dict, List, Optional, Tuple
from models.database import SessionLocal, AIConfig, Catalog, ProductEnrichment
from datetime import datetime
import json
import asyncio

class AIService:
    def __init__(self):
        """Initialize AI service without creating clients"""
        self.openai_client = None
        self.gemini_model = None
        self.active_config = None
        self._load_active_config()

    def _load_active_config(self):
        """Load active AI configuration"""
        db = SessionLocal()
        try:
            config = db.query(AIConfig).filter(AIConfig.is_active == True).first()
            if config:
                self.active_config = config
                if config.provider == 'openai' and config.api_key:
                    try:
                        self.openai_client = openai.OpenAI(api_key=config.api_key)
                    except Exception as e:
                        print(f"Error initializing OpenAI client: {str(e)}")
                elif config.provider == 'gemini' and config.api_key:
                    try:
                        genai.configure(api_key=config.api_key)
                        self.gemini_model = genai.GenerativeModel(config.model)
                    except Exception as e:
                        print(f"Error initializing Gemini client: {str(e)}")
        except Exception as e:
            print(f"Error loading AI config: {str(e)}")
        finally:
            db.close()

    async def generate_content(self, prompt: str, model: str = None) -> str:
        """Generate content using configured AI model"""
        if not self.active_config:
            raise Exception("No AI configuration found. Please configure an AI provider first.")

        try:
            # Use specified model or fall back to configured model
            use_model = model or self.active_config.model
            
            # Get language setting
            language = getattr(self.active_config, 'language', 'fr_FR')
            
            # Add language instruction to prompt
            language_map = {
                'fr_FR': 'French',
                'en_US': 'English',
                'es_ES': 'Spanish',
                'de_DE': 'German',
                'it_IT': 'Italian'
            }
            
            language_instruction = f"""
            Please respond in {language_map.get(language, 'French')}.
            Format the response in pure HTML using only <p>, <strong>, <ul>, and <li> tags.
            Do not include any markdown or code blocks.
            """
            
            full_prompt = f"{language_instruction}\n\n{prompt}"

            if self.active_config.provider == 'openai':
                if not self.openai_client:
                    raise Exception("OpenAI client not configured")
                
                # Create completion in a non-blocking way
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model=use_model,
                        messages=[
                            {"role": "system", "content": "You are a product enrichment specialist."},
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=self.active_config.temperature
                    )
                )
                return response.choices[0].message.content

            elif self.active_config.provider == 'gemini':
                if not self.gemini_model:
                    raise Exception("Gemini model not configured")
                
                # Create completion in a non-blocking way
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.gemini_model.generate_content(
                        full_prompt,
                        generation_config={"temperature": self.active_config.temperature}
                    )
                )
                return response.text

            else:
                raise Exception(f"Unsupported AI provider: {self.active_config.provider}")

        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")

    def configure_ai(self, provider: str, api_key: str, model: str, temperature: float = 0.7, language: str = 'fr_FR') -> Tuple[bool, str]:
        """Configure AI settings"""
        if not api_key and not self.active_config:
            return False, "API key is required"

        db = SessionLocal()
        try:
            # Test the configuration first
            try:
                if provider == 'openai':
                    client = openai.OpenAI(api_key=api_key)
                    # Test with a simple completion
                    client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                elif provider == 'gemini':
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model)
                    # Test with a simple completion
                    model.generate_content("test")
                else:
                    return False, f"Unsupported AI provider: {provider}"
            except Exception as e:
                return False, f"Error testing AI configuration: {str(e)}"

            # Deactivate all existing configs
            db.query(AIConfig).update({"is_active": False})
            
            # Create new config
            config = AIConfig(
                provider=provider,
                api_key=api_key if api_key else self.active_config.api_key if self.active_config else None,
                model=model,
                temperature=temperature,
                language=language,
                max_tokens=2000 if provider == 'openai' else None,
                is_active=True
            )
            db.add(config)
            db.commit()
            
            # Reload configuration
            self._load_active_config()
            return True, "AI configuration updated successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error configuring AI: {str(e)}"
        finally:
            db.close()

    def get_active_config(self) -> Optional[Dict]:
        """Get active AI configuration"""
        if self.active_config:
            return {
                'provider': self.active_config.provider,
                'model': self.active_config.model,
                'temperature': self.active_config.temperature,
                'language': getattr(self.active_config, 'language', 'fr_FR'),
                'last_used': self.active_config.last_used
            }
        return None

    def get_available_models(self, provider: str) -> List[str]:
        """Get available models for the specified provider"""
        if provider == 'openai':
            return ["gpt-3.5-turbo", "gpt-4"]
        elif provider == 'gemini':
            return ["gemini-pro"]
        return []
