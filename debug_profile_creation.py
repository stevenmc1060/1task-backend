#!/usr/bin/env python3
"""
Debug script to test profile creation
"""
import sys
import os
import logging
from datetime import datetime
import json

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from models import UserProfile, CreateUserProfileRequest, DocumentType
    from cosmos_config import cosmos_manager
    from user_profile_repository import user_profile_repo
    
    print("✓ Successfully imported all modules")
    
    # Test CosmosDB connection
    print("\n=== Testing CosmosDB Connection ===")
    cosmos_manager.initialize()
    print("✓ CosmosDB initialized successfully")
    
    # Test profile creation
    print("\n=== Testing Profile Creation ===")
    
    # Create test request
    test_request = CreateUserProfileRequest(
        display_name="Test User",
        email="test@example.com"
    )
    
    user_id = "test-user-debug-123"
    
    # Try to delete existing profile first (if any)
    try:
        existing_profile = user_profile_repo.get_user_profile(user_id)
        if existing_profile:
            user_profile_repo.delete_user_profile(user_id)
            print(f"✓ Deleted existing profile for {user_id}")
    except Exception as e:
        print(f"Note: Could not delete existing profile (may not exist): {e}")
    
    # Test profile creation
    try:
        profile = user_profile_repo.create_user_profile(user_id, test_request)
        print("✓ Profile created successfully")
        
        # Test to_cosmos_dict
        profile_dict = profile.to_cosmos_dict()
        print("✓ to_cosmos_dict() works")
        
        # Test serialization
        from function_app import serialize_datetimes
        serialized_profile = serialize_datetimes(profile_dict)
        json_str = json.dumps(serialized_profile)
        print("✓ JSON serialization works")
        print(f"Profile JSON length: {len(json_str)} characters")
        
        # Clean up
        user_profile_repo.delete_user_profile(user_id)
        print("✓ Test profile cleaned up")
        
    except Exception as e:
        print(f"✗ Profile creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n=== All Tests Passed ===")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
