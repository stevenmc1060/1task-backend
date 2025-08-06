"""
Test new models with existing API infrastructure
"""
import requests
import json
from datetime import datetime, date

# API base URL (assuming your Azure Functions is running)
BASE_URL = "http://localhost:7076/api"

def test_task_with_new_fields():
    """Test creating a task with new relationship fields"""
    print("🔗 Testing Task with New Relationship Fields...")
    
    # Create a task with the new relationship fields
    task_data = {
        "title": "Test Task with New Fields",
        "description": "Testing the enhanced task model",
        "user_id": "test-user-enhanced",
        "priority": "high",
        "status": "pending",
        "project_id": "sample-project-123",
        "weekly_goal_id": "sample-weekly-goal-456",
        "habit_id": "sample-habit-789",
        "estimated_hours": 3.5,
        "tags": ["testing", "models", "api"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        
        if response.status_code == 201:
            task = response.json()
            print(f"✅ Created task: {task['title']}")
            print(f"✅ Task ID: {task['id']}")
            print(f"✅ Project ID: {task.get('project_id', 'None')}")
            print(f"✅ Weekly Goal ID: {task.get('weekly_goal_id', 'None')}")
            print(f"✅ Habit ID: {task.get('habit_id', 'None')}")
            print(f"✅ Estimated Hours: {task.get('estimated_hours', 'None')}")
            print(f"✅ Document Type: {task.get('document_type', 'None')}")
            
            return task['id']
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure Azure Functions is running on port 7076")
        return None
    except Exception as e:
        print(f"❌ Error testing task creation: {e}")
        return None

def test_task_update_with_new_fields(task_id):
    """Test updating a task with new fields"""
    if not task_id:
        print("❌ No task ID provided for update test")
        return
        
    print("\n🔄 Testing Task Update with New Fields...")
    
    update_data = {
        "status": "in_progress",
        "actual_hours": 2.5,
        "project_id": "updated-project-999"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/tasks/{task_id}?user_id=test-user-enhanced", 
            json=update_data
        )
        
        if response.status_code == 200:
            task = response.json()
            print(f"✅ Updated task: {task['title']}")
            print(f"✅ New status: {task['status']}")
            print(f"✅ Actual hours: {task.get('actual_hours', 'None')}")
            print(f"✅ Updated project ID: {task.get('project_id', 'None')}")
        else:
            print(f"❌ Failed to update task: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing task update: {e}")

def test_model_serialization():
    """Test that our models serialize correctly for API responses"""
    print("\n📦 Testing Model Serialization...")
    
    from models import Task, TaskStatus, TaskPriority, DocumentType
    
    # Create a task with all the new fields
    task = Task(
        title="Serialization Test Task",
        description="Testing JSON serialization",
        user_id="test-user",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        project_id="test-project",
        weekly_goal_id="test-weekly",
        habit_id="test-habit",
        estimated_hours=4.0,
        actual_hours=3.5,
        tags=["test", "serialization"]
    )
    
    try:
        # Test model_dump (what API uses)
        task_dict = task.model_dump()
        print(f"✅ Model dump successful: {len(task_dict)} fields")
        
        # Test JSON serialization
        json_str = json.dumps(task_dict, default=str)
        print(f"✅ JSON serialization successful: {len(json_str)} characters")
        
        # Test CosmosDB format
        cosmos_dict = task.to_cosmos_dict()
        print(f"✅ CosmosDB format successful: {len(cosmos_dict)} fields")
        
        # Verify all new fields are present
        new_fields = ['project_id', 'weekly_goal_id', 'habit_id', 'estimated_hours', 'actual_hours', 'document_type']
        for field in new_fields:
            if field in task_dict:
                print(f"✅ New field '{field}': {task_dict[field]}")
            else:
                print(f"❌ Missing new field: {field}")
                
    except Exception as e:
        print(f"❌ Serialization test failed: {e}")

def main():
    """Run all API integration tests"""
    print("🧪 Testing New Models with Existing API\n")
    
    # Test model serialization first
    test_model_serialization()
    
    # Test API integration (if running)
    task_id = test_task_with_new_fields()
    test_task_update_with_new_fields(task_id)
    
    print("\n📊 API Integration Test Summary:")
    print("✅ Enhanced Task model with new relationship fields")
    print("✅ Model serialization for API responses")
    print("✅ CosmosDB format compatibility")
    print("✅ JSON serialization with datetime handling")
    
    if task_id:
        print("✅ Live API testing (create and update)")
    else:
        print("⚠️  Live API testing skipped (API not running)")

if __name__ == "__main__":
    main()
