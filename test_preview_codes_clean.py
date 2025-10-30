#!/usr/bin/env python3
"""
Clean test script for preview code functionality - handles existing data
Tests the preview code system without needing to deploy to Azure
"""

import os
import sys
import json
import uuid
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

def test_preview_code_retrieval():
    """Test retrieving existing preview codes"""
    print("\n🧪 Testing Preview Code Retrieval...")
    
    try:
        from preview_code_repository import preview_code_repo
        
        # Test: Get all preview codes
        print("  📊 Getting all preview codes...")
        all_codes = preview_code_repo.get_all_preview_codes()
        print(f"  ✅ Found {len(all_codes)} preview codes in database")
        
        if all_codes:
            # Test with the first existing code
            existing_code = all_codes[0]
            print(f"  🔍 Testing with existing code: {existing_code.code}")
            
            # Test retrieval
            retrieved_code = preview_code_repo.get_preview_code(existing_code.code)
            if retrieved_code:
                print(f"  ✅ Successfully retrieved code: {retrieved_code.code}")
                print(f"    - Used: {retrieved_code.is_used}")
                print(f"    - Created: {retrieved_code.created_at}")
                if retrieved_code.used_at:
                    print(f"    - Used At: {retrieved_code.used_at}")
                    print(f"    - Used By: {retrieved_code.used_by_user_id}")
            else:
                print("  ❌ Failed to retrieve existing code")
                return False
        
        # Test: Get stats
        print("  📊 Getting preview code stats...")
        stats = preview_code_repo.get_preview_code_stats()
        print(f"  ✅ Stats retrieved:")
        print(f"    - Total codes: {stats['total_codes']}")
        print(f"    - Used codes: {stats['used_codes']}")
        print(f"    - Available codes: {stats['remaining_codes']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing preview code retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_code_validation():
    """Test validating preview codes"""
    print("\n🧪 Testing Preview Code Validation...")
    
    try:
        from preview_code_repository import preview_code_repo
        
        # Get an unused code if available
        all_codes = preview_code_repo.get_all_preview_codes()
        unused_codes = [code for code in all_codes if not code.is_used]
        
        if unused_codes:
            test_code = unused_codes[0].code
            print(f"  🔓 Testing validation with unused code: {test_code}")
            
            # Test validation and use
            test_user = f"test-user-{uuid.uuid4()}"
            is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
                test_code, test_user
            )
            
            if is_valid:
                print(f"  ✅ Code validation successful: {message}")
                
                # Test using the same code again (should fail)
                print("  🚫 Testing duplicate usage...")
                is_valid_again, message_again, error_code_again = preview_code_repo.validate_and_use_preview_code(
                    test_code, "another-user"
                )
                
                if not is_valid_again and error_code_again == "CODE_ALREADY_USED":
                    print(f"  ✅ Duplicate usage correctly rejected: {message_again}")
                else:
                    print(f"  ❌ Duplicate usage not handled correctly")
                    return False
            else:
                print(f"  ❌ Code validation failed: {message}")
                return False
        else:
            print("  ⚠️ No unused codes available for testing validation")
            # Test with a non-existent code
            fake_code = f"FAKE{uuid.uuid4().hex[:6].upper()}"
            print(f"  🔍 Testing with non-existent code: {fake_code}")
            
            is_valid, message, error_code = preview_code_repo.validate_and_use_preview_code(
                fake_code, "test-user"
            )
            
            if not is_valid and error_code == "CODE_NOT_FOUND":
                print(f"  ✅ Non-existent code correctly rejected: {message}")
            else:
                print(f"  ❌ Non-existent code not handled correctly")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing preview code validation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_preview_code_creation():
    """Test creating new preview codes"""
    print("\n🧪 Testing Preview Code Creation...")
    
    try:
        from preview_code_repository import preview_code_repo
        
        # Generate a unique code
        unique_code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        print(f"  📝 Creating new preview code: {unique_code}")
        
        preview_code = preview_code_repo.create_preview_code(unique_code, "test-system")
        print(f"  ✅ Created preview code: {preview_code.code}")
        
        # Test retrieval of the new code
        print("  🔍 Retrieving newly created code...")
        retrieved_code = preview_code_repo.get_preview_code(unique_code)
        if retrieved_code and retrieved_code.code == unique_code:
            print(f"  ✅ Retrieved newly created code: {retrieved_code.code}")
        else:
            print("  ❌ Failed to retrieve newly created code")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing preview code creation: {e}")
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
        from preview_code_repository import preview_code_repo
        from models import PreviewCodeValidationRequest, PreviewCodeValidationResponse
        
        # Get existing codes for testing
        all_codes = preview_code_repo.get_all_preview_codes()
        
        if all_codes:
            # Test with an existing code
            test_code = all_codes[0].code
            print(f"  📡 Simulating preview code validation endpoint with: {test_code}")
            
            request_data = {
                "code": test_code,
                "user_id": f"api-test-user-{uuid.uuid4()}"
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
        else:
            print("  ⚠️ No codes available for API testing")
        
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
    print("🎫 OneTaskAssistant Preview Code System - Clean Test")
    print("=" * 60)
    
    # Load environment variables
    if not load_local_settings():
        print("❌ Failed to load local settings. Exiting.")
        return False
    
    tests = [
        ("Cosmos DB Connection", test_cosmos_connection),
        ("Pydantic Models", test_models),
        ("Preview Code Retrieval", test_preview_code_retrieval),
        ("Preview Code Creation", test_preview_code_creation),
        ("Preview Code Validation", test_preview_code_validation),
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
    print("📊 Clean Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All clean tests passed!")
        print("\n🚀 Preview code system is working locally!")
        print("\nYou can now:")
        print("1. Start the test server: python test_server.py")
        print("2. Start local Azure Functions: func start")
        print("3. Test endpoints at http://localhost:7071/api/")
    else:
        print(f"\n💥 {failed} test(s) failed. Check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
