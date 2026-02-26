"""
Testing settings for LedgerSG API.

- In-memory SQLite (optional) or test PostgreSQL
- Fast password hashing
- Disabled throttling
- Synchronous Celery
"""

from .base import *

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

DEBUG = False

# Allow testserver for Django test client
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# =============================================================================
# DATABASE (Testing)
# =============================================================================

# Use the development database for tests (DDL-managed schema)
# Tests run in transactions that are rolled back
DATABASES["default"]["NAME"] = "ledgersg_dev"
# Disable test database creation - use existing database
DATABASES["default"]["TEST"] = {
    "NAME": "ledgersg_dev",  # Same as default to avoid DB creation
}
# Prevent Django from running migrations
MIGRATE = False

# =============================================================================
# PASSWORD HASHING (Fast for tests)
# =============================================================================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# =============================================================================
# CACHING (Testing)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# =============================================================================
# CELERY (Testing - Synchronous)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# THROTTLING (Testing - Disabled)
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# =============================================================================
# LOGGING (Testing - Minimal)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "WARNING",
    },
}

# =============================================================================
# CORS (Testing)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# SECURITY (Testing - Disabled)
# =============================================================================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =============================================================================
# SENTRY (Testing - Disabled)
# =============================================================================

SENTRY_DSN = None

# =============================================================================
# TEST RUNNER
# =============================================================================

TEST_RUNNER = "common.test_runner.SchemaTestRunner"

# Speed up tests
DEBUG_PROPAGATE_EXCEPTIONS = True
