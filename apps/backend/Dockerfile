# LedgerSG API Dockerfile
FROM python:3.13-trixie

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive \
    APP_PORT=7860 \
    XDG_RUNTIME_DIR=/tmp/runtime-user \
    PATH="/home/user/.local/bin:/usr/local/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash coreutils ca-certificates cron curl wget git less procps sudo vim tar wget zip unzip tmux openssh-client rsync \
    build-essential gcc gnupg cmake pkg-config \
    libpq-dev libjson-c-dev libssl-dev libwebsockets-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    # Database Servers
    postgresql postgresql-contrib redis-server \
    # Cleanup
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN cd /usr/bin && wget https://github.com/nordeim/HF-Space/raw/refs/heads/main/bun
RUN cd /usr/bin && wget https://github.com/nordeim/HF-Space/raw/refs/heads/main/uv
RUN cd /usr/bin && wget https://github.com/nordeim/HF-Space/raw/refs/heads/main/uvx
RUN chmod a+x /usr/bin/bun /usr/bin/uv*

# Install Python dependencies
RUN pip install --upgrade pip && pip install django-celery-beat 
RUN pip install -U django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter && \
    pip install psycopg[binary] celery[redis] redis py-moneyed pydantic weasyprint lxml python-decouple whitenoise gunicorn structlog sentry-sdk[django] pytest pytest-django pytest-cov pytest-xdist model-bakery factory-boy faker httpx ruff mypy django-stubs djangorestframework-stubs pre-commit ipython django-debug-toolbar django-extensions

# Install FastAPI/Next.js development dependencies
RUN pip install fastapi uvicorn httpx pydantic python-multipart sqlalchemy alembic aiofiles jinja2

# Install Node.js 24.x LTS using the official NodeSource setup script
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    # Verify installation
    && node --version \
    && npm --version

# Create non-root user (Hugging Face requirement)
RUN groupadd -g 1000 user && \
    useradd -m -u 1000 -g user -d /home/user user && \
    # Limited sudo for cron only
    echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user && \
    # Create directories
    mkdir -p ${XDG_RUNTIME_DIR} /data /app && \
    chown -R user:user ${XDG_RUNTIME_DIR} /data /app

# Install global npm packages
RUN npm install -g --omit=dev \
    pnpm@latest \
    vite@latest \
    vitest@latest \

# CRITICAL: Install Playwright browsers AS ROOT, BEFORE switching user
# Install browsers first (without trying to get system deps)
RUN npx playwright install chromium
# Then install the system dependencies Playwright needs
RUN npx playwright install-deps chromium

# Switch to non-root user
USER user
WORKDIR /app

# Copy application code
COPY --chown=user:user . /app

# Expose ports
EXPOSE ${APP_PORT}

# 13. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT} || exit 1

# Run gunicorn
#CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4", "config.wsgi:application"]
