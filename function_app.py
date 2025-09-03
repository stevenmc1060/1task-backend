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
    UserProfile, CreateUserProfileRequest, UpdateUserProfileRequest,
    OnboardingStatus, OnboardingStep,
    ChatSession, ChatMessage, ChatMessageRole,
    DocumentType
)
from task_repository import task_repository
from generic_repository import generic_repository
from user_profile_repository import user_profile_repo, onboarding_repo, chat_session_repo

app = func.FunctionApp()

logger = logging.getLogger(__name__)


def serialize_datetimes(obj):
    if isinstance(obj, dict):
        return {k: serialize_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetimes(i) for i in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return obj


def create_cors_response(body: str, status_code: int = 200, mimetype: str = "application/json", origin: str = None) -> func.HttpResponse:
    """Create HTTP response with CORS headers"""
    
    # Allowed origins for CORS
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://polite-field-04b5c2a10.1.azurestaticapps.net",
        "https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net",
        "https://agreeable-rock-0ec903610-preview.centralus.1.azurestaticapps.net"
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
        
        logger.info(f"[HABITS GET] Loading habits for user: {user_id}")
        
        try:
            # Try to get habits using the generic repository
            habits = generic_repository.get_documents_by_user_and_type(user_id, DocumentType.HABIT, Habit)
            logger.info(f"[HABITS GET] Retrieved {len(habits)} habit objects")
            
            # Convert to dict format
            habits_data = []
            for habit in habits:
                try:
                    habit_dict = habit.model_dump()
                    habits_data.append(habit_dict)
                except Exception as e:
                    logger.error(f"[HABITS GET] Error converting habit to dict: {e}")
                    continue
            
            logger.info(f"[HABITS GET] Successfully converted {len(habits_data)} habits to dict")
            
            # Serialize datetimes
            serialized_data = serialize_datetimes(habits_data)
            logger.info(f"[HABITS GET] Successfully serialized habits data")
            
            return create_cors_response(
                json.dumps(serialized_data),
                origin=req.headers.get('Origin')
            )
            
        except Exception as repo_error:
            logger.error(f"[HABITS GET] Repository error: {repo_error}")
            logger.error(f"[HABITS GET] Repository error details: {str(repo_error)}")
            import traceback
            logger.error(f"[HABITS GET] Repository traceback: {traceback.format_exc()}")
            
            # Return empty list if no habits found or error occurred
            return create_cors_response(json.dumps([]))
            
    except Exception as e:
        logger.error(f"[HABITS GET] General error: {e}")
        logger.error(f"[HABITS GET] Error details: {str(e)}")
        import traceback
        logger.error(f"[HABITS GET] Traceback: {traceback.format_exc()}")
        return create_cors_response(json.dumps({"error": "Internal server error"}), status_code=500)


@app.route(route="habits", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new habit"""
    try:
        req_body = req.get_json()
        logger.info(f"[HABIT CREATE] Incoming payload: {json.dumps(req_body)}")
        
        # Ensure metadata.type is always set to 'habit'
        if 'metadata' not in req_body or not isinstance(req_body['metadata'], dict):
            req_body['metadata'] = {'type': 'habit'}
        else:
            req_body['metadata']['type'] = 'habit'
        
        # Create request object with validation
        try:
            create_request = CreateHabitRequest(**req_body)
            logger.info(f"[HABIT CREATE] CreateHabitRequest validated successfully")
        except Exception as validation_error:
            logger.error(f"[HABIT CREATE] Validation error: {validation_error}")
            return create_cors_response(json.dumps({"error": f"Validation error: {str(validation_error)}"}), status_code=400)
        
        # Create Habit object
        try:
            habit_data = create_request.model_dump()
            logger.info(f"[HABIT CREATE] Raw habit_data from request: {habit_data}")
            
            # CRITICAL FIX: Explicitly ensure document_type is set to HABIT
            habit_data['document_type'] = DocumentType.HABIT
            logger.info(f"[HABIT CREATE] habit_data after setting document_type: {habit_data}")
            
            habit = Habit(**habit_data)
            logger.info(f"[HABIT CREATE] Habit object created: {habit.model_dump()}")
            logger.info(f"[HABIT CREATE] Habit.document_type value: {habit.document_type}")
            logger.info(f"[HABIT CREATE] Habit.document_type type: {type(habit.document_type)}")
        except Exception as habit_error:
            logger.error(f"[HABIT CREATE] Error creating Habit object: {habit_error}")
            return create_cors_response(json.dumps({"error": f"Habit creation error: {str(habit_error)}"}), status_code=400)
        
        # Save to database
        try:
            created_habit = generic_repository.create_document(habit)
            logger.info(f"[HABIT CREATE] Saved document: {created_habit}")
        except Exception as db_error:
            logger.error(f"[HABIT CREATE] Database error: {db_error}")
            return create_cors_response(json.dumps({"error": f"Database error: {str(db_error)}"}), status_code=500)
        
        # Always convert to dict and serialize datetimes
        if hasattr(created_habit, "model_dump"):
            created_habit_dict = created_habit.model_dump()
        elif isinstance(created_habit, dict):
            created_habit_dict = created_habit
        else:
            created_habit_dict = dict(created_habit)
        
        serialized = serialize_datetimes(created_habit_dict)
        logger.info(f"[HABIT CREATE] Returning serialized habit: {serialized}")
        
        return create_cors_response(json.dumps(serialized), status_code=201)
        
    except Exception as e:
        logger.error(f"[HABIT CREATE] Unexpected error: {e}")
        import traceback
        logger.error(f"[HABIT CREATE] Traceback: {traceback.format_exc()}")
        return create_cors_response(json.dumps({"error": str(e)}), status_code=500)


@app.route(route="habits/{habit_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_habit(req: func.HttpRequest) -> func.HttpResponse:
    """Update a habit"""
    logger.info('Update habit endpoint triggered.')
    
    try:
        habit_id = req.route_params.get('habit_id')
        user_id = req.params.get('user_id')
        
        if not user_id:
            return create_cors_response(json.dumps({"error": "user_id parameter is required"}), status_code=400)
        
        # Parse request body
        try:
            req_body = req.get_json()
            logger.info(f"[HABIT UPDATE] Incoming payload: {json.dumps(req_body)}")
        except ValueError:
            return create_cors_response(
                json.dumps({"error": "Invalid JSON in request body"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Ensure metadata.type is always set to 'habit' on update
        if 'metadata' not in req_body or not isinstance(req_body['metadata'], dict):
            req_body['metadata'] = {'type': 'habit'}
        else:
            req_body['metadata']['type'] = 'habit'
        
        # Validate request
        try:
            update_request = UpdateHabitRequest(**req_body)
            updates = {k: v for k, v in update_request.model_dump().items() if v is not None}
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Validation error: {str(e)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Ensure document_type is always set to DocumentType.HABIT on update
        updates['document_type'] = DocumentType.HABIT
    
        # Update habit
        updates = update_request.model_dump(exclude_unset=True)
        updates['document_type'] = DocumentType.HABIT  # Ensure this is always set
        updated_habit = generic_repository.update_document(habit_id, user_id, updates, Habit)
        
        # Log the saved document with proper datetime serialization
        if updated_habit:
            if hasattr(updated_habit, "model_dump"):
                log_dict = updated_habit.model_dump()
            else:
                log_dict = dict(updated_habit)
            serialized_log = serialize_datetimes(log_dict)
            logger.info(f"[HABIT UPDATE] Saved document: {json.dumps(serialized_log)}")
        else:
            logger.info("[HABIT UPDATE] Saved document: None")
            
        if not updated_habit:
            return create_cors_response(
                json.dumps({"error": "Habit not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Ensure metadata.type is always set to 'habit' in the returned object
        if hasattr(updated_habit, 'metadata') and isinstance(updated_habit.metadata, dict):
            updated_habit.metadata['type'] = 'habit'
        elif hasattr(updated_habit, 'metadata') and updated_habit.metadata is None:
            updated_habit.metadata = {'type': 'habit'}

        # Log the full outgoing response for debugging
        if hasattr(updated_habit, "model_dump"):
            updated_habit_dict = updated_habit.model_dump()
        elif isinstance(updated_habit, dict):
            updated_habit_dict = updated_habit
        else:
            updated_habit_dict = dict(updated_habit)
        serialized = serialize_datetimes(updated_habit_dict)
        logger.info(f"[HABIT UPDATE RESPONSE] Returning: {json.dumps(serialized)}")

        return create_cors_response(
            json.dumps(serialized),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in update_habit: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )


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


@app.route(route="habits", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def habits_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for habits endpoint"""
    origin = req.headers.get('Origin')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080", 
        "https://polite-field-04b5c2a10.1.azurestaticapps.net",
        "https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net"
    ]
    
    allowed_origin = "*"
    if origin and origin in allowed_origins:
        allowed_origin = origin
    
    return func.HttpResponse(
        "",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true" if origin and origin in allowed_origins else "false"
        }
    )


@app.route(route="habits/{habit_id}", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def habit_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for specific habit endpoint"""
    origin = req.headers.get('Origin')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://polite-field-04b5c2a10.1.azurestaticapps.net",
        "https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net"
    ]
    
    allowed_origin = "*"
    if origin and origin in allowed_origins:
        allowed_origin = origin
    
    return func.HttpResponse(
        "",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true" if origin and origin in allowed_origins else "false"
        }
    )


# =====================
# User Profile API Endpoints
# =====================

@app.route(route="profiles", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new user profile"""
    try:
        # Get user_id from header or request
        user_id = req.headers.get('X-User-Id')
        if not user_id:
            body = req.get_json()
            user_id = body.get('user_id') if body else None
            
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Parse request body
        try:
            request_data = req.get_json()
            create_request = CreateUserProfileRequest(**request_data)
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Invalid request data: {str(e)}"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Create profile using repository
        profile = user_profile_repo.create_user_profile(user_id, create_request)
        
        # Also create initial onboarding status
        onboarding_repo.create_onboarding_status(user_id)
        
        # Convert to dict and serialize
        profile_dict = profile.to_cosmos_dict()
        serialized_profile = serialize_datetimes(profile_dict)
        
        return create_cors_response(
            json.dumps(serialized_profile),
            status_code=201,
            origin=req.headers.get('Origin')
        )
        
    except ValueError as e:
        if "already exists" in str(e):
            return create_cors_response(
                json.dumps({"error": str(e)}),
                status_code=409,
                origin=req.headers.get('Origin')
            )
        return create_cors_response(
            json.dumps({"error": str(e)}),
            status_code=400,
            origin=req.headers.get('Origin')
        )
    except Exception as e:
        logging.error(f"Error creating profile: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="profiles/{user_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Get user profile by user_id"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Get profile using repository
        profile = user_profile_repo.get_user_profile(user_id)
        
        if not profile:
            return create_cors_response(
                json.dumps({"error": "Profile not found"}),
                status_code=404,
                origin=req.headers.get('Origin')
            )
        
        # Convert to dict and serialize
        profile_dict = profile.to_cosmos_dict()
        serialized_profile = serialize_datetimes(profile_dict)
        
        return create_cors_response(
            json.dumps(serialized_profile),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error getting profile: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="profiles/{user_id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Update user profile"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Parse request body
        try:
            request_data = req.get_json()
            update_request = UpdateUserProfileRequest(**request_data)
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Invalid request data: {str(e)}"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Update profile using repository
        profile = user_profile_repo.update_user_profile(user_id, update_request)
        
        if not profile:
            return create_cors_response(
                json.dumps({"error": "Profile not found"}),
                status_code=404,
                origin=req.headers.get('Origin')
            )
        
        # Convert to dict and serialize
        profile_dict = profile.to_cosmos_dict()
        serialized_profile = serialize_datetimes(profile_dict)
        
        return create_cors_response(
            json.dumps(serialized_profile),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error updating profile: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="profiles/{user_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Delete user profile and all associated data"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Delete profile using repository (also deletes onboarding and chat data)
        success = user_profile_repo.delete_user_profile(user_id)
        
        if not success:
            return create_cors_response(
                json.dumps({"error": "Profile not found"}),
                status_code=404,
                origin=req.headers.get('Origin')
            )
        
        return create_cors_response(
            json.dumps({"message": "Profile and associated data deleted successfully"}),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error deleting profile: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


# =====================
# Onboarding API Endpoints
# =====================

@app.route(route="onboarding/{user_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_onboarding_status(req: func.HttpRequest) -> func.HttpResponse:
    """Get onboarding status for user"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Get onboarding status using repository
        onboarding = onboarding_repo.get_onboarding_status(user_id)
        
        if not onboarding:
            # Create initial onboarding status if it doesn't exist
            onboarding = onboarding_repo.create_onboarding_status(user_id)
        
        # Convert to dict and serialize
        onboarding_dict = onboarding.to_cosmos_dict()
        serialized_onboarding = serialize_datetimes(onboarding_dict)
        
        return create_cors_response(
            json.dumps(serialized_onboarding),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error getting onboarding status: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="onboarding/{user_id}/step", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_onboarding_step(req: func.HttpRequest) -> func.HttpResponse:
    """Update onboarding step"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Parse request body
        try:
            request_data = req.get_json()
            step = OnboardingStep(request_data.get('step'))
            interview_data = request_data.get('interview_data', {})
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Invalid request data: {str(e)}"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Update onboarding step using repository
        onboarding = onboarding_repo.update_onboarding_step(user_id, step, interview_data)
        
        if not onboarding:
            return create_cors_response(
                json.dumps({"error": "Failed to update onboarding"}),
                status_code=500,
                origin=req.headers.get('Origin')
            )
        
        # Convert to dict and serialize
        onboarding_dict = onboarding.to_cosmos_dict()
        serialized_onboarding = serialize_datetimes(onboarding_dict)
        
        return create_cors_response(
            json.dumps(serialized_onboarding),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error updating onboarding step: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


# =====================
# Chat Session API Endpoints
# =====================

@app.route(route="chat/{user_id}/sessions", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_chat_sessions(req: func.HttpRequest) -> func.HttpResponse:
    """Get recent chat sessions for user"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Get limit from query params (default 5)
        limit = int(req.params.get('limit', '5'))
        
        # Get chat sessions using repository
        sessions = chat_session_repo.get_recent_chat_sessions(user_id, limit)
        
        # Convert to dict and serialize
        sessions_data = []
        for session in sessions:
            session_dict = session.to_cosmos_dict()
            serialized_session = serialize_datetimes(session_dict)
            sessions_data.append(serialized_session)
        
        return create_cors_response(
            json.dumps(sessions_data),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error getting chat sessions: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="chat/{user_id}/sessions", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_chat_session(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new chat session"""
    try:
        user_id = req.route_params.get('user_id')
        if not user_id:
            return create_cors_response(
                json.dumps({"error": "user_id is required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Parse request body
        try:
            request_data = req.get_json()
            title = request_data.get('title', f"Chat {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Invalid request data: {str(e)}"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Create chat session using repository
        session = chat_session_repo.create_chat_session(user_id, title)
        
        # Convert to dict and serialize
        session_dict = session.to_cosmos_dict()
        serialized_session = serialize_datetimes(session_dict)
        
        return create_cors_response(
            json.dumps(serialized_session),
            status_code=201,
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error creating chat session: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


@app.route(route="chat/{user_id}/sessions/{session_id}/messages", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def add_chat_message(req: func.HttpRequest) -> func.HttpResponse:
    """Add a message to a chat session"""
    try:
        user_id = req.route_params.get('user_id')
        session_id = req.route_params.get('session_id')
        
        if not user_id or not session_id:
            return create_cors_response(
                json.dumps({"error": "user_id and session_id are required"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Parse request body
        try:
            request_data = req.get_json()
            role = ChatMessageRole(request_data.get('role'))
            content = request_data.get('content')
            
            if not content:
                raise ValueError("Message content is required")
                
            message = ChatMessage(role=role, content=content)
        except Exception as e:
            return create_cors_response(
                json.dumps({"error": f"Invalid message data: {str(e)}"}),
                status_code=400,
                origin=req.headers.get('Origin')
            )
        
        # Add message to session using repository
        session = chat_session_repo.add_message_to_session(user_id, session_id, message)
        
        if not session:
            return create_cors_response(
                json.dumps({"error": "Session not found"}),
                status_code=404,
                origin=req.headers.get('Origin')
            )
        
        # Convert to dict and serialize
        session_dict = session.to_cosmos_dict()
        serialized_session = serialize_datetimes(session_dict)
        
        return create_cors_response(
            json.dumps(serialized_session),
            origin=req.headers.get('Origin')
        )
        
    except Exception as e:
        logging.error(f"Error adding chat message: {e}")
        return create_cors_response(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            origin=req.headers.get('Origin')
        )


# =====================
# CORS Options Endpoints for User Profile APIs
# =====================

@app.route(route="profiles", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def profiles_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for profiles endpoint"""
    origin = req.headers.get('Origin')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://polite-field-04b5c2a10.1.azurestaticapps.net",
        "https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net"
    ]
    
    allowed_origin = "*"
    if origin and origin in allowed_origins:
        allowed_origin = origin
    
    return func.HttpResponse(
        "",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-User-Id",
            "Access-Control-Allow-Credentials": "true" if origin and origin in allowed_origins else "false"
        }
    )


@app.route(route="profiles/{user_id}", methods=["OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)  
def profile_options(req: func.HttpRequest) -> func.HttpResponse:
    """Handle CORS preflight requests for specific profile endpoint"""
    origin = req.headers.get('Origin')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://polite-field-04b5c2a10.1.azurestaticapps.net",
        "https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net"
    ]
    
    allowed_origin = "*"
    if origin and origin in allowed_origins:
        allowed_origin = origin
    
    return func.HttpResponse(
        "",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-User-Id",
            "Access-Control-Allow-Credentials": "true" if origin and origin in allowed_origins else "false"
        }
    )