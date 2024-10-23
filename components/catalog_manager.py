import streamlit as st
import pandas as pd
import hashlib
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_file, standardize_catalog_data, get_example_csv_content, get_example_excel_content
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService

def generate_file_hash(df):
    """Generate a unique hash for the dataframe content"""
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()

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
            
            # Generate unique hash for the file content
            file_hash = generate_file_hash(preview_df)
            
            # 2. Row selection
            header_row = st.number_input("Select Header Row Number", min_value=1, value=1)
            start_row = st.number_input("Start Reading Data from Row", min_value=header_row+1, value=header_row+1)
            
            if st.button("Confirm Row Selection"):
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Re-read file with selected rows
                if file_type == 'csv':
                    df = pd.read_csv(uploaded_file, header=header_row-1, skiprows=list(range(1, start_row)))
                else:
                    df = pd.read_excel(uploaded_file, header=header_row-1, skiprows=list(range(1, start_row)))
                
                # Initialize mapping in session state if not exists
                mapping_key = f"mapping_{file_hash}"
                if mapping_key not in st.session_state:
                    st.session_state[mapping_key] = {}
                
                # 3. Show column mapping interface
                st.subheader("Map Required Columns")
                available_columns = df.columns.tolist()
                required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
                
                # Reset mapping button with confirmation
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Reset Mapping"):
                        if st.session_state[mapping_key]:
                            st.session_state[mapping_key] = {}
                            st.warning("Column mapping has been reset.")
                
                with col2:
                    st.info("💡 Your column mapping will be preserved until you reset it or upload a different file.")
                
                # Create mapping interface with column layout
                col1, col2 = st.columns(2)
                unmapped_columns = []
                
                for idx, required_col in enumerate(required_columns):
                    with col1 if idx % 2 == 0 else col2:
                        # Get current mapping value from session state
                        current_value = st.session_state[mapping_key].get(required_col, '')
                        
                        # Create selectbox with unique key
                        selected_col = st.selectbox(
                            f"Map {required_col} to:",
                            options=[''] + available_columns,
                            index=0 if not current_value else available_columns.index(current_value) + 1,
                            key=f"map_{required_col}_{file_hash}"
                        )
                        
                        # Update mapping in session state
                        if selected_col:
                            st.session_state[mapping_key][required_col] = selected_col
                            st.success(f"✓ {required_col} mapped to {selected_col}")
                            
                            # Show data preview in expander
                            with st.expander(f"Preview {required_col} data"):
                                st.dataframe(df[selected_col].head(3))
                        else:
                            unmapped_columns.append(required_col)
                            if required_col in st.session_state[mapping_key]:
                                del st.session_state[mapping_key][required_col]
                            st.error(f"✗ {required_col} not mapped")
                
                # Show import section immediately after mapping
                st.markdown("---")
                if unmapped_columns:
                    st.warning(f"Please map the following columns to proceed: {', '.join(unmapped_columns)}")
                else:
                    st.success("✅ All required columns are mapped!")
                    if st.button("Process and Import Data", key=f"import_button_{file_hash}"):
                        # Create reverse mapping and process
                        mapping = st.session_state[mapping_key]
                        reverse_mapping = {v: k for k, v in mapping.items()}
                        df = df.rename(columns=reverse_mapping)
                        
                        # Data validation
                        valid_barcodes = df['barcode'].apply(validate_ean13)
                        valid_articles = df['article_code'].apply(validate_article_code)
                        
                        # Show validation summary
                        st.subheader("Data Validation")
                        validation_df = pd.DataFrame({
                            'Total Records': [len(df)],
                            'Valid Barcodes': [valid_barcodes.sum()],
                            'Valid Article Codes': [valid_articles.sum()],
                            'Invalid Records': [len(df) - min(valid_barcodes.sum(), valid_articles.sum())]
                        })
                        st.dataframe(validation_df)
                        
                        # Filter and import valid records
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
