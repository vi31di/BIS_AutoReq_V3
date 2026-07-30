import subprocess
import webbrowser
import time
import sys

def main():
    print("Starting BIS LIS Compliance Lookup System...")
    
    # 1. Start Backend FastAPI Server
    backend = subprocess.Popen(
        ["./.venv/bin/uvicorn", "api.index:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # 2. Start Frontend Vite Server
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd="../frontend",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # 3. Give servers a brief moment to boot
    time.sleep(2.0)
    
    # 4. Launch login screen (Vite opens index.html which redirects to login.html if not authenticated)
    login_url = "http://localhost:3000/pages/login.html"
    print(f"Launching web interface at: {login_url}")
    webbrowser.open(login_url)
    
    print("\n--- System Status: RUNNING ---")
    print("Press Ctrl+C in this terminal window to stop the servers.")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print("System stopped.")

if __name__ == "__main__":
    main()
