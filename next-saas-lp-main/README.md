# Next.js SaaS Landing Page

A modern, production-ready SaaS landing page and dashboard built with Next.js 15, React 19, and TypeScript.

## 🆕 Latest Feature: Flow Generator

**NEW!** We've added a complete Tersa-like visual workflow builder for AI content generation!

### Quick Start
```bash
npm install
npm run dev
# Visit http://localhost:3000/flow-generator
```

## 🛠️ Local Setup & Run (verified)

- Prerequisites: Node.js 18+ (tested with 23.x) and npm
- Install deps: `npm install`
- Env (optional for backend APIs): create `.env.local`
  ```bash
  NEXT_PUBLIC_DJANGO_URL=http://localhost:8000
  ```
- Development: `npm run dev -- --hostname 0.0.0.0 --port 3000` (Turbopack). If port 3000 is busy, override `--port 4000`.
- Production: `npm run build` then `npm start -- --hostname 0.0.0.0 --port 3000` (also supports `--port 4000` if needed).
- Frontend runs without the Django backend; API calls will fail until a backend is available at `NEXT_PUBLIC_DJANGO_URL`.

### Documentation
See [`FLOW_GENERATOR_INDEX.md`](./FLOW_GENERATOR_INDEX.md) for complete documentation.

## 🚀 Features

### Landing Pages
- Modern hero sections
- Feature showcases
- Pricing tables
- Testimonials
- FAQ sections
- Newsletter signup

### Dashboard
- User authentication
- Profile management
- Brand management
- Twitter automation
- Instagram automation
- Analytics dashboard
- CRM system
- Task management
- Chat system
- **Flow Generator** (NEW!)

### Flow Generator (Tersa-style)
- Visual workflow builder
- 5 node types: Text, Image, Audio, Video, Code
- Drag-and-drop interface
- Node connections for AI pipelines
- Auto-save functionality
- Beautiful glassmorphism UI

## 🛠️ Tech Stack

- **Framework**: Next.js 15
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components with Radix UI
- **Icons**: Lucide React, Tabler Icons
- **Animations**: Framer Motion, GSAP
- **Workflow**: React Flow (@xyflow/react)
- **State**: React Context API
- **Backend**: Django (separate repository)

## 📦 Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 🎯 Project Structure

```
next-saas-lp-main/
├── src/
│   ├── app/                          # Next.js app directory
│   │   ├── (auth)/                   # Auth pages
│   │   ├── (dashboard)/              # Dashboard pages
│   │   │   ├── flow-generator/       # Flow Generator (NEW!)
│   │   │   ├── dashboard/            # Main dashboard
│   │   │   ├── feed/                 # Social feed
│   │   │   └── layout.tsx            # Dashboard layout
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Landing page
│   │
│   ├── components/                   # React components
│   │   ├── flow/                     # Flow Generator components (NEW!)
│   │   ├── ui/                       # UI components
│   │   └── ...                       # Other components
│   │
│   ├── providers/                    # Context providers
│   │   ├── flow-provider.tsx         # Flow state (NEW!)
│   │   └── ...                       # Other providers
│   │
│   ├── lib/                          # Utility functions
│   │   ├── node-buttons.ts           # Flow node configs (NEW!)
│   │   └── ...                       # Other utils
│   │
│   ├── sections/                     # Landing page sections
│   └── hooks/                        # Custom React hooks
│
├── public/                           # Static assets
├── FLOW_GENERATOR_*.md              # Flow Generator docs (NEW!)
├── INTEGRATION_ROADMAP.md           # Backend integration guide
└── package.json
```

## 🎨 Features in Detail

### Dashboard Pages
- `/dashboard` - Main dashboard home
- `/dashboard/brands` - Brand management
- `/dashboard/twitter/*` - Twitter automation
- `/dashboard/instagram/*` - Instagram automation
- `/dashboard/analytics` - Analytics dashboard
- `/dashboard/crm/*` - CRM system
- `/dashboard/tasks` - Task management
- `/dashboard/chat` - Chat system
- `/dashboard/settings` - User settings
- `/flow-generator` - AI workflow builder (NEW!)

### Landing Page Sections
- Hero with animations
- Features showcase
- Pricing plans
- Testimonials
- FAQ
- Newsletter
- Footer

## 🔌 Backend Integration

This frontend is designed to work with a Django backend. See [`INTEGRATION_ROADMAP.md`](./INTEGRATION_ROADMAP.md) for:
- Authentication setup
- API endpoint connections
- Data flow architecture
- Implementation timeline

## 📚 Documentation

### Flow Generator
- [`FLOW_GENERATOR_INDEX.md`](./FLOW_GENERATOR_INDEX.md) - Documentation index
- [`FLOW_GENERATOR_QUICKSTART.md`](./FLOW_GENERATOR_QUICKSTART.md) - Quick start guide
- [`FLOW_GENERATOR_SUMMARY.md`](./FLOW_GENERATOR_SUMMARY.md) - Complete overview
- [`FLOW_GENERATOR_SHOWCASE.md`](./FLOW_GENERATOR_SHOWCASE.md) - Visual guide
- [`FLOW_GENERATOR_ARCHITECTURE.md`](./FLOW_GENERATOR_ARCHITECTURE.md) - Technical details
- [`FLOW_GENERATOR_README.md`](./FLOW_GENERATOR_README.md) - Feature docs
- [`DJANGO_BACKEND_INTEGRATION.md`](./DJANGO_BACKEND_INTEGRATION.md) - Backend guide

### Integration
- [`INTEGRATION_ROADMAP.md`](./INTEGRATION_ROADMAP.md) - Complete integration plan

## 🎯 Development

### Prerequisites
- Node.js 18+ 
- npm or pnpm
- Django backend (optional, for full functionality)

### Environment Variables
Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running the App
```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Linting
npm run lint
```

## 🎨 Customization

### Colors
Edit Tailwind CSS configuration or component styles.

### Components
All components are in `src/components/` and can be customized.

### Flow Generator Nodes
Add new node types in `src/components/flow/nodes/`.

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Other Platforms
The app can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- Render

## 📝 License

This is a private project. All rights reserved.

## 🤝 Contributing

This is a private project, but feel free to fork and customize for your own use.

## 📞 Support

For questions or issues:
1. Check documentation in `FLOW_GENERATOR_INDEX.md`
2. Review integration guide in `INTEGRATION_ROADMAP.md`
3. Check Next.js docs: https://nextjs.org/docs
4. Check React Flow docs: https://reactflow.dev/

## 🎉 Recent Updates

### November 18, 2025
- ✅ Added complete Flow Generator feature
- ✅ Implemented 5 node types (Text, Image, Audio, Video, Code)
- ✅ Created comprehensive documentation (6 files)
- ✅ Added Django backend integration guide
- ✅ Updated integration roadmap
- ✅ Installed required dependencies

### Features
- Visual workflow builder with React Flow
- Glassmorphism UI design
- Auto-save functionality
- Keyboard shortcuts
- Node operations (duplicate, focus, delete)
- Connection system for AI pipelines

## 🗺️ Roadmap

See [`INTEGRATION_ROADMAP.md`](./INTEGRATION_ROADMAP.md) for the complete 10-week implementation plan:

- [x] Phase 0: Flow Generator Frontend (Complete!)
- [ ] Phase 1: Authentication (Week 1)
- [ ] Phase 2: Brands (Week 2)
- [ ] Phase 3: Twitter (Weeks 3-4)
- [ ] Phase 4: Instagram (Week 5)
- [ ] Phase 5: Analytics (Week 6)
- [ ] Phase 6: CRM (Week 7)
- [ ] Phase 7: Tasks & Chat (Week 8)
- [ ] Phase 8: Flow Generator Backend (Week 9)
- [ ] Phase 9: Referral System (Week 10)

## 🌟 Highlights

- **Modern Stack**: Next.js 15, React 19, TypeScript
- **Beautiful UI**: Glassmorphism, smooth animations
- **Production Ready**: Type-safe, optimized, documented
- **Extensible**: Easy to add features and customize
- **Well Documented**: 6+ documentation files
- **Backend Ready**: Django integration guides included

---

**Built with ❤️ using Next.js and React**

For detailed Flow Generator documentation, start with [`FLOW_GENERATOR_INDEX.md`](./FLOW_GENERATOR_INDEX.md)
