import os
from core.interface.auth import AuthInterface
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Dict, Any, Optional
import inspect

from .blacklist import TokenBlacklist
from utils.configs import NSFWApiSettings
from infrastructure.logger.factory import get_logger

logger = get_logger("infrastructure.auth.jwt", "logs/infrastructure.log")


class JWTAuth(AuthInterface):
    def __init__(self):
        api_settings = NSFWApiSettings()
        self.__secret_key = api_settings.SECRET_KEY
        self.__algorithm = "HS256"
        self.__access_token_expire_minutes = 30
        self.__refresh_token_expire_minutes = 60 * 24 * 7  # 7 days
        self.__token_blacklist = TokenBlacklist()
        self.__logger = logger

    def create_access_token(self, data: Dict[str, Any]) -> str:
        try:
            # Ensure token_type is set correctly
            to_encode = data.copy()
            to_encode["token_type"] = "access"
            
            token = self.__create_token(
                data=to_encode,
                expires_delta=timedelta(minutes=self.__access_token_expire_minutes)
            )
            self.__logger.info(
                "Access token created", 
                extra={
                    "subject": data.get("sub", "unknown"),
                    "token_type": "access",
                    "operation": "token_creation"
                }
            )
            return token
        except Exception as e:
            self.__logger.error(
                f"Failed to create access token: {str(e)}", 
                extra={
                    "subject": data.get("sub", "unknown"),
                    "error": str(e),
                    "operation": "token_creation"
                }
            )
            raise

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        try:
            # Ensure token_type is set correctly
            to_encode = data.copy()
            to_encode["token_type"] = "refresh"
            
            token = self.__create_token(
                data=to_encode,
                expires_delta=timedelta(minutes=self.__refresh_token_expire_minutes)
            )
            self.__logger.info(
                "Refresh token created", 
                extra={
                    "subject": data.get("sub", "unknown"),
                    "token_type": "refresh",
                    "operation": "token_creation"
                }
            )
            return token
        except Exception as e:
            self.__logger.error(
                f"Failed to create refresh token: {str(e)}", 
                extra={
                    "subject": data.get("sub", "unknown"),
                    "error": str(e),
                    "operation": "token_creation"
                }
            )
            raise

    def verify_token(self, token: str, token_type: str) -> Dict[str, Any]:
        if not token:
            self.__logger.warning(
                "Token verification failed: Token is empty", 
                extra={"token_type": token_type, "operation": "token_verification", "status": "failed"}
            )
            raise ValueError("Token is required")
            
        # Check if token is blacklisted
        try:
            if self.is_token_blacklisted(token):
                self.__logger.warning(
                    "Token verification failed: Token is blacklisted", 
                    extra={"token_type": token_type, "operation": "token_verification", "status": "failed"}
                )
                raise ValueError("Token has been invalidated")
        except Exception as e:
            self.__logger.error(
                f"Error checking token blacklist: {str(e)}", 
                extra={"token_type": token_type, "operation": "token_verification", "error": str(e)}
            )
            raise
            
        try:
            # First decode without verification to log token details for debugging
            try:
                debug_payload = jwt.decode(token, key=self.__secret_key, options={"verify_signature": False})
                self.__logger.debug(
                    f"Token debug info - Type: {debug_payload.get('token_type', 'unknown')}, Expected: {token_type}",
                    extra={
                        "actual_type": debug_payload.get("token_type", "unknown"),
                        "expected_type": token_type,
                        "operation": "token_verification"
                    }
                )
            except Exception as debug_error:
                self.__logger.warning(f"Could not decode token for debugging: {str(debug_error)}")
                
            # Now verify the token properly
            payload = jwt.decode(token, self.__secret_key, algorithms=[self.__algorithm])
            
            # Check token type with better logging
            detected_type = payload.get("token_type")
            if detected_type != token_type:
                self.__logger.warning(
                    f"Token verification failed: Invalid token type", 
                    extra={
                        "expected": token_type, 
                        "received": detected_type,
                        "subject": payload.get("sub", "unknown"),
                        "username": payload.get("username", "unknown"),
                        "operation": "token_verification",
                        "status": "failed"
                    }
                )
                
                # This occurs often when client sends refresh token as access token or vice versa
                # Log more details to help diagnose the issue
                try:
                    exp_time = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
                    creation_time = exp_time - timedelta(minutes=self.__refresh_token_expire_minutes if detected_type == "refresh" else self.__access_token_expire_minutes)
                    self.__logger.debug(
                        f"Token details - Creation: {creation_time}, Expiration: {exp_time}, Duration: {exp_time - creation_time}",
                        extra={"token_duration": str(exp_time - creation_time)}
                    )
                except Exception as time_error:
                    self.__logger.debug(f"Could not calculate token times: {str(time_error)}")
                    
                raise ValueError(f"Invalid token type. Expected {token_type}, got {detected_type or 'unknown'}")
                
            self.__logger.info(
                "Token verification successful", 
                extra={
                    "token_type": token_type,
                    "subject": payload.get("sub", "unknown"),
                    "username": payload.get("username", "unknown"),
                    "operation": "token_verification",
                    "status": "success"
                }
            )
            return payload
        except JWTError as e:
            self.__logger.warning(
                f"Token verification failed: {str(e)}", 
                extra={
                    "token_type": token_type, 
                    "error": str(e),
                    "operation": "token_verification",
                    "status": "failed"
                }
            )
            raise ValueError("Invalid token")
            
    def blacklist_token(self, token: str) -> None:
        """Add token to blacklist"""
        if not token:
            self.__logger.warning(
                "Token blacklisting failed: Token is empty", 
                extra={"operation": "token_blacklist", "status": "failed"}
            )
            return
            
        try:
            # Decode without verification to get expiry
            payload = jwt.decode(token, key=self.__secret_key, options={"verify_signature": False})
            exp = payload.get("exp")
            token_type = payload.get("token_type", "unknown")
            subject = payload.get("sub", "unknown")
            
            if exp:
                # Convert Unix timestamp to datetime with UTC timezone
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                self.__token_blacklist.add(token, expires_at)
            else:
                # If no expiry, use default
                self.__token_blacklist.add(token)
                
            self.__logger.info(
                "Token blacklisted successfully", 
                extra={
                    "token_type": token_type,
                    "subject": subject,
                    "operation": "token_blacklist",
                    "status": "success",
                    "expires_at": exp
                }
            )
        except Exception as e:
            # Try to blacklist even if decoding fails
            try:
                self.__token_blacklist.add(token)
                self.__logger.warning(
                    f"Token blacklisted with default expiry due to error: {str(e)}", 
                    extra={
                        "operation": "token_blacklist", 
                        "status": "partial_success",
                        "error": str(e)
                    }
                )
            except Exception as inner_e:
                self.__logger.error(
                    f"Failed to blacklist token: {str(inner_e)}", 
                    extra={
                        "operation": "token_blacklist", 
                        "status": "failed",
                        "error": f"{str(e)} -> {str(inner_e)}"
                    }
                )
                raise
            
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            result = self.__token_blacklist.is_blacklisted(token)
            if result:
                self.__logger.debug(
                    "Token found in blacklist", 
                    extra={"operation": "blacklist_check", "status": "found"}
                )
            return result
        except Exception as e:
            self.__logger.error(
                f"Error checking token blacklist: {str(e)}", 
                extra={"operation": "blacklist_check", "status": "error", "error": str(e)}
            )
            # Return True as a safety measure when we can't verify
            return True

    def __create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
                
            to_encode.update({"exp": expire})
            
            # Check if token_type is already set in the data
            if "token_type" not in to_encode:
                # Determine token type based on which create method was called
                caller_method = inspect.currentframe().f_back.f_code.co_name
                
                self.__logger.debug(
                    f"Creating token - caller: {caller_method}, expires_in: {expires_delta}",
                    extra={"operation": "token_creation", "caller": caller_method}
                )
                
                if caller_method == "create_access_token":
                    to_encode.update({"token_type": "access"})
                    self.__logger.debug("Setting token_type to 'access' based on caller method")
                elif caller_method == "create_refresh_token":
                    to_encode.update({"token_type": "refresh"})
                    self.__logger.debug("Setting token_type to 'refresh' based on caller method")
                else:
                    # For direct calls, explicitly set token type based on expiration
                    if expires_delta and expires_delta.total_seconds() > 3600:
                        to_encode.update({"token_type": "refresh"})
                        self.__logger.debug("Setting token_type to 'refresh' based on long expiration time")
                    else:
                        to_encode.update({"token_type": "access"})
                        self.__logger.debug("Setting token_type to 'access' based on short expiration time")
                
            # Log the final token type that will be encoded
            self.__logger.debug(
                f"Final token_type: {to_encode.get('token_type')}",
                extra={
                    "token_type": to_encode.get("token_type", "unknown"),
                    "operation": "token_creation"
                }
            )
                
            encoded_jwt = jwt.encode(to_encode, self.__secret_key, algorithm=self.__algorithm)
            return encoded_jwt
        except Exception as e:
            self.__logger.error(
                f"Error creating JWT token: {str(e)}", 
                extra={
                    "subject": data.get("sub", "unknown"),
                    "operation": "token_creation",
                    "error": str(e)
                }
            )
            raise 