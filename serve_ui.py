#!/usr/bin/env python3
"""
Simple HTTP server to serve the test UI locally
"""
import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support for API calls"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    """Start the HTTP server and open the UI in browser"""
    print(f"🌐 Starting HTTP server on port {PORT}")
    print(f"📁 Serving files from: {DIRECTORY}")
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"✅ Server running at: http://localhost:{PORT}")
        print(f"🎯 UI available at: http://localhost:{PORT}/test-ui.html")
        print("📱 Make sure your Azure Functions is running on port 7071")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Open browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}/test-ui.html')
            print("🚀 Opening UI in your default browser...")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please manually open: http://localhost:{PORT}/test-ui.html")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")

if __name__ == "__main__":
    main()
