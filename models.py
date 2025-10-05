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


class LifeArea(str, Enum):
    """Enum for life areas to categorize goals, tasks, habits, and projects"""
    PROFESSIONAL_WORK = "professional_work"
    PERSONAL_GROWTH_LEARNING = "personal_growth_learning"
    RELATIONSHIPS = "relationships"
    HEALTH_SELF_CARE = "health_self_care"
    FINANCES = "finances"
    COMMUNITY = "community"
    UNCATEGORIZED = "uncategorized"
    
    @classmethod
    def get_display_name(cls, life_area: str) -> str:
        """Get user-friendly display name for life area"""
        display_names = {
            cls.PROFESSIONAL_WORK: "Professional / Work",
            cls.PERSONAL_GROWTH_LEARNING: "Personal Growth & Learning",
            cls.RELATIONSHIPS: "Relationships",
            cls.HEALTH_SELF_CARE: "Health & Self-Care",
            cls.FINANCES: "Finances",
            cls.COMMUNITY: "Community",
            cls.UNCATEGORIZED: "Uncategorized"
        }
        return display_names.get(life_area, life_area.replace("_", " ").title())
    
    @classmethod
    def get_all_areas_with_display_names(cls) -> dict:
        """Get all life areas with their display names"""
        return {
            area.value: cls.get_display_name(area.value) 
            for area in cls
        }
    
    @classmethod
    def get_default_areas(cls) -> List[str]:
        """Get default life areas for new users"""
        return [cls.PROFESSIONAL_WORK, cls.PERSONAL_GROWTH_LEARNING]
    
    @classmethod
    def is_valid_area(cls, area: str) -> bool:
        """Check if a life area value is valid"""
        try:
            cls(area)
            return True
        except ValueError:
            return False


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
    PREVIEW_CODE = "preview_code"


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
        datetime_fields = ['created_at', 'updated_at', 'completed_at', 'due_date', 'last_completed_at']
        date_fields = ['target_date', 'week_start_date', 'start_date', 'end_date']
        
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this goal belongs to")
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this goal belongs to")
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this goal belongs to")
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this habit belongs to")
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this project belongs to")
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
    life_area: Optional[LifeArea] = Field(default=None, description="Life area this task belongs to")
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
    status: Optional[GoalStatus] = None
    target_year: int
    life_area: Optional[LifeArea] = None
    key_metrics: List[str] = Field(default_factory=list)
    user_id: str


class CreateQuarterlyGoalRequest(BaseModel):
    """Request model for creating a quarterly goal"""
    title: str
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    target_year: int
    target_quarter: int
    life_area: Optional[LifeArea] = None
    key_metrics: List[str] = Field(default_factory=list)
    yearly_goal_id: Optional[str] = None
    user_id: str


class CreateWeeklyGoalRequest(BaseModel):
    """Request model for creating a weekly goal"""
    title: str
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    week_start_date: date
    life_area: Optional[LifeArea] = None
    key_metrics: List[str] = Field(default_factory=list)
    quarterly_goal_id: Optional[str] = None
    user_id: str


class CreateHabitRequest(BaseModel):
    """Request model for creating a habit"""
    title: str
    description: Optional[str] = None
    frequency: HabitFrequency
    life_area: Optional[LifeArea] = None
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
    status: Optional[ProjectStatus] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    life_area: Optional[LifeArea] = None
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
    status: Optional[TaskStatus] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    life_area: Optional[LifeArea] = None
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
    life_area: Optional[LifeArea] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateQuarterlyGoalRequest(BaseModel):
    """Request model for updating a quarterly goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    life_area: Optional[LifeArea] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateWeeklyGoalRequest(BaseModel):
    """Request model for updating a weekly goal"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None
    life_area: Optional[LifeArea] = None
    progress_percentage: Optional[float] = None
    key_metrics: Optional[List[str]] = None


class UpdateHabitRequest(BaseModel):
    """Request model for updating a habit"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[HabitStatus] = None
    frequency: Optional[HabitFrequency] = None
    life_area: Optional[LifeArea] = None
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
    life_area: Optional[LifeArea] = None
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
    life_area: Optional[LifeArea] = None
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
    
    # Life area preferences
    primary_life_areas: List[LifeArea] = Field(default_factory=list, description="User's primary focus life areas")
    life_area_priorities: Optional[dict] = Field(default=None, description="User's priority ranking for life areas")
    
    # Chat preferences
    preferred_greeting: Optional[str] = Field(default=None, description="User's preferred greeting style")
    communication_style: Optional[str] = Field(default=None, description="Preferred communication style")
    
    # Privacy settings
    data_sharing_consent: bool = Field(default=False, description="Consent for data sharing")
    analytics_consent: bool = Field(default=False, description="Consent for analytics tracking")
    
    # Profile completion
    is_profile_complete: bool = Field(default=False, description="Whether profile setup is complete")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    # Onboarding and suggestion engine data
    first_run: bool = Field(default=True, description="Flag for first-time user experience")
    onboarding_completed: bool = Field(default=False, description="Whether onboarding is complete")
    interview_data: Optional[dict] = Field(default=None, description="Raw interview data for suggestion engine")
    
    # Onboarding suggestions management
    onboarding_suggestions_cleared: bool = Field(default=False, description="Global flag to permanently hide all onboarding suggestions")
    deleted_onboarding_suggestions: List[str] = Field(default_factory=list, description="List of individual onboarding suggestion IDs that were deleted")
    
    # Preview code tracking
    preview_code_used: Optional[str] = Field(default=None, description="Preview code used during registration")
    
    # Address information
    contact_address: Optional[dict] = Field(default=None, description="Contact/shipping address")
    billing_address: Optional[dict] = Field(default=None, description="Billing address")
    billing_address_same_as_contact: Optional[bool] = Field(default=True, description="Whether billing address is same as contact")
    
    document_type: DocumentType = Field(default=DocumentType.USER_PROFILE, description="Document type")


class PreviewCode(BaseDocument):
    """Preview code model for early access control"""
    code: str = Field(..., description="The preview code string")
    is_used: bool = Field(default=False, description="Whether the code has been used")
    used_by_user_id: Optional[str] = Field(default=None, description="User ID who used this code")
    used_at: Optional[datetime] = Field(default=None, description="Timestamp when code was used")
    document_type: DocumentType = Field(default=DocumentType.PREVIEW_CODE, description="Document type")
    
    def to_cosmos_dict(self) -> dict:
        """Convert to dictionary format for CosmosDB"""
        data = super().to_cosmos_dict()
        # Use code as the document ID for fast lookups
        data['id'] = self.code
        return data
    
    @classmethod
    def from_cosmos_dict(cls, data: dict) -> 'PreviewCode':
        """Create PreviewCode instance from CosmosDB document"""
        # Convert ISO strings back to datetime objects
        for field in ['created_at', 'updated_at', 'used_at']:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except ValueError:
                    data[field] = None
        return cls(**data)


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
    primary_life_areas: List[LifeArea] = Field(default_factory=list)
    life_area_priorities: Optional[dict] = None
    preferred_greeting: Optional[str] = None
    communication_style: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    
    # Onboarding fields
    first_run: Optional[bool] = Field(default=True, description="Flag for first-time user")
    onboarding_completed: Optional[bool] = Field(default=False, description="Onboarding completion status")
    interview_data: Optional[dict] = Field(default=None, description="Interview data for suggestions")
    
    # Preview code tracking (from frontend onboarding)
    preview_code_used: Optional[str] = Field(default=None, description="Preview code used during registration")
    
    # Contact and billing address information
    contact_address: Optional[dict] = Field(default=None, description="Contact/shipping address")
    billing_address: Optional[dict] = Field(default=None, description="Billing address")
    billing_address_same_as_contact: Optional[bool] = Field(default=True, description="Whether billing address is same as contact")


class UpdateUserProfileRequest(BaseModel):
    """Request model for updating a user profile"""
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    primary_life_areas: Optional[List[LifeArea]] = None
    life_area_priorities: Optional[dict] = None
    preferred_greeting: Optional[str] = None
    communication_style: Optional[str] = None
    profile_picture_url: Optional[str] = None
    data_sharing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None
    
    # Onboarding fields for developer utilities
    first_run: Optional[bool] = None
    onboarding_completed: Optional[bool] = None
    interview_data: Optional[dict] = None
    
    # Onboarding suggestions management
    onboarding_suggestions_cleared: Optional[bool] = None
    deleted_onboarding_suggestions: Optional[List[str]] = None
    
    # Preview code tracking
    preview_code_used: Optional[str] = None
    
    # Address information
    contact_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    billing_address_same_as_contact: Optional[bool] = None


# =============================================
# NOTES APPLICATION MODELS
# =============================================

class FileAttachment(BaseModel):
    """Model for file attachments in notes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    name: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="MIME type (e.g., 'image/png')")
    data: str = Field(..., description="Base64 encoded file data OR Azure Blob URL")
    uploaded_at: datetime = Field(default_factory=datetime.now, description="Upload timestamp")


class Note(BaseModel):
    """Model for notes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User ID who owns this note")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note body content (markdown)")
    tags: List[str] = Field(default_factory=list, description="Array of tag strings")
    is_pinned: bool = Field(default=False, description="Whether note is pinned to top")
    folder_id: Optional[str] = Field(default=None, description="Parent folder ID (null = root level)")
    attachments: List[FileAttachment] = Field(default_factory=list, description="Array of file attachments")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    def to_dict(self):
        """Convert to dictionary for Cosmos DB storage"""
        return {
            "id": self.id,
            "user_id": self.user_id,  # Cosmos DB partition key
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "isPinned": self.is_pinned,
            "folderId": self.folder_id,
            "attachments": [att.dict() for att in self.attachments],
            "createdAt": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updatedAt": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "_type": "note"  # Document type discriminator
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create Note instance from Cosmos DB data"""
        attachments = []
        if data.get('attachments'):
            attachments = [FileAttachment(**att) if isinstance(att, dict) else att for att in data['attachments']]
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            tags=data.get('tags', []),
            is_pinned=data.get('isPinned', False),
            folder_id=data.get('folderId'),
            attachments=attachments,
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if isinstance(data.get('createdAt'), str) else data.get('createdAt', datetime.now()),
            updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if isinstance(data.get('updatedAt'), str) else data.get('updatedAt', datetime.now())
        )


class Folder(BaseModel):
    """Model for folders"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    user_id: str = Field(..., description="User ID who owns this folder")
    name: str = Field(..., description="Folder display name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID (null = root level)")
    color: str = Field(default="bg-gray-500", description="CSS color class (e.g., 'bg-blue-500')")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    def to_dict(self):
        """Convert to dictionary for Cosmos DB storage"""
        return {
            "id": self.id,
            "user_id": self.user_id,  # Cosmos DB partition key
            "name": self.name,
            "parentId": self.parent_id,
            "color": self.color,
            "createdAt": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "_type": "folder"  # Document type discriminator
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create Folder instance from Cosmos DB data"""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            name=data.get('name', ''),
            parent_id=data.get('parentId'),
            color=data.get('color', 'bg-gray-500'),
            created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if isinstance(data.get('createdAt'), str) else data.get('createdAt', datetime.now())
        )


# Request/Response models for Notes API

class CreateNoteRequest(BaseModel):
    """Request model for creating a note"""
    title: str = Field(..., description="Note title")
    content: str = Field(default="", description="Note content (markdown)")
    tags: List[str] = Field(default_factory=list, description="Array of tag strings")
    is_pinned: bool = Field(default=False, description="Whether note is pinned")
    folder_id: Optional[str] = Field(default=None, description="Parent folder ID")
    attachments: List[FileAttachment] = Field(default_factory=list, description="Array of file attachments")


class UpdateNoteRequest(BaseModel):
    """Request model for updating a note"""
    title: Optional[str] = Field(default=None, description="Note title")
    content: Optional[str] = Field(default=None, description="Note content (markdown)")
    tags: Optional[List[str]] = Field(default=None, description="Array of tag strings")
    is_pinned: Optional[bool] = Field(default=None, description="Whether note is pinned")
    folder_id: Optional[str] = Field(default=None, description="Parent folder ID")
    attachments: Optional[List[FileAttachment]] = Field(default=None, description="Array of file attachments")


class CreateFolderRequest(BaseModel):
    """Request model for creating a folder"""
    name: str = Field(..., description="Folder display name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")
    color: str = Field(default="bg-gray-500", description="CSS color class")


class UpdateFolderRequest(BaseModel):
    """Request model for updating a folder"""
    name: Optional[str] = Field(default=None, description="Folder display name")
    parent_id: Optional[str] = Field(default=None, description="Parent folder ID")
    color: Optional[str] = Field(default=None, description="CSS color class")


class TaskFromNoteRequest(BaseModel):
    """Request model for converting note to task"""
    title: str = Field(..., description="Task title (from note title)")
    description: str = Field(..., description="Task description (from note content/selection)")
    note_id: str = Field(..., description="Reference to source note")
    url: str = Field(..., description="Deep link back to note")


class NotesListResponse(BaseModel):
    """Response model for listing notes"""
    notes: List[Note] = Field(..., description="Array of notes")


class FoldersListResponse(BaseModel):
    """Response model for listing folders"""
    folders: List[Folder] = Field(..., description="Array of folders")


# Preview Code Validation Models
class PreviewCodeValidationRequest(BaseModel):
    """Request model for preview code validation"""
    code: str = Field(..., description="Preview code to validate")
    user_id: str = Field(..., description="User ID requesting validation")


class PreviewCodeValidationResponse(BaseModel):
    """Response model for preview code validation"""
    valid: bool = Field(..., description="Whether the code is valid")
    message: str = Field(..., description="Validation message")
    error: Optional[str] = Field(default=None, description="Error code if validation failed")
    code_id: Optional[str] = Field(default=None, description="Code ID if validation succeeded")
