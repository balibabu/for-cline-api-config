# providers/base_provider.py
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    def __init__(self, api_key: str):
        # We instantiate the class with the API key passed from Cline
        self.api_key = api_key

    @abstractmethod
    def chat_completion(self, messages: list, model: str, **kwargs) -> dict:
        """Handles standard, full JSON responses."""
        pass

    @abstractmethod
    def stream_completion(self, messages: list, model: str, **kwargs):
        """Handles Server-Sent Events (SSE) streaming."""
        pass