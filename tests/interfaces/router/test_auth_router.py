import time
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from interfaces.api.routers.auth_router import auth_router, get_auth_service, get_user_service

app.include_router(auth_router)
client = TestClient(app)

@pytest.fixture
def mock_auth_service():
    auth_service = MagicMock()
    auth_service.verify_hash.return_value = True
    auth_service.verify_and_update.return_value = (True, None)
    auth_service.create_tokens.return_value = {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token"
    }
    auth_service.verify_token.return_value = {"username": "testuser"}
    auth_service.blacklist_token.return_value = True
    
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    return auth_service

@pytest.fixture
def mock_user_service():
    user_service = MagicMock()
    user_service.read_user.return_value = {
        "username": "testuser",
        "password": "$2b$12$mock_hashed_password",
        "email": "test@example.com",
        "is_deleted": False
    }
    app.dependency_overrides[get_user_service] = lambda: user_service
    return user_service

@pytest.mark.asyncio
async def test_login_success(mock_auth_service, mock_user_service):
    # Make sure read_user returns a valid user
    mock_user_service.read_user.return_value = {
        "username": "testuser",
        "password": "$2b$12$mock_hashed_password",
        "email": "test@example.com",
        "is_deleted": False
    }
    
    # Reset mocks to ensure clean test
    mock_user_service.read_user.reset_mock()
    mock_auth_service.verify_hash.reset_mock()
    mock_auth_service.create_tokens.reset_mock()
    
    # Test login endpoint
    response = client.post(
        "/v1/login",
        data={"username": "testuser", "password": "password123"}
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer"
    }
    
    # Verify service calls with more precise assertions
    mock_user_service.read_user.assert_called_with(key="username", value="testuser")
    # For parameters we don't know exactly, we can use assert_called
    assert mock_auth_service.verify_hash.call_count > 0
    assert mock_auth_service.create_tokens.call_count > 0

@pytest.mark.asyncio
async def test_login_missing_data(mock_auth_service, mock_user_service):
    """Test login with missing username or password"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Test with missing username
        response = client.post(
            "/v1/login",
            data={"password": "password123"}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test with missing password
        response = client.post(
            "/v1/login",
            data={"username": "testuser"}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test with empty body
        response = client.post("/v1/login", data={})
        assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_auth_service, mock_user_service):
    # Mock verification to fail
    
    mock_auth_service.verify_hash.reset_mock()
    mock_auth_service.verify_and_update.reset_mock()
    
    mock_auth_service.verify_hash.return_value = False
    mock_auth_service.verify_and_update.return_value = (False, None)
    
    # Mock additional methods that are called during login
    mock_auth_service.get_hash.return_value = "$2b$12$mock_new_hash"
    mock_auth_service.identify_hash_type.return_value = "bcrypt"
    
    # Test login endpoint with invalid credentials
    response = client.post(
        "/v1/login",
        data={"username": "testuser", "password": "wrong_password"}
    )
    
    # Assert response
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_user_not_found(mock_auth_service, mock_user_service):
    # Mock user not found
    mock_user_service.read_user.return_value = None
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Test login endpoint with non-existent user
        response = client.post(
            "/v1/login",
            data={"username": "nonexistent", "password": "password123"}
        )
        
        # Assert response
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_deleted_user(mock_auth_service, mock_user_service):
    """Test login with a user that has been soft-deleted"""
    # Mock a deleted user
    mock_user_service.read_user.return_value = {
        "username": "testuser",
        "password": "$2b$12$mock_hashed_password",
        "email": "test@example.com",
        "is_deleted": True  # User is soft-deleted
    }
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Test login endpoint
        response = client.post(
            "/v1/login",
            data={"username": "testuser", "password": "password123"}
        )
        
        # Assert response
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_server_error(mock_auth_service, mock_user_service):
    """Test login with server error"""
    # Setup user service to raise an exception
    mock_user_service.read_user.side_effect = Exception("Database error")
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Test login endpoint
        response = client.post(
            "/v1/login",
            data={"username": "testuser", "password": "password123"}
        )
        
        # Assert response
        assert response.status_code == 500
        assert "An error occurred during login" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_performance(mock_auth_service, mock_user_service):
    """Test login performance"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Measure response time
        start_time = time.time()
        response = client.post(
            "/v1/login",
            data={"username": "testuser", "password": "password123"}
        )
        end_time = time.time()
        
        # Assert response time is acceptable (adjust threshold as needed)
        assert end_time - start_time < 1.0  # Should respond in less than 1 second
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_refresh_token_success(mock_auth_service):
    # Setup token verification mock to return a proper payload
    mock_auth_service.verify_token.return_value = {
        "username": "testuser",
        "token_type": "refresh"
    }
    
    # Only patch jwt.decode since the dependency is already overridden in the fixture
    with patch("interfaces.api.routers.auth_router.jwt.decode", return_value={"username": "testuser", "token_type": "refresh"}):
        
        # Reset mocks to ensure clean test
        mock_auth_service.verify_token.reset_mock()
        mock_auth_service.create_tokens.reset_mock()
        
        # Remove any side effects
        mock_auth_service.verify_token.side_effect = None
        
        # Test refresh token endpoint
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )
        
        # Assert response
        assert response.status_code == 200
        assert response.json() == {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "token_type": "bearer"
        }
        
        # Verify service calls with more flexible assertions
        mock_auth_service.verify_token.assert_any_call(
            token="valid_refresh_token", 
            token_type="refresh"
        )
        assert mock_auth_service.create_tokens.call_count > 0

@pytest.mark.asyncio
async def test_refresh_missing_token(mock_auth_service):
    """Test refresh endpoint with missing token"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Test with empty request body
        response = client.post(
            "/v1/refresh",
            json={}
        )
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test with null token
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": None}
        )
        assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_refresh_empty_token(mock_auth_service):
    """Test refresh endpoint with empty token string"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Mock token verification to fail with empty string
        mock_auth_service.verify_token.side_effect = ValueError("Invalid token")
        
        # Test with empty token string
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": ""}
        )
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token_invalid(mock_auth_service):
    # Mock token verification to fail
    mock_auth_service.verify_token.side_effect = ValueError("Invalid token")
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Test refresh token endpoint with invalid token
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        # Assert response
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token_missing_username(mock_auth_service):
    """Test refresh endpoint with token missing username"""
    # Setup token verification to return payload without username
    mock_auth_service.verify_token.return_value = {
        "token_type": "refresh"
        # Missing username
    }
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Test refresh token endpoint
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": "valid_token_no_username"}
        )
        
        # Assert response
        assert response.status_code == 401
        assert "Invalid token: missing username" in response.json()["detail"]

@pytest.mark.asyncio
async def test_refresh_token_server_error(mock_auth_service):
    """Test refresh endpoint with server error"""
    # Setup create_tokens to raise an exception
    mock_auth_service.verify_token.return_value = {"username": "testuser", "token_type": "refresh"}
    mock_auth_service.create_tokens.side_effect = Exception("Token creation error")
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Test refresh token endpoint
        response = client.post(
            "/v1/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )
        
        # Assert response
        assert response.status_code == 500
        assert "An error occurred during token refresh" in response.json()["detail"]

@pytest.mark.asyncio
async def test_logout_success(mock_auth_service):
    # Only patch jwt.decode since the dependency is already overridden in the fixture
    with patch("interfaces.api.routers.auth_router.jwt.decode", return_value={"username": "testuser", "token_type": "access"}):
        
        # Reset mock call counts to ensure clean test
        mock_auth_service.blacklist_token.reset_mock()
        
        # Make sure the mock method doesn't have any side effects that could cause it to fail
        mock_auth_service.blacklist_token.side_effect = None
        
        # Test logout endpoint
        response = client.post(
            "/v1/logout",
            json={
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token"
            }
        )
        
        # Assert response
        assert response.status_code == 204  # No Content
        assert response.content == b''  # Empty response body
        
        # Verify service calls using more precise assertions
        mock_auth_service.blacklist_token.assert_any_call("valid_access_token")
        mock_auth_service.blacklist_token.assert_any_call("valid_refresh_token")

@pytest.mark.asyncio
async def test_logout_without_refresh_token(mock_auth_service):
    """Test logout with only access token (refresh token is optional)"""
    # Only need to patch jwt.decode since the dependency is already overridden in the fixture
    with patch("interfaces.api.routers.auth_router.jwt.decode", return_value={"username": "testuser", "token_type": "access"}):
        
        # Reset mock call counts
        mock_auth_service.blacklist_token.reset_mock()
        
        # Make sure the mock method doesn't have any side effects that could cause it to fail
        mock_auth_service.blacklist_token.side_effect = None
        
        # Test logout endpoint with only access token
        response = client.post(
            "/v1/logout",
            json={"access_token": "valid_access_token"}
        )
        
        # Assert response
        assert response.status_code == 204
        
        # Verify that blacklist_token was called at least once with the access token
        mock_auth_service.blacklist_token.assert_any_call("valid_access_token")

@pytest.mark.asyncio
async def test_logout_missing_access_token(mock_auth_service):
    """Test logout with missing access token (which is required)"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service):
        
        # Test with missing access token
        response = client.post(
            "/v1/logout",
            json={"refresh_token": "valid_refresh_token"}
        )
        
        # Assert response (missing required field)
        assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_logout_blacklist_error(mock_auth_service):
    """Test logout when token blacklisting fails"""
    # Setup blacklist_token to fail
    mock_auth_service.blacklist_token.side_effect = Exception("Failed to blacklist token")
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.jwt.decode", return_value={"username": "testuser", "token_type": "access"}):
        
        # Test logout endpoint
        response = client.post(
            "/v1/logout",
            json={
                "access_token": "valid_access_token",
                "refresh_token": "valid_refresh_token"
            }
        )
        
        # Assert response is still successful (errors are logged but not propagated)
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_logout_invalid_token_format(mock_auth_service):
    """Test logout with invalid token format"""
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.jwt.decode", side_effect=Exception("Invalid token format")):
        
        # Test logout endpoint with malformed token
        response = client.post(
            "/v1/logout",
            json={
                "access_token": "invalid_format_token",
                "refresh_token": "valid_refresh_token"
            }
        )
        
        # Assert response is still successful (token verification errors are caught and logged)
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_get_current_user_success(mock_auth_service, mock_user_service):
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        # Reset mocks to ensure clean test
        mock_auth_service.verify_token.reset_mock()
        mock_user_service.read_user.reset_mock()
        
        # Remove any side effects
        mock_auth_service.verify_token.side_effect = None
        
        # Ensure proper return values
        mock_auth_service.verify_token.return_value = {"username": "testuser"}
        mock_user_service.read_user.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "is_deleted": False
        }
        
        # Create a mock request with authorization header
        from interfaces.api.routers.auth_router import get_current_user
        
        # Use the get_current_user dependency directly in a test
        user = await get_current_user(
            token="valid_access_token",
            auth_service=mock_auth_service,
            user_service=mock_user_service
        )
        
        # Assert user data
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        
        # Verify service calls with flexible assertions
        mock_auth_service.verify_token.assert_any_call(
            token="valid_access_token",
            token_type="access"
        )
        mock_user_service.read_user.assert_any_call(
            key="username", 
            value="testuser"
        )

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_auth_service, mock_user_service):
    """Test get_current_user with invalid token"""
    # Setup token verification to fail for both access and refresh token types
    mock_auth_service.verify_token.side_effect = ValueError("Invalid token")
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        from interfaces.api.routers.auth_router import get_current_user
        
        # Test with invalid token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token="invalid_token",
                auth_service=mock_auth_service,
                user_service=mock_user_service
            )
        
        # Assert exception details
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_missing_username(mock_auth_service, mock_user_service):
    """Test get_current_user with token missing username"""
    # Setup token verification to return payload without username
    mock_auth_service.verify_token.return_value = {}  # Empty payload, no username
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        from interfaces.api.routers.auth_router import get_current_user
        
        # Test with token missing username
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token="token_without_username",
                auth_service=mock_auth_service,
                user_service=mock_user_service
            )
        
        # Assert exception details
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_nonexistent(mock_auth_service, mock_user_service):
    """Test get_current_user with valid token but nonexistent user"""
    # Setup token verification to succeed but user lookup to fail
    mock_auth_service.verify_token.return_value = {"username": "nonexistent_user"}
    mock_user_service.read_user.return_value = None
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        from interfaces.api.routers.auth_router import get_current_user
        
        # Test with nonexistent user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token="valid_token_nonexistent_user",
                auth_service=mock_auth_service,
                user_service=mock_user_service
            )
        
        # Assert exception details
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_current_user_deleted(mock_auth_service, mock_user_service):
    """Test get_current_user with valid token but soft-deleted user"""
    # Setup token verification to succeed but user is soft-deleted
    mock_auth_service.verify_token.return_value = {"username": "deleted_user"}
    mock_user_service.read_user.return_value = {
        "username": "deleted_user",
        "email": "deleted@example.com",
        "is_deleted": True
    }
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.auth_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.auth_router.get_user_service", return_value=mock_user_service):
        
        from interfaces.api.routers.auth_router import get_current_user
        
        # Test with soft-deleted user
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                token="valid_token_deleted_user",
                auth_service=mock_auth_service,
                user_service=mock_user_service
            )
        
        # Assert exception details
        assert exc_info.value.status_code == 401
        assert "User is inactive" in str(exc_info.value.detail) 