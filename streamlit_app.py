import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🛍️",
    layout="wide"
)

def main():
    st.title("Data Fusion Catalog Manager")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Catalog Management", "Product Enrichment", "Price Management", "Subscriptions"]
    )
    
    if page == "Dashboard":
        st.header("Dashboard")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Products", "1,234")
        with col2:
            st.metric("Active Subscriptions", "56")
        with col3:
            st.metric("Sync Status", "Active")
            
        st.subheader("Recent Activities")
        st.write("Product sync completed - Success")
        st.write("New subscription added - Success")
        
    elif page == "Catalog Management":
        st.header("Catalog Management")
        st.write("Catalog management features coming soon...")
        
    elif page == "Product Enrichment":
        st.header("Product Enrichment")
        st.write("Product enrichment features coming soon...")
        
    elif page == "Price Management":
        st.header("Price Management")
        st.write("Price management features coming soon...")
        
    elif page == "Subscriptions":
        st.header("Subscription Management")
        st.write("Subscription management features coming soon...")

if __name__ == "__main__":
    main()
