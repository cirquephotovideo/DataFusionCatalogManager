import requests
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from models.database import SessionLocal, Catalog

class PrestashopService:
    def __init__(self, url: str = None, api_key: str = None):
        """Initialize PrestaShop connection"""
        # Load config if not provided
        if not all([url, api_key]):
            config = self.load_config()
            url = url or config.get('url')
            api_key = api_key or config.get('api_key')

        self.url = url.rstrip('/') if url else None
        self.api_key = api_key
        self.auth = (api_key, '') if api_key else None

    def load_config(self) -> Dict:
        """Load PrestaShop configuration from file"""
        try:
            with open('prestashop_config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'url': '',
                'api_key': ''
            }

    def export_product_translations(self, product_id: int, languages: List[str]) -> Tuple[bool, str]:
        """Export product translations to PrestaShop"""
        try:
            if not self.url or not self.api_key:
                return False, "PrestaShop configuration not found"

            db = SessionLocal()
            try:
                # Get product with translations
                product = db.query(Catalog).get(product_id)
                if not product:
                    return False, "Product not found"

                # For each language
                for lang in languages:
                    translation = product.get_translation(lang)
                    if not translation:
                        continue

                    # Prepare translation data
                    trans_data = {
                        'product': {
                            'name': {lang: translation.name},
                            'description': {lang: translation.description},
                            'description_short': {lang: translation.description[:800]},  # PrestaShop limit
                            'meta_title': {lang: translation.seo_title},
                            'meta_description': {lang: translation.seo_description},
                            'meta_keywords': {lang: translation.seo_keywords},
                            'link_rewrite': {lang: self.slugify(translation.name)}
                        }
                    }

                    # Update PrestaShop product translation
                    try:
                        response = requests.put(
                            f"{self.url}/api/products/{product.source_id}",
                            auth=self.auth,
                            json=trans_data
                        )
                        if not response.ok:
                            logging.error(f"Error updating translation for language {lang}: {response.text}")
                            continue

                    except Exception as e:
                        logging.error(f"Error updating translation for language {lang}: {str(e)}")
                        continue

                return True, "Translations exported successfully"

            finally:
                db.close()

        except Exception as e:
            logging.error(f"Error exporting translations: {str(e)}")
            return False, f"Error exporting translations: {str(e)}"

    def import_product_translations(self, product_id: int, languages: List[str]) -> Tuple[bool, str]:
        """Import product translations from PrestaShop"""
        try:
            if not self.url or not self.api_key:
                return False, "PrestaShop configuration not found"

            db = SessionLocal()
            try:
                # Get product
                product = db.query(Catalog).get(product_id)
                if not product:
                    return False, "Product not found"

                # Get PrestaShop product data
                try:
                    response = requests.get(
                        f"{self.url}/api/products/{product.source_id}",
                        auth=self.auth
                    )
                    if not response.ok:
                        return False, f"Error getting product data: {response.text}"

                    ps_product = response.json().get('product', {})

                    # For each language
                    for lang in languages:
                        # Update local translation
                        product.translate(
                            lang,
                            name=ps_product.get('name', {}).get(lang),
                            description=ps_product.get('description', {}).get(lang),
                            website_description=ps_product.get('description', {}).get(lang),
                            seo_title=ps_product.get('meta_title', {}).get(lang),
                            seo_description=ps_product.get('meta_description', {}).get(lang),
                            seo_keywords=ps_product.get('meta_keywords', {}).get(lang)
                        )

                except Exception as e:
                    logging.error(f"Error getting PrestaShop data: {str(e)}")
                    return False, f"Error getting PrestaShop data: {str(e)}"

                db.commit()
                return True, "Translations imported successfully"

            finally:
                db.close()

        except Exception as e:
            logging.error(f"Error importing translations: {str(e)}")
            return False, f"Error importing translations: {str(e)}"

    def sync_translations(self, product_id: int, languages: List[str], direction: str = 'both') -> Tuple[bool, str]:
        """Synchronize translations between local database and PrestaShop"""
        if direction == 'export' or direction == 'both':
            success, message = self.export_product_translations(product_id, languages)
            if not success and direction == 'export':
                return False, message

        if direction == 'import' or direction == 'both':
            success, message = self.import_product_translations(product_id, languages)
            if not success:
                return False, message

        return True, "Translation synchronization completed"

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug"""
        import re
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text).strip('-')
        return text

    # ... (rest of the methods remain the same)
