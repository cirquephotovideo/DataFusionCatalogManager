import streamlit as st
from services.manufacturer_service import ManufacturerService

def render_manufacturer_manager():
    st.header("Manufacturer & Brand Management")
    
    # Add manufacturer form
    with st.form("add_manufacturer"):
        st.subheader("Add New Manufacturer")
        manufacturer_name = st.text_input("Manufacturer Name")
        submit_manufacturer = st.form_submit_button("Add Manufacturer")
        
        if submit_manufacturer and manufacturer_name:
            success, message = ManufacturerService.add_manufacturer(manufacturer_name)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Add brand form
    manufacturers = ManufacturerService.get_manufacturers()
    
    with st.form("add_brand"):
        st.subheader("Add New Brand")
        manufacturer_options = {m['name']: m['id'] for m in manufacturers}
        selected_manufacturer = st.selectbox("Select Manufacturer", options=list(manufacturer_options.keys()))
        brand_name = st.text_input("Brand Name")
        submit_brand = st.form_submit_button("Add Brand")
        
        if submit_brand and brand_name and selected_manufacturer:
            success, message = ManufacturerService.add_brand(
                brand_name,
                manufacturer_options[selected_manufacturer]
            )
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # Display current manufacturers and brands
    st.subheader("Current Manufacturers and Brands")
    for manufacturer in manufacturers:
        with st.expander(f"{manufacturer['name']}"):
            for brand in manufacturer['brands']:
                st.write(f"• {brand['name']}")
