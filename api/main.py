from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
import pandas as pd
from models.database import SessionLocal
from services.catalog_service import CatalogService
from services.manufacturer_service import ManufacturerService
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="Catalog Management System API",
    description="API for managing product catalogs, manufacturers, and real-time synchronization",
    version="1.0.0"
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request/response
class ManufacturerCreate(BaseModel):
    name: str

class BrandCreate(BaseModel):
    name: str
    manufacturer_id: int

class CatalogEntry(BaseModel):
    article_code: str
    barcode: str
    brand_id: int
    description: str
    price: float

    class Config:
        json_schema_extra = {
            "example": {
                "article_code": "ABC123",
                "barcode": "1234567890123",
                "brand_id": 1,
                "description": "Sample product",
                "price": 99.99
            }
        }

# Endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Catalog Management System API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.post("/manufacturers/", tags=["Manufacturers"])
async def create_manufacturer(manufacturer: ManufacturerCreate):
    """Create a new manufacturer"""
    success, message = ManufacturerService.add_manufacturer(manufacturer.name)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.get("/manufacturers/", tags=["Manufacturers"])
async def get_manufacturers():
    """Get all manufacturers with their brands"""
    return ManufacturerService.get_manufacturers()

@app.post("/brands/", tags=["Brands"])
async def create_brand(brand: BrandCreate):
    """Create a new brand"""
    success, message = ManufacturerService.add_brand(brand.name, brand.manufacturer_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.get("/catalogs/", tags=["Catalogs"])
async def get_catalogs():
    """Get all catalog entries"""
    return CatalogService.get_catalogs()

@app.post("/catalogs/", tags=["Catalogs"])
async def create_catalog_entry(catalog: CatalogEntry):
    """Create a new catalog entry"""
    df = pd.DataFrame([catalog.dict()])
    success, message = CatalogService.add_catalog_entries(df)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": True,
        "message": str(exc.detail),
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": True,
        "message": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
