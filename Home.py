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

# Health check middleware
def check_health():
    try:
        # Basic health check - verify session state
        if not hasattr(st.session_state, 'health_check_status'):
            raise Exception("Session not initialized")
        return True
    except Exception as e:
        st.session_state.health_check_status = 'unhealthy'
        return False

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

# Main header
st.title("Data Fusion Catalog Manager")
st.markdown("""
Welcome to the Data Fusion Catalog Manager! This tool helps you manage and synchronize your product catalogs across multiple platforms.

Choose a function from the sidebar to get started:
- 📊 **Dashboard**: View key metrics and performance indicators
- 📥 **Import/Export**: Manage data import and export operations
- 📦 **Product Management**: Handle your product catalog
- 💰 **Price Management**: Manage pricing strategies
- 📦 **Stock Management**: Track inventory levels
- 📋 **Order Management**: Process and track orders
- 📈 **Reports & Analytics**: Generate insights from your data
""")

# System status indicator in sidebar
st.sidebar.title("System Status")
if check_health():
    st.sidebar.success("System Status: Healthy")
else:
    st.sidebar.error("System Status: Unhealthy")

# Display Import/Export options on home page
st.header("Quick Import/Export")
render_data_import_dashboard()
