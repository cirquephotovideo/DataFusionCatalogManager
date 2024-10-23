from ftplib import FTP
import os
import tempfile
from typing import Tuple, List
import pandas as pd
from utils.processors import read_csv_file, process_csv, standardize_catalog_data

class FTPService:
    def __init__(self, host: str, username: str = "", password: str = "", port: int = 21):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ftp = None

    def connect(self) -> Tuple[bool, str]:
        """Establish FTP connection"""
        try:
            self.ftp = FTP()
            self.ftp.connect(self.host, self.port)
            if self.username and self.password:
                self.ftp.login(self.username, self.password)
            else:
                self.ftp.login()  # Anonymous login
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        """Close FTP connection"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()

    def list_files(self, directory: str = "") -> Tuple[bool, List[str], str]:
        """List files in the specified directory"""
        try:
            if directory:
                self.ftp.cwd(directory)
            files = []
            self.ftp.retrlines('LIST', lambda x: files.append(x.split()[-1]))
            return True, files, "Files listed successfully"
        except Exception as e:
            return False, [], f"Error listing files: {str(e)}"

    def download_file(self, remote_path: str) -> Tuple[bool, pd.DataFrame, str]:
        """Download and process file from FTP server"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                # Download the file
                self.ftp.retrbinary(f'RETR {remote_path}', temp_file.write)
                temp_file_path = temp_file.name

            # Just read the CSV file without processing
            df, success, message = read_csv_file(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            if success:
                return True, df, "File downloaded successfully"
            return False, pd.DataFrame(), message
            
        except Exception as e:
            return False, pd.DataFrame(), f"Error downloading file: {str(e)}"
