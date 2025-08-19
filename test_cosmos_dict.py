#!/usr/bin/env python3
"""
Quick test to see what to_cosmos_dict produces
"""
import sys
import os
import json

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import UserProfile, CreateUserProfileRequest, DocumentType

# Create test request
test_request = CreateUserProfileRequest(
    display_name="Test User",
    email="test@example.com"
)

user_id = "test-user-debug-123"

# Create new profile
profile = UserProfile(
    user_id=user_id,
    display_name=test_request.display_name,
    email=test_request.email,
    first_name=test_request.first_name,
    last_name=test_request.last_name,
    location=test_request.location,
    timezone=test_request.timezone,
    bio=test_request.bio,
    preferred_greeting=test_request.preferred_greeting,
    communication_style=test_request.communication_style,
    oauth_provider=test_request.oauth_provider,
    oauth_id=test_request.oauth_id,
)

print("Profile object created:")
print(f"- id: {profile.id}")
print(f"- user_id: {profile.user_id}")

# Test to_cosmos_dict
profile_dict = profile.to_cosmos_dict()
print("\nto_cosmos_dict() result:")
print(json.dumps(profile_dict, indent=2))

print(f"\nDictionary contains id key: {'id' in profile_dict}")
if 'id' in profile_dict:
    print(f"ID value: {profile_dict['id']}")
