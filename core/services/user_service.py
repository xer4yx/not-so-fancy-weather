from typing import Dict, Any

from core.entities import User
from core.interface import DatabaseRepository

class UserService:
    def __init__(self, repository: DatabaseRepository):
        self.__repository = repository
    
    def create_user(self, username: str, email: str, password: str) -> str:
        return self.__repository.create(
            data=User(
                username=username, 
                email=email, 
                password=password).model_dump())
    
    def read_user(self, key: str, value: str) -> Dict[str, Any]:
        return self.__repository.read(key=key, value=value)
        
    
    def update_user(self, key: str, id: str, data: Dict[str, Any]) -> str: 
        return self.__repository.update(key=key, value=id, data=data)
    
    def delete_user(self, key: str, id: str) -> bool:
        return self.__repository.delete(key=key, value=id)
    