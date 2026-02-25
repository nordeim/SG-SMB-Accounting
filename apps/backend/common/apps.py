"""Django app configuration for common module."""

from django.apps import AppConfig
from django.db.models.signals import pre_migrate


def create_schemas(sender, **kwargs):
    """Create PostgreSQL schemas before migrations run."""
    from django.db import connection
    with connection.cursor() as cursor:
        schemas = ['core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit']
        for schema in schemas:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        cursor.execute(
            "GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit TO PUBLIC"
        )


class CommonConfig(AppConfig):
    """Configuration for common Django app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'common'
    verbose_name = 'Common'
    
    def ready(self):
        """Connect signals when app is ready."""
        pre_migrate.connect(create_schemas, sender=self)
