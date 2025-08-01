from pydantic_settings import BaseSettings
from pydantic.config import ConfigDict


class MailgunSettings(BaseSettings):
    model_config = ConfigDict(
        env_prefix="MAILGUN_",
        extra="ignore",
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8"
    )
    URL: str
    API_KEY: str
