// Django backend API connection
const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password1: string;
  password2: string;
  username?: string;
}

// Token-based authentication - no CSRF needed

// Get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

// Set auth token in localStorage
function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
}

// Remove auth token from localStorage
function removeAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth_token');
}

// Get current user using token authentication
export async function getCurrentUser(): Promise<User | null> {
  try {
    const token = getAuthToken();
    if (!token) return null;
    
    const response = await fetch(`${DJANGO_BACKEND}/api/auth/me/`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
      },
    });
    
    if (!response.ok) {
      // Token is invalid, remove it
      if (response.status === 401 || response.status === 403) {
        removeAuthToken();
      }
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching current user:', error);
    return null;
  }
}

// Login user with token authentication
export async function login(credentials: LoginCredentials): Promise<{ user: User | null; error: string | null }> {
  try {
    const response = await fetch(`${DJANGO_BACKEND}/api/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return { 
        user: null, 
        error: errorData.non_field_errors?.[0] || errorData.detail || 'Login failed' 
      };
    }
    
    const data = await response.json();
    
    // Save token to localStorage
    if (data.token) {
      setAuthToken(data.token);
    }
    
    // Return user from login response
    const user = data.user || null;
    return { user, error: null };
  } catch (error) {
    console.error('Login error:', error);
    return { user: null, error: 'An unexpected error occurred' };
  }
}

// Register user
export async function register(data: RegisterData): Promise<{ user: User | null; error: string | null }> {
  try {
    const response = await fetch(`${DJANGO_BACKEND}/api/auth/registration/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      const errorMessage = 
        errorData.email?.[0] || 
        errorData.username?.[0] ||
        errorData.password1?.[0] || 
        errorData.non_field_errors?.[0] ||
        errorData.detail || 
        'Registration failed';
      return { user: null, error: errorMessage };
    }
    
    const user = await getCurrentUser();
    return { user, error: null };
  } catch (error) {
    console.error('Registration error:', error);
    return { user: null, error: 'An unexpected error occurred' };
  }
}

// Logout user
export async function logout(): Promise<boolean> {
  try {
    const token = getAuthToken();
    
    if (token) {
      await fetch(`${DJANGO_BACKEND}/api/auth/logout/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`,
        },
      });
    }
    
    // Always remove token from localStorage
    removeAuthToken();
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    removeAuthToken(); // Remove token even if logout request fails
    return false;
  }
}

// Check if authenticated
export async function isAuthenticated(): Promise<boolean> {
  const user = await getCurrentUser();
  return user !== null;
}

// Legacy compatibility
export const currentUser = getCurrentUser;
export const currentUserProfile = getCurrentUser;
