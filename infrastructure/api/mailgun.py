import requests
from typing import Dict, Any

from core.entities.mail import Mail
from core.interface.api import ApiInterface
from utils.configs.mail_config import MailgunSettings


class MailgunApi(ApiInterface):
    def __init__(self, settings: MailgunSettings):
        self.settings = settings
        self.base_url = settings.URL
        self.api_key = settings.API_KEY
        
    def call(self, mail: Mail) -> Dict[str, Any]:
        response = requests.post(
            self.base_url,
            auth=("api", self.api_key),
            data=mail.model_dump()
        )

        if response.status_code != 200:
            raise Exception(f"Failed to send email: {response.status_code} {response.text}")
        
        return response.json()


