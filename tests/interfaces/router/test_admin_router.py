import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from interfaces.api.routers.admin_router import admin_router, get_auth_service, get_user_service

client = TestClient(app)
app.include_router(admin_router)

@pytest.fixture
def mock_auth_service():
    auth_service = MagicMock()
    auth_service.verify_hash.return_value = True
    auth_service.get_hash.return_value = "$2b$12$new_hashed_password"
    
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
    user_service.update_user.return_value = "user123"
    
    app.dependency_overrides[get_user_service] = lambda: user_service
    return user_service

@pytest.mark.asyncio
async def test_rehash_user_password(mock_auth_service, mock_user_service):
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=mock_user_service):
        
        # Test rehash user password endpoint
        response = client.post(
            "/v1/admin/rehash-user-password?username=testuser&plain_password=password123"
        )
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["old_hash_type"] == "bcrypt"
        assert data["new_hash_type"] == "bcrypt"
        assert data["success"] is True
        
        # Verify service calls
        mock_user_service.read_user.assert_called_once_with(key="username", value="testuser")
        auth_service = mock_auth_service
        auth_service.verify_hash.assert_called_once_with("password123", "$2b$12$new_hashed_password")
        auth_service.get_hash.assert_called_once_with("password123")
        mock_user_service.update_user.assert_called_once_with(
            key="username", 
            id="testuser", 
            data={"password": "$2b$12$new_hashed_password"}
        )

@pytest.mark.asyncio
async def test_rehash_user_password_not_found(mock_auth_service, mock_user_service):
    # Setup user not found
    mock_user_service.read_user.return_value = None
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=mock_user_service):
        
        # Test rehash user password endpoint with non-existent user
        response = client.post(
            "/v1/admin/rehash-user-password?username=nonexistent&plain_password=password123"
        )
        
        # Assert response
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
        
        # Verify service calls
        mock_user_service.read_user.assert_called_once_with(key="username", value="nonexistent")
        # Ensure other methods were not called
        mock_auth_service.get_hash.assert_not_called()
        mock_user_service.update_user.assert_not_called()

@pytest.mark.asyncio
async def test_rehash_user_password_verification_fail(mock_auth_service, mock_user_service):
    # Setup verification to fail
    mock_auth_service.verify_hash.return_value = False
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=mock_user_service):
        
        # Test rehash user password endpoint with verification failure
        response = client.post(
            "/v1/admin/rehash-user-password?username=testuser&plain_password=password123"
        )
        
        # Assert response
        assert response.status_code == 500
        assert "New hash verification test failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_check_user_hash(mock_auth_service, mock_user_service):
    # Create sample hash with current algorithm
    sample_hash = "$2b$12$sample_hash"
    mock_auth_service.get_hash.return_value = sample_hash
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=mock_user_service):
        
        # Test check user hash endpoint
        response = client.get("/v1/admin/check-user-hash?username=testuser")
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["current_hash_type"] == "bcrypt"
        assert data["expected_hash_type"] == "bcrypt"
        assert data["hash_mismatch"] is False
        
        # Verify service calls
        mock_user_service.read_user.assert_called_once_with(key="username", value="testuser")
        mock_auth_service.get_hash.assert_called_once_with("sample_password_for_hash_check")

@pytest.mark.asyncio
async def test_check_user_hash_mismatch(mock_auth_service, mock_user_service):
    # Setup hash mismatch scenario
    user_service = mock_user_service
    user_service.read_user.return_value["password"] = "$5$mocksha256hashedpassword"
    
    # Create sample hash with current algorithm (bcrypt)
    sample_hash = "$2b$12$sample_hash"
    mock_auth_service.get_hash.return_value = sample_hash
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=user_service):
        
        # Test check user hash endpoint
        response = client.get("/v1/admin/check-user-hash?username=testuser")
        
        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["current_hash_type"] == "sha256_crypt"
        assert data["expected_hash_type"] == "bcrypt"
        assert data["hash_mismatch"] is True
        
        # Verify service calls
        user_service.read_user.assert_called_once_with(key="username", value="testuser")
        mock_auth_service.get_hash.assert_called_once_with("sample_password_for_hash_check")

@pytest.mark.asyncio
async def test_check_user_hash_not_found(mock_auth_service, mock_user_service):
    # Setup user not found
    mock_user_service.read_user.return_value = None
    
    # Setup patching for dependencies
    with patch("interfaces.api.routers.admin_router.get_auth_service", return_value=mock_auth_service), \
         patch("interfaces.api.routers.admin_router.get_user_service", return_value=mock_user_service):
        
        # Test check user hash endpoint with non-existent user
        response = client.get("/v1/admin/check-user-hash?username=nonexistent")
        
        # Assert response
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
        
        # Verify service calls
        mock_user_service.read_user.assert_called_once_with(key="username", value="nonexistent")
        # Ensure other methods were not called
        mock_auth_service.get_hash.assert_not_called() 