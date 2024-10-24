import streamlit as st
from components.auth_manager import check_auth, render_user_management, render_change_password
from components.product_enrichment import render_product_enrichment
from components.catalog_manager import render_catalog_manager
from components.matching_engine import render_matching_engine
from components.sync_scheduler import render_sync_scheduler
from components.manufacturer_manager import render_manufacturer_manager
from components.ftp_manager import render_ftp_manager
from components.price_management import render_price_scraping, render_price_matching, render_competitor_analysis
from components.ai_settings import render_ai_settings
from components.web_scraper import render_web_scraper
from components.subscription_manager import render_subscription_manager

st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🔄",
    layout="wide"
)

# Check authentication
user_info = check_auth()

# Sidebar navigation
st.sidebar.title("Navigation")

# Main menu items
menu_items = {
    "Catalog Management": {
        "icon": "📊",
        "pages": ["Product Enrichment", "Catalog Manager", "Matching Engine"]
    },
    "Price Management": {
        "icon": "💰",
        "pages": ["Price Scraping", "Price Matching", "Competitor Analysis", "Web Scraper"]
    },
    "Sync & Integration": {
        "icon": "🔄",
        "pages": ["Sync Scheduler", "FTP Manager"]
    },
    "Configuration": {
        "icon": "⚙️",
        "pages": ["Manufacturer Manager", "User Management", "Change Password", "AI Settings"]
    },
    "Administration": {
        "icon": "👑",
        "pages": ["Subscription Manager"]
    }
}

# Create expandable sections for each menu category
selected_page = None
for category, details in menu_items.items():
    # Only show Administration menu to admin users
    if category == "Administration" and user_info["role"] != "admin":
        continue
        
    with st.sidebar.expander(f"{details['icon']} {category}", expanded=True):
        for page in details['pages']:
            if st.button(page, key=f"nav_{page}", use_container_width=True):
                selected_page = page

# User info in sidebar
st.sidebar.markdown("---")
st.sidebar.write(f"Logged in as: **{user_info['username']}** ({user_info['role']})")
if st.sidebar.button("Logout"):
    st.session_state.user_service.logout(st.session_state.auth_token)
    st.session_state.auth_token = None
    st.rerun()

# Store selected page in session state if it changed
if selected_page and ('current_page' not in st.session_state or st.session_state.current_page != selected_page):
    st.session_state.current_page = selected_page
    st.rerun()

# Get current page from session state
current_page = st.session_state.get('current_page', 'Product Enrichment')

# Render selected page
if current_page == "Product Enrichment":
    render_product_enrichment()
elif current_page == "Catalog Manager":
    render_catalog_manager()
elif current_page == "Matching Engine":
    render_matching_engine()
elif current_page == "Price Scraping":
    render_price_scraping()
elif current_page == "Price Matching":
    render_price_matching()
elif current_page == "Competitor Analysis":
    render_competitor_analysis()
elif current_page == "Web Scraper":
    render_web_scraper()
elif current_page == "Sync Scheduler":
    render_sync_scheduler()
elif current_page == "FTP Manager":
    render_ftp_manager()
elif current_page == "Manufacturer Manager":
    render_manufacturer_manager()
elif current_page == "User Management":
    if user_info["role"] == "admin":
        render_user_management()
    else:
        st.error("Access denied. Admin privileges required.")
elif current_page == "Change Password":
    render_change_password()
elif current_page == "AI Settings":
    if user_info["role"] == "admin":
        render_ai_settings()
    else:
        st.error("Access denied. Admin privileges required.")
elif current_page == "Subscription Manager":
    if user_info["role"] == "admin":
        render_subscription_manager()
    else:
        st.error("Access denied. Admin privileges required.")

# Add version info at bottom of sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("v1.0.0")
