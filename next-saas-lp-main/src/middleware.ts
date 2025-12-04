import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const DJANGO_BACKEND = process.env.NEXT_PUBLIC_DJANGO_URL || 'http://localhost:8000';
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/',
  '/feed',
  '/login',
  '/signup',
  '/signup/brand',
  '/signup/creator',
  '/forgot-password',
  '/terms',
  '/privacy',
  '/flow-generator', // Allow flow generator for now
  '/dashboard', // Allow dashboard
  '/tasks', // Allow tasks
];

// Check if route is public or matches public pattern
function isPublicRoute(pathname: string): boolean {
  // Exact match
  if (PUBLIC_ROUTES.includes(pathname)) {
    return true;
  }
  
  // Allow public workspace viewing by slug (pattern: /flow-generator/[slug])
  // Slugs are 12 characters (UUID prefix)
  if (/^\/flow-generator\/[a-f0-9-]{8,}/.test(pathname)) {
    return true;
  }
  
  // Allow public user profiles (pattern: /users/[id])
  if (/^\/users\/\d+/.test(pathname)) {
    return true;
  }
  
  // Allow static files, API routes, and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.startsWith('/images') ||
    pathname.includes('.')
  ) {
    return true;
  }
  
  return false;
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  // In development, be more lenient with auth
  // Check for auth token in cookies (token-based auth)
  if (IS_DEVELOPMENT) {
    const cookieHeader = request.headers.get('cookie') || '';
    
    // Check for sessionid (session-based) OR auth_token presence
    // Note: We can't read localStorage in middleware, but if a user is logged in,
    // they should have been to the site before and may have session cookies
    const hasSessionCookie = cookieHeader.includes('sessionid=');
    
    // For token-based auth, we need to be more permissive in middleware
    // since we can't access localStorage here. The client-side layout will handle auth.
    if (hasSessionCookie) {
      console.log('[Middleware] Session cookie found, allowing access to:', pathname);
      return NextResponse.next();
    }
    
    // In development, allow access to protected routes - let client-side auth handle it
    // This is necessary because token auth uses localStorage, not cookies
    console.log('[Middleware] No session cookie, but allowing access in development. Client-side will handle auth check.');
    return NextResponse.next();
  }

  // Production: Check authentication with Django backend
  const cookieHeader = request.headers.get('cookie') || '';
  
  try {
    console.log('[Middleware] Checking auth for:', pathname);
    
    const response = await fetch(`${DJANGO_BACKEND}/api/auth/me/`, {
      method: 'GET',
      headers: {
        'cookie': cookieHeader,
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    console.log('[Middleware] Auth response status:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('[Middleware] User authenticated:', data.email);
      return NextResponse.next();
    }
  } catch (error) {
    console.error('[Middleware] Auth check failed:', error);
  }

  // User is not authenticated, redirect to login
  console.log('[Middleware] Redirecting to login from:', pathname);
  const loginUrl = new URL('/login', request.url);
  
  // Only set redirect if it's a valid protected route (not auth-related)
  if (pathname !== '/login' && pathname !== '/signup' && !pathname.startsWith('/signup/')) {
    loginUrl.searchParams.set('redirect', pathname);
  }
  
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
