"""
Extensible Security-Tool Adapter Subsystem Package.
"""

from core.adapters.models import (
    ToolCapabilityMetadata,
    NormalizedFinding,
    NormalizedToolEvidence,
)
from core.adapters.base import BaseToolAdapter
from core.adapters.nmap import NmapAdapter
from core.adapters.zap import OWASPZAPAdapter
from core.adapters.burp import BurpSuiteAdapter
from core.adapters.tshark import WiresharkTsharkAdapter
from core.adapters.metasploit import MetasploitRPCAdapter
from core.adapters.registry import (
    ToolAdapterRegistry,
    AdapterPluginBridge,
    get_adapter_registry,
)

__all__ = [
    "ToolCapabilityMetadata",
    "NormalizedFinding",
    "NormalizedToolEvidence",
    "BaseToolAdapter",
    "NmapAdapter",
    "OWASPZAPAdapter",
    "BurpSuiteAdapter",
    "WiresharkTsharkAdapter",
    "MetasploitRPCAdapter",
    "ToolAdapterRegistry",
    "AdapterPluginBridge",
    "get_adapter_registry",
]
