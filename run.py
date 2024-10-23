import subprocess
import threading
import time

def run_streamlit():
    subprocess.run(["streamlit", "run", "main.py"])

def run_fastapi():
    subprocess.run(["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()

    # Run Streamlit in the main thread
    run_streamlit()
