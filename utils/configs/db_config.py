from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class NSFWDbSettings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    MONGO_DSN: str
    MONGO_USERNAME: str
    MONGO_PASSWORD: str