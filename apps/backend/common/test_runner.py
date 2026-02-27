"""Custom test runner that creates schemas before running tests."""

import os
from django.test.runner import DiscoverRunner
from django.db import connections, connection


class SchemaTestRunner(DiscoverRunner):
    """Test runner that creates PostgreSQL schemas and loads the full SQL schema before running tests."""
    
    def setup_databases(self, **kwargs):
        """Set up test databases with schema creation and table loading."""
        # Create schemas in the test database
        for conn in connections.all():
            with conn.cursor() as cursor:
                schemas = ['core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit']
                for schema in schemas:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
                cursor.execute(
                    "GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit TO PUBLIC"
                )
                
                # Load the full SQL schema
                schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database_schema.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r') as f:
                        sql = f.read()
                        # Execute the SQL. Note: this might be slow for large schemas.
                        cursor.execute(sql)
        
        # Continue with normal database setup
        return super().setup_databases(**kwargs)
