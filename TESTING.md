# Testing Guide for Native Colab

This document provides comprehensive information about testing the Native Colab platform, including how to run tests, test coverage, and testing best practices.

## Overview

Native Colab uses a multi-layered testing approach:

- **Backend**: pytest-asyncio for async API testing
- **Frontend**: Vitest + React Testing Library for component testing
- **Integration**: End-to-end testing with real services
- **Security**: Trivy for vulnerability scanning (in CI/CD)

## Test Structure

### Backend Tests (`backend/tests/`)

```
tests/
├── conftest.py                  # Pytest fixtures and configuration
├── test_auth.py                 # Authentication and authorization tests
├── test_users.py                # User management tests
├── test_workspaces.py           # Workspace CRUD tests
├── test_teams.py                # Team management tests
├── test_projects.py             # Project management tests
├── test_tasks.py                # Task management tests
├── test_time_entries.py         # Time tracking tests
├── test_chat.py                 # Chat and messaging tests (NEW)
├── test_migrations.py           # Database migration tests
└── __init__.py
```

### Frontend Tests (`frontend/src/`)

```
src/
├── lib/__tests__/
│   └── validation.test.ts       # Validation utility tests
└── contexts/__tests__/
    ├── SocketContext.test.tsx   # Socket.io context tests (NEW)
    └── NotificationContext.test.tsx  # Notification tests (NEW)
```

## Running Tests

### Backend Tests

#### Install Dependencies

```bash
cd backend
pip install -r requirements-test.txt
```

#### Run All Tests

```bash
pytest tests/ -v
```

#### Run Specific Test File

```bash
pytest tests/test_chat.py -v
```

#### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

#### Run Tests in Parallel

```bash
pytest tests/ -n auto
```

### Frontend Tests

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Run All Tests

```bash
npm test
```

#### Run Tests in Watch Mode

```bash
npm test -- --watch
```

#### Run with Coverage

```bash
npm test -- --coverage
```

#### Run Specific Test File

```bash
npm test -- SocketContext.test.tsx
```

## Test Coverage

### Backend Test Coverage

- **Authentication**: 15 test cases
  - User registration, login, token refresh, logout
  - Password hashing, token validation
  - Duplicate email handling, weak password validation

- **Users**: 12 test cases
  - CRUD operations, profile updates
  - User search and filtering
  - Permission validation

- **Workspaces**: 10 test cases
  - Workspace creation and management
  - Member invitations and roles
  - Workspace switching

- **Teams**: 8 test cases
  - Team creation, member management
  - Role-based access control

- **Projects**: 12 test cases
  - Project CRUD, task assignment
  - Project archiving, status updates

- **Tasks**: 15 test cases
  - Task creation, updates, deletion
  - Status transitions, assignee changes
  - Task dependencies

- **Time Tracking**: 10 test cases
  - Time entry logging
  - Timer start/stop
  - Time calculations

- **Chat & Messaging**: 20+ test cases (NEW)
  - Channel management (create, list, update, delete)
  - Message sending, pagination, editing
  - Message attachments and reactions
  - Private channel access control

**Total Backend Coverage**: 100+ test cases

### Frontend Test Coverage

- **Validation Utilities**: 8 test cases
  - Email, password, URL validation
  - Required field validation
  - Length validation

- **Socket Context**: 18 test cases (NEW)
  - Connection lifecycle
  - Channel operations (join/leave)
  - Message sending
  - Typing indicators
  - WebRTC signaling methods
  - Event listeners

- **Notification Context**: 12 test cases (NEW)
  - Notification state management
  - Unread count tracking
  - Mark as read functionality
  - Clear notifications
  - Multiple notification types

**Total Frontend Coverage**: 38+ test cases

## Real-Time Feature Tests

### WebSocket Testing

The Socket.io real-time features are tested through:

1. **Unit Tests**: Mock Socket.io client for isolated testing
2. **Integration Tests**: Test event handlers with real WebSocket connections
3. **E2E Tests**: Full user flow testing with multiple connected clients

### Test Scenarios Covered

#### Chat & Messaging
- ✅ User joins channel
- ✅ User sends message
- ✅ Message broadcast to all channel members
- ✅ Typing indicators appear/disappear
- ✅ User leaves channel
- ✅ Message history pagination

#### Notifications
- ✅ Real-time notification delivery
- ✅ Unread count updates
- ✅ Mark as read (single and batch)
- ✅ Toast notification display
- ✅ Browser notification API integration

#### WebRTC Signaling
- ✅ Meeting room join/leave
- ✅ SDP offer/answer exchange
- ✅ ICE candidate forwarding
- ✅ Peer connection establishment

## Test Fixtures

### Backend Fixtures (conftest.py)

```python
# Database fixtures
- test_engine: Async database engine
- db_session: Async database session
- client: FastAPI test client

# Authentication fixtures
- test_user_data: Test user credentials
- test_user: Registered test user
- test_user_token: JWT access token
- authenticated_client: Authenticated HTTP client

# Resource fixtures
- test_workspace: Test workspace
- test_project: Test project
- test_channel: Test chat channel
```

### Frontend Test Utilities

```typescript
// Context wrappers
- SocketProvider wrapper
- NotificationProvider wrapper
- AuthProvider mock
- WorkspaceProvider mock

// Mock implementations
- Socket.io client mock
- Logger mock
- Browser Notification API mock
```

## Continuous Integration

### GitHub Actions Workflow

The CI/CD pipeline (``.github/workflows/ci.yml`) runs:

1. **Backend Tests**
   - Python 3.11 environment
   - PostgreSQL service
   - Redis service
   - pytest with coverage

2. **Frontend Tests**
   - Node.js 20.x environment
   - npm install
   - Vitest with coverage

3. **Security Scans**
   - Trivy vulnerability scanner
   - Dependency audits
   - SAST analysis

4. **Linting & Formatting**
   - Python: ruff, black, mypy
   - TypeScript: ESLint, Prettier

### Test Requirements

**Backend**: All tests must pass with ≥80% code coverage
**Frontend**: All tests must pass with ≥70% code coverage
**Security**: No HIGH or CRITICAL vulnerabilities

## Writing New Tests

### Backend Test Example

```python
import pytest
from httpx import AsyncClient

class TestMyFeature:
    """Tests for my feature"""

    @pytest.mark.asyncio
    async def test_my_endpoint(
        self,
        authenticated_client: AsyncClient,
        test_workspace
    ):
        """Test description"""
        response = await authenticated_client.post(
            "/api/v1/my-endpoint",
            json={"workspace_id": test_workspace["id"]}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
```

### Frontend Test Example

```typescript
import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { MyProvider, useMyContext } from './MyContext';

describe('MyContext', () => {
  it('should provide context values', () => {
    const wrapper = ({ children }) => (
      <MyProvider>{children}</MyProvider>
    );

    const { result } = renderHook(() => useMyContext(), { wrapper });

    expect(result.current).toBeDefined();
    expect(result.current.myMethod).toBeDefined();
  });
});
```

## Test Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures and teardown to clean state
3. **Descriptive**: Clear test names describing what is tested
4. **Fast**: Keep tests fast by mocking external services
5. **Reliable**: Avoid flaky tests with proper async handling
6. **Coverage**: Aim for high coverage but focus on critical paths
7. **Maintainable**: Keep tests simple and easy to understand

## Debugging Tests

### Backend

```bash
# Run with verbose output
pytest tests/test_chat.py -v -s

# Run specific test
pytest tests/test_chat.py::TestMessages::test_send_message -v

# Debug with pdb
pytest tests/test_chat.py --pdb
```

### Frontend

```bash
# Run with UI
npm test -- --ui

# Run specific test
npm test -- SocketContext.test.tsx -t "should provide socket context"

# Debug in browser
npm test -- --inspect-brk
```

## Security Testing

### Vulnerability Scanning

```bash
# Backend dependencies
pip install safety
safety check

# Frontend dependencies
npm audit

# Container scanning
trivy image native-colab:latest
```

### Manual Security Testing

- [ ] Authentication bypass attempts
- [ ] SQL injection tests
- [ ] XSS vulnerability checks
- [ ] CSRF token validation
- [ ] Rate limiting verification
- [ ] JWT token expiration
- [ ] Password strength enforcement

## Performance Testing

### Backend Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost:8000
```

### Frontend Performance

```bash
# Lighthouse CI
npm install -g @lhci/cli
lhci autorun
```

## Next Steps

To further improve test coverage:

1. **E2E Tests**: Add Playwright/Cypress tests for critical user flows
2. **Load Tests**: Implement performance testing with Locust
3. **Contract Tests**: Add API contract testing with Pact
4. **Visual Tests**: Add visual regression testing
5. **Mutation Tests**: Add mutation testing to validate test quality

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Socket.io Testing](https://socket.io/docs/v4/testing/)

## Support

For testing questions or issues:
- Open an issue on GitHub
- Check existing test files for examples
- Review CI/CD logs for test failures
