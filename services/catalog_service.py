from models.database import SessionLocal, Catalog, Brand, Supplier, SupplierPrice, FTPConnection
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import json

class CatalogService:
    @staticmethod
    def update_catalog(product_id: str, updated_data: Dict) -> bool:
        """Update a catalog entry"""
        db = SessionLocal()
        try:
            product = db.query(Catalog).filter(Catalog.id == product_id).first()
            if not product:
                return False
            
            # Update fields
            for key, value in updated_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            
            product.updated_at = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating product: {str(e)}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_catalog(product_id: str) -> Optional[Dict]:
        """Retrieve a single catalog entry by ID"""
        db = SessionLocal()
        try:
            catalog = (
                db.query(Catalog)
                .options(
                    joinedload(Catalog.supplier_prices)
                    .joinedload(SupplierPrice.supplier)
                )
                .filter(Catalog.id == product_id)
                .first()
            )
            
            if not catalog:
                return None
                
            return {
                'id': catalog.id,
                'reference': catalog.reference,
                'article_code': catalog.article_code,
                'name': catalog.name,
                'barcode': catalog.barcode,
                'description': catalog.description,
                'price': catalog.price,
                'stock_quantity': catalog.stock_quantity,
                'purchase_price': catalog.purchase_price,
                'eco_value': catalog.eco_value,
                'created_at': catalog.created_at,
                'updated_at': catalog.updated_at,
                'last_import': catalog.last_import,
                'import_source': catalog.import_source,
                'supplier_prices': [
                    {
                        'supplier_code': sp.supplier.code,
                        'price': sp.price,
                        'stock': sp.stock
                    }
                    for sp in catalog.supplier_prices
                ]
            }
        finally:
            db.close()

    @staticmethod
    def add_catalog_entries(df: pd.DataFrame, source: str = None) -> tuple[bool, str]:
        """Add new catalog entries to database"""
        db = SessionLocal()
        try:
            added_count = 0
            updated_count = 0
            for _, row in df.iterrows():
                # Only article_code is required
                if 'article_code' not in row or pd.isna(row['article_code']):
                    continue

                try:
                    # Check for existing product by barcode
                    existing_product = None
                    if 'barcode' in row and pd.notna(row['barcode']):
                        existing_product = db.query(Catalog).filter(
                            Catalog.barcode == str(row['barcode'])
                        ).first()

                    if existing_product:
                        # Update existing product
                        if 'stock_quantity' in row and pd.notna(row['stock_quantity']):
                            existing_product.stock_quantity += CatalogService.clean_quantity(row['stock_quantity'])
                        if 'purchase_price' in row and pd.notna(row['purchase_price']):
                            existing_product.purchase_price = CatalogService.clean_price(row['purchase_price'])
                        existing_product.updated_at = datetime.utcnow()
                        existing_product.last_import = datetime.utcnow()
                        existing_product.import_source = source
                        updated_count += 1
                    else:
                        # Create new product
                        catalog_entry = Catalog(
                            article_code=str(row['article_code']),
                            name=str(row['name']) if 'name' in row and pd.notna(row['name']) else None,
                            barcode=str(row['barcode']) if 'barcode' in row and pd.notna(row['barcode']) else None,
                            description=str(row['description']) if 'description' in row and pd.notna(row['description']) else None,
                            stock_quantity=CatalogService.clean_quantity(row['stock_quantity']) if 'stock_quantity' in row else 0,
                            price=CatalogService.clean_price(row['price']) if 'price' in row else 0.0,
                            purchase_price=CatalogService.clean_price(row['purchase_price']) if 'purchase_price' in row else 0.0,
                            eco_value=CatalogService.clean_price(row['eco_value']) if 'eco_value' in row else 0.0,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                            last_import=datetime.utcnow(),
                            import_source=source
                        )
                        db.add(catalog_entry)
                        added_count += 1
                except Exception as e:
                    print(f"Skipping row due to error: {str(e)}")
                    continue
            
            db.commit()
            return True, f"Successfully imported {added_count} new products and updated {updated_count} existing products"
        except Exception as e:
            db.rollback()
            return False, f"Error during import: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def add_single_product(product_data: Dict) -> bool:
        """Add a single product to the database"""
        db = SessionLocal()
        try:
            catalog_entry = Catalog(
                article_code=product_data['article_code'],
                name=product_data.get('name'),
                barcode=product_data.get('barcode'),
                description=product_data.get('description'),
                stock_quantity=CatalogService.clean_quantity(product_data.get('stock_quantity', 0)),
                price=CatalogService.clean_price(product_data.get('price', 0.0)),
                purchase_price=CatalogService.clean_price(product_data.get('purchase_price', 0.0)),
                eco_value=CatalogService.clean_price(product_data.get('eco_value', 0.0)),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_import=datetime.utcnow(),
                import_source='manual'
            )
            db.add(catalog_entry)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error adding product: {str(e)}")
            return False
        finally:
            db.close()

    @staticmethod
    def search_products(query: str) -> List[Catalog]:
        """Search products by reference, name, or description"""
        db = SessionLocal()
        try:
            search = f"%{query}%"
            products = (
                db.query(Catalog)
                .options(
                    joinedload(Catalog.supplier_prices)
                    .joinedload(SupplierPrice.supplier)
                )
                .filter(
                    or_(
                        Catalog.reference.ilike(search),
                        Catalog.name.ilike(search),
                        Catalog.description.ilike(search),
                        Catalog.article_code.ilike(search),
                        Catalog.barcode.ilike(search)
                    )
                )
                .all()
            )
            return products
        finally:
            db.close()

    @staticmethod
    def get_catalogs() -> List[Dict]:
        """Retrieve all catalog entries"""
        db = SessionLocal()
        try:
            catalogs = (
                db.query(Catalog)
                .options(
                    joinedload(Catalog.supplier_prices)
                    .joinedload(SupplierPrice.supplier)
                )
                .all()
            )
            return [
                {
                    'id': c.id,
                    'reference': c.reference,
                    'article_code': c.article_code,
                    'name': c.name,
                    'barcode': c.barcode,
                    'description': c.description,
                    'price': c.price,
                    'stock_quantity': c.stock_quantity,
                    'purchase_price': c.purchase_price,
                    'eco_value': c.eco_value,
                    'created_at': c.created_at,
                    'updated_at': c.updated_at,
                    'last_import': c.last_import,
                    'import_source': c.import_source,
                    'supplier_prices': [
                        {
                            'supplier_code': sp.supplier.code,
                            'price': sp.price,
                            'stock': sp.stock
                        }
                        for sp in c.supplier_prices
                    ]
                }
                for c in catalogs
            ]
        finally:
            db.close()

    @staticmethod
    def save_ftp_mapping(connection_name: str, mapping: Dict) -> bool:
        """Save column mapping for FTP connection"""
        db = SessionLocal()
        try:
            connection = db.query(FTPConnection).filter(
                FTPConnection.name == connection_name
            ).first()
            
            if connection:
                connection.column_mapping = mapping
                connection.last_used = datetime.utcnow()
            else:
                connection = FTPConnection(
                    name=connection_name,
                    column_mapping=mapping,
                    last_used=datetime.utcnow()
                )
                db.add(connection)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error saving mapping: {str(e)}")
            return False
        finally:
            db.close()

    @staticmethod
    def get_ftp_mapping(connection_name: str) -> Dict:
        """Get column mapping for FTP connection"""
        db = SessionLocal()
        try:
            connection = db.query(FTPConnection).filter(
                FTPConnection.name == connection_name
            ).first()
            
            if connection and connection.column_mapping:
                return connection.column_mapping
            return {}
        finally:
            db.close()

    @staticmethod
    def clean_price(value) -> float:
        """Clean price value to extract only numbers"""
        if pd.isna(value) or value == '' or value == 'NC':
            return 0.0
        try:
            # Remove all non-numeric characters except dots and commas
            cleaned = str(value).replace(',', '.')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0

    @staticmethod
    def clean_quantity(value) -> int:
        """Clean quantity value to extract only numbers"""
        if pd.isna(value) or value == '' or value == 'NC':
            return 0
        try:
            return int(float(str(value)))
        except:
            return 0
