from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class HashInterface(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hashes the password."""
    
    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        """Verifies the password."""
        
    @abstractmethod
    def verify_and_update(self, password: str, hashed_password: str) -> Tuple[bool, str]:
        """Verifies the password and updates the hash if necessary."""
        
    @abstractmethod
    def identify_hash_type(self, hashed_password: str) -> str:
        """Identifies the hash type."""


class AuthInterface(ABC):
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Creates an access token."""
    
    @abstractmethod
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Creates a refresh token."""
    
    @abstractmethod
    def verify_token(self, token: str, token_type: str) -> Dict[str, Any]:
        """Verifies the token."""
        
    @abstractmethod
    def blacklist_token(self, token: str) -> None:
        """Blacklists a token."""
        
    @abstractmethod
    def is_token_blacklisted(self, token: str) -> bool:
        """Checks if a token is blacklisted."""