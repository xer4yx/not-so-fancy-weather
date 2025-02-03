from core.services import UserService
from infrastructure.database import MongoRepository


def get_user_service() -> UserService:
    return UserService(MongoRepository('users'))