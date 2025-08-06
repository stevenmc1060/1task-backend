"""
Simple test script for 1TaskAssistant API
Run this script to test the API endpoints locally
"""
import requests
import json
from datetime import datetime, timedelta

# Base URL for local development
BASE_URL = "http://localhost:7071/api"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_create_task(user_id="test_user_123"):
    """Test creating a new task"""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task created via API",
        "priority": "high",
        "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
        "user_id": user_id,
        "tags": ["test", "api"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        print(f"Create Task: {response.status_code}")
        if response.status_code == 201:
            task = response.json()
            print(f"Created task ID: {task['id']}")
            return task['id']
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Create task failed: {e}")
        return None

def test_get_tasks(user_id="test_user_123"):
    """Test getting tasks for a user"""
    try:
        response = requests.get(f"{BASE_URL}/tasks?user_id={user_id}")
        print(f"Get Tasks: {response.status_code}")
        if response.status_code == 200:
            tasks = response.json()
            print(f"Found {len(tasks)} tasks")
            return tasks
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Get tasks failed: {e}")
        return []

def test_update_task(task_id, user_id="test_user_123"):
    """Test updating a task"""
    update_data = {
        "status": "completed",
        "description": "Updated via API test"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}?user_id={user_id}", json=update_data)
        print(f"Update Task: {response.status_code}")
        if response.status_code == 200:
            task = response.json()
            print(f"Updated task status: {task['status']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Update task failed: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("=== 1TaskAssistant API Tests ===\n")
    
    # Test health check
    print("1. Testing health check...")
    if not test_health_check():
        print("Health check failed. Make sure the Azure Functions are running.")
        return
    print()
    
    # Test create task
    print("2. Testing create task...")
    task_id = test_create_task()
    if not task_id:
        print("Create task failed. Check your CosmosDB configuration.")
        return
    print()
    
    # Test get tasks
    print("3. Testing get tasks...")
    tasks = test_get_tasks()
    print()
    
    # Test update task
    print("4. Testing update task...")
    if task_id:
        test_update_task(task_id)
    print()
    
    print("=== Tests completed ===")

if __name__ == "__main__":
    run_all_tests()
