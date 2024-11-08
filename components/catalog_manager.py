import streamlit as st
import pandas as pd
from utils.validators import validate_ean13, validate_article_code, validate_required_fields
from utils.processors import process_file, standardize_catalog_data, get_example_csv_content, get_example_excel_content
from utils.helpers import prepare_catalog_summary
from services.catalog_service import CatalogService
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

class CatalogManager:
    def __init__(self, db):
        self.db = db
        if 'mappings' not in st.session_state:
            st.session_state.mappings = {}
        if 'import_df' not in st.session_state:
            st.session_state.import_df = None

    def format_datetime(self, dt):
        """Format datetime for display"""
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M")
        return "-"

    def render(self):
        st.header("Catalog Management")
        
        # Add tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Search Products", "Add Product", "Import Products"])
        
        with tab1:
            self.render_search_tab()
        
        with tab2:
            self.render_add_product_tab()
        
        with tab3:
            self.render_import_tab()

    def render_search_tab(self):
        # Search section
        st.subheader("Product Search")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_query = st.text_input("Search products", 
                                       placeholder="Enter reference, name, or description")
        with search_col2:
            st.write("")
            st.write("")
            search_button = st.button("🔍 Search", use_container_width=True)
        
        # Display search results
        if search_query or search_button:
            products = CatalogService.search_products(search_query)
            if products:
                for product in products:
                    with st.expander(f"{product.reference or product.article_code} - {product.name or 'No name'}"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.write("**Description:**")
                            st.write(product.description or "No description")
                            st.write("**Barcode:**", product.barcode or "-")
                            st.write("**Article Code:**", product.article_code)
                        with col2:
                            st.write("**Stock:**", product.stock_quantity or 0)
                            st.write("**PA HT:**", f"€{product.purchase_price:.2f}" if product.purchase_price else "-")
                            st.write("**Eco:**", f"€{product.eco_value:.2f}" if product.eco_value else "-")
                            st.write("**Price:**", f"€{product.price:.2f}" if product.price else "-")
                        
                        # Import information
                        st.markdown("---")
                        info_col1, info_col2, info_col3 = st.columns(3)
                        with info_col1:
                            st.write("**Created:**", self.format_datetime(product.created_at))
                        with info_col2:
                            st.write("**Last Updated:**", self.format_datetime(product.updated_at))
                        with info_col3:
                            st.write("**Last Import:**", self.format_datetime(product.last_import))
                            if product.import_source:
                                st.write("**Source:**", product.import_source)
                        
                        if product.supplier_prices:
                            st.markdown("---")
                            st.write("**Supplier Prices:**")
                            price_data = []
                            for sp in product.supplier_prices:
                                price_data.append({
                                    "Supplier": sp.supplier.code,
                                    "Stock": sp.stock,
                                    "Price": f"€{sp.price:.2f}",
                                    "Eco": f"€{product.eco_value:.2f}" if product.eco_value else "-"
                                })
                            st.table(pd.DataFrame(price_data))
            else:
                st.info("No products found matching your search criteria")

    def render_add_product_tab(self):
        # Manual product creation form
        st.subheader("Add New Product")
        with st.form("add_product_form"):
            col1, col2 = st.columns(2)
            with col1:
                article_code = st.text_input("Article Code*")
                name = st.text_input("Product Name")
                description = st.text_area("Description")
                barcode = st.text_input("Barcode")
            with col2:
                stock = st.number_input("Stock Quantity", min_value=0, value=0)
                price = st.number_input("Price", min_value=0.0, value=0.0)
                purchase_price = st.number_input("Purchase Price (PA HT)", min_value=0.0, value=0.0)
                eco_value = st.number_input("Eco Value", min_value=0.0, value=0.0)
            
            submit_button = st.form_submit_button("Add Product")
            
            if submit_button:
                if not article_code:
                    st.error("Article Code is required")
                else:
                    success = CatalogService.add_single_product({
                        'article_code': article_code,
                        'name': name,
                        'description': description,
                        'barcode': barcode,
                        'stock_quantity': stock,
                        'price': price,
                        'purchase_price': purchase_price,
                        'eco_value': eco_value
                    })
                    if success:
                        st.success("Product added successfully!")
                    else:
                        st.error("Error adding product")

    def render_import_tab(self):
        # File Import Section
        st.subheader("Import Products from File")
        
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
                
                # Show raw data preview
                st.subheader("Raw Data Preview")
                if file_type == 'csv':
                    preview_df = pd.read_csv(uploaded_file, nrows=20, thousands=None)
                else:
                    preview_df = pd.read_excel(uploaded_file, nrows=20, thousands=None)
                
                st.dataframe(preview_df.astype(str))
                
                # Row selection
                header_row = st.number_input("Select Header Row Number", min_value=1, value=1)
                start_row = st.number_input("Start Reading Data from Row", min_value=header_row+1, value=header_row+1)
                
                # Read the full file with selected rows
                uploaded_file.seek(0)  # Reset file pointer
                if file_type == 'csv':
                    st.session_state.import_df = pd.read_csv(uploaded_file, header=header_row-1, skiprows=range(1, start_row-1))
                else:
                    st.session_state.import_df = pd.read_excel(uploaded_file, header=header_row-1, skiprows=range(1, start_row-1))
                
                # Column mapping interface
                st.subheader("Map Columns")
                available_columns = preview_df.columns.tolist()
                optional_columns = ['article_code', 'barcode', 'name', 'description', 'price', 'stock_quantity', 'purchase_price', 'eco_value']
                
                # Reset mapping button
                if st.button("🔄 Reset Mappings"):
                    st.session_state.mappings = {}
                    st.warning("Column mappings have been reset.")
                
                # Create mapping interface
                col1, col2 = st.columns(2)
                
                # Optional columns
                for idx, optional_col in enumerate(optional_columns):
                    with col1 if idx % 2 == 0 else col2:
                        mapping_key = f"mapping_{optional_col}"
                        current_value = st.session_state.mappings.get(mapping_key, '')
                        
                        selected = st.selectbox(
                            f"Map {optional_col} to:",
                            options=[''] + available_columns,
                            index=available_columns.index(current_value) + 1 if current_value in available_columns else 0,
                            key=mapping_key
                        )
                        st.session_state.mappings[mapping_key] = selected
                
                # Import button
                if st.button("🔄 Import Data", use_container_width=True):
                    with st.spinner('Processing and importing data...'):
                        try:
                            if st.session_state.import_df is None:
                                raise Exception("No data loaded. Please upload a file first.")
                            
                            # Create reverse mapping
                            reverse_mapping = {
                                v: k.replace('mapping_', '') 
                                for k, v in st.session_state.mappings.items() if v
                            }
                            
                            # Apply mapping to the DataFrame
                            mapped_df = st.session_state.import_df.rename(columns=reverse_mapping)
                            
                            success, message = CatalogService.add_catalog_entries(mapped_df, source='file_import')
                            if success:
                                st.success(message)
                                # Clear the import DataFrame after successful import
                                st.session_state.import_df = None
                            else:
                                st.error(message)
                            
                        except Exception as e:
                            st.error(f"❌ Error during import: {str(e)}")
                            st.info("💡 Please try again or contact support if the issue persists")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your file format and try again")
