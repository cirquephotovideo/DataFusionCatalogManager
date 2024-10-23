from models.database import SessionLocal, Manufacturer, Brand
from sqlalchemy.orm import Session
from typing import List, Dict

class ManufacturerService:
    @staticmethod
    def add_manufacturer(name: str) -> tuple[bool, str]:
        """Add new manufacturer"""
        db = SessionLocal()
        try:
            manufacturer = Manufacturer(name=name)
            db.add(manufacturer)
            db.commit()
            return True, "Manufacturer added successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error adding manufacturer: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def add_brand(name: str, manufacturer_id: int) -> tuple[bool, str]:
        """Add new brand and link to manufacturer"""
        db = SessionLocal()
        try:
            brand = Brand(name=name, manufacturer_id=manufacturer_id)
            db.add(brand)
            db.commit()
            return True, "Brand added successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error adding brand: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def get_manufacturers() -> List[Dict]:
        """Retrieve all manufacturers and their brands"""
        db = SessionLocal()
        try:
            manufacturers = db.query(Manufacturer).all()
            return [
                {
                    'id': m.id,
                    'name': m.name,
                    'brands': [{'id': b.id, 'name': b.name} for b in m.brands]
                }
                for m in manufacturers
            ]
        finally:
            db.close()
