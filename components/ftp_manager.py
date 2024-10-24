import streamlit as st
from services.ftp_service import FTPService
from services.catalog_service import CatalogService
from utils.helpers import prepare_catalog_summary
import pandas as pd
import json
import os

def load_saved_connections():
    """Load saved connections from file"""
    try:
        if os.path.exists('saved_connections.json'):
            with open('saved_connections.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_connections(connections):
    """Save connections to file"""
    try:
        with open('saved_connections.json', 'w') as f:
            json.dump(connections, f)
    except Exception as e:
        st.error(f"Error saving connections: {str(e)}")

def render_ftp_manager():
    st.header("FTP/SFTP Data Retrieval")

    # Initialize session state
    if 'saved_ftp_connections' not in st.session_state:
        st.session_state.saved_ftp_connections = load_saved_connections()
    
    if 'scheduled_downloads' not in st.session_state:
        st.session_state.scheduled_downloads = []
    
    if 'ftp_mappings' not in st.session_state:
        st.session_state.ftp_mappings = {}
    
    if 'downloaded_df' not in st.session_state:
        st.session_state.downloaded_df = None
    
    if 'current_connection' not in st.session_state:
        st.session_state.current_connection = None

    # Show saved connections in a project-like view
    if st.session_state.saved_ftp_connections:
        st.subheader("Saved Connections")
        for idx, connection in enumerate(st.session_state.saved_ftp_connections):
            with st.expander(f"📁 {connection.get('name', connection['host'])}"):
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    st.write(f"**Host:** {connection['host']}")
                    st.write(f"**Username:** {connection['username'] or 'Anonymous'}")
                    st.write(f"**Type:** {'SFTP' if connection.get('use_sftp') else 'FTP'}")
                with col2:
                    st.write(f"**Port:** {connection['port']}")
                with col3:
                    if st.button("Connect", key=f"connect_{idx}"):
                        ftp_service = FTPService(
                            connection['host'],
                            connection['username'],
                            connection['password'],
                            connection['port'],
                            use_sftp=connection.get('use_sftp', False)
                        )
                        success, message = ftp_service.connect()
                        if success:
                            st.session_state['ftp_service'] = ftp_service
                            st.session_state.current_connection = connection.get('name', connection['host'])
                            # Load saved mapping for this connection
                            saved_mapping = CatalogService.get_ftp_mapping(st.session_state.current_connection)
                            if saved_mapping:
                                st.session_state.ftp_mappings = saved_mapping
                            st.success("Connected successfully!")
                        else:
                            st.error(message)
                    if st.button("Delete", key=f"delete_{idx}"):
                        st.session_state.saved_ftp_connections.pop(idx)
                        save_connections(st.session_state.saved_ftp_connections)
                        st.rerun()

    # New Connection Form
    with st.form("ftp_config"):
        st.subheader("New Connection")
        
        # Connection type
        connection_type = st.radio("Connection Type", ["FTP", "SFTP"], horizontal=True)
        use_sftp = connection_type == "SFTP"
        
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host")
            username = st.text_input("Username (optional)")
            connection_name = st.text_input("Connection Name (optional)")
        with col2:
            port = st.number_input("Port", value=22 if use_sftp else 21, min_value=1, max_value=65535)
            password = st.text_input("Password (optional)", type="password")

        save_connection = st.checkbox("Save connection")
        connect_button = st.form_submit_button("Connect")
        
        if connect_button:
            if not host:
                st.error("Host is required")
            else:
                ftp_service = FTPService(host, username, password, port, use_sftp=use_sftp)
                success, message = ftp_service.connect()
                
                if success:
                    st.session_state['ftp_service'] = ftp_service
                    conn_name = connection_name or host
                    st.session_state.current_connection = conn_name
                    st.success(message)
                    
                    if save_connection:
                        connection = {
                            'name': conn_name,
                            'host': host,
                            'username': username,
                            'password': password,
                            'port': port,
                            'use_sftp': use_sftp
                        }
                        if connection not in st.session_state.saved_ftp_connections:
                            st.session_state.saved_ftp_connections.append(connection)
                            save_connections(st.session_state.saved_ftp_connections)
                            st.success("Connection saved!")
                else:
                    st.error(message)

    # File Browser and Download
    if 'ftp_service' in st.session_state:
        ftp_service = st.session_state['ftp_service']
        
        st.markdown("---")
        st.subheader("File Browser")
        success, files, message = ftp_service.list_files()
        
        if success:
            if files:
                selected_file = st.selectbox("Select File", files)
                schedule_daily = st.checkbox("Schedule daily download")
                
                if st.button("Download and Preview"):
                    with st.spinner("Downloading file..."):
                        success, df, message = ftp_service.download_file(selected_file)
                        
                        if success:
                            st.session_state.downloaded_df = df
                            
                            if schedule_daily:
                                scheduled_item = {
                                    'connection': {
                                        'host': host,
                                        'username': username,
                                        'password': password,
                                        'port': port,
                                        'use_sftp': use_sftp
                                    },
                                    'file': selected_file,
                                    'last_download': None
                                }
                                if scheduled_item not in st.session_state.scheduled_downloads:
                                    st.session_state.scheduled_downloads.append(scheduled_item)
                                    st.success(f"Scheduled daily download for {selected_file}")
                            
                            # Show raw data preview
                            st.subheader("Raw Data Preview")
                            st.dataframe(df.head().astype(str))
                        else:
                            st.error(message)
                
                # Show mapping interface if data is downloaded
                if st.session_state.downloaded_df is not None:
                    df = st.session_state.downloaded_df
                    
                    # Column mapping interface
                    st.subheader("Map Columns")
                    available_columns = df.columns.tolist()
                    optional_columns = ['article_code', 'barcode', 'name', 'description', 'price', 'stock_quantity', 'purchase_price', 'eco_value']
                    
                    # Load saved mapping button
                    if st.session_state.current_connection:
                        saved_mapping = CatalogService.get_ftp_mapping(st.session_state.current_connection)
                        if saved_mapping and st.button("Load Saved Mapping"):
                            st.session_state.ftp_mappings = saved_mapping
                            st.success("Loaded saved mapping!")
                    
                    # Reset mapping button
                    if st.button("🔄 Reset Mappings"):
                        st.session_state.ftp_mappings = {}
                        st.warning("Column mappings have been reset.")
                    
                    # Create mapping interface
                    col1, col2 = st.columns(2)
                    
                    # Optional columns
                    for idx, optional_col in enumerate(optional_columns):
                        with col1 if idx % 2 == 0 else col2:
                            mapping_key = f"mapping_{optional_col}"
                            current_value = st.session_state.ftp_mappings.get(mapping_key, '')
                            
                            selected = st.selectbox(
                                f"Map {optional_col} to:",
                                options=[''] + available_columns,
                                index=available_columns.index(current_value) + 1 if current_value in available_columns else 0,
                                key=mapping_key
                            )
                            st.session_state.ftp_mappings[mapping_key] = selected
                    
                    # Save mapping button
                    if st.session_state.current_connection and st.button("Save Mapping"):
                        if CatalogService.save_ftp_mapping(st.session_state.current_connection, st.session_state.ftp_mappings):
                            st.success("Mapping saved successfully!")
                        else:
                            st.error("Error saving mapping")
                    
                    # Import button
                    if st.button("🔄 Import Data", use_container_width=True):
                        with st.spinner('Processing and importing data...'):
                            try:
                                # Create reverse mapping
                                reverse_mapping = {
                                    v: k.replace('mapping_', '') 
                                    for k, v in st.session_state.ftp_mappings.items() if v
                                }
                                mapped_df = df.rename(columns=reverse_mapping)
                                
                                success, message = CatalogService.add_catalog_entries(
                                    mapped_df,
                                    source=st.session_state.current_connection
                                )
                                if success:
                                    st.success(message)
                                    # Clear the downloaded data after successful import
                                    st.session_state.downloaded_df = None
                                else:
                                    st.error(message)
                                
                            except Exception as e:
                                st.error(f"❌ Error during import: {str(e)}")
                                st.info("💡 Please try again or contact support if the issue persists")
            else:
                st.info("No files found in the current directory")
        else:
            st.error(message)
            
        if st.button("Disconnect"):
            ftp_service.disconnect()
            del st.session_state['ftp_service']
            st.session_state.current_connection = None
            st.success("Disconnected from server")
