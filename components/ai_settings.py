import streamlit as st
from services.ai_service import AIService
from services.ollama_service import OllamaService

def render_ai_settings():
    """Render AI configuration settings"""
    st.title("AI Settings")

    # Initialize services
    if 'ai_service' not in st.session_state:
        st.session_state.ai_service = AIService()
    if 'ollama_service' not in st.session_state:
        st.session_state.ollama_service = OllamaService()

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

    # Save button
    if st.button("Save Configuration"):
        if not api_key and not current_config and provider != "ollama":
            st.error("API Key is required")
            return

        # Save AI configuration
        success, message = st.session_state.ai_service.configure_ai(
            provider=provider,
            api_key=api_key if api_key else None,  # Keep existing key if not provided
            model=model,
            temperature=temperature,
            language=selected_language
        )

        if success:
            st.session_state.enrichment_prompts = updated_prompts
            st.success("Configuration saved successfully!")
        else:
            st.error(f"Error saving configuration: {message}")

    # Display current configuration
    if current_config:
        st.subheader("Current Configuration")
        st.json({
            "Provider": current_config['provider'],
            "Model": current_config['model'],
            "Language": current_config.get('language', 'fr_FR'),
            "Temperature": current_config['temperature'],
            "Last Used": str(current_config['last_used']) if current_config['last_used'] else "Never"
        })
