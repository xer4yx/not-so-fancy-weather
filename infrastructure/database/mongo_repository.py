from typing import Dict, Any
from pymongo import MongoClient
from bson import ObjectId
from pymongo.errors import WriteError, OperationFailure, ConnectionFailure

from core.entities import User
from core.interface import DatabaseRepository
from utils.configs import NSFWDbSettings

class MongoRepository(DatabaseRepository):
    def __init__(self, collection_name: str):
        db_settings = NSFWDbSettings()
        self.__uri = db_settings.MONGO_DSN
        self.__client = MongoClient(self.__uri)
        try:
            self.__client.admin.command('ping')
        except ConnectionFailure as e:
            raise ConnectionFailure(f'Could not connect to MongoDB: {e}')
        except Exception as e:
            raise Exception(f'Could not connect to MongoDB: {e}')
        self.__db = self.__client.nsfw_db
        self.__collections = self.__db[collection_name]
    
    def create(self, data: Dict[str, Any]) -> str:
        result = self.__collections.insert_one(data)
        
        result.inserted_id
        
        return result.__str__()
        
    def read(self, key: str, value: str) -> Dict[str, Any]:
        user_data =self.__collections.find_one({key: value})
        return User.model_validate(user_data).model_dump()
    
    def update(self, key: str, value: str, data: Dict[str, Any]) -> str:
        if key == '_id':
            value = ObjectId(value)
        
        result = self.__collections.find_one_and_update({key: value}, {'$set': data})
        
        if result.modified_count == 0 and result.matched_count == 0:
            raise OperationFailure('Could not find record to update')
        
        return result.modified_count.__str__()
    
    def delete(self, key: str, value: str) -> bool:
        result = self.__collections.delete_many({key: value})
        
        if result.deleted_count == 0:
            return False
        
        return True