from typing import List, Dict
import pandas as pd

def get_duplicate_records(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Find duplicate records based on specified columns"""
    return df[df.duplicated(subset=columns, keep=False)]

def format_error_message(errors: List[str]) -> str:
    """Format error messages for display"""
    return "\n".join(f"• {error}" for error in errors)

def prepare_catalog_summary(df: pd.DataFrame) -> Dict:
    """Prepare summary statistics for catalog data"""
    summary = {'total_records': len(df)}
    
    # Safely calculate statistics for each column
    if 'brand' in df.columns:
        summary['unique_brands'] = df['brand'].nunique()
    else:
        summary['unique_brands'] = 0
        
    if 'barcode' in df.columns:
        summary['valid_barcodes'] = df['barcode'].apply(lambda x: len(str(x)) == 13).sum()
    else:
        summary['valid_barcodes'] = 0
        
    # Calculate missing values only for existing columns
    summary['missing_values'] = {
        col: df[col].isnull().sum()
        for col in df.columns if col in ['article_code', 'barcode', 'brand', 'description', 'price']
    }
    
    return summary
