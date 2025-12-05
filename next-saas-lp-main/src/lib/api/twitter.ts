/**
 * Client-side API service for Twitter operations
 */

export interface TwitterConfig {
  id: number;
  api_key: string | null;
  api_secret: string | null;
  access_token: string | null;
  access_token_secret: string | null;
  bearer_token: string | null;
  username?: string;
  is_active: boolean;
}

export interface QueuedTweet {
  id: number;
  content: string;
  status: 'draft' | 'queued' | 'scheduled' | 'posted' | 'failed';
  scheduled_at: string | null;
  posted_at: string | null;
  media_urls: string[];
  twitter_id: string | null;
  twitter_url: string | null;
  error_message: string | null;
  brand: {
    id: number;
    name: string;
    slug: string;
  };
  created_at: string;
  updated_at: string;
}

export interface TwitterQueue {
  tweets: QueuedTweet[];
  stats: {
    total_queued: number;
    total_scheduled: number;
    total_drafts: number;
    total_posted: number;
  };
}

export interface CreateTweetData {
  content: string;
  scheduled_at?: string | null;
  media_urls?: string[];
}

export interface TwitterTestResult {
  success: boolean;
  error?: string;
  error_type?: string;
  username?: string;
  tweet_id?: string;
  tweet_url?: string;
}

const API_URL = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://127.0.0.1:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

// Helper to make authenticated requests
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  
  // Don't set Content-Type for FormData (browser will set it with boundary)
  const isFormData = options.body instanceof FormData;
  
  const headers: HeadersInit = {
    ...(!isFormData && { 'Content-Type': 'application/json' }),
    ...(token && { 'Authorization': `Token ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
}

class TwitterAPI {
  async getConfig(brandId: number): Promise<TwitterConfig> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/config/`);

    if (!response.ok) {
      throw new Error('Failed to fetch Twitter configuration');
    }

    return response.json();
  }

  async saveConfig(brandId: number, data: Partial<TwitterConfig>): Promise<TwitterConfig> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/config/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to save Twitter configuration');
    }

    return response.json();
  }

  async testConnection(brandId: number): Promise<TwitterTestResult> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/test/`, {
      method: 'POST',
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Connection test failed',
      };
    }

    return data;
  }

  async sendTestTweet(brandId: number, content: string): Promise<TwitterTestResult> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/test-tweet/`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Tweet failed',
      };
    }

    return data;
  }

  async disconnect(brandId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/disconnect/`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to disconnect Twitter');
    }
  }

  async getQueue(brandId?: number): Promise<TwitterQueue> {
    const url = brandId 
      ? `${API_URL}/api/brands/${brandId}/twitter/queue/`
      : `${API_URL}/api/twitter/queue/`;
    
    const response = await fetchWithAuth(url);

    if (!response.ok) {
      throw new Error('Failed to fetch Twitter queue');
    }

    return response.json();
  }

  async createQueuedTweet(data: CreateTweetData & { brand_id: number }): Promise<QueuedTweet> {
    const response = await fetchWithAuth(`${API_URL}/api/twitter/queue/`, {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to create tweet');
    }

    return response.json();
  }

  async updateQueuedTweet(tweetId: number, data: Partial<CreateTweetData>): Promise<QueuedTweet> {
    const response = await fetchWithAuth(`${API_URL}/api/twitter/queue/${tweetId}/update/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update tweet');
    }

    return response.json();
  }

  async deleteQueuedTweet(tweetId: number): Promise<void> {
    const response = await fetchWithAuth(`${API_URL}/api/twitter/queue/${tweetId}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to delete tweet');
    }
  }

  async postTweetNow(tweetId: number): Promise<TwitterTestResult> {
    const response = await fetchWithAuth(`${API_URL}/api/twitter/queue/${tweetId}/post/`, {
      method: 'POST',
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || 'Failed to post tweet',
      };
    }

    return data;
  }

  async generateAITweets(brandId: number, params?: {
    prompt: string;
    count?: number;
    tone?: 'professional' | 'casual' | 'funny' | 'inspirational';
  }): Promise<{ success: boolean; count: number; tweets?: QueuedTweet[]; error?: string }> {
    const response = await fetchWithAuth(`${API_URL}/api/brands/${brandId}/twitter/generate/`, {
      method: 'POST',
      body: JSON.stringify(params || { prompt: 'General updates', count: 3 }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        count: 0,
        error: data.error || 'Failed to generate tweets',
      };
    }

    return data;
  }

  async uploadMedia(file: File): Promise<{ success: boolean; url?: string; error?: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetchWithAuth(`${API_URL}/api/twitter/upload-media/`, {
        method: 'POST',
        body: formData,
        headers: {}, // Let browser set Content-Type for FormData
      });

      const data = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: data.error || 'Failed to upload media',
        };
      }

      return {
        success: true,
        url: data.url,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to upload media',
      };
    }
  }

  async getAnalytics(brandId?: number): Promise<TwitterAnalytics> {
    const url = brandId 
      ? `${API_URL}/api/brands/${brandId}/twitter/analytics/`
      : `${API_URL}/api/twitter/analytics/`;
    
    const response = await fetchWithAuth(url);

    if (!response.ok) {
      throw new Error('Failed to fetch Twitter analytics');
    }

    return response.json();
  }
}

export interface TweetMetrics {
  likes: number;
  verified_likes: number;  // Actual count from liking_users API
  retweets: number;
  replies: number;
  quotes: number;
  engagement: number;
  engagement_rate: number;
}

export interface AnalyticsTweet {
  id: number | null;
  twitter_id: string;
  content: string;
  posted_at: string | null;
  twitter_url: string | null;
  brand_id: number;
  brand_name: string;
  metrics: TweetMetrics;
}

export interface BrandAnalytics {
  id: number;
  name: string;
  slug: string;
  username: string;
  followers: number;
  following: number;
  total_tweets: number;
  total_likes: number;
  total_retweets: number;
  total_replies: number;
  total_quotes: number;
  engagement_rate: number;
}

export interface TwitterAnalytics {
  success: boolean;
  total_tweets: number;
  total_followers: number;
  total_likes: number;
  total_retweets: number;
  total_replies: number;
  total_quotes: number;
  total_engagement: number;
  engagement_rate: number;
  tweets: AnalyticsTweet[];
  brands: BrandAnalytics[];
  top_performing: AnalyticsTweet[];
  message?: string;
}

export const twitterAPI = new TwitterAPI();