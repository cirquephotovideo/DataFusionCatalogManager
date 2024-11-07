import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

def render_dashboard():
    """Render main dashboard"""
    st.title("Dashboard")

    # Top Stats Cards
    render_stats_cards()

    # Main Content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sales Chart
        render_sales_chart()
        
        # Product Performance
        render_product_performance()
    
    with col2:
        # Platform Status
        render_platform_status()
        
        # Recent Activity
        render_recent_activity()

def render_stats_cards():
    """Render statistics cards"""
    # Create metrics cards with colorful containers
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style='padding: 1rem; background-color: #1f77b4; border-radius: 0.5rem; color: white;'>
                <h3 style='margin: 0; font-size: 1rem;'>Total Products</h3>
                <h2 style='margin: 0; font-size: 2rem;'>1,234</h2>
                <p style='margin: 0; color: #a7d5ff;'>↑ 12% this month</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='padding: 1rem; background-color: #2ca02c; border-radius: 0.5rem; color: white;'>
                <h3 style='margin: 0; font-size: 1rem;'>Active Products</h3>
                <h2 style='margin: 0; font-size: 2rem;'>987</h2>
                <p style='margin: 0; color: #a7ffa7;'>↑ 8% this month</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='padding: 1rem; background-color: #ff7f0e; border-radius: 0.5rem; color: white;'>
                <h3 style='margin: 0; font-size: 1rem;'>Low Stock</h3>
                <h2 style='margin: 0; font-size: 2rem;'>45</h2>
                <p style='margin: 0; color: #ffd4a7;'>↓ 5% this month</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div style='padding: 1rem; background-color: #d62728; border-radius: 0.5rem; color: white;'>
                <h3 style='margin: 0; font-size: 1rem;'>Out of Stock</h3>
                <h2 style='margin: 0; font-size: 2rem;'>23</h2>
                <p style='margin: 0; color: #ffa7a7;'>↑ 2% this month</p>
            </div>
        """, unsafe_allow_html=True)

def render_sales_chart():
    """Render sales performance chart"""
    st.subheader("Sales Performance")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    sales = [100 + i * 2 + random.randint(-10, 10) for i in range(len(dates))]
    df = pd.DataFrame({'Date': dates, 'Sales': sales})
    
    # Create line chart using Streamlit
    st.line_chart(df.set_index('Date'))

def render_product_performance():
    """Render product performance metrics"""
    st.subheader("Product Performance")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Top Products", "Categories"])
    
    with tab1:
        # Sample data for top products
        data = {
            'Product': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
            'Sales': [1200, 980, 850, 750, 650]
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Product'))
    
    with tab2:
        # Sample data for categories
        data = {
            'Category': ['Electronics', 'Clothing', 'Books', 'Home', 'Sports'],
            'Products': [450, 380, 250, 220, 180]
        }
        df = pd.DataFrame(data)
        st.bar_chart(df.set_index('Category'))

def render_platform_status():
    """Render platform connection status"""
    st.subheader("Platform Status")
    
    # Platform status with custom styling
    st.markdown("""
        <div style='padding: 1rem; background-color: #f0f2f6; border-radius: 0.5rem;'>
            <div style='margin-bottom: 1rem;'>
                <h4 style='margin: 0; color: #2ca02c;'>✓ Odoo</h4>
                <p style='margin: 0; color: #666;'>Last sync: 5 minutes ago</p>
            </div>
            <div style='margin-bottom: 1rem;'>
                <h4 style='margin: 0; color: #d62728;'>⚠ PrestaShop</h4>
                <p style='margin: 0; color: #666;'>Connection error</p>
            </div>
            <div style='margin-bottom: 1rem;'>
                <h4 style='margin: 0; color: #2ca02c;'>✓ WooCommerce</h4>
                <p style='margin: 0; color: #666;'>Last sync: 12 minutes ago</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_recent_activity():
    """Render recent activity feed"""
    st.subheader("Recent Activity")
    
    # Activity feed with custom styling
    activities = [
        {"time": "2 min ago", "action": "Product updated", "details": "iPhone 13 Pro"},
        {"time": "15 min ago", "action": "Stock adjusted", "details": "MacBook Air"},
        {"time": "1 hour ago", "action": "Price updated", "details": "iPad Mini"},
        {"time": "2 hours ago", "action": "Product added", "details": "AirPods Pro"},
        {"time": "3 hours ago", "action": "Sync completed", "details": "Odoo platform"}
    ]
    
    for activity in activities:
        st.markdown(f"""
            <div style='padding: 0.5rem; border-left: 3px solid #1f77b4; margin-bottom: 0.5rem;'>
                <p style='margin: 0; color: #666; font-size: 0.8rem;'>{activity['time']}</p>
                <p style='margin: 0; font-weight: bold;'>{activity['action']}</p>
                <p style='margin: 0; color: #333;'>{activity['details']}</p>
            </div>
        """, unsafe_allow_html=True)
