import streamlit as st
from components.catalog_manager import render_catalog_manager
from components.manufacturer_manager import render_manufacturer_manager
from components.matching_engine import render_matching_engine
from components.ftp_manager import render_ftp_manager

st.set_page_config(
    page_title="Catalog Management System",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("Catalog Management System")
    
    # Navigation
    menu = ["Catalog Management", "Manufacturer Management", "Product Matching", "FTP Data Retrieval"]
    choice = st.sidebar.selectbox("Navigate", menu)
    
    if choice == "Catalog Management":
        render_catalog_manager()
    elif choice == "Manufacturer Management":
        render_manufacturer_manager()
    elif choice == "FTP Data Retrieval":
        render_ftp_manager()
    else:
        render_matching_engine()

if __name__ == "__main__":
    main()
