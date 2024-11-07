import streamlit as st
from services.ai_service import AIService
from services.catalog_service import CatalogService
from services.ollama_service import OllamaService
import speech_recognition as sr
import json
import base64
from datetime import datetime
import pandas as pd

def create_chat_container():
    """Create a fixed chat container in the bottom right"""
    # Custom CSS for chat container
    st.markdown("""
        <style>
        .chat-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            height: 500px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            z-index: 1000;
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 10px;
        }
        .chat-input {
            padding: 10px;
            border-top: 1px solid #eee;
        }
        .audio-button {
            background-color: #ff4b4b;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
        }
        .audio-button:hover {
            background-color: #ff3333;
        }
        </style>
    """, unsafe_allow_html=True)

def record_audio():
    """Record audio and convert to text"""
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.write("🎤 Listening...")
            audio = r.listen(source)
            st.write("Processing...")
            
            # Try French first, then English
            try:
                text = r.recognize_google(audio, language="fr-FR")
            except:
                text = r.recognize_google(audio, language="en-US")
                
            return text
    except Exception as e:
        st.error(f"Error recording audio: {str(e)}")
        return None

def process_query(query: str, ai_service: AIService) -> str:
    """Process user query using AI"""
    # Create context from database
    db_context = get_database_context()
    
    # Create prompt with context
    prompt = f"""
    You are a helpful assistant with access to the following database information:
    {db_context}
    
    User query: {query}
    
    Please provide a helpful response based on the available data. If you need to query specific information,
    you can use SQL-like syntax which will be interpreted appropriately.
    
    Response should be in the same language as the query (French or English).
    """
    
    try:
        response = ai_service.generate_database_response(prompt)
        return response
    except Exception as e:
        return f"Error processing query: {str(e)}"

def get_database_context() -> str:
    """Get relevant context from database"""
    db_info = {}
    
    # Get product statistics
    products = CatalogService.get_catalogs()
    if products:
        db_info['total_products'] = len(products)
        db_info['active_products'] = len([p for p in products if p.get('status') == 'active'])
        db_info['product_categories'] = len(set(p.get('category', '') for p in products))
    
    # Format context
    context = f"""
    Database Information:
    - Total Products: {db_info.get('total_products', 0)}
    - Active Products: {db_info.get('active_products', 0)}
    - Product Categories: {db_info.get('product_categories', 0)}
    
    Available Tables:
    - Catalog (products)
    - ImportHistory
    - ValidationRules
    - ArchivedProducts
    """
    
    return context

def render_chat_assistant():
    """Render the chat assistant interface"""
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'ai_service' not in st.session_state:
        st.session_state.ai_service = AIService()

    # Create chat container
    create_chat_container()
    
    # Chat header
    st.markdown("""
        <div class="chat-header">
            <span>Assistant IA</span>
            <button class="audio-button" onclick="toggleAudio()">🎤</button>
        </div>
    """, unsafe_allow_html=True)
    
    # Chat messages
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.write(f"You: {message['content']}")
        else:
            st.write(f"Assistant: {message['content']}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    
    # Text input
    user_input = st.text_input("Message", key="chat_input")
    
    # Audio input
    if st.button("🎤 Record", key="record_button"):
        audio_text = record_audio()
        if audio_text:
            user_input = audio_text
            st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process input
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get AI response
        response = process_query(user_input, st.session_state.ai_service)
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear input
        st.session_state.chat_input = ""
        
        # Rerun to update chat
        st.experimental_rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # JavaScript for audio handling
    st.markdown("""
        <script>
        function toggleAudio() {
            // Toggle audio recording
            const button = document.querySelector('.audio-button');
            if (button.textContent === '🎤') {
                button.textContent = '⏹️';
                // Start recording
                document.querySelector('[data-testid="stButton"] button').click();
            } else {
                button.textContent = '🎤';
                // Stop recording
            }
        }
        </script>
    """, unsafe_allow_html=True)
