import streamlit as st

# Set page config with dark theme
st.set_page_config(
    page_title="Data Fusion Catalog Manager",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

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

# Main content
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

# System status indicator
st.sidebar.success("System Status: Healthy")
