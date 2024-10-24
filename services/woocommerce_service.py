from woocommerce.api import API
from typing import Dict, List, Optional
import json
from datetime import datetime

class WooCommerceService:
    def __init__(self, url: str, consumer_key: str, consumer_secret: str):
        """Initialize WooCommerce service"""
        self.url = url.rstrip('/')
        self.wcapi = API(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3"
        )

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to WooCommerce"""
        try:
            response = self.wcapi.get("products", params={"per_page": 1})
            if response.status_code == 200:
                return True, "Connection successful"
            return False, f"Connection failed: {response.status_code}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def get_products(self, per_page: int = 100, page: int = 1) -> List[Dict]:
        """Get products from WooCommerce"""
        try:
            response = self.wcapi.get("products", params={
                "per_page": per_page,
                "page": page
            })
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting products: {str(e)}")
            return []

    def update_product(self, product_id: int, data: Dict) -> bool:
        """Update product in WooCommerce"""
        try:
            response = self.wcapi.put(f"products/{product_id}", data)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error updating product: {str(e)}")
            return False

    def get_categories(self) -> List[Dict]:
        """Get categories from WooCommerce"""
        try:
            response = self.wcapi.get("products/categories", params={"per_page": 100})
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting categories: {str(e)}")
            return []

    def get_variations(self, product_id: int) -> List[Dict]:
        """Get variations for a product"""
        try:
            response = self.wcapi.get(f"products/{product_id}/variations")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting variations: {str(e)}")
            return []

    def update_variation(self, product_id: int, variation_id: int, data: Dict) -> bool:
        """Update product variation"""
        try:
            response = self.wcapi.put(f"products/{product_id}/variations/{variation_id}", data)
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error updating variation: {str(e)}")
            return False

    def batch_update_products(self, updates: List[Dict]) -> tuple[bool, str]:
        """Batch update products"""
        try:
            response = self.wcapi.post("products/batch", {
                "update": updates
            })
            if response.status_code in [200, 201]:
                return True, "Batch update successful"
            return False, f"Batch update failed: {response.status_code}"
        except Exception as e:
            return False, f"Batch update error: {str(e)}"

    def sync_product(self, product_data: Dict) -> tuple[bool, str]:
        """Sync product with WooCommerce"""
        try:
            # Check if product exists by SKU
            sku = product_data.get('sku')
            if not sku:
                return False, "SKU is required for product sync"

            response = self.wcapi.get("products", params={"sku": sku})
            if response.status_code == 200:
                products = response.json()
                
                if products:
                    # Update existing product
                    product_id = products[0]['id']
                    response = self.wcapi.put(f"products/{product_id}", product_data)
                    if response.status_code in [200, 201]:
                        # Handle variations if present
                        if 'variations' in product_data:
                            for variation in product_data['variations']:
                                if 'id' in variation:
                                    self.update_variation(product_id, variation['id'], variation)
                                else:
                                    self.wcapi.post(f"products/{product_id}/variations", variation)
                        return True, f"Product updated successfully (ID: {product_id})"
                    return False, f"Failed to update product: {response.status_code}"
                else:
                    # Create new product
                    response = self.wcapi.post("products", product_data)
                    if response.status_code in [200, 201]:
                        new_product = response.json()
                        # Handle variations if present
                        if 'variations' in product_data:
                            for variation in product_data['variations']:
                                self.wcapi.post(f"products/{new_product['id']}/variations", variation)
                        return True, f"Product created successfully (ID: {new_product['id']})"
                    return False, f"Failed to create product: {response.status_code}"
            
            return False, f"Error checking product existence: {response.status_code}"
        except Exception as e:
            return False, f"Sync error: {str(e)}"

    def get_attributes(self) -> List[Dict]:
        """Get product attributes"""
        try:
            response = self.wcapi.get("products/attributes")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting attributes: {str(e)}")
            return []

    def get_shipping_classes(self) -> List[Dict]:
        """Get shipping classes"""
        try:
            response = self.wcapi.get("products/shipping_classes")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting shipping classes: {str(e)}")
            return []

    def get_tags(self) -> List[Dict]:
        """Get product tags"""
        try:
            response = self.wcapi.get("products/tags")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting tags: {str(e)}")
            return []

    def create_batch_update(self, products: List[Dict]) -> tuple[bool, str]:
        """Create batch update for multiple products"""
        try:
            # Split into chunks of 100 (WooCommerce API limit)
            chunk_size = 100
            for i in range(0, len(products), chunk_size):
                chunk = products[i:i + chunk_size]
                response = self.wcapi.post("products/batch", {
                    "update": chunk
                })
                if response.status_code not in [200, 201]:
                    return False, f"Batch update failed at chunk {i//chunk_size + 1}"
            return True, "All batch updates completed successfully"
        except Exception as e:
            return False, f"Batch update error: {str(e)}"
