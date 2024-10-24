import requests
from typing import Dict, List, Optional
import json
from datetime import datetime
import base64

class PrestashopService:
    def __init__(self, url: str, api_key: str):
        """Initialize Prestashop service"""
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.auth = base64.b64encode(f"{api_key}:".encode()).decode()
        self.headers = {
            'Authorization': f'Basic {self.auth}',
            'Output-Format': 'JSON',
            'Content-Type': 'application/json'
        }

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Prestashop"""
        try:
            response = requests.get(
                f"{self.url}/api",
                headers=self.headers,
                verify=False  # Some shops might use self-signed certificates
            )
            if response.status_code == 200:
                return True, "Connection successful"
            return False, f"Connection failed: {response.status_code}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def get_products(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get products from Prestashop"""
        try:
            response = requests.get(
                f"{self.url}/api/products",
                headers=self.headers,
                params={
                    'limit': limit,
                    'offset': offset,
                    'display': 'full'
                },
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('products', [])
            return []
        except Exception as e:
            print(f"Error getting products: {str(e)}")
            return []

    def update_product(self, product_id: int, data: Dict) -> bool:
        """Update product in Prestashop"""
        try:
            response = requests.put(
                f"{self.url}/api/products/{product_id}",
                headers=self.headers,
                json={'product': data},
                verify=False
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error updating product: {str(e)}")
            return False

    def get_categories(self) -> List[Dict]:
        """Get categories from Prestashop"""
        try:
            response = requests.get(
                f"{self.url}/api/categories",
                headers=self.headers,
                params={'display': 'full'},
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('categories', [])
            return []
        except Exception as e:
            print(f"Error getting categories: {str(e)}")
            return []

    def get_stock_available(self, product_id: int) -> Optional[Dict]:
        """Get stock information for a product"""
        try:
            response = requests.get(
                f"{self.url}/api/stock_availables",
                headers=self.headers,
                params={
                    'filter[id_product]': product_id,
                    'display': 'full'
                },
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stock_availables', [])
                return stocks[0] if stocks else None
            return None
        except Exception as e:
            print(f"Error getting stock: {str(e)}")
            return None

    def update_stock(self, stock_id: int, quantity: int) -> bool:
        """Update stock quantity"""
        try:
            data = {
                'stock_available': {
                    'quantity': quantity
                }
            }
            response = requests.put(
                f"{self.url}/api/stock_availables/{stock_id}",
                headers=self.headers,
                json=data,
                verify=False
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error updating stock: {str(e)}")
            return False

    def get_specific_prices(self, product_id: int) -> List[Dict]:
        """Get specific prices for a product"""
        try:
            response = requests.get(
                f"{self.url}/api/specific_prices",
                headers=self.headers,
                params={
                    'filter[id_product]': product_id,
                    'display': 'full'
                },
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('specific_prices', [])
            return []
        except Exception as e:
            print(f"Error getting specific prices: {str(e)}")
            return []

    def update_specific_price(self, price_id: int, data: Dict) -> bool:
        """Update specific price"""
        try:
            response = requests.put(
                f"{self.url}/api/specific_prices/{price_id}",
                headers=self.headers,
                json={'specific_price': data},
                verify=False
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error updating specific price: {str(e)}")
            return False

    def sync_product(self, product_data: Dict) -> tuple[bool, str]:
        """Sync product with Prestashop"""
        try:
            # Check if product exists by reference
            response = requests.get(
                f"{self.url}/api/products",
                headers=self.headers,
                params={
                    'filter[reference]': product_data.get('reference'),
                    'display': 'full'
                },
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                if products:
                    # Update existing product
                    product_id = products[0]['id']
                    success = self.update_product(product_id, product_data)
                    if success:
                        # Update stock if provided
                        if 'quantity' in product_data:
                            stock = self.get_stock_available(product_id)
                            if stock:
                                self.update_stock(stock['id'], product_data['quantity'])
                        return True, f"Product updated successfully (ID: {product_id})"
                    return False, "Failed to update product"
                else:
                    # Create new product
                    response = requests.post(
                        f"{self.url}/api/products",
                        headers=self.headers,
                        json={'product': product_data},
                        verify=False
                    )
                    if response.status_code in [200, 201]:
                        return True, "Product created successfully"
                    return False, f"Failed to create product: {response.status_code}"
            
            return False, f"Error checking product existence: {response.status_code}"
        except Exception as e:
            return False, f"Sync error: {str(e)}"
