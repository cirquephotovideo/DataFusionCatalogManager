import streamlit as st
from models.database import SessionLocal, Supplier, SupplierProduct
from datetime import datetime

def render_supplier_management():
    """Render supplier management interface"""
    st.title("Supplier Management")

    # Create tabs for different functions
    list_tab, create_tab = st.tabs(["Supplier List", "Create Supplier"])

    with list_tab:
        render_supplier_list()

    with create_tab:
        render_supplier_form()

def render_supplier_list():
    """Render list of suppliers"""
    # Search
    search = st.text_input("Search Suppliers", placeholder="Enter supplier name")

    db = SessionLocal()
    try:
        # Get all suppliers
        suppliers = db.query(Supplier).all()
        
        # Filter suppliers based on search
        if search:
            suppliers = [s for s in suppliers if search.lower() in s.supplier_name.lower()]

        # Display suppliers
        if not suppliers:
            st.info("No suppliers found. Create a new supplier to get started.")
        
        for supplier in suppliers:
            with st.expander(f"{supplier.supplier_name}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write("**Contact Information**")
                    contact_info = supplier.contact_info or {}
                    st.write(f"Email: {contact_info.get('email', 'N/A')}")
                    st.write(f"Phone: {contact_info.get('phone', 'N/A')}")
                    st.write(f"Address: {contact_info.get('address', 'N/A')}")
                
                with col2:
                    st.write("**Business Information**")
                    st.write(f"Default Currency: {supplier.default_currency}")
                    # Get product count for this supplier
                    product_count = db.query(SupplierProduct).filter(
                        SupplierProduct.supplier_id == supplier.id
                    ).count()
                    st.write(f"Total Products: {product_count}")
                
                with col3:
                    st.write("**Actions**")
                    if st.button("Edit", key=f"edit_{supplier.id}"):
                        st.session_state.editing_supplier = {
                            'id': supplier.id,
                            'supplier_name': supplier.supplier_name,
                            'contact_info': supplier.contact_info,
                            'default_currency': supplier.default_currency
                        }
                    
                    if st.button("Delete", key=f"delete_{supplier.id}"):
                        # Check if supplier has products
                        if product_count > 0:
                            st.error(f"Cannot delete supplier with {product_count} products. Please delete or reassign products first.")
                        else:
                            db.delete(supplier)
                            db.commit()
                            st.success(f"Supplier {supplier.supplier_name} deleted")
                            st.experimental_rerun()

    finally:
        db.close()

def render_supplier_form():
    """Render supplier creation/edit form"""
    st.subheader("Supplier Details")
    
    editing = False
    if hasattr(st.session_state, 'editing_supplier'):
        editing = True
        supplier = st.session_state.editing_supplier
        st.info(f"Editing supplier: {supplier['supplier_name']}")
    else:
        supplier = {
            'supplier_name': '',
            'contact_info': {
                'email': '',
                'phone': '',
                'address': ''
            },
            'default_currency': 'USD'
        }

    # Basic Information
    st.write("**Basic Information**")
    supplier_name = st.text_input("Supplier Name", value=supplier['supplier_name'])
    
    # Contact Information
    st.write("**Contact Information**")
    contact_info = supplier.get('contact_info', {})
    email = st.text_input("Email", value=contact_info.get('email', ''))
    phone = st.text_input("Phone", value=contact_info.get('phone', ''))
    address = st.text_area("Address", value=contact_info.get('address', ''))
    
    # Business Information
    st.write("**Business Information**")
    default_currency = st.selectbox(
        "Default Currency",
        options=['USD', 'EUR', 'GBP', 'JPY'],
        index=['USD', 'EUR', 'GBP', 'JPY'].index(supplier.get('default_currency', 'USD'))
    )

    # Submit button outside the form
    if st.button("Save Supplier", type="primary"):
        if not supplier_name:
            st.error("Supplier name is required")
            return

        db = SessionLocal()
        try:
            if editing:
                # Update existing supplier
                db_supplier = db.query(Supplier).get(supplier['id'])
                if db_supplier:
                    db_supplier.supplier_name = supplier_name
                    db_supplier.contact_info = {
                        'email': email,
                        'phone': phone,
                        'address': address
                    }
                    db_supplier.default_currency = default_currency
                    db_supplier.updated_at = datetime.utcnow()
                    message = "Supplier updated successfully!"
            else:
                # Create new supplier
                st.write("Creating new supplier")  # Debug log
                new_supplier = Supplier(
                    supplier_name=supplier_name,
                    contact_info={
                        'email': email,
                        'phone': phone,
                        'address': address
                    },
                    default_currency=default_currency
                )
                db.add(new_supplier)
                message = "Supplier created successfully!"
            
            db.commit()
            st.success(message)
            
            if editing and 'editing_supplier' in st.session_state:
                del st.session_state.editing_supplier
            
            # Rerun to refresh the page
            st.experimental_rerun()
            
        except Exception as e:
            db.rollback()
            st.error(f"Error saving supplier: {str(e)}")
            st.write(f"Error details: {str(e)}")  # Debug log
        finally:
            db.close()

    if editing and st.button("Cancel Editing"):
        if 'editing_supplier' in st.session_state:
            del st.session_state.editing_supplier
        st.experimental_rerun()
