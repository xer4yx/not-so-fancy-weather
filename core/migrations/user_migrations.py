"""
User schema migration utilities
"""
from typing import Dict, Any, List, Optional
import logging
from core.interface import DatabaseRepository

logger = logging.getLogger(__name__)

def migrate_user_schema(repository: DatabaseRepository) -> int:
    """
    Runs a migration to ensure all users have the new schema fields.
    Uses the repository's bulk_update_missing_fields method to avoid 
    implementation-specific code.
    
    Args:
        repository: The database repository
        
    Returns:
        The number of users migrated
    """
    try:
        logger.info("Starting user schema migration")
        
        # Define the fields that should exist on all users
        missing_fields = {
            "is_deleted": False,
            "is_2fa_enabled": False
        }
        
        # Use the repository's bulk update method
        updated_count = repository.bulk_update_missing_fields(missing_fields=missing_fields)
        
        if updated_count > 0:
            logger.info(f"Successfully migrated {updated_count} users")
        else:
            logger.info("No users needed schema migration")
            
        return updated_count
    except Exception as e:
        logger.error(f"Error during user schema migration: {str(e)}", exc_info=True)
        return 0 