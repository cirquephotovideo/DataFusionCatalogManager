import streamlit as st
import os
from dotenv import load_dotenv
from models.database import SessionLocal, init_db, Subscription
from components.subscription_manager import SubscriptionManager
from components.catalog_manager import CatalogManager
from components.product_enrichment import ProductEnrichment
from components.price_management import PriceManagement

# Load environment variables
load_dotenv()

# Health check endpoint
def health_check():
    return {"status": "healthy"}

# Configure Streamlit
st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add health check endpoint
if st._is_running_with_streamlit:
    health_check()

# Initialize database at startup
@st.cache_resource
def initialize_database():
    try:
        init_db()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.db_session = None

@st.cache_resource
def get_db():
    """Get database session"""
    if not st.session_state.db_session:
        try:
            st.session_state.db_session = SessionLocal()
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            return None
    return st.session_state.db_session

@st.cache_resource
def init_components(db):
    """Initialize application components with error handling"""
    try:
        subscription_manager = SubscriptionManager(db)
        catalog_manager = CatalogManager(db)
        product_enrichment = ProductEnrichment()
        price_management = PriceManagement()
        return subscription_manager, catalog_manager, product_enrichment, price_management
    except Exception as e:
        st.error(f"Error initializing components: {str(e)}")
        return None, None, None, None

def main():
    try:
        # Initialize database
        if not initialize_database():
            st.stop()

        st.title("Data Fusion Catalog Manager")
        
        # Get database session
        db = get_db()
        if not db:
            st.stop()
        
        # Initialize components
        components = init_components(db)
        if not all(components):
            st.stop()
            
        subscription_manager, catalog_manager, product_enrichment, price_management = components
        
        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Dashboard", "Catalog Management", "Product Enrichment", "Price Management", "Subscriptions"]
        )
        
        if page == "Dashboard":
            st.header("Dashboard")
            try:
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
            except Exception as e:
                st.error(f"Error loading dashboard: {str(e)}")
            
        elif page == "Catalog Management":
            st.header("Catalog Management")
            try:
                tab1, tab2 = st.tabs(["Products", "Categories"])
                
                with tab1:
                    st.subheader("Product List")
                    if st.button("Sync Products"):
                        st.info("Starting product synchronization...")
                        
                with tab2:
                    st.subheader("Category Management")
                    st.text_input("New Category Name")
                    st.button("Add Category")
            except Exception as e:
                st.error(f"Error in catalog management: {str(e)}")
                
        elif page == "Product Enrichment":
            st.header("Product Enrichment")
            try:
                st.file_uploader("Upload Product Data", type=["csv", "xlsx"])
                st.button("Start Enrichment")
            except Exception as e:
                st.error(f"Error in product enrichment: {str(e)}")
            
        elif page == "Price Management":
            st.header("Price Management")
            try:
                st.number_input("Markup Percentage", min_value=0, max_value=100, value=20)
                st.button("Update Prices")
            except Exception as e:
                st.error(f"Error in price management: {str(e)}")
            
        elif page == "Subscriptions":
            st.header("Subscription Management")
            try:
                with st.form("new_subscription"):
                    st.subheader("New Subscription")
                    plan_type = st.selectbox("Plan Type", ["Basic", "Premium", "Enterprise"])
                    duration = st.number_input("Duration (months)", min_value=1, max_value=12)
                    st.form_submit_button("Create Subscription")
            except Exception as e:
                st.error(f"Error in subscription management: {str(e)}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up database session
        if st.session_state.db_session:
            st.session_state.db_session.close()
            st.session_state.db_session = None

if __name__ == "__main__":
    main()
