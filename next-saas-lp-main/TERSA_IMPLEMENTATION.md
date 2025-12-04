# Tersa Architecture Implementation Guide

## Overview
This document explains how Tersa's architecture has been integrated into the flow-generator page of the next-saas-lp-main project.

## Core Architecture Components

### 1. **Project Provider** (`/src/providers/project-provider.tsx`)
- Manages the current project context throughout the application
- Provides access to project data (nodes, edges, metadata) via `useProject()` hook
- Based on Tersa's Chapter 1: Projects and User Profile

**Usage:**
```tsx
const project = useProject();
// Access: project.id, project.content, project.name, etc.
```

### 2. **Gateway Provider** (`/src/providers/gateway-provider.tsx`)
- Central hub for all AI models (text, image, video, audio)
- Manages model definitions and pricing information
- Provides `useGateway()` hook for accessing available models
- Based on Tersa's Chapter 5: AI Models & Gateway

**Usage:**
```tsx
const { textModels } = useGateway();
// Access all available text generation models with pricing
```

### 3. **AI Model Definitions**
Located in `/src/lib/models/`:
- `image.ts` - Image generation models (DALL-E, FLUX, etc.)
- `text.ts` - Text generation models (GPT-4o, Claude, etc.)

Each model includes:
- Label and icon
- Provider (OpenAI, Anthropic, etc.)
- Cost calculation function
- Model-specific options (sizes, quality, etc.)
- Price indicators (lowest, low, high, highest)

### 4. **Provider Definitions** (`/src/lib/providers.ts`)
- Centralized registry of all AI providers
- Maps provider IDs to their metadata (name, icon)
- Used by model definitions to associate models with providers

### 5. **Server Actions** (`/src/app/actions/`)
Server-side functions for:

**Project Management** (`project.ts`):
- `updateProjectAction` - Save project changes (nodes, edges)
- `createProjectAction` - Create new projects
- `deleteProjectAction` - Delete projects
- `getProjectAction` - Fetch project data

**AI Operations** (`ai.ts`):
- `generateImageAction` - Generate images from text
- `generateTextAction` - Generate text responses
- `transcribeAudioAction` - Transcribe audio to text
- `generateVideoAction` - Generate videos from prompts

*Note: These currently use mock implementations. Replace with actual Django API calls.*

### 6. **Canvas Component** (`/src/components/flow-components/canvas.tsx`)
The main ReactFlow canvas implementing Tersa's architecture:

**Key Features:**
- Automatic project saving (debounced)
- Node validation and connection rules
- Copy/paste/duplicate operations
- Context menu for canvas operations
- Keyboard shortcuts (Cmd+A, Cmd+D, Cmd+C, Cmd+V)
- Cycle prevention in connections

**Architecture from Tersa's Chapter 3:**
- Uses `ReactFlow` for the visual canvas
- Manages nodes and edges state
- Validates connections with `isValidConnection`
- Auto-saves changes to project via `updateProjectAction`

### 7. **Node Types**
All node types are registered in `/src/components/flow-components/nodes/index.tsx`:
- `text` - Text input/generation
- `image` - Image generation/upload
- `video` - Video generation
- `audio` - Audio transcription
- `code` - Code execution
- `file` - File handling
- `tweet` - Tweet generation
- `drop` - Temporary connection helper

Each node has:
- **Primitive mode**: Direct user input
- **Transform mode**: AI processing from connected nodes

### 8. **Editor Integration** (Tiptap)
Based on Tersa's Chapter 4, the text editor provides:
- Rich text formatting (bold, italic, headings)
- Code blocks with syntax highlighting
- Lists (ordered, unordered, tasks)
- Slash commands for quick formatting
- Markdown support

Located in `/src/components/flow-components/ui/kibo-ui/editor/`

## How It Works: Data Flow

```
User Action (Add Node) 
  ↓
Canvas Component (ReactFlow)
  ↓
Update Local State (nodes, edges)
  ↓
Trigger Debounced Save
  ↓
updateProjectAction (Server Action)
  ↓
Django Backend (TODO: Implement)
  ↓
Database Update
```

## Integration with Django

### Current Implementation
The flow-generator page currently uses:
- Mock project data
- In-memory state management
- Simulated API responses

### Required Django Integration

1. **Authentication**
```typescript
// Add to server actions
const session = await getServerSession();
if (!session) throw new Error('Unauthorized');
```

2. **Project API Endpoints**
```python
# Django views.py
@api_view(['PATCH'])
def update_project(request, project_id):
    project = Project.objects.get(id=project_id, user=request.user)
    project.content = request.data.get('content')
    project.save()
    return Response({'success': True})
```

3. **AI API Endpoints**
```python
# Django views.py
@api_view(['POST'])
def generate_image(request):
    # Use AI SDK or direct API calls
    prompt = request.data.get('prompt')
    model = request.data.get('model')
    # Generate image...
    return Response({'imageUrl': url, 'cost': cost})
```

4. **Update Server Actions**
Replace mock implementations in `/src/app/actions/` with actual fetch calls:

```typescript
const response = await fetch(`${process.env.DJANGO_API_URL}/api/projects/${projectId}/`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify(data),
});
```

## Usage in Flow-Generator Page

```tsx
// /src/app/(dashboard)/flow-generator/page.tsx
<ProjectProvider data={project}>
  <GatewayProviderClient models={textModels}>
    <ReactFlowProvider>
      <Canvas>
        <Controls />
        <TopLeft />
        <TopRight />
        <Toolbar />
      </Canvas>
    </ReactFlowProvider>
  </GatewayProviderClient>
</ProjectProvider>
```

## Key Features Implemented

1. ✅ **Visual Workflow Builder** - ReactFlow canvas with drag-and-drop
2. ✅ **Node System** - Multiple node types (text, image, video, audio)
3. ✅ **Auto-Save** - Debounced project saving
4. ✅ **AI Model Selection** - Dropdown for choosing models
5. ✅ **Connection Validation** - Prevents invalid connections
6. ✅ **Rich Text Editor** - Tiptap for formatted prompts
7. ✅ **Provider Architecture** - Centralized model definitions
8. ✅ **Server Actions** - Ready for Django integration

## Next Steps

1. **Connect to Django Backend**
   - Replace mock data with real API calls
   - Implement authentication flow
   - Set up WebSocket for real-time updates

2. **Implement AI SDK**
   - Install `@ai-sdk/gateway`
   - Configure API keys in environment
   - Connect nodes to actual AI models

3. **Add Credits System**
   - Track API usage costs
   - Display remaining credits
   - Implement payment flow

4. **Enhance UI**
   - Add loading states
   - Implement error boundaries
   - Add toast notifications

5. **Testing**
   - Unit tests for server actions
   - Integration tests for canvas
   - E2E tests for workflows

## File Structure

```
src/
├── app/
│   ├── actions/
│   │   ├── project.ts       # Project CRUD
│   │   └── ai.ts            # AI operations
│   └── (dashboard)/
│       └── flow-generator/
│           └── page.tsx     # Main page
├── components/
│   └── flow-components/
│       ├── canvas.tsx       # ReactFlow canvas
│       ├── nodes/           # All node types
│       └── ui/              # UI components
├── lib/
│   ├── models/              # AI model definitions
│   ├── providers.ts         # Provider registry
│   └── xyflow.ts           # ReactFlow helpers
└── providers/
    ├── project-provider.tsx # Project context
    └── gateway-provider.tsx # AI gateway context
```

## References

- [Tersa Documentation](https://github.com/haydenbleasel/tersa)
- [ReactFlow Docs](https://reactflow.dev/)
- [AI SDK Docs](https://sdk.vercel.ai/)
- [Tiptap Docs](https://tiptap.dev/)
