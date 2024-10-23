import streamlit as st
import asyncio
from components.catalog_manager import render_catalog_manager
from components.manufacturer_manager import render_manufacturer_manager
from components.matching_engine import render_matching_engine
from components.ftp_manager import render_ftp_manager
from components.sync_monitor import render_sync_monitor
from services.websocket_handler import start_websocket_server
from services.sync_service import sync_service
import threading

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

def run_async_services():
    """Run async services in a separate thread"""
    async def start_services():
        sync_service.start_scheduler()
        server = await start_websocket_server()
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            sync_service.stop_scheduler()
            server.close()
            await server.wait_closed()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        loop.close()

if __name__ == "__main__":
    # Start background services in a separate thread
    services_thread = threading.Thread(target=run_async_services, daemon=True)
    services_thread.start()
    
    # Run the Streamlit app
    main()
