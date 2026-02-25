"""
Custom PostgreSQL database backend for LedgerSG.

Configures search_path for multi-schema architecture.
"""

from django.db.backends.postgresql import base


class DatabaseWrapper(base.DatabaseWrapper):
    """PostgreSQL backend with schema configuration."""
    
    def get_connection_params(self):
        """Get connection parameters with schema configuration."""
        conn_params = super().get_connection_params()
        conn_params.setdefault("options", "")
        
        # Set search path for multi-schema architecture
        search_path_option = "-c search_path=core,coa,gst,journal,invoicing,banking,audit,public"
        if conn_params["options"]:
            conn_params["options"] += f" {search_path_option}"
        else:
            conn_params["options"] = search_path_option
            
        # Add timeout and application name
        conn_params["options"] += " -c statement_timeout=30000"
        conn_params["options"] += " -c application_name=ledgersg_api"
        
        return conn_params
    
    def get_new_connection(self, conn_params):
        """Create new connection and ensure schemas exist."""
        # Try to connect with schema configuration
        try:
            return super().get_new_connection(conn_params)
        except Exception:
            # If connection fails due to missing schemas, connect without search_path
            # and create schemas
            temp_params = conn_params.copy()
            temp_params["options"] = "-c statement_timeout=30000 -c application_name=ledgersg_api"
            conn = super().get_new_connection(temp_params)
            
            # Create schemas
            with conn.cursor() as cursor:
                schemas = ['core', 'coa', 'gst', 'journal', 'invoicing', 'banking', 'audit']
                for schema in schemas:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
                cursor.execute(
                    "GRANT USAGE ON SCHEMA core, coa, gst, journal, invoicing, banking, audit TO PUBLIC"
                )
            conn.commit()
            conn.close()
            
            # Now connect with full search_path
            return super().get_new_connection(conn_params)
