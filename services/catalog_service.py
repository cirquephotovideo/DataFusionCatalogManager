from models.database import SessionLocal, Catalog, Brand
from sqlalchemy.orm import Session
from typing import List, Dict
import pandas as pd

class CatalogService:
    @staticmethod
    def add_catalog_entries(df: pd.DataFrame) -> tuple[bool, str]:
        """Add new catalog entries to database"""
        db = SessionLocal()
        try:
            for _, row in df.iterrows():
                brand = db.query(Brand).filter(Brand.name == row['brand']).first()
                if not brand:
                    continue
                
                catalog_entry = Catalog(
                    article_code=row['article_code'],
                    barcode=row['barcode'],
                    brand_id=brand.id,
                    description=row['description'],
                    price=float(row['price']) if 'price' in row else 0.0
                )
                db.add(catalog_entry)
            
            db.commit()
            return True, "Catalog entries added successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error adding catalog entries: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def get_catalogs() -> List[Dict]:
        """Retrieve all catalog entries"""
        db = SessionLocal()
        try:
            catalogs = db.query(Catalog).all()
            return [
                {
                    'id': c.id,
                    'article_code': c.article_code,
                    'barcode': c.barcode,
                    'description': c.description,
                    'price': c.price
                }
                for c in catalogs
            ]
        finally:
            db.close()
