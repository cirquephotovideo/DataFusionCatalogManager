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
    
    # Initialize mapping state at the top level
    if 'mapping_state' not in st.session_state:
        st.session_state.mapping_state = {
            'article_code': '',
            'barcode': '',
            'brand': '',
            'description': '',
            'price': ''
        }
    
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
            
            # 1. Show raw data preview
            st.subheader("Raw Data Preview")
            if file_type == 'csv':
                preview_df = pd.read_csv(uploaded_file, nrows=20, encoding_errors='replace')
            else:
                preview_df = pd.read_excel(uploaded_file, nrows=20)
            st.dataframe(preview_df)
            
            # Generate hash for current file
            current_file_hash = generate_file_hash(preview_df)
            
            # Initialize/reset mapping state for new file
            if 'current_file_hash' not in st.session_state or st.session_state.current_file_hash != current_file_hash:
                st.session_state.current_file_hash = current_file_hash
                st.session_state.mapping_state = {
                    'article_code': '',
                    'barcode': '',
                    'brand': '',
                    'description': '',
                    'price': ''
                }
            
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
            
            # 3. Column mapping section
            st.subheader("Map Required Columns")
            available_columns = df.columns.tolist()
            required_columns = ['article_code', 'barcode', 'brand', 'description', 'price']
            
            # Reset mapping button
            if st.button("🔄 Reset Mappings", help="Clear all column mappings"):
                st.session_state.mapping_state = {col: '' for col in required_columns}
                st.warning("Column mappings have been reset.")
            
            st.info("💡 Your column mapping will be preserved until you reset it or upload a different file.")
            
            # Create mapping interface with two columns
            col1, col2 = st.columns(2)
            for idx, required_col in enumerate(required_columns):
                with col1 if idx % 2 == 0 else col2:
                    # Use simple key without file hash
                    selected = st.selectbox(
                        f"Map {required_col} to:",
                        options=[''] + available_columns,
                        index=available_columns.index(st.session_state.mapping_state[required_col]) + 1 
                              if st.session_state.mapping_state[required_col] in available_columns 
                              else 0,
                        key=f'select_{required_col}'
                    )
                    
                    # Update mapping state immediately
                    st.session_state.mapping_state[required_col] = selected
                    
                    # Show preview if mapped
                    if selected:
                        st.success(f"✓ {required_col} mapped to {selected}")
                        with st.expander(f"Preview {required_col}"):
                            st.dataframe(df[selected].head())
                    else:
                        st.error(f"✗ {required_col} not mapped")
            
            # Show import section when all fields are mapped
            st.markdown("---")
            all_mapped = all(st.session_state.mapping_state.values())
            
            if all_mapped:
                st.success("✅ All required columns are mapped!")
                
                # Centered import button
                col1, col2, col3 = st.columns([1,2,1])
                with col2:
                    if st.button("🔄 Import Data", use_container_width=True):
                        with st.spinner('Processing and importing data...'):
                            try:
                                # Use mapping state directly
                                reverse_mapping = {v: k for k, v in st.session_state.mapping_state.items() if v}
                                mapped_df = df.rename(columns=reverse_mapping)
                                
                                # Validate data
                                valid_barcodes = mapped_df['barcode'].apply(validate_ean13)
                                valid_articles = mapped_df['article_code'].apply(validate_article_code)
                                
                                # Show validation summary
                                st.subheader("Data Validation")
                                validation_df = pd.DataFrame({
                                    'Total Records': [len(mapped_df)],
                                    'Valid Barcodes': [valid_barcodes.sum()],
                                    'Valid Article Codes': [valid_articles.sum()],
                                    'Invalid Records': [len(mapped_df) - min(valid_barcodes.sum(), valid_articles.sum())]
                                })
                                st.dataframe(validation_df)
                                
                                # Process valid records
                                valid_mask = valid_barcodes & valid_articles
                                valid_df = mapped_df[valid_mask].copy()
                                
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
                unmapped = [col for col, val in st.session_state.mapping_state.items() if not val]
                st.warning(f"⚠️ Please map the following columns to proceed: {', '.join(unmapped)}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Please check your file format and try again")
