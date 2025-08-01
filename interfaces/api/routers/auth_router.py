from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any

from core.services import AuthService, UserService
from core.entities import Token
from infrastructure.logger import get_logger
from interfaces.api.di import get_auth_service, get_user_service
from interfaces.api.schemas import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest
from jose import JWTError, jwt

# Configure logger
logger = get_logger("interfaces.api.routers.auth", "logs/interfaces.log")

auth_router = APIRouter(prefix="/v1", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")

@auth_router.post(path="/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Check if user exists and password is correct
    try:
        user = user_service.read_user(key="username", value=form_data.username)
        
        if not user:
            logger.warning(f"Failed login: User not found - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is soft-deleted
        if user.get("is_deleted", False):
            logger.warning(f"Failed login: User is soft-deleted - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get stored password hash for verification
        stored_hash_password = user.get("password", "")
        if not stored_hash_password:
            logger.warning(f"Failed login: No password hash found for user - {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Try to identify the hash type
        stored_hash_type = auth_service.identify_hash_type(hashed_password=stored_hash_password)
        
        # Add extended logging to debug verification issues
        logger.debug(f"Login for user {form_data.username}: Stored hash: {stored_hash_password[:10]}..., Hash type: {stored_hash_type}")
        
        # Generate new hash after verification for potential migration
        new_hashed_password = auth_service.get_hash(form_data.password)
        new_hash_type = auth_service.identify_hash_type(new_hashed_password)
        
        logger.info(f"Verifying password for user {form_data.username} (stored hash type: {stored_hash_type}, new hash type: {new_hash_type})")
            
        # Verify password directly - avoid generating a new hash for comparison
        if not auth_service.verify_hash(form_data.password, user.get("password", "")):
            try:
                verified, updated = auth_service.verify_and_update(password=form_data.password, hashed_password=user.get("password", ""))
                if not verified:
                    logger.warning(f"Failed login: Invalid password for user - {form_data.username}",
                                extra={"stored_hash_type": stored_hash_type,
                                        "new_hash_type": new_hash_type})
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Incorrect username or password",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    
                if updated is not None:
                    logger.info(f"Hash needs to be updated. Password updated for user {form_data.username}: {updated}")
                    user_service.update_user(
                        key="username", 
                        id=form_data.username, 
                        data={"password": updated}
                    )
            except HTTPException:
                # Re-raise HTTPExceptions (like 401) without modification
                raise
            except Exception as e:
                logger.error(f"Failed to verify and update hash: {e}", exc_info=True, stack_info=True, stacklevel=2)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred during login"
                )
            
        # If password is verified but using old hash algorithm, update to new hash
        if auth_service.verify_hash(form_data.password, user.get("password", "")) \
            and stored_hash_type != new_hash_type and stored_hash_type != "unknown" \
            and new_hash_type != "unknown":
            try:
                logger.info(f"Migrating password hash from {stored_hash_type} to {new_hash_type} for user: {form_data.username}")
                user_service.update_user(
                    key="username", 
                    id=form_data.username, 
                    data={"password": new_hashed_password}
                )
                logger.info(f"Password hash migration successful for user: {form_data.username}")
            except Exception as e:
                logger.error(f"Password hash migration failed for user {form_data.username}: {str(e)}", exc_info=True)
                # Continue login process even if migration fails
        
        # Create tokens
        token_data = Token(username=form_data.username, password="")
        tokens = auth_service.create_tokens(token_data)
        
        logger.info(f"Successful login for user: {form_data.username}")
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }
    except HTTPException as e:
        # Re-raise HTTP exceptions (like 401 Unauthorized) directly
        logger.error(f"HTTP exception during login: {str(e)}", exc_info=True)
        raise
    except JWTError as e:
        logger.error(f"JWT error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Login error for user {form_data.username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )

@auth_router.post(path="/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    logger.info("Token refresh request received")
    
    try:
        # Verify refresh token
        payload = auth_service.verify_token(
            token=refresh_request.refresh_token,
            token_type="refresh"
        )
        
        # Create new tokens
        username = payload.get("username")
        if not username:
            logger.warning("Token refresh failed: Missing username in token payload")
            raise ValueError("Invalid token: missing username")
            
        logger.info(f"Refreshing token for user: {username}")
        token_data = Token(username=username, password="")
        tokens = auth_service.create_tokens(token_data)
        
        logger.info(f"Token successfully refreshed for user: {username}")
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer"
        }
    except ValueError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )

@auth_router.post(path="/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    logout_request: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    logger.info("Logout request received")
    
    try:
        # First handle the access token
        if logout_request.access_token:
            # Try to get username from token for better logging, but don't fail if we can't
            username = "unknown"
            try:
                # First try decoding without verification just to get info
                try:
                    payload = jwt.decode(
                        logout_request.access_token, 
                        key="dummy_key_for_decoding_only", 
                        options={"verify_signature": False}
                    )
                    username = payload.get("username", "unknown")
                    token_type = payload.get("token_type", "unknown")
                    logger.info(f"Processing logout for user: {username}, token type: {token_type}")
                except Exception:
                    # Silently continue if we can't decode
                    pass
                    
                # Now verify properly, but this might fail with invalid token type
                payload = auth_service.verify_token(token=logout_request.access_token, token_type="access")
                username = payload.get("username", "unknown")
                logger.info(f"Successfully verified access token for user: {username}")
            except Exception as ve:
                logger.info(f"Token verification failed but continuing for user: {username}")
            
            # Always blacklist the token regardless of verification errors
            try:
                auth_service.blacklist_token(logout_request.access_token)
                logger.info("Access token successfully blacklisted")
            except Exception as e:
                logger.warning(f"Failed to blacklist access token: {str(e)}")
        
        # Then handle the refresh token if provided
        if logout_request.refresh_token:
            try:
                auth_service.blacklist_token(logout_request.refresh_token)
                logger.info("Refresh token successfully blacklisted")
            except Exception as e:
                logger.warning(f"Failed to blacklist refresh token: {str(e)}")
        
        logger.info("Logout successful")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}"
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """
    Get the current user from the token

    Args:
        token (str, optional): The token to get the current user from. Defaults to Depends(oauth2_scheme).
        auth_service (AuthService, optional): The authentication service to use. Defaults to Depends(get_auth_service).
        user_service (UserService, optional): The user service to use. Defaults to Depends(get_user_service).

    Raises:
        HTTPException: If the token is invalid.
        HTTPException: If the user is not found.
        HTTPException: If the user is soft-deleted.
        HTTPException: If an error occurs during authentication.

    Returns:
        dict: The current user.
    """    
    try:
        # First try to verify as an access token
        try:
            payload = auth_service.verify_token(token=token, token_type="access")
        except ValueError as access_error:
            # If that fails, try as a refresh token
            try:
                logger.debug("Failed to verify as access token, trying as refresh token")
                payload = auth_service.verify_token(token=token, token_type="refresh")
            except ValueError as refresh_error:
                # If both fail, raise the original error
                logger.warning(f"Authentication failed: {str(access_error)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(access_error),
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
        username = payload.get("username")
        
        if not username:
            logger.warning("Authentication failed: Missing username in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Authenticating user: {username}")
        user = user_service.read_user(key="username", value=username)
        if not user:
            logger.warning(f"Authentication failed: User not found - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is soft-deleted
        if user.get("is_deleted", False):
            logger.warning(f"Authentication failed: User is soft-deleted - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Ensure user has both 'id' and '_id' for consistency
        if "_id" in user and "id" not in user:
            user["id"] = user["_id"]
        elif "id" in user and "_id" not in user:
            user["_id"] = user["id"]
            
        logger.debug(f"User authenticated: {username}")
        return user
    except HTTPException as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise
    except ValueError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication"
        ) 