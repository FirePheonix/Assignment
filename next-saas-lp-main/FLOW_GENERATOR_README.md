# Flow Generator - Tersa-like Workflow Builder

A visual, node-based workflow builder for AI content generation, inspired by Tersa.

## Features

✨ **Visual Node-Based Interface**
- Drag-and-drop workflow creation
- Connect nodes to build AI pipelines
- Real-time visual feedback

🎨 **Node Types**
- **Text Generator**: Generate text with AI using custom instructions
- **Image Generator**: Create images from text prompts
- **Audio Generator**: Convert text to speech
- **Video Generator**: Generate videos from prompts
- **Code Executor**: Run code snippets in the browser

🔄 **Workflow Features**
- Connect nodes to create complex workflows
- Automatic save with Django backend
- Duplicate and manage nodes easily
- Keyboard shortcuts (Cmd+A for select all)
- Context menu for node operations

## Usage

1. Navigate to `/flow-generator` in the dashboard
2. Click on node buttons in the bottom toolbar to add nodes
3. Connect nodes by dragging from output (right) to input (left) handles
4. Configure each node with your prompts/instructions
5. Click "Generate" to execute

## Backend Integration

The frontend is ready and needs Django backend integration. See `DJANGO_BACKEND_INTEGRATION.md` for:

- API endpoint examples
- Database model structure
- Integration points for AI services

### API Endpoints Needed

```
POST /api/flow/save              # Save workflow
GET  /api/flow/load/:id          # Load workflow
POST /api/flow/generate/text     # Generate text
POST /api/flow/generate/image    # Generate image
POST /api/flow/generate/audio    # Generate audio
POST /api/flow/generate/video    # Generate video
POST /api/flow/execute/code      # Execute code
```

## Node Operations

### Adding Nodes
- Click any node type in the bottom toolbar
- Nodes appear at the viewport center

### Connecting Nodes
- Drag from the purple dot on the right (source)
- Drop on the purple dot on the left (target)
- Create AI pipelines by chaining nodes

### Node Menu
- Click the three dots on any node
- Options: Duplicate, Focus, Delete

## Keyboard Shortcuts

- `Cmd/Ctrl + A` - Select all nodes
- `Delete/Backspace` - Delete selected nodes
- Double-click - (Reserved for future use)

## Technical Stack

- **Frontend**: Next.js 15, React Flow, TypeScript
- **Styling**: Tailwind CSS with glassmorphism effects
- **Backend**: Django REST Framework (to be integrated)
- **State**: React Context API

## Customization

### Adding New Node Types

1. Create node component in `src/components/flow/nodes/`
2. Add to `src/components/flow/nodes/index.tsx`
3. Add button config in `src/lib/node-buttons.ts`
4. Create corresponding Django API endpoint

### Styling

All nodes use glassmorphism with:
- Dark gradient backgrounds
- Backdrop blur effects
- Purple accent colors (matching Tersa style)

## Future Enhancements

- [ ] Node templates library
- [ ] Export/import workflows
- [ ] Collaborative editing
- [ ] Workflow versioning
- [ ] Real-time execution status
- [ ] Node output preview
- [ ] Batch processing
- [ ] Workflow scheduling

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Access flow generator
http://localhost:3000/flow-generator
```

## Notes

- All generation functions currently log to console
- Replace placeholder API calls with actual Django endpoints
- Implement proper authentication for API calls
- Add error handling and loading states
- Consider rate limiting for AI generations
