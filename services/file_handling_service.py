import pandas as pd
import chardet
from typing import Tuple, Optional
import logging
import os
from datetime import datetime
import codecs

class FileHandlingService:
    @staticmethod
    def detect_file_encoding(file_path: str) -> str:
        """Detect the encoding of a file with high confidence"""
        try:
            # Read a larger chunk of the file for better detection
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                
                # If confidence is low or encoding is None, try specific encodings
                if not result['encoding'] or result['confidence'] < 0.8:
                    # Try to decode with common French encodings
                    encodings_to_try = ['iso-8859-1', 'cp1252', 'latin1', 'utf-8', 'utf-8-sig']
                    for encoding in encodings_to_try:
                        try:
                            raw_data.decode(encoding)
                            return encoding
                        except UnicodeDecodeError:
                            continue
                    
                    # If no encoding works, default to iso-8859-1 (common for French)
                    return 'iso-8859-1'
                
                return result['encoding']
        except Exception as e:
            logging.error(f"Error detecting file encoding: {str(e)}")
            return 'iso-8859-1'  # Default to ISO-8859-1 for French text

    @staticmethod
    def read_file_with_encoding(file_path: str, encoding: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
        """Read file with proper encoding detection and handling"""
        try:
            # For Excel files
            if file_path.endswith(('.xlsx', '.xls')):
                try:
                    df = pd.read_excel(file_path)
                    return df, 'utf-8'
                except Exception as e:
                    logging.error(f"Error reading Excel file: {str(e)}")
                    raise

            # For CSV files
            if not encoding:
                encoding = FileHandlingService.detect_file_encoding(file_path)

            # Try reading with detected encoding
            try:
                # First try with the detected encoding
                with codecs.open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    # Read first few lines to check encoding
                    f.readline()
                
                # If successful, read with pandas
                df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
                df = FileHandlingService.clean_dataframe(df)
                return df, encoding
            
            except UnicodeDecodeError:
                # If that fails, try other common encodings
                encodings_to_try = [
                    'iso-8859-1',
                    'cp1252',
                    'latin1',
                    'utf-8',
                    'utf-8-sig',
                    'mac_roman'
                ]
                
                for enc in encodings_to_try:
                    if enc != encoding:  # Skip already tried encoding
                        try:
                            df = pd.read_csv(file_path, encoding=enc, encoding_errors='replace')
                            df = FileHandlingService.clean_dataframe(df)
                            return df, enc
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            logging.error(f"Error reading file with encoding {enc}: {str(e)}")
                            continue

            raise ValueError(f"Could not read file with any supported encoding")

        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
            raise

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize dataframe content"""
        # Replace None and empty strings with NaN
        df = df.replace(['', 'None', 'NULL', 'null', 'NaN', 'nan'], pd.NA)
        
        # Drop rows where all values are NaN
        df = df.dropna(how='all')
        
        # Clean column names
        df.columns = [FileHandlingService.clean_text_data(str(col)).strip().lower().replace(' ', '_') 
                     for col in df.columns]
        
        # Clean text data in all string columns
        for column in df.select_dtypes(include=['object']).columns:
            df[column] = df[column].apply(lambda x: FileHandlingService.clean_text_data(str(x)) if pd.notna(x) else x)
        
        return df

    @staticmethod
    def clean_text_data(text: str) -> str:
        """Clean and normalize text data"""
        if not isinstance(text, str):
            return str(text)

        try:
            # Handle common French characters
            replacements = {
                b'\xe9'.decode('iso-8859-1'): 'é',
                b'\xe8'.decode('iso-8859-1'): 'è',
                b'\xea'.decode('iso-8859-1'): 'ê',
                b'\xe0'.decode('iso-8859-1'): 'à',
                b'\xe2'.decode('iso-8859-1'): 'â',
                b'\xf4'.decode('iso-8859-1'): 'ô',
                b'\xfb'.decode('iso-8859-1'): 'û',
                b'\xe7'.decode('iso-8859-1'): 'ç',
                b'\xc9'.decode('iso-8859-1'): 'É',
                b'\xc8'.decode('iso-8859-1'): 'È',
                b'\xca'.decode('iso-8859-1'): 'Ê',
                b'\xc0'.decode('iso-8859-1'): 'À',
                b'\xc2'.decode('iso-8859-1'): 'Â',
                b'\xd4'.decode('iso-8859-1'): 'Ô',
                b'\xdb'.decode('iso-8859-1'): 'Û',
                b'\xc7'.decode('iso-8859-1'): 'Ç',
                '\u2019': "'",  # Smart quote
                '\u2018': "'",  # Smart quote
                '\u201c': '"',  # Smart quote
                '\u201d': '"',  # Smart quote
                '\xa0': ' ',    # Non-breaking space
                '\r\n': '\n',   # Windows newline
                '\r': '\n',     # Mac newline
            }
            
            # Apply replacements
            for old, new in replacements.items():
                text = text.replace(old, new)

            # Remove BOM if present
            if text.startswith('\ufeff'):
                text = text[1:]

            return text.strip()

        except Exception:
            # If any error occurs, try to decode with iso-8859-1
            try:
                if isinstance(text, bytes):
                    return text.decode('iso-8859-1').strip()
                return text.encode('iso-8859-1', errors='replace').decode('iso-8859-1').strip()
            except Exception:
                # If all else fails, remove non-ASCII characters
                return ''.join(char for char in text if ord(char) < 128).strip()

    @staticmethod
    def save_import_file(file_path: str, archive_dir: str = "import_archives") -> str:
        """Save a copy of the import file with timestamp"""
        try:
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            base_name, ext = os.path.splitext(filename)
            archive_path = os.path.join(
                archive_dir,
                f"{base_name}_{timestamp}{ext}"
            )

            with open(file_path, 'rb') as source, open(archive_path, 'wb') as dest:
                dest.write(source.read())

            return archive_path

        except Exception as e:
            logging.error(f"Error archiving file {file_path}: {str(e)}")
            raise

    @staticmethod
    def get_file_metadata(file_path: str) -> dict:
        """Get metadata about the file"""
        try:
            stat = os.stat(file_path)
            encoding = FileHandlingService.detect_file_encoding(file_path)
            
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'encoding': encoding,
                'extension': os.path.splitext(file_path)[1].lower(),
                'filename': os.path.basename(file_path)
            }
        except Exception as e:
            logging.error(f"Error getting file metadata for {file_path}: {str(e)}")
            raise

    @staticmethod
    def validate_file_structure(df: pd.DataFrame, required_columns: list) -> Tuple[bool, list]:
        """Validate if the file has the required structure"""
        missing_columns = [col for col in required_columns if col not in df.columns]
        return len(missing_columns) == 0, missing_columns

    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize dataframe content"""
        return FileHandlingService.clean_dataframe(df)

    @staticmethod
    def get_file_date(file_path: str, filename_pattern: Optional[str] = None) -> datetime:
        """Extract date from file metadata or filename"""
        try:
            if filename_pattern:
                # Implementation of filename pattern matching would go here
                pass

            stat = os.stat(file_path)
            return datetime.fromtimestamp(stat.st_mtime)

        except Exception as e:
            logging.error(f"Error getting file date for {file_path}: {str(e)}")
            raise
