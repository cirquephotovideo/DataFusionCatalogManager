import streamlit as st
import pandas as pd
from datetime import datetime
import json
from models.database import SessionLocal, Catalog

def render_sync_monitor():
    st.header("Real-time Sync Monitor")
    
    # Add JavaScript for WebSocket connection
    st.markdown("""
        <script>
            const ws = new WebSocket('ws://0.0.0.0:8765');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const syncStatusElement = document.getElementById('sync-status');
                if (syncStatusElement) {
                    syncStatusElement.innerHTML = `
                        <div class="sync-message ${data.type}">
                            ${data.message}
                            <small>${new Date(data.timestamp).toLocaleString()}</small>
                        </div>
                    `;
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = function() {
                console.log('WebSocket connection closed');
            };
        </script>
        
        <style>
            .sync-message {
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
            }
            .sync-message.update {
                background-color: #e7f3ff;
            }
            .sync-message.error {
                background-color: #ffe7e7;
            }
            .sync-message small {
                display: block;
                font-size: 0.8em;
                color: #666;
            }
        </style>
        
        <div id="sync-status"></div>
    """, unsafe_allow_html=True)
    
    # Display sync statistics
    st.subheader("Sync Statistics")
    
    # Get sync statistics from database
    db = SessionLocal()
    try:
        stats = {
            "Last Sync": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "Total Records": db.query(Catalog).count(),
            "Recent Updates": db.query(Catalog).filter(
                Catalog.updated_at >= datetime.utcnow()
            ).count()
        }
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Last Sync", stats["Last Sync"])
        col2.metric("Total Records", stats["Total Records"])
        col3.metric("Recent Updates", stats["Recent Updates"])
        
    finally:
        db.close()
