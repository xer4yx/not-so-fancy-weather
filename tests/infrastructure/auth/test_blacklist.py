"""
Comprehensive test suite for token blacklist implementation.
Tests include:
- Basic token storage and retrieval
- Token expiry and cleanup mechanisms
- Edge cases and error handling
- Thread safety (where applicable)
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
import time
import os
import sys

from infrastructure.auth.blacklist import TokenBlacklist

# Mock logger to avoid file operations during tests
mock_logger = MagicMock()


class TestTokenBlacklist(unittest.TestCase):
    """Test the token blacklist implementation"""
    
    @patch('infrastructure.logger.factory.get_logger', return_value=mock_logger)
    def setUp(self, mock_get_logger):
        """Set up test environment"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        # Reset singleton instance to avoid test interference
        TokenBlacklist._instance = None
        self.blacklist = TokenBlacklist()
        self.test_tokens = [
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.first_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.second_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.third_token"
        ]

    def test_singleton_pattern(self):
        """Test that TokenBlacklist follows singleton pattern"""
        another_instance = TokenBlacklist()
        self.assertIs(self.blacklist, another_instance)
        
        # Add token to first instance
        self.blacklist.add(self.test_tokens[0])
        
        # Check token in second instance
        self.assertTrue(another_instance.is_blacklisted(self.test_tokens[0]))

    def test_add_and_check_token(self):
        """Test adding tokens to blacklist and checking their presence"""
        # Verify tokens are not blacklisted initially
        for token in self.test_tokens:
            self.assertFalse(self.blacklist.is_blacklisted(token))
        
        # Add tokens to blacklist
        for token in self.test_tokens:
            self.blacklist.add(token)
        
        # Verify tokens are now blacklisted
        for token in self.test_tokens:
            self.assertTrue(self.blacklist.is_blacklisted(token))

    def test_token_with_custom_expiry(self):
        """Test token with custom expiry time"""
        token = self.test_tokens[0]
        
        # Set expiry far in the future
        future_time = datetime.now(timezone.utc) + timedelta(days=30)
        self.blacklist.add(token, expires_at=future_time)
        
        # Token should be blacklisted
        self.assertTrue(self.blacklist.is_blacklisted(token))
        self.assertIn(token, self.blacklist.blacklisted_tokens)
        
        # Check that expiry time was set correctly
        self.assertEqual(self.blacklist.blacklisted_tokens[token], future_time)

    def test_expired_token_cleanup(self):
        """Test automatic cleanup of expired tokens"""
        # Add tokens with different expiry times
        now = datetime.now(timezone.utc)
        
        # Token expired in the past
        past_token = self.test_tokens[0]
        past_time = now - timedelta(seconds=2)
        self.blacklist.add(past_token, expires_at=past_time)
        
        # Token expiring in the future
        future_token = self.test_tokens[1]
        future_time = now + timedelta(days=1)
        self.blacklist.add(future_token, expires_at=future_time)
        
        # Force cleanup by manipulating last_cleanup time
        self.blacklist.last_cleanup = now - timedelta(hours=2)
        
        # Check tokens - this should trigger cleanup
        self.assertFalse(self.blacklist.is_blacklisted(past_token))
        self.assertTrue(self.blacklist.is_blacklisted(future_token))
        
        # Verify past token is removed from internal dict
        self.assertNotIn(past_token, self.blacklist.blacklisted_tokens)
        self.assertIn(future_token, self.blacklist.blacklisted_tokens)

    def test_handle_missing_timezone(self):
        """Test handling of datetime without timezone info"""
        token = self.test_tokens[0]
        
        # Create datetime without timezone
        naive_datetime = datetime.now() + timedelta(days=1)
        self.blacklist.add(token, expires_at=naive_datetime)
        
        # Token should be blacklisted
        self.assertTrue(self.blacklist.is_blacklisted(token))
        
        # Verify expiry has timezone info attached
        self.assertIsNotNone(self.blacklist.blacklisted_tokens[token].tzinfo)

    def test_empty_token_handling(self):
        """Test handling of empty token"""
        empty_token = ""
        
        # Add empty token
        self.blacklist.add(empty_token)
        
        # Should be blacklisted
        self.assertTrue(self.blacklist.is_blacklisted(empty_token))

    def test_exception_handling(self):
        """Test error handling in blacklist operations"""
        token = self.test_tokens[0]
        
        # Mock an exception during add by replacing the dictionary with a MagicMock
        # that raises an exception on __setitem__
        original_dict = self.blacklist.blacklisted_tokens
        mock_dict = MagicMock()
        mock_dict.__setitem__.side_effect = Exception("Test error")
        mock_dict.__contains__.return_value = False  # For initial is_blacklisted check
        
        # Replace the dictionary with our mock
        self.blacklist.blacklisted_tokens = mock_dict
        
        # Should raise the exception
        with self.assertRaises(Exception):
            self.blacklist.add(token)
            
        # Restore the original dictionary
        self.blacklist.blacklisted_tokens = original_dict
        
        # Mock an exception during is_blacklisted
        with patch.object(self.blacklist, 'blacklisted_tokens', new_callable=MagicMock) as mock_blacklist:
            mock_blacklist.__contains__.side_effect = Exception("Test error")
            
            # Should return True as a safety measure
            self.assertTrue(self.blacklist.is_blacklisted(token))
            
    def test_cleanup_does_not_affect_valid_tokens(self):
        """Test that cleanup doesn't remove valid tokens"""
        # Add a token that shouldn't expire
        valid_token = self.test_tokens[0]
        future_time = datetime.now(timezone.utc) + timedelta(days=7)
        self.blacklist.add(valid_token, expires_at=future_time)
        
        # Add a token that should expire
        expired_token = self.test_tokens[1]
        past_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.blacklist.add(expired_token, expires_at=past_time)
        
        # Force cleanup
        self.blacklist._cleanup_expired()
        
        # Check tokens after cleanup
        self.assertTrue(self.blacklist.is_blacklisted(valid_token))
        self.assertFalse(self.blacklist.is_blacklisted(expired_token))


if __name__ == "__main__":
    unittest.main() 