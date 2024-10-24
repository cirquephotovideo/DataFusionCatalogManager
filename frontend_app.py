import streamlit as st
from models.database import SessionLocal, User, Subscription, Payment
from services.subscription_service import SubscriptionService
import requests
from datetime import datetime

# Initialize subscription service
if 'subscription_service' not in st.session_state:
    st.session_state.subscription_service = SubscriptionService()

def render_home():
    st.title("Data Fusion Catalog Manager")
    
    # Hero section
    st.header("Streamline Your Product Catalog Management")
    st.write("""
    Manage and synchronize your product catalogs across multiple platforms with ease.
    Start your 10-day free trial today!
    """)
    
    # Pricing Plans
    st.header("Pricing Plans")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Free Trial")
        st.write("Try all features for 10 days")
        st.write("✓ Full functionality")
        st.write("✓ Up to 5,000 products")
        st.write("✓ No credit card required")
        if st.button("Start Free Trial", key="trial_btn"):
            st.switch_page("pages/signup.py")

    with col2:
        st.subheader("Basic")
        st.write("€500/month")
        st.write("✓ Up to 5,000 products")
        st.write("✓ All features included")
        st.write("✓ Email support")
        if st.button("Subscribe Basic", key="basic_btn"):
            st.switch_page("pages/signup.py")

    with col3:
        st.subheader("Premium")
        st.write("€1,000/month")
        st.write("✓ Up to 10,000 products")
        st.write("✓ Priority support")
        st.write("✓ Advanced analytics")
        if st.button("Subscribe Premium", key="premium_btn"):
            st.switch_page("pages/signup.py")

    # Features
    st.header("Features")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.subheader("Multi-Platform Integration")
        st.write("""
        - Odoo integration
        - Prestashop support
        - WooCommerce sync
        - FTP automation
        """)
        
        st.subheader("AI-Powered Enrichment")
        st.write("""
        - Automatic categorization
        - Product descriptions
        - Image analysis
        - Smart matching
        """)
    
    with feature_col2:
        st.subheader("Price Management")
        st.write("""
        - Competitor price tracking
        - Automated updates
        - Price history
        - Margin analysis
        """)
        
        st.subheader("Advanced Analytics")
        st.write("""
        - Performance metrics
        - Sync monitoring
        - Custom reports
        - Data visualization
        """)

def render_login():
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            try:
                response = requests.post(
                    "http://localhost:8520/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    st.success("Login successful!")
                    st.session_state.user = response.json()
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.write("Don't have an account? [Sign up here](/signup)")

def render_signup():
    st.title("Sign Up")
    
    with st.form("signup_form"):
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        plan = st.selectbox(
            "Select Plan",
            ["free_trial", "basic", "premium"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        if st.form_submit_button("Sign Up"):
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            if not terms:
                st.error("Please accept the terms and conditions")
                return
            
            try:
                response = requests.post(
                    "http://localhost:8520/signup",
                    json={
                        "email": email,
                        "username": username,
                        "password": password,
                        "plan": plan
                    }
                )
                if response.status_code == 200:
                    st.success("Account created successfully!")
                    st.session_state.user = response.json()
                    st.experimental_rerun()
                else:
                    st.error(response.json().get("detail", "Error creating account"))
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.write("Already have an account? [Login here](/login)")

def main():
    st.set_page_config(
        page_title="Data Fusion Catalog Manager",
        page_icon="🔄",
        layout="wide"
    )
    
    # Navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        if st.button("Home"):
            st.session_state.page = 'home'
        if st.button("Login"):
            st.session_state.page = 'login'
        if st.button("Sign Up"):
            st.session_state.page = 'signup'
    
    # Render selected page
    if st.session_state.page == 'home':
        render_home()
    elif st.session_state.page == 'login':
        render_login()
    elif st.session_state.page == 'signup':
        render_signup()

if __name__ == "__main__":
    main()
