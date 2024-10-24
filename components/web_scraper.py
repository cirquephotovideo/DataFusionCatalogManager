import streamlit as st
from services.ollama_service import OllamaService
from services.ai_service import AIService
import requests
from bs4 import BeautifulSoup
import json
import asyncio
from typing import List, Dict
import pandas as pd
from datetime import datetime
import urllib.parse

class WebScraper:
    def __init__(self):
        self.ollama_service = OllamaService()
        if 'ai_service' not in st.session_state:
            st.session_state.ai_service = AIService()
        self.ai_service = st.session_state.ai_service

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models from all services"""
        models = {
            "Ollama": self.ollama_service.list_models(),
            "OpenAI": ["gpt-3.5-turbo", "gpt-4"],
            "Gemini": ["gemini-pro"]
        }
        return models

    def _extract_json_from_text(self, text: str) -> Dict:
        """Extract JSON from text response"""
        if isinstance(text, dict):
            return text
            
        try:
            # Try direct JSON parsing first
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # Find JSON-like structure in text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = text[start:end]
                    return json.loads(json_str)
                else:
                    # Create default structure if no JSON found
                    return {
                        "suggested_fields": [
                            {
                                "name": "price",
                                "type": "number",
                                "importance": "high",
                                "description": "Product price"
                            },
                            {
                                "name": "name",
                                "type": "text",
                                "importance": "high",
                                "description": "Product name"
                            }
                        ]
                    }
            except:
                # Return default structure
                return {
                    "suggested_fields": [
                        {
                            "name": "price",
                            "type": "number",
                            "importance": "high",
                            "description": "Product price"
                        },
                        {
                            "name": "name",
                            "type": "text",
                            "importance": "high",
                            "description": "Product name"
                        }
                    ]
                }

    def _get_next_page_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Try to find next page URL using common patterns"""
        # Common patterns for next page links
        next_patterns = [
            'a[rel="next"]',
            'a.next',
            'a:contains("Next")',
            'a:contains("»")',
            'a.pagination-next',
            'a[aria-label="Next page"]'
        ]
        
        for pattern in next_patterns:
            next_link = soup.select_one(pattern)
            if next_link and next_link.get('href'):
                next_url = next_link['href']
                # Handle relative URLs
                if not next_url.startswith('http'):
                    return urllib.parse.urljoin(base_url, next_url)
                return next_url
        return None

    async def analyze_url(self, url: str, model_provider: str, model_name: str) -> Dict:
        """Analyze URL and suggest fields to extract"""
        try:
            # Fetch webpage content
            response = requests.get(url)
            html_content = response.text
            
            if model_provider == "Ollama":
                result = await self.ollama_service.analyze_webpage(url, html_content, model_name)
                return self._extract_json_from_text(result)
            else:
                # Use existing AI service
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
                
                Also identify pagination elements for multi-page scraping.
                
                Format the response as JSON:
                {{
                    "suggested_fields": [
                        {{
                            "name": "field_name",
                            "type": "text|number|image|etc",
                            "importance": "high|medium|low",
                            "description": "why this field is important"
                        }}
                    ],
                    "pagination": {{
                        "type": "css|xpath",
                        "next_button": "selector_for_next_button",
                        "page_numbers": "selector_for_page_numbers"
                    }}
                }}
                """
                response = await self.ai_service.generate_content(prompt, model_name)
                return self._extract_json_from_text(response)
        except Exception as e:
            st.error(f"Error analyzing URL: {str(e)}")
            return self._extract_json_from_text("{}")

    async def generate_scraping_rules(self, url: str, fields: List[str], model_provider: str, model_name: str) -> Dict:
        """Generate scraping rules for the specified fields"""
        try:
            if model_provider == "Ollama":
                result = await self.ollama_service.generate_scraping_rules(url, fields, model_name)
                return self._extract_json_from_text(result)
            else:
                prompt = f"""
                Generate web scraping rules for the following URL: {url}
                Fields to extract: {', '.join(fields)}
                
                Provide the rules in JSON format with:
                1. CSS selectors or XPath for each field
                2. Data cleaning rules
                3. Validation rules
                4. Pagination rules
                
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
                    }},
                    "pagination": {{
                        "type": "css|xpath",
                        "next_button": "selector_for_next_button",
                        "page_numbers": "selector_for_page_numbers"
                    }}
                }}
                """
                response = await self.ai_service.generate_content(prompt, model_name)
                result = self._extract_json_from_text(response)
                if "selectors" not in result:
                    # Create default selectors if none found
                    result = {
                        "selectors": {
                            field: {
                                "type": "css",
                                "path": f".{field}",
                                "attribute": "text",
                                "cleaning": [],
                                "validation": []
                            } for field in fields
                        }
                    }
                return result
        except Exception as e:
            st.error(f"Error generating rules: {str(e)}")
            return {
                "selectors": {
                    field: {
                        "type": "css",
                        "path": f".{field}",
                        "attribute": "text",
                        "cleaning": [],
                        "validation": []
                    } for field in fields
                }
            }

    def execute_scraping(self, url: str, rules: Dict, max_pages: int = 5) -> List[Dict]:
        """Execute scraping with generated rules"""
        try:
            all_results = []
            current_url = url
            pages_scraped = 0
            
            while current_url and pages_scraped < max_pages:
                try:
                    response = requests.get(current_url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract data from current page
                    page_results = []
                    for field, rule in rules["selectors"].items():
                        try:
                            if rule["type"] == "css":
                                elements = soup.select(rule["path"])
                            else:  # xpath
                                elements = soup.select(rule["path"])
                            
                            for element in elements:
                                if rule["attribute"] == "text":
                                    value = element.text.strip()
                                else:
                                    value = element.get(rule["attribute"], "")
                                
                                # Apply cleaning rules
                                for cleaning_rule in rule.get("cleaning", []):
                                    # Implement cleaning rules here
                                    pass
                                
                                # Find existing result with same index
                                result_index = len(page_results)
                                if result_index < len(page_results):
                                    page_results[result_index][field] = value
                                else:
                                    # Create new result
                                    result = {
                                        "field": field,
                                        "value": value,
                                        "page": pages_scraped + 1,
                                        "url": current_url,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    page_results.append(result)
                                
                        except Exception as e:
                            st.error(f"Error extracting {field}: {str(e)}")
                    
                    all_results.extend(page_results)
                    
                    # Try to find next page
                    if "pagination" in rules:
                        next_selector = rules["pagination"].get("next_button")
                        if next_selector:
                            next_link = soup.select_one(next_selector)
                            if next_link and next_link.get('href'):
                                current_url = urllib.parse.urljoin(url, next_link['href'])
                            else:
                                current_url = None
                        else:
                            # Try common patterns
                            current_url = self._get_next_page_url(soup, url)
                    else:
                        # Try common patterns as fallback
                        current_url = self._get_next_page_url(soup, url)
                    
                    pages_scraped += 1
                    if current_url:
                        st.info(f"Moving to page {pages_scraped + 1}...")
                
                except Exception as e:
                    st.error(f"Error processing page {pages_scraped + 1}: {str(e)}")
                    break
            
            return all_results
        except Exception as e:
            st.error(f"Error during scraping: {str(e)}")
            return []

def render_web_scraper():
    """Render web scraper interface"""
    st.title("Web Scraper")

    # Initialize scraper
    if 'web_scraper' not in st.session_state:
        st.session_state.web_scraper = WebScraper()

    # Model selection
    st.subheader("Select Model")
    models = st.session_state.web_scraper.get_available_models()
    
    model_provider = st.selectbox(
        "AI Provider",
        options=list(models.keys())
    )
    
    model_name = st.selectbox(
        "Model",
        options=models[model_provider]
    )

    # URL input
    st.subheader("Enter URL")
    url = st.text_input("URL to scrape")

    # Multi-page settings
    max_pages = st.number_input("Maximum pages to scrape", min_value=1, value=5)

    # Fields to extract
    st.subheader("Fields to Extract:")
    if 'scraping_fields' not in st.session_state:
        st.session_state.scraping_fields = ["name", "price"]

    # Add new field
    col1, col2 = st.columns([3, 1])
    with col1:
        new_field = st.text_input("Add field", key="new_field")
    with col2:
        if st.button("Add Field"):
            if new_field and new_field not in st.session_state.scraping_fields:
                st.session_state.scraping_fields.append(new_field)
                st.rerun()

    # Display and manage fields
    st.write("Current fields:")
    for field in st.session_state.scraping_fields:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(field)
        with col2:
            if st.button("❌", key=f"remove_{field}"):
                st.session_state.scraping_fields.remove(field)
                st.rerun()

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        analyze_button = st.button("1. Analyze URL", use_container_width=True)
    with col2:
        generate_button = st.button("2. Generate Rules", use_container_width=True)
    with col3:
        start_button = st.button("3. Start Scraping", type="primary", use_container_width=True)

    # Analyze URL
    if url and analyze_button:
        with st.spinner("Analyzing URL..."):
            analysis = asyncio.run(
                st.session_state.web_scraper.analyze_url(
                    url,
                    model_provider,
                    model_name
                )
            )
            if analysis and "suggested_fields" in analysis:
                st.subheader("Suggested Fields")
                for field in analysis["suggested_fields"]:
                    if st.button(
                        f"Add {field['name']} ({field['importance']})",
                        help=field['description']
                    ):
                        if field['name'] not in st.session_state.scraping_fields:
                            st.session_state.scraping_fields.append(field['name'])
                            st.rerun()

    # Generate scraping rules
    if url and st.session_state.scraping_fields and generate_button:
        with st.spinner("Generating scraping rules..."):
            rules = asyncio.run(
                st.session_state.web_scraper.generate_scraping_rules(
                    url,
                    st.session_state.scraping_fields,
                    model_provider,
                    model_name
                )
            )
            if rules and "selectors" in rules:
                st.subheader("Generated Scraping Rules")
                st.json(rules)
                st.session_state.scraping_rules = rules

    # Execute scraping
    if url and 'scraping_rules' in st.session_state and start_button:
        with st.spinner("Scraping data..."):
            results = st.session_state.web_scraper.execute_scraping(
                url,
                st.session_state.scraping_rules,
                max_pages
            )
            if results:
                st.success("Scraping completed!")
                
                # Convert results to DataFrame
                df = pd.DataFrame(results)
                
                # Display results
                st.subheader("Scraping Results")
                st.dataframe(df)
                
                # Save results
                st.session_state.latest_scraping_results = results
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Results (CSV)",
                    csv,
                    "scraping_results.csv",
                    "text/csv",
                    key='download-csv'
                )
