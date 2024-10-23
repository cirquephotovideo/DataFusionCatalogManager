import streamlit as st
from services.ftp_service import FTPService
from services.catalog_service import CatalogService
from utils.helpers import prepare_catalog_summary

def render_ftp_manager():
    st.header("FTP Data Retrieval")

    # Initialize session state for saved connections and scheduled downloads
    if 'saved_ftp_connections' not in st.session_state:
        st.session_state.saved_ftp_connections = []
    
    if 'scheduled_downloads' not in st.session_state:
        st.session_state.scheduled_downloads = []

    # FTP Connection Configuration
    with st.form("ftp_config"):
        st.subheader("FTP Server Configuration")
        col1, col2 = st.columns(2)
        
        with col1:
            host = st.text_input("FTP Host")
            username = st.text_input("Username (optional)")
        
        with col2:
            port = st.number_input("Port", value=21, min_value=1, max_value=65535)
            password = st.text_input("Password (optional)", type="password")

        # Add checkbox for saving connection
        save_connection = st.checkbox("Save connection details")
        
        connect_button = st.form_submit_button("Connect to FTP")
        
        if connect_button:
            if not host:
                st.error("FTP Host is required")
            else:
                ftp_service = FTPService(host, username, password, port)
                success, message = ftp_service.connect()
                
                if success:
                    st.session_state['ftp_service'] = ftp_service
                    st.success(message)
                    
                    # Save connection if checkbox is checked
                    if save_connection:
                        connection = {
                            'host': host,
                            'username': username,
                            'password': password,
                            'port': port
                        }
                        if connection not in st.session_state.saved_ftp_connections:
                            st.session_state.saved_ftp_connections.append(connection)
                            st.success("Connection saved!")
                else:
                    st.error(message)

    # Show saved connections
    if st.session_state.saved_ftp_connections:
        st.subheader("Saved Connections")
        saved_connection = st.selectbox(
            "Select saved connection",
            options=range(len(st.session_state.saved_ftp_connections)),
            format_func=lambda x: f"{st.session_state.saved_ftp_connections[x]['host']}"
        )
        
        if st.button("Use Saved Connection"):
            connection = st.session_state.saved_ftp_connections[saved_connection]
            st.session_state.update({
                'host': connection['host'],
                'username': connection['username'],
                'password': connection['password'],
                'port': connection['port']
            })

    # File Browser and Download
    if 'ftp_service' in st.session_state:
        ftp_service = st.session_state['ftp_service']
        
        st.subheader("FTP File Browser")
        success, files, message = ftp_service.list_files()
        
        if success:
            if files:
                selected_file = st.selectbox("Select File", files)
                
                # Add scheduling option
                schedule_daily = st.checkbox("Schedule daily download")
                
                if st.button("Download and Process"):
                    with st.spinner("Downloading and processing file..."):
                        success, df, message = ftp_service.download_file(selected_file)
                        
                        if success:
                            # Add to scheduled downloads if checkbox is checked
                            if schedule_daily:
                                scheduled_item = {
                                    'connection': {
                                        'host': host,
                                        'username': username,
                                        'password': password,
                                        'port': port
                                    },
                                    'file': selected_file,
                                    'last_download': None
                                }
                                if scheduled_item not in st.session_state.scheduled_downloads:
                                    st.session_state.scheduled_downloads.append(scheduled_item)
                                    st.success(f"Scheduled daily download for {selected_file}")
                            
                            # Show mapping interface
                            st.subheader("Map Your Columns")
                            csv_columns = df.columns.tolist()
                            mapping = {}
                            required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
                            
                            for required_col in required_columns:
                                mapping[required_col] = st.selectbox(
                                    f"Map {required_col} to:",
                                    options=[''] + csv_columns,
                                    key=f"map_{required_col}_ftp"
                                )
                            
                            # Preview unmapped data
                            st.subheader("Data Preview (Before Mapping)")
                            st.dataframe(df.head())
                            
                            # Only proceed if user has mapped all required columns
                            if st.button("Apply Mapping") and all(mapping.values()):
                                # Create reverse mapping and process
                                reverse_mapping = {v: k for k, v in mapping.items()}
                                df = df.rename(columns=reverse_mapping)
                                
                                # Display summary
                                summary = prepare_catalog_summary(df)
                                st.subheader("Catalog Summary")
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Total Records", summary['total_records'])
                                col2.metric("Unique Brands", summary['unique_brands'])
                                col3.metric("Valid Barcodes", summary['valid_barcodes'])
                                
                                # Display preview
                                st.subheader("Data Preview (After Mapping)")
                                st.dataframe(df.head())
                                
                                # Import option
                                if st.button("Import to Database"):
                                    success, message = CatalogService.add_catalog_entries(df)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        else:
                            st.error(message)
            else:
                st.info("No files found in the current directory")
        else:
            st.error(message)
            
        if st.button("Disconnect"):
            ftp_service.disconnect()
            del st.session_state['ftp_service']
            st.success("Disconnected from FTP server")
