from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime

# Create database connection using environment variables or default to SQLite
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./catalog.db')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    brands = relationship("Brand", back_populates="manufacturer")

class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    manufacturer = relationship("Manufacturer", back_populates="brands")

class Catalog(Base):
    __tablename__ = "catalogs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    reference = Column(String, index=True)
    article_code = Column(String, index=True)
    barcode = Column(String, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    description = Column(String)
    stock_quantity = Column(Integer, default=0)
    purchase_price = Column(Float)
    eco_value = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_import = Column(DateTime)
    import_source = Column(String)
    supplier_prices = relationship("SupplierPrice", back_populates="catalog")
    enrichment = relationship("ProductEnrichment", back_populates="product", uselist=False)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True)
    prices = relationship("SupplierPrice", back_populates="supplier")

class SupplierPrice(Base):
    __tablename__ = "supplier_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    price = Column(Float)
    stock = Column(Integer)
    catalog = relationship("Catalog", back_populates="supplier_prices")
    supplier = relationship("Supplier", back_populates="prices")

class FTPConnection(Base):
    __tablename__ = "ftp_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    host = Column(String)
    username = Column(String)
    password = Column(String)
    port = Column(Integer)
    last_used = Column(DateTime)
    column_mapping = Column(JSON)

class ProductEnrichment(Base):
    __tablename__ = "product_enrichments"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("catalogs.id"), unique=True)
    long_description = Column(Text)
    technical_specs = Column(JSON)  # Store technical specifications as JSON
    tags = Column(JSON)  # Store tags as JSON array
    image_urls = Column(JSON)  # Store image URLs as JSON array
    seo_description = Column(Text)
    seo_keywords = Column(JSON)
    enriched_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ai_model_used = Column(String)  # Store which AI model was used
    product = relationship("Catalog", back_populates="enrichment")

class AIConfig(Base):
    __tablename__ = "ai_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String)  # 'openai' or 'gemini'
    api_key = Column(String)
    model = Column(String)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)

# Create tables
Base.metadata.create_all(bind=engine)
