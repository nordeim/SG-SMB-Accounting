"""
Custom PostgreSQL database backend for LedgerSG.

Extends the default PostgreSQL backend to configure psycopg3 connection options
and set the search_path to include all LedgerSG schemas.
"""

from django.db.backends.postgresql import base


class DatabaseWrapper(base.DatabaseWrapper):
    """
    Custom PostgreSQL database wrapper.
    
    Configures connection options for:
    - Statement timeout
    - Application name
    - Search path (includes all LedgerSG schemas)
    """
    
    def get_connection_params(self):
        """
        Get connection parameters with custom options.
        """
        conn_params = super().get_connection_params()
        
        # Set application name for database monitoring
        conn_params.setdefault("options", "")
        
        # Add search_path to include all LedgerSG schemas
        # This allows queries without schema qualification
        search_path_option = "-c search_path=core,coa,gst,journal,invoicing,banking,audit,public"
        
        if conn_params["options"]:
            conn_params["options"] += f" {search_path_option}"
        else:
            conn_params["options"] = search_path_option
        
        # Set statement timeout (30 seconds for web requests)
        conn_params["options"] += " -c statement_timeout=30000"
        
        # Set application name for pg_stat_activity
        conn_params["options"] += " -c application_name=ledgersg_api"
        
        return conn_params
    
    def init_connection_state(self):
        """
        Initialize connection state.
        
        Called when a new connection is established.
        """
        super().init_connection_state()
        
        # Any additional connection initialization can go here
        # For example, setting session-specific configuration
        pass
