import streamlit as st
import pandas as pd
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_csv, standardize_catalog_data, get_example_csv_content
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService

def render_catalog_manager():
    st.header("Catalog Management")
    
    # Show example CSV format
    with st.expander("📝 View Example CSV Format"):
        st.code(get_example_csv_content(), language='csv')
        st.download_button(
            "Download Example CSV",
            get_example_csv_content(),
            "example_catalog.csv",
            "text/csv"
        )
    
    # File upload
    uploaded_file = st.file_uploader("Upload Catalog CSV", type=['csv'])
    
    if uploaded_file is not None:
        # Process and validate CSV
        df, success, message = process_csv(uploaded_file)
        
        if not success:
            st.error(message)
        else:
            df = standardize_catalog_data(df)
            
            # Display summary
            summary = prepare_catalog_summary(df)
            st.subheader("Catalog Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Records", summary['total_records'])
            col2.metric("Unique Brands", summary['unique_brands'])
            col3.metric("Valid Barcodes", summary['valid_barcodes'])
            
            # Display missing values if any
            missing_values = summary.get('missing_values', {})
            if any(missing_values.values()):
                st.warning("Missing Values Found:")
                for col, count in missing_values.items():
                    if count > 0:
                        st.write(f"• {col}: {count} missing values")
            
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
                        invalid_barcodes = df[~valid_barcodes]['barcode'].tolist()
                        st.error(f"Invalid barcodes detected: {', '.join(map(str, invalid_barcodes[:5]))}")
                    elif not valid_articles.all():
                        invalid_articles = df[~valid_articles]['article_code'].tolist()
                        st.error(f"Invalid article codes detected: {', '.join(map(str, invalid_articles[:5]))}")
                    else:
                        # Import to database
                        success, message = CatalogService.add_catalog_entries(df)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
