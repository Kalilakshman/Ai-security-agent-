"""
Abstract Base Class for Extensible Security-Tool Adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence
from core.executor import SafeExecutor
from core.logger import get_logger

logger = get_logger("tool_adapter_base")


class BaseToolAdapter(ABC):
    """Abstract contract required for all Security-Tool Adapters.
    
    Every integration MUST support:
    - installation detection
    - version detection
    - health check
    - capability discovery
    - configuration validation
    - structured output
    - timeout
    - error handling
    - normalized evidence
    """

    def __init__(self, executor: Optional[SafeExecutor] = None):
        self.executor = executor or SafeExecutor()

    @property
    @abstractmethod
    def name(self) -> str:
        """Friendly identifier name of the tool adapter."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief summary of tool capability."""
        pass

    @property
    def category(self) -> str:
        """Category domain of the security tool."""
        return "security_assessment"

    @abstractmethod
    def is_installed(self) -> bool:
        """Detect if the binary or API service is installed and available."""
        pass

    @abstractmethod
    def detect_version(self) -> str:
        """Detect installed version string of the tool or API."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Perform real-time operational health check against tool or service."""
        pass

    @abstractmethod
    def discover_capabilities(self) -> ToolCapabilityMetadata:
        """Discover capabilities and supported options of the tool adapter."""
        pass

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input configuration options against tool constraints."""
        errors = []
        caps = self.discover_capabilities()
        for k in config.keys():
            if caps.supported_options and k not in caps.supported_options and k not in ("timeout", "profile", "authorized"):
                logger.debug(f"Unrecognized option '{k}' passed to adapter '{self.name}'")
        return (len(errors) == 0, errors)

    @abstractmethod
    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> NormalizedToolEvidence:
        """Execute tool capability against target and return NormalizedToolEvidence."""
        pass
