# 🔧 LedgerSG Hugging Face Space - Troubleshooting Guide

## Document Information

| Attribute | Value |
|-----------|-------|
| **Version** | 1.0.1 |
| **Last Updated** | 2026-02-28 |
| **Audience** | DevOps, Developers, System Administrators |
| **Scope** | Hugging Face Spaces container deployment |

---

## 📋 Table of Contents

1. [Quick Start - Common Issues](#-quick-start---common-issues)
2. [Service Status Diagnostics](#-service-status-diagnostics)
3. [PostgreSQL Issues](#-postgresql-issues)
4. [Backend API Issues](#-backend-api-issues)
5. [Frontend Issues](#-frontend-issues)
6. [Redis Issues](#-redis-issues)
7. [Database Schema Issues](#-database-schema-issues)
8. [Build Time Issues](#-build-time-issues)
9. [Runtime/Startup Issues](#-runtimestartup-issues)
10. [Log Analysis](#-log-analysis)
11. [Prevention & Best Practices](#-prevention--best-practices)
12. [Emergency Recovery Procedures](#-emergency-recovery-procedures)

---

## 🚀 Quick Start - Common Issues

### Issue Matrix

| Symptom | Likely Cause | Quick Fix | Priority |
|---------|-------------|-----------|----------|
| `✗ ERROR: PostgreSQL installation not found` | PG version detection failing | Check `/usr/lib/postgresql/` exists | 🔴 Critical |
| `ValueError: Unable to configure handler 'file'` | Django logging misconfigured | Use `config.settings.service` | 🔴 Critical |
| `permission denied to create database` | User lacks CREATEDB privilege | Add `CREATEDB` to role | 🔴 Critical |
| `Backend API: Not responding` | Gunicorn crashed or not started | Check `/tmp/backend.log` | 🟠 High |
| `Schema already exists` error | Schema applied on every restart | Add idempotency check | 🟠 High |
| `Frontend standalone build missing` | Build step failed or skipped | Verify `.next/standalone/server.js` | 🟠 High |
| Container marked unhealthy | Health check timeout too short | Increase `start-period` to 120s | 🟡 Medium |

### Emergency Commands

```bash
# Access Space terminal, then run:

# 1. Check all service status
curl http://localhost:7860/

# 2. View backend logs
curl http://localhost:7860/logs/backend?lines=100

# 3. Check PostgreSQL status
sudo -u user /usr/lib/postgresql/17/bin/pg_isready -h localhost -p 5432

# 4. Check Redis status
redis-cli ping

# 5. Check if processes are running
ps aux | grep -E "gunicorn|node|redis|postgres"

# 6. View container environment
curl http://localhost:7860/env
```

---

## 📊 Service Status Diagnostics

### Service Health Check Endpoint

```bash
# Full service status overview
curl -s http://localhost:7860/ | python3 -m json.tool

# Expected response:
{
  "service": "LedgerSG HF Space",
  "status": "alive",
  "timestamp": "2026-02-28T...",
  "services": {
    "frontend": {"status": "healthy", "status_code": 200, "url": "http://localhost:3000"},
    "backend": {"status": "healthy", "status_code": 200, "url": "http://localhost:8000/api/v1/health/"},
    "boot": {"status": "healthy", "port": 7860}
  }
}
```

### Individual Service Checks

```bash
# Backend API health
curl -sf http://localhost:8000/api/v1/health/ && echo "✅ Backend OK" || echo "❌ Backend FAILED"

# Frontend health
curl -sf http://localhost:3000 && echo "✅ Frontend OK" || echo "❌ Frontend FAILED"

# PostgreSQL health
sudo -u user /usr/lib/postgresql/17/bin/pg_isready -h localhost -p 5432 && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL FAILED"

# Redis health
redis-cli ping && echo "✅ Redis OK" || echo "❌ Redis FAILED"

# Boot monitor health
curl -sf http://localhost:7860/health && echo "✅ Monitor OK" || echo "❌ Monitor FAILED"
```

### Process Status Check

```bash
# Check all critical processes
echo "=== Process Status ==="
ps aux | grep -E "gunicorn|node|redis-server|postgres" | grep -v grep

# Check specific PIDs from startup logs
echo "=== Backend PID ==="
pgrep -f "gunicorn.*config.wsgi" || echo "❌ Backend not running"

echo "=== Frontend PID ==="
pgrep -f "node.*server.js" || echo "❌ Frontend not running"

echo "=== Redis PID ==="
pgrep -f "redis-server" || echo "❌ Redis not running"

echo "=== PostgreSQL PID ==="
pgrep -f "postgres" || echo "❌ PostgreSQL not running"
```

---

## 🐘 PostgreSQL Issues

### Issue #1: PostgreSQL Installation Not Found

**Error Message:**
```
✗ ERROR: PostgreSQL installation not found
✗ ERROR: PostgreSQL 17 directory not found at /usr/lib/postgresql/17
```

**Root Cause:**
- PostgreSQL package not installed in Dockerfile
- Version detection logic failing at runtime
- Directory structure different than expected

**Diagnostic Commands:**
```bash
# Check if PostgreSQL directory exists
ls -la /usr/lib/postgresql/

# Check installed PostgreSQL version
dpkg -l | grep postgresql

# Check psql binary location
which psql
ls -la /usr/lib/postgresql/*/bin/psql

# Check pg_config
which pg_config
pg_config --version
```

**Solutions:**

| Solution | When to Use | Command |
|----------|-------------|---------|
| Verify Dockerfile has postgresql package | Build time | Add `postgresql postgresql-contrib` to apt-get install |
| Hardcode version in entrypoint | Runtime | Set `PG_VERSION="17"` instead of detection |
| Check build logs | Debug | Review `container_build_log.txt` for installation errors |

**Prevention:**
```dockerfile
# In Dockerfile, add verification at build time:
RUN apt-get install -y postgresql postgresql-contrib \
    && if [ ! -d "/usr/lib/postgresql/17" ]; then echo "ERROR: PG 17 not installed" && exit 1; fi \
    && echo "✓ PostgreSQL 17 verified at build time"
```

---

### Issue #2: PostgreSQL Won't Start

**Error Message:**
```
✗ PostgreSQL failed to start within 30 seconds
📋 PostgreSQL log:
FATAL:  data directory "/data/postgresql" has invalid permissions
```

**Root Cause:**
- Data directory permissions incorrect
- Port already in use
- Insufficient disk space
- Configuration file errors

**Diagnostic Commands:**
```bash
# Check data directory permissions
ls -la /data/postgresql/

# Check PostgreSQL log
cat /tmp/postgres.log

# Check if port is in use
netstat -tulpn | grep 5432
ss -tulpn | grep 5432

# Check disk space
df -h /data

# Check configuration files
cat /data/postgresql/postgresql.conf | grep -E "port|listen_addresses"
cat /data/postgresql/pg_hba.conf
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Permission denied | `chown -R user:user /data/postgresql && chmod 700 /data/postgresql` |
| Port in use | `pkill -f postgres` then restart |
| Disk full | Clean up `/tmp` or expand storage |
| Config error | Review and fix `postgresql.conf` |

**Prevention:**
```bash
# In entrypoint.sh, ensure permissions before start:
mkdir -p $PGDATA
chown -R user:user $PGDATA
chmod 700 $PGDATA
mkdir -p /var/run/postgresql
chown -R user:user /var/run/postgresql
chmod 777 /var/run/postgresql
```

---

### Issue #3: Database Connection Failed

**Error Message:**
```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed:
FATAL:  role "ledgersg" does not exist
```

**Root Cause:**
- Database user not created
- Password incorrect
- Database doesn't exist
- pg_hba.conf blocking connections

**Diagnostic Commands:**
```bash
# Check if user exists
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d postgres -c "\du ledgersg"

# Check if database exists
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d postgres -c "\l"

# Test connection with password
PGPASSWORD=ledgersg_secret_to_change psql -h localhost -U ledgersg -d ledgersg_dev -c "SELECT 1;"

# Check pg_hba.conf
cat /data/postgresql/pg_hba.conf
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| User doesn't exist | Run entrypoint again or manually create: `CREATE ROLE ledgersg WITH LOGIN CREATEDB PASSWORD '...';` |
| Database doesn't exist | `CREATE DATABASE ledgersg_dev OWNER ledgersg;` |
| Authentication failed | Check pg_hba.conf allows md5/trust for localhost |
| Password wrong | Reset: `ALTER ROLE ledgersg WITH PASSWORD 'new_password';` |

---

## 🔌 Backend API Issues

### Issue #1: Backend Crashes on Startup

**Error Message:**
```
✗ Backend Gunicorn process died (attempt 3)
📋 Backend error log:
ValueError: Unable to configure handler 'file'
Unable to configure handler 'file'
```

**Root Cause:**
- Django logging configuration references non-existent directory
- Using `config.settings.production` instead of `config.settings.service`
- Log directory not created before Gunicorn starts

**Diagnostic Commands:**
```bash
# Check backend logs
curl http://localhost:7860/logs/backend?lines=100

# Check if log directory exists
ls -la /tmp/backend_logs/

# Check Django settings module
curl http://localhost:7860/env | grep DJANGO

# Check if Gunicorn process exists
pgrep -f "gunicorn.*config.wsgi"

# Check backend .env file
cat /app/apps/backend/.env
```

**Solutions:**

| Solution | File | Change |
|----------|------|--------|
| Use console logging | `config/settings/service.py` | Remove file handlers, use only console |
| Create log directory | `entrypoint.sh` | `mkdir -p /tmp/backend_logs` before Gunicorn |
| Set correct settings module | `entrypoint.sh` | `export DJANGO_SETTINGS_MODULE=config.settings.service` |
| Use stdout for logs | `entrypoint.sh` | `--access-logfile - --error-logfile -` |

**Fixed Configuration:**
```python
# config/settings/service.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

---

### Issue #2: Backend Health Check Fails

**Error Message:**
```
⚠ Backend API may not be fully ready (continuing)
📋 Last 50 lines of error log:
(Various errors)
```

**Root Cause:**
- Django migrations not run
- Database not accessible
- Missing dependencies
- Port already in use

**Diagnostic Commands:**
```bash
# Check health endpoint directly
curl -v http://localhost:8000/api/v1/health/

# Check if port is listening
nc -zv localhost 8000

# Check Django can connect to database
cd /app/apps/backend
source /opt/venv/bin/activate
python manage.py check --deploy

# Check for migration issues
python manage.py showmigrations

# Check Django settings
python manage.py diffsettings | grep -E "DATABASE|ALLOWED"
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Migrations pending | `python manage.py migrate --noinput` |
| Database connection failed | Check DB credentials in .env |
| Port in use | `pkill -f gunicorn` then restart |
| Missing dependencies | `pip install -r requirements.txt` |

---

### Issue #3: Backend Returns 500 Errors

**Error Message:**
```
Internal Server Error
500 Internal Server Error
```

**Root Cause:**
- Uncaught Python exceptions
- Database query errors
- Missing configuration
- Permission issues

**Diagnostic Commands:**
```bash
# Check backend error logs
curl http://localhost:7860/logs/backend_error?lines=100

# Check Django logs
tail -100 /tmp/backend.log

# Check database connectivity
cd /app/apps/backend
source /opt/venv/bin/activate
python -c "from django.core.management import execute_from_command_line; execute_from_command_line(['manage.py', 'check'])"

# Test API endpoint with verbose output
curl -v http://localhost:8000/api/v1/health/
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Database errors | Check migrations, connection string |
| Permission errors | Check file/directory permissions |
| Missing config | Verify all environment variables set |
| Code errors | Check application logs for stack trace |

---

## 🎨 Frontend Issues

### Issue #1: Frontend Build Missing

**Error Message:**
```
✗ ERROR: Frontend standalone build missing!
ERROR: Frontend standalone build missing!
ls -la .next/
```

**Root Cause:**
- Next.js build failed during Docker build
- Standalone output not configured
- Build step skipped or failed

**Diagnostic Commands:**
```bash
# Check if standalone build exists
ls -la /app/apps/web/.next/standalone/

# Check server.js exists
ls -la /app/apps/web/.next/standalone/server.js

# Check static files
ls -la /app/apps/web/.next/standalone/.next/static/chunks/

# Check Next.js config
cat /app/apps/web/next.config.js | grep -A5 "output"
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Standalone not configured | Add `output: 'standalone'` to next.config.js |
| Build failed | Check Node.js version, npm install |
| Static files missing | Copy `.next/static` to `.next/standalone/.next/static` |
| Build step skipped | Ensure `npm run build` runs in Dockerfile |

**Prevention:**
```dockerfile
# In Dockerfile:
RUN cd /app/apps/web && \
    npm install && \
    npm run clean && \
    NEXT_OUTPUT_MODE=standalone NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build:server && \
    # Verify build
    if [ ! -f ".next/standalone/server.js" ]; then echo "ERROR: Build failed" && exit 1; fi
```

---

### Issue #2: Frontend Won't Start

**Error Message:**
```
⚠ Frontend may not be ready (continuing)
📋 Frontend log:
Error: Cannot find module '/app/apps/web/.next/standalone/server.js'
```

**Root Cause:**
- Standalone build incomplete
- Node.js version mismatch
- Missing dependencies
- Port already in use

**Diagnostic Commands:**
```bash
# Check frontend logs
curl http://localhost:7860/logs/frontend?lines=100

# Check if process is running
pgrep -f "node.*server.js"

# Check port availability
nc -zv localhost 3000

# Check Node.js version
node --version

# Check package.json dependencies
cat /app/apps/web/package.json | grep -A20 "dependencies"
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Missing server.js | Rebuild frontend: `npm run build:server` |
| Port in use | `pkill -f "node.*server.js"` then restart |
| Node version wrong | Ensure Node 24.x installed in Dockerfile |
| Dependencies missing | `npm install` in web directory |

---

### Issue #3: Frontend Can't Connect to Backend

**Error Message:**
```
Network Error
Failed to fetch
API endpoint not reachable
```

**Root Cause:**
- `NEXT_PUBLIC_API_URL` not configured
- Backend not running
- CORS not configured
- Network isolation in container

**Diagnostic Commands:**
```bash
# Check environment variables
curl http://localhost:7860/env | grep NEXT_PUBLIC

# Check backend is running
curl http://localhost:8000/api/v1/health/

# Test from frontend container
curl http://localhost:8000/api/v1/health/

# Check CORS headers
curl -I -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/health/
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Wrong API URL | Set `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| Backend not running | Start backend service first |
| CORS blocked | Add `http://localhost:3000` to `CORS_ALLOWED_ORIGINS` |
| Network issue | Use localhost, not container hostname |

---

## 📦 Redis Issues

### Issue #1: Redis Won't Start

**Error Message:**
```
✗ Redis failed to start
```

**Root Cause:**
- Port already in use
- Permission issues
- Configuration error

**Diagnostic Commands:**
```bash
# Check if Redis is running
redis-cli ping

# Check port
netstat -tulpn | grep 6379

# Check Redis logs
cat /var/log/redis/redis-server.log 2>/dev/null || echo "No log file"

# Try starting manually
redis-server --daemonize yes
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Port in use | `pkill redis-server` then restart |
| Permission denied | Run as user with proper permissions |
| Config error | Check redis.conf or use defaults |

---

### Issue #2: Redis Connection Failed

**Error Message:**
```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**Root Cause:**
- Redis not running
- Wrong port
- Firewall blocking
- Authentication required

**Diagnostic Commands:**
```bash
# Test connection
redis-cli ping

# Check Redis info
redis-cli info

# Check if port listening
nc -zv localhost 6379

# Check process
ps aux | grep redis
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Redis not running | `redis-server --daemonize yes` |
| Wrong port | Update `REDIS_URL` environment variable |
| Auth required | Add password to `REDIS_URL` |

---

## 🗄️ Database Schema Issues

### Issue #1: Schema Applied on Every Restart

**Error Message:**
```
psql:/app/apps/backend/database_schema.sql:78: NOTICE: schema "audit" does not exist, skipping
DROP SCHEMA
```

**Root Cause:**
- No idempotency check in entrypoint
- Schema file has `DROP SCHEMA IF EXISTS... CASCADE`
- Data loss on every container restart

**Diagnostic Commands:**
```bash
# Check table count
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d ledgersg_dev -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('core','coa','gst','journal','invoicing','banking','audit');"

# Check schema version table
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d ledgersg_dev -c \
  "SELECT * FROM core.schema_version ORDER BY applied_at DESC LIMIT 1;"

# Check if data exists
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d ledgersg_dev -c \
  "SELECT COUNT(*) FROM core.organisation;"
```

**Solutions:**

| Solution | Implementation |
|----------|----------------|
| Add table count check | `TABLE_COUNT=$(psql -c "SELECT COUNT(*)...")` |
| Add schema version tracking | Create `core.schema_version` table |
| Skip if tables exist | `if [ "$TABLE_COUNT" -eq "0" ]; then apply_schema; fi` |
| Use Django migrations | `python manage.py migrate --noinput` |

**Fixed Implementation:**
```bash
# In entrypoint.sh:
TABLE_COUNT=$(sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d ${DB_NAME} -t -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('core','coa','gst','journal','invoicing','banking','audit');" 2>/dev/null | tr -d ' ' || echo "0")

if [ -z "$TABLE_COUNT" ] || [ "$TABLE_COUNT" -eq "0" ]; then
    echo "  → Applying database schema (first run)..."
    sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d ${DB_NAME} -f /app/apps/backend/database_schema.sql
else
    echo "  ✓ Database schema already exists ($TABLE_COUNT tables found)"
    echo "  ℹ️  Skipping schema application to preserve data"
fi
```

---

### Issue #2: Permission Denied to Create Database

**Error Message:**
```
createdb: error: database creation failed: ERROR: permission denied to create database
```

**Root Cause:**
- Database user lacks `CREATEDB` privilege
- User created without proper grants

**Diagnostic Commands:**
```bash
# Check user privileges
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d postgres -c "\du ledgersg"

# Check if CREATEDB attribute set
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d postgres -c \
  "SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname='ledgersg';"
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Missing CREATEDB | `ALTER ROLE ledgersg WITH CREATEDB;` |
| User doesn't exist | `CREATE ROLE ledgersg WITH LOGIN CREATEDB PASSWORD '...';` |
| Wrong user | Ensure using correct database user |

**Prevention:**
```bash
# In entrypoint.sh, create user with CREATEDB:
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
  "CREATE ROLE ${DB_USER} WITH LOGIN CREATEDB PASSWORD '${DB_PASSWORD}';"
```

---

## 🔨 Build Time Issues

### Issue #1: Build Hangs Indefinitely

**Error Message:**
```
[Build stuck at npm install or similar]
```

**Root Cause:**
- Background process in RUN command (never exits)
- Network timeout during package download
- Interactive prompt waiting for input

**Solutions:**

| Problem | Solution |
|---------|----------|
| Background process | Never use `&` or `nohup` in RUN commands |
| Network timeout | Add `--network-timeout` to npm commands |
| Interactive prompt | Add `DEBIAN_FRONTEND=noninteractive` |

**Prevention:**
```dockerfile
# WRONG - will hang:
RUN npm run build && nohup npm run serve &

# CORRECT - build only:
RUN npm run build
```

---

### Issue #2: Build Fails with Permission Errors

**Error Message:**
```
EACCES: permission denied, mkdir '/app/apps/web/node_modules'
```

**Root Cause:**
- Running npm as wrong user
- Directory ownership incorrect
- Filesystem read-only

**Solutions:**

| Problem | Solution |
|---------|----------|
| Wrong user | `chown -R user:user /app/apps/web` |
| Directory permissions | `chmod -R 755 /app/apps/web` |
| Read-only filesystem | Check container storage |

---

## ⚡ Runtime/Startup Issues

### Issue #1: Container Marked Unhealthy

**Error Message:**
```
Health check failed: unhealthy
```

**Root Cause:**
- Health check timeout too short
- Services take longer than expected to start
- Health endpoint not responding

**Diagnostic Commands:**
```bash
# Check health endpoint manually
curl -f http://localhost:7860/health

# Check startup time
grep "Startup time" /tmp/entrypoint.log

# Check which service is failing
curl http://localhost:7860/ | python3 -m json.tool
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Timeout too short | Increase `--start-period` to 120s |
| Wrong endpoint | Check health endpoint path |
| Service not ready | Add startup delays or retries |

**Fixed HEALTHCHECK:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:7860/health 2>/dev/null || exit 1
```

---

### Issue #2: Services Start But Then Crash

**Error Message:**
```
Process exited with code 1
Container restarting continuously
```

**Root Cause:**
- Out of memory (OOM)
- Uncaught exceptions
- Resource limits exceeded

**Diagnostic Commands:**
```bash
# Check memory usage
free -h

# Check process status
ps aux --sort=-%mem | head -10

# Check dmesg for OOM
dmesg | grep -i "killed process"

# Check container logs
docker logs --tail 100 <container_id>
```

**Solutions:**

| Problem | Solution |
|---------|----------|
| Out of memory | Increase container memory limit |
| Exception | Check application logs for stack trace |
| Resource limit | Adjust Docker resource limits |

---

## 📝 Log Analysis

### Log File Locations

| Service | Log File | Access Command |
|---------|----------|----------------|
| Backend API | `/tmp/backend.log` | `curl http://localhost:7860/logs/backend` |
| Frontend | `/tmp/frontend.log` | `curl http://localhost:7860/logs/frontend` |
| PostgreSQL | `/tmp/postgres.log` | `curl http://localhost:7860/logs/postgres` |
| Redis | Systemd journal | `redis-cli ping` (no file log) |
| Entrypoint | stdout/stderr | Container logs |

### Common Error Patterns

| Error Pattern | Meaning | Action |
|--------------|---------|--------|
| `ValueError: Unable to configure handler` | Django logging misconfigured | Use console logging |
| `permission denied` | File/directory permissions | Check ownership with `ls -la` |
| `connection refused` | Service not running | Start the service |
| `role does not exist` | Database user missing | Create user or check credentials |
| `database does not exist` | Database not created | Create database or run migrations |
| `address already in use` | Port conflict | Kill process or change port |
| `no space left on device` | Disk full | Clean up or expand storage |

### Log Analysis Commands

```bash
# Get last N lines of any service log
curl "http://localhost:7860/logs/{service}?lines=100"

# Search for errors in backend log
curl http://localhost:7860/logs/backend | grep -i "error"

# Search for specific error pattern
curl http://localhost:7860/logs/backend | grep -i "ValueError"

# Get environment variables for debugging
curl http://localhost:7860/env

# Full service status
curl http://localhost:7860/ | python3 -m json.tool
```

---

## 🛡️ Prevention & Best Practices

### Pre-Deployment Checklist

- [ ] PostgreSQL version verified in Dockerfile
- [ ] Backend logging uses console-only (no file handlers)
- [ ] Schema application is idempotent (checks table count)
- [ ] Log paths match between entrypoint and boot.py
- [ ] Health check timeout sufficient (120s start-period)
- [ ] All environment variables documented
- [ ] Default passwords changed from Dockerfile
- [ ] Build steps don't include background processes

### Monitoring Recommendations

```bash
# Add to your deployment monitoring:

# 1. Service health check (every 5 minutes)
curl -f http://localhost:7860/health

# 2. Database connection check (every 5 minutes)
sudo -u user /usr/lib/postgresql/17/bin/pg_isready -h localhost -p 5432

# 3. Disk space monitoring (daily)
df -h /data /tmp

# 4. Log rotation (weekly)
# Configure logrotate for /tmp/*.log files
```

### Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Dump database
sudo -u user /usr/lib/postgresql/17/bin/pg_dump \
    -h localhost -U ledgersg ledgersg_dev \
    > "$BACKUP_DIR/ledgersg_${DATE}.sql"

# Keep last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/ledgersg_${DATE}.sql"
```

---

## 🚨 Emergency Recovery Procedures

### Procedure #1: Complete Service Restart

```bash
# 1. Access Space terminal

# 2. Stop all services
pkill -f gunicorn
pkill -f "node.*server.js"
pkill redis-server
sudo -u user /usr/lib/postgresql/17/bin/pg_ctl -D /data/postgresql stop

# 3. Clear temporary files
rm -f /tmp/*.log
rm -f /tmp/backend_logs/*

# 4. Restart container (from HF Spaces UI)
# Or if you have docker access:
docker restart <container_id>

# 5. Monitor startup
docker logs -f <container_id>
```

### Procedure #2: Database Recovery

```bash
# 1. Check database status
sudo -u user /usr/lib/postgresql/17/bin/pg_isready -h localhost -p 5432

# 2. If database corrupted, restore from backup
sudo -u user /usr/lib/postgresql/17/bin/dropdb -h localhost ledgersg_dev
sudo -u user /usr/lib/postgresql/17/bin/createdb -h localhost -O ledgersg ledgersg_dev
sudo -u user /usr/lib/postgresql/17/bin/psql -h localhost -d ledgersg_dev -f /data/backups/ledgersg_YYYYMMDD.sql

# 3. Restart services
# (Container will auto-restart services)
```

### Procedure #3: Log Collection for Support

```bash
# Collect all diagnostic information

# 1. Service status
curl http://localhost:7860/ > /tmp/diag_services.json

# 2. Environment variables
curl http://localhost:7860/env > /tmp/diag_env.json

# 3. All logs
curl "http://localhost:7860/logs/backend?lines=500" > /tmp/diag_backend.log
curl "http://localhost:7860/logs/frontend?lines=500" > /tmp/diag_frontend.log
curl "http://localhost:7860/logs/postgres?lines=500" > /tmp/diag_postgres.log

# 4. Process list
ps aux > /tmp/diag_processes.txt

# 5. Disk usage
df -h > /tmp/diag_disk.txt

# 6. Compress and download
tar -czf ledgersg_diagnostic_$(date +%Y%m%d_%H%M%S).tar.gz /tmp/diag_*
```

---

## 📞 Support Resources

### Internal Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Project Architecture | System overview | `Project_Architecture_Document.md` |
| API CLI Guide | API usage | `API_CLI_Usage_Guide.md` |
| Dockerfile Analysis | Build configuration | `hf_space_dockerfile_analysis.md` |
| This Guide | Troubleshooting | `TROUBLESHOOTING.md` |

### External Resources

| Resource | URL |
|----------|-----|
| Django Documentation | https://docs.djangoproject.com/ |
| Next.js Documentation | https://nextjs.org/docs |
| PostgreSQL Documentation | https://www.postgresql.org/docs/ |
| Hugging Face Spaces | https://huggingface.co/docs/hub/spaces |
| Docker Documentation | https://docs.docker.com/ |

### Contact & Escalation

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Build failures | DevOps Team | 4 hours |
| Runtime errors | Backend Team | 2 hours |
| Data loss | Database Admin | 1 hour |
| Security issues | Security Team | 30 minutes |

---

## 📊 Quick Reference Tables

### Port Mapping

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Boot Monitor | 7860 | HTTP | Health checks, logs, status |
| Frontend | 3000 | HTTP | Next.js web application |
| Backend API | 8000 | HTTP | Django REST API |
| PostgreSQL | 5432 | TCP | Database server |
| Redis | 6379 | TCP | Cache/session store |

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_PORT` | 7860 | Boot monitor port |
| `FRONTEND_PORT` | 3000 | Frontend port |
| `BACKEND_PORT` | 8000 | Backend API port |
| `DB_NAME` | ledgersg_dev | Database name |
| `DB_USER` | ledgersg | Database user |
| `DB_PASSWORD` | ledgersg_secret_to_change | Database password |
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5432 | Database port |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Frontend API endpoint |

### Critical File Paths

| Path | Purpose |
|------|---------|
| `/app/core/boot.py` | Boot monitor server |
| `/usr/local/bin/entrypoint.sh` | Container entrypoint |
| `/data/postgresql/` | PostgreSQL data directory |
| `/tmp/backend.log` | Backend application logs |
| `/tmp/frontend.log` | Frontend application logs |
| `/tmp/postgres.log` | PostgreSQL server logs |
| `/app/apps/backend/.env` | Backend environment |
| `/app/apps/backend/config/settings/service.py` | Django service settings |

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.1 | 2026-02-28 | Initial release with comprehensive troubleshooting |
| 1.0.0 | 2026-02-27 | Draft version |

---

**Document End**

*This troubleshooting guide is maintained as part of the LedgerSG project documentation. For updates or corrections, please submit a pull request to the main repository.*

# https://chat.qwen.ai/s/45c614b3-6930-4765-9cb4-397bb7356a45?fev=0.2.9
