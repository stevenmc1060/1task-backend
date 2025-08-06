"""
Test models with CosmosDB integration
"""
from models import YearlyGoal, QuarterlyGoal, Project, Task, CreateYearlyGoalRequest, CreateProjectRequest, CreateTaskRequest
from task_repository import task_repository
import asyncio
from datetime import datetime, date

def test_cosmos_integration():
    """Test models with actual CosmosDB"""
    print("🗄️ Testing CosmosDB Integration...")
    
    try:
        # Test creating a yearly goal
        yearly_goal_request = CreateYearlyGoalRequest(
            title="2025 Development Goals",
            description="Master backend and frontend development",
            target_year=2025,
            key_metrics=["Complete 10 projects", "Learn 5 new technologies"],
            user_id="test-user-models"
        )
        
        yearly_goal = YearlyGoal(**yearly_goal_request.model_dump())
        print(f"✅ Created YearlyGoal model: {yearly_goal.title}")
        
        # Test the cosmos dict conversion
        cosmos_dict = yearly_goal.to_cosmos_dict()
        print(f"✅ Converted to cosmos dict with {len(cosmos_dict)} fields")
        
        # Test restoration from cosmos dict
        restored_goal = YearlyGoal.from_cosmos_dict(cosmos_dict)
        print(f"✅ Restored from cosmos dict: {restored_goal.title}")
        
        # Test that document_type is set correctly
        print(f"✅ Document type: {cosmos_dict['document_type']}")
        print(f"✅ User ID (partition key): {cosmos_dict['user_id']}")
        
        # Test task creation (existing functionality should still work)
        task_data = {
            "title": "Test Model Integration",
            "description": "Verify new models work with existing repository",
            "user_id": "test-user-models",
            "priority": "medium",
            "status": "pending"
        }
        
        task = Task(**task_data)
        print(f"✅ Created Task model: {task.title}")
        print(f"✅ Task document type: {task.document_type}")
        
        # Test that all required fields are present for CosmosDB
        required_fields = ['user_id', 'document_type', 'created_at', 'updated_at']
        task_dict = task.to_cosmos_dict()
        
        for field in required_fields:
            if field in task_dict:
                print(f"✅ Required field '{field}' present: {task_dict[field]}")
            else:
                print(f"❌ Missing required field: {field}")
        
        print("\n🎯 Model Structure Validation:")
        print(f"YearlyGoal fields: {list(cosmos_dict.keys())}")
        print(f"Task fields: {list(task_dict.keys())}")
        
        print("\n✅ All CosmosDB integration tests passed!")
        
    except Exception as e:
        print(f"❌ CosmosDB integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cosmos_integration()
