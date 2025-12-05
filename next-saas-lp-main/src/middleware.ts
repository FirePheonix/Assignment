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

  // For token-based auth (localStorage), we cannot check auth in middleware
  // because middleware runs on the server and cannot access localStorage.
  // 
  // Let all protected routes through and rely on client-side auth checks.
  // The layout components will redirect unauthenticated users to login.
  console.log('[Middleware] Allowing access to:', pathname, '(client-side auth will handle)');
  return NextResponse.next();
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
