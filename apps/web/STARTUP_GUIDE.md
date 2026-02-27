# LedgerSG Frontend Startup Guide

**Version**: 1.0  
**Last Updated**: 2026-02-27

---

## Overview

The LedgerSG frontend supports **two modes** of operation:

1. **Development Mode** (`npm run dev`) - Full backend integration with hot reload
2. **Production Server Mode** (`npm run build:server` → `npm run start`) - Backend API integration
3. **Static Export Mode** (`npm run build` → `npm run serve`) - CDN deployment only

---

## Quick Start (Recommended for Development)

### Prerequisites
- Node.js 20+ installed
- Backend API running on `http://localhost:8000`
- Environment file configured (`.env.local`)

### 1. Start Backend
```bash
cd /home/project/Ledger-SG/apps/backend
source /opt/venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 2. Start Frontend (Development Mode)
```bash
cd /home/project/Ledger-SG/apps/web
npm run dev
```

Access the application at: **http://localhost:3000**

---

## Production Server Mode (Backend API Integration)

Use this mode for **production deployment with backend API integration**.

### Step 1: Build for Production
```bash
cd /home/project/Ledger-SG/apps/web

# Clean previous builds
npm run clean

# Build with server mode (enables backend API calls)
npm run build:server
```

### Step 2: Start Production Server
```bash
# Using default port (3000)
npm run start

# Using custom port
PORT=8080 npm run start

# Production mode with explicit settings
NODE_ENV=production PORT=3000 npm run start:prod
```

### What This Enables
✅ Full backend API integration  
✅ JWT authentication with HttpOnly cookies  
✅ React Query server state management  
✅ Dynamic data fetching  
✅ Server-side rendering (SSR)  
✅ API route proxying (in dev mode)  

---

## Static Export Mode (CDN Deployment)

Use this mode **only for static CDN deployment** without backend integration.

### Build & Serve
```bash
cd /home/project/Ledger-SG/apps/web

# Build static export
npm run build

# Serve static files
npm run serve
```

### ⚠️ Limitations of Static Export
❌ No backend API integration  
❌ No authentication (JWT)  
❌ No dynamic data fetching  
❌ No React Query server state  
❌ Login/logout non-functional  

---

## Environment Configuration

### Required Environment Variables (`.env.local`)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Output mode: "standalone" (server) or "export" (static)
NEXT_OUTPUT_MODE=standalone

# Feature flags
NEXT_PUBLIC_ENABLE_PEPPOL=true
NEXT_PUBLIC_ENABLE_GST_F5=true
NEXT_PUBLIC_ENABLE_BCRS=true
```

### Port Configuration

| Mode | Command | Port | Purpose |
|------|---------|------|---------|
| Development | `npm run dev` | 3000 (default) | Hot reload, backend API |
| Production Server | `npm run start` | 3000 (default) | Backend API integration |
| Custom Port | `PORT=8080 npm run start` | Custom | Flexible deployment |

---

## Available Scripts

### Development
```bash
npm run dev           # Start development server
npm run dev:clean     # Clean .next and start dev server
```

### Production (Server Mode with Backend)
```bash
npm run build:server  # Build for production with backend integration
npm run start         # Start production server
npm run start:prod    # Start with production settings
```

### Static Export (CDN Only)
```bash
npm run build         # Build static export
npm run build:static  # Same as above
npm run serve         # Serve static files (no backend)
```

### Testing
```bash
npm test              # Run unit tests
npm run test:coverage # Run tests with coverage
npm run test:e2e      # Run Playwright E2E tests
```

### Utilities
```bash
npm run clean         # Remove .next and dist
npm run clean:all     # Remove .next, dist, node_modules
npm run lint          # Run ESLint
npm run lint:fix      # Fix ESLint issues
```

---

## Architecture Overview

### Dual-Mode Configuration

The `next.config.ts` supports both modes via environment variable:

```typescript
const outputMode = process.env.NEXT_OUTPUT_MODE || "export";

const nextConfig: NextConfig = {
  output: isServerMode ? "standalone" : "export",
  distDir: isServerMode ? ".next" : "dist",
  // ...
};
```

### How Backend Integration Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (User)                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP / HTTPS
┌───────────────────────▼─────────────────────────────────────────┐
│              Next.js Server (Port 3000)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Middleware (CSP Headers, Security)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  React Components                                       │   │
│  │  ├─ React Query (TanStack)                              │   │
│  │  ├─ API Client (api-client.ts)                         │   │
│  │  └─ JWT Token Management                                │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────────┘
                        │ API Calls (fetch/XHR)
┌───────────────────────▼─────────────────────────────────────────┐
│              Django Backend (Port 8000)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  REST API (DRF)                                         │   │
│  │  ├─ JWT Authentication                                  │   │
│  │  ├─ Invoicing Endpoints                                 │   │
│  │  ├─ GST Calculation                                     │   │
│  │  └─ Database (PostgreSQL)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### API Client Flow

```typescript
// Frontend (React Query Hook)
const { data: invoices } = useInvoices(orgId);

// ↓ Calls api-client.ts
const response = await api.get(endpoints.invoices(orgId).list);

// ↓ Sends HTTP request
GET http://localhost:8000/api/v1/{orgId}/invoicing/documents/
Authorization: Bearer {accessToken}
Cookie: refresh_token={HttpOnlyCookie}

// ↓ Backend Response
{
  "data": [...],
  "count": 50,
  "next": "...",
  "previous": "..."
}
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm run start
```

### Backend Connection Failed
```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health/

# Check environment variable
echo $NEXT_PUBLIC_API_URL

# Should be: http://localhost:8000
```

### Build Errors
```bash
# Clean and rebuild
npm run clean
npm run build:server
```

### Module Not Found Errors
```bash
# Reinstall dependencies
npm run clean:all
npm install
npm run build:server
```

### Static Export Warning
If you see:
```
⚠ Statically exporting a Next.js application via `next export` disables API routes
```

**Solution**: You're using `npm run build` (static) instead of `npm run build:server` (server mode).

---

## Deployment Checklist

### Production Server Deployment

- [ ] Set `NEXT_PUBLIC_API_URL` to production backend URL
- [ ] Set `NEXT_OUTPUT_MODE=standalone`
- [ ] Run `npm run build:server`
- [ ] Copy `.next/standalone/` to server
- [ ] Start with `npm run start` or `node .next/standalone/server.js`
- [ ] Configure reverse proxy (nginx) for SSL/HTTPS
- [ ] Verify CSP headers include production backend URL

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build:server

EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

CMD ["node", ".next/standalone/server.js"]
```

---

## Security Considerations

### Content Security Policy (CSP)

The CSP headers are configured to allow:
- Self-hosted scripts and styles
- Backend API connections (`NEXT_PUBLIC_API_URL`)
- External services (Peppol, IRAS)

### JWT Token Security

- Access tokens: Stored in memory (JavaScript variable)
- Refresh tokens: HttpOnly cookie (not accessible to JavaScript)
- Token refresh: Automatic on 401 responses

### Headers Applied (Server Mode Only)

| Header | Value |
|--------|-------|
| Content-Security-Policy | Custom CSP with backend URL |
| Strict-Transport-Security | max-age=31536000 |
| X-Frame-Options | DENY |
| X-Content-Type-Options | nosniff |
| Referrer-Policy | strict-origin-when-cross-origin |

---

## Performance Optimization

### Production Build
- Code splitting automatically enabled
- Image optimization (when unoptimized: false)
- Static page generation where possible
- Edge runtime support

### React Query Caching
- Stale time: 5 minutes
- Cache time: 10 minutes
- Automatic background refetch

---

## Support

For issues or questions:
1. Check this guide first
2. Review `TROUBLESHOOTING.md` (if available)
3. Check backend logs for API errors
4. Review browser console for frontend errors

---

*Generated for LedgerSG v0.1.0*
