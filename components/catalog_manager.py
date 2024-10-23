import streamlit as st
import pandas as pd
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_csv, standardize_catalog_data
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService

def render_catalog_manager():
    st.header("Catalog Management")
    
    # File upload
    uploaded_file = st.file_uploader("Upload Catalog CSV", type=['csv'])
    
    if uploaded_file is not None:
        df = process_csv(uploaded_file)
        df = standardize_catalog_data(df)
        
        # Display summary
        summary = prepare_catalog_summary(df)
        st.subheader("Catalog Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Records", summary['total_records'])
        col2.metric("Unique Brands", summary['unique_brands'])
        col3.metric("Valid Barcodes", summary['valid_barcodes'])
        
        # Display data preview
        st.subheader("Data Preview")
        st.dataframe(df.head())
        
        # Validation and import
        if st.button("Validate and Import"):
            with st.spinner("Processing..."):
                # Validate data
                valid_barcodes = df['barcode'].apply(validate_ean13)
                valid_articles = df['article_code'].apply(validate_article_code)
                
                if not valid_barcodes.all():
                    st.error("Invalid barcodes detected")
                elif not valid_articles.all():
                    st.error("Invalid article codes detected")
                else:
                    # Import to database
                    success, message = CatalogService.add_catalog_entries(df)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
