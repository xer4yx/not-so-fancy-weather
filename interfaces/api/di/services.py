from core.services import UserService, AuthService, MigrationService, WeatherService, PreferencesService
from infrastructure.database import MongoRepository
from infrastructure.auth import AuthFactory


def get_user_service() -> UserService:
    return UserService(
        repository=MongoRepository('users'), 
        crypt_algo=AuthFactory.create_hash('bcrypt'))

def get_auth_service() -> AuthService:
    return AuthService(
        auth=AuthFactory.create_auth(),
        hash=AuthFactory.create_hash('bcrypt')
    )

def get_migration_service() -> MigrationService:
    return MigrationService(
        repository=MongoRepository('users')
    )

def get_weather_service() -> WeatherService:
    return WeatherService(
        repository=MongoRepository('weather_data')
    )

def get_preferences_service() -> PreferencesService:
    return PreferencesService(
        repository=MongoRepository('preferences')
    )