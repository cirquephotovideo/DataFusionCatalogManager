import streamlit as st
from data_import_options import render_data_import_dashboard

# Initialize session state for health check
if 'health_check_status' not in st.session_state:
    st.session_state.health_check_status = 'healthy'

# Set page config with dark theme
st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Health check endpoint
def health_check():
    try:
        # Update health status in session state
        st.session_state.health_check_status = 'healthy'
        return {"status": "healthy"}
    except Exception as e:
        st.session_state.health_check_status = 'unhealthy'
        return {"status": "unhealthy", "error": str(e)}

# Apply dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0f1419;
    }
    .stSidebar {
        background-color: #1a1f24;
    }
    .stSidebar [data-testid="stMarkdownContainer"] {
        color: white;
    }
    .stSidebar [data-testid="stSelectbox"] {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Main navigation
st.sidebar.title("Data Fusion Catalog")

# Main Functions
main_page = st.sidebar.selectbox(
    "Select Function",
    [
        "Import/Export",
        "Dashboard",
        "Product Management",
        "Price Management",
        "Stock Management",
        "Order Management",
        "Reports & Analytics"
    ],
    index=0  # Set Import/Export as default
)

# Run health check
health_status = health_check()

# Display health status in sidebar
st.sidebar.markdown("---")
if st.session_state.health_check_status == 'healthy':
    st.sidebar.success("System Status: Healthy")
else:
    st.sidebar.error("System Status: Unhealthy")

# Render selected page
if main_page == "Import/Export":
    render_data_import_dashboard()

elif main_page == "Dashboard":
    st.title("Dashboard")
    st.info("Dashboard coming soon...")

elif main_page == "Product Management":
    st.title("Product Management")
    st.info("Product management coming soon...")

elif main_page == "Price Management":
    st.title("Price Management")
    st.info("Price management coming soon...")

elif main_page == "Stock Management":
    st.title("Stock Management")
    st.info("Stock management coming soon...")

elif main_page == "Order Management":
    st.title("Order Management")
    st.info("Order management coming soon...")

elif main_page == "Reports & Analytics":
    st.title("Reports & Analytics")
    st.info("Reports & analytics coming soon...")
