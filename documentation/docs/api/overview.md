# API Overview

Native Colab provides a comprehensive RESTful API for all platform features, with additional WebSocket support for real-time functionality.

## Base URLs

**Development:**
```
https://localhost:8000/api/v1
```

**Production:**
```
https://api.nativecolab.com/api/v1
```

## Authentication

All API endpoints (except authentication endpoints) require a valid JWT access token.

### Getting Access Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Using Access Token

Include the token in the Authorization header:

```http
GET /api/v1/projects
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## Response Format

### Success Response

```json
{
  "data": {
    "id": "123",
    "name": "Project Name"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req-abc123"
  }
}
```

## Pagination

List endpoints support pagination:

```http
GET /api/v1/projects?page=1&limit=20
```

**Response:**
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Filtering & Sorting

### Filtering

```http
GET /api/v1/tasks?status=in_progress&assignee_id=user123
```

### Sorting

```http
GET /api/v1/projects?sort=-created_at,name
```

### Search

```http
GET /api/v1/messages?q=meeting&channel_id=ch123
```

## Rate Limiting

API requests are rate limited:

- **Authenticated users**: 60 requests/minute
- **Unauthenticated**: 10 requests/minute

Rate limit info in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642252800
```

## WebSocket Connection

Real-time features use Socket.io:

```javascript
import { io } from 'socket.io-client';

const socket = io('https://api.nativecolab.com', {
  auth: {
    token: 'your-access-token'
  }
});

// Listen for events
socket.on('message:new', (data) => {
  console.log('New message:', data);
});

// Emit events
socket.emit('message:send', {
  channel_id: 'ch123',
  content: 'Hello!'
});
```

## API Modules

### Authentication
- Login, register, logout
- Token refresh
- Password reset
- OAuth providers

### Workspaces
- Create and manage workspaces
- Invite members
- Manage roles and permissions

### Projects & Tasks
- CRUD operations for projects
- Task management
- Assignments and comments
- File attachments

### Chat & Messaging
- Channels and direct messages
- Send and receive messages
- File sharing
- Reactions and threads

### Documents
- Create and edit documents
- Version history
- Sharing and permissions
- Export formats

### Time Tracking
- Log time entries
- Manage timesheets
- Reports and analytics

### Calendar
- Create events
- Manage meetings
- RSVP tracking
- External calendar sync

## Interactive Documentation

Full interactive API documentation available at:

- **Swagger UI**: https://api.nativecolab.com/docs
- **ReDoc**: https://api.nativecolab.com/redoc
- **OpenAPI JSON**: https://api.nativecolab.com/openapi.json

## SDKs & Client Libraries

Official client libraries:

- **JavaScript/TypeScript**: `npm install @nativecolab/sdk`
- **Python**: `pip install nativecolab-sdk`

## Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Invalid or missing authentication |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Invalid input data |
| `CONFLICT` | Resource conflict |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

## Webhooks

Configure webhooks to receive events:

```http
POST /api/v1/webhooks
Content-Type: application/json

{
  "url": "https://yourdomain.com/webhook",
  "events": ["message.created", "task.updated"],
  "secret": "your-webhook-secret"
}
```

## Best Practices

1. **Use HTTPS**: Always use secure connections
2. **Store Tokens Securely**: Never expose in client code
3. **Refresh Tokens**: Refresh before expiration
4. **Handle Errors**: Implement proper error handling
5. **Respect Rate Limits**: Implement exponential backoff
6. **Use Webhooks**: For real-time updates when possible
7. **Cache Responses**: Cache when appropriate
