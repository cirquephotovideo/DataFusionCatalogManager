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

async def init_background_services():
    """Initialize background services"""
    sync_service.start_scheduler()
    server = await start_websocket_server()
    try:
        await asyncio.Future()  # run forever
    finally:
        sync_service.stop_scheduler()
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    # Start background services in a separate thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the background services in a separate thread
    background_task = loop.create_task(init_background_services())
    
    try:
        # Run the Streamlit app
        main()
    except KeyboardInterrupt:
        # Ensure clean shutdown
        background_task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
