from typing import AsyncGenerator, Callable

from core.interface import DatabaseRepository
from infrastructure.database.mongo_repository import MongoRepository


def get_mongodb_repository(collection_name: str) -> Callable[[], AsyncGenerator[DatabaseRepository, None]]:
    async def _get_repository() -> AsyncGenerator[DatabaseRepository, None]:
        mongo_repository = MongoRepository(collection_name)
        try:
            yield mongo_repository
        finally:
            pass
    return _get_repository
