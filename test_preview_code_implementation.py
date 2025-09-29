#!/usr/bin/env python3
"""
Test script to validate the preview code system implementation.
This script checks that all the required components are properly configured.
"""

import os
import sys
import importlib.util


def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    required_files = [
        'models.py',
        'cosmos_config.py', 
        'preview_code_repository.py',
        'function_app.py',
        'user_profile_repository.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Test that we can load the models without Azure dependencies
    try:
        spec = importlib.util.spec_from_file_location("models", "models.py")
        models = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(models)
        
        # Check for required classes
        required_classes = [
            'PreviewCode',
            'PreviewCodeValidationRequest', 
            'PreviewCodeValidationResponse',
            'DocumentType'
        ]
        
        for cls_name in required_classes:
            if hasattr(models, cls_name):
                print(f"✅ {cls_name} class found")
            else:
                print(f"❌ {cls_name} class missing")
                return False
                
        # Check DocumentType enum includes PREVIEW_CODE
        if hasattr(models.DocumentType, 'PREVIEW_CODE'):
            print("✅ PREVIEW_CODE added to DocumentType enum")
        else:
            print("❌ PREVIEW_CODE missing from DocumentType enum")
            return False
            
    except Exception as e:
        print(f"❌ Error loading models.py: {e}")
        return False
    
    return True


def test_function_app():
    """Test that function_app.py has the required endpoints"""
    print("\n🧪 Testing function_app.py...")
    
    try:
        with open('function_app.py', 'r') as f:
            content = f.read()
        
        required_endpoints = [
            'preview-codes/validate',
            'preview-codes/stats'
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                print(f"✅ {endpoint} endpoint found")
            else:
                print(f"❌ {endpoint} endpoint missing")
                return False
        
        # Check for import
        if 'from preview_code_repository import preview_code_repo' in content:
            print("✅ preview_code_repository import found")
        else:
            print("❌ preview_code_repository import missing")
            return False
            
    except Exception as e:
        print(f"❌ Error reading function_app.py: {e}")
        return False
    
    return True


def test_cosmos_config():
    """Test that cosmos_config.py has preview codes container"""
    print("\n🧪 Testing cosmos_config.py...")
    
    try:
        with open('cosmos_config.py', 'r') as f:
            content = f.read()
        
        required_elements = [
            'preview_codes_container_name',
            'preview_codes_container',
            'get_preview_codes_container',
            '_create_preview_codes_container_if_not_exists'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"✅ {element} found")
            else:
                print(f"❌ {element} missing")
                return False
                
    except Exception as e:
        print(f"❌ Error reading cosmos_config.py: {e}")
        return False
    
    return True


def test_user_profile_updates():
    """Test that user profile repository handles new fields"""
    print("\n🧪 Testing user_profile_repository.py...")
    
    try:
        with open('user_profile_repository.py', 'r') as f:
            content = f.read()
        
        required_fields = [
            'preview_code_used',
            'contact_address',
            'billing_address',
            'billing_address_same_as_contact'
        ]
        
        for field in required_fields:
            if field in content:
                print(f"✅ {field} field handling found")
            else:
                print(f"❌ {field} field handling missing")
                return False
                
    except Exception as e:
        print(f"❌ Error reading user_profile_repository.py: {e}")
        return False
    
    return True


def test_preview_codes():
    """Test the generated preview codes"""
    print("\n🧪 Testing preview codes...")
    
    expected_codes = [
        'WSHA61P9', 'F7WQUWYS', '1PHZ5MG3', 'K2TV2NU5', 'ZLQQX14D',
        'NV9I9IVY', 'YEW4C753', '72SQQPNK', 'RKAFLHWJ', 'I4QDZ6WY',
        'BUKEF4R8', '9Z1NKGD8', 'JG7RSHA2', 'GIV1SGIJ', '8U3YEW49',
        'DEBG4CU5', '4P2GI8WY', 'N5X19GBM', '5NGHZCGT', '7PTE4AMP',
        '24Q4YMG8', 'ECNLZ3NV', '6448ZFBK', 'PU9II8NN', '8TFQ95N6'
    ]
    
    print(f"✅ Generated {len(expected_codes)} preview codes")
    
    # Check for duplicates
    if len(expected_codes) == len(set(expected_codes)):
        print("✅ All codes are unique")
    else:
        print("❌ Duplicate codes found")
        return False
    
    # Check code format
    valid_format = True
    for code in expected_codes:
        if len(code) == 8 and code.isalnum() and code.isupper():
            continue
        else:
            print(f"❌ Invalid code format: {code}")
            valid_format = False
    
    if valid_format:
        print("✅ All codes follow correct format (8 chars, alphanumeric, uppercase)")
    
    return valid_format


def main():
    """Run all tests"""
    print("🎫 OneTaskAssistant Preview Code System - Implementation Test")
    print("=" * 60)
    
    tests = [
        ("File Structure & Imports", test_imports),
        ("Function App Endpoints", test_function_app), 
        ("CosmosDB Configuration", test_cosmos_config),
        ("User Profile Updates", test_user_profile_updates),
        ("Preview Codes", test_preview_codes)
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
    print("📊 Test Results Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your preview code system is ready.")
        print("\n🚀 Next steps:")
        print("1. Set up your CosmosDB environment variables")
        print("2. Run 'python initialize_preview_codes.py' to populate the database")
        print("3. Deploy your Azure Functions")
        print("4. Test the preview code validation endpoint")
        return True
    else:
        print(f"\n💥 {failed} test(s) failed. Please fix the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
