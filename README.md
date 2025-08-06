# 1TaskAssistant Backend API

A Python Azure Functions-based backend API for the 1TaskAssistant application with CosmosDB persistence layer.

## Features

- **Task Management**: Full CRUD operations for tasks
- **User-based Partitioning**: Tasks are partitioned by user_id for optimal performance
- **Priority Management**: Support for task priorities (low, medium, high, urgent)
- **Status Tracking**: Track task status (pending, in_progress, completed, cancelled)
- **Due Date Management**: Set and track task due dates
- **Overdue Task Detection**: API endpoint to retrieve overdue tasks
- **Tag Support**: Categorize tasks with tags

## Project Structure

```
1task-backend/
├── function_app.py          # Azure Functions app with API endpoints
├── models.py                # Pydantic data models for tasks
├── cosmos_config.py         # CosmosDB configuration and connection management
├── task_repository.py       # Repository layer for task operations
├── requirements.txt         # Python dependencies
├── local.settings.json      # Local development configuration
├── host.json               # Azure Functions host configuration
└── .env.template           # Environment variables template
```

## API Endpoints

### Health Check
- `GET /api/health` - Health check endpoint

### Task Operations
- `GET /api/tasks?user_id={user_id}` - Get all tasks for a user
- `GET /api/tasks?user_id={user_id}&status={status}` - Get tasks by status
- `GET /api/tasks?user_id={user_id}&priority={priority}` - Get tasks by priority
- `POST /api/tasks` - Create a new task
- `GET /api/tasks/{task_id}?user_id={user_id}` - Get a specific task
- `PUT /api/tasks/{task_id}?user_id={user_id}` - Update a task
- `DELETE /api/tasks/{task_id}?user_id={user_id}` - Delete a task
- `GET /api/tasks/overdue?user_id={user_id}` - Get overdue tasks

## Setup and Configuration

### Prerequisites
- Python 3.11+
- Azure Functions Core Tools
- Azure CosmosDB account

### Installation

1. Clone or initialize the project:
   ```bash
   # Project is already initialized
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your CosmosDB credentials
   ```

4. Update `local.settings.json` with your CosmosDB credentials:
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "AzureWebJobsStorage": "",
       "COSMOS_ENDPOINT": "your-cosmos-endpoint",
       "COSMOS_KEY": "your-cosmos-key",
       "COSMOS_DATABASE_NAME": "1task-db",
       "COSMOS_CONTAINER_NAME": "tasks"
     }
   }
   ```

### Local Development

1. Start the Azure Functions runtime:
   ```bash
   func start
   ```

2. The API will be available at `http://localhost:7071`

### CosmosDB Setup

The application will automatically create the database and container if they don't exist:
- **Database**: `1task-db`
- **Container**: `tasks`
- **Partition Key**: `/user_id`

## Data Models

### Task Model
```python
{
    "id": "string",                    # Unique identifier
    "title": "string",                 # Task title (required)
    "description": "string",           # Task description (optional)
    "status": "pending|in_progress|completed|cancelled",
    "priority": "low|medium|high|urgent",
    "due_date": "ISO datetime",        # Optional due date
    "created_at": "ISO datetime",      # Creation timestamp
    "updated_at": "ISO datetime",      # Last update timestamp
    "completed_at": "ISO datetime",    # Completion timestamp
    "tags": ["string"],                # Array of tags
    "user_id": "string"                # User identifier (required)
}
```

## Example API Usage

### Create a Task
```bash
curl -X POST "http://localhost:7071/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README and API docs",
    "priority": "high",
    "due_date": "2025-08-10T10:00:00Z",
    "user_id": "user123",
    "tags": ["documentation", "project"]
  }'
```

### Get Tasks
```bash
# Get all tasks for a user
curl "http://localhost:7071/api/tasks?user_id=user123"

# Get completed tasks
curl "http://localhost:7071/api/tasks?user_id=user123&status=completed"

# Get high priority tasks
curl "http://localhost:7071/api/tasks?user_id=user123&priority=high"
```

### Update a Task
```bash
curl -X PUT "http://localhost:7071/api/tasks/{task_id}?user_id=user123" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "description": "Updated description"
  }'
```

## Deployment

### Deploy to Azure

1. Create an Azure Function App
2. Configure application settings with your CosmosDB credentials
3. Deploy using Azure Functions Core Tools:
   ```bash
   func azure functionapp publish <your-function-app-name>
   ```

## Development Notes

- The application uses Python 3.11+ for optimal Azure Functions performance
- CosmosDB is configured with a partition key of `/user_id` for efficient queries
- All datetime fields are stored as ISO strings for consistency
- The repository layer provides async operations for better performance
- Proper error handling and logging are implemented throughout

## Security Considerations

- Function authorization level is set to `FUNCTION` for production endpoints
- Always validate user access to tasks based on `user_id`
- Store CosmosDB credentials securely in Azure Key Vault for production
- Consider implementing authentication middleware for user validation
