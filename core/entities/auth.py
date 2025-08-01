from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    username: str
    password: Optional[str] = ""
