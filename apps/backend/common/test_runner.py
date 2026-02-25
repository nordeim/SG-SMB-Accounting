"""Custom test runner that creates schemas before running tests."""

from django.test.runner import DiscoverRunner
from django.db import connections


class SchemaTestRunner(DiscoverRunner):
    """Test runner that creates PostgreSQL schemas before running tests."""
    
    def setup_databases(self, **kwargs):
        """Set up test databases with schema creation."""
        # Create schemas in the test database
        for connection in connections.all():
            with connection.cursor() as cursor:
                schemas = ['core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit']
                for schema in schemas:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
                cursor.execute(
                    "GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit TO PUBLIC"
                )
        
        # Continue with normal database setup
        return super().setup_databases(**kwargs)
