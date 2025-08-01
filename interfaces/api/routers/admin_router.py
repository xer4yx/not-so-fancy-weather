from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core.services import AuthService, UserService
from interfaces.api.di import get_auth_service, get_user_service
from infrastructure.logger import get_logger
import re

# Configure logger
logger = get_logger("interfaces.api.routers.user_hash_utils", "logs/interfaces.log")

admin_router = APIRouter(prefix="/v1/admin", tags=["admin"])

def identify_hash_type(hashed_password: str) -> str:
    """
    Identify the hash algorithm used based on the format of the hashed password.
    
    Returns:
        str: The identified hash type ('bcrypt', 'sha256_crypt', 'pbkdf2_sha256', or 'unknown')
    """
    if hashed_password.startswith('$2'):
        return "bcrypt"
    elif hashed_password.startswith('$5$'):
        return "sha256_crypt"
    elif hashed_password.startswith('$pbkdf2-sha256$'):
        return "pbkdf2_sha256"
    else:
        return "unknown"

@admin_router.post("/rehash-user-password", status_code=status.HTTP_200_OK)
async def rehash_user_password(
    username: str,
    plain_password: str,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Admin utility to rehash a user's password using the current hash algorithm.
    This can be used to fix password hash mismatches.
    
    Note: This requires knowing the user's plain password.
    """
    logger.info(f"Attempting to rehash password for user: {username}")
    
    # Check if user exists
    user = user_service.read_user(key="username", value=username)
    if not user:
        logger.warning(f"Rehash failed: User not found - {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get the current hash types
    current_hashed_password = user.get("password", "")
    current_hash_type = identify_hash_type(current_hashed_password)
    
    # Hash with current algorithm
    new_hashed_password = auth_service.get_hash(plain_password)
    new_hash_type = identify_hash_type(new_hashed_password)
    
    # Log the hash information
    logger.info(f"User hash info for {username}:",
        extra={
            "current_hash_type": current_hash_type,
            "new_hash_type": new_hash_type
        }
    )
    
    # Update the user's password hash
    try:
        # Test if the new hash would verify correctly
        verification_test = auth_service.verify_hash(plain_password, new_hashed_password)
        if not verification_test:
            logger.error(f"Verification test failed for new hash for user {username}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="New hash verification test failed"
            )
            
        # Update the password
        user["password"] = new_hashed_password
        user_service.update_user(key="username", id=user.get("username"), data={"password": new_hashed_password})
        
        logger.info(f"Successfully rehashed password for user: {username}")
        return {
            "username": username,
            "old_hash_type": current_hash_type,
            "new_hash_type": new_hash_type,
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to rehash password for user {username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rehash password: {str(e)}"
        )

@admin_router.get("/check-user-hash", status_code=status.HTTP_200_OK)
async def check_user_hash(
    username: str,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Admin utility to check a user's current password hash type without changing it.
    """
    logger.info(f"Checking hash for user: {username}")
    
    # Check if user exists
    user = user_service.read_user(key="username", value=username)
    if not user:
        logger.warning(f"Hash check failed: User not found - {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get the current hash type
    current_hashed_password = user.get("password", "")
    current_hash_type = identify_hash_type(current_hashed_password)
    
    # Create a sample hash with current algorithm
    sample_password = "sample_password_for_hash_check"
    sample_hash = auth_service.get_hash(sample_password)
    expected_hash_type = identify_hash_type(sample_hash)
    
    logger.info(f"Hash check for user {username}:",
        extra={
            "current_hash_type": current_hash_type,
            "expected_hash_type": expected_hash_type,
            "hash_match": current_hash_type == expected_hash_type
        }
    )
    
    return {
        "username": username,
        "current_hash_type": current_hash_type,
        "expected_hash_type": expected_hash_type,
        "hash_mismatch": current_hash_type != expected_hash_type
    }
    
    
@admin_router.post("/check-hash-from-plain", status_code=status.HTTP_200_OK)
async def check_hash_from_plain(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Admin utility to check a user's current password hash type without changing it.
    """
    logger.info(f"Checking hash for user: {form_data.username}")
    
    # Check if user exists
    user = user_service.read_user(key="username", value=form_data.username)
    if not user:
        logger.warning(f"Hash check failed: User not found - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash the plain password
    current_hashed_password = user.get("password", "")
    hashed_password = auth_service.get_hash(form_data.password)
    
    
    # Identify the hash type
    hash_type = identify_hash_type(hashed_password)
    logger.debug(f"Password length: {len(form_data.password)}, Hash type: {hash_type}")
    current_hash_type = identify_hash_type(current_hashed_password)
    
    # Verify against the stored hash - this is what's used in login
    actual_verification = auth_service.verify_hash(form_data.password, current_hashed_password)
    
    logger.info(f"Hash check for user {form_data.username}:",
        extra={
            "current_hash_type": current_hash_type,
            "plaintext_hash_type": hash_type,
            "hash_match": actual_verification
        }
    )
    
    return {
        "username": form_data.username,
        "current_hash_type": current_hash_type,
        "plaintext_hash_type": hash_type,
        "current_hash": current_hashed_password,
        "plaintext_hash": hashed_password,
        "stored_hash_verification": actual_verification,
        "self_hash_verification": auth_service.verify_hash(form_data.password, hashed_password)
    }
