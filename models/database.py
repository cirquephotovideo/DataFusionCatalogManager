from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

# Create database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./catalog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String)  # openai, gemini, ollama
    model = Column(String)
    api_key = Column(String)
    temperature = Column(Float, default=0.7)
    language = Column(String, default='fr_FR')
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIEnrichmentPrompt(Base):
    __tablename__ = "ai_enrichment_prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    prompt = Column(Text)
    language = Column(String)
    category = Column(String)  # description, features, seo, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("ai_configs.id"))
    prompt_id = Column(Integer, ForeignKey("ai_enrichment_prompts.id"))
    input_text = Column(Text)
    output_text = Column(Text)
    tokens_used = Column(Integer)
    duration = Column(Float)  # in seconds
    status = Column(String)  # success, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    config = relationship("AIConfig")
    prompt = relationship("AIEnrichmentPrompt")

class Catalog(Base):
    __tablename__ = "catalogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    active = Column(Boolean, default=True)
    reference = Column(String, index=True)
    article_code = Column(String, index=True)
    barcode = Column(String, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    stock_quantity = Column(Integer, default=0)
    purchase_price = Column(Float, default=0.0)
    list_price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String)
    source_id = Column(String)
    data = Column(JSON)
    status = Column(String)

    # Relationships
    brand = relationship("Brand", back_populates="catalogs")
    category = relationship("Category", back_populates="products")
    enrichments = relationship("ProductEnrichment", back_populates="catalog")

class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    logo_url = Column(String)
    website = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    catalogs = relationship("Catalog", back_populates="brand")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("Catalog", back_populates="category")
    children = relationship("Category")

class ProductEnrichment(Base):
    __tablename__ = "product_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"))
    enriched_data = Column(JSON)
    status = Column(String)  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    catalog = relationship("Catalog", back_populates="enrichments")

# Create all tables
Base.metadata.create_all(bind=engine)
