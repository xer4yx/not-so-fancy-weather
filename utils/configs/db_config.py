from pydantic_settings import BaseSettings
from pydantic import MongoDsn, ConfigDict


class NSFWDbSettings(BaseSettings):
    model_config = ConfigDict(
        env_file="db.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    MONGO_DSN: MongoDsn