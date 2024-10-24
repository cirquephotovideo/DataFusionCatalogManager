import xmlrpc.client
import logging
import ssl
import json
import os
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from models.database import SessionLocal, Catalog, AIConfig
from sqlalchemy.orm import Session

class OdooService:
    def __init__(self, url: str, db: str, username: str, password: str, verify_ssl: bool = False):
        """Initialize Odoo connection"""
        self.url = url.rstrip('/')  # Remove trailing slash
        self.db = db
        self.username = username
        self.password = password
        self.field_mappings = None  # Will be loaded when needed
        
        # Create SSL context
        if not verify_ssl:
            self.ssl_context = ssl._create_unverified_context()
        else:
            self.ssl_context = ssl.create_default_context()
        
        # XML-RPC endpoints with SSL context
        self.common = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/common',
            context=self.ssl_context
        )
        self.models = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/object',
            context=self.ssl_context
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Test Odoo connection with detailed error reporting"""
        try:
            # Validate URL format
            if not self.url.startswith(('http://', 'https://')):
                return False, "Invalid URL format. URL must start with http:// or https://"

            # Try to get version info first
            try:
                version = self.common.version()
                if not version:
                    return False, "Could not get Odoo version information"
            except Exception as e:
                if "SSL" in str(e):
                    return False, "SSL Certificate error. Try disabling SSL verification if using self-signed certificate."
                return False, f"Server connection error: {str(e)}"

            # Try authentication
            success, message = self._authenticate()
            if not success:
                return False, message

            # Test database access
            try:
                # Try a simple database operation
                self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'product.template', 'search_count',
                    [[['active', '=', True]]]
                )
            except xmlrpc.client.Fault as f:
                if "access" in str(f).lower():
                    return False, "Authentication successful but user lacks necessary permissions."
                return False, f"Database access error: {str(f)}"

            return True, f"Connected successfully to Odoo {version.get('server_version', 'Unknown')}"
            
        except Exception as e:
            error_msg = str(e)
            if "SSL" in error_msg:
                return False, "SSL Certificate error. Try disabling SSL verification if using self-signed certificate."
            elif "connection" in error_msg.lower():
                return False, f"Connection error: Could not connect to {self.url}"
            else:
                return False, f"Error: {error_msg}"

    def _authenticate(self) -> Tuple[bool, str]:
        """Authenticate with Odoo and get user id"""
        try:
            # First test if server is reachable
            version = self.common.version()
            if not version:
                return False, "Could not get Odoo version information"

            # Try to authenticate
            uid = self.common.authenticate(self.db, self.username, self.password, {})
            if uid:
                self.uid = uid
                return True, "Authentication successful"
            else:
                return False, "Authentication failed. Please check credentials."

        except xmlrpc.client.Fault as f:
            # Parse database error from fault string
            if "database" in str(f).lower() and "exist" in str(f).lower():
                # Try to list available databases
                try:
                    dbs = self.common.db.list()
                    return False, f"Database '{self.db}' not found. Available databases: {', '.join(dbs)}"
                except:
                    return False, f"Database '{self.db}' not found. Please verify the database name."
            return False, f"Odoo error: {str(f)}"
        except ConnectionRefusedError:
            return False, f"Connection refused. Please check if the Odoo server is running at {self.url}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def get_odoo_fields(self) -> Dict[str, str]:
        """Get available fields from Odoo product.template model"""
        try:
            # Authenticate first
            success, message = self._authenticate()
            if not success:
                return {}

            # Get fields info from Odoo
            fields_info = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.template', 'fields_get',
                [], {'attributes': ['string', 'type', 'help']}
            )

            # Format fields info
            fields = {}
            for field_name, field_info in fields_info.items():
                field_type = field_info.get('type', '')
                if field_type in ['char', 'text', 'float', 'integer', 'boolean']:
                    fields[field_name] = {
                        'name': field_name,
                        'string': field_info.get('string', field_name),
                        'type': field_type,
                        'help': field_info.get('help', '')
                    }

            return fields
        except Exception as e:
            logging.error(f"Error getting Odoo fields: {str(e)}")
            return {}

    def load_field_mappings(self) -> Dict:
        """Load Odoo field mappings from configuration or create default"""
        try:
            # Try to load from file first
            if os.path.exists('odoo_mappings.json'):
                with open('odoo_mappings.json', 'r') as f:
                    self.field_mappings = json.load(f)
                    return self.field_mappings

            # If no file exists, create default mappings
            self.field_mappings = {
                'name': 'name',
                'article_code': 'default_code',
                'barcode': 'barcode',
                'description': 'description',
                'price': 'list_price',
                'purchase_price': 'standard_price',
                'stock_quantity': 'qty_available'
            }
            return self.field_mappings
        except Exception:
            # If any error occurs, return default mappings
            self.field_mappings = {
                'name': 'name',
                'article_code': 'default_code',
                'barcode': 'barcode',
                'description': 'description',
                'price': 'list_price',
                'purchase_price': 'standard_price',
                'stock_quantity': 'qty_available'
            }
            return self.field_mappings

    def save_field_mappings(self, mappings: Dict) -> bool:
        """Save Odoo field mappings"""
        try:
            with open('odoo_mappings.json', 'w') as f:
                json.dump(mappings, f)
            self.field_mappings = mappings
            return True
        except Exception as e:
            logging.error(f"Error saving mappings: {str(e)}")
            return False

    def get_field_mappings(self) -> Dict:
        """Get current field mappings"""
        if self.field_mappings is None:
            self.field_mappings = self.load_field_mappings()
        return self.field_mappings

    def get_field_suggestions(self) -> Dict[str, List[str]]:
        """Get field mapping suggestions based on Odoo fields"""
        odoo_fields = self.get_odoo_fields()
        
        # Define common patterns for each local field
        suggestions = {
            'name': ['name', 'display_name', 'product_name'],
            'article_code': ['default_code', 'reference', 'sku', 'internal_reference'],
            'barcode': ['barcode', 'ean13', 'upc'],
            'description': ['description', 'description_sale', 'description_purchase'],
            'price': ['list_price', 'sale_price', 'retail_price'],
            'purchase_price': ['standard_price', 'cost_price', 'purchase_price'],
            'stock_quantity': ['qty_available', 'virtual_available', 'incoming_qty']
        }

        # Add actual matching fields from Odoo
        for local_field, patterns in suggestions.items():
            matching_fields = [
                field for field in odoo_fields.keys()
                if any(pattern in field.lower() for pattern in patterns)
            ]
            suggestions[local_field] = matching_fields

        return suggestions

    def sync_products(self) -> Tuple[bool, str]:
        """Sync products with Odoo"""
        try:
            # Verify connection first
            success, message = self._authenticate()
            if not success:
                return False, message

            # Get Odoo field names from mappings
            fields = list(self.get_field_mappings().values())
            
            # Get products from Odoo
            odoo_products = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.template', 'search_read',
                [[['active', '=', True]]],
                {'fields': fields}
            )

            db = SessionLocal()
            try:
                updated = 0
                created = 0
                
                for product in odoo_products:
                    # Reverse map fields from Odoo to local
                    local_data = {}
                    for local_field, odoo_field in self.get_field_mappings().items():
                        if odoo_field in product:
                            local_data[local_field] = product[odoo_field]
                    
                    # Check if product exists
                    existing_product = None
                    if local_data.get('barcode'):
                        existing_product = db.query(Catalog).filter(
                            Catalog.barcode == local_data['barcode']
                        ).first()
                    
                    if not existing_product and local_data.get('article_code'):
                        existing_product = db.query(Catalog).filter(
                            Catalog.article_code == local_data['article_code']
                        ).first()

                    if existing_product:
                        # Update existing product
                        for field, value in local_data.items():
                            setattr(existing_product, field, value)
                        existing_product.updated_at = datetime.utcnow()
                        existing_product.last_import = datetime.utcnow()
                        existing_product.import_source = 'odoo'
                        updated += 1
                    else:
                        # Create new product
                        new_product = Catalog(**local_data)
                        new_product.created_at = datetime.utcnow()
                        new_product.updated_at = datetime.utcnow()
                        new_product.last_import = datetime.utcnow()
                        new_product.import_source = 'odoo'
                        db.add(new_product)
                        created += 1

                db.commit()
                return True, f"Sync completed: {created} products created, {updated} products updated"
            
            except Exception as db_error:
                db.rollback()
                raise db_error
            finally:
                db.close()

        except Exception as e:
            logging.error(f"Odoo sync error: {str(e)}")
            return False, f"Sync failed: {str(e)}"

    def export_products(self, products: List[Dict]) -> Tuple[bool, str]:
        """Export products to Odoo"""
        try:
            # Verify connection first
            success, message = self._authenticate()
            if not success:
                return False, message

            # Get field mappings
            mappings = self.get_field_mappings()
            reverse_mappings = {v: k for k, v in mappings.items() if v}  # Only include non-empty mappings

            updated = 0
            created = 0
            errors = []
            processed_barcodes = set()  # Track processed barcodes

            for product in products:
                try:
                    # Convert local fields to Odoo fields
                    odoo_data = {}
                    for odoo_field, local_field in reverse_mappings.items():
                        if local_field in product and product[local_field] is not None:
                            # Clean and validate the value before adding
                            value = product[local_field]
                            if isinstance(value, (int, float, bool, str)):
                                odoo_data[odoo_field] = value
                            elif value is not None:
                                odoo_data[odoo_field] = str(value)

                    # Ensure required fields are present
                    if not odoo_data.get('name'):
                        odoo_data['name'] = product.get('name') or product.get('article_code', 'Unknown Product')

                    # Check for existing product first
                    existing_id = None
                    search_domain = []

                    # First try to find by default_code (article_code)
                    if odoo_data.get('default_code'):
                        search_domain = [['default_code', '=', odoo_data['default_code']]]
                        existing_ids = self.models.execute_kw(
                            self.db, self.uid, self.password,
                            'product.template', 'search',
                            [search_domain]
                        )
                        if existing_ids:
                            existing_id = existing_ids[0]

                    # If not found by default_code, try barcode
                    if not existing_id and odoo_data.get('barcode'):
                        barcode = odoo_data['barcode']
                        
                        # Skip if we've already processed this barcode
                        if barcode in processed_barcodes:
                            errors.append(f"Skipping duplicate barcode {barcode} for product {product.get('name', 'Unknown')}")
                            continue
                        
                        # Check if barcode exists in Odoo
                        search_domain = [['barcode', '=', barcode]]
                        existing_ids = self.models.execute_kw(
                            self.db, self.uid, self.password,
                            'product.template', 'search',
                            [search_domain]
                        )
                        if existing_ids:
                            existing_id = existing_ids[0]
                        
                        processed_barcodes.add(barcode)

                    if existing_id:
                        # Update existing product
                        if odoo_data:  # Only update if there's data to update
                            try:
                                self.models.execute_kw(
                                    self.db, self.uid, self.password,
                                    'product.template', 'write',
                                    [existing_id, odoo_data]
                                )
                                updated += 1
                            except xmlrpc.client.Fault as f:
                                if "Barcode" in str(f):
                                    # Remove barcode from update if it causes conflict
                                    odoo_data.pop('barcode', None)
                                    self.models.execute_kw(
                                        self.db, self.uid, self.password,
                                        'product.template', 'write',
                                        [existing_id, odoo_data]
                                    )
                                    updated += 1
                                    errors.append(f"Updated product {product.get('name', 'Unknown')} without barcode due to conflict")
                                else:
                                    raise f
                    else:
                        # Create new product
                        if odoo_data:  # Only create if there's data to create
                            try:
                                self.models.execute_kw(
                                    self.db, self.uid, self.password,
                                    'product.template', 'create',
                                    [odoo_data]
                                )
                                created += 1
                            except xmlrpc.client.Fault as f:
                                if "Barcode" in str(f):
                                    # Try creating without barcode
                                    odoo_data.pop('barcode', None)
                                    self.models.execute_kw(
                                        self.db, self.uid, self.password,
                                        'product.template', 'create',
                                        [odoo_data]
                                    )
                                    created += 1
                                    errors.append(f"Created product {product.get('name', 'Unknown')} without barcode due to conflict")
                                else:
                                    raise f

                except Exception as e:
                    product_id = product.get('name', product.get('article_code', 'Unknown'))
                    errors.append(f"Error processing product {product_id}: {str(e)}")

            # Prepare result message
            result_message = f"Export completed: {created} products created, {updated} products updated"
            if errors:
                result_message += f"\nWarnings/Errors ({len(errors)}):"
                for error in errors[:10]:  # Show first 10 errors
                    result_message += f"\n- {error}"
                if len(errors) > 10:
                    result_message += f"\n... and {len(errors) - 10} more messages"

            # Consider it successful even with barcode warnings
            return True, result_message

        except Exception as e:
            logging.error(f"Odoo export error: {str(e)}")
            return False, f"Export failed: {str(e)}"

    def get_available_databases(self) -> List[str]:
        """Get list of available databases"""
        try:
            return self.common.db.list()
        except:
            return []

    def get_sync_status(self) -> Dict:
        """Get sync status information"""
        try:
            # Test connection first
            success, message = self._authenticate()
            if not success:
                return {
                    'status': 'disconnected',
                    'error': message,
                    'mappings': self.get_field_mappings()
                }

            product_count = self.models.execute_kw(
                self.db, self.uid, self.password,
                'product.template', 'search_count',
                [[['active', '=', True]]]
            )
            
            return {
                'status': 'connected',
                'product_count': product_count,
                'last_sync': datetime.utcnow().isoformat(),
                'server_url': self.url,
                'database': self.db,
                'mappings': self.get_field_mappings()
            }
        except Exception as e:
            return {
                'status': 'disconnected',
                'error': str(e),
                'mappings': self.get_field_mappings()
            }
