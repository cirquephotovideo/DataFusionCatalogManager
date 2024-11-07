import streamlit as st
from services.heygen_service import HeyGenService
import json

def render_heygen_settings():
    """Render HeyGen configuration settings"""
    st.title("HeyGen Video Settings")

    # Initialize service
    if 'heygen_service' not in st.session_state:
        st.session_state.heygen_service = HeyGenService()

    # Create tabs for different settings
    general_tab, style_tab, templates_tab = st.tabs(["General Settings", "Style & Animation", "Scene Templates"])

    with general_tab:
        render_general_settings()

    with style_tab:
        render_style_settings()

    with templates_tab:
        render_template_settings()

def render_general_settings():
    """Render general HeyGen settings"""
    st.subheader("API Configuration")
    api_key = st.text_input(
        "API Key",
        value=st.session_state.get('heygen_settings', {}).get('api_key', ''),
        type="password"
    )

    st.subheader("Default Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        language = st.selectbox(
            "Default Language",
            options=['en', 'fr'],
            format_func=lambda x: 'English' if x == 'en' else 'French'
        )

    with col2:
        resolution = st.selectbox(
            "Video Resolution",
            options=['720p', '1080p', '4K'],
            index=1
        )

def render_style_settings():
    """Render style and animation settings"""
    st.subheader("Visual Style")

    # Background Style
    st.write("Background Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        background_type = st.selectbox(
            "Background Type",
            options=['gradient', 'blur', 'minimal', 'studio'],
            index=0
        )

    with col2:
        if background_type == 'gradient':
            gradient_colors = st.color_picker("Gradient Color", '#007AFF')

    # Animation Settings
    st.write("Animation Settings")
    col1, col2 = st.columns(2)

    with col1:
        transitions = st.multiselect(
            "Transitions",
            options=['fade', 'slide', 'zoom', 'wave'],
            default=['fade', 'slide']
        )

    with col2:
        effects = st.multiselect(
            "Effects",
            options=['blur', 'float', '3d_rotate', 'pulse'],
            default=['float', '3d_rotate']
        )

    # Product Animation
    st.write("Product Animation")
    product_animation = st.selectbox(
        "Product Showcase Style",
        options=['3d_rotate', 'float', 'zoom_pan', 'highlight'],
        index=0
    )

    # Text Animation
    st.write("Text Animation")
    text_animation = st.selectbox(
        "Text Style",
        options=['float', 'slide_in', 'fade_in', 'typewriter'],
        index=0
    )

def render_template_settings():
    """Render scene template settings"""
    st.subheader("Scene Templates")

    # Product Showcase Template
    st.write("Product Showcase")
    col1, col2 = st.columns(2)
    
    with col1:
        showcase_background = st.selectbox(
            "Background Style",
            options=['gradient', 'studio', 'minimal'],
            key='showcase_bg'
        )
        camera_movement = st.selectbox(
            "Camera Movement",
            options=['smooth_pan', 'static', 'orbit'],
            key='showcase_camera'
        )

    with col2:
        lighting = st.selectbox(
            "Lighting Style",
            options=['studio', 'dramatic', 'soft'],
            key='showcase_light'
        )
        product_animation = st.selectbox(
            "Product Animation",
            options=['3d_rotate', 'float', 'showcase'],
            key='showcase_anim'
        )

    # Feature Highlight Template
    st.write("Feature Highlights")
    col1, col2 = st.columns(2)
    
    with col1:
        highlight_background = st.selectbox(
            "Background Style",
            options=['blur', 'minimal', 'gradient'],
            key='highlight_bg'
        )
        zoom_effect = st.checkbox("Enable Zoom Effect", value=True)

    with col2:
        text_animation = st.selectbox(
            "Text Animation",
            options=['float', 'slide_in', 'fade_in'],
            key='highlight_text'
        )
        highlight_color = st.color_picker("Highlight Color", '#007AFF')

    # Technical Specs Template
    st.write("Technical Specifications")
    col1, col2 = st.columns(2)
    
    with col1:
        specs_background = st.selectbox(
            "Background Style",
            options=['minimal', 'gradient', 'blur'],
            key='specs_bg'
        )
        layout = st.selectbox(
            "Layout Style",
            options=['grid', 'list', 'cards'],
            key='specs_layout'
        )

    with col2:
        animation = st.selectbox(
            "Animation Style",
            options=['slide_in', 'fade_in', 'cascade'],
            key='specs_anim'
        )
        icon_style = st.selectbox(
            "Icon Style",
            options=['outlined', 'filled', 'minimal'],
            key='specs_icons'
        )

    # Save Template Settings
    if st.button("Save Template Settings"):
        template_settings = {
            'product_showcase': {
                'background': showcase_background,
                'camera_movement': camera_movement,
                'lighting': lighting,
                'product_animation': product_animation
            },
            'feature_highlight': {
                'background': highlight_background,
                'zoom_effect': zoom_effect,
                'text_animation': text_animation,
                'highlight_color': highlight_color
            },
            'technical_specs': {
                'background': specs_background,
                'layout': layout,
                'animation': animation,
                'icon_style': icon_style
            }
        }
        
        # Save to config
        config = st.session_state.heygen_service.load_config()
        config['scene_templates'] = template_settings
        if st.session_state.heygen_service.save_config(config):
            st.success("Template settings saved successfully!")
        else:
            st.error("Error saving template settings")
