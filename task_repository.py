"""
Repository layer for task operations with CosmosDB
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from models import Task, TaskStatus
from cosmos_config import cosmos_manager

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for task CRUD operations"""
    
    def __init__(self):
        self.container = None
    
    def _get_container(self):
        """Get CosmosDB container instance"""
        if not self.container:
            self.container = cosmos_manager.get_container()
        return self.container
    
    def create_task(self, task: Task) -> Task:
        """Create a new task in CosmosDB"""
        try:
            # Generate ID if not provided
            if not task.id:
                task.id = str(uuid.uuid4())
            
            # Ensure timestamps are set
            task.created_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            
            container = self._get_container()
            task_dict = task.to_cosmos_dict()
            
            # Create the document
            response = container.create_item(body=task_dict)
            logger.info(f"Created task with ID: {response['id']}")
            
            return Task.from_cosmos_dict(response)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            raise
    
    def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a task by ID and user ID"""
        try:
            container = self._get_container()
            response = container.read_item(item=task_id, partition_key=user_id)
            return Task.from_cosmos_dict(response)
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Task not found: {task_id} for user: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            raise
    
    def get_tasks_by_user(self, user_id: str, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks for a user, optionally filtered by status"""
        try:
            container = self._get_container()
            
            # Build query
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            if status:
                query += " AND c.status = @status"
                parameters.append({"name": "@status", "value": status.value})
            
            query += " ORDER BY c.created_at DESC"
            
            # Execute query
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            tasks = [Task.from_cosmos_dict(item) for item in items]
            logger.info(f"Retrieved {len(tasks)} tasks for user: {user_id}")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error retrieving tasks for user {user_id}: {e}")
            raise
    
    def update_task(self, task_id: str, user_id: str, updates: dict) -> Optional[Task]:
        """Update a task with partial updates"""
        try:
            # First, get the existing task
            existing_task = self.get_task_by_id(task_id, user_id)
            if not existing_task:
                return None
            
            # Apply updates
            task_dict = existing_task.to_cosmos_dict()
            task_dict.update(updates)
            task_dict['updated_at'] = datetime.utcnow().isoformat()
            
            # Handle completion timestamp
            if updates.get('status') == TaskStatus.COMPLETED and not task_dict.get('completed_at'):
                task_dict['completed_at'] = datetime.utcnow().isoformat()
            elif updates.get('status') != TaskStatus.COMPLETED:
                task_dict['completed_at'] = None
            
            container = self._get_container()
            response = container.replace_item(item=task_id, body=task_dict)
            
            logger.info(f"Updated task: {task_id}")
            return Task.from_cosmos_dict(response)
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Task not found for update: {task_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            raise
    
    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task"""
        try:
            container = self._get_container()
            container.delete_item(item=task_id, partition_key=user_id)
            
            logger.info(f"Deleted task: {task_id}")
            return True
            
        except CosmosResourceNotFoundError:
            logger.warning(f"Task not found for deletion: {task_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            raise
    
    def get_tasks_by_priority(self, user_id: str, priority: str) -> List[Task]:
        """Get tasks by priority for a user"""
        try:
            container = self._get_container()
            
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.priority = @priority ORDER BY c.created_at DESC"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@priority", "value": priority}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            tasks = [Task.from_cosmos_dict(item) for item in items]
            logger.info(f"Retrieved {len(tasks)} {priority} priority tasks for user: {user_id}")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error retrieving {priority} priority tasks for user {user_id}: {e}")
            raise
    
    def get_overdue_tasks(self, user_id: str) -> List[Task]:
        """Get overdue tasks for a user"""
        try:
            container = self._get_container()
            current_time = datetime.utcnow().isoformat()
            
            query = """SELECT * FROM c 
                      WHERE c.user_id = @user_id 
                      AND c.due_date != null 
                      AND c.due_date < @current_time 
                      AND c.status != @completed_status
                      ORDER BY c.due_date ASC"""
            
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@current_time", "value": current_time},
                {"name": "@completed_status", "value": TaskStatus.COMPLETED.value}
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))
            
            tasks = [Task.from_cosmos_dict(item) for item in items]
            logger.info(f"Retrieved {len(tasks)} overdue tasks for user: {user_id}")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error retrieving overdue tasks for user {user_id}: {e}")
            raise


# Global repository instance
task_repository = TaskRepository()
