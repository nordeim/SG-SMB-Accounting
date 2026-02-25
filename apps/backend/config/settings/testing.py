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

# =============================================================================
# DATABASE (Testing)
# =============================================================================

DATABASES["default"]["NAME"] = config("TEST_DB_NAME", default="ledgersg_test")

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

TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Speed up tests
DEBUG_PROPAGATE_EXCEPTIONS = True
