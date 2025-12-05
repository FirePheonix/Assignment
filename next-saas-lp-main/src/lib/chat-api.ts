// Chat API for Django backend
const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

// Get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export interface Conversation {
  id: number;
  brand?: {
    id: number;
    name: string;
    logo?: string;
  };
  participant1: {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
    profile_picture?: string;
  };
  participant2: {
    id: number;
    username: string;
    email: string;
    first_name?: string;
    last_name?: string;
    profile_picture?: string;
  };
  created_at: string;
  updated_at: string;
  last_message?: {
    content: string;
    timestamp: string;
    sender_id: number;
  };
  unread_count?: number;
}

export interface Message {
  id: number;
  sender: {
    id: number;
    username: string;
    first_name?: string;
    last_name?: string;
    profile_picture?: string;
  };
  content: string;
  timestamp: string;
  is_read: boolean;
  image?: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationStats {
  user_type: 'creator' | 'brand';
  total_chats: number;
  unread_messages: number;
  creator_chats: number;
  brand_chats: number;
}

class ChatAPI {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const token = getAuthToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${DJANGO_BACKEND}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Token ${token}`,
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || error.error || 'Request failed');
    }

    return response.json();
  }

  async getConversations(type?: 'all' | 'creators' | 'brands'): Promise<{
    user_type: string;
    chats: Conversation[];
    creator_chats: number;
    brand_chats: number;
    total_chats: number;
  }> {
    const params = new URLSearchParams();
    if (type && type !== 'all') {
      params.append('type', type);
    }
    
    return this.request(
      `/chat/api/conversations/${params.toString() ? `?${params.toString()}` : ''}`
    );
  }

  async getConversation(conversationId: number): Promise<ConversationDetail> {
    return this.request(`/chat/api/conversations/${conversationId}/`);
  }

  async getMessages(conversationId: number): Promise<Message[]> {
    return this.request(`/chat/api/conversations/${conversationId}/messages/`);
  }

  async sendMessage(
    conversationId: number,
    content: string,
    image?: File
  ): Promise<Message> {
    const token = getAuthToken();
    if (!token) {
      throw new Error('Not authenticated');
    }

    const formData = new FormData();
    formData.append('content', content);
    if (image) {
      formData.append('image', image);
    }

    const response = await fetch(
      `${DJANGO_BACKEND}/chat/api/conversations/${conversationId}/messages/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to send message' }));
      throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
  }

  async startConversationWithUser(userId: number): Promise<{
    conversation: ConversationDetail;
    created: boolean;
  }> {
    return this.request(`/chat/api/start-conversation/user/${userId}/`, {
      method: 'POST',
    });
  }

  async startConversationWithBrand(brandId: number): Promise<{
    conversation: ConversationDetail;
    created: boolean;
  }> {
    return this.request(`/chat/api/start-conversation/brand/${brandId}/`, {
      method: 'POST',
    });
  }

  async getConversationStats(): Promise<ConversationStats> {
    return this.request('/chat/api/conversation-stats/');
  }

  // WebSocket connection helper
  createWebSocket(conversationId: number): WebSocket | null {
    const token = getAuthToken();
    if (!token || typeof window === 'undefined') {
      return null;
    }

    // Use ws:// for localhost, wss:// for production
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = DJANGO_BACKEND.replace('http://', '').replace('https://', '');
    
    // Pass token as query parameter since WebSocket doesn't support custom headers
    const ws = new WebSocket(
      `${wsProtocol}//${wsHost}/ws/conversation/${conversationId}/?token=${token}`
    );

    return ws;
  }
}

export const chatApi = new ChatAPI();
