import azure.functions as func
import datetime
import json
import logging
from models import (
    Task, CreateTaskRequest, UpdateTaskRequest, TaskStatus, TaskPriority,
    YearlyGoal, CreateYearlyGoalRequest, UpdateYearlyGoalRequest,
    QuarterlyGoal, CreateQuarterlyGoalRequest, UpdateQuarterlyGoalRequest,
    WeeklyGoal, CreateWeeklyGoalRequest, UpdateWeeklyGoalRequest,
    Habit, CreateHabitRequest, UpdateHabitRequest,
    Project, CreateProjectRequest, UpdateProjectRequest,
    DocumentType
)
from task_repository import task_repository
from generic_repository import generic_repository

app = func.FunctionApp()

logger = logging.getLogger(__name__)


def create_cors_response(body: str, status_code: int = 200, mimetype: str = "application/json", origin: str = None) -> func.HttpResponse:
    """Create HTTP response with CORS headers"""
    
    # Allowed origins for CORS
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://polite-field-04b5c2a10.1.azurestaticapps.net"
    ]
    
    # Determine allowed origin
    allowed_origin = "*"
    if origin and origin in allowed_origins:
        allowed_origin = origin
    
    return func.HttpResponse(
        body,
        status_code=status_code,
        mimetype=mimetype,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true" if origin and origin in allowed_origins else "false"
        }
    )


def create_cors_response_from_request(req: func.HttpRequest, body: str, status_code: int = 200, mimetype: str = "application/json") -> func.HttpResponse:
    """Create HTTP response with CORS headers, automatically extracting origin from request"""
    origin = req.headers.get('Origin')
    return create_cors_response(body, status_code, mimetype, origin)


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info('Health check endpoint triggered.')
    
    return create_cors_response_from_request(
        req,
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "service": "1TaskAssistant API"
        })
    )


@app.route(route="health", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def health_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for health endpoint"""
    return create_cors_response_from_request(req, "", status_code=200)


@app.route(route="tasks", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Get tasks for a user"""
    logger.info('Get tasks endpoint triggered.')
    
    try:
        # Get query parameters
        user_id = req.params.get('user_id')
        status = req.params.get('status')
        priority = req.params.get('priority')
        
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400
            )
        
        # Get all tasks for the user using generic repository
        tasks = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.TASK, Task)
        
        # Apply filters if provided
        if status:
            task_status = TaskStatus(status) if status in [s.value for s in TaskStatus] else None
            if not task_status:
                return create_cors_response(
                    json.dumps({"error": f"Invalid status: {status}"}),
                    status_code=400,
                    mimetype="application/json"
                )
            tasks = [task for task in tasks if task.status == task_status]
        
        if priority:
            task_priority = TaskPriority(priority) if priority in [p.value for p in TaskPriority] else None
            if not task_priority:
                return create_cors_response(
                    json.dumps({"error": f"Invalid priority: {priority}"}),
                    status_code=400,
                    mimetype="application/json"
                )
            tasks = [task for task in tasks if task.priority == task_priority]
        
        # Convert tasks to dict format
        tasks_data = [task.model_dump() for task in tasks]
        
        return create_cors_response(
            json.dumps(tasks_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_tasks: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new task"""
    logger.info('Create task endpoint triggered.')
    
    try:
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return create_cors_response(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400
            )
        
        # Validate request
        try:
            create_request = CreateTaskRequest(**req_body)
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Validation error: {str(e)}"}),
                status_code=400
            )
        
        # Create task
        task = Task(**create_request.model_dump())
        created_task = generic_repository.create_document(task)
        
        return create_cors_response(
            json.dumps(created_task.model_dump(), default=str),
            status_code=201
        )
        
    except ValueError as ve:
        logger.error(f"Validation error in create_task: {ve}")
        return create_cors_response(
            json.dumps({"error": f"Validation error: {str(ve)}"}),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        return create_cors_response(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500
        )


@app.route(route="tasks/{task_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    """Get a specific task by ID"""
    logger.info('Get task by ID endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        task = generic_repository.get_document_by_id(task_id, user_id, Task)
        
        if not task:
            return create_cors_response(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return create_cors_response(
            json.dumps(task.model_dump(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_task_by_id: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/{task_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    """Update a task"""
    logger.info('Update task endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Parse request body
        try:
            req_body = req.get_json()
        except ValueError:
            return create_cors_response(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate request
        try:
            update_request = UpdateTaskRequest(**req_body)
            updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Validation error: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Update task
        updates = update_request.model_dump(exclude_unset=True)
        updated_task = generic_repository.update_document(task_id, user_id, updates, Task)
        
        if not updated_task:
            return create_cors_response(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return create_cors_response(
            json.dumps(updated_task.model_dump(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/{task_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a task"""
    logger.info('Delete task endpoint triggered.')
    
    try:
        task_id = req.route_params.get('task_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        success = generic_repository.delete_document(task_id, user_id)
        
        if not success:
            return create_cors_response(
                json.dumps({"error": "Task not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return create_cors_response(
            json.dumps({"message": "Task deleted successfully"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks/overdue", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_overdue_tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Get overdue tasks for a user"""
    logger.info('Get overdue tasks endpoint triggered.')
    
    try:
        user_id = req.params.get('user_id')
        
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id parameter is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get all tasks and filter for overdue ones
        tasks = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.TASK, Task)
        from datetime import datetime
        now = datetime.utcnow()
        overdue_tasks = [task for task in tasks if task.due_date and task.due_date < now and task.status != TaskStatus.COMPLETED]
        tasks_data = [task.model_dump() for task in overdue_tasks]
        
        return create_cors_response(
            json.dumps(tasks_data, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in get_overdue_tasks: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


@app.route(route="tasks", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def tasks_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for tasks endpoints"""
    return create_cors_response_from_request(req, "", status_code=200)


@app.route(route="tasks/{task_id}", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def task_by_id_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for task by ID endpoints"""
    return create_cors_response_from_request(req, "", status_code=200)


@app.route(route="tasks/overdue", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def overdue_tasks_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for overdue tasks endpoint"""
    return create_cors_response_from_request(req, "", status_code=200)


# =============================================================================
# YEARLY GOALS ENDPOINTS
# =============================================================================

@app.route(route="yearly-goals", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_yearly_goals(req: func.HttpRequest) -> func.HttpResponse:
    """Get yearly goals for a user"""
    try:
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        goals = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.YEARLY_GOAL, YearlyGoal)
        goals_data = [goal.model_dump() for goal in goals]
        
        return create_cors_response(json.dumps(goals_data, default=str))
    except Exception as e:
        logger.error(f"Error in get_yearly_goals: {e}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="yearly-goals", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_yearly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new yearly goal"""
    try:
        req_body = req.get_json()
        create_request = CreateYearlyGoalRequest(**req_body)
        goal = YearlyGoal(**create_request.model_dump())
        created_goal = generic_repository.create_document(goal)
        
        return create_cors_response(json.dumps(created_goal.model_dump(), default=str), status_code=201)
    except Exception as e:
        logger.error(f"Error in create_yearly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="yearly-goals/{goal_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_yearly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Update a yearly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        req_body = req.get_json()
        update_request = UpdateYearlyGoalRequest(**req_body)
        updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        
        updated_goal = generic_repository.update_document(goal_id, user_id, updates, YearlyGoal)
        if not updated_goal:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps(updated_goal.model_dump(), default=str))
    except Exception as e:
        logger.error(f"Error in update_yearly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="yearly-goals/{goal_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_yearly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a yearly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        success = generic_repository.delete_document(goal_id, user_id)
        if not success:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps({"message": "Goal deleted successfully"}))
    except Exception as e:
        logger.error(f"Error in delete_yearly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


# =============================================================================
# QUARTERLY GOALS ENDPOINTS
# =============================================================================

@app.route(route="quarterly-goals", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_quarterly_goals(req: func.HttpRequest) -> func.HttpResponse:
    """Get quarterly goals for a user"""
    try:
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        goals = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.QUARTERLY_GOAL, QuarterlyGoal)
        goals_data = [goal.model_dump() for goal in goals]
        
        return create_cors_response(json.dumps(goals_data, default=str))
    except Exception as e:
        logger.error(f"Error in get_quarterly_goals: {e}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="quarterly-goals", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_quarterly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new quarterly goal"""
    try:
        req_body = req.get_json()
        create_request = CreateQuarterlyGoalRequest(**req_body)
        goal = QuarterlyGoal(**create_request.model_dump())
        created_goal = generic_repository.create_document(goal)
        
        return create_cors_response(json.dumps(created_goal.model_dump(), default=str), status_code=201)
    except Exception as e:
        logger.error(f"Error in create_quarterly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="quarterly-goals/{goal_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_quarterly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Update a quarterly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        req_body = req.get_json()
        update_request = UpdateQuarterlyGoalRequest(**req_body)
        updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        
        updated_goal = generic_repository.update_document(goal_id, user_id, updates, QuarterlyGoal)
        if not updated_goal:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps(updated_goal.model_dump(), default=str))
    except Exception as e:
        logger.error(f"Error in update_quarterly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="quarterly-goals/{goal_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_quarterly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a quarterly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        success = generic_repository.delete_document(goal_id, user_id)
        if not success:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps({"message": "Goal deleted successfully"}))
    except Exception as e:
        logger.error(f"Error in delete_quarterly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


# =============================================================================
# WEEKLY GOALS ENDPOINTS
# =============================================================================

@app.route(route="weekly-goals", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_weekly_goals(req: func.HttpRequest) -> func.HttpResponse:
    """Get weekly goals for a user"""
    try:
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        goals = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.WEEKLY_GOAL, WeeklyGoal)
        goals_data = [goal.model_dump() for goal in goals]
        
        return create_cors_response(json.dumps(goals_data, default=str))
    except Exception as e:
        logger.error(f"Error in get_weekly_goals: {e}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="weekly-goals", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_weekly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new weekly goal"""
    try:
        req_body = req.get_json()
        create_request = CreateWeeklyGoalRequest(**req_body)
        goal = WeeklyGoal(**create_request.model_dump())
        created_goal = generic_repository.create_document(goal)
        
        return create_cors_response(json.dumps(created_goal.model_dump(), default=str), status_code=201)
    except Exception as e:
        logger.error(f"Error in create_weekly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="weekly-goals/{goal_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_weekly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Update a weekly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        req_body = req.get_json()
        update_request = UpdateWeeklyGoalRequest(**req_body)
        updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        
        updated_goal = generic_repository.update_document(goal_id, user_id, updates, WeeklyGoal)
        if not updated_goal:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps(updated_goal.model_dump(), default=str))
    except Exception as e:
        logger.error(f"Error in update_weekly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="weekly-goals/{goal_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_weekly_goal(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a weekly goal"""
    try:
        goal_id = req.route_params.get('goal_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        success = generic_repository.delete_document(goal_id, user_id)
        if not success:
            return create_cors_response(json.dumps({"error": "Goal not found"}), status_code=404)
        
        return create_cors_response(json.dumps({"message": "Goal deleted successfully"}))
    except Exception as e:
        logger.error(f"Error in delete_weekly_goal: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


# =============================================================================
# HABITS ENDPOINTS
# =============================================================================

@app.route(route="habits", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_habits(req: func.HttpRequest) -> func.HttpResponse:
    """Get habits for a user"""
    try:
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        habits = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.HABIT, Habit)
        habits_data = [habit.model_dump() for habit in habits]
        
        return create_cors_response(json.dumps(habits_data, default=str))
    except Exception as e:
        logger.error(f"Error in get_habits: {e}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="habits", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new habit"""
    try:
        req_body = req.get_json()
        create_request = CreateHabitRequest(**req_body)
        habit = Habit(**create_request.model_dump())
        created_habit = generic_repository.create_document(habit)
        
        return create_cors_response(json.dumps(created_habit.model_dump(), default=str), status_code=201)
    except Exception as e:
        logger.error(f"Error in create_habit: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="habits/{habit_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Update a habit"""
    try:
        habit_id = req.route_params.get('habit_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        req_body = req.get_json()
        update_request = UpdateHabitRequest(**req_body)
        updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        
        updated_habit = generic_repository.update_document(habit_id, user_id, updates, Habit)
        if not updated_habit:
            return create_cors_response(json.dumps({"error": "Habit not found"}), status_code=404)
        
        return create_cors_response(json.dumps(updated_habit.model_dump(), default=str))
    except Exception as e:
        logger.error(f"Error in update_habit: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="habits/{habit_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a habit"""
    try:
        habit_id = req.route_params.get('habit_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        success = generic_repository.delete_document(habit_id, user_id)
        if not success:
            return create_cors_response(json.dumps({"error": "Habit not found"}), status_code=404)
        
        return create_cors_response(json.dumps({"message": "Habit deleted successfully"}))
    except Exception as e:
        logger.error(f"Error in delete_habit: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


# =============================================================================
# PROJECTS ENDPOINTS
# =============================================================================

@app.route(route="projects", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_projects(req: func.HttpRequest) -> func.HttpResponse:
    """Get projects for a user"""
    try:
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        projects = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.PROJECT, Project)
        projects_data = [project.model_dump() for project in projects]
        
        return create_cors_response(json.dumps(projects_data, default=str))
    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="projects", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_project(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new project"""
    try:
        req_body = req.get_json()
        create_request = CreateProjectRequest(**req_body)
        project = Project(**create_request.model_dump())
        created_project = generic_repository.create_document(project)
        
        return create_cors_response(json.dumps(created_project.model_dump(), default=str), status_code=201)
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="projects/{project_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_project(req: func.HttpRequest) -> func.HttpResponse:
    """Update a project"""
    try:
        project_id = req.route_params.get('project_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        req_body = req.get_json()
        update_request = UpdateProjectRequest(**req_body)
        updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        
        updated_project = generic_repository.update_document(project_id, user_id, updates, Project)
        if not updated_project:
            return create_cors_response(json.dumps({"error": "Project not found"}), status_code=404)
        
        return create_cors_response(json.dumps(updated_project.model_dump(), default=str))
    except Exception as e:
        logger.error(f"Error in update_project: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=400)


@app.route(route="projects/{project_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_project(req: func.HttpRequest) -> func.HttpResponse:
    """Delete a project"""
    try:
        project_id = req.route_params.get('project_id')
        user_id = req.params.get('user_id')
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        success = generic_repository.delete_document(project_id, user_id)
        if not success:
            return create_cors_response(json.dumps({"error": "Project not found"}), status_code=404)
        
        return create_cors_response(json.dumps({"message": "Project deleted successfully"}))
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


@app.route(route="projects", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def projects_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for projects endpoints"""
    return create_cors_response_from_request(req, "", status_code=200)


@app.route(route="projects/{project_id}", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def project_by_id_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for project by ID endpoints"""
    return create_cors_response_from_request(req, "", status_code=200)