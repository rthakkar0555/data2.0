import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Get token and user from cookies or headers
  const token = request.cookies.get('access_token')?.value
  const userStr = request.cookies.get('user')?.value
  
  let user = null
  if (userStr) {
    try {
      user = JSON.parse(userStr)
    } catch {
      user = null
    }
  }

  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/']
  
  // Admin-only routes
  const adminRoutes = ['/admin']
  
  // User routes (require authentication but not admin role)
  const userRoutes = ['/user']

  // If accessing a public route, allow
  if (publicRoutes.includes(pathname)) {
    return NextResponse.next()
  }

  // If no token, redirect to login
  if (!token || !user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Check admin routes
  if (adminRoutes.some(route => pathname.startsWith(route))) {
    if (user.role !== 'admin') {
      return NextResponse.redirect(new URL('/user', request.url))
    }
  }

  // Check user routes
  if (userRoutes.some(route => pathname.startsWith(route))) {
    if (user.role !== 'user' && user.role !== 'admin') {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
