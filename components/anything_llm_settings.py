import streamlit as st
from services.anything_llm_service import AnythingLLMService
import json

def render_anything_llm_settings():
    """Render AnythingLLM configuration settings"""
    st.title("AnythingLLM Settings")

    # Initialize service
    if 'anything_llm_service' not in st.session_state:
        st.session_state.anything_llm_service = AnythingLLMService()

    # Load current settings
    if 'anything_llm_settings' not in st.session_state:
        try:
            with open('anything_llm_config.json', 'r') as f:
                st.session_state.anything_llm_settings = json.load(f)
        except:
            st.session_state.anything_llm_settings = {
                'api_url': 'http://localhost:3001/api',
                'api_key': '',
                'mode': 'local',
                'extension_enabled': False
            }

    # Deployment Mode
    st.subheader("Deployment")
    mode = st.selectbox(
        "Mode",
        options=['local', 'server'],
        index=0 if st.session_state.anything_llm_settings.get('mode') == 'local' else 1
    )

    # API Configuration
    st.subheader("API Configuration")
    api_url = st.text_input(
        "API URL",
        value=st.session_state.anything_llm_settings.get('api_url', '')
    )
    api_key = st.text_input(
        "API Key",
        value=st.session_state.anything_llm_settings.get('api_key', ''),
        type="password"
    )

    # Browser Extension
    st.subheader("Browser Extension")
    extension_enabled = st.toggle(
        "Enable Browser Extension",
        value=st.session_state.anything_llm_settings.get('extension_enabled', False)
    )

    if extension_enabled:
        if st.button("Generate Extension Key"):
            service = AnythingLLMService(api_url, api_key)
            success, result = service.generate_extension_key()
            if success:
                st.code(result, language=None)
                st.info("Copy this connection string to your browser extension")
            else:
                st.error(result)

        # Check extension status
        if st.button("Check Extension Status"):
            service = AnythingLLMService(api_url, api_key)
            success, message = service.get_extension_status()
            if success:
                st.success(message)
            else:
                st.error(message)

    # Test Connection
    if st.button("Test Connection"):
        service = AnythingLLMService(api_url, api_key)
        success, message = service.test_connection()
        if success:
            st.success(message)
        else:
            st.error(message)

    # Save Settings
    if st.button("Save Settings"):
        new_settings = {
            'api_url': api_url,
            'api_key': api_key,
            'mode': mode,
            'extension_enabled': extension_enabled
        }
        
        service = AnythingLLMService()
        if service.save_config(new_settings):
            st.session_state.anything_llm_settings = new_settings
            st.success("Settings saved successfully!")
        else:
            st.error("Error saving settings")
