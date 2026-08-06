"""
Plugin package initialization.
"""

from plugins.base import SecurityPlugin
from plugins.manager import PluginManager

__all__ = ["SecurityPlugin", "PluginManager"]
