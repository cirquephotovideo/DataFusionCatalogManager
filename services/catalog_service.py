from models.database import SessionLocal, Catalog
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime

class CatalogService:
    @staticmethod
    def get_catalogs(db: Optional[Session] = None) -> List[Dict]:
        """Get all catalogs"""
        if not db:
            db = SessionLocal()
        try:
            catalogs = db.query(Catalog).all()
            return [CatalogService._catalog_to_dict(catalog) for catalog in catalogs]
        finally:
            if not db:
                db.close()

    @staticmethod
    def get_catalog(catalog_id: int, db: Optional[Session] = None) -> Optional[Dict]:
        """Get catalog by ID"""
        if not db:
            db = SessionLocal()
        try:
            catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
            return CatalogService._catalog_to_dict(catalog) if catalog else None
        finally:
            if not db:
                db.close()

    @staticmethod
    def create_catalog(data: Dict, db: Optional[Session] = None) -> Dict:
        """Create new catalog"""
        if not db:
            db = SessionLocal()
        try:
            catalog = Catalog(**data)
            db.add(catalog)
            db.commit()
            db.refresh(catalog)
            return CatalogService._catalog_to_dict(catalog)
        finally:
            if not db:
                db.close()

    @staticmethod
    def update_catalog(catalog_id: int, data: Dict, db: Optional[Session] = None) -> Optional[Dict]:
        """Update catalog"""
        if not db:
            db = SessionLocal()
        try:
            catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
            if catalog:
                for key, value in data.items():
                    setattr(catalog, key, value)
                catalog.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(catalog)
                return CatalogService._catalog_to_dict(catalog)
            return None
        finally:
            if not db:
                db.close()

    @staticmethod
    def delete_catalog(catalog_id: int, db: Optional[Session] = None) -> bool:
        """Delete catalog"""
        if not db:
            db = SessionLocal()
        try:
            catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
            if catalog:
                db.delete(catalog)
                db.commit()
                return True
            return False
        finally:
            if not db:
                db.close()

    @staticmethod
    def _catalog_to_dict(catalog: Catalog) -> Dict:
        """Convert catalog model to dictionary"""
        return {
            'id': catalog.id,
            'name': catalog.name,
            'description': catalog.description,
            'active': catalog.active,
            'reference': catalog.reference,
            'article_code': catalog.article_code,
            'barcode': catalog.barcode,
            'stock_quantity': catalog.stock_quantity,
            'purchase_price': catalog.purchase_price,
            'list_price': catalog.list_price,
            'created_at': catalog.created_at.isoformat() if catalog.created_at else None,
            'updated_at': catalog.updated_at.isoformat() if catalog.updated_at else None,
            'source': catalog.source,
            'source_id': catalog.source_id,
            'data': catalog.data,
            'status': catalog.status
        }
