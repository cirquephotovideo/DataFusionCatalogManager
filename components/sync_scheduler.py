import streamlit as st
from services.odoo_service import OdooService
from services.prestashop_service import PrestashopService
from services.woocommerce_service import WooCommerceService
import json
from datetime import datetime
import pandas as pd

def render_sync_scheduler():
    """Render sync scheduler interface"""
    st.title("Sync Scheduler")

    # Platform selection
    platform = st.selectbox(
        "Select Platform",
        ["Odoo", "Prestashop", "WooCommerce"]
    )

    if platform == "Odoo":
        render_odoo_sync()
    elif platform == "Prestashop":
        render_prestashop_sync()
    else:
        render_woocommerce_sync()

def render_odoo_sync():
    """Render Odoo sync configuration"""
    st.subheader("Odoo Configuration")

    # Load existing configuration
    if 'odoo_config' not in st.session_state:
        try:
            with open('odoo_config.json', 'r') as f:
                st.session_state.odoo_config = json.load(f)
        except:
            st.session_state.odoo_config = {
                'url': '',
                'db': '',
                'username': '',
                'password': ''
            }

    # Configuration form
    with st.form("odoo_config_form"):
        url = st.text_input("Odoo URL", value=st.session_state.odoo_config.get('url', ''))
        db = st.text_input("Database", value=st.session_state.odoo_config.get('db', ''))
        username = st.text_input("Username", value=st.session_state.odoo_config.get('username', ''))
        password = st.text_input("Password", type="password")

        if st.form_submit_button("Save Configuration"):
            st.session_state.odoo_config = {
                'url': url,
                'db': db,
                'username': username,
                'password': password if password else st.session_state.odoo_config.get('password', '')
            }
            with open('odoo_config.json', 'w') as f:
                json.dump(st.session_state.odoo_config, f)
            st.success("Configuration saved!")

    # Test connection
    if st.button("Test Connection"):
        config = st.session_state.odoo_config
        odoo = OdooService(config['url'], config['db'], config['username'], config['password'])
        success, message = odoo.test_connection()
        if success:
            st.success(message)
        else:
            st.error(message)

def render_prestashop_sync():
    """Render Prestashop sync configuration"""
    st.subheader("Prestashop Configuration")

    # Load existing configuration
    if 'prestashop_config' not in st.session_state:
        try:
            with open('prestashop_config.json', 'r') as f:
                st.session_state.prestashop_config = json.load(f)
        except:
            st.session_state.prestashop_config = {
                'url': '',
                'api_key': ''
            }

    # Configuration form
    with st.form("prestashop_config_form"):
        url = st.text_input("Prestashop URL", value=st.session_state.prestashop_config.get('url', ''))
        api_key = st.text_input("API Key", type="password")

        if st.form_submit_button("Save Configuration"):
            st.session_state.prestashop_config = {
                'url': url,
                'api_key': api_key if api_key else st.session_state.prestashop_config.get('api_key', '')
            }
            with open('prestashop_config.json', 'w') as f:
                json.dump(st.session_state.prestashop_config, f)
            st.success("Configuration saved!")

    # Test connection
    if st.button("Test Connection"):
        config = st.session_state.prestashop_config
        prestashop = PrestashopService(config['url'], config['api_key'])
        success, message = prestashop.test_connection()
        if success:
            st.success(message)
        else:
            st.error(message)

    # Sync options
    st.subheader("Sync Options")
    sync_type = st.selectbox(
        "Select what to sync",
        ["Products", "Categories", "Stock", "Prices"]
    )

    if sync_type == "Products":
        if st.button("Sync Products"):
            config = st.session_state.prestashop_config
            prestashop = PrestashopService(config['url'], config['api_key'])
            with st.spinner("Syncing products..."):
                products = prestashop.get_products()
                if products:
                    df = pd.DataFrame(products)
                    st.write(f"Found {len(products)} products")
                    st.dataframe(df)
                else:
                    st.warning("No products found")

def render_woocommerce_sync():
    """Render WooCommerce sync configuration"""
    st.subheader("WooCommerce Configuration")

    # Load existing configuration
    if 'woocommerce_config' not in st.session_state:
        try:
            with open('woocommerce_config.json', 'r') as f:
                st.session_state.woocommerce_config = json.load(f)
        except:
            st.session_state.woocommerce_config = {
                'url': '',
                'consumer_key': '',
                'consumer_secret': ''
            }

    # Configuration form
    with st.form("woocommerce_config_form"):
        url = st.text_input("WooCommerce URL", value=st.session_state.woocommerce_config.get('url', ''))
        consumer_key = st.text_input("Consumer Key", type="password")
        consumer_secret = st.text_input("Consumer Secret", type="password")

        if st.form_submit_button("Save Configuration"):
            st.session_state.woocommerce_config = {
                'url': url,
                'consumer_key': consumer_key if consumer_key else st.session_state.woocommerce_config.get('consumer_key', ''),
                'consumer_secret': consumer_secret if consumer_secret else st.session_state.woocommerce_config.get('consumer_secret', '')
            }
            with open('woocommerce_config.json', 'w') as f:
                json.dump(st.session_state.woocommerce_config, f)
            st.success("Configuration saved!")

    # Test connection
    if st.button("Test Connection"):
        config = st.session_state.woocommerce_config
        woo = WooCommerceService(config['url'], config['consumer_key'], config['consumer_secret'])
        success, message = woo.test_connection()
        if success:
            st.success(message)
        else:
            st.error(message)

    # Sync options
    st.subheader("Sync Options")
    sync_type = st.selectbox(
        "Select what to sync",
        ["Products", "Categories", "Variations", "Attributes", "Tags"]
    )

    if sync_type == "Products":
        if st.button("Sync Products"):
            config = st.session_state.woocommerce_config
            woo = WooCommerceService(config['url'], config['consumer_key'], config['consumer_secret'])
            with st.spinner("Syncing products..."):
                products = woo.get_products()
                if products:
                    df = pd.DataFrame(products)
                    st.write(f"Found {len(products)} products")
                    st.dataframe(df)
                else:
                    st.warning("No products found")

def save_sync_history(platform: str, sync_type: str, status: str, message: str):
    """Save sync history to file"""
    try:
        try:
            with open('sync_history.json', 'r') as f:
                history = json.load(f)
        except:
            history = []

        history.append({
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'type': sync_type,
            'status': status,
            'message': message
        })

        with open('sync_history.json', 'w') as f:
            json.dump(history, f)
    except Exception as e:
        st.error(f"Error saving sync history: {str(e)}")
