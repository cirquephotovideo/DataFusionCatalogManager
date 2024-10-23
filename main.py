import streamlit as st
from components.catalog_manager import render_catalog_manager
from components.manufacturer_manager import render_manufacturer_manager
from components.matching_engine import render_matching_engine

st.set_page_config(
    page_title="Catalog Management System",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("Catalog Management System")
    
    # Navigation
    menu = ["Catalog Management", "Manufacturer Management", "Product Matching"]
    choice = st.sidebar.selectbox("Navigate", menu)
    
    if choice == "Catalog Management":
        render_catalog_manager()
    elif choice == "Manufacturer Management":
        render_manufacturer_manager()
    else:
        render_matching_engine()

if __name__ == "__main__":
    main()
