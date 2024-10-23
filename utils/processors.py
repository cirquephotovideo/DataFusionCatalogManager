import pandas as pd
from typing import List, Dict, Tuple
import hashlib

def validate_csv_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate required columns in CSV file"""
    required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    return len(missing_columns) == 0, missing_columns

def process_csv(file) -> Tuple[pd.DataFrame, bool, str]:
    """Process uploaded CSV file with validation and encoding handling"""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file, encoding=encoding, encoding_errors='replace', on_bad_lines='skip')
            # Validate required columns
            columns_valid, missing_columns = validate_csv_columns(df)
            if not columns_valid:
                return pd.DataFrame(), False, f"Missing required columns: {', '.join(missing_columns)}"
            
            # Fill missing values with appropriate defaults
            defaults = {
                'article_code': '',
                'barcode': '',
                'brand': '',
                'description': '',
                'price': 0.0
            }
            df = df.fillna(defaults)
            return df, True, "CSV processed successfully"
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return pd.DataFrame(), False, f"Error processing CSV: {str(e)}"
    
    return pd.DataFrame(), False, "Unable to process CSV with any supported encoding"

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

def get_example_csv_content() -> str:
    """Generate example CSV content"""
    return """article_code,barcode,brand,description,price
ABC123,1234567890123,ExampleBrand,Product Description,99.99
XYZ789,9876543210123,AnotherBrand,Another Product,149.99"""
