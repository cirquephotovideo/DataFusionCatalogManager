import streamlit as st
from services.user_service import UserService

def init_auth():
    """Initialize authentication state"""
    if 'user_service' not in st.session_state:
        st.session_state.user_service = UserService()
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None

def render_login():
    """Render login form"""
    st.title("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            token = st.session_state.user_service.login(username, password)
            if token:
                st.session_state.auth_token = token
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def render_user_management():
    """Render user management interface"""
    st.header("User Management")
    
    # Add new user
    with st.form("add_user"):
        st.subheader("Add New User")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        
        if st.form_submit_button("Add User"):
            if username and password:
                if st.session_state.user_service.create_user(username, password, role):
                    st.success(f"User {username} created successfully")
                else:
                    st.error("Username already exists")
            else:
                st.error("Username and password are required")

    # List users
    st.subheader("Users")
    users = st.session_state.user_service.get_users()
    
    for user in users:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(f"**{user['username']}**")
        with col2:
            st.write(f"Role: {user['role']}")
        with col3:
            st.write(f"Last login: {user['last_login'] or 'Never'}")
        with col4:
            if user['username'] != "admin":
                if st.button("Delete", key=f"delete_{user['username']}"):
                    if st.session_state.user_service.delete_user(user['username']):
                        st.success(f"User {user['username']} deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")

def render_change_password():
    """Render change password form"""
    st.header("Change Password")
    
    with st.form("change_password"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password"):
            if new_password != confirm_password:
                st.error("New passwords don't match")
            else:
                user_info = st.session_state.user_service.verify_session(st.session_state.auth_token)
                if st.session_state.user_service.change_password(user_info["username"], old_password, new_password):
                    st.success("Password changed successfully")
                else:
                    st.error("Current password is incorrect")

def check_auth():
    """Check if user is authenticated and return user info"""
    init_auth()
    
    if not st.session_state.auth_token:
        render_login()
        st.stop()
    
    user_info = st.session_state.user_service.verify_session(st.session_state.auth_token)
    if not user_info:
        st.session_state.auth_token = None
        render_login()
        st.stop()
    
    return user_info
