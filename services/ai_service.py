import google.generativeai as genai
import openai
from typing import Dict, List, Tuple, Optional
from models.database import SessionLocal, AIConfig, AIEnrichmentPrompt, AIGenerationLog
from datetime import datetime
import json
import logging
from services.ollama_service import OllamaService

class AIService:
    def __init__(self):
        """Initialize AI service"""
        self.openai_client = None
        self.gemini_model = None
        self.ollama_service = OllamaService()
        self.active_config = None
        self._load_active_config()

    def _load_active_config(self):
        """Load active AI configuration"""
        db = SessionLocal()
        try:
            config = db.query(AIConfig).filter(AIConfig.is_active == True).first()
            if config:
                self.active_config = {
                    'provider': config.provider,
                    'model': config.model,
                    'api_key': config.api_key,
                    'temperature': config.temperature,
                    'language': config.language,
                    'settings': config.settings
                }
                
                if config.provider == 'openai' and config.api_key:
                    try:
                        self.openai_client = openai.OpenAI(api_key=config.api_key)
                    except Exception as e:
                        logging.error(f"Error initializing OpenAI client: {str(e)}")
                
                elif config.provider == 'gemini' and config.api_key:
                    try:
                        genai.configure(api_key=config.api_key)
                        self.gemini_model = genai.GenerativeModel(config.model)
                    except Exception as e:
                        logging.error(f"Error initializing Gemini client: {str(e)}")
                
                # Update last used timestamp
                config.last_used = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logging.error(f"Error loading AI config: {str(e)}")
        finally:
            db.close()

    def get_active_config(self) -> Optional[Dict]:
        """Get current active configuration"""
        return self.active_config

    def configure_ai(self, provider: str, model: str, api_key: Optional[str] = None,
                    temperature: float = 0.7, language: str = 'fr_FR',
                    settings: Optional[Dict] = None) -> Tuple[bool, str]:
        """Configure AI service"""
        db = SessionLocal()
        try:
            # Deactivate current active config
            db.query(AIConfig).filter(AIConfig.is_active == True).update(
                {"is_active": False}
            )

            # Create new config
            config = AIConfig(
                provider=provider,
                model=model,
                api_key=api_key,
                temperature=temperature,
                language=language,
                settings=settings or {},
                is_active=True
            )
            db.add(config)
            db.commit()

            # Reload configuration
            self._load_active_config()
            return True, "Configuration saved successfully"

        except Exception as e:
            db.rollback()
            return False, f"Error saving configuration: {str(e)}"
        finally:
            db.close()

    def get_enrichment_prompts(self, language: Optional[str] = None) -> List[Dict]:
        """Get available enrichment prompts"""
        db = SessionLocal()
        try:
            query = db.query(AIEnrichmentPrompt).filter(AIEnrichmentPrompt.is_active == True)
            if language:
                query = query.filter(AIEnrichmentPrompt.language == language)
            
            prompts = query.all()
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'prompt': p.prompt,
                    'language': p.language,
                    'category': p.category
                }
                for p in prompts
            ]
        finally:
            db.close()

    def save_enrichment_prompt(self, name: str, prompt: str, language: str,
                             category: str) -> Tuple[bool, str]:
        """Save new enrichment prompt"""
        db = SessionLocal()
        try:
            prompt_obj = AIEnrichmentPrompt(
                name=name,
                prompt=prompt,
                language=language,
                category=category
            )
            db.add(prompt_obj)
            db.commit()
            return True, "Prompt saved successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error saving prompt: {str(e)}"
        finally:
            db.close()

    def generate_content(self, prompt: str, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """Generate content using configured AI service"""
        if not self.active_config:
            return False, "No active AI configuration"

        try:
            start_time = datetime.utcnow()
            response = ""
            tokens = 0
            error_msg = None

            if self.active_config['provider'] == 'openai':
                if not self.openai_client:
                    return False, "OpenAI client not initialized"
                
                completion = self.openai_client.chat.completions.create(
                    model=self.active_config['model'],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.active_config['temperature']
                )
                response = completion.choices[0].message.content
                tokens = completion.usage.total_tokens

            elif self.active_config['provider'] == 'gemini':
                if not self.gemini_model:
                    return False, "Gemini model not initialized"
                
                result = self.gemini_model.generate_content(prompt)
                response = result.text

            elif self.active_config['provider'] == 'ollama':
                response = self.ollama_service.generate(
                    model=self.active_config['model'],
                    prompt=prompt
                )

            # Log generation
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._log_generation(prompt, response, tokens, duration, error_msg)

            return True, response

        except Exception as e:
            error_msg = str(e)
            self._log_generation(prompt, "", 0, 0, error_msg)
            return False, f"Error generating content: {error_msg}"

    def _log_generation(self, input_text: str, output_text: str, tokens: int,
                       duration: float, error_message: Optional[str] = None):
        """Log AI generation attempt"""
        db = SessionLocal()
        try:
            config = db.query(AIConfig).filter(AIConfig.is_active == True).first()
            if config:
                log = AIGenerationLog(
                    config_id=config.id,
                    input_text=input_text,
                    output_text=output_text,
                    tokens_used=tokens,
                    duration=duration,
                    status="success" if not error_message else "failed",
                    error_message=error_message
                )
                db.add(log)
                db.commit()
        except Exception as e:
            logging.error(f"Error logging AI generation: {str(e)}")
        finally:
            db.close()
