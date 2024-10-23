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
        
        # First just read the file to get columns
        if file_type == 'csv':
            df, success, message = process_file(uploaded_file, 'csv')
        else:
            df, success, message = process_file(uploaded_file, 'excel')
        
        if not success:
            st.error(message)
        else:
            # Show mapping interface
            st.subheader("Map Your Columns")
            file_columns = df.columns.tolist()
            mapping = {}
            required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
            
            for required_col in required_columns:
                mapping[required_col] = st.selectbox(
                    f"Map {required_col} to:",
                    options=[''] + file_columns,
                    key=f"map_{required_col}"
                )
            
            # Preview unmapped data with row selection
            st.subheader("Data Preview (Before Mapping)")
            preview_rows = min(10, len(df))
            st.dataframe(df.head(preview_rows))
            
            # Row selection feature
            st.subheader("Row Selection")
            start_row = st.number_input("Start Row", min_value=0, max_value=len(df)-1, value=0)
            end_row = st.number_input("End Row", min_value=start_row+1, max_value=len(df), value=min(start_row+100, len(df)))
            
            # Only proceed if user has mapped all required columns
            if st.button("Apply Mapping") and all(mapping.values()):
                # Create reverse mapping and process
                reverse_mapping = {v: k for k, v in mapping.items()}
                selected_df = df.iloc[start_row:end_row].copy()
                selected_df = selected_df.rename(columns=reverse_mapping)
                
                # Display summary
                summary = prepare_catalog_summary(selected_df)
                st.subheader("Catalog Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Selected Records", summary['total_records'])
                col2.metric("Unique Brands", summary['unique_brands'])
                col3.metric("Valid Barcodes", summary['valid_barcodes'])
                
                # Display preview of mapped data
                st.subheader("Data Preview (After Mapping)")
                st.dataframe(selected_df.head(preview_rows))
                
                # Data validation status
                st.subheader("Data Validation")
                valid_barcodes = selected_df['barcode'].apply(validate_ean13)
                valid_articles = selected_df['article_code'].apply(validate_article_code)
                
                validation_status = pd.DataFrame({
                    'Total Records': [len(selected_df)],
                    'Valid Barcodes': [valid_barcodes.sum()],
                    'Valid Article Codes': [valid_articles.sum()],
                    'Invalid Records': [len(selected_df) - min(valid_barcodes.sum(), valid_articles.sum())]
                })
                st.dataframe(validation_status)
                
                # Import option
                if st.button("Import Selected Rows"):
                    # Filter out invalid records
                    valid_mask = valid_barcodes & valid_articles
                    valid_df = selected_df[valid_mask]
                    
                    if len(valid_df) > 0:
                        success, message = CatalogService.add_catalog_entries(valid_df)
                        if success:
                            st.success(f"Successfully imported {len(valid_df)} records")
                        else:
                            st.error(message)
                    else:
                        st.warning("No valid records to import")
