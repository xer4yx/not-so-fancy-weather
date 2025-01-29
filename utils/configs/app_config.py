from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict


class NSFWSetting(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",
        env_file="app.env", 
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    APP_NAME: str
    HOST: str
    PORT: int
    RELOAD: bool