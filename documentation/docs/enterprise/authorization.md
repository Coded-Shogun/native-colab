# Enterprise Authorization & Permissions

Native Colab Enterprise implements a comprehensive Role-Based Access Control (RBAC) system with fine-grained permissions for secure multi-tenant operations.

## Authorization Model

### Role-Based Access Control (RBAC)

**Hierarchical Role System:**
```
Super Admin (Platform-wide)
└── Workspace Owner
    ├── Workspace Admin
    │   ├── Manager
    │   │   ├── Member
    │   │   │   └── Guest
```

**Role Inheritance:**
- Higher roles inherit all permissions from lower roles
- Explicit permission overrides possible
- Custom roles can be created in Enterprise

### Attribute-Based Access Control (ABAC)

**Coming Soon - Context-Aware Permissions:**
- User attributes (department, clearance level)
- Resource attributes (classification, owner)
- Environmental attributes (time, location, IP)
- Action attributes (read, write, delete, share)

## Workspace Roles

### Super Admin

**Platform-Wide Permissions:**
- Manage all workspaces
- Access all data across workspaces
- Configure system settings
- Manage billing and subscriptions
- View enterprise analytics
- Manage enterprise security policies
- Access audit logs across all workspaces

**Use Case:** Platform operators, compliance officers

### Workspace Owner

**Workspace-Level Permissions:**
- Full control over workspace
- Manage workspace members and roles
- Delete workspace
- Configure workspace settings
- Access all projects and data within workspace
- Manage billing for workspace
- View workspace analytics
- Export workspace data

**Use Case:** Business unit leaders, department heads

### Workspace Admin

**Administrative Permissions:**
- Invite and remove members
- Assign roles (except Owner)
- Create and archive projects
- Manage integrations
- Configure workspace policies
- View workspace analytics
- Cannot delete workspace
- Cannot manage billing

**Use Case:** IT administrators, team leads

### Manager

**Project Management Permissions:**
- Create and manage projects
- Assign tasks to team members
- View all project data
- Manage project members
- Create channels and documents
- Cannot manage workspace settings
- Cannot invite workspace members

**Use Case:** Project managers, team leads

### Member

**Standard User Permissions:**
- Access assigned projects
- Create and complete tasks
- Participate in channels
- Create and edit documents
- Track time
- Schedule meetings
- Cannot manage projects
- Cannot assign roles

**Use Case:** Regular team members

### Guest

**Limited Access Permissions:**
- View-only access to specific resources
- Cannot create new resources
- Cannot invite others
- Limited to specific projects/channels
- Cannot access workspace settings
- Cannot view member list

**Use Case:** External contractors, clients, auditors

## Resource Permissions

### Projects

**Permission Levels:**
- **Owner**: Full control, can delete project
- **Admin**: Manage settings, assign members
- **Editor**: Create/edit tasks, assign tasks
- **Viewer**: Read-only access
- **No Access**: Project hidden from user

**Permission Matrix:**
| Action | Owner | Admin | Editor | Viewer |
|--------|-------|-------|--------|--------|
| View project | ✅ | ✅ | ✅ | ✅ |
| Edit project | ✅ | ✅ | ❌ | ❌ |
| Delete project | ✅ | ❌ | ❌ | ❌ |
| Create tasks | ✅ | ✅ | ✅ | ❌ |
| Edit tasks | ✅ | ✅ | ✅ | ❌ |
| Delete tasks | ✅ | ✅ | ✅ | ❌ |
| Assign tasks | ✅ | ✅ | ✅ | ❌ |
| Add members | ✅ | ✅ | ❌ | ❌ |
| Change permissions | ✅ | ✅ | ❌ | ❌ |

### Channels

**Channel Types:**
- **Public**: All workspace members can join
- **Private**: Invite-only access
- **Shared**: Cross-workspace channels (Enterprise)

**Channel Roles:**
- **Owner**: Created the channel, full control
- **Admin**: Moderate messages, manage members
- **Member**: Send messages, read history
- **Guest**: Read-only or limited posting

### Documents

**Sharing Levels:**
- **Private**: Only owner can access
- **Shared**: Specific users with assigned permissions
- **Workspace**: All workspace members
- **Public Link**: Anyone with link (optional password)

**Document Permissions:**
- **Owner**: Full control, can delete
- **Editor**: Can edit content
- **Commenter**: Can add comments, no editing
- **Viewer**: Read-only access

### Time Tracking

**Visibility Settings:**
- **Private**: Only user and managers can view
- **Team**: Team members can view each other's time
- **Public**: All workspace members can view
- **Restricted**: Only specific roles can view

## Permission Enforcement

### API-Level Authorization

**Decorator-Based Permissions:**
```python
from app.core.security import require_permission, require_role

@router.post("/projects")
@require_role("member")  # Minimum role required
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    # Only members and above can create projects
    return await create_project_service(project, current_user)

@router.delete("/projects/{project_id}")
@require_permission("project:delete", resource_id="project_id")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    # Only project owners can delete
    return await delete_project_service(project_id, current_user)
```

### Database-Level Security

**Row-Level Security (PostgreSQL):**
```sql
-- Ensure users can only access their workspace data
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_workspace_isolation ON projects
    USING (workspace_id IN (
        SELECT workspace_id FROM workspace_members
        WHERE user_id = current_user_id()
    ));

-- Project-level permissions
CREATE POLICY projects_permission_check ON projects
    USING (
        -- Check if user has permission to access this project
        EXISTS (
            SELECT 1 FROM project_members
            WHERE project_id = projects.id
            AND user_id = current_user_id()
            AND permission_level IN ('owner', 'admin', 'editor', 'viewer')
        )
    );
```

### Middleware Authorization

**Request-Level Checks:**
```python
class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract user from JWT
        user = await get_user_from_token(request)

        # Check workspace access
        if workspace_id := extract_workspace_id(request):
            if not await has_workspace_access(user.id, workspace_id):
                raise HTTPException(403, "Access denied to workspace")

        # Check resource-level permissions
        if resource_id := extract_resource_id(request):
            if not await has_resource_permission(user.id, resource_id, request.method):
                raise HTTPException(403, "Insufficient permissions")

        return await call_next(request)
```

## Custom Roles

**Enterprise Feature: Create Custom Roles**

```python
# Create custom role
POST /api/v1/workspaces/{workspace_id}/roles
{
  "name": "QA Tester",
  "description": "Can view and test features",
  "permissions": [
    "project:read",
    "task:read",
    "task:update_status",
    "document:read",
    "channel:read",
    "channel:write"
  ],
  "inherits_from": "member"
}

# Assign custom role
POST /api/v1/workspaces/{workspace_id}/members/{user_id}/role
{
  "role_id": "qa-tester-role-id"
}
```

**Permission Granularity:**
```
resource:action:scope

Examples:
- project:read:own          # Read own projects
- project:read:team         # Read team projects
- project:read:all          # Read all projects
- task:create:assigned      # Create tasks in assigned projects
- document:delete:own       # Delete own documents
- channel:moderate:all      # Moderate all channels
```

## Permission Checks

### Frontend Authorization

**React Hook for Permission Checks:**
```typescript
import { usePermission } from '@/hooks/usePermission';

function ProjectActions({ project }) {
  const canEdit = usePermission('project:edit', project.id);
  const canDelete = usePermission('project:delete', project.id);

  return (
    <>
      {canEdit && <EditButton />}
      {canDelete && <DeleteButton />}
    </>
  );
}
```

**Component-Level Guards:**
```typescript
import { RequirePermission } from '@/components/auth';

<RequirePermission permission="project:create">
  <CreateProjectButton />
</RequirePermission>

<RequireRole role="admin">
  <AdminPanel />
</RequireRole>
```

### Backend Authorization

**Service-Level Checks:**
```python
class ProjectService:
    async def delete_project(self, project_id: int, user: User):
        # Check if user has permission
        if not await self.has_permission(user.id, project_id, 'delete'):
            raise PermissionDenied("Cannot delete this project")

        # Log the action for audit
        await audit_log.log(
            user_id=user.id,
            action='delete',
            resource_type='project',
            resource_id=project_id
        )

        # Perform deletion
        return await self.repository.delete(project_id)
```

## Data Access Policies

### Multi-Tenancy Isolation

**Workspace Isolation:**
- All data scoped to workspace
- Cross-workspace access explicitly granted
- API automatically filters by workspace
- Database policies enforce isolation

**Implementation:**
```python
# Automatic workspace filtering
@router.get("/projects")
async def list_projects(
    workspace_id: int = Depends(get_current_workspace),
    current_user: User = Depends(get_current_user)
):
    # Only returns projects from current workspace
    return await get_projects(workspace_id=workspace_id)
```

### Data Classification

**Sensitivity Levels:**
- **Public**: Available to all workspace members
- **Internal**: Default for most resources
- **Confidential**: Restricted to specific roles
- **Restricted**: Highest security, minimal access

**Access Controls:**
```python
# Document classification
{
  "classification": "confidential",
  "allowed_roles": ["owner", "admin", "manager"],
  "allowed_users": ["user-uuid-1", "user-uuid-2"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

## Sharing & External Access

### External Sharing

**Share with Non-Members:**
```python
# Create shareable link
POST /api/v1/documents/{document_id}/share
{
  "access_level": "view",
  "expires_in_days": 7,
  "password_protected": true,
  "password": "secure-password",
  "notify_on_access": true
}

# Response
{
  "share_url": "https://app.nativecolab.com/s/abc123xyz",
  "expires_at": "2025-01-22T10:00:00Z",
  "access_count": 0
}
```

**Link Permissions:**
- View only
- Comment
- Edit (requires account)
- Time-limited access
- Password protection
- Access tracking

### Guest Access

**Invite External Users:**
```python
# Invite guest
POST /api/v1/workspaces/{workspace_id}/guests
{
  "email": "contractor@external.com",
  "projects": ["project-uuid"],
  "expires_in_days": 30,
  "permissions": ["view", "comment"]
}
```

**Guest Limitations:**
- Cannot invite others
- Limited resource access
- Cannot download all data
- Watermarked documents (optional)
- Session recording (optional)

## Audit Logging

### Permission Changes

**Logged Events:**
- Role assignments
- Permission grants/revokes
- Access attempts (success/failure)
- Privilege escalation
- Admin actions
- Guest access

**Audit Log Format:**
```json
{
  "event_id": "evt_123",
  "timestamp": "2025-01-15T10:30:00Z",
  "user_id": "user_abc",
  "action": "role_change",
  "resource_type": "workspace_member",
  "resource_id": "member_xyz",
  "old_value": {"role": "member"},
  "new_value": {"role": "admin"},
  "ip_address": "192.168.1.100",
  "success": true
}
```

## Best Practices

### For Administrators

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Regular Reviews**: Audit permissions quarterly
3. **Role-Based**: Use roles instead of individual permissions
4. **Separation of Duties**: No single user should have all access
5. **External Access**: Limit and monitor external sharing
6. **Guest Management**: Review and expire guest access regularly
7. **Custom Roles**: Create roles for specific job functions
8. **Permission Testing**: Test permissions before granting widely

### For Developers

1. **Always Check Permissions**: Never trust frontend checks alone
2. **Resource-Level Checks**: Verify access to specific resources
3. **Workspace Isolation**: Ensure multi-tenant data separation
4. **Audit Everything**: Log all permission changes
5. **Fail Securely**: Deny access by default
6. **Performance**: Cache permission checks when appropriate
7. **Testing**: Include permission tests in test suites

## API Reference

### Permission Check Endpoints

```http
# Check if user has permission
GET /api/v1/permissions/check
?resource_type=project
&resource_id=proj_123
&action=delete

# List user permissions
GET /api/v1/users/{user_id}/permissions

# List role permissions
GET /api/v1/roles/{role_id}/permissions

# Grant permission
POST /api/v1/permissions
{
  "user_id": "user_abc",
  "resource_type": "project",
  "resource_id": "proj_123",
  "permission": "edit",
  "expires_at": "2025-12-31T23:59:59Z"
}

# Revoke permission
DELETE /api/v1/permissions/{permission_id}
```

## Troubleshooting

**Issue:** User can't access resource they should have access to
- Verify workspace membership
- Check role assignments
- Review resource-specific permissions
- Check permission expiration
- Review audit logs for changes

**Issue:** Permission checks are slow
- Enable permission caching
- Use database indexes on permission tables
- Consider Redis for permission cache
- Review query optimization

**Issue:** Guest user has too much access
- Review guest role permissions
- Check resource-specific grants
- Ensure guest restrictions are enforced
- Update guest policies

## Next Steps

- [Authentication →](./authentication)
- [Data Protection →](./data-protection)
- [Audit Logging →](./audit-logging)
- [Security Overview →](./security)
