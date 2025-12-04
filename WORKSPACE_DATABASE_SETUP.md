# Workspace Database Integration Guide

## Django Backend Setup

### 1. Add Workspace Model to Django

The workspace files have been created in `gemnar-website/website/`:
- `workspace_models.py` - Database model
- `workspace_serializers.py` - REST API serializers  
- `workspace_views.py` - API ViewSet
- `workspace_urls.py` - URL routing

### 2. Register the Model

Add to `website/models.py`:
```python
from .workspace_models import Workspace
```

Or add this line to `website/__init__.py`:
```python
from .workspace_models import Workspace
```

### 3. Add URLs

In `gemnar/urls.py`, add:
```python
from website.workspace_urls import workspace_urlpatterns

urlpatterns = [
    # ... existing patterns
] + workspace_urlpatterns
```

### 4. Run Migrations

```bash
cd gemnar-website
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

### 5. API Endpoints

Once setup, these endpoints will be available:

- `GET /api/workspaces/` - List all user workspaces
- `POST /api/workspaces/` - Create new workspace
  ```json
  {
    "name": "My Workspace",
    "content": {"nodes": [], "edges": []}
  }
  ```
- `GET /api/workspaces/{id}/` - Get specific workspace
- `PATCH /api/workspaces/{id}/` - Update workspace content (save)
  ```json
  {
    "content": {"nodes": [...], "edges": [...]}
  }
  ```
- `DELETE /api/workspaces/{id}/` - Delete workspace
- `POST /api/workspaces/{id}/rename/` - Rename workspace
  ```json
  {
    "name": "New Name"
  }
  ```

## Frontend Integration

### Update Environment Variables

Add to `next-saas-lp-main/.env.local`:
```env
NEXT_PUBLIC_DJANGO_API_URL=http://localhost:8000
```

### Update Workspace Actions

In `next-saas-lp-main/src/app/actions/workspace.ts`, replace the mock implementations with real API calls.

Example for `saveWorkspaceAction`:
```typescript
export const saveWorkspaceAction = async (
  workspaceId: string,
  content: { nodes: any[]; edges: any[] }
): Promise<
  | {
      success: true;
      workspace: Workspace;
    }
  | {
      error: string;
    }
> => {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/workspaces/${workspaceId}/`, {
      method: 'PATCH',
      credentials: 'include', // Include cookies for Django session auth
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save workspace');
    }

    const data = await response.json();
    
    return { 
      success: true, 
      workspace: {
        ...data.workspace,
        createdAt: new Date(data.workspace.createdAt),
        updatedAt: new Date(data.workspace.updatedAt),
      }
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return { error: message };
  }
};
```

## Current Status

**⚠️ Workspaces are currently stored in memory (server-side Map) and reset on each page refresh or server restart.**

To persist workspaces, you have two options:

### Option A: Use Django Backend (Recommended for Production)
1. Follow the Django Backend Setup steps above
2. Update the workspace actions to call the real API
3. Workspaces will persist in PostgreSQL/SQLite

### Option B: Temporary localStorage Solution
Store workspaces in browser localStorage until backend is ready. This works but data is not shared across devices/browsers.

Would you like me to:
1. Implement the localStorage temporary solution?
2. Help you integrate the Django backend?
3. Both?
