from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict


class NSFWLogSettings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="LOG_",
        extra="ignore",
        env_file=".env", 
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    LEVEL: str = "INFO"
    QUEUE_SIZE: int = 100
    FILE_PATH: str = "logs/app_logs.json"
    FORMAT: str = "%(levelprefix)s     %(message)s" 