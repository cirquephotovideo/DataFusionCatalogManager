import streamlit as st
import pandas as pd
import hashlib
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_file, standardize_catalog_data, get_example_csv_content, get_example_excel_content
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService
from tenacity import retry, stop_after_attempt, wait_exponential

def generate_file_hash(df):
    """Generate a unique hash for the dataframe content"""
    return hashlib.md5(str(df.values.tobytes()).encode()).hexdigest()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def import_catalog_data(df):
    """Import catalog data with retry logic"""
    return CatalogService.add_catalog_entries(df)

def render_catalog_manager():
    st.header("Catalog Management")
    
    # Initialize session state for mappings if not exists
    if 'mappings' not in st.session_state:
        st.session_state.mappings = {}
    if 'current_file_hash' not in st.session_state:
        st.session_state.current_file_hash = None
    
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
        try:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            # 1. Show raw data preview first
            st.subheader("Raw Data Preview")
            try:
                if file_type == 'csv':
                    preview_df = pd.read_csv(uploaded_file, nrows=20, encoding_errors='replace')
                else:
                    preview_df = pd.read_excel(uploaded_file, nrows=20)
                st.dataframe(preview_df)
                
                # Generate unique hash for the file content
                file_hash = generate_file_hash(preview_df)
                
                # Update current file hash in session state
                if st.session_state.current_file_hash != file_hash:
                    st.session_state.current_file_hash = file_hash
                    # Clear mappings when a new file is uploaded
                    st.session_state.mappings = {}
                
                # 2. Row selection
                header_row = st.number_input("Select Header Row Number", min_value=1, value=1)
                start_row = st.number_input("Start Reading Data from Row", min_value=header_row+1, value=header_row+1)
                
                # Read file with selected rows
                uploaded_file.seek(0)
                with st.spinner("Processing file..."):
                    if file_type == 'csv':
                        df = pd.read_csv(uploaded_file, header=header_row-1, skiprows=list(range(1, start_row)))
                    else:
                        df = pd.read_excel(uploaded_file, header=header_row-1, skiprows=list(range(1, start_row)))
                
                # 3. Column mapping interface
                st.subheader("Map Required Columns")
                available_columns = df.columns.tolist()
                required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
                
                # Reset mapping button with confirmation
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🔄 Reset", help="Clear all column mappings"):
                        st.session_state.mappings = {}
                        st.warning("Column mappings have been reset.")
                
                with col2:
                    st.info("💡 Your column mapping will be preserved until you reset it or upload a different file.")
                
                # Create mapping interface with persistent state
                mapping_cols = st.columns(2)
                for idx, required_col in enumerate(required_columns):
                    with mapping_cols[idx % 2]:
                        mapping_key = f"mapping_{required_col}_{file_hash}"
                        current_mapping = st.session_state.mappings.get(mapping_key, '')
                        
                        # Create selectbox with persistent state
                        try:
                            current_index = available_columns.index(current_mapping) + 1 if current_mapping in available_columns else 0
                        except ValueError:
                            current_index = 0
                        
                        selected_column = st.selectbox(
                            f"Map {required_col} to:",
                            options=[''] + available_columns,
                            key=mapping_key,
                            index=current_index,
                            help=f"Select the column that contains {required_col} data"
                        )
                        
                        # Update mapping state
                        if selected_column:
                            st.session_state.mappings[mapping_key] = selected_column
                            st.success(f"✓ {required_col}")
                            with st.expander(f"Preview {required_col}"):
                                st.dataframe(df[selected_column].head())
                        else:
                            if mapping_key in st.session_state.mappings:
                                del st.session_state.mappings[mapping_key]
                            st.error(f"✗ {required_col} not mapped")
                
                # Show import section when all fields are mapped
                st.markdown("---")
                all_mapped = all(f"mapping_{col}_{file_hash}" in st.session_state.mappings 
                               for col in required_columns)
                
                if all_mapped:
                    st.success("✅ All required columns are mapped!")
                    
                    # Add clear import button with visual emphasis
                    import_col1, import_col2, import_col3 = st.columns([1,2,1])
                    with import_col2:
                        if st.button("🔄 Import Data", key=f"import_{file_hash}", use_container_width=True):
                            try:
                                # Add loading spinner
                                with st.spinner('Importing data...'):
                                    # Create reverse mapping
                                    mappings = {col: st.session_state.mappings[f"mapping_{col}_{file_hash}"] 
                                              for col in required_columns}
                                    reverse_mapping = {v: k for k, v in mappings.items()}
                                    df = df.rename(columns=reverse_mapping)
                                    
                                    # Validate data
                                    valid_barcodes = df['barcode'].apply(validate_ean13)
                                    valid_articles = df['article_code'].apply(validate_article_code)
                                    
                                    # Show validation results
                                    validation_df = pd.DataFrame({
                                        'Total Records': [len(df)],
                                        'Valid Barcodes': [valid_barcodes.sum()],
                                        'Valid Article Codes': [valid_articles.sum()],
                                        'Invalid Records': [len(df) - min(valid_barcodes.sum(), valid_articles.sum())]
                                    })
                                    st.dataframe(validation_df)
                                    
                                    # Filter valid records
                                    valid_mask = valid_barcodes & valid_articles
                                    valid_df = df[valid_mask].copy()
                                    
                                    if len(valid_df) > 0:
                                        success, message = import_catalog_data(valid_df)
                                        if success:
                                            st.success(f"✅ Successfully imported {len(valid_df)} records")
                                        else:
                                            st.error(f"❌ Import failed: {message}")
                                    else:
                                        st.warning("⚠️ No valid records to import")
                            except Exception as e:
                                st.error(f"❌ Error during import: {str(e)}")
                                st.info("💡 Please try again or contact support if the issue persists")
                else:
                    unmapped = [col for col in required_columns 
                               if f"mapping_{col}_{file_hash}" not in st.session_state.mappings]
                    st.warning(f"⚠️ Please map the following columns to proceed: {', '.join(unmapped)}")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.info("💡 Please make sure your file is in the correct format and try again")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Please try uploading the file again")
