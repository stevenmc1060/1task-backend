#!/usr/bin/env python3
"""
Test script to verify the PATCH endpoint fix is working
Run this after deploying the backend changes.
"""

import requests
import json

# Backend URL
BASE_URL = "https://1task-backend-api-gse0fsgngtfxhjc6.southcentralus-01.azurewebsites.net/api"

def test_patch_fix():
    """Test the PATCH endpoint to verify our fix works"""
    
    print("🔧 Testing PATCH endpoint fix...")
    
    # First, get the list of notes to find one to update
    print("\n1. Getting existing notes...")
    response = requests.get(f"{BASE_URL}/notes", params={"user_id": "dev-user-localhost"})
    
    if response.status_code != 200:
        print(f"❌ Failed to get notes: {response.status_code} - {response.text}")
        return False
    
    notes = response.json().get("notes", [])
    if not notes:
        print("❌ No notes found to test with")
        return False
    
    note_to_update = notes[0]
    note_id = note_to_update["id"]
    print(f"✅ Found note to update: {note_id}")
    
    # Test PATCH request
    print("\n2. Testing PATCH request...")
    update_data = {
        "user_id": "dev-user-localhost",
        "title": f"Updated Title - {note_to_update.get('title', 'Untitled')} ✨",
        "content": f"{note_to_update.get('content', '')}\n\n**Update test successful!** 🎉"
    }
    
    response = requests.patch(
        f"{BASE_URL}/notes/{note_id}",
        headers={"Content-Type": "application/json"},
        json=update_data
    )
    
    if response.status_code == 200:
        print("✅ PATCH request successful!")
        updated_note = response.json()
        print(f"   Updated title: {updated_note.get('title', 'N/A')}")
        return True
    else:
        print(f"❌ PATCH request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_comprehensive():
    """Run comprehensive tests"""
    print("🧪 Running comprehensive backend tests...\n")
    
    # Test GET
    print("Testing GET /notes...")
    response = requests.get(f"{BASE_URL}/notes", params={"user_id": "dev-user-localhost"})
    print(f"GET status: {response.status_code}")
    
    # Test POST
    print("\nTesting POST /notes...")
    new_note = {
        "user_id": "dev-user-localhost",
        "title": "Test Note",
        "content": "This is a test note",
        "tags": ["test"],
        "is_pinned": False,
        "folder_id": None,
        "attachments": []
    }
    response = requests.post(f"{BASE_URL}/notes", headers={"Content-Type": "application/json"}, json=new_note)
    print(f"POST status: {response.status_code}")
    
    if response.status_code == 201:
        created_note = response.json()
        note_id = created_note["id"]
        print(f"Created note ID: {note_id}")
        
        # Test PATCH
        print(f"\nTesting PATCH /notes/{note_id}...")
        update_data = {
            "user_id": "dev-user-localhost",
            "title": "Updated Test Note ✅",
            "content": "This note has been updated successfully!"
        }
        response = requests.patch(f"{BASE_URL}/notes/{note_id}", headers={"Content-Type": "application/json"}, json=update_data)
        print(f"PATCH status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ All tests passed! The fix is working.")
        else:
            print(f"❌ PATCH failed: {response.text}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_comprehensive()
