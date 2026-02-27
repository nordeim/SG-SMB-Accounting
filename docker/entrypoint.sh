#!/bin/bash
set -e
echo "=== LedgerSG Development Space Starting ==="

# ─────────────────────────────────────────────────────────────────
# CRITICAL FIX: Detect PostgreSQL version and set binary path
# ─────────────────────────────────────────────────────────────────
# PostgreSQL binaries are in version-specific directories on Debian
# We must find the correct path rather than relying on PATH

PG_VERSION=$(ls /usr/lib/postgresql/ | head -1)
if [ -z "$PG_VERSION" ]; then
    echo "✗ ERROR: PostgreSQL installation not found"
    exit 1
fi

PG_BIN="/usr/lib/postgresql/${PG_VERSION}/bin"
echo "✓ PostgreSQL version: ${PG_VERSION}"
echo "✓ Binary path: ${PG_BIN}"

# Verify critical binaries exist
for cmd in initdb pg_ctl psql; do
    if [ ! -f "${PG_BIN}/${cmd}" ]; then
        echo "✗ ERROR: ${cmd} not found at ${PG_BIN}/${cmd}"
        exit 1
    fi
done

# ─────────────────────────────────────────────────────────────────
# Environment Setup
# ─────────────────────────────────────────────────────────────────
# Ensure PostgreSQL data directory exists and is owned by user
mkdir -p $PGDATA
chown -R user:user $PGDATA
chmod 700 $PGDATA

# Ensure PostgreSQL socket directory is accessible
mkdir -p /var/run/postgresql
chown -R user:user /var/run/postgresql
chmod 777 /var/run/postgresql

# ─────────────────────────────────────────────────────────────────
# Initialize Postgres if not exists (as user via sudo)
# ─────────────────────────────────────────────────────────────────
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "Initializing PostgreSQL cluster at $PGDATA..."
    
    # CRITICAL: Use full path to initdb
    sudo -u user ${PG_BIN}/initdb -D $PGDATA
    
    # Configure PostgreSQL for password authentication
    echo "Configuring PostgreSQL authentication..."
    
    # Allow local connections with password
    cat >> $PGDATA/pg_hba.conf << 'PGHBA'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
PGHBA
    
    # Configure listen addresses
    echo "listen_addresses = 'localhost'" >> $PGDATA/postgresql.conf
    echo "port = 5432" >> $PGDATA/postgresql.conf
fi

# ─────────────────────────────────────────────────────────────────
# Start Redis in background
# ─────────────────────────────────────────────────────────────────
echo "Starting Redis on port 6379..."
redis-server --daemonize yes

# ─────────────────────────────────────────────────────────────────
# Start Postgres in background (as user via sudo)
# ─────────────────────────────────────────────────────────────────
echo "Starting PostgreSQL on port 5432..."
# CRITICAL: Use full path to pg_ctl
sudo -u user ${PG_BIN}/pg_ctl -D $PGDATA -l /tmp/postgres.log start

# ─────────────────────────────────────────────────────────────────
# Wait for Postgres to be ready
# ─────────────────────────────────────────────────────────────────
echo "Waiting for PostgreSQL to accept connections..."
for i in {1..30}; do
    # CRITICAL: Use full path to pg_isready
    if sudo -u user ${PG_BIN}/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start within 30 seconds"
        cat /tmp/postgres.log
        exit 1
    fi
    sleep 1
done

# ─────────────────────────────────────────────────────────────────
# Create database user and database if not exists
# ─────────────────────────────────────────────────────────────────
echo "Setting up database user and database..."

# CRITICAL: Use full path to psql
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || \
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';"

sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 || \
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d postgres -c \
    "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Grant all privileges
sudo -u user ${PG_BIN}/psql -h localhost -p 5432 -d $DB_NAME -c \
    "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "✓ Database setup complete: $DB_NAME (user: $DB_USER)"

# ─────────────────────────────────────────────────────────────────
# Verify Redis is running
# ─────────────────────────────────────────────────────────────────
echo "Verifying Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is ready on localhost:6379"
else
    echo "✗ Redis failed to start"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────
# Execute the main command (Web Server) AS USER
# ─────────────────────────────────────────────────────────────────
echo "=== Starting Web Server on port $APP_PORT ==="
exec sudo -u user "$@"
