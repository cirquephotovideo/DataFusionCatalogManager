from models.database import engine, SessionLocal, Supplier
from datetime import datetime

def add_test_supplier():
    session = SessionLocal()
    try:
        # Create test supplier
        test_supplier = Supplier(
            supplier_name="Test Supplier",
            contact_info={
                "email": "contact@testsupplier.com",
                "phone": "+1234567890",
                "address": "123 Test Street"
            },
            default_currency="USD",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(test_supplier)
        session.commit()
        print(f"Test supplier created with ID: {test_supplier.supplier_id}")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating test supplier: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    add_test_supplier()
