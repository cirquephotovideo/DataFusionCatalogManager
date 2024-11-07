import streamlit as st
from services.ai_service import AIService
from services.ollama_service import OllamaService
from services.whatsapp_service import WhatsAppService
import json

def render_ai_settings():
    """Render AI configuration settings"""
    st.title("AI & Communication Settings")

    # Initialize services
    if 'ai_service' not in st.session_state:
        st.session_state.ai_service = AIService()
    if 'ollama_service' not in st.session_state:
        st.session_state.ollama_service = OllamaService()

    # Create tabs for different settings
    ai_tab, whatsapp_tab = st.tabs(["AI Configuration", "WhatsApp Integration"])

    with ai_tab:
        render_ai_configuration()

    with whatsapp_tab:
        render_whatsapp_configuration()

def render_ai_configuration():
    """Render AI-specific settings"""
    # Get current config
    current_config = st.session_state.ai_service.get_active_config()

    # Provider selection
    provider = st.selectbox(
        "AI Provider",
        options=["openai", "gemini", "ollama"],
        index=0 if not current_config else 
              0 if current_config['provider'] == 'openai' else 
              1 if current_config['provider'] == 'gemini' else 2
    )

    # API Key input (not needed for Ollama)
    if provider != "ollama":
        api_key = st.text_input("API Key", type="password")
    else:
        api_key = None
        # Ollama model management
        st.subheader("Ollama Models")
        available_models = st.session_state.ollama_service.list_models()
        
        # Model installation
        new_model = st.text_input("Install new model (e.g., llama2, mistral, codellama)")
        if st.button("Install Model"):
            with st.spinner(f"Installing {new_model}..."):
                success = st.session_state.ollama_service.pull_model(new_model)
                if success:
                    st.success(f"Successfully installed {new_model}")
                    st.rerun()
                else:
                    st.error(f"Failed to install {new_model}")
        
        # Display installed models
        if available_models:
            st.write("Installed models:")
            for model in available_models:
                st.code(model)
        else:
            st.info("No Ollama models installed. Install a model to get started.")

    # Model selection based on provider
    if provider == "ollama":
        available_models = st.session_state.ollama_service.list_models()
        if not available_models:
            available_models = ["mistral"]  # Default model
    else:
        available_models = st.session_state.ai_service.get_available_models(provider)
    
    model = st.selectbox(
        "Model",
        options=available_models,
        index=0 if not current_config else available_models.index(current_config['model']) if current_config['model'] in available_models else 0
    )

    # Language selection
    languages = {
        "fr_FR": "French",
        "en_US": "English",
        "es_ES": "Spanish",
        "de_DE": "German",
        "it_IT": "Italian"
    }
    default_lang = "fr_FR"
    selected_language = st.selectbox(
        "Response Language",
        options=list(languages.keys()),
        format_func=lambda x: languages[x],
        index=list(languages.keys()).index(default_lang)
    )

    # Temperature setting
    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=1.0,
        value=0.7 if not current_config else current_config['temperature'],
        step=0.1
    )

    # Enrichment prompts configuration
    st.subheader("Product Enrichment Prompts")
    
    if "enrichment_prompts" not in st.session_state:
        st.session_state.enrichment_prompts = [
            "Create a detailed product description focusing on features and benefits",
            "Generate technical specifications in a structured format",
            "Suggest SEO-optimized product title and meta description",
            "List main product features and use cases",
            "Generate relevant product categories and tags",
            "Create a marketing-focused product description highlighting unique selling points"
        ]

    # Display and edit prompts
    updated_prompts = []
    for i, prompt in enumerate(st.session_state.enrichment_prompts):
        updated_prompt = st.text_area(f"Prompt {i+1}", value=prompt, height=100)
        updated_prompts.append(updated_prompt)

    # Save AI settings
    if st.button("Save AI Configuration"):
        if not api_key and not current_config and provider != "ollama":
            st.error("API Key is required")
            return

        # Save AI configuration
        success, message = st.session_state.ai_service.configure_ai(
            provider=provider,
            api_key=api_key if api_key else None,
            model=model,
            temperature=temperature,
            language=selected_language
        )

        if success:
            st.session_state.enrichment_prompts = updated_prompts
            st.success("AI Configuration saved successfully!")
        else:
            st.error(f"Error saving configuration: {message}")

def render_whatsapp_configuration():
    """Render WhatsApp configuration settings"""
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
    st.subheader("WhatsApp Business API")
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
    st.subheader("Notifications")
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

    # Test Connection
    if st.button("Test WhatsApp Connection"):
        if phone_number_id and access_token and verify_token:
            whatsapp = WhatsAppService(phone_number_id, access_token, verify_token)
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

    # Save WhatsApp settings
    if st.button("Save WhatsApp Configuration"):
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
            'language': st.session_state.whatsapp_settings.get('language', 'fr')
        }
        
        # Save to file
        with open('whatsapp_settings.json', 'w') as f:
            json.dump(new_settings, f)
        
        st.session_state.whatsapp_settings = new_settings
        st.success("WhatsApp configuration saved successfully!")
