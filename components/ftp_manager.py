import streamlit as st
from services.ftp_service import FTPService
from services.catalog_service import CatalogService
from utils.helpers import prepare_catalog_summary

def render_ftp_manager():
    st.header("FTP Data Retrieval")

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
                else:
                    st.error(message)

    # File Browser and Download
    if 'ftp_service' in st.session_state:
        ftp_service = st.session_state['ftp_service']
        
        st.subheader("FTP File Browser")
        success, files, message = ftp_service.list_files()
        
        if success:
            if files:
                selected_file = st.selectbox("Select File", files)
                
                if st.button("Download and Process"):
                    with st.spinner("Downloading and processing file..."):
                        success, df, message = ftp_service.download_file(selected_file)
                        
                        if success:
                            # Display summary
                            summary = prepare_catalog_summary(df)
                            st.subheader("Catalog Summary")
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Total Records", summary['total_records'])
                            col2.metric("Unique Brands", summary['unique_brands'])
                            col3.metric("Valid Barcodes", summary['valid_barcodes'])
                            
                            # Display preview
                            st.subheader("Data Preview")
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
