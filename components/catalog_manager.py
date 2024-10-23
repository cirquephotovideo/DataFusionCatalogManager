import streamlit as st
import pandas as pd
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_file, standardize_catalog_data, get_example_csv_content, get_example_excel_content
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService

def render_catalog_manager():
    st.header("Catalog Management")
    
    # Show example file formats
    example_format = st.radio("View Example Format", ["CSV", "Excel"])
    
    with st.expander("📝 View Example Format"):
        if example_format == "CSV":
            st.code(get_example_csv_content(), language='csv')
            st.download_button(
                "Download Example CSV",
                get_example_csv_content(),
                "example_catalog.csv",
                "text/csv"
            )
        else:
            st.download_button(
                "Download Example Excel",
                get_example_excel_content(),
                "example_catalog.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # File upload
    uploaded_file = st.file_uploader("Upload Catalog File", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        # 1. Show raw data preview first
        st.subheader("Raw Data Preview (First 20 Rows)")
        try:
            if file_type == 'csv':
                preview_df = pd.read_csv(uploaded_file, nrows=20, encoding_errors='replace')
            else:
                preview_df = pd.read_excel(uploaded_file, nrows=20)
            st.dataframe(preview_df)
            
            # 2. Row selection
            header_row = st.number_input("Select Header Row Number", min_value=1, value=1)
            start_row = st.number_input("Start Reading Data from Row", min_value=header_row+1, value=header_row+1)
            
            if st.button("Confirm Row Selection"):
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Re-read file with selected rows
                if file_type == 'csv':
                    df = pd.read_csv(uploaded_file, header=header_row-1, skiprows=range(1, start_row))
                else:
                    df = pd.read_excel(uploaded_file, header=header_row-1, skiprows=range(1, start_row))
                
                # 3. Show column mapping interface
                st.subheader("Map Required Columns")
                available_columns = df.columns.tolist()
                mapping = {}
                required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
                
                for required_col in required_columns:
                    mapping[required_col] = st.selectbox(
                        f"Map {required_col} to:",
                        options=[''] + available_columns,
                        key=f"map_{required_col}"
                    )
                
                # Only proceed if user has mapped all required columns
                if st.button("Apply Mapping") and all(mapping.values()):
                    # Create reverse mapping and process
                    reverse_mapping = {v: k for k, v in mapping.items()}
                    df = df.rename(columns=reverse_mapping)
                    
                    # Display preview of mapped data
                    st.subheader("Data Preview (After Mapping)")
                    preview_rows = min(10, len(df))
                    st.dataframe(df.head(preview_rows))
                    
                    # Data validation
                    st.subheader("Data Validation")
                    valid_barcodes = df['barcode'].apply(validate_ean13)
                    valid_articles = df['article_code'].apply(validate_article_code)
                    
                    validation_status = pd.DataFrame({
                        'Total Records': [len(df)],
                        'Valid Barcodes': [valid_barcodes.sum()],
                        'Valid Article Codes': [valid_articles.sum()],
                        'Invalid Records': [len(df) - min(valid_barcodes.sum(), valid_articles.sum())]
                    })
                    st.dataframe(validation_status)
                    
                    # Display summary
                    summary = prepare_catalog_summary(df)
                    st.subheader("Catalog Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Records", summary['total_records'])
                    col2.metric("Unique Brands", summary['unique_brands'])
                    col3.metric("Valid Barcodes", summary['valid_barcodes'])
                    
                    # Import option
                    if st.button("Import Valid Records"):
                        # Filter out invalid records
                        valid_mask = valid_barcodes & valid_articles
                        valid_df = df[valid_mask]
                        
                        if len(valid_df) > 0:
                            success, message = CatalogService.add_catalog_entries(valid_df)
                            if success:
                                st.success(f"Successfully imported {len(valid_df)} records")
                            else:
                                st.error(message)
                        else:
                            st.warning("No valid records to import")
                            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
