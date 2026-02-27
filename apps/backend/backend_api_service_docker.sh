#!/bin/bash

# ============================================================================
# LedgerSG Backend API Service Management Script
# ============================================================================
# Purpose: Start, stop, and manage the LedgerSG Django API service
# Author: LedgerSG Development Team
# Version: 1.0.0
# Last Updated: 2026-02-27
# ============================================================================

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# ============================================================================
# CONFIGURATION
# ============================================================================

# Script configuration
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/apps/backend"
VENV_PATH="/opt/venv"

# Service configuration
SERVICE_NAME="ledgersg-api"
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="8000"
DEFAULT_WORKERS="4"
LOG_LEVEL="info"

# PID file location
PID_DIR="$HOME/.ledgersg"
PID_FILE="$PID_DIR/$SERVICE_NAME.pid"
LOG_DIR="$PID_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}============================================${NC}"
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d "$VENV_PATH" ]]; then
        log_error "Virtual environment not found at: $VENV_PATH"
        log_info "Please create the virtual environment first:"
        log_info "  python3 -m venv $VENV_PATH"
        log_info "  source $VENV_PATH/bin/activate"
        log_info "  pip install -e $BACKEND_DIR/[dev]"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    log_info "Activating virtual environment..."
    # shellcheck source=/dev/null
    source "$VENV_PATH/bin/activate"
    
    # Verify activation
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    log_success "Virtual environment activated: $VIRTUAL_ENV"
}

# Create necessary directories
create_directories() {
    mkdir -p "$PID_DIR"
    mkdir -p "$LOG_DIR"
}

# Check if service is running
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Get service PID
get_pid() {
    if [[ -f "$PID_FILE" ]]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

# Check if port is in use
is_port_in_use() {
    local port=$1
    if lsof -i ":$port" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Wait for service to start
wait_for_service() {
    local max_attempts=30
    local attempt=1
    local host=${1:-$DEFAULT_HOST}
    local port=${2:-$DEFAULT_PORT}
    
    log_info "Waiting for service to start on $host:$port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://$host:$port/api/v1/health/" | grep -q "200"; then
            log_success "Service is ready!"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Service failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Check database connection
check_database() {
    log_info "Checking database connection..."
    
    cd "$BACKEND_DIR" || exit 1
    
    if python -c "
import os
import django
from django.db import connection
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.service')
django.setup()

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        cursor.fetchone()
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        log_success "Database connection is OK"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

# ============================================================================
# SERVICE COMMANDS
# ============================================================================

# Start the service
start_service() {
    local host=${1:-$DEFAULT_HOST}
    local port=${2:-$DEFAULT_PORT}
    local workers=${3:-$DEFAULT_WORKERS}
    
    log_header "STARTING LEDGERSG API SERVICE"
    
    # Check if already running
    if is_running; then
        local pid
        pid=$(get_pid)
        log_warning "Service is already running (PID: $pid)"
        return 0
    fi
    
    # Check if port is in use
    if is_port_in_use "$port"; then
        log_error "Port $port is already in use"
        log_info "Check what's using the port:"
        log_info "  lsof -i :$port"
        return 1
    fi
    
    # Check virtual environment
    #check_venv
    
    # Activate virtual environment
    #activate_venv
    
    # Check database connection
    if ! check_database; then
        log_error "Database connection check failed"
        log_info "Please ensure PostgreSQL is running and the database exists"
        return 1
    fi
    
    # Create directories
    create_directories
    
    # Change to backend directory
    cd "$BACKEND_DIR" || exit 1
    
    log_info "Starting Django development server..."
    log_info "Host: $host"
    log_info "Port: $port"
    log_info "Workers: $workers"
    log_info "Log Level: $LOG_LEVEL"
    
    # Start the service in background
    if [[ "$workers" -eq 1 ]]; then
        # Development server (single process)
        DJANGO_SETTINGS_MODULE=config.settings.service nohup python manage.py runserver "$host:$port" \
            >"$LOG_DIR/api_service.log" 2>&1 &
        local pid=$!
        echo "$pid" >"$PID_FILE"
    else
        # Production server with gunicorn (if available)
        if command -v gunicorn >/dev/null 2>&1; then
            log_info "Using gunicorn with $workers workers"
            DJANGO_SETTINGS_MODULE=config.settings.service nohup gunicorn config.wsgi:application \
                --bind "$host:$port" \
                --workers "$workers" \
                --worker-class sync \
                --worker-tmp-dir /dev/shm \
                --max-requests 1000 \
                --max-requests-jitter 100 \
                --timeout 30 \
                --keep-alive 2 \
                --log-level "$LOG_LEVEL" \
                --access-logfile "$LOG_DIR/access.log" \
                --error-logfile "$LOG_DIR/error.log" \
                --pid "$PID_FILE" \
                --daemon
            local pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        else
            log_warning "gunicorn not found, falling back to development server"
            DJANGO_SETTINGS_MODULE=config.settings.service nohup python manage.py runserver "$host:$port" \
                >"$LOG_DIR/api_service.log" 2>&1 &
            local pid=$!
            echo "$pid" >"$PID_FILE"
        fi
    fi
    
    log_info "Service started with PID: $pid"
    
    # Wait for service to be ready
    if wait_for_service "$host" "$port"; then
        log_success "LedgerSG API service is running!"
        log_info "API URL: http://$host:$port/api/v1/"
        log_info "Health Check: http://$host:$port/api/v1/health/"
        log_info "Admin Panel: http://$host:$port/admin/"
        log_info "Logs: $LOG_DIR/api_service.log"
        return 0
    else
        log_error "Service failed to start properly"
        stop_service
        return 1
    fi
}

# Stop the service
stop_service() {
    log_header "STOPPING LEDGERSG API SERVICE"
    
    if ! is_running; then
        log_warning "Service is not running"
        return 0
    fi
    
    local pid
    pid=$(get_pid)
    
    log_info "Stopping service (PID: $pid)..."
    
    # Try graceful shutdown first
    if kill -TERM "$pid" 2>/dev/null; then
        log_info "Sent SIGTERM signal, waiting for graceful shutdown..."
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
            sleep 1
            ((count++))
        done
        
        # Check if process is still running
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "Graceful shutdown timed out, forcing termination..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    else
        log_warning "Could not send SIGTERM, forcing termination..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
    
    log_success "Service stopped"
}

# Restart the service
restart_service() {
    log_header "RESTARTING LEDGERSG API SERVICE"
    
    stop_service
    sleep 2
    start_service "$@"
}

# Show service status
show_status() {
    log_header "LEDGERSG API SERVICE STATUS"
    
    if is_running; then
        local pid
        pid=$(get_pid)
        local cmd
        cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
        local start_time
        start_time=$(ps -p "$pid" -o lstart= 2>/dev/null || echo "unknown")
        
        echo -e "${GREEN}●${NC} Service is running"
        echo "  PID: $pid"
        echo "  Command: $cmd"
        echo "  Started: $start_time"
        echo "  PID File: $PID_FILE"
        echo "  Log Directory: $LOG_DIR"
        
        # Try to get additional info if it's our Django service
        if [[ "$cmd" == *"python"* ]] || [[ "$cmd" == *"gunicorn"* ]]; then
            echo ""
            log_info "Service Details:"
            echo "  Project: LedgerSG API"
            echo "  Framework: Django 6.0.2"
            echo "  Database: PostgreSQL"
        fi
        
        # Check if health endpoint is responding
        if curl -s -o /dev/null -w "%{http_code}" "http://$DEFAULT_HOST:$DEFAULT_PORT/api/v1/health/" | grep -q "200"; then
            echo ""
            log_success "Health check: ✅ PASS"
        else
            echo ""
            log_warning "Health check: ❌ FAIL"
        fi
    else
        echo -e "${RED}●${NC} Service is not running"
        echo "  PID File: $PID_FILE"
        
        if [[ -f "$PID_FILE" ]]; then
            echo "  Warning: PID file exists but process is dead"
        fi
    fi
    
    echo ""
    echo "Configuration:"
    echo "  Service Name: $SERVICE_NAME"
    echo "  Default Host: $DEFAULT_HOST"
    echo "  Default Port: $DEFAULT_PORT"
    echo "  Backend Directory: $BACKEND_DIR"
    echo "  Virtual Environment: $VENV_PATH"
}

# Show logs
show_logs() {
    local lines=${1:-50}
    
    log_header "LEDGERSG API SERVICE LOGS"
    
    if [[ -f "$LOG_DIR/api_service.log" ]]; then
        log_info "Showing last $lines lines of service log:"
        echo ""
        tail -n "$lines" "$LOG_DIR/api_service.log"
    else
        log_warning "Log file not found: $LOG_DIR/api_service.log"
        log_info "Start the service to generate logs"
    fi
}

# Show help
show_help() {
    cat << EOF
LedgerSG Backend API Service Management Script

USAGE:
    $SCRIPT_NAME [COMMAND] [OPTIONS]

COMMANDS:
    start [HOST] [PORT] [WORKERS]    Start the API service
    stop                           Stop the API service
    restart [HOST] [PORT] [WORKERS]  Restart the API service
    status                         Show service status
    logs [LINES]                   Show service logs (default: 50 lines)
    help                          Show this help message

EXAMPLES:
    $SCRIPT_NAME start                          # Start with defaults (127.0.0.1:8000, 1 worker)
    $SCRIPT_NAME start 0.0.0.0 8000 4           # Start on all interfaces, port 8000, 4 workers
    $SCRIPT_NAME stop                           # Stop the service
    $SCRIPT_NAME restart 0.0.0.0 8000            # Restart on all interfaces, port 8000
    $SCRIPT_NAME status                         # Show current status
    $SCRIPT_NAME logs 100                       # Show last 100 log lines

DEFAULTS:
    Host: $DEFAULT_HOST
    Port: $DEFAULT_PORT
    Workers: $DEFAULT_WORKERS

FILES:
    PID File: $PID_FILE
    Log Directory: $LOG_DIR

REQUIREMENTS:
    - Python 3.12+
    - PostgreSQL database running
    - Virtual environment at $VENV_PATH
    - LedgerSG backend code at $BACKEND_DIR

EOF
}

# ============================================================================
# MAIN SCRIPT LOGIC
# ============================================================================

# Parse command line arguments
case "${1:-}" in
    start)
        start_service "${2:-}" "${3:-}" "${4:-}"
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service "${2:-}" "${3:-}" "${4:-}"
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-50}"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        log_error "No command specified"
        echo ""
        show_help
        exit 1
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
