import streamlit as st
import pandas as pd
from datetime import datetime
import json
from models.database import SessionLocal, Catalog

def render_sync_monitor():
    st.header("Real-time Sync Monitor")
    
    # Add JavaScript for WebSocket connection with auto-reconnect
    st.markdown("""
        <script>
            let ws;
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 5;
            const reconnectDelay = 5000;
            
            function connect() {
                ws = new WebSocket('ws://0.0.0.0:8765');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    const syncStatusElement = document.getElementById('sync-status');
                    if (syncStatusElement) {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `sync-message ${data.type}`;
                        
                        let messageContent = `
                            <div class="message-content">
                                <strong>${data.message}</strong>
                                <small>${new Date(data.timestamp).toLocaleString()}</small>
                            </div>
                        `;
                        
                        if (data.stats) {
                            messageContent += `
                                <div class="stats-content">
                                    <span>Total Records: ${data.stats.total_records}</span>
                                    <span>Recent Updates: ${data.stats.recent_updates}</span>
                                </div>
                            `;
                        }
                        
                        messageDiv.innerHTML = messageContent;
                        syncStatusElement.insertBefore(messageDiv, syncStatusElement.firstChild);
                        
                        // Keep only last 10 messages
                        while (syncStatusElement.children.length > 10) {
                            syncStatusElement.removeChild(syncStatusElement.lastChild);
                        }
                    }
                    
                    // Update metrics if stats are available
                    if (data.stats) {
                        const totalRecordsElement = document.querySelector('[data-testid="stMetricValue"]:first-child');
                        const recentUpdatesElement = document.querySelector('[data-testid="stMetricValue"]:last-child');
                        
                        if (totalRecordsElement) {
                            totalRecordsElement.textContent = data.stats.total_records;
                        }
                        if (recentUpdatesElement) {
                            recentUpdatesElement.textContent = data.stats.recent_updates;
                        }
                    }
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    tryReconnect();
                };
                
                ws.onclose = function() {
                    console.log('WebSocket connection closed');
                    tryReconnect();
                };
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                    reconnectAttempts = 0;
                    // Send periodic ping to keep connection alive
                    setInterval(() => {
                        if (ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({type: 'ping'}));
                        }
                    }, 30000);
                };
            }
            
            function tryReconnect() {
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    console.log(`Reconnecting... Attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
                    setTimeout(connect, reconnectDelay);
                } else {
                    console.log('Max reconnection attempts reached');
                    const syncStatusElement = document.getElementById('sync-status');
                    if (syncStatusElement) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'sync-message error';
                        errorDiv.innerHTML = `
                            <strong>Connection lost</strong>
                            <small>Please refresh the page to reconnect</small>
                        `;
                        syncStatusElement.insertBefore(errorDiv, syncStatusElement.firstChild);
                    }
                }
            }
            
            // Initial connection
            connect();
        </script>
        
        <style>
            .sync-message {
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
                border-left: 4px solid #ccc;
            }
            .sync-message.update {
                background-color: #e7f3ff;
                border-left-color: #2196f3;
            }
            .sync-message.error {
                background-color: #ffe7e7;
                border-left-color: #f44336;
            }
            .sync-message.connection {
                background-color: #e8f5e9;
                border-left-color: #4caf50;
            }
            .sync-message.status {
                background-color: #f5f5f5;
                border-left-color: #9e9e9e;
            }
            .sync-message small {
                display: block;
                font-size: 0.8em;
                color: #666;
                margin-top: 5px;
            }
            .stats-content {
                margin-top: 8px;
                display: flex;
                gap: 20px;
                font-size: 0.9em;
                color: #555;
            }
            .message-content {
                display: flex;
                flex-direction: column;
            }
        </style>
        
        <div id="sync-status"></div>
    """, unsafe_allow_html=True)
    
    # Display sync statistics
    st.subheader("Sync Statistics")
    
    # Get initial sync statistics from database
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
        col1, col2 = st.columns(2)
        col1.metric("Total Records", stats["Total Records"])
        col2.metric("Recent Updates", stats["Recent Updates"])
        
    finally:
        db.close()
