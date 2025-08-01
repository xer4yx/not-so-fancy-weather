"""
Migration service to handle database schema migration operations
"""
from core.interface import DatabaseRepository
from core.migrations.user_migrations import migrate_user_schema
import logging

logger = logging.getLogger(__name__)

class MigrationService:
    """
    Service to handle data migrations across different entities
    
    This service abstracts away the infrastructure details from the application
    layer and provides a clean interface for running migrations.
    """
    
    def __init__(self, repository: DatabaseRepository):
        """
        Initialize migration service with a repository
        
        Args:
            repository: Database repository implementation that will be used for migrations
        """
        self.__repository = repository
    
    def migrate_user_schema(self) -> int:
        """
        Run user schema migration
        
        Returns:
            The number of users migrated
        """
        try:
            logger.info("Starting user schema migration")
            migrated_count = migrate_user_schema(repository=self.__repository)
            logger.info(f"User schema migration completed: {migrated_count} users updated")
            return migrated_count
        except Exception as e:
            logger.error(f"Error during user schema migration: {str(e)}", exc_info=True)
            return 0 