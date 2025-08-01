from fastapi import APIRouter, Depends, Query, Request, Body, HTTPException, status
from core.services import AuthService, UserService, PreferencesService
from infrastructure.logger.factory import get_logger
from interfaces.api.di import get_user_service, get_preferences_service, get_auth_service
from interfaces.api.schemas import UserCreate, UserResponse, UserUpdate, UserPreferences
from interfaces.api.routers.auth_router import get_current_user
import logging

# Configure logger
logger = get_logger("interfaces.api.routers.user_router", "logs/interfaces.log")

user_router = APIRouter(prefix="/v1", tags=["users"])

@user_router.get(path="/user/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the profile of the currently authenticated user
    """
    logger.info(f"Retrieving profile for current user: {current_user.get('username')}")
    
    # We already have the user data from the get_current_user dependency
    # Make sure it has the expected structure
    if "_id" not in current_user and "id" in current_user:
        # If the field exists as 'id' but is needed as '_id', adjust it
        current_user["_id"] = current_user["id"]
    
    return current_user

@user_router.post(path="/user/me", response_model=str)
async def update_current_user_profile(
    request: Request,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update the profile of the currently authenticated user
    """
    username = current_user.get("username")
    logger.info(f"Request to update profile for current user: {username}")
    
    try:
        # Convert Pydantic model to dict
        data = user_update.model_dump(exclude_unset=True)
        
        # Handle unique constraints if updating username or email
        if "username" in data and data["username"] != username:
            username_check = user_service.read_user(key="username", value=data["username"])
            if username_check:
                logger.warning(f"Profile update failed: New username already exists - {data['username']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
                
        if "email" in data and data["email"] != current_user.get("email"):
            email_check = user_service.read_user(key="email", value=data["email"])
            if email_check:
                logger.warning(f"Profile update failed: New email already exists - {data['email']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )
        
        # Update the user
        result = user_service.update_user(key="username", id=username, data=data)
        logger.info(f"Profile updated successfully for user: {username}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except ValueError as e:
        logger.error(f"Value error during profile update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating profile for user {username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating your profile"
        )

@user_router.post(path="/user/password", status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    password_data: dict = Body(...),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Change the password of the currently authenticated user
    """
    username = current_user.get("username")
    logger.info(f"Request to change password for user: {username}")
    
    try:
        # Validate request body
        if "current_password" not in password_data or "new_password" not in password_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both current_password and new_password are required"
            )
        
        # Verify current password
        user = user_service.read_user(key="username", value=username)
        
        if not auth_service.verify_hash(password_data["current_password"], user.get("password")):
            logger.warning(f"Password change failed: Incorrect current password for user - {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update the password
        new_password_hash = auth_service.get_hash(password_data["new_password"])
        result = user_service.update_user(
            key="username", 
            id=username, 
            data={"password": new_password_hash}
        )
        
        logger.info(f"Password changed successfully for user: {username}")
        return {"message": "Password updated successfully"}
    except HTTPException as e:
        logger.error(
            f"Error changing password for user {username}: {str(e)}", 
            exc_info=True,
            stack_info=True,
            stacklevel=2)
        raise
    except Exception as e:
        logger.error(
            f"Error changing password for user {username}: {str(e)}", 
            exc_info=True, 
            stack_info=True, 
            stacklevel=2)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing your password"
        )

@user_router.post(path="/user", response_model=str)
async def create_user(
    request: Request,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)):
    
    logger.info(f"Request to create user with username: {user_data.username}, email: {user_data.email}")
    
    try:
        # Check if user already exists
        existing_user = user_service.read_user(key="username", value=user_data.username)
        if existing_user:
            logger.warning(f"User creation failed: Username already exists - {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
            
        # Check if email already exists
        existing_email = user_service.read_user(key="email", value=user_data.email)
        if existing_email:
            logger.warning(f"User creation failed: Email already exists - {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        
        result = user_service.create_user(username=user_data.username, email=user_data.email, password=user_data.password)
        logger.info(f"User created successfully: {user_data.username}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except ValueError as e:
        logger.error(f"Value error during user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user {user_data.username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )

@user_router.get(path="/user", response_model=UserResponse)
async def read_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    
    logger.info(f"Request to read user with {key}: {value}")
    
    try:
        # Validate key
        valid_keys = ["username", "email", "_id"]
        if key not in valid_keys:
            logger.warning(f"Invalid key for user lookup: {key}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid key. Must be one of: {', '.join(valid_keys)}"
            )
        
        user = user_service.read_user(key=key, value=value)
        if not user:
            logger.info(f"User not found with {key}: {value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is soft-deleted, unless explicitly querying for deleted users
        if user.get("is_deleted", False):
            logger.info(f"User found but is soft-deleted: {key}={value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User found with {key}: {value}")
        return user
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except Exception as e:
        logger.error(f"Error reading user with {key}: {value}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the user"
        )

@user_router.put(path="/user", response_model=str)
async def update_user(
    request: Request,
    user_update: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    
    logger.info(f"Request to update user with {key}: {value}")
    
    try:
        # Validate key
        valid_keys = ["username", "email", "_id"]
        if key not in valid_keys:
            logger.warning(f"Invalid key for user update: {key}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid key. Must be one of: {', '.join(valid_keys)}"
            )
        
        # Check if user exists
        existing_user = user_service.read_user(key=key, value=value)
        if not existing_user:
            logger.warning(f"User update failed: User not found with {key}: {value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is soft-deleted
        if existing_user.get("is_deleted", False):
            logger.warning(f"User update failed: User is soft-deleted: {key}={value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a deleted user"
            )
        
        # Convert Pydantic model to dict
        data = user_update.model_dump(exclude_unset=True)
        
        # Handle unique constraints if updating username or email
        if "username" in data and data["username"] != existing_user.get("username"):
            username_check = user_service.read_user(key="username", value=data["username"])
            if username_check:
                logger.warning(f"User update failed: New username already exists - {data['username']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
                
        if "email" in data and data["email"] != existing_user.get("email"):
            email_check = user_service.read_user(key="email", value=data["email"])
            if email_check:
                logger.warning(f"User update failed: New email already exists - {data['email']}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )
        
        result = user_service.update_user(key=key, id=value, data=data)
        logger.info(f"User updated successfully: {key}={value}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except ValueError as e:
        logger.error(f"Value error during user update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user with {key}: {value}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the user"
        )

@user_router.delete(path="/user", response_model=bool)
async def delete_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    
    logger.info(f"Request to delete user with {key}: {value}")
    
    try:
        # Validate key
        valid_keys = ["username", "email", "_id"]
        if key not in valid_keys:
            logger.warning(f"Invalid key for user deletion: {key}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid key. Must be one of: {', '.join(valid_keys)}"
            )
        
        # Check if user exists
        existing_user = user_service.read_user(key=key, value=value)
        if not existing_user:
            logger.warning(f"User deletion failed: User not found with {key}: {value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = user_service.delete_user(key=key, id=value)
        logger.info(f"User deleted successfully: {key}={value}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except Exception as e:
        logger.error(f"Error deleting user with {key}: {value}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the user"
        )

@user_router.put(path="/user/soft-delete", response_model=str)
async def soft_delete_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    key: str = Query(description="Key"),
    value: str = Query(description="Value")):
    
    logger.info(f"Request to soft delete user with {key}: {value}")
    
    try:
        # Validate key
        valid_keys = ["username", "email", "_id"]
        if key not in valid_keys:
            logger.warning(f"Invalid key for user soft deletion: {key}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid key. Must be one of: {', '.join(valid_keys)}"
            )
        
        # Check if user exists
        existing_user = user_service.read_user(key=key, value=value)
        if not existing_user:
            logger.warning(f"User soft deletion failed: User not found with {key}: {value}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already soft-deleted
        if existing_user.get("is_deleted", False):
            logger.info(f"User already soft-deleted: {key}={value}")
            return "User already deleted"
        
        result = user_service.soft_delete_user(key=key, id=value)
        logger.info(f"User soft deleted successfully: {key}={value}")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions that we've already handled
        raise
    except Exception as e:
        logger.error(f"Error soft deleting user with {key}: {value}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while soft deleting the user"
        )

@user_router.get(path="/user/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    prefs_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Get the preferences of the currently authenticated user
    """
    username = current_user.get("username")
    # Get user ID, handling both possible formats (_id or id)
    user_id = current_user.get("_id") or current_user.get("id")
    
    if not user_id:
        logger.error(f"Error retrieving user ID for {username}, user data: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not determine user ID"
        )
        
    logger.info(f"Retrieving preferences for user: {username} with ID: {user_id}")
    
    try:
        # Check if user has preferences
        preferences = prefs_service.get_preferences_by_user_id(user_id)
        
        # Return default preferences if none found
        if not preferences:
            logger.info(f"No preferences found for user {username}, returning defaults and creating record")
            # Create default preferences
            prefs_id = prefs_service.create_preferences(
                user_id=user_id,
                username=username
            )
            # Return the default preferences
            return UserPreferences(user_id=user_id, username=username)
        
        logger.info(f"Preferences retrieved for user: {username}")
        return preferences
    except Exception as e:
        logger.error(f"Error retrieving preferences for user {username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving your preferences"
        )

@user_router.post(path="/user/preferences", status_code=status.HTTP_200_OK)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
    prefs_service: PreferencesService = Depends(get_preferences_service)
):
    """
    Update the preferences of the currently authenticated user
    """
    username = current_user.get("username")
    # Get user ID, handling both possible formats (_id or id)
    user_id = current_user.get("_id") or current_user.get("id")
    
    if not user_id:
        logger.error(f"Error retrieving user ID for {username}, user data: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not determine user ID"
        )
        
    logger.info(f"Updating preferences for user: {username} with ID: {user_id}")
    
    try:
        # Convert to dict and validate
        pref_data = preferences.model_dump(exclude_unset=True)
        
        # Ensure we have user ID and username in the data
        pref_data["user_id"] = user_id
        pref_data["username"] = username
        
        # Use the update_preferences_by_user_id method which handles create-if-not-exists
        result = prefs_service.update_preferences_by_user_id(
            user_id=user_id,
            data=pref_data
        )
        
        logger.info(f"Preferences updated for user: {username}")
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logger.error(f"Error updating preferences for user {username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating your preferences"
        )