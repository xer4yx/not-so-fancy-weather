from abc import ABC, abstractmethod
from typing import Dict, Any


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