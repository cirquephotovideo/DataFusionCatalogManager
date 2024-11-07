#!/bin/bash

# Kill any existing streamlit processes
pkill -f streamlit

# Initialize the database
python init_db.py

# Start the application
streamlit run main.py
