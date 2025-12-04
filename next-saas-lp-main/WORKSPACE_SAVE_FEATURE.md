# Flow Generator Workspace Save Feature

## Overview
Implemented a ChatGPT-style workspace save and management system for the flow-generator. Users can now:
- Save their current workspace with a save button
- Create multiple workspaces
- Switch between workspaces using a dropdown selector
- Rename and delete workspaces
- Auto-load workspace content when switching

## Implementation Details

### 1. Workspace Actions (`src/app/actions/workspace.ts`)
Created server actions for workspace management:
- `saveWorkspaceAction(workspaceId, content)` - Save workspace content (nodes & edges)
- `createWorkspaceAction(name, userId)` - Create a new workspace
- `deleteWorkspaceAction(workspaceId)` - Delete a workspace
- `getWorkspaceAction(workspaceId)` - Load a specific workspace
- `listWorkspacesAction(userId)` - List all user workspaces
- `renameWorkspaceAction(workspaceId, name)` - Rename a workspace

**Note:** Currently using in-memory mock storage. Replace with Django API calls by uncommenting the TODO sections.

### 2. Updated Project Provider (`src/providers/project-provider.tsx`)
Enhanced the provider to support:
- State management for workspace data
- `updateProject()` method for updating workspace properties
- `setProject()` method for switching to a different workspace
- Automatic `updatedAt` timestamp updates

### 3. Save Button (`src/components/flow-components/controls.tsx`)
Added a save button to the controls panel that:
- Shows a spinning loader while saving
- Displays a green checkmark for 2 seconds after successful save
- Uses the save icon in idle state
- Triggers manual save via `saveWorkspaceAction`
- Shows toast notifications for success/failure

### 4. Workspace Selector (`src/components/flow-components/workspace-selector.tsx`)
Created a dropdown component that allows users to:
- View all their workspaces
- Search/filter workspaces (using Fuse.js)
- Create new workspaces with custom names
- Rename existing workspaces
- Delete workspaces (with confirmation)
- Switch between workspaces
- Group workspaces by ownership (My Workspaces vs Other Workspaces)

### 5. Flow Generator Page Updates (`src/app/(dashboard)/flow-generator/page.tsx`)
Modified the main page to:
- Load workspaces on mount
- Create a default workspace if none exist
- Display workspace selector in the top-left corner
- Handle workspace switching with proper state updates
- Show loading state while initializing
- Pass workspace data to ProjectProvider

### 6. Canvas Updates (`src/components/flow-components/canvas.tsx`)
Enhanced canvas to:
- Use the updated project context with `updateProject`
- Auto-load nodes and edges when workspace changes (via `useEffect`)
- Clear and reload canvas content when switching workspaces

### 7. Toast Notifications
Added Sonner toast provider to the dashboard layout for user feedback on:
- Successful saves
- Failed saves
- Workspace creation
- Workspace deletion
- Workspace renaming

## How It Works

### User Flow:
1. **Initial Load**: System loads all user workspaces, or creates a default one if none exist
2. **Working**: User creates nodes and edges in the flow generator
3. **Saving**: User clicks the save button (or auto-save could be enabled)
4. **Switching**: User can switch workspaces via the dropdown selector
5. **Canvas Updates**: Canvas automatically loads the new workspace's nodes and edges
6. **Management**: User can create, rename, or delete workspaces via the dropdown menu

### Technical Flow:
```
User Action → Client Component → Server Action → Mock Storage (or Django API)
     ↓                                                    ↓
Toast Notification ← Response ← Server Action Result ← Storage
     ↓
UI Update (Canvas reload, selector update, etc.)
```

## File Structure
```
src/
├── app/
│   ├── actions/
│   │   └── workspace.ts                    # Server actions for workspace management
│   └── (dashboard)/
│       ├── layout.tsx                      # Added Toaster component
│       └── flow-generator/
│           └── page.tsx                    # Main page with workspace integration
├── components/
│   └── flow-components/
│       ├── canvas.tsx                      # Updated to handle workspace switching
│       ├── controls.tsx                    # Added save button
│       └── workspace-selector.tsx          # New dropdown selector component
└── providers/
    └── project-provider.tsx                # Enhanced with state management
```

## Next Steps (Django Integration)

To connect this to your Django backend:

1. **Create Django API endpoints:**
   ```python
   # In gemnar-website/website/views.py or new workspaces app
   
   GET    /api/workspaces/               # List workspaces
   POST   /api/workspaces/               # Create workspace
   GET    /api/workspaces/{id}/          # Get workspace
   PATCH  /api/workspaces/{id}/          # Update workspace (save content)
   DELETE /api/workspaces/{id}/          # Delete workspace
   ```

2. **Database Model:**
   ```python
   class Workspace(models.Model):
       id = models.UUIDField(primary_key=True, default=uuid.uuid4)
       user = models.ForeignKey(User, on_delete=models.CASCADE)
       name = models.CharField(max_length=255)
       content = models.JSONField(default=dict)  # Stores nodes and edges
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)
   ```

3. **Update workspace.ts actions:**
   - Uncomment the fetch() calls in each action
   - Add proper authentication headers
   - Set `DJANGO_API_URL` environment variable
   - Remove the mock `workspacesStore` Map

4. **Authentication:**
   - Ensure user is authenticated before accessing workspace endpoints
   - Use JWT or session auth from your existing Django setup

## Features Included

✅ Save button with loading states  
✅ Workspace dropdown selector  
✅ Create new workspaces  
✅ Rename workspaces  
✅ Delete workspaces  
✅ Switch between workspaces  
✅ Auto-load workspace content  
✅ Toast notifications  
✅ Search/filter workspaces  
✅ Default workspace creation  
✅ Confirmation dialogs for destructive actions  

## Usage

Users can now:
- Click the **Save button** (floppy disk icon) in the bottom-left controls to manually save their work
- Use the **workspace dropdown** in the top-left to switch between workspaces
- Click **"Create new workspace"** in the dropdown to start a fresh workspace
- Hover and click workspace options to rename or delete

The system automatically loads the workspace content (all nodes and edges) when switching between workspaces, providing a seamless experience similar to ChatGPT's conversation management.
