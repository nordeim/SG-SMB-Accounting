/**
 * LEDGERSG SECURITY MIDDLEWARE
 *
 * Purpose: Apply security headers to all responses
 * Implements: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, etc.
 *
 * Note: This middleware runs in development but Next.js static export
 * only includes middleware in server mode. For static export, headers
 * should be applied at the reverse proxy (nginx, Cloudflare, etc.)
 */

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Content Security Policy directives
const cspDirectives = {
  "default-src": ["'self'"],
  "script-src": [
    "'self'",
    "'unsafe-eval'", // Required for Next.js 16 + React 19
    "'unsafe-inline'", // Required for Next.js inline scripts
    "https://vercel.live", // Vercel Live feedback
  ],
  "style-src": [
    "'self'",
    "'unsafe-inline'", // Required for Tailwind CSS v4
    "https://fonts.googleapis.com",
  ],
  "font-src": ["'self'", "https://fonts.gstatic.com"],
  "img-src": ["'self'", "data:", "blob:", "https:"],
  "connect-src": [
    "'self'",
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    "https://api.peppol.sg",
    "https://api.iras.gov.sg",
    "https://vitals.vercel-insights.com", // Vercel Analytics
  ],
  "frame-ancestors": ["'none'"], // Prevent clickjacking
  "base-uri": ["'self'"],
  "form-action": ["'self'"],
  "upgrade-insecure-requests": [], // Upgrade HTTP to HTTPS
};

// Build CSP string from directives
function buildCSP(): string {
  return Object.entries(cspDirectives)
    .map(([key, values]) => {
      if (values.length === 0) return key;
      return `${key} ${values.join(" ")}`;
    })
    .join("; ");
}

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Get nonce for CSP (for scripts that need it)
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");

  // Build CSP with nonce support
  const csp = buildCSP()
    .replace(/{{nonce}}/g, nonce)
    .replace("'unsafe-inline'", `'nonce-${nonce}' 'unsafe-inline'`);

  // Security Headers
  const securityHeaders = {
    // Content Security Policy
    "Content-Security-Policy": csp,

    // Strict Transport Security (HSTS)
    "Strict-Transport-Security":
      "max-age=31536000; includeSubDomains; preload",

    // Prevent MIME type sniffing
    "X-Content-Type-Options": "nosniff",

    // Prevent clickjacking
    "X-Frame-Options": "DENY",

    // XSS Protection (legacy, CSP is primary)
    "X-XSS-Protection": "1; mode=block",

    // Referrer Policy
    "Referrer-Policy": "strict-origin-when-cross-origin",

    // Permissions Policy (formerly Feature Policy)
    "Permissions-Policy":
      "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=()",

    // Cross-Origin policies
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
  };

  // Apply all security headers
  Object.entries(securityHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  // Add nonce to response headers for use in meta tags
  response.headers.set("x-nonce", nonce);

  return response;
}

// Matcher configuration
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
