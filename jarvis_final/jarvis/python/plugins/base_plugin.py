from abc import ABC, abstractmethod
class BasePlugin(ABC):
    name = "plugin"
    enabled = True
    @abstractmethod
    def can_handle(self, message: str) -> bool: pass
    @abstractmethod
    def handle(self, message: str, context: dict) -> dict: pass
