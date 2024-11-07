import streamlit as st
import json
from datetime import datetime, time
from services.whatsapp_service import WhatsAppService

def render_whatsapp_settings():
    """Render WhatsApp configuration settings"""
    st.title("WhatsApp Settings")

    # Load existing settings
    if 'whatsapp_settings' not in st.session_state:
        try:
            with open('whatsapp_settings.json', 'r') as f:
                st.session_state.whatsapp_settings = json.load(f)
        except:
            st.session_state.whatsapp_settings = {
                'phone_number_id': '',
                'access_token': '',
                'verify_token': '',
                'webhook_url': '',
                'enabled': False,
                'notification_settings': {
                    'sales_alerts': True,
                    'inventory_alerts': True,
                    'order_notifications': True,
                    'price_changes': True
                },
                'auto_reply': True,
                'business_hours': {
                    'start': '09:00',
                    'end': '18:00'
                },
                'language': 'fr'
            }

    # WhatsApp Business API Settings
    st.subheader("API Configuration")
    phone_number_id = st.text_input(
        "Phone Number ID",
        value=st.session_state.whatsapp_settings.get('phone_number_id', ''),
        type="password"
    )
    access_token = st.text_input(
        "Access Token",
        value=st.session_state.whatsapp_settings.get('access_token', ''),
        type="password"
    )
    verify_token = st.text_input(
        "Verify Token",
        value=st.session_state.whatsapp_settings.get('verify_token', ''),
        type="password"
    )
    webhook_url = st.text_input(
        "Webhook URL",
        value=st.session_state.whatsapp_settings.get('webhook_url', '')
    )

    # Enable/Disable WhatsApp Integration
    enabled = st.toggle(
        "Enable WhatsApp Integration",
        value=st.session_state.whatsapp_settings.get('enabled', False)
    )

    # Notification Settings
    st.subheader("Notification Settings")
    col1, col2 = st.columns(2)
    with col1:
        sales_alerts = st.checkbox(
            "Sales Alerts",
            value=st.session_state.whatsapp_settings.get('notification_settings', {}).get('sales_alerts', True)
        )
        inventory_alerts = st.checkbox(
            "Inventory Alerts",
            value=st.session_state.whatsapp_settings.get('notification_settings', {}).get('inventory_alerts', True)
        )
    with col2:
        order_notifications = st.checkbox(
            "Order Notifications",
            value=st.session_state.whatsapp_settings.get('notification_settings', {}).get('order_notifications', True)
        )
        price_changes = st.checkbox(
            "Price Changes",
            value=st.session_state.whatsapp_settings.get('notification_settings', {}).get('price_changes', True)
        )

    # Auto-Reply Settings
    st.subheader("Auto-Reply Settings")
    auto_reply = st.checkbox(
        "Enable Auto-Reply",
        value=st.session_state.whatsapp_settings.get('auto_reply', True)
    )

    # Business Hours
    st.subheader("Business Hours")
    col1, col2 = st.columns(2)
    
    # Convert stored string times to time objects
    default_start = datetime.strptime(
        st.session_state.whatsapp_settings['business_hours']['start'],
        '%H:%M'
    ).time()
    default_end = datetime.strptime(
        st.session_state.whatsapp_settings['business_hours']['end'],
        '%H:%M'
    ).time()
    
    with col1:
        start_time = st.time_input(
            "Start Time",
            value=default_start
        )
    with col2:
        end_time = st.time_input(
            "End Time",
            value=default_end
        )

    # Language Settings
    language = st.selectbox(
        "Language",
        options=['fr', 'en'],
        index=0 if st.session_state.whatsapp_settings.get('language', 'fr') == 'fr' else 1
    )

    # Test Connection
    if st.button("Test Connection"):
        if phone_number_id and access_token and verify_token:
            whatsapp = WhatsAppService(phone_number_id, access_token, verify_token)
            # Send test message to admin number
            success = whatsapp.send_message(
                to=phone_number_id,
                message="Test connection successful!"
            )
            if success:
                st.success("WhatsApp connection test successful!")
            else:
                st.error("WhatsApp connection test failed!")
        else:
            st.error("Please fill in all required fields!")

    # Save Settings
    if st.button("Save Settings"):
        new_settings = {
            'phone_number_id': phone_number_id,
            'access_token': access_token,
            'verify_token': verify_token,
            'webhook_url': webhook_url,
            'enabled': enabled,
            'notification_settings': {
                'sales_alerts': sales_alerts,
                'inventory_alerts': inventory_alerts,
                'order_notifications': order_notifications,
                'price_changes': price_changes
            },
            'auto_reply': auto_reply,
            'business_hours': {
                'start': start_time.strftime('%H:%M'),
                'end': end_time.strftime('%H:%M')
            },
            'language': language
        }
        
        # Save to file
        with open('whatsapp_settings.json', 'w') as f:
            json.dump(new_settings, f)
        
        st.session_state.whatsapp_settings = new_settings
        st.success("Settings saved successfully!")
