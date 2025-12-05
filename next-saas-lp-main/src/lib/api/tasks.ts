/**
 * Tasks API Service
 * Connects to Django backend for task management
 */

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

// Task Types
export type TaskCategory = 
  | "POST" 
  | "REEL" 
  | "STORY" 
  | "VIDEO" 
  | "BLOG" 
  | "REVIEW" 
  | "UNBOXING" 
  | "TUTORIAL" 
  | "COLLABORATION" 
  | "UGC" 
  | "TESTIMONIAL" 
  | "LIVESTREAM";

export type TaskGenre = 
  | "BEAUTY" 
  | "FASHION" 
  | "FOOD" 
  | "FITNESS" 
  | "TECH" 
  | "TRAVEL" 
  | "HOME" 
  | "AUTOMOTIVE" 
  | "GAMING" 
  | "FINANCE" 
  | "EDUCATION" 
  | "ENTERTAINMENT" 
  | "SPORTS" 
  | "PETS" 
  | "PARENTING" 
  | "SUSTAINABLE" 
  | "LUXURY" 
  | "B2B" 
  | "OTHER";

export type IncentiveType = 
  | "NONE" 
  | "BARTER" 
  | "PAY" 
  | "COMMISSION" 
  | "EXPOSURE" 
  | "GIFT_CARD" 
  | "EXPERIENCE";

export type ApplicationStatus = "PENDING" | "ACCEPTED" | "REJECTED" | "COMPLETED";

// Labels for UI
export const CATEGORY_LABELS: Record<TaskCategory, string> = {
  POST: "Instagram Post",
  REEL: "Instagram Reel",
  STORY: "Instagram Story",
  VIDEO: "Video Content",
  BLOG: "Blog Article",
  REVIEW: "Product Review",
  UNBOXING: "Unboxing Video",
  TUTORIAL: "Tutorial",
  COLLABORATION: "Brand Collaboration",
  UGC: "User Generated Content",
  TESTIMONIAL: "Testimonial",
  LIVESTREAM: "Live Stream",
};

export const GENRE_LABELS: Record<TaskGenre, string> = {
  BEAUTY: "Beauty & Cosmetics",
  FASHION: "Fashion & Style",
  FOOD: "Food & Beverage",
  FITNESS: "Fitness & Health",
  TECH: "Technology",
  TRAVEL: "Travel & Lifestyle",
  HOME: "Home & Decor",
  AUTOMOTIVE: "Automotive",
  GAMING: "Gaming",
  FINANCE: "Finance & Business",
  EDUCATION: "Education",
  ENTERTAINMENT: "Entertainment",
  SPORTS: "Sports & Recreation",
  PETS: "Pets & Animals",
  PARENTING: "Parenting & Family",
  SUSTAINABLE: "Sustainability & Eco-friendly",
  LUXURY: "Luxury Goods",
  B2B: "Business to Business",
  OTHER: "Other",
};

export const INCENTIVE_LABELS: Record<IncentiveType, string> = {
  NONE: "No Compensation",
  BARTER: "Product Exchange",
  PAY: "Monetary Payment",
  COMMISSION: "Commission Based",
  EXPOSURE: "Exposure & Credits",
  GIFT_CARD: "Gift Card",
  EXPERIENCE: "Experience/Event Access",
};

// API Response Types
export interface Task {
  id: number;
  title: string;
  description: string;
  category: TaskCategory;
  genre: TaskGenre;
  incentive_type: IncentiveType;
  barter_details?: string;
  pay_amount?: number;
  commission_percentage?: number;
  gift_card_amount?: number;
  experience_details?: string;
  deadline?: string;
  is_active: boolean;
  brand: number;
  brand_username: string;
  brand_email: string;
  application_count: number;
  accepted_applications_count: number;
  user_has_applied: boolean;
  created_at: string;
}

export interface TaskApplication {
  id: number;
  task: number;
  creator: number;
  creator_username: string;
  creator_email: string;
  task_title: string;
  task_category: TaskCategory;
  task_incentive_type: IncentiveType;
  status: ApplicationStatus;
  message: string;
  applied_at: string;
  updated_at: string;
  user?: {
    id: number;
    username: string;
    instagram_handle?: string;
    profile_picture?: string;
  };
}

export interface CreateTaskData {
  title: string;
  description: string;
  category: TaskCategory;
  genre: TaskGenre;
  incentive_type: IncentiveType;
  barter_details?: string;
  pay_amount?: number;
  commission_percentage?: number;
  gift_card_amount?: number;
  experience_details?: string;
  deadline?: string;
}

export interface TasksResponse {
  tasks: Task[];
  count: number;
  page: number;
  page_size: number;
}

export interface ApplicationsResponse {
  applications: TaskApplication[];
}

// Helper function to get auth token
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/**
 * Get all tasks with optional filters
 */
export async function getTasks(params?: {
  category?: TaskCategory;
  genre?: TaskGenre;
  incentive_type?: IncentiveType;
  page?: number;
  page_size?: number;
}): Promise<{ data: TasksResponse | null; error: string | null }> {
  try {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.append('category', params.category);
    if (params?.genre) queryParams.append('genre', params.genre);
    if (params?.incentive_type) queryParams.append('incentive_type', params.incentive_type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const url = `${DJANGO_BACKEND}/api/tasks/?${queryParams.toString()}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch tasks' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching tasks:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Get a specific task by ID
 */
export async function getTask(taskId: number): Promise<{ data: Task | null; error: string | null }> {
  try {
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/${taskId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch task' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching task:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Create a new task
 */
export async function createTask(taskData: CreateTaskData): Promise<{ data: Task | null; error: string | null }> {
  try {
    const authToken = getAuthToken();
    
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Token ${authToken}` }),
      },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      const error = await response.json();
      return { 
        data: null, 
        error: error.detail || error.non_field_errors?.[0] || 'Failed to create task' 
      };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error creating task:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Update a task
 */
export async function updateTask(
  taskId: number, 
  taskData: Partial<CreateTaskData>
): Promise<{ data: Task | null; error: string | null }> {
  try {
    const authToken = getAuthToken();
    
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/${taskId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Token ${authToken}` }),
      },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to update task' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error updating task:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Delete a task
 */
export async function deleteTask(taskId: number): Promise<{ success: boolean; error: string | null }> {
  try {
    const authToken = getAuthToken();
    
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/${taskId}/`, {
      method: 'DELETE',
      headers: {
        ...(authToken && { 'Authorization': `Token ${authToken}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { success: false, error: error.detail || 'Failed to delete task' };
    }

    return { success: true, error: null };
  } catch (error) {
    console.error('Error deleting task:', error);
    return { 
      success: false, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Get tasks created by the current user
 */
export async function getMyTasks(statusFilter?: 'active' | 'inactive'): Promise<{ data: TasksResponse | null; error: string | null }> {
  try {
    const queryParams = new URLSearchParams();
    if (statusFilter) queryParams.append('status', statusFilter);

    const url = `${DJANGO_BACKEND}/api/my-tasks/?${queryParams.toString()}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch your tasks' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching my tasks:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Apply to a task
 */
export async function applyToTask(
  taskId: number, 
  message: string
): Promise<{ data: TaskApplication | null; error: string | null }> {
  try {
    const authToken = getAuthToken();
    
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/${taskId}/applications/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Token ${authToken}` }),
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const error = await response.json();
      return { 
        data: null, 
        error: error.detail || error.non_field_errors?.[0] || error.message?.[0] || 'Failed to apply to task' 
      };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error applying to task:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Get applications for a specific task (task owner only)
 */
export async function getTaskApplications(taskId: number): Promise<{ data: ApplicationsResponse | null; error: string | null }> {
  try {
    const response = await fetch(`${DJANGO_BACKEND}/api/tasks/${taskId}/applications/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch applications' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching task applications:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Get applications submitted by the current user
 */
export async function getMyApplications(statusFilter?: ApplicationStatus): Promise<{ data: ApplicationsResponse | null; error: string | null }> {
  try {
    const queryParams = new URLSearchParams();
    if (statusFilter) queryParams.append('status', statusFilter);

    const url = `${DJANGO_BACKEND}/api/my-applications/?${queryParams.toString()}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch your applications' };
    }
    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching my applications:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Update application status (task owner only)
 */
export async function updateApplicationStatus(
  applicationId: number, 
  status: ApplicationStatus
): Promise<{ data: TaskApplication | null; error: string | null }> {
  try {
    const authToken = getAuthToken();
    
    const response = await fetch(`${DJANGO_BACKEND}/api/applications/${applicationId}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Token ${authToken}` }),
      },
      body: JSON.stringify({ status }),
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to update application' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error updating application:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}

/**
 * Get a specific application
 */
export async function getApplication(applicationId: number): Promise<{ data: TaskApplication | null; error: string | null }> {
  try {
    const response = await fetch(`${DJANGO_BACKEND}/api/applications/${applicationId}/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return { data: null, error: error.detail || 'Failed to fetch application' };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    console.error('Error fetching application:', error);
    return { 
      data: null, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    };
  }
}
