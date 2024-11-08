from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, Product, SupplierProduct, Inventory

# Create database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./catalog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def empty_products():
    """Empty all products from the database"""
    session = SessionLocal()
    try:
        # Get counts before deletion for feedback
        supplier_product_count = session.query(SupplierProduct).count()
        product_count = session.query(Product).count()
        
        # First delete all inventory records
        session.query(Inventory).delete()
        
        # Then delete all supplier products due to foreign key relationship
        session.query(SupplierProduct).delete()
        
        # Finally delete all products
        session.query(Product).delete()
        
        session.commit()
        print(f"Successfully deleted {supplier_product_count} supplier products and {product_count} products from the database")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error emptying products: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    empty_products()
