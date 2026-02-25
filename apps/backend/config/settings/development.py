"""
Development settings for LedgerSG API.

- Debug mode enabled
- Console email backend
- CORS allow-all for local development
- Debug toolbar enabled
- Expanded logging
"""

from .base import *

# =============================================================================
# DEBUG SETTINGS
# =============================================================================

DEBUG = True

# =============================================================================
# ALLOWED HOSTS
# =============================================================================

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

# =============================================================================
# EMAIL BACKEND
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# CORS SETTINGS (Development - Allow All)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# DATABASE (Development)
# =============================================================================

# Use local PostgreSQL or Docker
DATABASES["default"]["NAME"] = config("DB_NAME", default="ledgersg_dev")
DATABASES["default"]["USER"] = config("DB_USER", default="ledgersg")
DATABASES["default"]["PASSWORD"] = config("DB_PASSWORD", default="ledgersg")
DATABASES["default"]["HOST"] = config("DB_HOST", default="localhost")

# =============================================================================
# LOGGING (Development - Debug Level)
# =============================================================================

LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["ledgersg"]["level"] = "DEBUG"

# =============================================================================
# DEBUG TOOLBAR (Optional)
# =============================================================================

if config("DEBUG_TOOLBAR", default=True, cast=bool):
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

# =============================================================================
# CELERY (Development - Synchronous)
# =============================================================================

# Run tasks synchronously in development
CELERY_TASK_ALWAYS_EAGER = config("CELERY_ALWAYS_EAGER", default=True, cast=bool)

# =============================================================================
# JWT (Development - Longer Lifetimes)
# =============================================================================

SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(hours=1)
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = timedelta(days=30)

# =============================================================================
# SHELL PLUS (Django Extensions)
# =============================================================================

SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True

# =============================================================================
# SECURITY (Development - Relaxed)
# =============================================================================

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
