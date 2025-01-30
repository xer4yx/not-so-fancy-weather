from typing import Dict, Any
from abc import ABC, abstractmethod


class ApiInterface(ABC):
    @abstractmethod
    def call(self, *args, **kwargs) -> Dict[str, Any]:
        """Calls the API returning JSON serializable data."""