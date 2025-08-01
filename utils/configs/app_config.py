from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict


class NSFWSetting(BaseSettings):
    model_config = ConfigDict(
        env_prefix="APP_",
        extra="ignore",
        env_file=".env", 
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    NAME: str
    HOST: str
    PORT: int
    RELOAD: bool
    REDIRECT_URL: str