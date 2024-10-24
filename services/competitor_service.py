import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Optional

class CompetitorService:
    def __init__(self):
        self.config_file = "competitor_config.json"
        self.competitors = self.load_competitors()

    def load_competitors(self) -> Dict:
        """Load competitor configurations from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def save_competitors(self):
        """Save competitor configurations to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.competitors, f, indent=2)

    def add_competitor(self, name: str, base_url: str, price_selector: str) -> bool:
        """
        Add a new competitor configuration
        Args:
            name: Competitor name
            base_url: Base URL for the competitor's website
            price_selector: CSS selector for price element
        """
        self.competitors[name] = {
            "url": base_url,
            "selectors": {
                "price": price_selector
            }
        }
        self.save_competitors()
        return True

    def remove_competitor(self, name: str) -> bool:
        """Remove a competitor configuration"""
        if name in self.competitors:
            del self.competitors[name]
            self.save_competitors()
            return True
        return False

    def get_competitors(self) -> Dict:
        """Get list of configured competitors"""
        return self.competitors

    async def fetch_price(self, session: aiohttp.ClientSession, url: str, selectors: Dict[str, str]) -> Optional[float]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    price_element = soup.select_one(selectors["price"])
                    if price_element:
                        # Extract numeric price value and convert to float
                        price_text = price_element.text.strip()
                        price = float(''.join(filter(str.isdigit, price_text))) / 100
                        return price
                return None
        except Exception as e:
            print(f"Error fetching price from {url}: {str(e)}")
            return None

    async def get_competitor_prices(self, product_reference: str) -> Dict[str, float]:
        """
        Fetch prices from all configured competitors for a given product
        """
        prices = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for competitor, config in self.competitors.items():
                # Construct product URL - this may need to be customized per competitor
                product_url = f"{config['url']}/{product_reference}"
                task = self.fetch_price(session, product_url, config['selectors'])
                tasks.append((competitor, task))
            
            for competitor, task in tasks:
                price = await task
                if price is not None:
                    prices[competitor] = price
        
        return prices

    def calculate_margin(self, purchase_price_ht: float, selling_price_ttc: float, tax_rate: float = 0.20) -> Dict:
        """
        Calculate margin details given purchase price HT and selling price TTC
        """
        selling_price_ht = selling_price_ttc / (1 + tax_rate)
        margin_ht = selling_price_ht - purchase_price_ht
        margin_percentage = (margin_ht / purchase_price_ht) * 100 if purchase_price_ht > 0 else 0
        
        return {
            "purchase_price_ht": purchase_price_ht,
            "selling_price_ht": selling_price_ht,
            "selling_price_ttc": selling_price_ttc,
            "margin_ht": margin_ht,
            "margin_percentage": margin_percentage,
            "is_profitable": margin_ht > 0
        }

    def validate_pricing_strategy(self, product_price: float, competitor_prices: Dict[str, float], min_margin: float = 0) -> Dict:
        """
        Validate pricing strategy against competitors
        """
        if not competitor_prices:
            return {"valid": True, "message": "No competitor prices available for comparison"}

        avg_competitor_price = sum(competitor_prices.values()) / len(competitor_prices)
        min_competitor_price = min(competitor_prices.values())
        
        validation = {
            "valid": True,
            "messages": []
        }

        # Check if price is too high compared to competitors
        if product_price > avg_competitor_price * 1.1:  # 10% threshold
            validation["valid"] = False
            validation["messages"].append(f"Price is significantly higher than average competitor price (€{avg_competitor_price:.2f})")

        # Check if price is too low (potential margin issues)
        if product_price < min_competitor_price * 0.9:  # 10% threshold
            validation["messages"].append("Price is significantly lower than competitors - verify margins")

        return validation
