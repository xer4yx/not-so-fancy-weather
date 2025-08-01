"""
Test suite for authentication components:
- JWT token creation and verification
- Password hashing and verification
- Token blacklisting
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import time
import os
import sys

from infrastructure.auth.jwt import JWTAuth
from infrastructure.auth.crypt import Sha256Hash, BcryptHash
from infrastructure.auth.blacklist import TokenBlacklist

# Mock logger to avoid file operations during tests
mock_logger = MagicMock()


class TestJWTAuth(unittest.TestCase):
    """Test the JWT authentication implementation"""
    
    @patch('infrastructure.logger.factory.get_logger', return_value=mock_logger)
    def setUp(self, mock_get_logger):
        """Set up test environment"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, project_root)
        self.auth = JWTAuth()
        self.test_payload = {
            "sub": "test_user_id",
            "username": "test_user"
        }

    def test_access_token_creation(self):
        """Test creating an access token"""
        token = self.auth.create_access_token(self.test_payload)
        
        # Assertions to verify token was created
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)
        
        # Verify the token
        payload = self.auth.verify_token(token, "access")
        self.assertEqual(payload["sub"], self.test_payload["sub"])
        self.assertEqual(payload["username"], self.test_payload["username"])
        self.assertEqual(payload["token_type"], "access")

    def test_refresh_token_creation(self):
        """Test creating a refresh token"""
        token = self.auth.create_refresh_token(self.test_payload)
        
        # Assertions to verify token was created
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 0)
        
        # Verify the token
        payload = self.auth.verify_token(token, "refresh")
        self.assertEqual(payload["sub"], self.test_payload["sub"])
        self.assertEqual(payload["username"], self.test_payload["username"])
        self.assertEqual(payload["token_type"], "refresh")

    def test_token_expiration(self):
        """Test token expiration validation"""
        # Use a private method to create a token with very short expiration
        token = self.auth._JWTAuth__create_token(
            self.test_payload.copy(),
            expires_delta=timedelta(seconds=1)
        )
        
        # Verify token works initially
        payload = self.auth.verify_token(token, "access")
        self.assertEqual(payload["sub"], self.test_payload["sub"])
        
        # Wait for token to expire
        time.sleep(2)
        
        # Verify token fails after expiration
        with self.assertRaises(ValueError):
            self.auth.verify_token(token, "access")

    def test_token_type_validation(self):
        """Test token type validation"""
        # Create an access token but try to verify as refresh
        token = self.auth.create_access_token(self.test_payload)
        
        with self.assertRaises(ValueError):
            self.auth.verify_token(token, "refresh")
            
        # Create a refresh token but try to verify as access
        token = self.auth.create_refresh_token(self.test_payload)
        
        with self.assertRaises(ValueError):
            self.auth.verify_token(token, "access")

    def test_token_blacklisting(self):
        """Test token blacklisting functionality"""
        token = self.auth.create_access_token(self.test_payload)
        
        # Verify token works before blacklisting
        payload = self.auth.verify_token(token, "access")
        self.assertEqual(payload["sub"], self.test_payload["sub"])
        
        # Blacklist the token
        self.auth.blacklist_token(token)
        
        # Verify token fails after blacklisting
        with self.assertRaises(ValueError):
            self.auth.verify_token(token, "access")


class TestPasswordHashing(unittest.TestCase):
    """Test password hashing implementations"""
    
    def setUp(self):
        """Set up test environment"""
        self.sha256_hasher = Sha256Hash()
        self.bcrypt_hasher = BcryptHash()
        self.test_password = "secure_password123"

    def test_sha256_hash_and_verify(self):
        """Test SHA256 password hashing and verification"""
        hashed = self.sha256_hasher.hash(self.test_password)
        
        # Assertions to verify hash was created
        self.assertIsNotNone(hashed)
        self.assertTrue(len(hashed) > 0)
        
        # Verify correct password
        self.assertTrue(self.sha256_hasher.verify(self.test_password, hashed))
        
        # Verify incorrect password
        self.assertFalse(self.sha256_hasher.verify("wrong_password", hashed))

    def test_bcrypt_hash_and_verify(self):
        """Test Bcrypt password hashing and verification"""
        hashed = self.bcrypt_hasher.hash(self.test_password)
        
        # Assertions to verify hash was created
        self.assertIsNotNone(hashed)
        self.assertTrue(len(hashed) > 0)
        
        # Verify correct password
        self.assertTrue(self.bcrypt_hasher.verify(self.test_password, hashed))
        
        # Verify incorrect password
        self.assertFalse(self.bcrypt_hasher.verify("wrong_password", hashed))


class TestTokenBlacklist(unittest.TestCase):
    """Test token blacklist implementation"""
    
    @patch('infrastructure.logger.factory.get_logger', return_value=mock_logger)
    def setUp(self, mock_get_logger):
        """Set up test environment"""
        # Reset singleton instance to avoid test interference
        TokenBlacklist._instance = None
        self.blacklist = TokenBlacklist()

    def test_add_and_check_token(self):
        """Test adding tokens to blacklist and checking"""
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
        
        # Verify token is not blacklisted initially
        self.assertFalse(self.blacklist.is_blacklisted(test_token))
        
        # Add token to blacklist
        self.blacklist.add(test_token)
        
        # Verify token is now blacklisted
        self.assertTrue(self.blacklist.is_blacklisted(test_token))

    def test_token_expiry_cleanup(self):
        """Test automatic cleanup of expired tokens"""
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired_token"
        
        # Add token with expiry in the past
        past_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.blacklist.add(test_token, expires_at=past_time)
        
        # Force cleanup by manipulating last_cleanup time
        self.blacklist.last_cleanup = datetime.now(timezone.utc) - timedelta(hours=2)
        
        # Check token - this should trigger cleanup
        self.assertFalse(self.blacklist.is_blacklisted(test_token))
        self.assertNotIn(test_token, self.blacklist.blacklisted_tokens)


if __name__ == "__main__":
    unittest.main() 