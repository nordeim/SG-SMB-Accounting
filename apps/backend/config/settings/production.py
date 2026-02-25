"""
Production settings for LedgerSG API.

- Debug mode disabled
- HTTPS enforcement
- HSTS headers
- CSP headers
- Sentry error tracking
- Restricted CORS
"""

from .base import *

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

DEBUG = False

# Force HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# =============================================================================
# CORS SETTINGS (Production)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="https://app.ledgersg.sg",
)

# =============================================================================
# DATABASE (Production)
# =============================================================================

DATABASES["default"]["CONN_MAX_AGE"] = 60  # Persistent connections

# =============================================================================
# CACHING (Production)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# =============================================================================
# CELERY (Production)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = False

# =============================================================================
# LOGGING (Production)
# =============================================================================

LOGGING["handlers"]["file"] = {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": "/var/log/ledgersg/django.log",
    "maxBytes": 10485760,  # 10 MB
    "backupCount": 10,
    "formatter": "verbose",
}

LOGGING["loggers"]["django"]["handlers"] = ["console", "file"]
LOGGING["loggers"]["ledgersg"]["handlers"] = ["console", "file"]

# =============================================================================
# STATIC FILES (Production)
# =============================================================================

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =============================================================================
# ADMINS AND MANAGERS
# =============================================================================

ADMINS = [
    ("LedgerSG DevOps", config("ADMIN_EMAIL", default="ops@ledgersg.sg")),
]

MANAGERS = ADMINS

# =============================================================================
# ERROR REPORTING
# =============================================================================

# Only report errors via Sentry (configured in base.py)
# Disable email error reporting to avoid spam
SEND_BROKEN_LINK_EMAILS = False
