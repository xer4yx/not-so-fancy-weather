from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: str
    username: str
    email: str
    password: Optional[str]