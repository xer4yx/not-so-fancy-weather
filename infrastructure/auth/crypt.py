from passlib.context import CryptContext
from core.interface import HashInterface
from infrastructure.logger import get_logger
from typing import Tuple

logger = get_logger("infrastructure.auth.crypt", "logs/infrastructure.log")

class Sha256Hash(HashInterface):
    def __init__(self):
        self.__crypt_context = CryptContext(
            schemes=["sha256_crypt", "hex_sha256", "pbkdf2_sha256"],
            default="sha256_crypt",
            deprecated="auto",
        )

    def hash(self, password: str) -> str:
        return self.__crypt_context.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return self.__crypt_context.verify(password, hashed_password)
    
    def verify_and_update(self, password: str, hashed_password: str) -> Tuple[bool, str]:
        """
        Verifies the password and updates the hash if necessary.
        """
        verified, updated = self.__crypt_context.verify_and_update(password, hashed_password)
        
        if not verified and updated is None:
            logger.error(f"Failed to verify the password. Password is not updated.")
            
        if verified and updated is not None:
            logger.info(f"Password verified successfully. Hash updated.")
        else:
            logger.info(f"Password verified successfully. No update needed.")
        
        return verified, updated
    
    def identify_hash_type(self, hashed_password: str) -> str:
        """
        Identify the hash algorithm used based on the format of the hashed password.

        Args:
            hashed_password: The hashed password string to identify

        Returns:
            str: The identified hash type ('bcrypt', 'sha256_crypt', 'pbkdf2_sha256', or 'unknown')
        """
        try:
            if not hashed_password:
                return "unknown"

            # Check for bcrypt formats
            if hashed_password.startswith('$2a$') or hashed_password.startswith('$2b$') or hashed_password.startswith('$2y$'):
                return "bcrypt"

            # Check for sha256_crypt
            elif hashed_password.startswith('$5$'):
                return "sha256_crypt"

            # Check for pbkdf2_sha256
            elif hashed_password.startswith('$pbkdf2-sha256$') or hashed_password.startswith('$django$'):
                return "pbkdf2_sha256"

            # Check for hex_sha256 (64 char hex string)
            elif all(c in '0123456789abcdef' for c in hashed_password.lower()) and len(hashed_password) == 64:
                return "hex_sha256"

            # Unknown format
            else:
                return "unknown"
        except Exception as e:
            # Log the error but don't crash
            logger.warning(f"Error identifying hash type: {str(e)}")
            return "unknown"
    
    
class BcryptHash(HashInterface):
    def __init__(self):
        # Support both bcrypt and older hash formats for migration
        self.__crypt_context = CryptContext(
            schemes=["bcrypt", "sha256_crypt", "hex_sha256", "pbkdf2_sha256"],
            default="bcrypt",
            deprecated=["sha256_crypt", "hex_sha256", "pbkdf2_sha256"]
        )

    def hash(self, password: str) -> str:
        try:
            # Log that we're creating a new hash
            logger.debug(f"Creating new password hash")
            
            # Ensure password is properly encoded before hashing
            if isinstance(password, str):
                # Make sure we're working with UTF-8 encoded strings consistently
                password_normalized = password.encode('utf-8').decode('utf-8')
            else:
                # If it's already bytes, decode to string for passlib
                password_normalized = password.decode('utf-8') if isinstance(password, bytes) else str(password)
            
            # Generate the hash using passlib's CryptContext
            hashed = self.__crypt_context.hash(password_normalized)
            
            # Log hash type for debugging
            hash_type = "bcrypt" if hashed.startswith('$2') else "other"
            logger.debug(f"Created new password hash of type: {hash_type}")
            
            return hashed
        except Exception as e:
            # Log any errors that occur during hashing
            logger.error(f"Error creating password hash: {str(e)}")
            
            # Fallback to default implementation if an error occurs
            return self.__crypt_context.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        # Log hash information for debugging
        if hashed_password.startswith('$2'):
            logger.debug(f"Verifying bcrypt password hash: {hashed_password[:10]}...")
        else:
            logger.debug(f"Verifying non-bcrypt hash type: {hashed_password[:10]}...")
            
        # First try using direct bcrypt verification
        if hashed_password.startswith('$2'):
            try:
                import bcrypt
                
                # Convert password to bytes if it's a string
                pwd_bytes = password.encode('utf-8') if isinstance(password, str) else password
                
                # Convert hash to bytes if it's a string
                hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
                
                # Try direct bcrypt verification
                result = bcrypt.checkpw(pwd_bytes, hash_bytes)
                if result:
                    logger.debug("Password verified successfully with direct bcrypt")
                    return True
                logger.debug("Password verification failed with direct bcrypt")
            except Exception as e:
                logger.warning(f"Direct bcrypt verification failed: {str(e)}")
                # Continue to passlib fallback
        
        # Try passlib CryptContext verification
        try:
            result = self.__crypt_context.verify(password, hashed_password)
            if result:
                logger.debug("Password verified successfully with passlib CryptContext")
                return True
            logger.debug("Password verification failed with passlib CryptContext")
        except Exception as e:
            logger.warning(f"Passlib CryptContext verification failed: {str(e)}")
            # Continue to sha256 fallback
            
        # Fallback for unrecognized hash formats
        # Try the Sha256Hash verifier as a last resort
        try:
            logger.warning(f"bcrypt hash failed to verify. Attempting to verify using sha256_crypt scheme")
            sha256_context = CryptContext(
                schemes=["sha256_crypt", "hex_sha256", "pbkdf2_sha256"],
                deprecated="auto"
            )
            result = sha256_context.verify(password, hashed_password)
            if result:
                logger.debug("Password verified successfully with sha256_crypt fallback")
                return True
            logger.debug("Password verification failed with sha256_crypt fallback")
        except Exception as e:
            logger.critical(f"Failed to verify password using sha256_crypt scheme: {str(e)}")
            
        # If all verification attempts fail, return False
        return False
    
    def verify_and_update(self, password: str, hashed_password: str) -> Tuple[bool, str]:
        """
        Verifies the password and updates the hash if necessary.
        """
        verified, updated = self.__crypt_context.verify_and_update(password, hashed_password)
        
        if not verified and updated is None:
            logger.error(f"Failed to verify the password. Password is not updated.")
            
        if verified and updated is not None:
            logger.info(f"Password verified successfully. Hash updated.")
        else:
            logger.info(f"Password verified successfully. No update needed.")
        
        return verified, updated
        
    def identify_hash_type(self, hashed_password: str) -> str:
        """
        Identify the hash algorithm used based on the format of the hashed password.

        Args:
            hashed_password: The hashed password string to identify

        Returns:
            str: The identified hash type ('bcrypt', 'sha256_crypt', 'pbkdf2_sha256', or 'unknown')
        """
        try:
            if not hashed_password:
                return "unknown"

            # Check for bcrypt formats
            if hashed_password.startswith('$2a$') or hashed_password.startswith('$2b$') or hashed_password.startswith('$2y$'):
                return "bcrypt"

            # Check for sha256_crypt
            elif hashed_password.startswith('$5$'):
                return "sha256_crypt"

            # Check for pbkdf2_sha256
            elif hashed_password.startswith('$pbkdf2-sha256$') or hashed_password.startswith('$django$'):
                return "pbkdf2_sha256"

            # Check for hex_sha256 (64 char hex string)
            elif all(c in '0123456789abcdef' for c in hashed_password.lower()) and len(hashed_password) == 64:
                return "hex_sha256"

            # Unknown format
            else:
                return "unknown"
        except Exception as e:
            # Log the error but don't crash
            logger.warning(f"Error identifying hash type: {str(e)}")
            return "unknown"