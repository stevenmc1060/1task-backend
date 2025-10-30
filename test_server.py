#!/usr/bin/env python3
"""
Simple HTTP test server for preview code functionality
This script creates a minimal Flask server to test our preview code endpoints
without requiring the full Azure Functions runtime
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables from local.settings.json
def load_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            
        for key, value in settings.get('Values', {}).items():
            os.environ[key] = value
            
        print("✅ Loaded local settings")
        return True
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")
        return False

# Load settings first
if not load_local_settings():
    sys.exit(1)

# Now import our modules after environment is set
from preview_code_repository import preview_code_repo
from models import PreviewCodeValidationRequest, PreviewCodeValidationResponse

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "1TaskAssistant Preview Code Service",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/preview-codes/validate', methods=['POST'])
def validate_preview_code():
    """Validate a preview code for early access"""
    try:
        # Parse request body
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "valid": False,
                "message": "Request body is required",
                "error": "MISSING_BODY"
            }), 400
        
        try:
            validation_request = PreviewCodeValidationRequest(**request_data)
        except Exception as e:
            return jsonify({
                "valid": False,
                "message": f"Invalid request data: {str(e)}",
                "error": "INVALID_REQUEST"
            }), 400
        
        # Validate the preview code
        is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
            validation_request.code,
            validation_request.user_id
        )
        
        # Create response
        response = PreviewCodeValidationResponse(
            valid=is_valid,
            message=message,
            error=error_code,
            code_id=validation_request.code if is_valid else None
        )
        
        return jsonify(response.model_dump())
        
    except Exception as e:
        print(f"Error validating preview code: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "valid": False,
            "message": "Server error validating preview code",
            "error": "SERVER_ERROR"
        }), 500

@app.route('/api/preview-codes/stats', methods=['GET'])
def get_preview_code_stats():
    """Get preview code usage statistics"""
    try:
        stats = preview_code_repo.get_preview_code_stats()
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting preview code stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to get preview code statistics"}), 500

@app.route('/api/preview-codes/create', methods=['POST'])
def create_preview_code():
    """Create a new preview code (admin endpoint for testing)"""
    try:
        request_data = request.get_json()
        code = request_data.get('code')
        user_id = request_data.get('user_id', 'system')
        
        if not code:
            return jsonify({"error": "Code is required"}), 400
        
        preview_code = preview_code_repo.create_preview_code(code, user_id)
        
        return jsonify({
            "success": True,
            "code": preview_code.code,
            "created_at": preview_code.created_at.isoformat()
        })
        
    except Exception as e:
        print(f"Error creating preview code: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to create preview code"}), 500

@app.route('/api/preview-codes', methods=['GET'])
def list_preview_codes():
    """List all preview codes (admin endpoint for testing)"""
    try:
        codes = preview_code_repo.get_all_preview_codes()
        
        return jsonify({
            "codes": [
                {
                    "code": code.code,
                    "is_used": code.is_used,
                    "used_by": code.used_by_user_id,
                    "used_at": code.used_at.isoformat() if code.used_at else None,
                    "created_at": code.created_at.isoformat()
                }
                for code in codes
            ]
        })
        
    except Exception as e:
        print(f"Error listing preview codes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to list preview codes"}), 500

if __name__ == '__main__':
    print("🎫 1TaskAssistant Preview Code Test Server")
    print("=" * 50)
    print("Server will start on http://localhost:5000")
    print("Available endpoints:")
    print("  GET  /health")
    print("  POST /api/preview-codes/validate")
    print("  GET  /api/preview-codes/stats")
    print("  POST /api/preview-codes/create (admin)")
    print("  GET  /api/preview-codes (admin)")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
