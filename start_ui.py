#!/usr/bin/env python3
"""
Simple HTTP server to serve the 1TaskAssistant UI locally
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
UI_DIR = SCRIPT_DIR / "ui"
PORT = 8081

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(UI_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow requests from the UI to the API
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the HTTP server"""
    
    # Check if UI directory exists
    if not UI_DIR.exists():
        print(f"❌ UI directory not found: {UI_DIR}")
        return
    
    # Check if index.html exists
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        print(f"❌ index.html not found: {index_file}")
        return
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 Starting 1TaskAssistant UI server...")
            print(f"📂 Serving files from: {UI_DIR}")
            print(f"🌐 Server running at: http://localhost:{PORT}")
            print(f"📋 API should be running at: http://localhost:7076")
            print(f"")
            print(f"✨ Features:")
            print(f"   • Create and manage tasks with full relationship support")
            print(f"   • Click on table rows to edit items")
            print(f"   • Visual progress tracking and status badges")
            print(f"   • Real-time API testing for all your models")
            print(f"")
            print(f"💡 Make sure your Azure Functions API is running on port 7076")
            print(f"   Run: func start --port 7076")
            print(f"")
            print(f"Press Ctrl+C to stop the server")
            
            # Try to open the browser automatically
            try:
                webbrowser.open(f"http://localhost:{PORT}")
                print(f"🌐 Opening browser automatically...")
            except:
                print(f"📌 Manual: Open http://localhost:{PORT} in your browser")
            
            print(f"")
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")

if __name__ == "__main__":
    start_server()
