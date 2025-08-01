from fastapi.encoders import jsonable_encoder
from typing import Dict, Any, Tuple

from core.entities import Token
from core.interface import AuthInterface, HashInterface
from infrastructure.logger import get_logger

logger = get_logger("core.services.auth_service", "logs/core.log")


class AuthService:
    def __init__(self, auth: AuthInterface, hash: HashInterface):
        self.__auth = auth
        self.__hash = hash

    def create_access_token(self, data: Dict[str, Any]) -> str:
        try:
            return self.__auth.create_access_token(data=data)
        except Exception as e:
            logger.error(f"Failed to create access token: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        try:
            return self.__auth.create_refresh_token(data=data)
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def create_tokens(self, data: Token) -> Dict[str, str]:
        try:
            encoded_data = jsonable_encoder(data)
            
            # Create access token data with explicit token type
            access_token_data = encoded_data.copy()
            access_token_data["token_type"] = "access"
            
            # Create refresh token data with explicit token type
            refresh_token_data = encoded_data.copy()
            refresh_token_data["token_type"] = "refresh"
            
            return {
                "access_token": self.__auth.create_access_token(data=access_token_data),
                    "refresh_token": self.__auth.create_refresh_token(data=refresh_token_data)
                }
        except Exception as e:
            logger.error(f"Failed to create tokens: {e}")
            raise

    def verify_token(self, token: str, token_type: str) -> Dict[str, Any]:
        try:
            return self.__auth.verify_token(token=token, token_type=token_type)
        except Exception as e:
            logger.error(f"Failed to verify token: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def blacklist_token(self, token: str) -> None:
        try:
            return self.__auth.blacklist_token(token=token)
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def is_token_blacklisted(self, token: str) -> bool:
        try:
            return self.__auth.is_token_blacklisted(token=token)
        except Exception as e:
            logger.error(f"Failed to check if token is blacklisted: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def get_hash(self, password: str) -> str:
        try:
            return self.__hash.hash(password=password)
        except Exception as e:
            logger.error(f"Failed to get hash: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise

    def verify_hash(self, password: str, hashed_password: str) -> bool:
        try:
            return self.__hash.verify(password=password, hashed_password=hashed_password)
        except Exception as e:
            logger.error(f"Failed to verify hash: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise
    
    def verify_and_update(self, password: str, hashed_password: str) -> Tuple[bool, str]:
        try:
            return self.__hash.verify_and_update(password=password, hashed_password=hashed_password)
        except Exception as e:
            logger.error(f"Failed to verify and update hash: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise
    
    def identify_hash_type(self, hashed_password: str) -> str:
        try:
            return self.__hash.identify_hash_type(hashed_password=hashed_password)
        except Exception as e:
            logger.error(f"Failed to identify hash type: {e}", exc_info=True, stack_info=True, stacklevel=2)
            raise
