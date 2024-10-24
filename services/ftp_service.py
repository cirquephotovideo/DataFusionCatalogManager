import ftplib
import paramiko
import pandas as pd
from io import StringIO, BytesIO
import os
from typing import Tuple, List
from datetime import datetime

class FTPService:
    def __init__(self, host: str, username: str = None, password: str = None, port: int = 21, use_sftp: bool = False):
        self.host = host
        self.username = username or 'anonymous'
        self.password = password or 'anonymous@'
        self.port = port
        self.use_sftp = use_sftp
        self.connection = None
        self.sftp = None

    def connect(self) -> Tuple[bool, str]:
        """Connect to FTP/SFTP server"""
        try:
            if self.use_sftp:
                # SFTP connection
                transport = paramiko.Transport((self.host, self.port))
                transport.connect(username=self.username, password=self.password)
                self.sftp = paramiko.SFTPClient.from_transport(transport)
                self.connection = transport
            else:
                # Regular FTP connection
                self.connection = ftplib.FTP()
                self.connection.connect(self.host, self.port)
                self.connection.login(self.username, self.password)
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self):
        """Disconnect from server"""
        try:
            if self.use_sftp:
                if self.sftp:
                    self.sftp.close()
                if self.connection:
                    self.connection.close()
            else:
                if self.connection:
                    self.connection.quit()
        except:
            pass
        finally:
            self.connection = None
            self.sftp = None

    def list_files(self) -> Tuple[bool, List[str], str]:
        """List files in current directory"""
        try:
            if self.use_sftp:
                files = self.sftp.listdir()
            else:
                files = self.connection.nlst()
            return True, files, "Files listed successfully"
        except Exception as e:
            return False, [], f"Error listing files: {str(e)}"

    def download_file(self, filename: str) -> Tuple[bool, pd.DataFrame, str]:
        """Download and parse file"""
        try:
            # Create a buffer to store file content
            buffer = BytesIO()

            if self.use_sftp:
                # SFTP download
                self.sftp.getfo(filename, buffer)
            else:
                # FTP download
                self.connection.retrbinary(f'RETR {filename}', buffer.write)

            buffer.seek(0)
            
            # Try to determine file type from extension
            file_ext = os.path.splitext(filename)[1].lower()
            
            try:
                if file_ext in ['.xlsx', '.xls']:
                    df = pd.read_excel(buffer)
                else:  # Default to CSV
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'cp1252']
                    for encoding in encodings:
                        try:
                            buffer.seek(0)
                            df = pd.read_csv(buffer, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        return False, pd.DataFrame(), "Unable to decode file with supported encodings"
                
                return True, df, "File downloaded and parsed successfully"
            except Exception as parse_error:
                return False, pd.DataFrame(), f"Error parsing file: {str(parse_error)}"
                
        except Exception as e:
            return False, pd.DataFrame(), f"Error downloading file: {str(e)}"

    def upload_file(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """Upload file to server"""
        try:
            if self.use_sftp:
                self.sftp.put(local_path, remote_path)
            else:
                with open(local_path, 'rb') as file:
                    self.connection.storbinary(f'STOR {remote_path}', file)
            return True, "File uploaded successfully"
        except Exception as e:
            return False, f"Error uploading file: {str(e)}"

    def create_directory(self, directory: str) -> Tuple[bool, str]:
        """Create directory on server"""
        try:
            if self.use_sftp:
                self.sftp.mkdir(directory)
            else:
                self.connection.mkd(directory)
            return True, "Directory created successfully"
        except Exception as e:
            return False, f"Error creating directory: {str(e)}"

    def change_directory(self, directory: str) -> Tuple[bool, str]:
        """Change current directory"""
        try:
            if self.use_sftp:
                self.sftp.chdir(directory)
            else:
                self.connection.cwd(directory)
            return True, "Directory changed successfully"
        except Exception as e:
            return False, f"Error changing directory: {str(e)}"

    def get_current_directory(self) -> Tuple[bool, str, str]:
        """Get current working directory"""
        try:
            if self.use_sftp:
                path = self.sftp.getcwd()
            else:
                path = self.connection.pwd()
            return True, path, "Current directory retrieved successfully"
        except Exception as e:
            return False, "", f"Error getting current directory: {str(e)}"
