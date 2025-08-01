import certifi
from bson import ObjectId
import urllib.parse as urlparser
from pymongo import MongoClient
from pymongo.errors import WriteError, OperationFailure, ConnectionFailure
from typing import Dict, Any, List

from core.entities import User, Preferences
from core.interface import DatabaseRepository
from infrastructure.logger import get_logger
from utils.configs import NSFWDbSettings

class MongoRepository(DatabaseRepository):
    def __init__(self, collection_name: str):
        db_settings = NSFWDbSettings()
        self.__username = urlparser.quote_plus(db_settings.MONGO_USERNAME)
        self.__password = urlparser.quote_plus(db_settings.MONGO_PASSWORD)
        self.__uri = db_settings.MONGO_DSN
        self.logger = get_logger("infrastructure.database.mongo", "logs/infrastructure.log")
        
        # Use certifi CA certificates for SSL connection
        ca = certifi.where()
        
        try:
            self.__client = MongoClient(
                self.__uri % (self.__username, self.__password),
                tls=True,
                tlsCAFile=ca,  # Add this line to specify the CA file
                retryWrites=True,
                w="majority",
                connectTimeoutMS=30000,
                socketTimeoutMS=45000,
                serverSelectionTimeoutMS=50000
            )
            
            # Test connection
            self.__client.admin.command('ping')
            
            self.__db = self.__client.nsfw_db
            self.__collections = self.__db[collection_name]
            
        except ConnectionFailure as e:
            self.logger.error(
                f"Could not connect to MongoDB: {e}",
                extra={
                    "error_type": "ConnectionFailure"
                }
            )
            raise ConnectionFailure(f'Could not connect to MongoDB: {e}')
        except Exception as e:
            self.logger.error(
                f"Could not connect to MongoDB: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not connect to MongoDB: {e}')
    
    def create(self, data: Dict[str, Any]) -> str:
        try:
            result = self.__collections.insert_one(data)
            
            if not result.inserted_id:
                self.logger.error(
                    "Failed to create record",
                    extra={
                        "error_type": "WriteError"
                    }
                )
                raise WriteError("Failed to create record")
            
            self.logger.info(
                "Record created successfully",
                extra={
                    "database": self.__db.name,
                    "collection": self.__collections.name,
                    "inserted_id": result.inserted_id
                }
            )
            return str(result.inserted_id)
        except OperationFailure as e:
            self.logger.error(
                f"Operation failed: {e}",
                extra={
                    "error_type": "OperationFailure"
                }
            )
            raise OperationFailure(f'Could not create record: {e}')
        except Exception as e:
            self.logger.error(
                f"Error occurred when trying to create record: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not create record: {e}')
        
    def read(self, key: str, value: str) -> Dict[str, Any]:
        try:
            doc = self.__collections.find_one({key: value})
            if not doc:
                self.logger.warning(
                    "No record found",
                    extra={
                        "error_type": "Warning"
                    }
                )
                return None
            
            # Determine which entity to use based on collection name
            if self.__collections.name == 'users':
                return User.model_validate(doc).model_dump()
            elif self.__collections.name == 'preferences':
                return Preferences.model_validate(doc).model_dump()
            else:
                # For other collections, just return the document
                return doc
        except OperationFailure as e:
            self.logger.error(
                f"Operation failed: {e}",
                extra={
                    "error_type": "OperationFailure"
                }
            )
            raise OperationFailure(f'Could not read record: {e}')
        except Exception as e:
            self.logger.error(
                f"Error occurred when trying to read record: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not read record: {e}')
        
    def update(self, key: str, value: str, data: Dict[str, Any]) -> str:
        try:
            if key == '_id':
                value = ObjectId(value)
            
            # find_one_and_update returns the document before update, not a result object
            result = self.__collections.find_one_and_update({key: value}, {'$set': data})
            
            if result is None:
                self.logger.error(
                    "Could not find record to update",
                    extra={
                        "error_type": "OperationFailure"
                    }
                )
                raise OperationFailure('Could not find record to update')
            
            self.logger.info(
                "Record updated successfully",
                extra={
                    "database": self.__db.name,
                    "collection": self.__collections.name,
                    "document_id": str(result.get("_id", "unknown"))
                }
            )
            return "1"  # Indicating one document was updated
        except OperationFailure as e:
            self.logger.error(
                f"Operation failed: {e}",
                extra={
                    "error_type": "OperationFailure"
                }
            )
            raise OperationFailure(f'Could not update record: {e}')
        except Exception as e:
            self.logger.error(
                f"Error occurred when trying to update record: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not update record: {e}')
        
    def delete(self, key: str, value: str) -> bool:
        try:
            result = self.__collections.delete_many({key: value})
            
            if result.deleted_count == 0:
                self.logger.warning(
                    "No record found to delete",
                    extra={
                        "error_type": "Warning"
                    }
                )
                return False
            
            self.logger.info(
                "Record deleted successfully",
                extra={
                    "database": self.__db.name,
                    "collection": self.__collections.name,
                    "deleted_count": result.deleted_count
                }
            )
            return True
        except OperationFailure as e:
            self.logger.error(
                f"Operation failed: {e}",
                extra={
                    "error_type": "OperationFailure"
                }
            )
            raise OperationFailure(f'Could not delete record: {e}')
        except Exception as e:
            self.logger.error(
                f"Error occurred when trying to delete record: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not delete record: {e}')

    def bulk_update_missing_fields(self, missing_fields: Dict[str, Any]) -> int:
        """
        Update multiple records to ensure they have certain fields.
        
        Args:
            missing_fields: A dictionary of field names and their default values
                           to add to records that don't have these fields
                           
        Returns:
            The number of records updated
        """
        try:
            # Create a query that finds all documents missing any of the specified fields
            or_conditions = [
                {field: {"$exists": False}} for field in missing_fields.keys()
            ]
            
            if not or_conditions:
                return 0
                
            query = {"$or": or_conditions}
            
            # Find all documents needing updates
            docs_to_update = list(self.__collections.find(query))
            
            if not docs_to_update:
                self.logger.info("No records need schema migration")
                return 0
                
            self.logger.info(f"Found {len(docs_to_update)} records that need schema migration")
            
            # Update each document with missing fields
            updated_count = 0
            for doc in docs_to_update:
                update_data = {}
                
                # Only add fields that are missing
                for field, default_value in missing_fields.items():
                    if field not in doc:
                        update_data[field] = default_value
                
                if update_data:
                    result = self.__collections.update_one(
                        {"_id": doc["_id"]},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
            
            self.logger.info(f"Successfully updated {updated_count} records")
            return updated_count
        except Exception as e:
            self.logger.error(
                f"Error during bulk update: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not perform bulk update: {e}')
            
    def get_all_records(self) -> List[Dict[str, Any]]:
        """
        Get all records from the collection.
        
        Returns:
            A list of all records
        """
        try:
            return list(self.__collections.find({}))
        except Exception as e:
            self.logger.error(
                f"Error retrieving all records: {e}",
                extra={
                    "error_type": "Exception"
                }
            )
            raise Exception(f'Could not retrieve all records: {e}')
