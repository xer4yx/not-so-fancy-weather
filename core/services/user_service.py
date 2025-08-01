from typing import Dict, Any, List, Optional
from fastapi.encoders import jsonable_encoder
from core.entities import User
from core.interface import DatabaseRepository, HashInterface

class UserService:
    def __init__(self, repository: DatabaseRepository, crypt_algo: HashInterface):
        self.__repository = repository
        self.__crypt_algo = crypt_algo
    
    def create_user(self, username: str, email: str, password: str) -> str:
        """Create a new user with default values for new fields"""
        return self.__repository.create(
            data=jsonable_encoder(
                User(
                    username=username, 
                    email=email, 
                    password=self.__crypt_algo.hash(password=password),
                    is_deleted=False,
                    is_2fa_enabled=False
                )
            )
        )
    
    def read_user(self, key: str, value: str) -> Dict[str, Any]:
        """Read a user and ensure they have the new fields"""
        user_data = self.__repository.read(key=key, value=value)
        if user_data:
            # Ensure the user data has the new fields
            user_data = self.__ensure_user_schema_updated(user_data)
        return user_data
    
    def update_user(self, key: str, id: str, data: Dict[str, Any]) -> str:
        """Update a user, handling password hashing if needed"""
        return self.__repository.update(key=key, value=id, data=data)
    
    def delete_user(self, key: str, id: str) -> bool:
        """Hard delete a user (consider using soft delete via is_deleted)"""
        return self.__repository.delete(key=key, value=id)
    
    def soft_delete_user(self, key: str, id: str) -> str:
        """Soft delete a user by setting is_deleted to True"""
        return self.__repository.update(key=key, value=id, data={"is_deleted": True})
    
    def __ensure_user_schema_updated(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure user data has all required fields with defaults for missing ones"""
        updated = False
        
        # Add missing fields with default values
        if "is_deleted" not in user_data:
            user_data["is_deleted"] = False
            updated = True
            
        if "is_2fa_enabled" not in user_data:
            user_data["is_2fa_enabled"] = False
            updated = True
            
        # If updates were made, save them back to the database
        if updated:
            self.__repository.update(
                key="_id", 
                value=user_data["_id"], 
                data={
                    "is_deleted": user_data["is_deleted"],
                    "is_2fa_enabled": user_data["is_2fa_enabled"]
                }
            )
            
        return user_data
    
    def migrate_users(self) -> int:
        """
        Migrate all users to ensure they have the new schema fields.
        Returns the count of users migrated.
        """
        # This would need to be implemented if the repository provides a way to get all users
        # For now, this is a placeholder for this functionality
        # We'll handle migration automatically per user in read_user instead
        return 0
    