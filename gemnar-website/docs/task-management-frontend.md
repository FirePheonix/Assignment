# Task Management Frontend Documentation

## Overview

A comprehensive frontend system for managing active tasks created for creators. This system allows brands and administrators to:

- View all active tasks with detailed statistics
- Manage creator applications (accept, reject, complete, award prizes)
- Track task analytics and performance metrics
- Get insights on task engagement and completion rates

## Features

### 1. Active Tasks Dashboard (`/tasks/active/`)

**Purpose**: Main dashboard for viewing and managing all active tasks.

**Features**:
- Grid view of all active tasks with key information
- Statistics summary (total tasks, applications, pending reviews, completions)
- Filtering by category, genre, and incentive type
- Quick action buttons for each task

**Access**: 
- Brand users can see their own tasks
- Staff/superusers can see all tasks

### 2. Task Detail Management (`/tasks/<task_id>/manage/`)

**Purpose**: Detailed management interface for individual tasks.

**Features**:
- Complete task information display
- Tabbed view of applications by status (Pending, Accepted, Completed, Rejected)
- Application management actions:
  - **Accept**: Approve a creator's application
  - **Reject**: Decline a creator's application  
  - **Mark Complete**: Mark accepted work as completed
  - **Award Prize**: Complete task and award prize
  - **Reset to Pending**: Reset status for re-evaluation
- Creator profile information and social links
- Application statistics overview

**Workflow**:
1. Creators apply to tasks via the API
2. Applications appear in "Pending" tab
3. Brand users review and accept/reject applications
4. Accepted creators work on the task
5. Brand users mark work as complete or award prizes

### 3. Task Analytics (`/tasks/<task_id>/analytics/`)

**Purpose**: Detailed analytics and insights for individual tasks.

**Features**:
- Key metrics (total applications, acceptance rate, completion rate)
- Application status distribution with percentages
- Progress tracking with visual progress bars
- Applications timeline (last 30 days)
- Performance insights and recommendations
- Applications over time chart

**Metrics Explained**:
- **Acceptance Rate**: % of applications that were accepted
- **Completion Rate**: % of accepted applications that were completed
- **Status Distribution**: Breakdown of all application statuses

### 4. System Overview (`/tasks/overview/`) - Admin Only

**Purpose**: System-wide analytics and management for administrators.

**Features**:
- Overall system statistics
- Task distribution by category, genre, and incentive type
- Top brands by task creation
- Top creators by application count
- Recent tasks overview
- Interactive charts and visualizations

## URL Structure

```
/tasks/active/                    # Main dashboard
/tasks/<id>/manage/              # Task management
/tasks/<id>/analytics/           # Task analytics  
/tasks/overview/                 # Admin overview
```

## Permissions

### Brand Users
- Can view and manage their own created tasks
- Can see applications for their tasks
- Can accept/reject applications and award prizes

### Staff/Superusers
- Can view all tasks in the system
- Can access system overview dashboard
- Can manage any task or application

### Regular Users/Creators
- Cannot access these management interfaces
- Use API endpoints to apply to tasks

## Integration Points

### API Integration
The frontend integrates with existing API endpoints:
- `/api/tasks/` - List and create tasks
- `/api/tasks/<id>/` - Task details
- `/api/tasks/<id>/applications/` - Task applications
- `/api/applications/<id>/` - Application management

### Landing Page Integration
- Active Tasks card in landing page now links to the dashboard
- Displays real-time task statistics

## Technical Details

### Views
- `active_tasks_dashboard`: Main dashboard view
- `task_detail_management`: Individual task management
- `task_analytics`: Task analytics and insights
- `all_tasks_overview`: System-wide overview (admin)

### Templates
- `tasks/active_tasks_dashboard.html`: Main dashboard
- `tasks/task_detail_management.html`: Task management interface
- `tasks/task_analytics.html`: Analytics dashboard
- `tasks/all_tasks_overview.html`: Admin overview
- `tasks/partials/application_card.html`: Reusable application display

### Models Used
- `Task`: Main task model
- `TaskApplication`: Creator applications to tasks
- `User`: Creator and brand user information

## Usage Examples

### For Brands
1. Navigate to `/tasks/active/` to see all your active tasks
2. Click "Manage" on any task to review applications
3. In the Pending tab, accept or reject creator applications
4. Monitor accepted creators in the Accepted tab
5. Mark work as complete or award prizes when finished
6. View detailed analytics to optimize future tasks

### For Administrators
1. Access `/tasks/overview/` for system-wide insights
2. Monitor task creation trends and popular categories
3. Identify top-performing brands and creators
4. Use analytics to improve the platform

## Future Enhancements

Potential improvements that could be added:
- Bulk application management
- Task templates for common task types
- Advanced filtering and search
- Email notifications for status changes
- Task collaboration features
- Creator portfolio integration
- Payment processing integration
- Task deadline reminders
- Performance benchmarking
