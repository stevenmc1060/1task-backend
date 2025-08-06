<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# 1TaskAssistant Backend Development Instructions

This is a Python Azure Functions project for the 1TaskAssistant application backend with CosmosDB persistence.

## Project Context
- **Framework**: Azure Functions with Python 3.11
- **Database**: Azure CosmosDB with SQL API
- **Architecture**: Repository pattern with async operations
- **Data Models**: Pydantic for validation and serialization

## Key Components
- `function_app.py`: Main Azure Functions app with HTTP endpoints
- `models.py`: Pydantic data models for Task and request/response schemas
- `cosmos_config.py`: CosmosDB configuration and connection management
- `task_repository.py`: Repository layer for CRUD operations

## Development Guidelines

### Code Style
- Use async/await for all database operations
- Follow PEP 8 naming conventions
- Use type hints for all function parameters and return values
- Use Pydantic models for request/response validation
- Include comprehensive error handling and logging

### CosmosDB Best Practices
- Always use partition key (`user_id`) in queries for optimal performance
- Use parameterized queries to prevent injection attacks
- Handle CosmosResourceNotFoundError appropriately
- Convert datetime objects to ISO strings for storage

### API Design
- Use HTTP status codes appropriately (200, 201, 400, 404, 500)
- Include user_id validation for all task operations
- Return consistent JSON error responses
- Use proper HTTP methods (GET, POST, PUT, DELETE)

### Error Handling
- Log errors with appropriate detail levels
- Return user-friendly error messages
- Handle CosmosDB exceptions gracefully
- Validate input data using Pydantic models

### Testing Considerations
- Test with various user scenarios
- Validate partition key behavior
- Test error conditions and edge cases
- Verify datetime handling across timezones

When generating code, prioritize:
1. Type safety with proper annotations
2. Async operations for database calls
3. Proper error handling and logging
4. CosmosDB query optimization
5. Pydantic model validation
