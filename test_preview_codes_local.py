#!/usr/bin/env python3
"""
Local test script for preview code functionality
Tests the preview code system without needing to deploy to Azure
"""

import os
import sys
import json
from datetime import datetime

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

def test_preview_code_repository():
    """Test the preview code repository functionality"""
    print("\n🧪 Testing Preview Code Repository...")
    
    try:
        from preview_code_repository import preview_code_repo
        
        # Test 1: Create a test preview code
        print("  📝 Creating test preview code...")
        test_code = "TEST1234"
        preview_code = preview_code_repo.create_preview_code(test_code, "test-user")
        print(f"  ✅ Created preview code: {preview_code.code}")
        
        # Test 2: Retrieve the preview code
        print("  🔍 Retrieving preview code...")
        retrieved_code = preview_code_repo.get_preview_code(test_code)
        if retrieved_code and retrieved_code.code == test_code:
            print(f"  ✅ Retrieved preview code: {retrieved_code.code}")
        else:
            print("  ❌ Failed to retrieve preview code")
            return False
        
        # Test 3: Validate and use the preview code
        print("  🔓 Validating and using preview code...")
        is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
            test_code, "test-user-123"
        )
        
        if is_valid:
            print(f"  ✅ Code validation successful: {message}")
        else:
            print(f"  ❌ Code validation failed: {message}")
            return False
        
        # Test 4: Try to use the same code again (should fail)
        print("  🚫 Testing duplicate usage...")
        is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
            test_code, "another-user"
        )
        
        if not is_valid and error_code == "CODE_ALREADY_USED":
            print(f"  ✅ Duplicate usage correctly rejected: {message}")
        else:
            print(f"  ❌ Duplicate usage not handled correctly")
            return False
        
        # Test 5: Get stats
        print("  📊 Getting preview code stats...")
        stats = preview_code_repo.get_preview_code_stats()
        print(f"  ✅ Stats retrieved - Total codes: {stats['total_codes']}, Used: {stats['used_codes']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing preview code repository: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test the Pydantic models"""
    print("\n🧪 Testing Pydantic Models...")
    
    try:
        from models import PreviewCode, PreviewCodeValidationRequest, PreviewCodeValidationResponse, DocumentType
        
        # Test PreviewCode model
        print("  📋 Testing PreviewCode model...")
        code = PreviewCode(
            code="MODEL123",
            user_id="test-user",
            is_used=False
        )
        
        # Test serialization
        code_dict = code.to_cosmos_dict()
        print(f"  ✅ PreviewCode serialization works")
        
        # Test deserialization
        restored_code = PreviewCode.from_cosmos_dict(code_dict)
        print(f"  ✅ PreviewCode deserialization works")
        
        # Test validation request/response
        print("  📨 Testing request/response models...")
        request = PreviewCodeValidationRequest(code="TEST123", user_id="user123")
        response = PreviewCodeValidationResponse(valid=True, message="Success")
        
        print(f"  ✅ Request model: {request.code}")
        print(f"  ✅ Response model: {response.valid}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing models: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cosmos_connection():
    """Test basic Cosmos DB connection"""
    print("\n🧪 Testing Cosmos DB Connection...")
    
    try:
        from cosmos_config import cosmos_manager
        
        # Test getting the preview codes container
        print("  🗄️ Getting preview codes container...")
        container = cosmos_manager.get_preview_codes_container()
        
        if container:
            print("  ✅ Successfully connected to preview codes container")
            return True
        else:
            print("  ❌ Failed to get preview codes container")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing Cosmos connection: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints_simulation():
    """Simulate API endpoint calls"""
    print("\n🧪 Testing API Endpoints (Simulation)...")
    
    try:
        # Import the validation function logic
        from preview_code_repository import preview_code_repo
        from models import PreviewCodeValidationRequest, PreviewCodeValidationResponse
        
        # Create a test code first
        test_code = "API12345"
        preview_code_repo.create_preview_code(test_code, "system")
        
        # Simulate POST /api/preview-codes/validate
        print("  📡 Simulating preview code validation endpoint...")
        
        request_data = {
            "code": test_code,
            "user_id": "api-test-user"
        }
        
        validation_request = PreviewCodeValidationRequest(**request_data)
        
        # Call the repository method
        is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
            validation_request.code,
            validation_request.user_id
        )
        
        response = PreviewCodeValidationResponse(
            valid=is_valid,
            message=message,
            error=error_code,
            code_id=validation_request.code if is_valid else None
        )
        
        print(f"  ✅ API response: {response.model_dump()}")
        
        # Simulate GET /api/preview-codes/stats
        print("  📊 Simulating stats endpoint...")
        stats = preview_code_repo.get_preview_code_stats()
        print(f"  ✅ Stats response: {json.dumps(stats, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing API simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all local tests"""
    print("🎫 OneTaskAssistant Preview Code System - Local Test")
    print("=" * 60)
    
    # Load environment variables
    if not load_local_settings():
        print("❌ Failed to load local settings. Exiting.")
        return False
    
    tests = [
        ("Cosmos DB Connection", test_cosmos_connection),
        ("Pydantic Models", test_models),
        ("Preview Code Repository", test_preview_code_repository),
        ("API Endpoints Simulation", test_api_endpoints_simulation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
                failed += 1
        except Exception as e:
            print(f"💥 {test_name} - ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 Local Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All local tests passed!")
        print("\n🚀 Preview code system is working locally!")
        print("\nYou can now:")
        print("1. Initialize preview codes: python initialize_preview_codes.py")
        print("2. Start local Azure Functions: func start")
        print("3. Test endpoints at http://localhost:7071/api/")
    else:
        print(f"\n💥 {failed} test(s) failed. Check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
