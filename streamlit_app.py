import streamlit as st
import pandas as pd

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
    activity_data = pd.DataFrame({
        "Timestamp": ["2024-01-24 10:00", "2024-01-24 09:45", "2024-01-24 09:30"],
        "Activity": ["Product sync completed", "New subscription added", "Price update"],
        "Status": ["Success", "Success", "Success"]
    })
    st.dataframe(activity_data, use_container_width=True)
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Sync Performance")
        performance_data = pd.DataFrame({
            "Success Rate": [99, 98, 99, 100, 99, 98, 99],
            "Error Rate": [1, 2, 1, 0, 1, 2, 1]
        })
        st.line_chart(performance_data)
    
    with chart_col2:
        st.subheader("Product Distribution")
        distribution_data = pd.DataFrame({
            "Category": ["A", "B", "C", "D", "E"],
            "Products": [100, 80, 60, 40, 20]
        }).set_index("Category")
        st.bar_chart(distribution_data)

elif main_page == "Import/Export":
    st.title("Import/Export")
    st.info("Import/Export functionality coming soon...")

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
