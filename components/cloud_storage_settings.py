import streamlit as st
from services.cloud_storage_service import CloudStorageService
import json
from datetime import datetime

def render_cloud_storage_settings():
    """Render cloud storage configuration and backup management"""
    st.title("Cloud Storage & Backup")

    # Initialize service
    if 'cloud_storage_service' not in st.session_state:
        st.session_state.cloud_storage_service = CloudStorageService()

    # Create tabs for different storage providers
    google_tab, aws_tab, backups_tab = st.tabs([
        "Google Drive", "AWS S3", "Backups"
    ])

    with google_tab:
        render_google_drive_settings()

    with aws_tab:
        render_aws_settings()

    with backups_tab:
        render_backup_management()

def render_google_drive_settings():
    """Render Google Drive configuration"""
    st.subheader("Google Drive Settings")

    # Load current settings
    config = st.session_state.cloud_storage_service.config['google_drive']

    # Enable/Disable Google Drive
    enabled = st.toggle("Enable Google Drive", value=config.get('enabled', False))

    if enabled:
        # Credentials file
        st.file_uploader(
            "Upload credentials.json",
            type=['json'],
            key="google_credentials",
            help="Download from Google Cloud Console"
        )

        # Backup folder ID
        folder_id = st.text_input(
            "Backup Folder ID",
            value=config.get('backup_folder_id', ''),
            help="Google Drive folder ID for storing backups"
        )

        # Test connection
        if st.button("Test Google Drive Connection"):
            success, message = st.session_state.cloud_storage_service.init_google_drive()
            if success:
                st.success(message)
            else:
                st.error(message)

        # Save settings
        if st.button("Save Google Drive Settings"):
            new_config = st.session_state.cloud_storage_service.config
            new_config['google_drive'] = {
                'enabled': enabled,
                'credentials_file': 'credentials.json',
                'token_file': 'token.json',
                'backup_folder_id': folder_id
            }
            
            if st.session_state.cloud_storage_service.save_config(new_config):
                st.success("Settings saved successfully!")
            else:
                st.error("Error saving settings")

def render_aws_settings():
    """Render AWS S3 configuration"""
    st.subheader("AWS S3 Settings")

    # Load current settings
    config = st.session_state.cloud_storage_service.config['aws_s3']

    # Enable/Disable AWS S3
    enabled = st.toggle("Enable AWS S3", value=config.get('enabled', False))

    if enabled:
        # AWS credentials
        col1, col2 = st.columns(2)
        with col1:
            access_key = st.text_input(
                "Access Key ID",
                value=config.get('access_key_id', ''),
                type="password"
            )
        with col2:
            secret_key = st.text_input(
                "Secret Access Key",
                value=config.get('secret_access_key', ''),
                type="password"
            )

        # S3 settings
        col1, col2 = st.columns(2)
        with col1:
            region = st.text_input(
                "Region",
                value=config.get('region', '')
            )
        with col2:
            bucket = st.text_input(
                "Bucket Name",
                value=config.get('bucket', '')
            )

        backup_prefix = st.text_input(
            "Backup Prefix",
            value=config.get('backup_prefix', 'backups/'),
            help="Prefix for backup files in the bucket"
        )

        # Test connection
        if st.button("Test S3 Connection"):
            success, message = st.session_state.cloud_storage_service.init_s3()
            if success:
                st.success(message)
            else:
                st.error(message)

        # Save settings
        if st.button("Save S3 Settings"):
            new_config = st.session_state.cloud_storage_service.config
            new_config['aws_s3'] = {
                'enabled': enabled,
                'access_key_id': access_key,
                'secret_access_key': secret_key,
                'region': region,
                'bucket': bucket,
                'backup_prefix': backup_prefix
            }
            
            if st.session_state.cloud_storage_service.save_config(new_config):
                st.success("Settings saved successfully!")
            else:
                st.error("Error saving settings")

def render_backup_management():
    """Render backup management interface"""
    st.subheader("Backup Management")

    # Create backup
    st.write("Create New Backup")
    col1, col2 = st.columns(2)
    
    with col1:
        backup_destination = st.selectbox(
            "Backup Destination",
            options=['both', 'google_drive', 's3'],
            format_func=lambda x: {
                'both': 'Both Services',
                'google_drive': 'Google Drive Only',
                's3': 'AWS S3 Only'
            }[x]
        )
    
    with col2:
        if st.button("Create Backup"):
            with st.spinner("Creating backup..."):
                success, message = st.session_state.cloud_storage_service.backup_database(backup_destination)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    # List backups
    st.write("Available Backups")
    backups = st.session_state.cloud_storage_service.list_backups()

    # Google Drive backups
    if backups['google_drive']:
        st.write("Google Drive Backups")
        for backup in backups['google_drive']:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(backup['name'])
            with col2:
                st.write(datetime.fromisoformat(backup['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S'))
            with col3:
                if st.button("Restore", key=f"drive_{backup['id']}"):
                    with st.spinner("Restoring backup..."):
                        success, message = st.session_state.cloud_storage_service.restore_database(
                            backup['id'],
                            'google_drive'
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)

    # S3 backups
    if backups['s3']:
        st.write("AWS S3 Backups")
        for backup in backups['s3']:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(backup['name'])
            with col2:
                st.write(backup['created'].strftime('%Y-%m-%d %H:%M:%S'))
            with col3:
                if st.button("Restore", key=f"s3_{backup['id']}"):
                    with st.spinner("Restoring backup..."):
                        success, message = st.session_state.cloud_storage_service.restore_database(
                            backup['id'],
                            's3'
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
