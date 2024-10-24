from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Create database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./catalog.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    stripe_customer_id = Column(String, unique=True)
    role = Column(String, default="user")  # user, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    catalog_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String, unique=True)
    plan_type = Column(String)  # free_trial, basic, premium
    status = Column(String)  # active, canceled, trialing, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    amount = Column(Float)
    currency = Column(String)
    stripe_invoice_id = Column(String, unique=True)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String)  # openai, ollama, etc.
    model = Column(String)
    api_key = Column(String)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    manufacturers = relationship("Manufacturer", back_populates="brand")

class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    code = Column(String, unique=True)
    contact_info = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="manufacturers")
    catalogs = relationship("Catalog", back_populates="manufacturer")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True)
    contact_info = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prices = relationship("SupplierPrice", back_populates="supplier")
    ftp_connections = relationship("FTPConnection", back_populates="supplier")

class SupplierPrice(Base):
    __tablename__ = "supplier_prices"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    catalog_id = Column(Integer, ForeignKey("catalogs.id"))
    product_id = Column(String, index=True)
    price = Column(Float)
    currency = Column(String)
    quantity = Column(Integer)
    last_updated = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="prices")
    catalog = relationship("Catalog", back_populates="supplier_prices")

class FTPConnection(Base):
    __tablename__ = "ftp_connections"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    host = Column(String)
    port = Column(Integer, default=21)
    username = Column(String)
    password = Column(String)
    remote_path = Column(String)
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="ftp_connections")

class Catalog(Base):
    __tablename__ = "catalogs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"))
    source = Column(String)  # odoo, prestashop, woocommerce, etc.
    source_id = Column(String)
    data = Column(JSON)
    status = Column(String)  # active, archived, pending
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="catalogs")
    manufacturer = relationship("Manufacturer", back_populates="catalogs")
    enrichments = relationship("ProductEnrichment", back_populates="catalog")
    supplier_prices = relationship("SupplierPrice", back_populates="catalog")

class ProductEnrichment(Base):
    __tablename__ = "product_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    catalog_id = Column(Integer, ForeignKey("catalogs.id"))
    product_id = Column(String)
    original_data = Column(JSON)
    enriched_data = Column(JSON)
    status = Column(String)  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    catalog = relationship("Catalog", back_populates="enrichments")

class PlanLimit(Base):
    __tablename__ = "plan_limits"

    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String, unique=True)  # free_trial, basic, premium
    product_limit = Column(Integer)
    price = Column(Float)
    currency = Column(String, default="EUR")
    stripe_price_id = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SubscriptionMetric(Base):
    __tablename__ = "subscription_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True)
    total_users = Column(Integer)
    active_subscriptions = Column(Integer)
    trial_users = Column(Integer)
    monthly_revenue = Column(Float)
    currency = Column(String, default="EUR")
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String, unique=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)

    # Relationship
    user = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)  # login, logout, subscription_change, payment, etc.
    details = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)

    # Relationship
    user = relationship("User")

# Drop all tables and recreate
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
