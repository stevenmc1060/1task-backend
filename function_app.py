import azure.functions as func
import datetime
import json
import logging
from models import Task, CreateTaskRequest, UpdateTaskRequest, TaskStatus, TaskPriority
from task_repository import task_repository

app = func.FunctionApp()

logger = logging.getLogger(__name__)


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info('Health check endpoint triggered.')
    
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "service": "1TaskAssistant API"
        }),
        status_code=200,
        mimetype="application/json"
    )


@app.route(route="tasks", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Get tasks for a user"""
    logger.info('Get tasks endpoint triggered.')
    
    try:
        # Get query parameters
        user_id = req.params.get('user_id')
        status = req.params.get('status')
        priority = req.params.get('priority')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get tasks based on filters
        if priority:
            tasks = task_repository.get_tasks_by_priority(user_id, priority)
        elif status:
            task_status = TaskStatus(status) if status in [s.value for s in TaskStatus] else None
            if not task_status:
                return func.HttpResponse(
                    json.dumps({"error": f"Invalid status: {status}"}),
                    status_code=400,
                    mimetype="application/json"
                )
            tasks = task_repository.get_tasks_by_user(user_id, task_status)
        else:
            tasks = task_repository.get_tasks_by_user(user_id)
        
        # Convert tasks to dict format
        tasks_data = [task.model_dump() for task in tasks]
        
        return func.HttpResponse(
            json.dumps(tasks_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_tasks: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new task"""
    logger.info('Create task endpoint triggered.')
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate request
        try:
            create_request = CreateTaskRequest(**req_body)
        except Exception as e:
            return func.HttpResponse(
                json.dumps({"error": f"Validation error: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create task
        task = Task(**create_request.model_dump())
        created_task = task_repository.create_task(task)
        
        return func.HttpResponse(
            json.dumps(created_task.model_dump(), default=str),
            status_code=201,
            mimetype="application/json"
        )
        
    except ValueError as ve:
        logger.error(f"Validation error in create_task: {ve}")
        return func.HttpResponse(
            json.dumps({"error": f"Validation error: {str(ve)}"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/{task_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    """Get a specific task by ID"""
    logger.info('Get task by ID endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        task = task_repository.get_task_by_id(task_id, user_id)
        
        if not task:
            return func.HttpResponse(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(task.model_dump(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_task_by_id: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/{task_id}", methods=["PUT"], auth_level=func.AuthLevel.FUNCTION)
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    """Update a task"""
    logger.info('Update task endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate request
        try:
            update_request = UpdateTaskRequest(**req_body)
            updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        except Exception as e:
            return func.HttpResponse(
                json.dumps({"error": f"Validation error: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Update task
        updated_task = task_repository.update_task(task_id, user_id, updates)
        
        if not updated_task:
            return func.HttpResponse(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(updated_task.model_dump(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/{task_id}", methods=["DELETE"], auth_level=func.AuthLevel.FUNCTION)
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a task"""
    logger.info('Delete task endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        success = task_repository.delete_task(task_id, user_id)
        
        if not success:
            return func.HttpResponse(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps({"message": "Task deleted successfully"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/overdue", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def get_overdue_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Get overdue tasks for a user"""
    logger.info('Get overdue tasks endpoint triggered.')
    
    try:
        user_id = req.params.get('user_id')
        
        if not user_id:
            return func.HttpResponse(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        tasks = task_repository.get_overdue_tasks(user_id)
        tasks_data = [task.model_dump() for task in tasks]
        
        return func.HttpResponse(
            json.dumps(tasks_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_overdue_tasks: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )