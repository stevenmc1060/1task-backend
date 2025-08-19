"""Data models for 1TaskAssistant application
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Union
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Enum for task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Enum for task priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class GoalStatus(str, Enum):
    """Enum for goal status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    """Enum for project status"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class HabitFrequency(str, Enum):
    """Enum for habit frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class HabitStatus(str, Enum):
    """Enum for habit status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    """Enum for document types"""
    TASK = "task"
    YEARLY_GOAL = "yearly_goal"
    QUARTERLY_GOAL = "quarterly_goal"
    WEEKLY_GOAL = "weekly_goal"
    HABIT = "habit"
    PROJECT = "project"
    USER_PROFILE = "user_profile"
    ONBOARDING_STATUS = "onboarding_status"
    CHAT_SESSION = "chat_session"


class OnboardingStep(str, Enum):
    """Enum for onboarding steps"""
    WELCOME = "welcome"
    PROFILE_SETUP = "profile_setup" 
    PREFERENCES = "preferences"
    FIRST_TASK = "first_task"
    COMPLETED = "completed"


class ChatMessageRole(str, Enum):
    """Enum for chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class BaseDocument(BaseModel):
    """Base document model with common fields"""
    id: Optional[str] = Field(default=None, description="Unique identifier")
    user_id: str = Field(..., description="User ID who owns this document")
    document_type: DocumentType = Field(..., description="Type of document")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def to_cosmos_dict(self) -> dict:
        """Convert to dictionary format for CosmosDB"""
        data = self.model_dump()
        
        # Generate UUID for id if it's None
        if data.get('id') is None:
            data['id'] = str(uuid.uuid4())
        
        # Convert datetime, date, and enum objects to proper formats
        for field_name, field_value in data.items():
            if isinstance(field_value, datetime):
                data[field_name] = field_value.isoformat()
            elif isinstance(field_value, date):
                data[field_name] = field_value.isoformat()
            elif hasattr(field_value, 'value'):  # Handle enum objects
                data[field_name] = field_value.value
        
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: dict) -> 'BaseDocument':
        """Create document instance from CosmosDB document"""
        # Convert ISO strings back to datetime/date objects
        datetime_fields = ['created_at', 'updated_at', 'completed_at', 'due_date', 'start_date', 'end_date', 'last_completed_at']
        date_fields = ['target_date', 'week_start_date']
        
        for field in datetime_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError as e:
                    # Handle any datetime parsing errors
                    print(f"Error parsing datetime field {field}: {e}")
                    data[field] = None
        
        for field in date_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = date.fromisoformat(data[field])
                except ValueError as e:
                    # Handle any date parsing errors
                    print(f"Error parsing date field {field}: {e}")
                    data[field] = None
        
        return cls(**data)


class YearlyGoal(BaseDocument):
    """Yearly goal model"""
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(default=None, description="Goal description")
    status: GoalStatus = Field(default=GoalStatus.NOT_STARTED, description="Goal status")
    target_year: int = Field(..., description="Target year for the goal")
    progress_percentage: float = Field(default=0.0, description="Progress percentage (0-100)")
    key_metrics: List[str] = Field(default_factory=list, description="Key metrics to track")
    quarterly_goal_ids: List[str] = Field(default_factory=list, description="Associated quarterly goal IDs")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    document_type: DocumentType = Field(default=DocumentType.YEARLY_GOAL, description="Document type")


class QuarterlyGoal(BaseDocument):
    """Quarterly goal model"""
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(default=None, description="Goal description")
    status: GoalStatus = Field(default=GoalStatus.NOT_STARTED, description="Goal status")
    target_year: int = Field(..., description="Target year")
    target_quarter: int = Field(..., description="Target quarter (1-4)")
    progress_percentage: float = Field(default=0.0, description="Progress percentage (0-100)")
    key_metrics: List[str] = Field(default_factory=list, description="Key metrics to track")
    yearly_goal_id: Optional[str] = Field(default=None, description="Parent yearly goal ID")
    weekly_goal_ids: List[str] = Field(default_factory=list, description="Associated weekly goal IDs")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    document_type: DocumentType = Field(default=DocumentType.QUARTERLY_GOAL, description="Document type")


class WeeklyGoal(BaseDocument):
    """Weekly goal model"""
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(default=None, description="Goal description")
    status: GoalStatus = Field(default=GoalStatus.NOT_STARTED, description="Goal status")
    week_start_date: date = Field(..., description="Start date of the week")
    progress_percentage: float = Field(default=0.0, description="Progress percentage (0-100)")
    key_metrics: List[str] = Field(default_factory=list, description="Key metrics to track")
    quarterly_goal_id: Optional[str] = Field(default=None, description="Parent quarterly goal ID")
    task_ids: List[str] = Field(default_factory=list, description="Associated task IDs")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    document_type: DocumentType = Field(default=DocumentType.WEEKLY_GOAL, description="Document type")


class Habit(BaseDocument):
    """Habit model"""
    title: str = Field(..., description="Habit title")
    description: Optional[str] = Field(default=None, description="Habit description")
    status: HabitStatus = Field(default=HabitStatus.ACTIVE, description="Habit status")
    frequency: HabitFrequency = Field(..., description="How often the habit should be performed")
    target_count: int = Field(default=1, description="Target count per frequency period")
    current_count: int = Field(default=0, description="Completions in current period (e.g. week)")
    current_streak: int = Field(default=0, description="Current streak count")
    longest_streak: int = Field(default=0, description="Longest streak achieved")
    total_completions: int = Field(default=0, description="Total number of completions")
    reminder_time: Optional[str] = Field(default=None, description="Reminder time (HH:MM format)")
    tags: List[str] = Field(default_factory=list, description="Habit tags")
    last_completed_at: Optional[datetime] = Field(default=None, description="Last completion timestamp")
    document_type: DocumentType = Field(default=DocumentType.HABIT, description="Document type")


class Project(BaseDocument):
    """Project model"""
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(default=None, description="Project description")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING, description="Project status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Project priority")
    start_date: Optional[date] = Field(default=None, description="Project start date")
    end_date: Optional[date] = Field(default=None, description="Project end date")
    progress_percentage: float = Field(default=0.0, description="Progress percentage (0-100)")
    tags: List[str] = Field(default_factory=list, description="Project tags")
    task_ids: List[str] = Field(default_factory=list, description="Associated task IDs")
    yearly_goal_id: Optional[str] = Field(default=None, description="Parent yearly goal ID")
    quarterly_goal_id: Optional[str] = Field(default=None, description="Parent quarterly goal ID")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    document_type: DocumentType = Field(default=DocumentType.PROJECT, description="Document type")


class Task(BaseDocument):
    """Task model for 1TaskAssistant"""
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    project_id: Optional[str] = Field(default=None, description="Parent project ID")
    weekly_goal_id: Optional[str] = Field(default=None, description="Parent weekly goal ID")
    habit_id: Optional[str] = Field(default=None, description="Parent habit ID")
    estimated_hours: Optional[float] = Field(default=None, description="Estimated hours to complete")
    actual_hours: Optional[float] = Field(default=None, description="Actual hours spent")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata for special item types")
    document_type: DocumentType = Field(default=DocumentType.TASK, description="Document type")
    
    def to_cosmos_dict(self) -> dict:
        """Convert to dictionary format for CosmosDB"""
        data = self.model_dump()
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'completed_at', 'due_date']:
            if data.get(field):
                data[field] = data[field].isoformat() if isinstance(data[field], datetime) else data[field]
        
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: dict) -> 'Task':
        """Create Task instance from CosmosDB document"""
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at', 'completed_at', 'due_date']:
            if data.get(field):
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)


# Request Models for Creating Documents

class CreateYearlyGoalRequest(BaseModel):
    """Request model for creating a yearly goal"""
    title: str
    description: Optional[str] = None
    target_year: int
    key_metrics: List[str] = Field(default_factory=list)
    user_id: str


class CreateQuarterlyGoalRequest(BaseModel):
    """Request model for creating a quarterly goal"""
    title: str
    description: Optional[str] = None
    target_year: int
    target_quarter: int
    key_metrics: List[str] = Field(default_factory=list)
    yearly_goal_id: Optional[str] = None
    user_id: str


class CreateWeeklyGoalRequest(BaseModel):
    """Request model for creating a weekly goal"""
    title: str
    description: Optional[str] = None
    week_start_date: date
    key_metrics: List[str] = Field(default_factory=list)
    quarterly_goal_id: Optional[str] = None
    user_id: str


class CreateHabitRequest(BaseModel):
    """Request model for creating a habit"""
    title: str
    description: Optional[str] = None
    frequency: HabitFrequency
    target_count: Union[int, str] = 1  # Accept both int and string, convert to int
    current_count: int = 0
    status: HabitStatus = HabitStatus.ACTIVE
    reminder_time: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_id: str
    # Allow extra fields that frontend might send
    itemType: Optional[str] = None
    metadata: Optional[dict] = None
    
    def model_post_init(self, __context):
        """Convert string target_count to int"""
        if isinstance(self.target_count, str):
            self.target_count = int(self.target_count)


class CreateProjectRequest(BaseModel):
    """Request model for creating a project"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    tags: List[str] = Field(default_factory=list)
    yearly_goal_id: Optional[str] = None
    quarterly_goal_id: Optional[str] = None
    user_id: str


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    weekly_goal_id: Optional[str] = None
    habit_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    metadata: Optional[dict] = None
    user_id: str


# Request Models for Updating Documents

class UpdateYearlyGoalRequest(BaseModel):
    """Request model for updating a yearly goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateQuarterlyGoalRequest(BaseModel):
    """Request model for updating a quarterly goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateWeeklyGoalRequest(BaseModel):
    """Request model for updating a weekly goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateHabitRequest(BaseModel):
    """Request model for updating a habit"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[HabitStatus] = None
    frequency: Optional[HabitFrequency] = None
    target_count: Optional[int] = None
    current_count: Optional[int] = None
    reminder_time: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateProjectRequest(BaseModel):
    """Request model for updating a project"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    priority: Optional[TaskPriority] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    progress_percentage: Optional[float] = None
    tags: Optional[List[str]] = None


class UpdateTaskRequest(BaseModel):
    """Request model for updating an existing task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    project_id: Optional[str] = None
    weekly_goal_id: Optional[str] = None
    habit_id: Optional[str] = None


# =====================
# User Profile Models
# =====================

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: ChatMessageRole = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatSession(BaseDocument):
    """Chat session model for storing conversation history"""
    session_title: str = Field(..., description="Brief title for the session")
    messages: List[ChatMessage] = Field(default_factory=list, description="Chat messages in this session")
    session_date: date = Field(default_factory=date.today, description="Date of the session")
    message_count: int = Field(default=0, description="Number of messages in session")
    document_type: DocumentType = Field(default=DocumentType.CHAT_SESSION, description="Document type")


class OnboardingStatus(BaseDocument):
    """Onboarding progress tracking"""
    current_step: OnboardingStep = Field(default=OnboardingStep.WELCOME, description="Current onboarding step")
    completed_steps: List[OnboardingStep] = Field(default_factory=list, description="Completed onboarding steps")
    is_completed: bool = Field(default=False, description="Whether onboarding is fully completed")
    completed_at: Optional[datetime] = Field(default=None, description="Onboarding completion timestamp")
    welcome_shown: bool = Field(default=False, description="Whether welcome message has been shown")
    interview_responses: dict = Field(default_factory=dict, description="Interview responses during onboarding")
    document_type: DocumentType = Field(default=DocumentType.ONBOARDING_STATUS, description="Document type")


class UserProfile(BaseDocument):
    """User profile model for personalized chat"""
    # OAuth provider data (auto-populated when possible)
    oauth_provider: Optional[str] = Field(default=None, description="OAuth provider (microsoft, google)")
    oauth_id: Optional[str] = Field(default=None, description="OAuth provider user ID")
    
    # Core profile data
    display_name: str = Field(..., description="User's preferred display name")
    email: str = Field(..., description="User's email address")
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    
    # Location and timezone
    location: Optional[str] = Field(default=None, description="User's location (city, country)")
    timezone: Optional[str] = Field(default=None, description="User's timezone")
    
    # Profile customization
    profile_picture_url: Optional[str] = Field(default=None, description="Profile picture URL")
    bio: Optional[str] = Field(default=None, description="User bio/description")
    
    # Chat preferences
    preferred_greeting: Optional[str] = Field(default=None, description="User's preferred greeting style")
    communication_style: Optional[str] = Field(default=None, description="Preferred communication style")
    
    # Privacy settings
    data_sharing_consent: bool = Field(default=False, description="Consent for data sharing")
    analytics_consent: bool = Field(default=False, description="Consent for analytics tracking")
    
    # Profile completion
    is_profile_complete: bool = Field(default=False, description="Whether profile setup is complete")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    document_type: DocumentType = Field(default=DocumentType.USER_PROFILE, description="Document type")


# =====================
# Request/Response Models for User Profile API
# =====================

class CreateUserProfileRequest(BaseModel):
    """Request model for creating a user profile"""
    display_name: str = Field(..., description="User's preferred display name")
    email: str = Field(..., description="User's email address")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    preferred_greeting: Optional[str] = None
    communication_style: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UpdateUserProfileRequest(BaseModel):
    """Request model for updating a user profile"""
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    preferred_greeting: Optional[str] = None
    communication_style: Optional[str] = None
    profile_picture_url: Optional[str] = None
    data_sharing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None
