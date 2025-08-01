from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class DatabaseRepository(ABC):
    @abstractmethod
    def create(self, *args, **kwargs) -> str:
        """Create a new record in the database."""
        
    @abstractmethod
    def read(self, *args, **kwargs) -> Dict[str, Any]:
        """Read a record from the database."""
        
    @abstractmethod
    def update(self, *args, **kwargs) -> str:
        """Update a record in the database."""
        
    @abstractmethod
    def delete(self, *args, **kwargs) -> bool:
        """Delete a record from the database."""
        
    def bulk_update_missing_fields(self, missing_fields: Dict[str, Any]) -> int:
        """
        Update multiple records to ensure they have certain fields.
        This method is optional and can be implemented by repository classes
        that support efficient bulk operations.
        
        Args:
            missing_fields: A dictionary of field names and their default values
                           to add to records that don't have these fields
                           
        Returns:
            The number of records updated
        """
        # Default implementation does nothing
        return 0
        
    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records from the repository.
        This method is optional and can be implemented by repository classes
        that need to support full dataset operations.
        
        Returns:
            A list of all records
        """
        # Default implementation returns empty list
        return []