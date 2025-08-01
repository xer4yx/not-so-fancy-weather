from pydantic_settings import BaseSettings, SettingsConfigDict


class NSFWApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    OPENWEATHER_API_KEY: str
    SECRET_KEY: str