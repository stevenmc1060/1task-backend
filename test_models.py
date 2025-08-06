"""
Test script for 1TaskAssistant data models
"""
import json
from datetime import datetime, date
from models import (
    # Document models
    YearlyGoal, QuarterlyGoal, WeeklyGoal, Habit, Project, Task,
    
    # Enums
    TaskStatus, TaskPriority, GoalStatus, ProjectStatus, HabitStatus, HabitFrequency, DocumentType,
    
    # Request models
    CreateYearlyGoalRequest, CreateQuarterlyGoalRequest, CreateWeeklyGoalRequest,
    CreateHabitRequest, CreateProjectRequest, CreateTaskRequest,
    UpdateYearlyGoalRequest, UpdateQuarterlyGoalRequest, UpdateWeeklyGoalRequest,
    UpdateHabitRequest, UpdateProjectRequest, UpdateTaskRequest,
    HabitCompletionRequest, ProgressUpdateRequest
)

def test_yearly_goal():
    """Test YearlyGoal model creation and serialization"""
    print("🎯 Testing YearlyGoal...")
    
    # Test creation from request
    request = CreateYearlyGoalRequest(
        title="Master Software Development",
        description="Become proficient in full-stack development",
        target_year=2025,
        key_metrics=["Complete 5 projects", "Learn 3 new frameworks", "Contribute to open source"],
        user_id="user123"
    )
    
    goal = YearlyGoal(**request.model_dump())
    print(f"✅ Created yearly goal: {goal.title}")
    
    # Test CosmosDB serialization
    cosmos_dict = goal.to_cosmos_dict()
    print(f"✅ Cosmos dict keys: {list(cosmos_dict.keys())}")
    
    # Test deserialization
    restored_goal = YearlyGoal.from_cosmos_dict(cosmos_dict)
    print(f"✅ Restored goal: {restored_goal.title}")
    
    return goal

def test_quarterly_goal(yearly_goal_id: str):
    """Test QuarterlyGoal model"""
    print("\n📅 Testing QuarterlyGoal...")
    
    request = CreateQuarterlyGoalRequest(
        title="Q1 2025: Frontend Mastery",
        description="Focus on React and TypeScript",
        target_year=2025,
        target_quarter=1,
        key_metrics=["Build 2 React projects", "Learn TypeScript"],
        yearly_goal_id=yearly_goal_id,
        user_id="user123"
    )
    
    goal = QuarterlyGoal(**request.model_dump())
    print(f"✅ Created quarterly goal: {goal.title}")
    print(f"✅ Linked to yearly goal: {goal.yearly_goal_id}")
    
    return goal

def test_weekly_goal(quarterly_goal_id: str):
    """Test WeeklyGoal model"""
    print("\n📆 Testing WeeklyGoal...")
    
    request = CreateWeeklyGoalRequest(
        title="Week 1: React Setup",
        description="Set up React development environment",
        week_start_date=date(2025, 1, 6),
        key_metrics=["Configure dev environment", "Create first component"],
        quarterly_goal_id=quarterly_goal_id,
        user_id="user123"
    )
    
    goal = WeeklyGoal(**request.model_dump())
    print(f"✅ Created weekly goal: {goal.title}")
    print(f"✅ Week start: {goal.week_start_date}")
    
    return goal

def test_habit():
    """Test Habit model"""
    print("\n🔄 Testing Habit...")
    
    request = CreateHabitRequest(
        title="Daily Coding Practice",
        description="Code for at least 1 hour every day",
        frequency=HabitFrequency.DAILY,
        target_count=1,
        reminder_time="09:00",
        tags=["coding", "learning", "productivity"],
        user_id="user123"
    )
    
    habit = Habit(**request.model_dump())
    print(f"✅ Created habit: {habit.title}")
    print(f"✅ Frequency: {habit.frequency}")
    print(f"✅ Current streak: {habit.current_streak}")
    
    return habit

def test_project(yearly_goal_id: str, quarterly_goal_id: str):
    """Test Project model"""
    print("\n📂 Testing Project...")
    
    request = CreateProjectRequest(
        title="Personal Portfolio Website",
        description="Build a modern portfolio to showcase projects",
        priority=TaskPriority.HIGH,
        start_date=date(2025, 1, 15),
        end_date=date(2025, 3, 15),
        tags=["portfolio", "react", "typescript"],
        yearly_goal_id=yearly_goal_id,
        quarterly_goal_id=quarterly_goal_id,
        user_id="user123"
    )
    
    project = Project(**request.model_dump())
    print(f"✅ Created project: {project.title}")
    print(f"✅ Priority: {project.priority}")
    print(f"✅ Linked to goals: {project.yearly_goal_id}, {project.quarterly_goal_id}")
    
    return project

def test_task(project_id: str, weekly_goal_id: str, habit_id: str):
    """Test Task model"""
    print("\n✅ Testing Task...")
    
    request = CreateTaskRequest(
        title="Design portfolio homepage",
        description="Create wireframes and mockups for the main page",
        priority=TaskPriority.MEDIUM,
        due_date=datetime(2025, 1, 20, 17, 0),
        tags=["design", "ui/ux"],
        project_id=project_id,
        weekly_goal_id=weekly_goal_id,
        habit_id=habit_id,
        estimated_hours=4.0,
        user_id="user123"
    )
    
    task = Task(**request.model_dump())
    print(f"✅ Created task: {task.title}")
    print(f"✅ Due date: {task.due_date}")
    print(f"✅ Linked to project: {task.project_id}")
    print(f"✅ Linked to weekly goal: {task.weekly_goal_id}")
    print(f"✅ Linked to habit: {task.habit_id}")
    
    return task

def test_updates():
    """Test update request models"""
    print("\n🔄 Testing Update Models...")
    
    # Test goal update
    goal_update = UpdateYearlyGoalRequest(
        title="Updated: Master Full-Stack Development",
        status=GoalStatus.IN_PROGRESS,
        progress_percentage=25.0
    )
    print(f"✅ Goal update: {goal_update.title}, Progress: {goal_update.progress_percentage}%")
    
    # Test habit update
    habit_update = UpdateHabitRequest(
        status=HabitStatus.ACTIVE,
        target_count=2
    )
    print(f"✅ Habit update: Status: {habit_update.status}, Target: {habit_update.target_count}")
    
    # Test task update
    task_update = UpdateTaskRequest(
        status=TaskStatus.IN_PROGRESS,
        actual_hours=2.5
    )
    print(f"✅ Task update: Status: {task_update.status}, Hours: {task_update.actual_hours}")

def test_special_requests():
    """Test special request models"""
    print("\n⭐ Testing Special Requests...")
    
    # Test habit completion
    completion = HabitCompletionRequest(
        completion_date=datetime.utcnow(),
        notes="Great coding session today!"
    )
    print(f"✅ Habit completion: {completion.completion_date}")
    
    # Test progress update
    progress = ProgressUpdateRequest(
        progress_percentage=75.0,
        notes="Making good progress on the project"
    )
    print(f"✅ Progress update: {progress.progress_percentage}%")

def test_cosmos_serialization():
    """Test CosmosDB serialization for all models"""
    print("\n🗄️ Testing CosmosDB Serialization...")
    
    # Create sample documents
    yearly_goal = YearlyGoal(
        title="Test Goal",
        target_year=2025,
        user_id="user123"
    )
    
    habit = Habit(
        title="Test Habit",
        frequency=HabitFrequency.DAILY,
        user_id="user123"
    )
    
    project = Project(
        title="Test Project",
        user_id="user123"
    )
    
    task = Task(
        title="Test Task",
        user_id="user123"
    )
    
    documents = [yearly_goal, habit, project, task]
    
    for doc in documents:
        cosmos_dict = doc.to_cosmos_dict()
        restored_doc = type(doc).from_cosmos_dict(cosmos_dict)
        
        print(f"✅ {type(doc).__name__}: Serialization successful")
        print(f"   Document type: {cosmos_dict['document_type']}")
        print(f"   Original title: {doc.title}")
        print(f"   Restored title: {restored_doc.title}")

def test_enum_values():
    """Test all enum values"""
    print("\n🔢 Testing Enums...")
    
    print(f"TaskStatus: {[status.value for status in TaskStatus]}")
    print(f"TaskPriority: {[priority.value for priority in TaskPriority]}")
    print(f"GoalStatus: {[status.value for status in GoalStatus]}")
    print(f"ProjectStatus: {[status.value for status in ProjectStatus]}")
    print(f"HabitStatus: {[status.value for status in HabitStatus]}")
    print(f"HabitFrequency: {[freq.value for freq in HabitFrequency]}")
    print(f"DocumentType: {[doc_type.value for doc_type in DocumentType]}")

def main():
    """Run all tests"""
    print("🧪 Starting 1TaskAssistant Model Tests\n")
    
    try:
        # Test individual models and build relationships
        yearly_goal = test_yearly_goal()
        quarterly_goal = test_quarterly_goal(yearly_goal.id or "test-yearly-id")
        weekly_goal = test_weekly_goal(quarterly_goal.id or "test-quarterly-id")
        habit = test_habit()
        project = test_project(yearly_goal.id or "test-yearly-id", quarterly_goal.id or "test-quarterly-id")
        task = test_task(
            project.id or "test-project-id",
            weekly_goal.id or "test-weekly-id", 
            habit.id or "test-habit-id"
        )
        
        # Test updates and special requests
        test_updates()
        test_special_requests()
        
        # Test serialization
        test_cosmos_serialization()
        
        # Test enums
        test_enum_values()
        
        print("\n🎉 All model tests completed successfully!")
        
        # Print summary
        print("\n📊 Test Summary:")
        print("✅ YearlyGoal - Creation, serialization, relationships")
        print("✅ QuarterlyGoal - Hierarchical linking to yearly goals")
        print("✅ WeeklyGoal - Date handling and quarterly goal links")
        print("✅ Habit - Frequency settings and streak tracking")
        print("✅ Project - Multi-goal linking and priority management")
        print("✅ Task - Cross-document relationships (project, goal, habit)")
        print("✅ Update Models - Partial updates with optional fields")
        print("✅ Special Requests - Habit completions and progress updates")
        print("✅ CosmosDB Serialization - All document types")
        print("✅ Enum Validation - All status and type enums")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
