import type { NextConfig } from "next";

/**
 * LEDGERSG NEXT.JS CONFIGURATION
 *
 * Features:
 * - Dual mode: Static export (default) OR Server mode (with backend)
 * - Security headers (CSP, HSTS, etc.)
 * - CORS configuration for backend API
 * - Image optimization (disabled for static, enabled for server)
 *
 * Mode Selection:
 * - Static export: `npm run build` → `npm run serve` (default)
 * - Server mode: `npm run build:server` → `npm run start` (backend integration)
 */

// Determine output mode from environment variable
const outputMode = process.env.NEXT_OUTPUT_MODE || "export";
const isStaticExport = outputMode === "export";
const isServerMode = outputMode === "standalone" || !isStaticExport;

// Backend API URL for CSP and rewrites
const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // Output mode: 'export' for static, 'standalone' for server
  output: isServerMode ? "standalone" : "export",
  distDir: isServerMode ? ".next" : "dist",

  // Image optimization: disabled for static, enabled for server
  images: {
    unoptimized: isStaticExport,
  },

  // Enable React Strict Mode
  reactStrictMode: true,

  // Configure trailing slashes for Django backend compatibility
  trailingSlash: true,

  // Security headers - only applied in server mode
  async headers() {
    // Security headers don't work with static export
    if (isStaticExport) {
      return [];
    }

    return [
      {
        source: "/:path*",
        headers: [
          // Content Security Policy
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob:",
              // Allow connections to backend API and external services
              `connect-src 'self' ${apiUrl} http://localhost:8000 https://api.peppol.sg https://api.iras.gov.sg`,
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
          // HTTP Strict Transport Security
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          // X-Frame-Options
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          // X-Content-Type-Options
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          // Referrer-Policy
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          // Permissions-Policy
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          // X-XSS-Protection (legacy, CSP replaces this)
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
        ],
      },
    ];
  },

  // Rewrites for API proxy (development only)
  async rewrites() {
    // Rewrites don't work with static export
    if (isStaticExport) {
      return [];
    }

    // In development, proxy API calls to backend
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: `${apiUrl}/api/:path*`,
        },
      ];
    }

    return [];
  },

  // CORS configuration for API routes
  async redirects() {
    return [];
  },
};

export default nextConfig;
