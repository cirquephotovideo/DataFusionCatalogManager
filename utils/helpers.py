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
    return {
        'total_records': len(df),
        'unique_brands': df['brand'].nunique(),
        'valid_barcodes': df['barcode'].apply(lambda x: len(str(x)) == 13).sum(),
        'missing_values': df.isnull().sum().to_dict()
    }
