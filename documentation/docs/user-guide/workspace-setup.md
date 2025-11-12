# Workspace Setup

A **workspace** in Native Colab is a shared environment where your team collaborates. This guide will help you create and configure your workspace.

## What is a Workspace?

A workspace is the top-level container for all your team's:
- Chat channels and messages
- Projects and tasks
- Documents
- Time entries
- Calendar events
- Team members

Think of it as your company's or team's dedicated space within Native Colab.

## Creating a Workspace

### As an Administrator

1. Click the **Workspace** dropdown in the top-left corner
2. Click **"Create New Workspace"**
3. Fill in the workspace details:
   ```
   Workspace Name: e.g., "Acme Corporation"
   Workspace Slug: e.g., "acme" (URL-friendly identifier)
   Description: Brief description of your workspace
   ```
4. Click **"Create Workspace"**

### Workspace Settings

After creating a workspace, configure these important settings:

#### General Settings
- **Workspace Name**: Display name
- **Workspace Icon**: Upload a logo or icon
- **Description**: What this workspace is for
- **Time Zone**: Default time zone for the workspace
- **Language**: Default language

#### Privacy & Access
- **Workspace Visibility**:
  - **Private**: Invite-only
  - **Public**: Anyone with link can request access
- **Member Approval**: Require admin approval for new members
- **Guest Access**: Allow external guests

#### Features
Enable or disable specific features for the workspace:
- ✅ Chat & Messaging
- ✅ Project Management
- ✅ Document Collaboration
- ✅ Time Tracking
- ✅ Calendar & Events
- ✅ Video Meetings
- ✅ Whiteboard
- ✅ Digital Signatures

## Inviting Team Members

### Sending Invitations

1. Go to **Workspace Settings** → **Members**
2. Click **"Invite Members"**
3. Enter email addresses (comma-separated for multiple)
4. Select role for new members:
   - **Admin**: Full workspace control
   - **Manager**: Can manage projects and teams
   - **Member**: Standard access
   - **Guest**: Limited, read-only access
5. Add a personal message (optional)
6. Click **"Send Invitations"**

### Invitation Link

Generate a shareable invitation link:

1. Go to **Workspace Settings** → **Invitations**
2. Click **"Generate Invite Link"**
3. Set expiration (optional)
4. Set maximum uses (optional)
5. Copy and share the link

:::warning Security Note
Invitation links grant immediate access. Use with caution and set expiration dates.
:::

## Managing Members

### Member Roles

**Admin**
- Full workspace configuration
- Manage billing and subscriptions
- Add/remove members
- Delete workspace

**Manager**
- Create and manage projects
- Manage team members
- View all workspace content
- Configure team settings

**Member**
- Access assigned projects
- Participate in channels
- Create documents
- Track time
- Schedule meetings

**Guest**
- Access specific projects only
- Read-only by default
- Limited chat access
- Cannot see member list

### Changing Member Roles

1. Go to **Workspace Settings** → **Members**
2. Find the member
3. Click the role dropdown
4. Select new role
5. Confirm change

### Removing Members

1. Go to **Workspace Settings** → **Members**
2. Find the member
3. Click **"Remove"**
4. Confirm removal
5. Choose whether to:
   - Archive their content
   - Reassign their tasks
   - Transfer ownership

## Organizing with Teams

Teams help organize members into groups (e.g., Development, Marketing, Sales).

### Creating Teams

1. Go to **Workspace Settings** → **Teams**
2. Click **"Create Team"**
3. Enter team details:
   - Team Name
   - Description
   - Team Lead (optional)
4. Add team members
5. Click **"Create"**

### Team Benefits

- **Private Channels**: Team-specific communication
- **Team Projects**: Projects visible only to team members
- **Team Permissions**: Granular access control
- **Team Mentions**: Tag entire team with @team-name

## Workspace Customization

### Branding

1. Go to **Workspace Settings** → **Branding**
2. Customize:
   - **Logo**: Upload company logo
   - **Colors**: Primary and secondary colors
   - **Favicon**: Browser tab icon
3. Preview changes
4. Save

### Custom Fields

Add custom fields for projects and tasks:

1. Go to **Workspace Settings** → **Custom Fields**
2. Click **"Add Field"**
3. Configure:
   - Field Name
   - Field Type (text, number, date, dropdown, user)
   - Required/Optional
   - Default Value
4. Save

### Workspace Templates

Create templates for common workflows:

1. Go to **Workspace Settings** → **Templates**
2. Click **"Create Template"**
3. Choose template type:
   - Project Template
   - Task Template
   - Document Template
4. Configure template
5. Save

## Integration Setup

### Email Integration

Connect your email server:

1. Go to **Workspace Settings** → **Integrations** → **Email**
2. Enter SMTP settings:
   ```
   SMTP Server: smtp.gmail.com
   Port: 587
   Username: your-email@company.com
   Password: your-app-password
   ```
3. Test connection
4. Save

### Calendar Integration

Sync with external calendars:

1. Go to **Workspace Settings** → **Integrations** → **Calendar**
2. Choose provider:
   - Google Calendar
   - Microsoft Outlook
   - CalDAV
3. Authenticate
4. Select calendars to sync

### Webhooks

Set up webhooks for external integrations:

1. Go to **Workspace Settings** → **Integrations** → **Webhooks**
2. Click **"Create Webhook"**
3. Configure:
   - Name
   - URL
   - Events to trigger
   - Secret key (for verification)
4. Save

## Best Practices

### Workspace Organization

1. **Clear Naming**: Use descriptive workspace names
2. **Team Structure**: Align teams with your organization
3. **Role Definition**: Clearly define role responsibilities
4. **Regular Cleanup**: Remove inactive members periodically

### Security

1. **Two-Factor Authentication**: Require for all members
2. **Role-Based Access**: Use least privilege principle
3. **Regular Audits**: Review member access quarterly
4. **Strong Passwords**: Enforce password policies
5. **Invitation Links**: Set expiration dates

### Communication

1. **Welcome Guide**: Create onboarding documentation
2. **Channel Guidelines**: Establish channel naming conventions
3. **Response Expectations**: Set communication norms
4. **Status Updates**: Encourage regular updates

### Data Management

1. **Backup Schedule**: Configure regular backups
2. **Retention Policies**: Define data retention rules
3. **Archive Old Projects**: Keep workspace organized
4. **Storage Monitoring**: Monitor storage usage

## Multi-Workspace Management

Users can belong to multiple workspaces. To switch:

1. Click workspace name in top-left
2. Select different workspace from dropdown
3. Or create a new workspace

## Workspace Billing (If Applicable)

1. Go to **Workspace Settings** → **Billing**
2. View current plan
3. Upgrade/downgrade plan
4. View usage statistics
5. Manage payment methods
6. Download invoices

## Workspace Export

Export all workspace data:

1. Go to **Workspace Settings** → **Data Export**
2. Select data to export:
   - Messages
   - Projects
   - Documents
   - Time entries
   - All data
3. Choose format (JSON, CSV, ZIP)
4. Click **"Export"**
5. Download when ready

## Deleting a Workspace

:::danger Warning
Deleting a workspace is permanent and cannot be undone!
:::

1. Go to **Workspace Settings** → **General**
2. Scroll to **Danger Zone**
3. Click **"Delete Workspace"**
4. Type workspace name to confirm
5. Confirm deletion

All data, including messages, projects, documents, and files, will be permanently deleted.

## Next Steps

Now that your workspace is set up:

1. [Start using Chat →](./features/chat)
2. [Create your first project →](./features/projects)
3. [Upload documents →](./features/documents)

## Troubleshooting

### Can't Create Workspace?
- Check if you have admin permissions
- Verify email is confirmed
- Contact system administrator

### Members Not Receiving Invitations?
- Check spam folders
- Verify email addresses are correct
- Ensure email integration is configured

### Workspace Not Appearing?
- Refresh the page
- Check workspace dropdown
- Verify you're logged in with correct account
