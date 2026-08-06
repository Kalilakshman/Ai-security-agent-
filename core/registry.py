"""
Dynamic Plugin Registry system for discovery and registration.
"""

import os
import sys
import pkgutil
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Type, Optional
from plugins.base import BasePlugin
from core.logger import get_logger

logger = get_logger("registry")


class PluginRegistry:
    """Central registry providing automatic discovery and management of tool plugins."""

    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path(__file__).parent.parent / "plugins"
        self._plugins: Dict[str, BasePlugin] = {}
        self.auto_discover()

    def auto_discover(self) -> None:
        """Scan plugins directory and dynamically import/register all BasePlugin implementations."""
        if not self.plugins_dir.exists() or not self.plugins_dir.is_dir():
            logger.warning(f"Plugins directory '{self.plugins_dir}' does not exist.")
            return

        # Ensure parent directory of plugins is in sys.path
        parent_dir = str(self.plugins_dir.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Iterate over all .py files in plugins directory
        for file in self.plugins_dir.glob("*.py"):
            if file.name.startswith("_") or file.name in ("base.py", "manager.py"):
                continue

            module_name = f"plugins.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                # Re-import to pick up changes if needed
                importlib.reload(module)

                # Search module attributes for BasePlugin subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, BasePlugin)
                        and attr is not BasePlugin
                    ):
                        try:
                            instance = attr()
                            self.register(instance)
                        except Exception as e:
                            logger.error(f"Failed to instantiate plugin class '{attr_name}' in {module_name}: {str(e)}")

            except Exception as e:
                logger.error(f"Failed to load plugin module '{module_name}': {str(e)}")

    def register(self, plugin: BasePlugin) -> None:
        """Register a BasePlugin instance into the central registry."""
        self._plugins[plugin.name] = plugin
        logger.debug(f"Registered plugin: '{plugin.name}' ({'Installed' if plugin.is_installed() else 'Not Installed'})")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Retrieve registered plugin instance by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> Dict[str, BasePlugin]:
        """Return all registered plugin instances."""
        return self._plugins.copy()


# Global singleton registry instance
_default_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get global PluginRegistry singleton instance."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry
