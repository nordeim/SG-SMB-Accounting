"""
Celery configuration for LedgerSG API.

Auto-discovers tasks from all apps/ modules.
"""

import os

from celery import Celery
from celery.signals import setup_logging

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Create Celery app
app = Celery("ledgersg")

# Configure from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery workers."""
    from logging.config import dictConfig
    from django.conf import settings
    dictConfig(settings.LOGGING)
