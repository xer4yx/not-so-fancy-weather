import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from core.services import AuthService
from interfaces.api.di import get_auth_service
from interfaces.api.routers.user_router import user_router
from interfaces.api.routers.auth_router import auth_router, get_current_user
from interfaces.api.di import get_user_service, get_preferences_service, get_auth_service

# Make sure user_router is included in the app
app.include_router(user_router)
client = TestClient(app)

@pytest.fixture
def mock_user_service():
    user_service = MagicMock()
    user_service.read_user.return_value = {
        "_id": "user123",
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "is_deleted": False
    }
    user_service.create_user.return_value = "user123"
    user_service.update_user.return_value = "user123"
    user_service.delete_user.return_value = True
    user_service.soft_delete_user.return_value = "user123"
    
    app.dependency_overrides[get_user_service] = lambda: user_service
    return user_service

@pytest.fixture
def mock_preferences_service():
    preferences_service = MagicMock()
    preferences_service.get_preferences_by_user_id.return_value = {
        "_id": "pref123",
        "user_id": "user123",
        "username": "testuser",
        "theme": "light",
        "units": "metric"
    }
    preferences_service.create_preferences.return_value = "pref123"
    preferences_service.update_preferences_by_user_id.return_value = "pref123"
    
    app.dependency_overrides[get_preferences_service] = lambda: preferences_service
    return preferences_service

@pytest.fixture
def mock_auth_service():
    mock_auth_service = MagicMock(spec=AuthService)
    mock_auth_service.get_hash.side_effect = lambda password: f"hashed_{password}"
    mock_auth_service.verify_hash.return_value = True  # <- Important fix here

    # Override the auth_service dependency in FastAPI
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    return mock_auth_service

@pytest.fixture
def mock_current_user():
    current_user = {
        "_id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "password": "hashed_password",  # SHA256 hash format
        "is_deleted": False
    }
    
    app.dependency_overrides[get_current_user] = lambda: current_user
    return current_user

@pytest.mark.asyncio
async def test_get_current_user_profile(mock_current_user):
    # Test get current user profile endpoint
    response = client.get("/v1/user/me")
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == mock_current_user

@pytest.mark.asyncio
async def test_update_current_user_profile(mock_user_service, mock_current_user):
    # Reset mock
    mock_user_service.update_user.reset_mock()
    
    # Setup - Need to make sure a username check will succeed, not return a user
    # Otherwise we get a 409 Conflict for existing username
    mock_user_service.read_user.side_effect = [None, None]  # First for username check, then email check
    
    # Test update current user profile endpoint
    response = client.post(
        "/v1/user/me",
        json={"email": "updated@example.com", "is_2fa_enabled": True}
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == "user123"
    
    # Verify service calls
    mock_user_service.update_user.assert_called_once_with(
        key="username", 
        id="testuser", 
        data={"email": "updated@example.com", "is_2fa_enabled": True}
    )

@pytest.mark.asyncio
def test_change_password_success(mock_auth_service, mock_user_service, mock_current_user):
    mock_user_service.update_user.reset_mock()
    mock_auth_service.verify_hash.reset_mock()
    mock_auth_service.get_hash.reset_mock()
    
    # Call the endpoint
    response = client.post(
        "/v1/user/password",
        json={
            "current_password": "hashed_password",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password updated successfully"
    mock_auth_service.get_hash.assert_called_once_with("newpassword123")
    mock_auth_service.verify_hash.assert_called_once()

@pytest.mark.asyncio
async def test_change_password_with_login(mock_auth_service, mock_user_service, mock_current_user):
    # Setup - reset mocks
    mock_user_service.update_user.reset_mock()
    mock_user_service.read_user.reset_mock()
    mock_auth_service.verify_hash.reset_mock()
    mock_auth_service.get_hash.reset_mock()
    mock_auth_service.create_tokens.reset_mock()
    
    # 1. First change the password
    mock_auth_service.get_hash.return_value = "hashed_newpassword123"
    
    change_response = client.post(
        "/v1/user/password",
        json={
            "current_password": "hashed_password",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
    )
    
    assert change_response.status_code == 200
    assert change_response.json()["message"] == "Password updated successfully"
    
    # Verify password was updated
    mock_user_service.update_user.assert_called_once_with(
        key="username", 
        id="testuser", 
        data={"password": "hashed_newpassword123"}
    )
    
    # 2. Now setup for login with new password
    # Update mock to return user with the new password
    updated_user = {
        "_id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "password": "hashed_newpassword123",
        "is_deleted": False
    }
    mock_user_service.read_user.return_value = updated_user
    
    # Setup auth mocks
    mock_auth_service.verify_hash.side_effect = lambda password, hashed: password == "newpassword123" and hashed == "hashed_newpassword123"
    mock_auth_service.create_tokens.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token"
    }
    
    # 3. Now attempt to login with the new password
    # Make sure auth_router is included for this test
    if auth_router not in app.routes:
        app.include_router(auth_router)
    
    login_response = client.post(
        "/v1/login",
        data={"username": "testuser", "password": "newpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # 4. Assert login was successful
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["access_token"] == "new_access_token"
    assert token_data["refresh_token"] == "new_refresh_token"
    assert token_data["token_type"] == "bearer"
    
    # Verify auth service was called with correct params
    mock_auth_service.verify_hash.assert_called_with("newpassword123", "hashed_newpassword123")

@pytest.mark.asyncio
async def test_create_user(mock_user_service):
    # Set up mock for user doesn't exist yet
    mock_user_service.read_user.side_effect = [None, None]  # For username check and email check
    
    # Reset create_user mock
    mock_user_service.create_user.reset_mock()
    
    # Test create user endpoint
    response = client.post(
        "/v1/user",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == "user123"
    
    # Verify service calls
    assert mock_user_service.read_user.call_count == 2  # Check for existing username and email
    mock_user_service.create_user.assert_called_once_with(
        username="newuser",
        email="newuser@example.com",
        password="password123"
    )

@pytest.mark.asyncio
async def test_read_user(mock_user_service):
    # Reset mock
    mock_user_service.read_user.reset_mock()
    
    # Test read user endpoint
    response = client.get("/v1/user?key=username&value=testuser")
    
    # Assert response
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    
    # Verify service calls
    mock_user_service.read_user.assert_called_once_with(key="username", value="testuser")

@pytest.mark.asyncio
async def test_update_user(mock_user_service):
    # Reset mocks
    mock_user_service.read_user.reset_mock()
    mock_user_service.update_user.reset_mock()
    
    # Setup - Need to make sure a username check will succeed, not return a user
    # For username conflict check
    mock_user_service.read_user.side_effect = [{"username": "testuser"}, None]
    
    # Test update user endpoint
    response = client.put(
        "/v1/user?key=username&value=testuser",
        json={"email": "updated@example.com", "is_2fa_enabled": True}
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == "user123"
    
    # Verify service calls - check the key parts but don't be too strict
    assert mock_user_service.read_user.call_count > 0
    mock_user_service.update_user.assert_called_once_with(
        key="username", 
        id="testuser", 
        data={"email": "updated@example.com", "is_2fa_enabled": True}
    )

@pytest.mark.asyncio
async def test_delete_user(mock_user_service):
    # Reset mocks
    mock_user_service.read_user.reset_mock()
    mock_user_service.delete_user.reset_mock()
    
    # Test delete user endpoint
    response = client.delete("/v1/user?key=username&value=testuser")
    
    # Assert response
    assert response.status_code == 200
    assert response.json() is True
    
    # Verify service calls
    mock_user_service.read_user.assert_called_once_with(key="username", value="testuser")
    mock_user_service.delete_user.assert_called_once_with(key="username", id="testuser")

@pytest.mark.asyncio
async def test_soft_delete_user(mock_user_service):
    # Reset mocks
    mock_user_service.read_user.reset_mock()
    mock_user_service.soft_delete_user.reset_mock()
    
    # Test soft delete user endpoint
    response = client.put("/v1/user/soft-delete?key=username&value=testuser")
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == "user123"
    
    # Verify service calls
    mock_user_service.read_user.assert_called_once_with(key="username", value="testuser")
    mock_user_service.soft_delete_user.assert_called_once_with(key="username", id="testuser")

@pytest.mark.asyncio
async def test_get_user_preferences(mock_preferences_service, mock_current_user):
    # Reset mock
    mock_preferences_service.get_preferences_by_user_id.reset_mock()
    
    # Test get user preferences endpoint
    response = client.get("/v1/user/preferences")
    
    # Assert response
    assert response.status_code == 200
    preferences = response.json()
    assert preferences["user_id"] == "user123"
    assert preferences["username"] == "testuser"
    assert preferences["theme"] == "light"
    
    # Verify service calls
    mock_preferences_service.get_preferences_by_user_id.assert_called_once_with("user123")

@pytest.mark.asyncio
async def test_update_user_preferences(mock_preferences_service, mock_current_user):
    # Reset mock
    mock_preferences_service.update_preferences_by_user_id.reset_mock()
    
    # Test update user preferences endpoint
    response = client.post(
        "/v1/user/preferences",
        json={
            "user_id": "user123",
            "username": "testuser",
            "theme": "dark",
            "units": "imperial"
        }
    )
    
    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "Preferences updated successfully"}
    
    # Verify service calls
    mock_preferences_service.update_preferences_by_user_id.assert_called_once_with(
        user_id="user123",
        data={
            "user_id": "user123",
            "username": "testuser",
            "theme": "dark",
            "units": "imperial"
        }
    ) 