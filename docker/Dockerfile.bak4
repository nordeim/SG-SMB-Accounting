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
ENV PYTHONDONTWRIBYTECODE=1
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
    postgresql postgresql-contrib redis-server \
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
# 10. Verify Frontend Build Integrity
# ═══════════════════════════════════════════════════════════════════════════════
RUN cd /app/apps/web && \
    echo "Verifying standalone build..." && \
    ls -la .next/standalone/server.js && \
    if [ ! -d ".next/standalone/.next/static" ]; then \
        echo "ERROR: Static files not in standalone folder!"; \
        exit 1; \
    fi && \
    STATIC_COUNT=$(ls .next/standalone/.next/static/chunks/*.js 2>/dev/null | wc -l) && \
    if [ "$STATIC_COUNT" -lt "5" ]; then \
        echo "ERROR: Only $STATIC_COUNT JS chunks found. Expected 20+"; \
        exit 1; \
    else \
        echo "✓ Standalone build verified: $STATIC_COUNT JS chunks"; \
    fi

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
#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "   LedgerSG HF Space Starting"
echo "════════════════════════════════════════════════════════════════"
echo "🕐 Startup time: $(date -Iseconds)"

# ═══════════════════════════════════════════════════════════════════════════════
# PostgreSQL Detection & Setup
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Configuring PostgreSQL..."
PG_VERSION="17"
PG_BIN="/usr/lib/postgresql/${PG_VERSION}/bin"

if [ ! -d "/usr/lib/postgresql/${PG_VERSION}" ]; then
    echo "✗ ERROR: PostgreSQL ${PG_VERSION} not found"
    ls -la /usr/lib/postgresql/ 2>&1 || echo "  (directory not accessible)"
    exit 1
fi

echo "✓ PostgreSQL ${PG_VERSION} at ${PG_BIN}"

# Verify binaries
for cmd in initdb pg_ctl psql pg_isready; do
    if [ ! -x "${PG_BIN}/${cmd}" ]; then
        echo "✗ ERROR: ${cmd} not found"
        exit 1
    fi
done
echo "✓ All PostgreSQL binaries verified"

# Environment setup
mkdir -p $PGDATA
chown -R user:user $PGDATA
chmod 700 $PGDATA
mkdir -p /var/run/postgresql
chown -R user:user /var/run/postgresql
chmod 777 /var/run/postgresql

# Initialize PostgreSQL if needed
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "📦 Initializing PostgreSQL cluster..."
    sudo -u user ${PG_BIN}/initdb -D $PGDATA
    
    cat >> $PGDATA/pg_hba.conf << 'PGHBA'
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
PGHBA
    
    echo "listen_addresses = 'localhost'" >> $PGDATA/postgresql.conf
    echo "port = 5432" >> $PGDATA/postgresql.conf
    echo "✓ PostgreSQL initialized"
else
    echo "✓ PostgreSQL cluster exists"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Start Redis
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🚀 Starting Redis on port 6379..."
redis-server --daemonize yes
sleep 1

# ═══════════════════════════════════════════════════════════════════════════════
# Start PostgreSQL
# ═══════════════════════════════════════════════════════════════════════════════
echo "🚀 Starting PostgreSQL on port 5432..."
sudo -u user ${PG_BIN}/pg_ctl -D $PGDATA -l /tmp/postgres.log start

echo "⏳ Waiting for PostgreSQL..."
for i in {1..30}; do
    if sudo -u user ${PG_BIN}/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "✓ PostgreSQL ready (attempt $i)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start"
        cat /tmp/postgres.log 2>/dev/null || echo "  (log not available)"
        exit 1
    fi
    sleep 1
done

# ═══════════════════════════════════════════════════════════════════════════════
# Create Database User and Database
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🗄️  Setting up database..."

if ! sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}';" | grep -q 1; then
    echo "  → Creating user: ${DB_USER}"
    sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE ROLE ${DB_USER} WITH LOGIN CREATEDB PASSWORD '${DB_PASSWORD}';"
else
    echo "  ✓ User ${DB_USER} exists"
fi

if ! sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1; then
    echo "  → Creating database: ${DB_NAME}"
    sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
else
    echo "  ✓ Database ${DB_NAME} exists"
fi

sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d ${DB_NAME} -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
echo "✓ Database setup complete"

# Apply schema
echo "  → Applying database schema..."
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d ${DB_NAME} -f /app/apps/backend/database_schema.sql
echo "  ✓ Schema applied"

# ═══════════════════════════════════════════════════════════════════════════════
# Verify Redis
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🔍 Verifying Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis ready on localhost:6379"
else
    echo "✗ Redis failed to start"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════════
# Start Backend API (Django + Gunicorn - Production Ready)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🚀 Starting Backend API (Gunicorn) on port ${BACKEND_PORT}..."
cd /app/apps/backend

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
        --access-logfile /tmp/backend_access.log \
        --error-logfile /tmp/backend_error.log \
        --capture-output \
        --enable-stdio-inheritance
" > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend PID: ${BACKEND_PID} (Gunicorn: 2 workers, 2 threads)"

# Wait for backend
for i in {1..60}; do
    if curl -s http://localhost:${BACKEND_PORT}/api/v1/health/ > /dev/null 2>&1; then
        echo "✓ Backend API ready (attempt $i)"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠ Backend may not be ready (continuing)"
        tail -20 /tmp/backend_error.log 2>/dev/null || true
    fi
    sleep 1
done

# ═══════════════════════════════════════════════════════════════════════════════
# Start Frontend (Next.js Standalone)
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "🚀 Starting Frontend on port ${FRONTEND_PORT}..."
cd /app/apps/web

# Verify build integrity
if [ ! -f ".next/standalone/server.js" ]; then
    echo "✗ ERROR: Frontend standalone build missing!"
    exit 1
fi

sudo -u user nohup bash -c "
    export NODE_ENV=production
    export PORT=${FRONTEND_PORT}
    export HOSTNAME=0.0.0.0
    export NEXT_PUBLIC_API_URL=http://localhost:8000
    node .next/standalone/server.js
" > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✓ Frontend PID: ${FRONTEND_PID}"

# Wait for frontend
for i in {1..30}; do
    if curl -s http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
        echo "✓ Frontend ready (attempt $i)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠ Frontend may not be ready (continuing)"
        tail -20 /tmp/frontend.log 2>/dev/null || true
    fi
    sleep 1
done

# ═══════════════════════════════════════════════════════════════════════════════
# Final Service Status
# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "   Service Status Summary"
echo "════════════════════════════════════════════════════════════════"
echo "🕐 Ready at: $(date -Iseconds)"
echo ""

SERVICES_READY=true

if curl -s http://localhost:${BACKEND_PORT}/api/v1/health/ > /dev/null 2>&1; then
    echo "  ✅ Backend API:    http://localhost:${BACKEND_PORT} (Gunicorn)"
else
    echo "  ⚠️  Backend API:    Not responding"
    SERVICES_READY=false
fi

if curl -s http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
    echo "  ✅ Frontend:       http://localhost:${FRONTEND_PORT}"
else
    echo "  ⚠️  Frontend:       Not responding"
    SERVICES_READY=false
fi

if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis:          localhost:6379"
else
    echo "  ⚠️  Redis:          Not responding"
fi

if sudo -u user ${PG_BIN}/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL:     localhost:5432"
else
    echo "  ⚠️  PostgreSQL:     Not responding"
fi

echo "  ℹ️  Monitor:        http://localhost:${APP_PORT} (boot.py)"
echo ""

if [ "$SERVICES_READY" = true ]; then
    echo "🎉 All critical services are ready!"
else
    echo "⚠️  Some services still starting..."
fi

echo ""
echo "📖 Debug commands:"
echo "  • Full status:  curl http://localhost:${APP_PORT}/"
echo "  • Health:       curl http://localhost:${APP_PORT}/health"
echo "  • Logs:         curl http://localhost:${APP_PORT}/logs/backend"
echo "  • Frontend:     curl http://localhost:${APP_PORT}/logs/frontend"
echo ""
echo "════════════════════════════════════════════════════════════════"

# Execute the main command (boot.py keep-alive server)
exec sudo -u user "$@"
ENTRYEOF

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown -R user:user /app/core /app/scripts

# ═══════════════════════════════════════════════════════════════════════════════
# 13. Finalization
# ═══════════════════════════════════════════════════════════════════════════════
WORKDIR /app
RUN touch /app/.env && chown user:user /app/.env

# Expose ALL ports for flexible HF Space URL mapping
# HF Space can map its URL to any of these ports via settings
EXPOSE ${APP_PORT} ${FRONTEND_PORT} ${BACKEND_PORT}

# Health check - flexible for any exposed port
# HF Space will configure which port the URL maps to
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${FRONTEND_PORT} 2>/dev/null || \
        curl -f http://localhost:${APP_PORT}/health 2>/dev/null || \
        exit 1

# Use Entrypoint to start all services, then run the keep-alive server
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/opt/venv/bin/python", "/app/core/boot.py"]
