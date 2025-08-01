from typing import Dict, Any, Optional
from fastapi.encoders import jsonable_encoder
from core.entities import Preferences
from core.interface import DatabaseRepository
import logging
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

class PreferencesService:
    def __init__(self, repository: DatabaseRepository):
        self.__repository = repository
    
    def create_preferences(self, user_id: str, username: str, 
                          units: str = "metric", 
                          theme: str = "auto", 
                          default_location: str = "") -> str:
        """Create new preferences for a user"""
        logger.info(f"Creating new preferences for user {username} with ID {user_id}")
        return self.__repository.create(
            data=jsonable_encoder(
                Preferences(
                    user_id=user_id,
                    username=username,
                    units=units,
                    theme=theme,
                    defaultLocation=default_location
                )
            )
        )
    
    def get_preferences_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get preferences by user ID"""
        return self.__repository.read(key="user_id", value=user_id)
    
    def get_preferences_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get preferences by username"""
        return self.__repository.read(key="username", value=username)
    
    def update_preferences(self, preferences_id: str, data: Dict[str, Any]) -> str:
        """Update preferences by ID"""
        try:
            return self.__repository.update(key="_id", value=preferences_id, data=data)
        except OperationFailure as e:
            # If the record wasn't found for updating, create a new one
            if "Could not find record to update" in str(e):
                logger.info(f"Preference record not found for ID {preferences_id}, creating new record")
                # Extract user_id and username from data
                user_id = data.get("user_id")
                username = data.get("username")
                
                if not user_id or not username:
                    logger.error("Missing user_id or username for creating new preferences")
                    raise ValueError("User ID and username are required to create new preferences")
                
                # Create new preferences
                return self.create_preferences(
                    user_id=user_id,
                    username=username,
                    units=data.get("units", "metric"),
                    theme=data.get("theme", "auto"),
                    default_location=data.get("defaultLocation", "")
                )
            # If it's another type of error, re-raise it
            raise
    
    def update_preferences_by_user_id(self, user_id: str, data: Dict[str, Any]) -> str:
        """Update preferences by user ID"""
        # First check if preferences exist
        prefs = self.get_preferences_by_user_id(user_id)
        if not prefs:
            # Create new preferences if they don't exist
            username = data.pop("username", None)
            if not username:
                raise ValueError("Username is required to create new preferences")
            return self.create_preferences(
                user_id=user_id,
                username=username,
                units=data.get("units", "metric"),
                theme=data.get("theme", "auto"),
                default_location=data.get("defaultLocation", "")
            )
        
        # Update existing preferences
        return self.__repository.update(key="user_id", value=user_id, data=data)
    
    def update_preferences_by_username(self, username: str, data: Dict[str, Any]) -> str:
        """Update preferences by username"""
        # First check if preferences exist
        prefs = self.get_preferences_by_username(username)
        if not prefs:
            # Create new preferences if they don't exist
            user_id = data.pop("user_id", None)
            if not user_id:
                raise ValueError("User ID is required to create new preferences")
            return self.create_preferences(
                user_id=user_id,
                username=username,
                units=data.get("units", "metric"),
                theme=data.get("theme", "auto"),
                default_location=data.get("defaultLocation", "")
            )
        
        # Update existing preferences
        return self.__repository.update(key="username", value=username, data=data)
    
    def delete_preferences(self, preferences_id: str) -> bool:
        """Delete preferences by ID"""
        return self.__repository.delete(key="_id", value=preferences_id)
    
    def delete_preferences_by_user_id(self, user_id: str) -> bool:
        """Delete preferences by user ID"""
        return self.__repository.delete(key="user_id", value=user_id) 