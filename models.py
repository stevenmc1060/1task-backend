"""
Data models for 1TaskAssistant application
"""
from datetime import datetime
from typing import Optional, List
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


class Task(BaseModel):
    """Task model for 1TaskAssistant"""
    id: Optional[str] = Field(default=None, description="Unique identifier for the task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Task last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    user_id: str = Field(..., description="User ID who owns the task")
    
    def to_cosmos_dict(self) -> dict:
        """Convert to dictionary format for CosmosDB"""
        data = self.model_dump()
        if data.get('id') is None:
            data.pop('id', None)  # Let CosmosDB generate the ID
        
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


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task"""
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    user_id: str


class UpdateTaskRequest(BaseModel):
    """Request model for updating an existing task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
