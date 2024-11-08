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

# Main navigation
st.sidebar.title("Data Fusion Catalog")

# System status indicator
st.sidebar.success("System Status: Healthy")

# Main Functions
main_page = st.sidebar.selectbox(
    "Select Function",
    [
        "Dashboard",
        "Import/Export",
        "Product Management",
        "Price Management",
        "Stock Management",
        "Order Management",
        "Reports & Analytics"
    ],
    index=0  # Set Dashboard as default
)

# Render selected page
if main_page == "Dashboard":
    st.title("Dashboard")
    
    # Create a 3-column layout for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Products", value="1,234", delta="↑ 123 from last month")
    with col2:
        st.metric(label="Active Syncs", value="56", delta="↑ 3 today")
    with col3:
        st.metric(label="Success Rate", value="99.8%", delta="↑ 0.2%")
    
    # Recent Activity
    st.subheader("Recent Activity")
    st.table({
        "Timestamp": ["2024-01-24 10:00", "2024-01-24 09:45", "2024-01-24 09:30"],
        "Activity": ["Product sync completed", "New subscription added", "Price update"],
        "Status": ["Success", "Success", "Success"]
    })
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Sync Performance")
        st.line_chart({
            "Success Rate": [99, 98, 99, 100, 99, 98, 99],
            "Error Rate": [1, 2, 1, 0, 1, 2, 1]
        })
    
    with chart_col2:
        st.subheader("Product Distribution")
        st.bar_chart({
            "Category A": [100],
            "Category B": [80],
            "Category C": [60],
            "Category D": [40],
            "Category E": [20]
        })

else:
    st.title(main_page)
    st.info(f"{main_page} functionality coming soon...")
