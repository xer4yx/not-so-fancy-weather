from typing import Any
from pydantic import BaseModel


class APIResponse(BaseModel):
    data: Any