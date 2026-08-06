"""
Plugin discovery and registry manager.
"""

import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Type, Optional
from core.interfaces import IPlugin, PluginStatus
from core.logger import get_logger

logger = get_logger("plugin_manager")


class PluginManager:
    """Manages discovery, loading, and lifecycle of Security Orchestrator Plugins."""

    def __init__(self, plugins_directory: str = "plugins"):
        self.plugins_dir = Path(plugins_directory)
        self._registry: Dict[str, IPlugin] = {}
        self._status: Dict[str, PluginStatus] = {}

    def discover_plugins() -> List[str]:
        """Scan plugins directory for potential Python plugin modules."""
        if not self.plugins_dir.exists() or not self.plugins_dir.is_dir():
            logger.debug(f"Plugins directory '{self.plugins_dir}' does not exist.")
            return []

        found_modules = []
        for path in self.plugins_dir.glob("*.py"):
            if path.name.startswith("_") or path.name in ("base.py", "manager.py"):
                continue
            found_modules.append(path.stem)
        return found_modules

    def register_plugin(self, plugin: IPlugin) -> bool:
        """Manually register a plugin instance."""
        name = plugin.name
        try:
            health = plugin.health_check()
            if health:
                self._registry[name] = plugin
                self._status[name] = PluginStatus.LOADED
                logger.info(f"Registered plugin: {name} v{plugin.version}")
                return True
            else:
                self._status[name] = PluginStatus.ERROR
                logger.warning(f"Plugin '{name}' failed health check during registration.")
                return False
        except Exception as e:
            self._status[name] = PluginStatus.ERROR
            logger.exception(f"Error registering plugin '{name}': {str(e)}")
            return False

    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Retrieve a loaded plugin instance by name."""
        return self._registry.get(name)

    def list_plugins() -> Dict[str, Dict[str, str]]:
        """Return metadata for all registered plugins."""
        info = {}
        for name, plugin in self._registry.items():
            info[name] = {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "status": self._status.get(name, PluginStatus.UNLOADED).value
            }
        return info
