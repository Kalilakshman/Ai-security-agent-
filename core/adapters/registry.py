"""
Central Tool Adapter Registry and automatic PluginRegistry bridge.
"""

from typing import Dict, List, Optional, Type, Any
from core.adapters.base import BaseToolAdapter
from core.adapters.nmap import NmapAdapter
from core.adapters.zap import OWASPZAPAdapter
from core.adapters.burp import BurpSuiteAdapter
from core.adapters.tshark import WiresharkTsharkAdapter
from core.adapters.metasploit import MetasploitRPCAdapter
from plugins.base import BasePlugin, StandardPluginOutput
from core.logger import get_logger

logger = get_logger("tool_adapter_registry")


class AdapterPluginBridge(BasePlugin):
    """Bridge adapter allowing any BaseToolAdapter to act as a native BasePlugin."""

    def __init__(self, adapter: BaseToolAdapter):
        super().__init__()
        self.adapter = adapter

    @property
    def name(self) -> str:
        return self.adapter.name

    @property
    def description(self) -> str:
        return self.adapter.description

    def is_installed(self) -> bool:
        return self.adapter.is_installed()

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        return ["tool-adapter-exec", self.name, target]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        return []

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> StandardPluginOutput:
        evidence = self.adapter.execute(target, options)
        status = "COMPLETED" if evidence.success else ("TIMED_OUT" if evidence.status_code == 408 else "FAILED")
        if not self.adapter.is_installed():
            status = "NOT_INSTALLED"

        findings = [f.model_dump() for f in evidence.normalized_findings]

        return StandardPluginOutput(
            tool=self.name,
            target=target,
            status=status,
            findings=findings,
            errors=evidence.errors,
            metadata={
                "tool_version": evidence.tool_version,
                "execution_time_ms": evidence.execution_time_ms,
                "status_code": evidence.status_code,
                "raw_output": evidence.raw_output,
            }
        )


class ToolAdapterRegistry:
    """Registry managing security tool adapters and synchronizing with PluginRegistry."""

    def __init__(self):
        self._adapters: Dict[str, BaseToolAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self):
        default_classes = [
            NmapAdapter,
            OWASPZAPAdapter,
            BurpSuiteAdapter,
            WiresharkTsharkAdapter,
            MetasploitRPCAdapter,
        ]
        for adapter_cls in default_classes:
            try:
                instance = adapter_cls()
                self.register(instance)
            except Exception as e:
                logger.error(f"Failed to instantiate default adapter '{adapter_cls.__name__}': {str(e)}")

    def register(self, adapter: BaseToolAdapter) -> None:
        """Register a tool adapter and bridge it into the central PluginRegistry."""
        name = adapter.name
        self._adapters[name] = adapter
        logger.debug(f"Registered Tool Adapter: '{name}' (Category: {adapter.category})")

        # Automatically bridge into core PluginRegistry for zero workflow changes
        try:
            from core.registry import get_registry
            plugin_registry = get_registry()
            bridge = AdapterPluginBridge(adapter)
            plugin_registry.register(bridge)
        except Exception as e:
            logger.debug(f"Failed to bridge adapter '{name}' to PluginRegistry: {str(e)}")

    def get_adapter(self, name: str) -> Optional[BaseToolAdapter]:
        """Retrieve registered tool adapter by name."""
        return self._adapters.get(name)

    def list_adapters(self) -> Dict[str, BaseToolAdapter]:
        """Return dict of all registered tool adapters."""
        return self._adapters.copy()


# Global Singleton Instance
_adapter_registry: Optional[ToolAdapterRegistry] = None


def get_adapter_registry() -> ToolAdapterRegistry:
    """Retrieve global ToolAdapterRegistry singleton instance."""
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = ToolAdapterRegistry()
    return _adapter_registry
