# LedgerSG API Dockerfile
FROM python:3.13-trixie

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    curl wget zip unzip tar git rsync bash \
    ca-certificates \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip && pip install django-celery-beat 
RUN pip install -U django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter && \
    pip install psycopg[binary] celery[redis] redis py-moneyed pydantic weasyprint lxml python-decouple whitenoise gunicorn structlog sentry-sdk[django] pytest pytest-django pytest-cov pytest-xdist model-bakery factory-boy faker httpx ruff mypy django-stubs djangorestframework-stubs pre-commit ipython django-debug-toolbar django-extensions

# Install FastAPI/Next.js development dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    pydantic \
    python-multipart \
    sqlalchemy \
    alembic \
    aiofiles \
    jinja2

# Install Node.js 24.x LTS using the official NodeSource setup script
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    # Verify installation
    && node --version \
    && npm --version

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "4", "config.wsgi:application"]
