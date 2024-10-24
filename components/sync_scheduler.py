import streamlit as st
from services.odoo_service import OdooService
from datetime import datetime, time
import json
import os
import pandas as pd

def load_odoo_config():
    """Load Odoo configuration from file"""
    try:
        if os.path.exists('odoo_config.json'):
            with open('odoo_config.json', 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def save_odoo_config(config):
    """Save Odoo configuration to file"""
    try:
        with open('odoo_config.json', 'w') as f:
            json.dump(config, f)
        return True
    except Exception:
        return False

def save_sync_log(log_entry):
    """Save sync log to history"""
    try:
        history = []
        if os.path.exists('sync_history.json'):
            with open('sync_history.json', 'r') as f:
                history = json.load(f)
        
        # Add new entry at the beginning
        history.insert(0, log_entry)
        
        # Keep only last 100 entries
        history = history[:100]
        
        with open('sync_history.json', 'w') as f:
            json.dump(history, f)
    except Exception as e:
        st.error(f"Error saving sync log: {str(e)}")

def render_sync_scheduler():
    st.header("Odoo Sync Scheduler")

    # Initialize session state
    if 'odoo_service' not in st.session_state:
        st.session_state.odoo_service = None
    if 'available_databases' not in st.session_state:
        st.session_state.available_databases = []
    if 'odoo_fields' not in st.session_state:
        st.session_state.odoo_fields = {}
    if 'sync_logs' not in st.session_state:
        st.session_state.sync_logs = []

    # Load saved configuration
    saved_config = load_odoo_config()
    
    # Odoo Connection Configuration
    with st.form("odoo_config"):
        st.subheader("Odoo Connection")
        
        col1, col2 = st.columns(2)
        with col1:
            url = st.text_input(
                "Odoo URL",
                value=saved_config.get('url', '') if saved_config else '',
                help="Example: https://yourodoo.com"
            )
            
            # Check databases if URL is provided
            if url and st.form_submit_button("Check Available Databases", type="secondary"):
                try:
                    temp_service = OdooService(url, "", "", "", verify_ssl=False)
                    st.session_state.available_databases = temp_service.get_available_databases()
                    if st.session_state.available_databases:
                        st.success(f"Found {len(st.session_state.available_databases)} databases")
                    else:
                        st.warning("No databases found or couldn't access database list")
                except Exception as e:
                    st.error(f"Error checking databases: {str(e)}")
            
            # Database selection/input
            if st.session_state.available_databases:
                database = st.selectbox(
                    "Database",
                    options=st.session_state.available_databases,
                    index=st.session_state.available_databases.index(saved_config.get('database', '')) if saved_config and saved_config.get('database') in st.session_state.available_databases else 0
                )
            else:
                database = st.text_input(
                    "Database",
                    value=saved_config.get('database', '') if saved_config else '',
                    help="Enter your Odoo database name"
                )
            
            verify_ssl = st.checkbox(
                "Verify SSL Certificate",
                value=saved_config.get('verify_ssl', False) if saved_config else False,
                help="Disable this if using self-signed certificates"
            )
        
        with col2:
            username = st.text_input(
                "Username",
                value=saved_config.get('username', '') if saved_config else '',
                help="Your Odoo username/email"
            )
            password = st.text_input(
                "Password",
                type="password",
                help="Your Odoo password"
            )

        save_config = st.checkbox("Save configuration", value=True)
        test_button = st.form_submit_button("Test Connection")
        
        if test_button:
            if not all([url, database, username, password]):
                st.error("All fields are required")
            else:
                try:
                    odoo = OdooService(url, database, username, password, verify_ssl=verify_ssl)
                    success, message = odoo.test_connection()
                    
                    if success:
                        st.session_state.odoo_service = odoo
                        # Load Odoo fields
                        st.session_state.odoo_fields = odoo.get_odoo_fields()
                        st.success(message)
                        
                        if save_config:
                            config = {
                                'url': url,
                                'database': database,
                                'username': username,
                                'password': password,
                                'verify_ssl': verify_ssl
                            }
                            if save_odoo_config(config):
                                st.success("Configuration saved!")
                            else:
                                st.warning("Failed to save configuration")
                    else:
                        st.error(message)
                        if "SSL" in message:
                            st.info("💡 Try disabling SSL verification if you're using a self-signed certificate")
                        elif "database" in message.lower():
                            st.info("💡 Click 'Check Available Databases' to see available databases")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    # Field Mapping Configuration
    if st.session_state.odoo_service:
        st.markdown("---")
        st.subheader("Field Mapping")
        
        # Get current mappings and suggestions
        current_mappings = st.session_state.odoo_service.get_field_mappings()
        field_suggestions = st.session_state.odoo_service.get_field_suggestions()
        
        with st.form("field_mapping"):
            st.write("Map local fields to Odoo fields:")
            
            # Local fields with descriptions
            field_descriptions = {
                'name': 'Product Name',
                'article_code': 'Internal Reference',
                'barcode': 'Barcode/EAN13',
                'description': 'Product Description',
                'price': 'Sales Price',
                'purchase_price': 'Cost Price',
                'stock_quantity': 'Quantity On Hand'
            }
            
            # Show available Odoo fields
            if st.session_state.odoo_fields:
                with st.expander("Available Odoo Fields"):
                    for field_name, field_info in st.session_state.odoo_fields.items():
                        st.write(f"**{field_info['string']}** (`{field_name}`): {field_info['help']}")
            
            # Create mapping interface
            mappings = {}
            col1, col2 = st.columns(2)
            for idx, (field, desc) in enumerate(field_descriptions.items()):
                with col1 if idx % 2 == 0 else col2:
                    # Show suggestions if available
                    suggestions = field_suggestions.get(field, [])
                    if suggestions:
                        mappings[field] = st.selectbox(
                            f"Map {desc} ({field}) to:",
                            options=[''] + suggestions,
                            index=suggestions.index(current_mappings.get(field)) + 1 if current_mappings.get(field) in suggestions else 0,
                            help=f"Select Odoo field for {desc}"
                        )
                    else:
                        mappings[field] = st.text_input(
                            f"Map {desc} ({field}) to:",
                            value=current_mappings.get(field, ''),
                            help=f"Enter Odoo field name for {desc}"
                        )
            
            if st.form_submit_button("Save Mappings"):
                if st.session_state.odoo_service.save_field_mappings(mappings):
                    st.success("Field mappings saved successfully!")
                else:
                    st.error("Failed to save field mappings")

        # Sync Schedule Configuration
        st.markdown("---")
        st.subheader("Sync Schedule")
        
        # Get sync status
        status = st.session_state.odoo_service.get_sync_status()
        
        # Display status
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", status.get('status', 'Unknown'))
        with col2:
            st.metric("Products in Odoo", str(status.get('product_count', 0)))
        with col3:
            st.metric("Last Sync", status.get('last_sync', '-'))

        # Schedule configuration
        st.markdown("### Schedule Settings")
        
        schedule_enabled = st.toggle("Enable scheduled sync")
        
        if schedule_enabled:
            col1, col2 = st.columns(2)
            with col1:
                sync_time = st.time_input(
                    "Daily sync time",
                    value=time(hour=0, minute=0)
                )
            with col2:
                sync_direction = st.selectbox(
                    "Sync direction",
                    ["Import from Odoo", "Export to Odoo", "Bidirectional"]
                )
            
            if st.button("Save Schedule"):
                # Save schedule configuration
                schedule_config = {
                    'enabled': True,
                    'time': sync_time.strftime("%H:%M"),
                    'direction': sync_direction
                }
                try:
                    with open('sync_schedule.json', 'w') as f:
                        json.dump(schedule_config, f)
                    st.success("Schedule saved!")
                except Exception as e:
                    st.error(f"Error saving schedule: {str(e)}")

        # Manual sync buttons
        st.markdown("### Manual Sync")
        col1, col2 = st.columns(2)
        
        # Progress bar placeholder
        progress_placeholder = st.empty()
        log_placeholder = st.empty()
        
        with col1:
            if st.button("Import from Odoo"):
                progress_bar = progress_placeholder.progress(0)
                log_container = log_placeholder.container()
                
                with st.spinner("Importing products from Odoo..."):
                    start_time = datetime.now()
                    success, message = st.session_state.odoo_service.sync_products()
                    end_time = datetime.now()
                    
                    # Update progress
                    progress_bar.progress(100)
                    
                    # Save sync log
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'operation': 'Import',
                        'status': 'Success' if success else 'Failed',
                        'message': message,
                        'duration': str(end_time - start_time)
                    }
                    save_sync_log(log_entry)
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        with col2:
            if st.button("Export to Odoo"):
                progress_bar = progress_placeholder.progress(0)
                log_container = log_placeholder.container()
                
                with st.spinner("Exporting products to Odoo..."):
                    start_time = datetime.now()
                    from services.catalog_service import CatalogService
                    products = CatalogService.get_catalogs()
                    total_products = len(products)
                    
                    # Update progress as products are processed
                    for i, batch in enumerate(range(0, total_products, 50)):
                        batch_products = products[batch:batch + 50]
                        success, message = st.session_state.odoo_service.export_products(batch_products)
                        
                        # Update progress
                        progress = min(100, int((batch + 50) * 100 / total_products))
                        progress_bar.progress(progress)
                        
                        # Update log
                        log_container.write(f"Processed {min(batch + 50, total_products)} of {total_products} products")
                        
                        if not success:
                            st.error(f"Error in batch {i+1}: {message}")
                            break
                    
                    end_time = datetime.now()
                    
                    # Save sync log
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'operation': 'Export',
                        'status': 'Success' if success else 'Failed',
                        'message': message,
                        'duration': str(end_time - start_time)
                    }
                    save_sync_log(log_entry)
                    
                    if success:
                        st.success(f"Successfully exported {total_products} products")
                    else:
                        st.error(message)

        # Sync History
        st.markdown("### Sync History")
        try:
            if os.path.exists('sync_history.json'):
                with open('sync_history.json', 'r') as f:
                    history = json.load(f)
                    history_df = pd.DataFrame(history)
                    st.dataframe(
                        history_df,
                        columns=['timestamp', 'operation', 'status', 'message', 'duration'],
                        hide_index=True
                    )
            else:
                st.info("No sync history available")
        except Exception as e:
            st.error(f"Error loading sync history: {str(e)}")
