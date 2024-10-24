import pandas as pd
from typing import List, Dict, Tuple
import hashlib
import io
import re
import csv

def read_csv_file(file) -> Tuple[pd.DataFrame, bool, str]:
    """Read CSV file without validation, trying different encodings and parsing options"""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            # Try different CSV parsing options
            try:
                # First try: standard reading
                df = pd.read_csv(
                    file, 
                    encoding=encoding,
                    encoding_errors='replace',
                    on_bad_lines='skip',
                    low_memory=False
                )
                return df, True, "CSV read successfully"
            except:
                # Second try: with different separator
                file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    encoding_errors='replace',
                    on_bad_lines='skip',
                    sep=';',
                    low_memory=False
                )
                return df, True, "CSV read successfully"
            
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Try manual reading for problematic files
            try:
                file.seek(0)
                # Read file content
                content = file.read().decode(encoding)
                # Split into lines
                lines = content.split('\n')
                if not lines:
                    continue
                
                # Detect delimiter
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(lines[0])
                delimiter = dialect.delimiter
                
                # Parse manually
                data = []
                headers = None
                for line in lines:
                    if not line.strip():
                        continue
                    row = line.split(delimiter)
                    if headers is None:
                        headers = [h.strip() for h in row]
                    else:
                        # Ensure row has same length as headers
                        while len(row) < len(headers):
                            row.append('')
                        data.append(dict(zip(headers, [cell.strip() for cell in row[:len(headers)]])))
                
                if data:
                    df = pd.DataFrame(data)
                    return df, True, "CSV read successfully with manual parsing"
                
            except Exception as manual_error:
                continue
    
    return pd.DataFrame(), False, "Unable to read CSV with any supported encoding or format"

def read_excel_file(file) -> Tuple[pd.DataFrame, bool, str]:
    """Read Excel file (XLS/XLSX) without validation"""
    try:
        # Try reading as XLSX first
        df = pd.read_excel(file, engine='openpyxl')
        return df, True, "Excel file read successfully"
    except Exception as xlsx_error:
        try:
            # If XLSX fails, try XLS format
            df = pd.read_excel(file, engine='xlrd')
            return df, True, "Excel file read successfully"
        except Exception as xls_error:
            return pd.DataFrame(), False, f"Error reading Excel file: {str(xlsx_error)}"

def clean_price(value) -> float:
    """Clean price value to extract only numbers"""
    if pd.isna(value) or value == '' or value == 'NC':
        return 0.0
    try:
        # Remove all non-numeric characters except dots and commas
        cleaned = re.sub(r'[^0-9,.]', '', str(value))
        # Replace comma with dot for decimal
        cleaned = cleaned.replace(',', '.')
        # If multiple dots exist, keep only the first one
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

def clean_quantity(value) -> int:
    """Clean quantity value to extract only numbers"""
    if pd.isna(value) or value == '' or value == 'NC':
        return 0
    try:
        # Remove all non-numeric characters
        cleaned = re.sub(r'[^0-9]', '', str(value))
        return int(cleaned) if cleaned else 0
    except:
        return 0

def process_file(file, file_type: str, column_mapping: Dict[str, str] = None) -> Tuple[pd.DataFrame, bool, str]:
    """Process uploaded file (CSV or Excel) with validation and encoding handling"""
    if file_type == 'csv':
        df, success, message = read_csv_file(file)
    else:  # xlsx or xls
        df, success, message = read_excel_file(file)
        
    if not success:
        return pd.DataFrame(), False, message
    
    # Apply column mapping if provided
    if column_mapping:
        try:
            df = df.rename(columns=column_mapping)
        except Exception as e:
            return pd.DataFrame(), False, f"Error applying column mapping: {str(e)}"
    
    return df, True, "File processed successfully"

def generate_fusion_code(article_code: str, prefix: str = None) -> str:
    """Generate unique fusion article code"""
    if prefix is None:
        prefix = article_code.split('-')[0] if '-' in article_code else article_code
    combined = f"{prefix.lower()}_{article_code}".encode('utf-8')
    return hashlib.md5(combined).hexdigest()[:12]

def standardize_catalog_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize catalog data format"""
    # Convert string columns
    string_columns = ['article_code', 'barcode', 'name', 'description']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    # Convert and clean numeric columns
    if 'price' in df.columns:
        df['price'] = df['price'].apply(clean_price)
    if 'purchase_price' in df.columns:
        df['purchase_price'] = df['purchase_price'].apply(clean_price)
    if 'eco_value' in df.columns:
        df['eco_value'] = df['eco_value'].apply(clean_price)
    if 'stock_quantity' in df.columns:
        df['stock_quantity'] = df['stock_quantity'].apply(clean_quantity)
    
    return df

def get_example_csv_content() -> str:
    """Generate example CSV content"""
    return """article_code,name,description,barcode,price,stock_quantity,purchase_price,eco_value
ABC123,Product Name,Product Description,1234567890123,99.99,10,80.00,2.00
XYZ789,Another Product,Another Description,9876543210123,149.99,5,120.00,2.50"""

def get_example_excel_content() -> bytes:
    """Generate example Excel content"""
    df = pd.DataFrame({
        'article_code': ['ABC123', 'XYZ789'],
        'name': ['Product Name', 'Another Product'],
        'description': ['Product Description', 'Another Description'],
        'barcode': ['1234567890123', '9876543210123'],
        'price': [99.99, 149.99],
        'stock_quantity': [10, 5],
        'purchase_price': [80.00, 120.00],
        'eco_value': [2.00, 2.50]
    })
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    return excel_buffer.getvalue()
