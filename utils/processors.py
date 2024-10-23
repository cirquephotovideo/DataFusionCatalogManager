import pandas as pd
from typing import List, Dict
import hashlib

def process_csv(file) -> pd.DataFrame:
    """Process uploaded CSV file"""
    df = pd.read_csv(file)
    df = df.fillna('')
    return df

def generate_fusion_code(article_code: str, brand: str) -> str:
    """Generate unique fusion article code"""
    combined = f"{brand.lower()}_{article_code}".encode('utf-8')
    return hashlib.md5(combined).hexdigest()[:12]

def standardize_catalog_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize catalog data format"""
    standard_columns = {
        'article_code': str,
        'barcode': str,
        'brand': str,
        'description': str,
        'price': float
    }
    
    for col, dtype in standard_columns.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    
    return df
