"""
Database router for LedgerSG.

Routes reads to replica (future) and writes to primary.
Currently routes all operations to the default database.
"""


class DatabaseRouter:
    """
    Database router for read/write splitting.
    
    Currently routes all operations to the default database.
    Future enhancement: route reads to replicas for scaling.
    """
    
    def db_for_read(self, model, **hints):
        """
        Return database for read operations.
        
        Currently returns 'default'. Future: return replica for read-heavy models.
        """
        return "default"
    
    def db_for_write(self, model, **hints):
        """
        Return database for write operations.
        
        Always returns 'default' (primary).
        """
        return "default"
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects from the same database.
        
        Returns True to allow all relations (all models in same DB).
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Allow migrations on the default database only.
        
        Since we use unmanaged models, this is mostly a no-op.
        """
        return db == "default"
