import streamlit as st
import os
from models.database import SessionLocal, init_db
from models.subscription_models import Subscription
from components.subscription_manager import SubscriptionManager
from components.catalog_manager import CatalogManager
from components.product_enrichment import ProductEnrichment
from components.price_management import PriceManagement

# Initialize database
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization error: {str(e)}")

# Page configuration
st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🛍️",
    layout="wide"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def init_components():
    try:
        db = SessionLocal()
        subscription_manager = SubscriptionManager(db)
        catalog_manager = CatalogManager(db)
        product_enrichment = ProductEnrichment()
        price_management = PriceManagement()
        return subscription_manager, catalog_manager, product_enrichment, price_management
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        return None, None, None, None
    finally:
        if 'db' in locals():
            db.close()

def main():
    try:
        st.title("Data Fusion Catalog Manager")
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Dashboard", "Catalog Management", "Product Enrichment", "Price Management", "Subscriptions"]
        )
        
        components = init_components()
        if not all(components):
            st.error("Failed to initialize application components")
            return
            
        subscription_manager, catalog_manager, product_enrichment, price_management = components
        
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
            st.table({
                "Timestamp": ["2024-01-24 10:00", "2024-01-24 09:45"],
                "Activity": ["Product sync completed", "New subscription added"],
                "Status": ["Success", "Success"]
            })
            
        elif page == "Catalog Management":
            st.header("Catalog Management")
            
            tab1, tab2 = st.tabs(["Products", "Categories"])
            
            with tab1:
                st.subheader("Product List")
                if st.button("Sync Products"):
                    st.info("Starting product synchronization...")
                    
            with tab2:
                st.subheader("Category Management")
                st.text_input("New Category Name")
                st.button("Add Category")
                
        elif page == "Product Enrichment":
            st.header("Product Enrichment")
            st.file_uploader("Upload Product Data", type=["csv", "xlsx"])
            st.button("Start Enrichment")
            
        elif page == "Price Management":
            st.header("Price Management")
            st.number_input("Markup Percentage", min_value=0, max_value=100, value=20)
            st.button("Update Prices")
            
        elif page == "Subscriptions":
            st.header("Subscription Management")
            
            # Add subscription form
            with st.form("new_subscription"):
                st.subheader("New Subscription")
                plan_type = st.selectbox("Plan Type", ["Basic", "Premium", "Enterprise"])
                duration = st.number_input("Duration (months)", min_value=1, max_value=12)
                st.form_submit_button("Create Subscription")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
