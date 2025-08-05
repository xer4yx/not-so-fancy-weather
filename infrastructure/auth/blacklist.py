from datetime import datetime, timedelta, timezone
from typing import Dict, Set, Optional

from infrastructure.logger.factory import get_logger


class TokenBlacklist:
    """
    Simple in-memory token blacklist implementation.
    In production, this should be replaced with a Redis or database-backed solution.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenBlacklist, cls).__new__(cls)
            cls._instance.blacklisted_tokens: Dict[str, datetime] = {}
            cls._instance.last_cleanup = datetime.now(timezone.utc)
            cls._instance.logger = get_logger("infrastructure.auth.blacklist", "logs/infrastructure.log")
            cls._instance.logger.info("Token blacklist initialized")
        return cls._instance
    
    def add(self, token: str, expires_at: Optional[datetime] = None) -> None:
        """Add a token to the blacklist with its expiry time"""
        try:
            token_prefix = token[:10] if len(token) > 10 else token
            
            if not expires_at:
                # Default expiry of 7 days if not specified
                expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            elif expires_at.tzinfo is None:
                # Ensure the expiry time has timezone info
                expires_at = expires_at.replace(tzinfo=timezone.utc)
                
            self.blacklisted_tokens[token] = expires_at
            
            self.logger.info(
                "Token added to blacklist", 
                extra={
                    "token_prefix": f"{token_prefix}...",
                    "operation": "blacklist_add",
                    "expires_at": expires_at.isoformat(),
                    "blacklist_size": len(self.blacklisted_tokens)
                }
            )
            
            self._cleanup_expired()
        except Exception as e:
            self.logger.error(
                f"Failed to add token to blacklist: {str(e)}", 
                extra={
                    "operation": "blacklist_add",
                    "error": str(e)
                }
            )
            raise
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        try:
            # Run cleanup occasionally to prevent memory leaks
            now = datetime.now(timezone.utc)
            if (now - self.last_cleanup) > timedelta(hours=1):
                self._cleanup_expired()
                
            is_blacklisted = token in self.blacklisted_tokens
            
            if is_blacklisted:
                token_prefix = token[:10] if len(token) > 10 else token
                self.logger.debug(
                    "Token found in blacklist", 
                    extra={
                        "token_prefix": f"{token_prefix}...",
                        "operation": "blacklist_check",
                        "result": "blacklisted"
                    }
                )
                
            return is_blacklisted
        except Exception as e:
            self.logger.error(
                f"Error checking blacklist: {str(e)}", 
                extra={
                    "operation": "blacklist_check",
                    "error": str(e)
                }
            )
            # Return True as a safety measure when we can't verify
            return True
    
    def _cleanup_expired(self) -> None:
        """Remove expired tokens from the blacklist"""
        try:
            now = datetime.now(timezone.utc)
            old_size = len(self.blacklisted_tokens)
            
            expired_tokens = []
            for token, expiry in self.blacklisted_tokens.items():
                # Ensure expiry has timezone info
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                
                if expiry < now:
                    expired_tokens.append(token)
            
            # Remove expired tokens
            for token in expired_tokens:
                self.blacklisted_tokens.pop(token, None)
            
            new_size = len(self.blacklisted_tokens)
            removed_count = old_size - new_size
            
            if removed_count > 0:
                self.logger.info(
                    f"Removed {removed_count} expired tokens from blacklist", 
                    extra={
                        "operation": "blacklist_cleanup",
                        "removed_count": removed_count,
                        "current_size": new_size
                    }
                )
                
            self.last_cleanup = now
        except Exception as e:
            self.logger.error(
                f"Error during blacklist cleanup: {str(e)}", 
                extra={
                    "operation": "blacklist_cleanup",
                    "error": str(e)
                }
            ) 