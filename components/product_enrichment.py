import streamlit as st
import pandas as pd

class ProductEnrichment:
    def __init__(self):
        pass

    def render(self):
        """Render product enrichment interface"""
        st.title("Product Management")

        # Create tabs for different functions
        list_tab, create_tab = st.tabs(["Product List", "Create Product"])

        with list_tab:
            self.render_product_list()

        with create_tab:
            self.render_product_form()

    def render_product_list(self):
        """Render list of products"""
        # Search and filter
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("Search Products", placeholder="Enter product name or reference")
        with col2:
            status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])

        # Sample products data
        products = [
            {
                'id': 1,
                'name': 'iPhone 13 Pro',
                'reference': 'IP13P-256',
                'article_code': 'APPL-13P',
                'barcode': '123456789',
                'stock_quantity': 50,
                'purchase_price': 899.99,
                'list_price': 999.99,
                'status': 'active',
                'description': 'Latest iPhone model with pro camera system'
            },
            {
                'id': 2,
                'name': 'MacBook Air M1',
                'reference': 'MBA-M1-256',
                'article_code': 'APPL-MBA',
                'barcode': '987654321',
                'stock_quantity': 25,
                'purchase_price': 899.99,
                'list_price': 999.99,
                'status': 'active',
                'description': 'Powerful laptop with M1 chip'
            },
            {
                'id': 3,
                'name': 'AirPods Pro',
                'reference': 'APP-2ND',
                'article_code': 'APPL-APP',
                'barcode': '456789123',
                'stock_quantity': 100,
                'purchase_price': 199.99,
                'list_price': 249.99,
                'status': 'active',
                'description': 'Wireless earbuds with noise cancellation'
            }
        ]

        # Display products
        for product in products:
            with st.expander(f"{product['name']} ({product['reference']})"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Article Code: {product['article_code']}")
                    st.write(f"Barcode: {product['barcode']}")
                    st.write(f"Status: {product['status']}")
                    
                with col2:
                    st.write("**Stock & Price**")
                    st.write(f"Stock: {product['stock_quantity']}")
                    st.write(f"Purchase Price: ${product['purchase_price']:.2f}")
                    st.write(f"List Price: ${product['list_price']:.2f}")
                
                with col3:
                    st.write("**Actions**")
                    if st.button("Edit", key=f"edit_{product['id']}"):
                        st.session_state.editing_product = product
                    
                    if st.button("Delete", key=f"delete_{product['id']}"):
                        st.success(f"Product {product['name']} would be deleted")
                
                if product['description']:
                    st.write("**Description**")
                    st.write(product['description'])

    def render_product_form(self):
        """Render product creation/edit form"""
        st.subheader("Product Details")
        
        editing = False
        if hasattr(st.session_state, 'editing_product'):
            editing = True
            product = st.session_state.editing_product
            st.info(f"Editing product: {product['name']}")
        else:
            product = {
                'name': '',
                'description': '',
                'reference': '',
                'article_code': '',
                'barcode': '',
                'stock_quantity': 0,
                'purchase_price': 0.0,
                'list_price': 0.0,
                'status': 'active'
            }

        with st.form("product_form"):
            # Basic Information
            st.write("**Basic Information**")
            name = st.text_input("Product Name", value=product['name'])
            description = st.text_area("Description", value=product['description'])
            
            col1, col2 = st.columns(2)
            with col1:
                reference = st.text_input("Reference", value=product['reference'])
                article_code = st.text_input("Article Code", value=product['article_code'])
            
            with col2:
                barcode = st.text_input("Barcode", value=product['barcode'])
                status = st.selectbox(
                    "Status",
                    options=['active', 'inactive', 'pending'],
                    index=['active', 'inactive', 'pending'].index(product['status'])
                )
            
            # Stock and Price
            st.write("**Stock & Price Information**")
            col1, col2, col3 = st.columns(3)
            with col1:
                stock = st.number_input(
                    "Stock Quantity",
                    value=product['stock_quantity'],
                    min_value=0
                )
            with col2:
                purchase_price = st.number_input(
                    "Purchase Price",
                    value=product['purchase_price'],
                    min_value=0.0,
                    format="%.2f"
                )
            with col3:
                list_price = st.number_input(
                    "List Price",
                    value=product['list_price'],
                    min_value=0.0,
                    format="%.2f"
                )

            # Media
            st.write("**Media**")
            st.file_uploader("Product Images", accept_multiple_files=True)

            # Categories and Tags
            st.write("**Organization**")
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Category", ["Electronics", "Computers", "Accessories"])
                st.multiselect("Tags", ["New", "Featured", "Sale", "Premium"])
            with col2:
                st.selectbox("Brand", ["Apple", "Samsung", "Microsoft"])
                st.selectbox("Supplier", ["Direct", "Distributor A", "Distributor B"])

            if st.form_submit_button("Save Product"):
                if editing:
                    st.success("Product updated successfully!")
                    if 'editing_product' in st.session_state:
                        del st.session_state.editing_product
                else:
                    st.success("Product created successfully!")

        if editing and st.button("Cancel Editing"):
            if 'editing_product' in st.session_state:
                del st.session_state.editing_product
