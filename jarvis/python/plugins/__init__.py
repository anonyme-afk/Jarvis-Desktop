from .phone_plugin import PhonePlugin
from .browser_plugin import BrowserPlugin

# Liste de tous les plugins actifs
ALL_PLUGINS = [
    BrowserPlugin(),
    PhonePlugin(),
]

def find_plugin(message: str):
    """Trouve le premier plugin capable de gérer ce message"""
    for plugin in ALL_PLUGINS:
        if plugin.enabled and plugin.can_handle(message):
            return plugin
    return None
