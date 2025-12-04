# Flow Generator Architecture

## Component Hierarchy

```
/flow-generator (Page)
├── ReactFlowProvider
│   └── FlowProvider
│       └── FlowCanvas
│           ├── NodeOperationsProvider
│           │   └── ReactFlow
│           │       ├── Background
│           │       ├── Controls
│           │       ├── MiniMap
│           │       ├── Nodes (TextNode, ImageNode, etc.)
│           │       ├── FlowToolbar (Bottom)
│           │       └── SaveIndicator (Top Right)
```

## Data Flow

```
User Action
    ↓
Canvas Component
    ↓
State Update (nodes/edges)
    ↓
Debounced Save Function (1 second)
    ↓
Django API Call
    ↓
Database Persistence
```

## Node Types Flow

```
1. Text Node
   Input: Instructions (textarea)
   Action: Generate button → API call
   Output: Generated text display

2. Image Node
   Input: Prompt (textarea)
   Action: Generate button → API call
   Output: Image preview

3. Audio Node
   Input: Text (textarea)
   Action: Generate button → API call
   Output: Audio player

4. Video Node
   Input: Prompt (textarea)
   Action: Generate button → API call
   Output: Video player

5. Code Node
   Input: Code (textarea)
   Action: Run button → API call
   Output: Execution result
```

## Node Connection Flow

```
Source Node (Right Handle)
    ↓
Connection Drag
    ↓
Target Node (Left Handle)
    ↓
Edge Created
    ↓
Saved to State
    ↓
Auto-saved to Django
```

## File Structure

```
src/
├── app/
│   └── (dashboard)/
│       └── flow-generator/
│           └── page.tsx                 # Main page entry
│
├── components/
│   └── flow/
│       ├── canvas.tsx                   # Main canvas logic
│       ├── toolbar.tsx                  # Bottom node toolbar
│       ├── save-indicator.tsx           # Save status display
│       └── nodes/
│           ├── index.tsx                # Node registry
│           ├── node-layout.tsx          # Shared layout
│           ├── text-node.tsx            # Text generator
│           ├── image-node.tsx           # Image generator
│           ├── audio-node.tsx           # Audio generator
│           ├── video-node.tsx           # Video generator
│           └── code-node.tsx            # Code executor
│
├── providers/
│   ├── flow-provider.tsx                # Flow state management
│   └── node-operations-provider.tsx     # Node operations
│
└── lib/
    └── node-buttons.ts                  # Node configurations
```

## API Integration Points

### Frontend → Django

1. **Save Flow:**
   ```typescript
   POST /api/flow/save
   Body: { name, nodes, edges }
   Response: { success, id }
   ```

2. **Load Flow:**
   ```typescript
   GET /api/flow/load/:id
   Response: { nodes, edges }
   ```

3. **Generate Text:**
   ```typescript
   POST /api/flow/generate/text
   Body: { instructions }
   Response: { text }
   ```

4. **Generate Image:**
   ```typescript
   POST /api/flow/generate/image
   Body: { prompt }
   Response: { imageUrl }
   ```

5. **Generate Audio:**
   ```typescript
   POST /api/flow/generate/audio
   Body: { text }
   Response: { audioUrl }
   ```

6. **Generate Video:**
   ```typescript
   POST /api/flow/generate/video
   Body: { prompt }
   Response: { videoUrl }
   ```

7. **Execute Code:**
   ```typescript
   POST /api/flow/execute/code
   Body: { code, language }
   Response: { output }
   ```

## State Management

### Flow Provider State
```typescript
{
  saveState: {
    isSaving: boolean,
    lastSaved: Date | null
  },
  setSaveState: Dispatch<SetStateAction<FlowState>>
}
```

### Canvas State
```typescript
{
  nodes: Node[],           // Array of workflow nodes
  edges: Edge[],           // Array of connections
  setNodes: Function,      // Update nodes
  setEdges: Function       // Update edges
}
```

### Node Operations Context
```typescript
{
  addNode: (type, options) => string,
  duplicateNode: (id) => void
}
```

## Node Structure

```typescript
interface Node {
  id: string,              // Unique identifier (nanoid)
  type: string,            // 'text' | 'image' | 'audio' | 'video' | 'code'
  position: {
    x: number,
    y: number
  },
  data: {
    // Node-specific data
    text?: string,
    prompt?: string,
    instructions?: string,
    imageUrl?: string,
    audioUrl?: string,
    videoUrl?: string,
    code?: string,
    output?: string
  }
}
```

## Edge Structure

```typescript
interface Edge {
  id: string,              // Unique identifier (nanoid)
  source: string,          // Source node ID
  target: string,          // Target node ID
  type: 'smoothstep',      // Edge visualization type
  animated: boolean        // Show animated flow
}
```

## Styling System

### Colors
- **Background**: `from-black via-gray-900 to-black`
- **Accent**: `purple-500`, `purple-600`
- **Glassmorphism**: `bg-white/5`, `backdrop-blur-xl`
- **Borders**: `border-white/10`, `border-white/20`
- **Text**: `text-white/90`, `text-white/70`, `text-white/50`

### Effects
- **Hover**: `hover:bg-white/10`
- **Focus**: `focus:ring-2 focus:ring-purple-500`
- **Transitions**: `transition-all`, `transition-colors`
- **Shadows**: `shadow-2xl`, `shadow-lg`

## User Interactions

### Adding Nodes
1. Click node button in toolbar
2. Node appears at viewport center
3. Node is automatically selected
4. Auto-save triggered

### Connecting Nodes
1. Drag from source handle (right)
2. Drop on target handle (left)
3. Edge created with animation
4. Auto-save triggered

### Node Menu (3 dots)
- **Duplicate**: Creates copy with +200px offset
- **Focus**: Centers viewport on node
- **Delete**: Removes node and connections

### Keyboard Shortcuts
- **Cmd+A**: Select all nodes
- **Delete/Backspace**: Delete selected nodes
- **Escape**: Close menus/dialogs

## Performance Optimizations

1. **Debounced Save**: 1-second delay prevents excessive API calls
2. **Memoized Nodes**: React.memo prevents unnecessary re-renders
3. **Context Separation**: Flow state separate from node operations
4. **Lazy Loading**: Components loaded on demand

## Security Considerations

### Code Execution Node
- Must run in sandboxed environment
- Use Docker containers or restricted Python
- Timeout limits (30 seconds max)
- Resource limits (CPU, memory)
- No network access from executed code

### API Security
- JWT authentication required
- Rate limiting on generation endpoints
- Input validation and sanitization
- File size limits for uploads
- CORS configuration

## Scalability

### Database Design
```sql
-- Flow configurations table
CREATE TABLE flow_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    brand_id INTEGER REFERENCES brands(id),
    name VARCHAR(255),
    nodes JSONB,
    edges JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Flow executions table
CREATE TABLE flow_executions (
    id SERIAL PRIMARY KEY,
    flow_id INTEGER REFERENCES flow_configurations(id),
    status VARCHAR(20),
    results JSONB,
    created_at TIMESTAMP
);
```

### Caching Strategy
- Cache AI generations by prompt hash
- Store generated assets in CDN
- Cache flow configurations
- Rate limit per user

## Future Enhancements

1. **Templates**: Pre-built workflow templates
2. **Export/Import**: JSON workflow files
3. **Collaboration**: Real-time multi-user editing
4. **Versioning**: Flow history and rollback
5. **Scheduling**: Automated workflow execution
6. **Webhooks**: Trigger workflows from external events
7. **Variables**: Pass data between nodes
8. **Conditional Logic**: If/else branches
9. **Loops**: Repeat operations
10. **Sub-flows**: Nested workflows

---

This architecture provides a solid foundation for a production-ready AI workflow builder!
