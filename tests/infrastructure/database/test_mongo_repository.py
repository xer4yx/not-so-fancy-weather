import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import OperationFailure, ConnectionFailure
from bson import ObjectId

from infrastructure.database.mongo_repository import MongoRepository

class TestMongoRepository:
    @pytest.fixture
    def mock_db_settings(self):
        with patch('infrastructure.database.mongo_repository.NSFWDbSettings') as mock_settings:
            instance = mock_settings.return_value
            instance.MONGO_USERNAME = "test_user"
            instance.MONGO_PASSWORD = "test_password"
            instance.MONGO_DSN = "mongodb+srv://%s:%s@testcluster.mongodb.net/?retryWrites=true&w=majority"
            yield mock_settings
    
    @pytest.fixture
    def mock_client(self):
        with patch('infrastructure.database.mongo_repository.MongoClient') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            
            # Create mock db and collections
            mock_db = MagicMock()
            mock_instance.nsfw_db = mock_db
            
            mock_users_collection = MagicMock()
            mock_preferences_collection = MagicMock()
            
            # Setup dictionary-like access to collections
            mock_db.__getitem__ = lambda self, key: {
                'users': mock_users_collection,
                'preferences': mock_preferences_collection
            }.get(key, MagicMock())
            
            yield mock_client
    
    @pytest.fixture
    def mock_logger(self):
        with patch('infrastructure.database.mongo_repository.get_logger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            yield mock_logger
    
    @pytest.fixture
    def mongo_repo_users(self, mock_db_settings, mock_client, mock_logger):
        return MongoRepository(collection_name='users')
    
    @pytest.fixture
    def mongo_repo_preferences(self, mock_db_settings, mock_client, mock_logger):
        return MongoRepository(collection_name='preferences')
    
    def test_init_connection_success(self, mock_db_settings, mock_client, mock_logger):
        # Test successful connection
        repo = MongoRepository(collection_name='users')
        mock_client.assert_called_once()
        mock_client.return_value.admin.command.assert_called_once_with('ping')
    
    def test_init_connection_failure(self, mock_db_settings, mock_logger):
        # Test connection failure
        with patch('infrastructure.database.mongo_repository.MongoClient') as mock_client:
            mock_client.side_effect = ConnectionFailure("Connection failed")
            
            with pytest.raises(ConnectionFailure) as exc_info:
                MongoRepository(collection_name='users')
            
            assert "Connection failed" in str(exc_info.value)
            mock_logger.return_value.error.assert_called_once()
    
    def test_create_success(self, mongo_repo_users, mock_client):
        # Set up mock for successful creation
        mock_inserted_id = ObjectId()
        mock_client.return_value.nsfw_db['users'].insert_one.return_value.inserted_id = mock_inserted_id
        
        # Test data
        test_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword"
        }
        
        # Call method
        result = mongo_repo_users.create(test_data)
        
        # Assertions
        mock_client.return_value.nsfw_db['users'].insert_one.assert_called_once_with(test_data)
        assert result == str(mock_inserted_id)
    
    def test_create_failure(self, mongo_repo_users, mock_client):
        # Set up mock for failed creation
        mock_client.return_value.nsfw_db['users'].insert_one.side_effect = OperationFailure("Failed to insert")
        
        # Test data
        test_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        # Assert the exception is raised
        with pytest.raises(OperationFailure) as exc_info:
            mongo_repo_users.create(test_data)
        
        assert "Failed to insert" in str(exc_info.value)
    
    def test_read_success_user(self, mongo_repo_users, mock_client):
        # Mock user data
        user_data = {
            "_id": "123abc",
            "username": "testuser",
            "email": "test@example.com",
            "password": "hashedpassword",
            "is_deleted": False,
            "is_2fa_enabled": False
        }
        
        # Set up mock for find_one
        mock_client.return_value.nsfw_db['users'].find_one.return_value = user_data
        
        # Create a mock for the User class and set the name attribute of the mongo_repo_users collection
        mock_user = MagicMock()
        mock_user.model_dump.return_value = user_data
        
        # Important: Set the collection name property so the repository identifies this as 'users'
        mongo_repo_users._MongoRepository__collections.name = 'users'
        
        # Patch the User class in the repository module
        with patch('infrastructure.database.mongo_repository.User') as mock_user_class:
            mock_user_class.model_validate.return_value = mock_user
            
            # Call the method
            result = mongo_repo_users.read("username", "testuser")
            
            # Assertions
            mock_client.return_value.nsfw_db['users'].find_one.assert_called_once_with({"username": "testuser"})
            mock_user_class.model_validate.assert_called_once_with(user_data)
            assert result == user_data
    
    def test_read_success_preferences(self, mongo_repo_preferences, mock_client):
        # Mock preferences data
        pref_data = {
            "_id": "456def",
            "user_id": "123abc",
            "username": "testuser",
            "units": "metric",
            "theme": "dark",
            "defaultLocation": "New York"
        }
        
        # Set up mock for find_one
        mock_client.return_value.nsfw_db['preferences'].find_one.return_value = pref_data
        
        # Create a mock for the Preferences class
        mock_pref = MagicMock()
        mock_pref.model_dump.return_value = pref_data
        
        # Important: Set the collection name property so the repository identifies this as 'preferences'
        mongo_repo_preferences._MongoRepository__collections.name = 'preferences'
        
        # Patch the Preferences class in the repository module
        with patch('infrastructure.database.mongo_repository.Preferences') as mock_pref_class:
            mock_pref_class.model_validate.return_value = mock_pref
            
            # Call the method - this will trigger the model_validate call
            result = mongo_repo_preferences.read("user_id", "123abc")
            
            # Assertions
            mock_client.return_value.nsfw_db['preferences'].find_one.assert_called_once_with({"user_id": "123abc"})
            mock_pref_class.model_validate.assert_called_once_with(pref_data)
            assert result == pref_data
    
    def test_read_not_found(self, mongo_repo_users, mock_client):
        # Set up mock for find_one returning None
        mock_client.return_value.nsfw_db['users'].find_one.return_value = None
        
        # Call the method
        result = mongo_repo_users.read("username", "nonexistent")
        
        # Assertions
        assert result is None
    
    def test_update_success(self, mongo_repo_users, mock_client):
        # Use a valid 24-character hex string for ObjectId
        valid_id = "507f1f77bcf86cd799439011"
        object_id = ObjectId(valid_id)
        
        # Mock user data
        user_data = {
            "_id": object_id,
            "username": "testuser",
            "email": "test@example.com"
        }
        
        # Set up mock for find_one_and_update
        mock_client.return_value.nsfw_db['users'].find_one_and_update.return_value = user_data
        
        # Test data
        updated_data = {
            "email": "newemail@example.com"
        }
        
        # Call method
        result = mongo_repo_users.update("_id", valid_id, updated_data)
        
        # Assertions
        mock_client.return_value.nsfw_db['users'].find_one_and_update.assert_called_once()
        assert result == "1"
    
    def test_update_not_found(self, mongo_repo_users, mock_client):
        # Set up mock for find_one_and_update returning None
        mock_client.return_value.nsfw_db['users'].find_one_and_update.return_value = None
        
        # Test data
        updated_data = {
            "email": "newemail@example.com"
        }
        
        # Assert the exception is raised
        with pytest.raises(OperationFailure) as exc_info:
            mongo_repo_users.update("username", "nonexistent", updated_data)
        
        assert "Could not find record to update" in str(exc_info.value)
    
    def test_delete_success(self, mongo_repo_users, mock_client):
        # Set up mock for delete_many
        mock_client.return_value.nsfw_db['users'].delete_many.return_value.deleted_count = 1
        
        # Call method
        result = mongo_repo_users.delete("username", "testuser")
        
        # Assertions
        mock_client.return_value.nsfw_db['users'].delete_many.assert_called_once_with({"username": "testuser"})
        assert result is True
    
    def test_delete_not_found(self, mongo_repo_users, mock_client):
        # Set up mock for delete_many with no deletions
        mock_client.return_value.nsfw_db['users'].delete_many.return_value.deleted_count = 0
        
        # Call method
        result = mongo_repo_users.delete("username", "nonexistent")
        
        # Assertions
        assert result is False
    
    def test_bulk_update_missing_fields(self, mongo_repo_users, mock_client):
        # Create valid ObjectIds
        object_id_1 = ObjectId("507f1f77bcf86cd799439011")
        object_id_2 = ObjectId("507f1f77bcf86cd799439012")
        
        # Mock documents that need updating
        docs_to_update = [
            {"_id": object_id_1, "username": "user1", "email": "user1@example.com"},
            {"_id": object_id_2, "username": "user2", "email": "user2@example.com"}
        ]
        
        # Set up mock for find returning documents
        mock_client.return_value.nsfw_db['users'].find.return_value = docs_to_update
        
        # Set up mock for update_one
        mock_update_result = MagicMock()
        mock_update_result.modified_count = 1
        mock_client.return_value.nsfw_db['users'].update_one.return_value = mock_update_result
        
        # Call method with missing fields
        missing_fields = {"is_deleted": False, "is_2fa_enabled": False}
        result = mongo_repo_users.bulk_update_missing_fields(missing_fields)
        
        # Assertions
        assert mock_client.return_value.nsfw_db['users'].find.call_count == 1
        assert mock_client.return_value.nsfw_db['users'].update_one.call_count == 2
        assert result == 2
    
    def test_bulk_update_no_records_found(self, mongo_repo_users, mock_client):
        # Set up mock for find returning empty list
        mock_client.return_value.nsfw_db['users'].find.return_value = []
        
        # Call method
        missing_fields = {"is_deleted": False}
        result = mongo_repo_users.bulk_update_missing_fields(missing_fields)
        
        # Assertions
        assert result == 0
        mock_client.return_value.nsfw_db['users'].update_one.assert_not_called()
    
    def test_get_all_records(self, mongo_repo_users, mock_client):
        # Mock records
        records = [
            {"_id": "123", "username": "user1", "email": "user1@example.com"},
            {"_id": "456", "username": "user2", "email": "user2@example.com"}
        ]
        
        # Set up mock for find
        mock_client.return_value.nsfw_db['users'].find.return_value = records
        
        # Call method
        result = mongo_repo_users.get_all_records()
        
        # Assertions
        mock_client.return_value.nsfw_db['users'].find.assert_called_once_with({})
        assert result == records 