# Project Management

Native Colab's project management module helps teams organize work, track progress, and collaborate effectively using Kanban boards, task lists, and timelines.

## Overview

Project management features include:
- **Kanban Boards**: Visual workflow management
- **Task Lists**: Organized task tracking
- **Task Dependencies**: Link related tasks
- **Custom Fields**: Tailor projects to your needs
- **Progress Tracking**: Monitor project completion
- **Team Assignment**: Assign tasks to team members
- **Due Dates & Reminders**: Never miss deadlines
- **Comments & Attachments**: Collaborate on tasks

## Creating Projects

### New Project

1. Click **Projects** in the sidebar
2. Click **"Create Project"**
3. Fill in project details:
   ```
   Project Name: Website Redesign
   Description: Redesign company website with modern UI
   Workspace: Select workspace
   Template: Blank / Use template
   Privacy: Public / Private
   ```
4. Click **"Create"**

### Project Templates

Choose from pre-built templates:
- **Software Development**: Sprints, bugs, features
- **Marketing Campaign**: Campaign planning and execution
- **Product Launch**: Launch checklist and timeline
- **Event Planning**: Event organization workflow
- **Blank**: Start from scratch

### Project Settings

Configure your project:

**General**
- Project name and description
- Project icon/color
- Project owner
- Default task view

**Members**
- Add/remove team members
- Set member roles
- Guest access

**Workflow**
- Customize task statuses
- Define status workflow
- Set status colors

**Custom Fields**
- Add custom fields for tasks
- Define field types
- Set required fields

## Task Management

### Creating Tasks

**Quick Add:**
1. Click **"Add Task"** in any project
2. Enter task title
3. Press Enter

**Detailed Task:**
1. Click **"Add Task"**
2. Fill in details:
   - Title
   - Description (supports Markdown)
   - Assignee(s)
   - Due date
   - Priority
   - Tags
   - Custom fields
3. Click **"Create Task"**

### Task Details

Click any task to view/edit:

**Overview**
- Title and description
- Status and priority
- Assignee(s)
- Due date
- Progress

**Details**
- Created by/date
- Last updated
- Time tracked
- Custom fields

**Activity**
- Comments
- Status changes
- Assignment changes
- File attachments

### Task Properties

#### Status
Define task progress:
- 📝 **To Do**: Not started
- 🏗️ **In Progress**: Currently working
- 👀 **Review**: Ready for review
- ✅ **Done**: Completed
- ❌ **Blocked**: Cannot proceed

Customize statuses in project settings.

#### Priority
Set task importance:
- 🔴 **Urgent**: Critical, immediate action
- 🟠 **High**: Important, near-term
- 🟡 **Medium**: Normal priority
- 🟢 **Low**: Nice to have

#### Tags
Organize with tags:
- Add multiple tags per task
- Color-coded for quick identification
- Filter tasks by tags
- Create tags on the fly

### Task Assignment

**Assign to User:**
1. Open task
2. Click **"Assignee"** field
3. Select team member(s)
4. They receive notification

**Unassigned Tasks:**
- Tasks without assignees appear in "Unassigned" filter
- Useful for distributing work

**Multiple Assignees:**
- Assign tasks to multiple people
- All assignees receive notifications
- Any assignee can complete the task

### Due Dates

Set deadlines:
1. Click **"Due Date"** field
2. Select date from calendar
3. Optionally set time
4. Add reminder notification

**Overdue Tasks:**
- Automatically highlighted in red
- Appear in "Overdue" filter
- Send reminder notifications

### Task Dependencies

Link related tasks:

1. Open task
2. Go to **"Dependencies"** section
3. Click **"Add Dependency"**
4. Select dependency type:
   - **Blocks**: This task blocks another
   - **Blocked by**: This task is blocked by another
5. Select the related task

**Benefits:**
- Visual dependency chain
- Cannot complete blocked tasks
- Automatic reordering

## Project Views

### Kanban Board

Visual workflow with columns:

**Features:**
- Drag & drop tasks between columns
- Swim lanes for grouping
- Column limits (WIP limits)
- Filter and sort options

**Using Kanban:**
1. Click **"Board"** view
2. Drag tasks between status columns
3. Click task to view details
4. Add new tasks to any column

### List View

Traditional task list:

**Features:**
- Hierarchical task structure
- Bulk actions
- Sorting and filtering
- Customizable columns

**Using List View:**
1. Click **"List"** view
2. Sort by any column
3. Group by status, assignee, or tag
4. Bulk select for mass actions

### Calendar View

Timeline-based visualization:

**Features:**
- Monthly, weekly, daily views
- Drag to reschedule
- Color-coded by project/tag
- Show/hide completed tasks

**Using Calendar:**
1. Click **"Calendar"** view
2. View tasks by due date
3. Drag tasks to new dates
4. Click date to create new task

### Timeline (Gantt)

Project timeline with dependencies:

**Features:**
- Task duration bars
- Dependency connections
- Milestone markers
- Critical path highlighting

**Using Timeline:**
1. Click **"Timeline"** view
2. Set task start/end dates
3. View dependencies
4. Identify scheduling conflicts

## Subtasks & Checklists

### Creating Subtasks

Break down complex tasks:

1. Open parent task
2. Click **"Add Subtask"**
3. Enter subtask title
4. Subtask inherits parent's project

**Benefits:**
- Track granular progress
- Assign different subtasks to different people
- Roll-up progress to parent

### Checklists

Simple to-do lists within tasks:

1. Open task
2. In description, use:
   ```markdown
   - [ ] Unchecked item
   - [x] Checked item
   ```
3. Check off items as you complete them

**Progress Tracking:**
- Checklist completion percentage shown
- Contributes to overall task progress

## Comments & Collaboration

### Adding Comments

1. Open task
2. Scroll to **Comments** section
3. Type comment (Markdown supported)
4. Mention users with `@username`
5. Click **"Comment"**

### Attachments

Attach files to tasks:

1. In task or comment
2. Click paperclip icon
3. Upload files
4. Files visible to all project members

### @Mentions in Comments

Notify team members:
- `@username`: Notify specific user
- `@team-name`: Notify entire team
- They receive notification and email

## Filtering & Search

### Quick Filters

Built-in filters:
- My Tasks
- Unassigned
- Due Today
- Due This Week
- Overdue
- Completed

### Custom Filters

Create advanced filters:

1. Click **"Filter"** button
2. Add conditions:
   - Status is/is not
   - Assignee is/is not
   - Due date is before/after
   - Tags include/exclude
   - Custom field equals
3. Save filter for reuse

### Search Tasks

Search within project:
1. Click search icon
2. Enter keywords
3. Searches titles and descriptions

## Project Progress

### Progress Indicators

Visual progress tracking:
- **Progress Bar**: Percentage complete
- **Task Counts**: X of Y tasks completed
- **Velocity**: Tasks completed per sprint

### Reports

Built-in project reports:
- **Burndown Chart**: Work remaining over time
- **Velocity Chart**: Team productivity trends
- **Time Tracking**: Hours logged per task
- **Completion Report**: Tasks completed by member

Access reports:
1. Click **"Reports"** tab in project
2. Select report type
3. Choose date range
4. Export as PDF or CSV

## Automation

Automate repetitive tasks:

### Setting Up Automation

1. Go to **Project Settings** → **Automation**
2. Click **"Add Rule"**
3. Define trigger:
   - When status changes to...
   - When assigned to...
   - When due date approaches...
4. Define action:
   - Assign to user
   - Add comment
   - Send notification
   - Move to project
5. Save rule

### Example Rules

- **Status Change**: When task moved to "Done" → Add comment "Great job!"
- **Assignment**: When assigned to manager → Set priority to High
- **Due Date**: 1 day before due → Send reminder notification

## Templates

### Creating Task Templates

Save common tasks as templates:

1. Create a task with all details
2. Click **More** → **"Save as Template"**
3. Name the template
4. Template available for reuse

### Using Templates

1. Click **"Add Task"** → **"From Template"**
2. Select template
3. Customize if needed
4. Create

## Best Practices

### Project Organization

1. **One Project Per Initiative**: Don't create mega-projects
2. **Use Templates**: Standardize common workflows
3. **Clear Naming**: Descriptive project and task names
4. **Regular Cleanup**: Archive completed projects

### Task Management

1. **Atomic Tasks**: Tasks should be completable in one session
2. **Clear Descriptions**: Include context and acceptance criteria
3. **Set Due Dates**: All tasks should have target dates
4. **Update Status**: Keep task status current
5. **Add Comments**: Document decisions and progress

### Team Collaboration

1. **Assign Ownership**: Every task should have an owner
2. **Review Regularly**: Daily standup around board
3. **Use Dependencies**: Show task relationships
4. **Communicate**: Comment on tasks, don't silo information

### Workflow Design

1. **Keep It Simple**: Start with basic statuses
2. **Define Done**: Clear criteria for completion
3. **Limit WIP**: Set work-in-progress limits
4. **Regular Retrospectives**: Continuously improve workflow

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New task | `N` |
| Search tasks | `/` |
| Quick filter | `F` |
| Assign to me | `I` |
| Mark complete | `X` |
| Due date | `D` |
| Priority | `P` |
| Navigate tasks | `↑` `↓` |

## Troubleshooting

### Can't Create Project?
- Check workspace permissions
- Verify you're a member of workspace
- Contact workspace admin

### Task Not Saving?
- Check required fields
- Ensure internet connection
- Try refreshing page

### Can't Assign Task?
- Verify user is project member
- Check user is active in workspace
- Add member to project first

## Next Steps

- [Learn about Time Tracking →](./time-tracking)
- [Explore Document Collaboration →](./documents)
- [Managing Projects Guide →](../guides/managing-projects)
