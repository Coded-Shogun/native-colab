# Contributing to Native Colab

Thank you for your interest in contributing to Native Colab! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community.

---

## Getting Started

### Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **Git** for version control

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/native-colab.git
   cd native-colab
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/native-colab.git
   ```

---

## Development Setup

### Quick Start with Docker

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- pgAdmin: http://localhost:5050
- Redis Commander: http://localhost:8081
- MailHog: http://localhost:8025

### Local Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Project Structure

```
native-colab/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── core/     # Configuration
│   │   ├── db/       # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── tests/
├── frontend/          # React + Vite application
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── services/
│   └── public/
├── mobile/            # React Native application
├── docker/            # Docker configurations
└── docs/              # Documentation
```

---

## Coding Standards

### Python (Backend)

- **Style Guide**: PEP 8
- **Formatter**: Black (line length: 88)
- **Linter**: Flake8
- **Type Checking**: MyPy

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type check
mypy app/
```

**Python Best Practices:**
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Use async/await for I/O operations
- Follow REST API conventions
- Keep functions small and focused

**Example:**
```python
async def get_user_by_id(
    user_id: int,
    db: AsyncSession
) -> Optional[User]:
    """
    Retrieve a user by their ID.

    Args:
        user_id: The ID of the user to retrieve
        db: Database session

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### TypeScript (Frontend)

- **Style Guide**: Airbnb TypeScript Style Guide
- **Formatter**: Prettier
- **Linter**: ESLint

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type check
npm run type-check
```

**TypeScript Best Practices:**
- Use TypeScript strict mode
- Define interfaces for all data structures
- Use functional components with hooks
- Follow React best practices
- Use TanStack Query for server state
- Implement proper error boundaries

**Example:**
```typescript
interface User {
  id: number
  email: string
  fullName: string
  avatarUrl?: string
}

async function fetchUser(userId: number): Promise<User> {
  const response = await fetch(`/api/v1/users/${userId}`)
  if (!response.ok) {
    throw new Error('Failed to fetch user')
  }
  return response.json()
}
```

### Component Structure

```typescript
// Component with proper TypeScript types
interface ButtonProps {
  variant?: 'primary' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  onClick?: () => void
  children: React.ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  onClick,
  children
}: ButtonProps) {
  return (
    <button
      className={cn('button', `button-${variant}`, `button-${size}`)}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
```

---

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no code change)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system changes
- **ci**: CI/CD changes
- **chore**: Other changes (dependencies, etc.)

### Examples

```bash
feat(chat): add real-time message reactions

Implement emoji reactions for chat messages using Socket.io.
Users can now react to messages with emojis.

Closes #123
```

```bash
fix(auth): resolve JWT token expiration issue

Fixed bug where refresh tokens were not properly validated,
causing premature logout for users.

Fixes #456
```

```bash
docs(api): update authentication endpoint documentation

Added examples for OAuth2 login flow and improved
parameter descriptions in API docs.
```

---

## Pull Request Process

### Before Submitting

1. **Update your fork** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** following the coding standards

4. **Test your changes**:
   ```bash
   # Backend tests
   cd backend && pytest

   # Frontend tests
   cd frontend && npm run test
   ```

5. **Commit your changes** following the commit guidelines

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting the PR

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template:
   - **Title**: Brief description of changes
   - **Description**: Detailed explanation of what and why
   - **Type of Change**: Bug fix, feature, docs, etc.
   - **Testing**: How you tested the changes
   - **Screenshots**: If applicable (UI changes)
   - **Related Issues**: Link to related issues

### PR Template Example

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots here

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and linters
2. **Code Review**: At least one maintainer reviews the PR
3. **Address Feedback**: Make requested changes
4. **Approval**: PR is approved by maintainer(s)
5. **Merge**: PR is merged into main branch

---

## Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_login_success
```

**Test Structure:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test user creation endpoint"""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
```

### Frontend Testing

```bash
cd frontend

# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

**Test Structure:**
```typescript
import { render, screen } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    screen.getByText('Click me').click()
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

---

## Documentation

### Code Documentation

- **Python**: Use Google-style docstrings
- **TypeScript**: Use JSDoc comments

### API Documentation

- Backend API docs are auto-generated at `/docs`
- Update endpoint descriptions in route decorators

### User Documentation

- Add user guides to `docs/user-guide/`
- Use Markdown format
- Include screenshots for UI features

---

## Questions?

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: support@yourcompany.com

---

Thank you for contributing to Native Colab! 🎉
