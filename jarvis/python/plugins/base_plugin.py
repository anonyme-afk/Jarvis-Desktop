"""
Classe de base pour tous les plugins JARVIS.
Pour créer un plugin : hériter de BasePlugin et implémenter les méthodes.
"""
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    name = "plugin"
    description = "Description du plugin"
    enabled = True

    @abstractmethod
    def can_handle(self, message: str) -> bool:
        """Retourne True si ce plugin peut gérer ce message"""
        pass

    @abstractmethod
    def handle(self, message: str, context: dict) -> dict:
        """
        Traite le message.
        Retourne {"reply": str, "action": dict|None}
        """
        pass
