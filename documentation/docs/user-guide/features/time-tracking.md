# Time Tracking

Track time spent on projects and tasks with Native Colab's built-in time tracking module. Log hours, generate timesheets, and analyze productivity.

## Overview

Time tracking features:
- Manual time entry
- Live timer tracking
- Project and task association
- Billable vs non-billable hours
- Timesheet management
- Reports and analytics
- Calendar integration
- Export to CSV/PDF

## Quick Start

### Starting a Timer

1. Navigate to any project or task
2. Click the **"Start Timer"** button
3. Timer begins tracking automatically
4. Continue working
5. Click **"Stop"** when finished

### Manual Time Entry

1. Go to **Time Tracking** in sidebar
2. Click **"Add Entry"**
3. Fill in details:
   - Project
   - Task (optional)
   - Start time
   - End time
   - Description
   - Billable status
4. Click **"Save"**

## Time Entries

### Entry Details

Each time entry includes:
- **Date**: When work was performed
- **Duration**: Hours and minutes
- **Project**: Associated project
- **Task**: Specific task (optional)
- **Description**: What you worked on
- **Billable**: Billable or non-billable
- **User**: Who logged the time

### Editing Entries

1. Go to **Time Tracking**
2. Find entry to edit
3. Click entry
4. Update details
5. Save changes

### Deleting Entries

1. Click entry
2. Click **"Delete"**
3. Confirm deletion

:::warning
Deleted time entries cannot be recovered unless they're part of a submitted timesheet.
:::

## Live Timer

### Using the Timer

**Start Timer:**
- Click play icon anywhere in the app
- Timer widget appears in navigation
- Shows elapsed time
- Works across all pages

**Add Description:**
- Click timer widget
- Add what you're working on
- Associate with project/task

**Pause/Resume:**
- Click pause to temporarily stop
- Click play to resume
- Time accumulates

**Stop Timer:**
- Click stop button
- Time entry created automatically
- Edit details if needed

### Timer Widget

The floating timer widget shows:
- Current elapsed time
- Project/task being tracked
- Description (if added)
- Play/pause/stop controls

## Timesheets

### Creating Timesheets

1. Go to **Time Tracking** → **Timesheets**
2. Click **"New Timesheet"**
3. Select period:
   - Current week
   - Last week
   - Custom date range
4. Time entries auto-populate
5. Review and edit if needed
6. Add notes (optional)
7. Submit for approval

### Timesheet Status

- **Draft**: Editable, not submitted
- **Submitted**: Awaiting approval
- **Approved**: Accepted by manager
- **Rejected**: Needs revision
- **Paid**: Processed for payment

### Approval Workflow

**For Employees:**
1. Create and submit timesheet
2. Wait for manager review
3. Make corrections if rejected
4. Resubmit

**For Managers:**
1. Review submitted timesheets
2. Check for accuracy
3. Approve or reject with comments
4. Approved timesheets lock automatically

## Reports

### Personal Reports

View your own time tracking:

**By Period:**
- Today
- This Week
- This Month
- Custom Range

**By Project:**
- Time per project
- Billable vs non-billable
- Project progress

**By Task:**
- Time per task
- Task efficiency
- Time estimates vs actual

### Team Reports

**Manager View:**
- Team member hours
- Project allocation
- Billable utilization
- Overtime tracking

**Workspace View:**
- Total hours logged
- Hours by department/team
- Cost tracking
- Revenue projections

### Generating Reports

1. Go to **Time Tracking** → **Reports**
2. Select report type
3. Choose date range
4. Filter by:
   - Project
   - User
   - Billable status
   - Client
5. View report
6. Export as PDF or CSV

## Billable Hours

### Setting Billable Rates

**Project Rates:**
1. Open project settings
2. Go to **"Billing"**
3. Set hourly rate
4. Apply to all tasks or per-task

**User Rates:**
1. Workspace settings → **Members**
2. Edit user profile
3. Set default hourly rate
4. Rate applies to all projects unless overridden

### Tracking Billable Time

**Mark as Billable:**
- Toggle billable flag on time entry
- Set during timer tracking
- Or mark afterward

**Billable vs Non-Billable:**
- Internal meetings: Non-billable
- Client work: Billable
- Training: Non-billable
- Development: Billable (if client project)

### Invoicing

Generate invoices from time entries:

1. Go to **Time Tracking** → **Invoicing**
2. Select client/project
3. Choose date range
4. Review billable hours
5. Apply rate
6. Generate invoice
7. Export as PDF
8. Mark as invoiced

## Calendar Integration

### Syncing Time Entries

Automatic calendar integration:
- Time entries appear on calendar
- Meetings automatically tracked
- Block out time visually
- Sync with external calendars

### Scheduling Time

Plan future work:
1. Open calendar
2. Block time for project
3. When time arrives, timer prompts you
4. Start tracking with one click

## Productivity Analytics

### Personal Insights

View your productivity patterns:
- **Busiest Days**: When you log most hours
- **Peak Hours**: Most productive times
- **Project Distribution**: Time allocation
- **Trends**: Week-over-week comparison

### Team Insights

**Manager Dashboard:**
- Team capacity
- Utilization rates
- Project health
- Resource allocation
- Bottlenecks

## Best Practices

### Accurate Time Tracking

1. **Track as You Go**: Use live timer, not retrospective
2. **Be Specific**: Add clear descriptions
3. **Break Down Work**: Log different tasks separately
4. **Daily Logging**: Enter time entries daily
5. **Review Before Submit**: Check for accuracy

### Organization

1. **Consistent Categories**: Use standard project/task names
2. **Billable Clarity**: Clear billable/non-billable distinction
3. **Regular Timesheets**: Submit weekly
4. **Backup Notes**: Keep work diary for reference

### Efficiency

1. **Use Timer**: More accurate than manual entry
2. **Keyboard Shortcuts**: Quick timer control
3. **Templates**: Save common time entries
4. **Batch Similar Work**: Group similar tasks

## Integrations

### External Tools

Native Colab integrates with:
- **Google Calendar**: Sync time blocks
- **Outlook Calendar**: Sync meetings
- **JIRA**: Import tasks
- **GitHub**: Track code commits
- **Harvest**: Migrate existing data

## Tips & Tricks

- **Quick Timer**: Press `T` to start/stop timer
- **Copy Entries**: Duplicate recurring work
- **Favorites**: Pin frequently tracked projects
- **Mobile App**: Track time on the go
- **Reminders**: Set daily logging reminders

## Troubleshooting

**Timer Not Starting?**
- Check browser permissions
- Refresh page
- Clear cache

**Missing Time Entries?**
- Check date range filter
- Verify project selection
- Look in Draft timesheets

**Cannot Submit Timesheet?**
- Fill all required fields
- Check for time entry gaps
- Verify date range is correct

## Next Steps

- [Explore Calendar Features →](./calendar)
- [Learn About Projects →](./projects)
- [Time Tracking Guide →](../guides/tracking-time)
