import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import boto3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import shutil
import sqlite3

class CloudStorageService:
    def __init__(self):
        """Initialize cloud storage service"""
        self.s3_client = None
        self.drive_service = None
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load cloud storage configuration"""
        try:
            with open('cloud_storage_config.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'google_drive': {
                    'enabled': False,
                    'credentials_file': 'credentials.json',
                    'token_file': 'token.json',
                    'backup_folder_id': ''
                },
                'aws_s3': {
                    'enabled': False,
                    'access_key_id': '',
                    'secret_access_key': '',
                    'region': '',
                    'bucket': '',
                    'backup_prefix': 'backups/'
                }
            }

    def save_config(self, config: Dict) -> bool:
        """Save cloud storage configuration"""
        try:
            with open('cloud_storage_config.json', 'w') as f:
                json.dump(config, f)
            return True
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
            return False

    def init_google_drive(self) -> Tuple[bool, str]:
        """Initialize Google Drive service"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            creds = None

            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config['google_drive']['credentials_file'], SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            self.drive_service = build('drive', 'v3', credentials=creds)
            return True, "Google Drive initialized successfully"
        except Exception as e:
            return False, f"Error initializing Google Drive: {str(e)}"

    def init_s3(self) -> Tuple[bool, str]:
        """Initialize AWS S3 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config['aws_s3']['access_key_id'],
                aws_secret_access_key=self.config['aws_s3']['secret_access_key'],
                region_name=self.config['aws_s3']['region']
            )
            return True, "AWS S3 initialized successfully"
        except Exception as e:
            return False, f"Error initializing AWS S3: {str(e)}"

    def backup_database(self, destination: str = 'both') -> Tuple[bool, str]:
        """Backup SQLite database to cloud storage"""
        try:
            # Create backup directory if it doesn't exist
            os.makedirs('backups', exist_ok=True)

            # Create backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backups/catalog_backup_{timestamp}.db"

            # Create backup
            conn = sqlite3.connect('catalog.db')
            backup_conn = sqlite3.connect(backup_file)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()

            success = True
            messages = []

            # Upload to Google Drive
            if destination in ['google_drive', 'both'] and self.config['google_drive']['enabled']:
                drive_success, drive_message = self._upload_to_drive(backup_file, timestamp)
                success = success and drive_success
                messages.append(f"Google Drive: {drive_message}")

            # Upload to S3
            if destination in ['s3', 'both'] and self.config['aws_s3']['enabled']:
                s3_success, s3_message = self._upload_to_s3(backup_file, timestamp)
                success = success and s3_success
                messages.append(f"AWS S3: {s3_message}")

            # Clean up local backup
            os.remove(backup_file)

            return success, "\n".join(messages)
        except Exception as e:
            return False, f"Error creating backup: {str(e)}"

    def _upload_to_drive(self, file_path: str, timestamp: str) -> Tuple[bool, str]:
        """Upload backup to Google Drive"""
        try:
            if not self.drive_service:
                success, message = self.init_google_drive()
                if not success:
                    return False, message

            file_metadata = {
                'name': f"catalog_backup_{timestamp}.db",
                'parents': [self.config['google_drive']['backup_folder_id']]
            }
            media = MediaFileUpload(file_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return True, f"Backup uploaded to Google Drive with ID: {file.get('id')}"
        except Exception as e:
            return False, f"Error uploading to Google Drive: {str(e)}"

    def _upload_to_s3(self, file_path: str, timestamp: str) -> Tuple[bool, str]:
        """Upload backup to AWS S3"""
        try:
            if not self.s3_client:
                success, message = self.init_s3()
                if not success:
                    return False, message

            key = f"{self.config['aws_s3']['backup_prefix']}catalog_backup_{timestamp}.db"
            self.s3_client.upload_file(
                file_path,
                self.config['aws_s3']['bucket'],
                key
            )

            return True, f"Backup uploaded to S3: s3://{self.config['aws_s3']['bucket']}/{key}"
        except Exception as e:
            return False, f"Error uploading to S3: {str(e)}"

    def restore_database(self, backup_id: str, source: str = 'google_drive') -> Tuple[bool, str]:
        """Restore database from cloud storage backup"""
        try:
            # Create temporary directory for restoration
            os.makedirs('restore_temp', exist_ok=True)
            temp_file = 'restore_temp/temp_restore.db'

            success = False
            message = ""

            # Download from selected source
            if source == 'google_drive':
                success, message = self._download_from_drive(backup_id, temp_file)
            elif source == 's3':
                success, message = self._download_from_s3(backup_id, temp_file)

            if not success:
                return False, message

            # Verify backup file
            try:
                verify_conn = sqlite3.connect(temp_file)
                verify_conn.close()
            except:
                return False, "Invalid backup file"

            # Restore database
            try:
                # Stop any active connections
                # TODO: Implement connection pool management

                # Create backup of current database
                shutil.copy('catalog.db', 'catalog.db.bak')

                # Restore from backup
                restore_conn = sqlite3.connect(temp_file)
                current_conn = sqlite3.connect('catalog.db')
                restore_conn.backup(current_conn)
                current_conn.close()
                restore_conn.close()

                # Clean up
                os.remove(temp_file)
                return True, "Database restored successfully"

            except Exception as e:
                # Restore from backup if restoration fails
                if os.path.exists('catalog.db.bak'):
                    shutil.copy('catalog.db.bak', 'catalog.db')
                return False, f"Error restoring database: {str(e)}"

        except Exception as e:
            return False, f"Error in restoration process: {str(e)}"
        finally:
            # Clean up
            if os.path.exists('restore_temp'):
                shutil.rmtree('restore_temp')
            if os.path.exists('catalog.db.bak'):
                os.remove('catalog.db.bak')

    def _download_from_drive(self, file_id: str, destination: str) -> Tuple[bool, str]:
        """Download backup from Google Drive"""
        try:
            if not self.drive_service:
                success, message = self.init_google_drive()
                if not success:
                    return False, message

            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            fh.seek(0)
            with open(destination, 'wb') as f:
                f.write(fh.read())

            return True, "Backup downloaded from Google Drive"
        except Exception as e:
            return False, f"Error downloading from Google Drive: {str(e)}"

    def _download_from_s3(self, key: str, destination: str) -> Tuple[bool, str]:
        """Download backup from AWS S3"""
        try:
            if not self.s3_client:
                success, message = self.init_s3()
                if not success:
                    return False, message

            self.s3_client.download_file(
                self.config['aws_s3']['bucket'],
                key,
                destination
            )

            return True, "Backup downloaded from S3"
        except Exception as e:
            return False, f"Error downloading from S3: {str(e)}"

    def list_backups(self, source: str = 'both') -> Dict[str, List[Dict]]:
        """List available backups from cloud storage"""
        backups = {
            'google_drive': [],
            's3': []
        }

        if source in ['google_drive', 'both'] and self.config['google_drive']['enabled']:
            try:
                if not self.drive_service:
                    self.init_google_drive()

                results = self.drive_service.files().list(
                    q=f"'{self.config['google_drive']['backup_folder_id']}' in parents",
                    fields="files(id, name, createdTime, size)"
                ).execute()

                backups['google_drive'] = [{
                    'id': f['id'],
                    'name': f['name'],
                    'created': f['createdTime'],
                    'size': f['size']
                } for f in results.get('files', [])]

            except Exception as e:
                logging.error(f"Error listing Google Drive backups: {str(e)}")

        if source in ['s3', 'both'] and self.config['aws_s3']['enabled']:
            try:
                if not self.s3_client:
                    self.init_s3()

                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(
                    Bucket=self.config['aws_s3']['bucket'],
                    Prefix=self.config['aws_s3']['backup_prefix']
                )

                for page in pages:
                    for obj in page.get('Contents', []):
                        backups['s3'].append({
                            'id': obj['Key'],
                            'name': os.path.basename(obj['Key']),
                            'created': obj['LastModified'],
                            'size': obj['Size']
                        })

            except Exception as e:
                logging.error(f"Error listing S3 backups: {str(e)}")

        return backups
