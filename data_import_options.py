import streamlit as st

def render_data_import_dashboard():
    # Custom styles for dark theme and cards
    st.markdown("""
        <style>
        /* Card container */
        div[data-testid="stHorizontalBlock"] {
            gap: 1rem;
            padding: 1rem 0;
        }
        
        /* Card styling */
        div.element-container div.stButton > button {
            background-color: white;
            color: #333;
            border: none;
            border-radius: 10px;
            padding: 1.5rem;
            cursor: pointer;
            transition: transform 0.2s;
            min-height: 180px;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            font-size: 1.2rem;
            white-space: pre-line;
        }
        
        div.element-container div.stButton > button:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        /* Configuration screen styling */
        .config-container {
            background-color: #1a1f24;
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
        }

        .config-section {
            background-color: #242a30;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .config-title {
            color: white;
            font-size: 1.2rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #363c42;
            padding-bottom: 0.5rem;
        }

        /* Form styling */
        .stTextInput > div > div {
            background-color: #2a3138;
            border-color: #363c42;
            color: white;
        }

        .stSelectbox > div > div {
            background-color: #2a3138;
            border-color: #363c42;
            color: white;
        }

        /* Button styling */
        .primary-button {
            background-color: #3498db;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .primary-button:hover {
            background-color: #2980b9;
        }

        .secondary-button {
            background-color: #2a3138;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            border: 1px solid #363c42;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .secondary-button:hover {
            background-color: #363c42;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Choose how you want to import your data:")

    # Initialize session state
    if 'selected_method' not in st.session_state:
        st.session_state.selected_method = None

    # Create a 2x2 grid layout
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        if st.button("📁\n\nUpload files\n\n• CSV, XLS, XML", key="file_upload"):
            st.session_state.selected_method = "file_upload"

    with col2:
        if st.button("🔗\n\nAutomated FTP/SFTP\n\n• Monitored folders", key="transfer_protocol"):
            st.session_state.selected_method = "transfer_protocol"

    with col3:
        if st.button("🌐\n\nExtract data\n\n• From websites", key="web_scraping"):
            st.session_state.selected_method = "web_scraping"

    with col4:
        if st.button("🔌\n\nReal-time sync\n\n• External sources", key="api"):
            st.session_state.selected_method = "api"

    # Show configuration based on selection
    if st.session_state.selected_method:
        st.markdown("---")
        if st.session_state.selected_method == "file_upload":
            render_file_upload_config()
        elif st.session_state.selected_method == "transfer_protocol":
            render_transfer_protocol_config()
        elif st.session_state.selected_method == "web_scraping":
            render_web_scraping_config()
        elif st.session_state.selected_method == "api":
            render_api_config()

def render_file_upload_config():
    st.markdown('<div class="config-container">', unsafe_allow_html=True)
    st.header("File Upload Configuration")
    
    # File Upload Section
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">1. Choose File to Upload</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop your file here or click to browse", 
                                   type=['csv', 'xls', 'xlsx', 'xml'])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        # File Type Selection
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        st.markdown('<div class="config-title">2. File Type Configuration</div>', unsafe_allow_html=True)
        file_type = st.selectbox("Select file type:", 
                                ["Auto-detect", "CSV", "Excel", "XML"])
        st.markdown('</div>', unsafe_allow_html=True)

        # Column Mapping
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        st.markdown('<div class="config-title">3. Column Mapping</div>', unsafe_allow_html=True)
        st.markdown("Map your file columns to catalog fields:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("File Column", "Product_Name")
        with col2:
            st.selectbox("Catalog Field", ["Product Name", "SKU", "Price", "Stock"])
        st.markdown('</div>', unsafe_allow_html=True)

        # Preview & Validation
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        st.markdown('<div class="config-title">4. Preview & Validation</div>', unsafe_allow_html=True)
        if st.button("Preview Data", type="primary"):
            st.dataframe({
                'Product Name': ['Sample Product 1', 'Sample Product 2'],
                'Price': ['$99.99', '$149.99'],
                'Stock': [50, 25]
            })
        st.markdown('</div>', unsafe_allow_html=True)

        # Import Controls
        st.markdown('<div class="config-section">', unsafe_allow_html=True)
        st.markdown('<div class="config-title">5. Import Controls</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.button("Save Configuration", type="secondary")
        with col2:
            st.button("Run Import Now", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_transfer_protocol_config():
    st.markdown('<div class="config-container">', unsafe_allow_html=True)
    st.header("Transfer Protocol Configuration")
    
    # Connection Type
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">1. Connection Type</div>', unsafe_allow_html=True)
    connection_type = st.selectbox("Select Protocol:", ["FTP", "SFTP"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Server Settings
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">2. Server Settings</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Server Address")
        st.text_input("Username")
        st.text_input("Directory Path")
    with col2:
        st.text_input("Port")
        st.text_input("Password", type="password")
        st.text_input("File Pattern", placeholder="*.csv")
    st.markdown('</div>', unsafe_allow_html=True)

    # Monitoring Settings
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">3. Monitoring Settings</div>', unsafe_allow_html=True)
    st.checkbox("Enable Automatic Import")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Test Connection", type="secondary")
    with col2:
        st.button("Save Configuration", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_web_scraping_config():
    st.markdown('<div class="config-container">', unsafe_allow_html=True)
    st.header("Web Scraping Configuration")
    
    # URL Configuration
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">1. Target URL</div>', unsafe_allow_html=True)
    st.text_input("Enter URL", placeholder="https://example.com/products")
    st.markdown('</div>', unsafe_allow_html=True)

    # Element Selection
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">2. Element Selection</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Product Name Selector", placeholder=".product-title")
        st.text_input("Price Selector", placeholder=".price-amount")
    with col2:
        st.text_input("Image Selector", placeholder="img.product-image")
        st.button("Test Selectors", type="secondary")
    st.markdown('</div>', unsafe_allow_html=True)

    # Scheduling
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">3. Scheduling</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Frequency", ["Once", "Hourly", "Daily", "Weekly"])
    with col2:
        st.button("Start Scraping", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_api_config():
    st.markdown('<div class="config-container">', unsafe_allow_html=True)
    st.header("API Configuration")
    
    # Endpoint Configuration
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">1. API Endpoint</div>', unsafe_allow_html=True)
    st.text_input("API URL", placeholder="https://api.example.com/v1")
    st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
    st.markdown('</div>', unsafe_allow_html=True)

    # Authentication
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">2. Authentication</div>', unsafe_allow_html=True)
    auth_type = st.selectbox("Authentication Type", 
                            ["None", "Basic Auth", "OAuth", "API Key"])
    if auth_type != "None":
        if auth_type == "Basic Auth":
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Username")
            with col2:
                st.text_input("Password", type="password")
        elif auth_type == "OAuth":
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Client ID")
            with col2:
                st.text_input("Client Secret", type="password")
        else:
            st.text_input("API Key")
    st.markdown('</div>', unsafe_allow_html=True)

    # Connection Test
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown('<div class="config-title">3. Connection Test</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.button("Test Connection", type="secondary")
    with col2:
        st.button("Save Configuration", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
