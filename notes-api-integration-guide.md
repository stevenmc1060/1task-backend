# Notes Application API Integration Guide

This document details the requirements and specifications for integrating a notes application with the 1TaskAssistant backend APIs.

## Overview

The 1TaskAssistant backend provides a comprehensive notes API that supports:
- **Notes Management**: Full CRUD operations for notes with markdown content
- **Folder Organization**: Hierarchical folder structure for organizing notes
- **File Attachments**: Support for file attachments with base64 encoding or blob URLs
- **Search & Filtering**: Advanced search, tagging, and filtering capabilities
- **Task Integration**: Convert notes to tasks with deep linking

## Base API Information

- **Base URL**: `https://1task-backend-api-gse0fsgngtfxhjc6.southcentralus-01.azurewebsites.net/api`
- **Authentication**: Currently using `AuthLevel.ANONYMOUS` (no authentication required)
- **Content-Type**: `application/json`
- **CORS**: Enabled for multiple origins including localhost and Azure Static Web Apps

## Data Models

### Note Model
```json
{
  "id": "string (UUID)",
  "user_id": "string (required - partition key)",
  "title": "string (required)",
  "content": "string (markdown content)",
  "tags": ["string array"],
  "is_pinned": "boolean (default: false)",
  "folder_id": "string or null (parent folder)",
  "attachments": [FileAttachment],
  "created_at": "datetime (ISO format)",
  "updated_at": "datetime (ISO format)"
}
```

### Folder Model
```json
{
  "id": "string (UUID)",
  "user_id": "string (required - partition key)",
  "name": "string (required)",
  "parent_id": "string or null (parent folder)",
  "color": "string (CSS class, default: 'bg-gray-500')",
  "created_at": "datetime (ISO format)"
}
```

### FileAttachment Model
```json
{
  "id": "string (UUID)",
  "name": "string (filename)",
  "size": "integer (bytes)",
  "type": "string (MIME type)",
  "data": "string (base64 encoded OR Azure Blob URL)",
  "uploaded_at": "datetime (ISO format)"
}
```

## API Endpoints

### Notes Endpoints

#### 1. Get Notes (with filtering)
```http
GET /api/notes?user_id={user_id}&folderId={folder_id}&search={term}&tag={tag}&pinned={true/false}
```

**Query Parameters:**
- `user_id` (required): User identifier
- `folderId` (optional): Filter by folder ID (null for root level)
- `search` (optional): Search term for title/content
- `tag` (optional): Filter by specific tag
- `pinned` (optional): Filter pinned notes only

**Response:**
```json
{
  "notes": [Note]
}
```

#### 2. Create Note
```http
POST /api/notes
```

**Request Body:**
```json
{
  "user_id": "string (required)",
  "title": "string (required)",
  "content": "string (optional, default: '')",
  "tags": ["string array (optional)"],
  "is_pinned": "boolean (optional, default: false)",
  "folder_id": "string or null (optional)",
  "attachments": [FileAttachment] "(optional)"
}
```

**Response:** Note object

#### 3. Get Single Note
```http
GET /api/notes/{note_id}?user_id={user_id}
```

**Response:** Note object

#### 4. Update Note
```http
PATCH /api/notes/{note_id}
```

**Request Body (all fields optional):**
```json
{
  "user_id": "string (required for authorization)",
  "title": "string",
  "content": "string",
  "tags": ["string array"],
  "is_pinned": "boolean",
  "folder_id": "string or null",
  "attachments": [FileAttachment]
}
```

**Response:** Updated Note object

#### 5. Delete Note
```http
DELETE /api/notes/{note_id}?user_id={user_id}
```

**Response:** `{"message": "Note deleted successfully"}`

### Folder Endpoints

#### 1. Get Folders
```http
GET /api/folders?user_id={user_id}&parent_id={parent_id}
```

**Query Parameters:**
- `user_id` (required): User identifier
- `parent_id` (optional): Filter by parent folder (null for root level)

**Response:**
```json
{
  "folders": [Folder]
}
```

#### 2. Create Folder
```http
POST /api/folders
```

**Request Body:**
```json
{
  "user_id": "string (required)",
  "name": "string (required)",
  "parent_id": "string or null (optional)",
  "color": "string (optional, default: 'bg-gray-500')"
}
```

**Response:** Folder object

#### 3. Update Folder
```http
PATCH /api/folders/{folder_id}
```

**Request Body (all fields optional):**
```json
{
  "user_id": "string (required for authorization)",
  "name": "string",
  "parent_id": "string or null",
  "color": "string"
}
```

**Response:** Updated Folder object

#### 4. Delete Folder
```http
DELETE /api/folders/{folder_id}?user_id={user_id}
```

**Response:** `{"message": "Folder deleted successfully"}`

## Integration Requirements

### 1. User Management
- Each user must have a unique `user_id` string
- All API calls must include the `user_id` parameter
- The `user_id` serves as the Cosmos DB partition key for optimal performance

### 2. Error Handling
Your application should handle these common error scenarios:

**400 Bad Request:**
```json
{
  "error": "user_id is required"
}
```

**404 Not Found:**
```json
{
  "error": "Note not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "An unexpected error occurred"
}
```

### 3. CORS Configuration
The API supports the following origins:
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `https://polite-field-04b5c2a10.1.azurestaticapps.net`
- `https://polite-field-04b5c2a10-preview.centralus.1.azurestaticapps.net`
- `https://agreeable-rock-0ec903610-preview.centralus.1.azurestaticapps.net`

### 4. Data Storage Considerations

#### Cosmos DB Storage Format
Notes are stored with these field mappings:
- `is_pinned` → `isPinned`
- `folder_id` → `folderId`
- `created_at` → `createdAt`
- `updated_at` → `updatedAt`
- `parent_id` → `parentId`
- Document type: `_type: "note"` or `_type: "folder"`

#### File Attachments
- Support both base64 encoded data and Azure Blob URLs
- Include proper MIME type detection
- Track file size for storage management
- Generate unique IDs for each attachment

## Implementation Examples

### JavaScript/TypeScript Client

```typescript
class NotesApiClient {
  private baseUrl = 'https://1task-backend-api-gse0fsgngtfxhjc6.southcentralus-01.azurewebsites.net/api';
  
  async getNotes(userId: string, filters?: {
    folderId?: string;
    search?: string;
    tag?: string;
    pinned?: boolean;
  }) {
    const params = new URLSearchParams({ user_id: userId });
    
    if (filters?.folderId) params.append('folderId', filters.folderId);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.tag) params.append('tag', filters.tag);
    if (filters?.pinned) params.append('pinned', 'true');
    
    const response = await fetch(`${this.baseUrl}/notes?${params}`);
    return response.json();
  }
  
  async createNote(note: CreateNoteRequest) {
    const response = await fetch(`${this.baseUrl}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(note)
    });
    return response.json();
  }
  
  async updateNote(noteId: string, updates: UpdateNoteRequest) {
    const response = await fetch(`${this.baseUrl}/notes/${noteId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return response.json();
  }
  
  // ... other methods
}
```

### Python Client

```python
import requests
from typing import Optional, List, Dict, Any

class NotesApiClient:
    def __init__(self):
        self.base_url = "https://1task-backend-api-gse0fsgngtfxhjc6.southcentralus-01.azurewebsites.net/api"
    
    def get_notes(self, user_id: str, folder_id: Optional[str] = None, 
                  search: Optional[str] = None, tag: Optional[str] = None,
                  pinned: Optional[bool] = None) -> Dict[str, Any]:
        params = {"user_id": user_id}
        
        if folder_id is not None:
            params["folderId"] = folder_id
        if search:
            params["search"] = search
        if tag:
            params["tag"] = tag
        if pinned:
            params["pinned"] = "true"
        
        response = requests.get(f"{self.base_url}/notes", params=params)
        response.raise_for_status()
        return response.json()
    
    def create_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/notes",
            json=note_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    # ... other methods
```

## Advanced Features

### 1. Search Implementation
The API supports full-text search across note titles and content. Implement search with debouncing for better UX:

```typescript
// Debounced search example
const debouncedSearch = useMemo(
  () => debounce((searchTerm: string) => {
    if (searchTerm.length >= 2) {
      notesApi.getNotes(userId, { search: searchTerm });
    }
  }, 300),
  [userId]
);
```

### 2. Real-time Updates
Consider implementing WebSocket or polling for real-time updates across multiple devices/tabs.

### 3. Offline Sync
For mobile/PWA applications, implement offline caching with sync capabilities:
- Cache notes locally using IndexedDB
- Queue mutations when offline
- Sync on reconnection

### 4. File Upload Flow
For file attachments:
1. Convert files to base64 (for small files < 1MB)
2. Or upload to Azure Blob Storage and store URLs
3. Include proper progress indicators
4. Validate file types and sizes

## Performance Considerations

### 1. Pagination
For large note collections, implement pagination:
- The API doesn't currently support pagination
- Consider client-side pagination for now
- Request pagination support for future versions

### 2. Caching Strategy
- Cache folder structure (changes infrequently)
- Cache recently viewed notes
- Implement proper cache invalidation

### 3. Optimistic Updates
Implement optimistic updates for better UX:
- Update UI immediately
- Revert on API failure
- Show loading states for async operations

## Security Considerations

### 1. User Identification
- Ensure proper user identification system
- Validate user permissions on frontend
- Plan for proper authentication implementation

### 2. Data Validation
- Validate all inputs on frontend
- Handle API validation errors gracefully
- Sanitize user content for XSS prevention

### 3. File Security
- Validate file types and sizes
- Scan uploaded files for malware
- Implement proper access controls

## Future Roadmap Items

### Near-term
- Authentication and authorization
- Pagination support
- Rate limiting
- Better error codes and messages

### Medium-term
- Real-time collaboration features
- Version history for notes
- Advanced search with filters
- Bulk operations

### Long-term
- Sharing and permissions
- Integration with external services
- Advanced analytics
- Mobile push notifications

## Testing Strategy

### 1. Unit Tests
Test individual API calls with various inputs and edge cases.

### 2. Integration Tests
Test complete workflows:
- Create note → Edit → Move to folder → Delete
- Folder creation → Add notes → Rename folder → Delete

### 3. Performance Tests
- Load testing with large datasets
- Stress testing API endpoints
- Monitor response times and resource usage

## Monitoring and Analytics

Consider tracking these metrics:
- Note creation/edit frequency
- Search usage patterns
- Folder organization patterns
- File attachment usage
- User engagement metrics

## Support and Documentation

- API endpoint documentation
- Error code reference
- Integration examples
- Best practices guide
- Troubleshooting guide

---

*This document should be updated as the API evolves and new features are added.*
