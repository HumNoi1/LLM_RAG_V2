import { NextRequest, NextResponse } from 'next/server';

// Routes that don't require authentication
const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/api',
  '/_next',
  '/public',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes to pass through
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // For protected routes, middleware just allows them through
  // The actual auth check happens in ProtectedRoute component on client-side
  // This middleware is mainly for security headers and logging
  
  // Optional: Log protected route access
  if (process.env.NODE_ENV === 'development') {
    console.debug(`[Middleware] Accessing protected route: ${pathname}`);
  }

  return NextResponse.next();
}

// Configure which routes to protect with middleware
export const config = {
  matcher: [
    // Protect all routes except public ones
    '/((?!_next/static|_next/image|favicon.ico|api/).*)',
  ],
};
