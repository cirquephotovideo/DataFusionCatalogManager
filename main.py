import streamlit as st
import asyncio
from components.catalog_manager import render_catalog_manager
from components.manufacturer_manager import render_manufacturer_manager
from components.matching_engine import render_matching_engine
from components.ftp_manager import render_ftp_manager
from components.sync_monitor import render_sync_monitor
from services.websocket_handler import start_websocket_server
from services.sync_service import sync_service

st.set_page_config(
    page_title="Catalog Management System",
    page_icon="📊",
    layout="wide"
)

async def init_sync_service():
    """Initialize sync service and WebSocket server"""
    sync_service.start_scheduler()
    server = await start_websocket_server()
    await server.wait_closed()

def main():
    st.title("Catalog Management System")
    
    # Navigation
    menu = ["Catalog Management", "Manufacturer Management", 
            "Product Matching", "FTP Data Retrieval", "Sync Monitor"]
    choice = st.sidebar.selectbox("Navigate", menu)
    
    if choice == "Catalog Management":
        render_catalog_manager()
    elif choice == "Manufacturer Management":
        render_manufacturer_manager()
    elif choice == "FTP Data Retrieval":
        render_ftp_manager()
    elif choice == "Sync Monitor":
        render_sync_monitor()
    else:
        render_matching_engine()

if __name__ == "__main__":
    # Start sync service and WebSocket server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(init_sync_service())
    
    # Run the Streamlit app
    main()
