import streamlit as st

def render_chat_widget():
    """Render chat widget"""
    # Initialize chat state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Chat container
    with st.sidebar:
        st.header("Chat Assistant")

        # Quick actions
        st.markdown("### Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            st.button("Products")
            st.button("Import/Export")
        with col2:
            st.button("Sync")
            st.button("Help")
