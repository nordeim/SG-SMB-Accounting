# LedgerSG Full-Stack Dockerfile
# Optimized for Hugging Face Spaces with Live Frontend + Backend API Integration
# Multi-port exposure for flexible HF Space URL mapping (3000/7860/8000)
# Database: PostgreSQL 17 + Redis (localhost:6379)
# Frontend: Next.js Standalone Mode
# Backend: Django + Gunicorn (Production WSGI)
FROM python:3.13-trixie

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Environment Configuration
# ═══════════════════════════════════════════════════════════════════════════════
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

# Service Ports (all exposed for flexible HF Space mapping)
ENV APP_PORT=7860
ENV FRONTEND_PORT=3000
ENV BACKEND_PORT=8000

# Runtime directories
ENV XDG_RUNTIME_DIR=/tmp/runtime-user
ENV PATH="/home/user/.local/bin:/usr/local/bin:${PATH}"

# PostgreSQL Configuration (persistent & user-writable)
ENV PGDATA=/data/postgresql
ENV PGHOST=/tmp
ENV PGPORT=5432

# Database Configuration
ENV DB_NAME=ledgersg_dev
ENV DB_USER=ledgersg
ENV DB_PASSWORD=ledgersg_secret_to_change
ENV DB_HOST=localhost
ENV DB_PORT=5432
ENV REDIS_URL=redis://localhost:6379/0

# Frontend Configuration for Backend API Integration
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_OUTPUT_MODE=standalone
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0

# ═══════════════════════════════════════════════════════════════════════════════
# 2. System Dependencies (Database + Dev Tools)
# ═══════════════════════════════════════════════════════════════════════════════
RUN apt-get update && apt-get install -y \
    bash coreutils ca-certificates cron curl wget git less procps sudo vim tar zip unzip tmux openssh-client rsync \
    build-essential gcc gnupg cmake pkg-config \
    libpq-dev libjson-c-dev libssl-dev libwebsockets-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev libjpeg-dev libopenjp2-7-dev \
    postgresql postgresql-contrib redis-server netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && if [ ! -d "/usr/lib/postgresql/17" ]; then echo "ERROR: PostgreSQL 17 not installed" && exit 1; fi \
    && echo "✓ PostgreSQL 17 verified at build time"

# ═══════════════════════════════════════════════════════════════════════════════
# 3. Toolchain Installation (UV, Bun)
# ═══════════════════════════════════════════════════════════════════════════════
RUN cd /usr/bin && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/bun && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/uv && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/uvx && \
    chmod a+x /usr/bin/bun /usr/bin/uv*

# ═══════════════════════════════════════════════════════════════════════════════
# 4. Python Virtual Environment & Dependencies
# ═══════════════════════════════════════════════════════════════════════════════
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip

# Install Python dependencies (includes gunicorn)
RUN /opt/venv/bin/pip install django-celery-beat && \
    /opt/venv/bin/pip install -U django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter && \
    /opt/venv/bin/pip install psycopg[binary] celery[redis] redis py-moneyed pydantic weasyprint lxml python-decouple whitenoise gunicorn structlog sentry-sdk[django] argon2-cffi pytest pytest-django pytest-cov pytest-xdist model-bakery factory-boy faker httpx ruff mypy django-stubs djangorestframework-stubs pre-commit ipython django-debug-toolbar django-extensions && \
    /opt/venv/bin/pip install fastapi uvicorn httpx pydantic python-multipart sqlalchemy alembic aiofiles jinja2

# ═══════════════════════════════════════════════════════════════════════════════
# 5. Node.js Installation (LTS 24.x)
# ═══════════════════════════════════════════════════════════════════════════════
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && \
    npm --version

# ═══════════════════════════════════════════════════════════════════════════════
# 6. User & Permission Setup (Hugging Face Requirement)
# ═══════════════════════════════════════════════════════════════════════════════
RUN groupadd -g 1000 user && \
    useradd -m -u 1000 -g user -d /home/user user && \
    echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user && \
    mkdir -p ${XDG_RUNTIME_DIR} /data /app /var/run/postgresql /data/postgresql && \
    chown -R user:user ${XDG_RUNTIME_DIR} /opt/venv /data /app /var/run/postgresql /var/lib/postgresql && \
    chmod 700 /data/postgresql

# ═══════════════════════════════════════════════════════════════════════════════
# 7. Global NPM & Playwright
# ═══════════════════════════════════════════════════════════════════════════════
RUN npm install -g --omit=dev pnpm@latest vite@latest vitest@latest serve && \
    npx playwright install chromium && \
    npx playwright install-deps chromium

# ═══════════════════════════════════════════════════════════════════════════════
# 8. Clone LedgerSG Repository (AT BUILD TIME)
# ═══════════════════════════════════════════════════════════════════════════════
RUN cd /app && \
    git clone https://github.com/nordeim/ledgersg.git ledgersg_src && \
    mv ledgersg_src/* . && \
    mv ledgersg_src/.* . 2>/dev/null || true && \
    rm -rf ledgersg_src && \
    chown -R user:user /app

# ═══════════════════════════════════════════════════════════════════════════════
# 9. Frontend Build (AT BUILD TIME - Standalone Mode)
# ═══════════════════════════════════════════════════════════════════════════════
RUN cd /app/apps/web && \
    npm install && \
    npm run clean && \
    NEXT_OUTPUT_MODE=standalone NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build:server && \
    ls -la .next/standalone/ && \
    chown -R user:user /app/apps/web

# ═══════════════════════════════════════════════════════════════════════════════
# 10. Verify Frontend Build Integrity (WITH ERROR HANDLING)
# ═══════════════════════════════════════════════════════════════════════════════
RUN cd /app/apps/web && \
    echo "Verifying standalone build..." && \
    if [ ! -f ".next/standalone/server.js" ]; then \
        echo "ERROR: Frontend standalone build missing!"; \
        ls -la .next/ 2>&1 || true; \
        exit 1; \
    fi && \
    if [ ! -d ".next/standalone/.next/static" ]; then \
        echo "WARNING: Static files not in standalone folder, copying..."; \
        cp -r .next/static .next/standalone/.next/ 2>/dev/null || true; \
    fi && \
    STATIC_COUNT=$(ls .next/standalone/.next/static/chunks/*.js 2>/dev/null | wc -l) && \
    echo "✓ Standalone build verified: $STATIC_COUNT JS chunks" && \
    chown -R user:user /app/apps/web

# ═══════════════════════════════════════════════════════════════════════════════
# 11. Database & Server Bootstrap Scripts (Embedded)
# ═══════════════════════════════════════════════════════════════════════════════
RUN mkdir -p /app/core /app/scripts && \
    chown -R user:user /app

# Enhanced boot.py - Keep-alive + Service Health Monitor + Log Viewer
COPY <<'BOOTEOF' /app/core/boot.py
"""
LedgerSG HF Space Keep-Alive Server
Provides health checks, service monitoring, and log access for debugging
"""
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn
import os
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

app = FastAPI(title="LedgerSG Space Monitor")

def check_service(url: str, timeout: int = 2) -> dict:
    """Check if a service is responding"""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {
                "status": "healthy",
                "status_code": response.status,
                "url": url
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "error": f"HTTP {e.code}",
            "url": url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url": url
        }

@app.get("/")
def read_root():
    """Complete service status overview"""
    return {
        "service": "LedgerSG HF Space",
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "frontend": check_service("http://localhost:3000"),
            "backend": check_service("http://localhost:8000/api/v1/health/"),
            "boot": {"status": "healthy", "port": 7860}
        },
        "endpoints": {
            "health": "/health",
            "logs": "/logs/{service}?lines=50",
            "status": "/"
        }
    }

@app.get("/health")
def health():
    """Simple health check for container orchestration"""
    return {"status": "healthy", "service": "ledgersg-boot"}

@app.get("/logs/{service}")
def get_logs(service: str, lines: int = 50):
    """View service logs for debugging"""
    log_files = {
        "backend": "/tmp/backend.log",
        "backend_error": "/tmp/backend_error.log",
        "backend_access": "/tmp/backend_access.log",
        "frontend": "/tmp/frontend.log",
        "postgres": "/tmp/postgres.log"
    }
    if service not in log_files:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Unknown service",
                "available_services": list(log_files.keys())
            }
        )
    log_path = log_files[service]
    try:
        result = subprocess.run(
            ["tail", f"-{lines}", log_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {
            "service": service,
            "log_file": log_path,
            "lines_requested": lines,
            "lines_returned": len(result.stdout.strip().split('\n')),
            "content": result.stdout
        }
    except subprocess.TimeoutExpired:
        return JSONResponse(
            status_code=500,
            content={"error": "Timeout reading log file"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/env")
def show_env():
    """Show relevant environment variables (safe for debugging)"""
    return {
        "APP_PORT": os.getenv("APP_PORT"),
        "FRONTEND_PORT": os.getenv("FRONTEND_PORT"),
        "BACKEND_PORT": os.getenv("BACKEND_PORT"),
        "NEXT_PUBLIC_API_URL": os.getenv("NEXT_PUBLIC_API_URL"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
        "NODE_ENV": os.getenv("NODE_ENV")
    }

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 7860))
    print(f"Starting LedgerSG boot server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
BOOTEOF

# ═══════════════════════════════════════════════════════════════════════════════
# 12. Entrypoint Script (Runtime Service Orchestration)
# ═══════════════════════════════════════════════════════════════════════════════
COPY <<'ENTRYEOF' /usr/local/bin/entrypoint.sh
# ═══════════════════════════════════════════════════════════════════════════════
# Start Backend API (Django + Gunicorn - Production Ready)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🚀 Starting Backend API (Gunicorn) on port ${BACKEND_PORT}..."
cd /app/apps/backend

# Create log directories (CRITICAL FIX)
mkdir -p /tmp/backend_logs
chown user:user /tmp/backend_logs
chmod 755 /tmp/backend_logs
echo "✓ Backend log directory created"

# Create .env file for backend
cat > .env << ENVEOF
DEBUG=False
SECRET_KEY=django-secret-key-for-hf-space-$(date +%s)
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
REDIS_URL=${REDIS_URL}
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}
LOG_LEVEL=INFO
ENVEOF

# Start Django with Gunicorn (production WSGI)
sudo -u user nohup bash -c "
source /opt/venv/bin/activate &&
cd /app/apps/backend &&
gunicorn config.wsgi:application \
-b 0.0.0.0:${BACKEND_PORT} \
--workers 2 \
--threads 2 \
--worker-class gthread \
--timeout 60 \
--keep-alive 5 \
--max-requests 1000 \
--max-requests-jitter 50 \
--access-logfile /tmp/backend_logs/access.log \
--error-logfile /tmp/backend_logs/error.log \
--capture-output \
--enable-stdio-inheritance
" > /tmp/backend_logs/gunicorn.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend PID: ${BACKEND_PID} (Gunicorn: 2 workers, 2 threads)"

# Wait for backend with improved health check
echo "⏳ Waiting for Backend API..."
BACKEND_READY=false
for i in {1..60}; do
    # Check if Gunicorn process is still running
    if ! pgrep -f "gunicorn.*config.wsgi" > /dev/null 2>&1; then
        echo "✗ Backend Gunicorn process died (attempt $i)"
        echo "📋 Backend error log:"
        tail -50 /tmp/backend_logs/error.log 2>/dev/null || echo "  (log not available)"
        break
    fi
    
    # Check health endpoint
    if curl -sf http://localhost:${BACKEND_PORT}/api/v1/health/ > /dev/null 2>&1; then
        echo "✓ Backend API ready (attempt $i)"
        BACKEND_READY=true
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "⚠ Backend not ready after 30s, checking logs..."
        tail -30 /tmp/backend_logs/error.log 2>/dev/null || true
    fi
    
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo "✗ Backend API failed to start"
    echo "📋 Last 50 lines of backend error log:"
    tail -50 /tmp/backend_logs/error.log 2>/dev/null || echo "  (log not available)"
fi
ENTRYEOF

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown -R user:user /app/core /app/scripts

# ═══════════════════════════════════════════════════════════════════════════════
# 13. Finalization
# ═══════════════════════════════════════════════════════════════════════════════
WORKDIR /app
RUN touch /app/.env && chown user:user /app/.env

# Expose ALL ports for flexible HF Space URL mapping
EXPOSE ${APP_PORT} ${FRONTEND_PORT} ${BACKEND_PORT}

# Health check - flexible for any exposed port
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${FRONTEND_PORT} 2>/dev/null || \
        curl -f http://localhost:${APP_PORT}/health 2>/dev/null || \
        exit 1

# Use Entrypoint to start all services, then run the keep-alive server
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/opt/venv/bin/python", "/app/core/boot.py"]
