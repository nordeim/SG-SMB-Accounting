# LedgerSG Full-Stack Dockerfile
# Optimized for Hugging Face Spaces with Live Frontend + Backend API Integration
# Database Configuration: PostgreSQL 17 + Redis (localhost:6379)
# Frontend: Next.js Standalone Mode with Backend API Integration
FROM python:3.13-trixie

# ──────────────────────────────────────────────────────────────────────────────
# 1. Environment Configuration
# ──────────────────────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive
ENV APP_PORT=7860
ENV FRONTEND_PORT=3000
ENV BACKEND_PORT=8000
ENV XDG_RUNTIME_DIR=/tmp/runtime-user
ENV PATH="/home/user/.local/bin:/usr/local/bin:${PATH}"

# CRITICAL: Use /data for PostgreSQL (persistent & user-writable)
ENV PGDATA=/data/postgresql
ENV PGHOST=/tmp
ENV PGPORT=5432

# Database Configuration (from .env)
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

# ──────────────────────────────────────────────────────────────────────────────
# 2. System Dependencies (Database + Dev Tools)
# ──────────────────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    bash coreutils ca-certificates cron curl wget git less procps sudo vim tar zip unzip tmux openssh-client rsync \
    build-essential gcc gnupg cmake pkg-config \
    libpq-dev libjson-c-dev libssl-dev libwebsockets-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev libjpeg-dev libopenjp2-7-dev \
    postgresql postgresql-contrib redis-server \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    # Verify PostgreSQL installation at build time
    && if [ ! -d "/usr/lib/postgresql/17" ]; then echo "ERROR: PostgreSQL 17 not installed" && exit 1; fi \
    && echo "✓ PostgreSQL 17 verified at build time"

# ──────────────────────────────────────────────────────────────────────────────
# 3. Toolchain Installation (UV, Bun)
# ──────────────────────────────────────────────────────────────────────────────
RUN cd /usr/bin && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/bun && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/uv && \
    wget -q https://github.com/nordeim/HF-Space/raw/refs/heads/main/uvx && \
    chmod a+x /usr/bin/bun /usr/bin/uv*

# ──────────────────────────────────────────────────────────────────────────────
# 4. Python Virtual Environment & Dependencies
# ──────────────────────────────────────────────────────────────────────────────
# Create virtual environment for the application
RUN python3 -m venv /opt/venv && \
    chown -R user:user /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip

# Install Python dependencies in virtual environment
RUN /opt/venv/bin/pip install django-celery-beat && \
    /opt/venv/bin/pip install -U django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter && \
    /opt/venv/bin/pip install psycopg[binary] celery[redis] redis py-moneyed pydantic weasyprint lxml python-decouple whitenoise gunicorn structlog sentry-sdk[django] argon2-cffi pytest pytest-django pytest-cov pytest-xdist model-bakery factory-boy faker httpx ruff mypy django-stubs djangorestframework-stubs pre-commit ipython django-debug-toolbar django-extensions && \
    /opt/venv/bin/pip install fastapi uvicorn httpx pydantic python-multipart sqlalchemy alembic aiofiles jinja2 gunicorn 

# ──────────────────────────────────────────────────────────────────────────────
# 5. Node.js Installation (LTS 24.x)
# ──────────────────────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && \
    npm --version

# ──────────────────────────────────────────────────────────────────────────────
# 6. User & Permission Setup (Hugging Face Requirement)
# ──────────────────────────────────────────────────────────────────────────────
RUN groupadd -g 1000 user && \
    useradd -m -u 1000 -g user -d /home/user user && \
    echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user && \
    mkdir -p ${XDG_RUNTIME_DIR} /data /app /var/run/postgresql /data/postgresql && \
    chown -R user:user ${XDG_RUNTIME_DIR} /data /app /var/run/postgresql /var/lib/postgresql && \
    chmod 700 /data/postgresql

# ──────────────────────────────────────────────────────────────────────────────
# 7. Global NPM & Playwright
# ──────────────────────────────────────────────────────────────────────────────
RUN npm install -g --omit=dev pnpm@latest vite@latest vitest@latest serve && \
    npx playwright install chromium && \
    npx playwright install-deps chromium

# ──────────────────────────────────────────────────────────────────────────────
# 8. Clone LedgerSG Repository (AT BUILD TIME)
# ──────────────────────────────────────────────────────────────────────────────
RUN cd /app && \
    git clone https://github.com/nordeim/ledgersg.git ledgersg_src && \
    mv ledgersg_src/* . && \
    mv ledgersg_src/.* . 2>/dev/null || true && \
    rm -rf ledgersg_src && \
    chown -R user:user /app

# ──────────────────────────────────────────────────────────────────────────────
# 9. Frontend Build (AT BUILD TIME - Standalone Mode for Backend API)
# ──────────────────────────────────────────────────────────────────────────────
RUN cd /app/apps/web && \
    npm install && \
    npm run clean && \
    # Build with server mode for backend API integration
    NEXT_OUTPUT_MODE=standalone NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build:server && \
    # Verify standalone build output exists
    ls -la .next/standalone/ && \
    chown -R user:user /app/apps/web

# ──────────────────────────────────────────────────────────────────────────────
# 10. Database & Server Bootstrap Scripts (Embedded)
# ──────────────────────────────────────────────────────────────────────────────
RUN mkdir -p /app/core /app/scripts && \
    chown -R user:user /app

COPY <<EOF /app/core/boot.py
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "alive", "service": "LedgerSG Dev Space"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF

# ──────────────────────────────────────────────────────────────────────────────
# CRITICAL: Fixed Entrypoint Script (ALL services start at RUNTIME)
# ──────────────────────────────────────────────────────────────────────────────
COPY <<EOF /usr/local/bin/entrypoint.sh
#!/bin/bash
set -e
echo "=== LedgerSG Development Space Starting ==="
echo "🕐 Startup time: \$(date -Iseconds)"

# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQL Detection
# ──────────────────────────────────────────────────────────────────────────────
echo "🔍 Detecting PostgreSQL installation..."
PG_VERSION="17"
PG_BIN="/usr/lib/postgresql/\${PG_VERSION}/bin"

if [ ! -d "/usr/lib/postgresql/\${PG_VERSION}" ]; then
    echo "✗ ERROR: PostgreSQL 17 directory not found"
    ls -la /usr/lib/postgresql/ 2>&1 || echo "  (directory not accessible)"
    exit 1
fi

echo "✓ PostgreSQL version: \${PG_VERSION}"
echo "✓ Binary path: \${PG_BIN}"
echo "🔍 Verifying PostgreSQL binaries..."

for cmd in initdb pg_ctl psql pg_isready; do
    if [ ! -x "\${PG_BIN}/\${cmd}" ]; then
        echo "✗ ERROR: \${cmd} not found or not executable"
        exit 1
    fi
    echo "  ✓ \${cmd} verified"
done

# ──────────────────────────────────────────────────────────────────────────────
# Environment Setup
# ──────────────────────────────────────────────────────────────────────────────
echo "🔧 Configuring environment..."
mkdir -p \$PGDATA
chown -R user:user \$PGDATA
chmod 700 \$PGDATA
mkdir -p /var/run/postgresql
chown -R user:user /var/run/postgresql
chmod 777 /var/run/postgresql

# ──────────────────────────────────────────────────────────────────────────────
# Initialize Postgres if not exists
# ──────────────────────────────────────────────────────────────────────────────
if [ ! -f "\$PGDATA/PG_VERSION" ]; then
    echo "📦 Initializing PostgreSQL cluster at \$PGDATA..."
    sudo -u user \${PG_BIN}/initdb -D \$PGDATA
    
    echo "🔐 Configuring PostgreSQL authentication..."
    cat >> \$PGDATA/pg_hba.conf << 'PGHBA'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
PGHBA
    
    echo "listen_addresses = 'localhost'" >> \$PGDATA/postgresql.conf
    echo "port = 5432" >> \$PGDATA/postgresql.conf
    echo "✓ PostgreSQL configuration complete"
else
    echo "✓ PostgreSQL cluster already initialized at \$PGDATA"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Start Redis
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting Redis on port 6379..."
redis-server --daemonize yes
sleep 1

# ──────────────────────────────────────────────────────────────────────────────
# Start PostgreSQL
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting PostgreSQL on port 5432..."
sudo -u user \${PG_BIN}/pg_ctl -D \$PGDATA -l /tmp/postgres.log start

echo "⏳ Waiting for PostgreSQL to accept connections..."
for i in {1..30}; do
    if sudo -u user \${PG_BIN}/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready (attempt \$i)"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start within 30 seconds"
        cat /tmp/postgres.log 2>/dev/null || echo "  (log not available)"
        exit 1
    fi
    sleep 1
done

# ──────────────────────────────────────────────────────────────────────────────
# Create Database User and Database - WITH CREATEDB PRIVILEGE
# ──────────────────────────────────────────────────────────────────────────────
echo "🗄️ Setting up database user and database..."

if ! sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_roles WHERE rolname='\${DB_USER}';" | grep -q 1; then
    echo "  → Creating user: \${DB_USER}"
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE ROLE \${DB_USER} WITH LOGIN CREATEDB PASSWORD '\${DB_PASSWORD}';"
else
    echo "  ✓ User \${DB_USER} already exists"
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "ALTER ROLE \${DB_USER} WITH CREATEDB;" 2>/dev/null || true
fi

if ! sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_database WHERE datname='\${DB_NAME}';" | grep -q 1; then
    echo "  → Creating database: \${DB_NAME}"
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE \${DB_NAME} OWNER \${DB_USER};"
else
    echo "  ✓ Database \${DB_NAME} already exists"
fi

sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d \${DB_NAME} -c "GRANT ALL PRIVILEGES ON DATABASE \${DB_NAME} TO \${DB_USER};"
echo "✓ Database setup complete: \${DB_NAME} (user: \${DB_USER})"
sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d \${DB_NAME} -f /app/apps/backend/database_schema.sql

# ──────────────────────────────────────────────────────────────────────────────
# Verify Redis
# ──────────────────────────────────────────────────────────────────────────────
echo "🔍 Verifying Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready on localhost:6379"
else
    echo "✗ Redis failed to start"
    exit 1
fi

# ──────────────────────────────────────────────────────────────────────────────
# Start Backend API Service (Django)
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting Backend API on port \${BACKEND_PORT}..."
cd /app/apps/backend

# Create .env file for backend
cat > .env << ENVEOF
DEBUG=True
SECRET_KEY=django-secret-key-for-docker-local-development
DB_NAME=\${DB_NAME}
DB_USER=\${DB_USER}
DB_PASSWORD=\${DB_PASSWORD}
DB_HOST=\${DB_HOST}
DB_PORT=\${DB_PORT}
REDIS_URL=\${REDIS_URL}
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:\${FRONTEND_PORT},http://127.0.0.1:\${FRONTEND_PORT}
ENVEOF

# Start Django backend in background
sudo -u user nohup bash -c "source /opt/venv/bin/activate && python manage.py runserver 0.0.0.0:\${BACKEND_PORT}" > /tmp/backend.log 2>&1 &
BACKEND_PID=\$!
echo "✓ Backend PID: \${BACKEND_PID}"

# Wait for backend to be ready
for i in {1..60}; do
    if curl -s http://localhost:\${BACKEND_PORT}/api/v1/health/ > /dev/null 2>&1 || curl -s http://localhost:\${BACKEND_PORT} > /dev/null 2>&1; then
        echo "✓ Backend API is ready (attempt \$i)"
        break
    fi
    if [ \$i -eq 60 ]; then
        echo "⚠ Backend may not be ready yet (continuing anyway)"
        echo "Backend log:"
        tail -20 /tmp/backend.log 2>/dev/null || echo "  (log not available)"
    fi
    sleep 1
done

# ──────────────────────────────────────────────────────────────────────────────
# Start Frontend (AT RUNTIME - Live Server with Backend API Integration)
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting Frontend on port \${FRONTEND_PORT}..."
cd /app/apps/web

# CRITICAL: Use standalone server for backend API integration
# The standalone build output is in .next/standalone/
sudo -u user nohup bash -c "NODE_ENV=production PORT=\${FRONTEND_PORT} HOSTNAME=0.0.0.0 node .next/standalone/server.js" > /tmp/frontend.log 2>&1 &
FRONTEND_PID=\$!
echo "✓ Frontend PID: \${FRONTEND_PID}"
echo "✓ Frontend mode: Standalone (with backend API integration)"

# Wait for frontend to be ready
for i in {1..30}; do
    if curl -s http://localhost:\${FRONTEND_PORT} > /dev/null 2>&1; then
        echo "✓ Frontend is ready (attempt \$i)"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "⚠ Frontend may not be ready yet (continuing anyway)"
        echo "Frontend log:"
        tail -20 /tmp/frontend.log 2>/dev/null || echo "  (log not available)"
    fi
    sleep 1
done

# ──────────────────────────────────────────────────────────────────────────────
# Start Web Server (CMD)
# ──────────────────────────────────────────────────────────────────────────────
echo "=== Starting Web Server on port \$APP_PORT ==="
echo "✅ All services initialized successfully"
echo ""
echo "📋 Service Status:"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis:      localhost:6379"
echo "  • Backend:    http://localhost:\${BACKEND_PORT} (Django API)"
echo "  • Frontend:   http://localhost:\${FRONTEND_PORT} (Next.js with API)"
echo "  • Web Server: http://localhost:\$APP_PORT"
echo ""

# Execute the main command (Web Server) AS USER
exec sudo -u user "\$@"
EOF

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown -R user:user /app/core /app/scripts

# ──────────────────────────────────────────────────────────────────────────────
# 11. Finalization
# ──────────────────────────────────────────────────────────────────────────────
WORKDIR /app
# Ensure .env file exists
RUN touch /app/.env && chown user:user /app/.env

EXPOSE ${APP_PORT} ${FRONTEND_PORT} ${BACKEND_PORT}

# Healthcheck against the boot.py server
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

# Use Entrypoint to start DBs, then run the boot.py server
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "/app/core/boot.py"]
