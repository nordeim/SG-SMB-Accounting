"""Create PostgreSQL schemas for multi-tenant architecture."""

from django.db import migrations


class Migration(migrations.Migration):
    """Initial migration to create database schemas."""
    
    initial = True
    
    dependencies = []
    
    operations = [
        migrations.RunSQL(
            sql="""
                CREATE SCHEMA IF NOT EXISTS core;
                CREATE SCHEMA IF NOT EXISTS coa;
                CREATE SCHEMA IF NOT EXISTS gst;
                CREATE SCHEMA IF NOT EXISTS journal;
                CREATE SCHEMA IF NOT EXISTS invoicing;
                CREATE SCHEMA IF NOT EXISTS banking;
                CREATE SCHEMA IF NOT EXISTS audit;
                GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit TO PUBLIC;
            """,
            reverse_sql="""
                DROP SCHEMA IF EXISTS core CASCADE;
                DROP SCHEMA IF EXISTS coa CASCADE;
                DROP SCHEMA IF EXISTS gst CASCADE;
                DROP SCHEMA IF EXISTS journal CASCADE;
                DROP SCHEMA IF EXISTS invoicing CASCADE;
                DROP SCHEMA IF EXISTS banking CASCADE;
                DROP SCHEMA IF EXISTS audit CASCADE;
            """
        ),
    ]
