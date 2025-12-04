# Frontend → Backend Integration Roadmap

**Project:** Connecting Next.js Dashboard to Django Backend  
**Start Date:** November 18, 2025  
**Estimated Timeline:** 9 weeks

---

## 📊 Current Status

- **Django Backend:** 108+ templates, 7,715+ lines of API code ✅
- **Next.js Frontend:** 24+ pages (UI shell + Flow Generator) ✅
- **Flow Generator:** Tersa-like workflow builder implemented ✅
- **Implementation Gap:** ~75% of features need backend integration
- **Django API Base URL:** `http://localhost:8000`

---

## 🎯 PHASE 1: AUTHENTICATION & USER FOUNDATION
**Timeline:** Week 1 (Days 1-7)  
**Priority:** CRITICAL - Start here first

### Why This First?
Nothing works without authentication. All APIs require JWT tokens.

### Installation
```bash
cd d:\Gemnar-com\next-saas-lp-main
npm install next-auth @auth/prisma-adapter axios
```

### Tasks

#### 1.1 Create API Client Layer
**File:** `src/lib/api-client.ts`

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

#### 1.2 Setup Next-Auth
**File:** `src/app/api/auth/[...nextauth]/route.ts`

```typescript
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import apiClient from '@/lib/api-client';

const handler = NextAuth({
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        const res = await apiClient.post('/api/auth/login/', {
          email: credentials?.email,
          password: credentials?.password,
        });
        
        if (res.data.token) {
          return {
            id: res.data.user.id,
            email: res.data.user.email,
            token: res.data.token,
          };
        }
        return null;
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    }
  }
});

export { handler as GET, handler as POST };
```

#### 1.3 Environment Variables
**File:** `.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your-super-secret-key-change-this
NEXTAUTH_URL=http://localhost:3000
```

#### 1.4 Update Profile Settings Page
**File:** `src/app/(dashboard)/dashboard/settings/page.tsx`

Connect the form to Django's `GET/PATCH /api/users/profile/`

```typescript
// Add at top
import apiClient from '@/lib/api-client';
import { useSession } from 'next-auth/react';

// Replace mock data with API call
useEffect(() => {
  const fetchProfile = async () => {
    const res = await apiClient.get('/api/users/profile/');
    setFormData(res.data);
  };
  fetchProfile();
}, []);

// Update handleSubmit
const handleSubmit = async (e) => {
  e.preventDefault();
  await apiClient.patch('/api/users/profile/', formData);
};
```

### Django Endpoints
- `POST /api/auth/login/` - Login (needs creation)
- `GET /api/users/profile/` - Get user profile ✅
- `PATCH /api/users/profile/` - Update profile ✅

### Deliverables
- [ ] API client with interceptors
- [ ] Next-Auth configuration
- [ ] Login/logout flow
- [ ] Protected routes middleware
- [ ] User profile fetch/update
- [ ] Session persistence

### Success Criteria
✅ User can login with Django credentials  
✅ JWT token stored and sent with requests  
✅ Profile page shows real user data  
✅ Form saves to Django database  

---

## 🎯 PHASE 2: BRANDS & ORGANIZATION
**Timeline:** Week 2 (Days 8-14)  
**Priority:** HIGH - Required for all social features

### Why This Second?
All Twitter/Instagram/Analytics features are brand-specific. Users need to select a brand context.

### Tasks

#### 2.1 Create Brand Context Provider
**File:** `src/contexts/brand-context.tsx`

```typescript
'use client';
import { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface Brand {
  id: number;
  name: string;
  slug: string;
  logo?: string;
}

const BrandContext = createContext<{
  selectedBrand: Brand | null;
  brands: Brand[];
  selectBrand: (brand: Brand) => void;
}>({
  selectedBrand: null,
  brands: [],
  selectBrand: () => {},
});

export function BrandProvider({ children }) {
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState(null);

  useEffect(() => {
    const fetchBrands = async () => {
      const res = await apiClient.get('/api/brands/');
      setBrands(res.data);
      if (res.data.length > 0) {
        setSelectedBrand(res.data[0]);
      }
    };
    fetchBrands();
  }, []);

  return (
    <BrandContext.Provider value={{ selectedBrand, brands, selectBrand: setSelectedBrand }}>
      {children}
    </BrandContext.Provider>
  );
}

export const useBrand = () => useContext(BrandContext);
```

#### 2.2 Update Brand List Page
**File:** `src/app/(dashboard)/dashboard/brands/page.tsx`

Replace mock data with API calls:

```typescript
import { useBrand } from '@/contexts/brand-context';

const { brands } = useBrand();
// Use real brands from context
```

#### 2.3 Add Brand Selector to Layout
**File:** `src/app/(dashboard)/layout.tsx`

Add dropdown in sidebar to switch brands.

### Django Endpoints
- `GET /api/brands/` - List user's brands ✅
- `POST /api/brands/create/` - Create brand ✅
- `PUT /api/brands/{brand_id}/` - Update brand ✅
- `POST /api/brands/{brand_id}/set-default/` - Set default ✅

### Deliverables
- [ ] Brand context provider
- [ ] Brand list from API
- [ ] Brand selector in sidebar
- [ ] Brand creation form
- [ ] Brand edit functionality
- [ ] Default brand persistence

### Success Criteria
✅ Brand dropdown shows user's brands  
✅ Selected brand persists across pages  
✅ User can create new brands  
✅ User can switch between brands  

---

## 🎯 PHASE 3: TWITTER AUTOMATION
**Timeline:** Weeks 3-4 (Days 15-28)  
**Priority:** CRITICAL - Core product feature

### Why This Third?
Twitter automation is the main value proposition. Most complex integration.

### Tasks

#### 3.1 Twitter API Configuration
**File:** `src/app/(dashboard)/dashboard/twitter/config/page.tsx`

```typescript
const handleSubmit = async (e) => {
  e.preventDefault();
  await apiClient.post(`/api/brands/${brandId}/connect-twitter/`, {
    twitter_api_key: formData.apiKey,
    twitter_api_secret: formData.apiSecret,
    twitter_access_token: formData.accessToken,
    twitter_access_token_secret: formData.accessTokenSecret,
    twitter_bearer_token: formData.bearerToken,
  });
};

const testConnection = async () => {
  const res = await apiClient.post(`/api/brands/${brandId}/test-twitter/`);
  // Show success/error message
};
```

#### 3.2 Tweet Queue System
**File:** `src/app/(dashboard)/dashboard/twitter/queue/page.tsx`

```typescript
useEffect(() => {
  const fetchTweets = async () => {
    const res = await apiClient.get('/api/twitter/brand-tweets/', {
      params: { brand_id: selectedBrand.id }
    });
    setTweets(res.data);
  };
  fetchTweets();
}, [selectedBrand]);

const postNow = async (tweetId) => {
  await apiClient.post(`/api/twitter/brand-tweets/${tweetId}/post-now/`);
  // Refresh list
};
```

#### 3.3 Create Tweet Form
Add form to create new tweets:

```typescript
const createTweet = async (data) => {
  await apiClient.post('/api/twitter/brand-tweets/', {
    brand: selectedBrand.id,
    text: data.text,
    scheduled_time: data.scheduledTime,
    status: 'draft',
  });
};
```

#### 3.4 AI Content Generation
Add strategy selector and AI generation:

```typescript
const strategies = await apiClient.get('/api/twitter/strategies/');

const generateWithAI = async (strategyId) => {
  const res = await apiClient.post('/api/twitter/generate-with-strategy/', {
    strategy_id: strategyId,
    brand_id: selectedBrand.id,
  });
  setTweetText(res.data.text);
};
```

#### 3.5 Image Generation
Add AI image generation button:

```typescript
const generateImage = async (tweetId) => {
  const res = await apiClient.post(`/api/twitter/tweets/${tweetId}/generate-image/`, {
    quality: 'high',
    prompt: 'custom prompt if needed',
  });
  // Show generated image
};
```

#### 3.6 Tweet Analytics
**File:** `src/app/(dashboard)/dashboard/twitter/analytics/page.tsx`

```typescript
const analytics = await apiClient.get('/api/twitter/analytics/', {
  params: { brand_id: selectedBrand.id }
});
```

### Django Endpoints (Already Exist!)
- `GET /api/twitter/brand-tweets/` - List tweets ✅
- `POST /api/twitter/brand-tweets/` - Create tweet ✅
- `PUT /api/twitter/brand-tweets/{tweet_id}/` - Update tweet ✅
- `DELETE /api/twitter/tweets/{tweet_id}/delete/` - Delete tweet ✅
- `POST /api/twitter/brand-tweets/{tweet_id}/post-now/` - Post immediately ✅
- `POST /api/twitter/brand-tweets/{tweet_id}/refresh-metrics/` - Refresh metrics ✅
- `POST /api/twitter/generate-with-strategy/` - AI generation ✅
- `POST /api/twitter/tweets/{tweet_id}/generate-image/` - Image generation ✅
- `POST /api/twitter/tweets/{tweet_id}/generate-text/` - Text generation ✅
- `GET /api/twitter/strategies/` - Strategy list ✅
- `GET /api/twitter/strategies/by-category/` - Strategies by category ✅
- `GET /api/twitter/analytics/` - Analytics data ✅
- `POST /api/brands/{brand_id}/connect-twitter/` - Connect API ✅
- `POST /api/brands/{brand_id}/test-twitter/` - Test connection ✅

### Deliverables
- [ ] Twitter API configuration form
- [ ] Connection test functionality
- [ ] Tweet queue with real data
- [ ] Create/edit tweet forms
- [ ] Schedule tweet functionality
- [ ] Post now button
- [ ] AI content generation
- [ ] AI image generation
- [ ] Tweet strategy selector
- [ ] Tweet analytics dashboard
- [ ] Metrics refresh
- [ ] Tweet deletion

### Success Criteria
✅ User can connect Twitter API credentials  
✅ Connection test passes  
✅ Tweets display in queue  
✅ User can create tweets  
✅ AI generates tweet content  
✅ AI generates images  
✅ Tweets post to Twitter successfully  
✅ Analytics show real data  

---

## 🎯 PHASE 4: INSTAGRAM AUTOMATION
**Timeline:** Week 5 (Days 29-35)  
**Priority:** HIGH - Secondary social platform

### Tasks

#### 4.1 Instagram OAuth Connection
**File:** `src/app/(dashboard)/dashboard/instagram/connect/page.tsx`

```typescript
const checkStatus = async () => {
  const res = await apiClient.get('/api/instagram/oauth-status/', {
    params: { brand_id: selectedBrand.id }
  });
  setConnected(res.data.connected);
};

const startOAuth = async () => {
  const res = await apiClient.get('/api/instagram/oauth-start/', {
    params: { brand_id: selectedBrand.id }
  });
  window.location.href = res.data.auth_url;
};
```

#### 4.2 Instagram Post Queue
**File:** `src/app/(dashboard)/dashboard/instagram/queue/page.tsx`

```typescript
const fetchPosts = async () => {
  const res = await apiClient.get('/api/instagram/brand-posts/', {
    params: { brand_id: selectedBrand.id }
  });
  setPosts(res.data);
};

const postNow = async (postId) => {
  await apiClient.post(`/api/instagram/brand-posts/${postId}/post-now/`);
};
```

#### 4.3 Video Generation
Add video generation form:

```typescript
const generateVideo = async (data) => {
  const res = await apiClient.post('/api/instagram/generate-video/', {
    brand_id: selectedBrand.id,
    prompt: data.prompt,
    duration: data.duration,
    quality: data.quality,
  });
  
  // Poll for video status
  const taskId = res.data.task_id;
  pollVideoStatus(taskId);
};

const pollVideoStatus = async (taskId) => {
  const interval = setInterval(async () => {
    const res = await apiClient.get(`/api/instagram/video-status/${taskId}/`);
    if (res.data.status === 'completed') {
      clearInterval(interval);
      // Show video
    }
  }, 3000);
};
```

### Django Endpoints (Already Exist!)
- `GET /api/instagram/oauth-status/` - Check connection ✅
- `GET /api/instagram/oauth-start/` - Start OAuth ✅
- `GET /api/instagram/oauth-callback/` - OAuth callback ✅
- `GET /api/instagram/brand-posts/` - List posts ✅
- `POST /api/instagram/brand-posts/` - Create post ✅
- `PUT /api/instagram/brand-posts/{post_id}/` - Update post ✅
- `POST /api/instagram/brand-posts/{post_id}/post-now/` - Post now ✅
- `POST /api/instagram/generate-video/` - Generate video ✅
- `GET /api/instagram/video-status/{task_uuid}/` - Check video status ✅
- `POST /api/instagram/upload-video/` - Upload video ✅
- `POST /api/instagram/generate-content/` - AI caption ✅

### Deliverables
- [ ] Instagram OAuth flow
- [ ] Connection status display
- [ ] Post queue with real data
- [ ] Create post form
- [ ] Video generation UI
- [ ] Video status polling
- [ ] Post scheduling
- [ ] Post now functionality
- [ ] AI caption generation

### Success Criteria
✅ User can connect Instagram account  
✅ Posts display in queue  
✅ User can create posts  
✅ Videos generate successfully  
✅ Posts publish to Instagram  

---

## 🎯 PHASE 5: ANALYTICS INTEGRATION
**Timeline:** Week 6 (Days 36-42)  
**Priority:** MEDIUM - Data insights

### Tasks

#### 5.1 Analytics Dashboard
**File:** `src/app/(dashboard)/dashboard/analytics/page.tsx`

```typescript
import { Chart } from 'chart.js/auto';

const fetchAnalytics = async () => {
  const res = await apiClient.get(`/api/analytics/${selectedBrand.id}/data/`, {
    params: {
      start_date: startDate,
      end_date: endDate,
    }
  });
  setAnalytics(res.data);
};

// Replace mock data with real metrics
<StatCard
  label="Page Views"
  value={analytics.total_pageviews}
  change={analytics.pageviews_change}
/>
```

#### 5.2 Install Chart.js
```bash
npm install chart.js react-chartjs-2
```

#### 5.3 Create Charts
```typescript
const chartData = {
  labels: analytics.daily_pageviews.map(d => d.date),
  datasets: [{
    label: 'Page Views',
    data: analytics.daily_pageviews.map(d => d.count),
  }]
};
```

### Django Endpoints (Already Exist!)
- `GET /api/analytics/{brand_id}/data/` - Dashboard metrics ✅
- `POST /api/analytics/pageview` - Track page view ✅
- `POST /api/analytics/event` - Track event ✅
- `GET /api/analytics/metrics` - Get metrics ✅
- `GET /brand/{brand_id}/analytics/sessions/` - Session data ✅
- `GET /brand/{brand_id}/analytics/pages/` - Page analytics ✅
- `GET /brand/{brand_id}/analytics/events/` - Event analytics ✅

### Deliverables
- [ ] Real analytics data display
- [ ] Chart.js visualizations
- [ ] Date range selector
- [ ] Page analytics
- [ ] Event tracking
- [ ] Session data
- [ ] Conversion funnels

### Success Criteria
✅ Dashboard shows real metrics  
✅ Charts display data correctly  
✅ Date filtering works  
✅ Page analytics functional  

---

## 🎯 PHASE 6: CRM SYSTEM
**Timeline:** Week 7 (Days 43-49)  
**Priority:** MEDIUM - Business management

### Tasks

#### 6.1 Check CRM Models
Verify Django has CRM models (Contact, Company, Deal) in `website/models.py`.  
If not, create them first.

#### 6.2 Create CRM API Endpoints
**Django:** Add to `api_views.py`

```python
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def contacts_list(request):
    if request.method == 'GET':
        contacts = Contact.objects.filter(brand=request.user.selected_brand)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)
    # POST logic...
```

#### 6.3 Connect CRM Pages
**Files:** 
- `src/app/(dashboard)/dashboard/crm/contacts/page.tsx`
- `src/app/(dashboard)/dashboard/crm/companies/page.tsx`
- `src/app/(dashboard)/dashboard/crm/deals/page.tsx`

### Django Endpoints (Need Creation!)
- `GET /api/crm/contacts/` - List contacts ❌
- `POST /api/crm/contacts/` - Create contact ❌
- `GET /api/crm/companies/` - List companies ❌
- `POST /api/crm/companies/` - Create company ❌
- `GET /api/crm/deals/` - List deals ❌
- `POST /api/crm/deals/` - Create deal ❌

### Deliverables
- [ ] CRM models in Django
- [ ] CRM API endpoints
- [ ] Contacts CRUD
- [ ] Companies CRUD
- [ ] Deals CRUD
- [ ] Pipeline visualization

### Success Criteria
✅ Contacts display from database  
✅ User can add contacts  
✅ Companies management works  
✅ Deals pipeline functional  

---

## 🎯 PHASE 7: TASKS & CHAT
**Timeline:** Week 8 (Days 50-56)  
**Priority:** MEDIUM - Collaboration features

### Tasks

#### 7.1 Tasks Integration
**File:** `src/app/(dashboard)/dashboard/tasks/page.tsx`

```typescript
const fetchTasks = async () => {
  const res = await apiClient.get('/api/tasks/');
  setTasks(res.data);
};

const createTask = async (data) => {
  await apiClient.post('/api/tasks/', data);
};
```

#### 7.2 Chat WebSocket
**Install Socket.io:**
```bash
npm install socket.io-client
```

**File:** `src/lib/socket-client.ts`

```typescript
import { io } from 'socket.io-client';

const socket = io(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000');

export default socket;
```

**File:** `src/app/(dashboard)/dashboard/chat/page.tsx`

```typescript
import socket from '@/lib/socket-client';

useEffect(() => {
  socket.on('message', (data) => {
    setMessages(prev => [...prev, data]);
  });
}, []);

const sendMessage = (text) => {
  socket.emit('send_message', {
    conversation_id: conversationId,
    text: text,
  });
};
```

### Django Endpoints (Already Exist!)
- `GET /api/tasks/` - List tasks ✅
- `POST /api/tasks/` - Create task ✅
- `GET /api/tasks/{task_id}/` - Task detail ✅
- `PATCH /api/tasks/{task_id}/` - Update task ✅
- Django Channels WebSocket for chat ✅

### Deliverables
- [ ] Tasks list from API
- [ ] Task creation form
- [ ] Task status updates
- [ ] WebSocket connection
- [ ] Real-time messaging
- [ ] Conversation list
- [ ] Message history

### Success Criteria
✅ Tasks sync with database  
✅ Real-time chat works  
✅ Messages persist  
✅ Conversations load  

---

## 🎯 PHASE 8: FLOW GENERATOR INTEGRATION
**Timeline:** Week 9 (Days 57-63)  
**Priority:** MEDIUM - AI Workflow Builder

### Overview
A Tersa-like visual workflow builder for AI content generation. The frontend is already implemented with React Flow, but needs Django backend integration.

### What's Already Built (Frontend)
- ✅ Visual node-based canvas with React Flow
- ✅ 5 node types: Text, Image, Audio, Video, Code
- ✅ Node connections and workflow building
- ✅ Drag & drop interface
- ✅ Auto-save functionality (frontend only)
- ✅ Keyboard shortcuts
- ✅ Node operations (duplicate, delete, focus)

### Tasks

#### 8.1 Create Django Models
**File:** `website/models.py`

```python
from django.db import models
from django.contrib.auth.models import User

class FlowConfiguration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, default="Untitled Flow")
    nodes = models.JSONField(default=list)
    edges = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class FlowExecution(models.Model):
    flow = models.ForeignKey(FlowConfiguration, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 8.2 Create Django API Endpoints
**File:** `website/flow_api_views.py`

See `DJANGO_BACKEND_INTEGRATION.md` for complete endpoint implementations:
- `POST /api/flow/save` - Save workflow
- `GET /api/flow/load/:id` - Load workflow
- `GET /api/flow/list` - List user's workflows
- `POST /api/flow/generate/text` - Generate text with AI
- `POST /api/flow/generate/image` - Generate image with AI
- `POST /api/flow/generate/audio` - Text to speech
- `POST /api/flow/generate/video` - Generate video
- `POST /api/flow/execute/code` - Execute code safely

#### 8.3 Connect Frontend to Backend
**File:** `src/components/flow/canvas.tsx`

Update save function to use Django API:

```typescript
const save = useDebouncedCallback(async () => {
  try {
    setSaveState((prev) => ({ ...prev, isSaving: true }));
    
    await apiClient.post('/api/flow/save', {
      name: flowName,
      nodes,
      edges,
    });
    
    setSaveState((prev) => ({ ...prev, lastSaved: new Date() }));
  } catch (error) {
    console.error("Error saving flow:", error);
  } finally {
    setSaveState((prev) => ({ ...prev, isSaving: false }));
  }
}, 1000);
```

#### 8.4 Connect Node Generators
**Files:** 
- `src/components/flow/nodes/text-node.tsx`
- `src/components/flow/nodes/image-node.tsx`
- `src/components/flow/nodes/audio-node.tsx`
- `src/components/flow/nodes/video-node.tsx`
- `src/components/flow/nodes/code-node.tsx`

Example for Text Node:

```typescript
const handleGenerate = async () => {
  setLoading(true);
  try {
    const res = await apiClient.post('/api/flow/generate/text', {
      instructions: instructions,
    });
    setText(res.data.text);
  } catch (error) {
    console.error("Error generating text:", error);
  } finally {
    setLoading(false);
  }
};
```

#### 8.5 Add Flow List Page
**File:** `src/app/(dashboard)/dashboard/flows/page.tsx`

Create a page to list and manage saved workflows:

```typescript
const fetchFlows = async () => {
  const res = await apiClient.get('/api/flow/list');
  setFlows(res.data);
};

const loadFlow = async (flowId) => {
  router.push(`/flow-generator?id=${flowId}`);
};
```

### Django Endpoints (Need Creation!)
- `POST /api/flow/save` - Save workflow ❌
- `GET /api/flow/load/:id` - Load workflow ❌
- `GET /api/flow/list` - List workflows ❌
- `DELETE /api/flow/:id` - Delete workflow ❌
- `POST /api/flow/generate/text` - Text generation ❌
- `POST /api/flow/generate/image` - Image generation ❌
- `POST /api/flow/generate/audio` - Audio generation ❌
- `POST /api/flow/generate/video` - Video generation ❌
- `POST /api/flow/execute/code` - Code execution ❌

### AI Service Integration
You'll need to integrate:
- **Text Generation**: OpenAI GPT-4, Claude, or similar
- **Image Generation**: DALL-E, Stable Diffusion, Midjourney API
- **Audio Generation**: ElevenLabs, OpenAI TTS
- **Video Generation**: Runway ML, Luma AI, or similar

### Deliverables
- [ ] Django models for flows
- [ ] Flow CRUD API endpoints
- [ ] AI generation endpoints
- [ ] Frontend API integration
- [ ] Loading states for generations
- [ ] Error handling
- [ ] Flow list/management page
- [ ] Flow naming and organization

### Success Criteria
✅ Flows save to Django database  
✅ Flows load from database  
✅ Text generation works with AI  
✅ Image generation works  
✅ Audio generation works  
✅ Video generation works  
✅ Code execution is safe and functional  
✅ Users can manage saved flows  

### Documentation
See these files for complete implementation details:
- `FLOW_GENERATOR_README.md` - Feature documentation
- `DJANGO_BACKEND_INTEGRATION.md` - Complete API implementation guide

---

## 🎯 PHASE 9: REFERRAL SYSTEM
**Timeline:** Week 10 (Days 64-70)  
**Priority:** LOW - Growth feature

### Tasks

#### 8.1 Create Referral Page
**File:** `src/app/(dashboard)/dashboard/referral/page.tsx`

```typescript
const fetchReferralData = async () => {
  const res = await apiClient.get('/api/referral/dashboard/');
  setReferralData(res.data);
};
```

#### 8.2 Leaderboard
```typescript
const fetchLeaderboard = async () => {
  const res = await apiClient.get('/api/referral/leaderboard/');
  setLeaderboard(res.data);
};
```

### Django Endpoints (Already Exist!)
- `GET /api/referral/dashboard/` - Referral stats ✅
- `GET /api/referral/code/` - Get referral code ✅
- `GET /api/referral/leaderboard/` - Leaderboard ✅
- `GET /api/referral/badges/` - User badges ✅
- `POST /api/referral/track-click/` - Track clicks ✅

### Deliverables
- [ ] Referral dashboard page
- [ ] Referral code display
- [ ] Stats display
- [ ] Leaderboard
- [ ] Badge system
- [ ] Activity tracking

### Success Criteria
✅ Referral stats display  
✅ Leaderboard works  
✅ Clicks track properly  

---

## 📋 IMPLEMENTATION CHECKLIST

### Week 1: Foundation
- [ ] Install dependencies (next-auth, axios)
- [ ] Create `src/lib/api-client.ts`
- [ ] Setup Next-Auth in `src/app/api/auth/[...nextauth]/route.ts`
- [ ] Add `.env.local` with API URL
- [ ] Test login with Django credentials
- [ ] Update profile settings page with API
- [ ] Create protected route middleware

### Week 2: Brands
- [ ] Create `src/contexts/brand-context.tsx`
- [ ] Fetch brands from API
- [ ] Add brand selector to sidebar
- [ ] Connect brands page to API
- [ ] Test brand switching

### Week 3-4: Twitter
- [ ] Connect Twitter config page
- [ ] Fetch tweets in queue page
- [ ] Add create tweet form
- [ ] Implement post now button
- [ ] Add AI content generation
- [ ] Add AI image generation
- [ ] Connect analytics page
- [ ] Test full Twitter flow

### Week 5: Instagram
- [ ] Implement OAuth flow
- [ ] Connect post queue
- [ ] Add video generation
- [ ] Test posting flow

### Week 6: Analytics
- [ ] Install Chart.js
- [ ] Connect analytics dashboard
- [ ] Replace all mock data
- [ ] Add date filtering

### Week 7: CRM
- [ ] Create CRM API endpoints (if needed)
- [ ] Connect contacts page
- [ ] Connect companies page
- [ ] Connect deals page

### Week 8: Tasks & Chat
- [ ] Connect tasks API
- [ ] Install socket.io-client
- [ ] Implement WebSocket chat
- [ ] Test real-time messaging

### Week 9: Flow Generator
- [ ] Create Django models (FlowConfiguration, FlowExecution)
- [ ] Create flow API endpoints
- [ ] Integrate AI services (OpenAI, etc.)
- [ ] Connect frontend save/load
- [ ] Connect node generators to APIs
- [ ] Add loading states
- [ ] Create flow list page
- [ ] Test full workflow execution

### Week 10: Referral
- [ ] Create referral page
- [ ] Connect referral APIs
- [ ] Display leaderboard

---

## 🚀 GETTING STARTED

### Step 1: Start Django Backend
```bash
cd d:\Gemnar-com\gemnar-website
python manage.py runserver
```

### Step 2: Start Next.js Frontend
```bash
cd d:\Gemnar-com\next-saas-lp-main
npm run dev
```

### Step 3: Test Backend Access
```bash
curl http://localhost:8000/api/users/profile/
```

### Step 4: Begin with Authentication
Follow Phase 1 tasks in exact order.

---

## 📚 TECHNICAL RESOURCES

### Django API Documentation
- Base URL: `http://localhost:8000`
- Authentication: JWT tokens
- API file: `d:\Gemnar-com\gemnar-website\website\api_views.py` (7,715 lines)
- URL patterns: `d:\Gemnar-com\gemnar-website\website\urls.py`

### Next.js Frontend
- Base path: `d:\Gemnar-com\next-saas-lp-main`
- Dashboard: `src/app/(dashboard)/dashboard/`
- Components: `src/components/`
- 23+ pages already created

### Key Dependencies
- **Backend:** Django, Django REST Framework, Django Channels, Celery
- **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS
- **Auth:** NextAuth.js, JWT
- **Real-time:** Django Channels, Socket.io
- **Charts:** Chart.js, react-chartjs-2

---

## ⚠️ IMPORTANT NOTES

1. **Start with Auth** - Everything depends on it
2. **Test Each Phase** - Don't move forward until current phase works
3. **Use Real Data** - Replace all mock data progressively
4. **Django APIs Exist** - Most endpoints are already built
5. **WebSocket for Chat** - Django Channels already configured
6. **Brand Context** - Store selected brand globally

---

## 🎯 SUCCESS METRICS

### Phase 1 Success
✅ Login works with Django credentials  
✅ JWT stored and sent with requests  
✅ Profile updates save to database  

### Phase 3 Success
✅ Tweets post to Twitter  
✅ AI generates content  
✅ Images generate correctly  

### Final Success
✅ All 23 pages connected to backend  
✅ No mock data remaining  
✅ Real-time features functional  
✅ Users can fully operate platform  

---

## 📞 SUPPORT

If you encounter issues:
1. Check Django server is running
2. Verify API URL in `.env.local`
3. Check browser console for errors
4. Verify JWT token in localStorage
5. Test endpoints with curl/Postman

---

**START DATE:** November 18, 2025  
**TARGET COMPLETION:** January 27, 2026 (Extended by 1 week for Flow Generator)  
**CURRENT PHASE:** Phase 1 - Authentication (Not Started)  
**SPECIAL FEATURE:** Flow Generator (Tersa-like workflow builder) - Frontend Complete ✅

---

## 🔄 PROGRESS TRACKING

Update this section as you complete each phase:

- [ ] Phase 1: Authentication (Week 1)
- [ ] Phase 2: Brands (Week 2)
- [ ] Phase 3: Twitter (Weeks 3-4)
- [ ] Phase 4: Instagram (Week 5)
- [ ] Phase 5: Analytics (Week 6)
- [ ] Phase 6: CRM (Week 7)
- [ ] Phase 7: Tasks & Chat (Week 8)
- [ ] Phase 8: Flow Generator (Week 9)
- [ ] Phase 9: Referral (Week 10)

**Last Updated:** November 18, 2025  
**Current Task:** Flow Generator frontend completed ✅ - Next: Authentication system setup
