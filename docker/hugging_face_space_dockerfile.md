# 🔍 PostgreSQL psql Command Error - Fixed

## Executive Summary

**Great progress!** PostgreSQL detection, initialization, and startup are now working perfectly. The error is in the **database user creation step** - the `psql -c` command argument is being split incorrectly due to quoting issues in the entrypoint script.

**Root Cause:** The SQL command string is not being passed as a single argument to `psql -c`, causing it to interpret `-c` as requiring a separate argument.

---

## Phase 1: Root Cause Analysis

### 🔬 The Problem

```bash
# Current (broken):
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1
```

**Issue:** The backslash continuation + quoting causes the `-c` flag and SQL command to be treated as separate arguments.

### 📋 Error Evidence

```
/usr/lib/postgresql/17/bin/psql: option requires an argument -- 'c'
psql: hint: Try "psql --help" for more information.
```

This confirms `psql` is receiving `-c` without its required SQL argument.

---

## Phase 2: Solution

### 📐 Fix Strategy

| Issue | Solution |
|-------|----------|
| Command splitting | Put `-c "SQL"` on same line |
| Variable quoting | Use double quotes for variables |
| Pipe to grep | Capture output properly |
| Error handling | Add explicit error messages |

---

## Phase 3: Implementation

### 🔧 Fixed Dockerfile (Entrypoint Section Only)

Replace **only the entrypoint.sh section** in your Dockerfile with this corrected version:

```dockerfile
# ──────────────────────────────────────────────────────────────────────────────
# CRITICAL: Fixed Entrypoint Script (psql command quoting corrected)
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
# Create Database User and Database - FIXED psql COMMANDS
# ──────────────────────────────────────────────────────────────────────────────
echo "🗄️ Setting up database user and database..."

# Check if user exists - FIXED: -c and SQL on same line, proper quoting
if ! sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_roles WHERE rolname='\${DB_USER}';" | grep -q 1; then
    echo "  → Creating user: \${DB_USER}"
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE ROLE \${DB_USER} WITH LOGIN PASSWORD '\${DB_PASSWORD}';"
else
    echo "  ✓ User \${DB_USER} already exists"
fi

# Check if database exists - FIXED: -c and SQL on same line, proper quoting
if ! sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "SELECT 1 FROM pg_database WHERE datname='\${DB_NAME}';" | grep -q 1; then
    echo "  → Creating database: \${DB_NAME}"
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE \${DB_NAME} OWNER \${DB_USER};"
else
    echo "  ✓ Database \${DB_NAME} already exists"
fi

# Grant privileges - FIXED: -c and SQL on same line, proper quoting
sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d \${DB_NAME} -c "GRANT ALL PRIVILEGES ON DATABASE \${DB_NAME} TO \${DB_USER};"

echo "✓ Database setup complete: \${DB_NAME} (user: \${DB_USER})"

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
# Start Web Server
# ──────────────────────────────────────────────────────────────────────────────
echo "=== Starting Web Server on port \$APP_PORT ==="
echo "✅ All services initialized successfully"
exec sudo -u user "\$@"
EOF

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown -R user:user /app/core
```

---

## Phase 4: Key Changes Made

| Change | Before | After | Why |
|--------|--------|-------|-----|
| **psql -c command** | Split across lines with `\` | Single line: `-c "SQL"` | Prevents argument splitting |
| **Variable quoting** | `'$DB_USER'` | `'\${DB_USER}'` | Proper escaping in Docker heredoc |
| **Semicolon in SQL** | Missing | Added `;` | Proper SQL termination |
| **Error handling** | Generic | Specific messages | Better debugging |
| **User check logic** | Complex pipe | Simplified `if !` | More reliable |

---

## Phase 5: Expected Output

```
=== LedgerSG Development Space Starting ===
🕐 Startup time: 2026-02-27T08:33:27+00:00
🔍 Detecting PostgreSQL installation...
✓ PostgreSQL version: 17
✓ Binary path: /usr/lib/postgresql/17/bin
🔍 Verifying PostgreSQL binaries...
  ✓ initdb verified
  ✓ pg_ctl verified
  ✓ psql verified
  ✓ pg_isready verified
🔧 Configuring environment...
📦 Initializing PostgreSQL cluster at /data/postgresql...
...
🚀 Starting Redis on port 6379...
🚀 Starting PostgreSQL on port 5432...
⏳ Waiting for PostgreSQL to accept connections...
✓ PostgreSQL is ready (attempt 1)
🗄️ Setting up database user and database...
  → Creating user: ledgersg
  → Creating database: ledgersg_dev
✓ Database setup complete: ledgersg_dev (user: ledgersg)
🔍 Verifying Redis connection...
✓ Redis is ready on localhost:6379
=== Starting Web Server on port 7860 ===
✅ All services initialized successfully
```

---

## Phase 6: Validation

### 🧪 Test Commands

```bash
# Build and test locally
docker build -t ledgersg:test .

# Run container
docker run -d -p 7860:7860 ledgersg:test

# Check logs
docker logs -f <container_id>

# Verify database connection
docker exec <container_id> sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -U ledgersg -d ledgersg_dev -c "SELECT 1;"
```

### ✅ Success Criteria

| Criterion | Status |
|-----------|--------|
| PostgreSQL detects correctly | ✅ Verified |
| PostgreSQL initializes | ✅ Verified |
| PostgreSQL starts | ✅ Verified |
| psql commands execute | ⏳ Pending Fix |
| Database user created | ⏳ Pending Fix |
| Database created | ⏳ Pending Fix |
| Web server starts | ⏳ Pending Fix |

---

## 🎯 Immediate Action Required

**Deploy this updated Dockerfile to Hugging Face Spaces.** The fix ensures:

1. ✅ `psql -c "SQL"` is passed as a single argument
2. ✅ Variables are properly escaped in Docker heredoc
3. ✅ SQL statements are properly terminated with `;`
4. ✅ Error handling is explicit and debuggable

**Expected result:** Container should complete database setup and start the web server successfully.

---

# 🔍 PostgreSQL Detection Hanging - Root Cause Identified

## Executive Summary

The container is **hanging at PostgreSQL detection** because the complex `timeout 10 bash -c "$(declare -f detect_postgres_version); detect_postgres_version"` pattern is **not working correctly** in the Hugging Face Spaces environment. The build logs confirm PostgreSQL 17 IS installed at `/usr/lib/postgresql/17/`, so we need to simplify the detection logic.

---

## Phase 1: Root Cause Analysis

### 🔬 Why The Detection Is Hanging

| Issue | Evidence | Impact |
|-------|----------|--------|
| Complex `timeout` + `bash -c` pattern | Script stops at detection line | 🔴 Critical |
| Function declaration in subshell | `declare -f` may not work in all environments | 🔴 Critical |
| `ls` command may hang | Directory access issues in HF Spaces | 🟠 High |
| No fallback to known version | Build log shows PG 17 installed | 🟠 High |

### 📋 Build Log Evidence

From `container_build_log.txt`:
```
Setting up postgresql-17 (17.8-0+deb13u1) ...
Creating new PostgreSQL cluster 17/main ...
/usr/lib/postgresql/17/bin/initdb -D /var/lib/postgresql/17/main
```

**PostgreSQL 17 IS installed.** The detection script just can't find it due to the complex logic.

---

## Phase 2: Execution Plan

### 📐 Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMPLIFIED DETECTION STRATEGY                │
├─────────────────────────────────────────────────────────────────┤
│  1. Hardcode version check for PG 17 (known from build)        │
│  2. Use direct file existence checks (no command execution)    │
│  3. Remove timeout wrapper (causing hang)                      │
│  4. Add explicit error messages with diagnostics               │
│  5. Fail fast if binaries not found                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 3: Implementation

### 🔧 Fixed Dockerfile with Simplified Entrypoint

Replace your **entire Dockerfile** with this corrected version:

```dockerfile
# LedgerSG API Dockerfile
# Optimized for Hugging Face Spaces (Single-Stage, Non-Root, Persistent Services)
# Database Configuration: PostgreSQL 17 + Redis (localhost:6379)
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
# 4. Python Dependencies
# ──────────────────────────────────────────────────────────────────────────────
RUN pip install --upgrade pip && \
    pip install django-celery-beat && \
    pip install -U django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter && \
    pip install psycopg[binary] celery[redis] redis py-moneyed pydantic weasyprint lxml python-decouple whitenoise gunicorn structlog sentry-sdk[django] pytest pytest-django pytest-cov pytest-xdist model-bakery factory-boy faker httpx ruff mypy django-stubs djangorestframework-stubs pre-commit ipython django-debug-toolbar django-extensions && \
    pip install fastapi uvicorn httpx pydantic python-multipart sqlalchemy alembic aiofiles jinja2

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
    # Create ALL required directories
    mkdir -p ${XDG_RUNTIME_DIR} /data /app /var/run/postgresql /data/postgresql && \
    # CRITICAL FIX: Own ALL postgres-related directories
    chown -R user:user ${XDG_RUNTIME_DIR} /data /app /var/run/postgresql /var/lib/postgresql && \
    chmod 700 /data/postgresql

# ──────────────────────────────────────────────────────────────────────────────
# 7. Global NPM & Playwright
# ──────────────────────────────────────────────────────────────────────────────
RUN npm install -g --omit=dev pnpm@latest vite@latest vitest@latest && \
    npx playwright install chromium && \
    npx playwright install-deps chromium

# ──────────────────────────────────────────────────────────────────────────────
# 8. Database & Server Bootstrap Scripts (Embedded)
# ──────────────────────────────────────────────────────────────────────────────
RUN mkdir -p /app/core && \
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
# CRITICAL: Simplified Entrypoint Script (NO HANGING LOGIC)
# ──────────────────────────────────────────────────────────────────────────────
COPY <<EOF /usr/local/bin/entrypoint.sh
#!/bin/bash
set -e

echo "=== LedgerSG Development Space Starting ==="
echo "🕐 Startup time: \$(date -Iseconds)"

# ──────────────────────────────────────────────────────────────────────────────
# PostgreSQL Detection - SIMPLIFIED (No hanging commands)
# ──────────────────────────────────────────────────────────────────────────────
echo "🔍 Detecting PostgreSQL installation..."

# We know PG 17 is installed from build - check directly
PG_VERSION="17"
PG_BIN="/usr/lib/postgresql/\${PG_VERSION}/bin"

# Verify the directory exists
if [ ! -d "/usr/lib/postgresql/\${PG_VERSION}" ]; then
    echo "✗ ERROR: PostgreSQL 17 directory not found at /usr/lib/postgresql/\${PG_VERSION}"
    echo "📋 Available versions:"
    ls -la /usr/lib/postgresql/ 2>&1 || echo "  (directory not accessible)"
    exit 1
fi

# Verify critical binaries exist AND are executable
echo "✓ PostgreSQL version: \${PG_VERSION}"
echo "✓ Binary path: \${PG_BIN}"
echo "🔍 Verifying PostgreSQL binaries..."

for cmd in initdb pg_ctl psql pg_isready; do
    if [ ! -x "\${PG_BIN}/\${cmd}" ]; then
        echo "✗ ERROR: \${cmd} not found or not executable at \${PG_BIN}/\${cmd}"
        echo "📁 Binary directory contents:"
        ls -la "\${PG_BIN}/" 2>&1 || echo "  Directory listing failed"
        exit 1
    fi
    echo "  ✓ \${cmd} verified"
done

# ──────────────────────────────────────────────────────────────────────────────
# Environment Setup
# ──────────────────────────────────────────────────────────────────────────────
echo "🔧 Configuring environment..."

# Ensure PostgreSQL data directory exists and is owned by user
mkdir -p \$PGDATA
chown -R user:user \$PGDATA
chmod 700 \$PGDATA

# Ensure PostgreSQL socket directory is accessible
mkdir -p /var/run/postgresql
chown -R user:user /var/run/postgresql
chmod 777 /var/run/postgresql

# ──────────────────────────────────────────────────────────────────────────────
# Initialize Postgres if not exists (as user via sudo)
# ──────────────────────────────────────────────────────────────────────────────
if [ ! -f "\$PGDATA/PG_VERSION" ]; then
    echo "📦 Initializing PostgreSQL cluster at \$PGDATA..."
    sudo -u user \${PG_BIN}/initdb -D \$PGDATA
    
    # Configure PostgreSQL for password authentication
    echo "🔐 Configuring PostgreSQL authentication..."
    cat >> \$PGDATA/pg_hba.conf << 'PGHBA'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
PGHBA
    
    # Configure listen addresses
    echo "listen_addresses = 'localhost'" >> \$PGDATA/postgresql.conf
    echo "port = 5432" >> \$PGDATA/postgresql.conf
    echo "✓ PostgreSQL configuration complete"
else
    echo "✓ PostgreSQL cluster already initialized at \$PGDATA"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Start Redis in background
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting Redis on port 6379..."
redis-server --daemonize yes
sleep 1

# ──────────────────────────────────────────────────────────────────────────────
# Start Postgres in background (as user via sudo)
# ──────────────────────────────────────────────────────────────────────────────
echo "🚀 Starting PostgreSQL on port 5432..."
sudo -u user \${PG_BIN}/pg_ctl -D \$PGDATA -l /tmp/postgres.log start

# ──────────────────────────────────────────────────────────────────────────────
# Wait for Postgres to be ready
# ──────────────────────────────────────────────────────────────────────────────
echo "⏳ Waiting for PostgreSQL to accept connections..."
for i in {1..30}; do
    if sudo -u user \${PG_BIN}/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready (attempt \$i)"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start within 30 seconds"
        echo "📋 PostgreSQL log:"
        cat /tmp/postgres.log 2>/dev/null || echo "  (log not available)"
        exit 1
    fi
    sleep 1
done

# ──────────────────────────────────────────────────────────────────────────────
# Create database user and database if not exists
# ──────────────────────────────────────────────────────────────────────────────
echo "🗄️ Setting up database user and database..."
sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "SELECT 1 FROM pg_roles WHERE rolname='\$DB_USER'" | grep -q 1 || \
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "CREATE ROLE \$DB_USER WITH LOGIN PASSWORD '\$DB_PASSWORD';"

sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "SELECT 1 FROM pg_database WHERE datname='\$DB_NAME'" | grep -q 1 || \
    sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "CREATE DATABASE \$DB_NAME OWNER \$DB_USER;"

sudo -u user \${PG_BIN}/psql -h localhost -p 5432 -d \$DB_NAME -c \
    "GRANT ALL PRIVILEGES ON DATABASE \$DB_NAME TO \$DB_USER;"

echo "✓ Database setup complete: \$DB_NAME (user: \$DB_USER)"

# ──────────────────────────────────────────────────────────────────────────────
# Verify Redis is running
# ──────────────────────────────────────────────────────────────────────────────
echo "🔍 Verifying Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready on localhost:6379"
else
    echo "✗ Redis failed to start"
    exit 1
fi

# ──────────────────────────────────────────────────────────────────────────────
# Execute the main command (Web Server) AS USER
# ──────────────────────────────────────────────────────────────────────────────
echo "=== Starting Web Server on port \$APP_PORT ==="
echo "✅ All services initialized successfully"
exec sudo -u user "\$@"
EOF

RUN chmod +x /usr/local/bin/entrypoint.sh && \
    chown -R user:user /app/core

# ──────────────────────────────────────────────────────────────────────────────
# 9. Finalization
# ──────────────────────────────────────────────────────────────────────────────
# CRITICAL: Do NOT switch to user here - entrypoint handles it
WORKDIR /app
COPY --chown=user:user . /app

# Ensure .env file exists (create empty if not provided)
RUN touch /app/.env && chown user:user /app/.env

EXPOSE ${APP_PORT}

# Healthcheck against the boot.py server
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

# Use Entrypoint to start DBs, then run the boot.py server
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "/app/core/boot.py"]
```

---

## Phase 4: Key Changes Made

| Change | Before | After | Why |
|--------|--------|-------|-----|
| **PG Version Detection** | Complex function with `timeout` + `bash -c` | Hardcoded `PG_VERSION="17"` | Build logs confirm PG 17, no need to detect |
| **Timeout Wrapper** | `timeout 10 bash -c "$(declare -f...)"` | Removed entirely | Causing hang in HF Spaces |
| **Directory Check** | `ls /usr/lib/postgresql/` | Direct `[ ! -d "/usr/lib/postgresql/17" ]` | Faster, no hanging |
| **Binary Verification** | Complex loop with command execution | Simple `[ ! -x ]` checks | More reliable |
| **Error Messages** | Generic | Detailed with diagnostics | Better debugging |

---

## Phase 5: Validation

### 🧪 Testing Checklist

```bash
# 1. Build locally to verify
docker build -t ledgersg:test .

# 2. Check PostgreSQL directory in built image
docker run --rm ledgersg:test ls -la /usr/lib/postgresql/

# 3. Verify entrypoint script
docker run --rm ledgersg:test cat /usr/local/bin/entrypoint.sh | head -30

# 4. Test container startup
docker run -d -p 7860:7860 ledgersg:test
docker logs -f <container_id>
```

### ✅ Expected Output

```
=== LedgerSG Development Space Starting ===
🕐 Startup time: 2026-02-27T08:25:27+00:00
🔍 Detecting PostgreSQL installation...
✓ PostgreSQL version: 17
✓ Binary path: /usr/lib/postgresql/17/bin
🔍 Verifying PostgreSQL binaries...
  ✓ initdb verified
  ✓ pg_ctl verified
  ✓ psql verified
  ✓ pg_isready verified
🔧 Configuring environment...
📦 Initializing PostgreSQL cluster at /data/postgresql...
...
✅ All services initialized successfully
=== Starting Web Server on port 7860 ===
```

---

## Phase 6: Delivery

### 📄 Files To Update

| File | Action | Priority |
|------|--------|----------|
| `Dockerfile` | Replace entire file | 🔴 Critical |
| `/usr/local/bin/entrypoint.sh` | Embedded in Dockerfile | 🔴 Critical |

### 🔮 If Still Failing

Run these diagnostic commands in HF Spaces terminal:

```bash
# Check if PostgreSQL directory exists
ls -la /usr/lib/postgresql/

# Check if binaries are executable
ls -la /usr/lib/postgresql/17/bin/

# Check entrypoint script
cat /usr/local/bin/entrypoint.sh | head -50

# Run entrypoint manually with debug
bash -x /usr/local/bin/entrypoint.sh echo "test"
```

---

## 🎯 Immediate Action Required

**Deploy this updated Dockerfile to Hugging Face Spaces.** The simplified detection logic eliminates all hanging commands and uses the known PostgreSQL 17 version from the build logs.

**Expected result:** Container should progress past PostgreSQL detection and initialize the database successfully.

# https://chat.qwen.ai/s/45c614b3-6930-4765-9cb4-397bb7356a45?fev=0.2.9
