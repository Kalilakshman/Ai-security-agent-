"""
Core domain interfaces and abstract contracts for the AI Security Orchestrator CLI.

Enforces Dependency Inversion Principle (DIP) and Interface Segregation Principle (ISP).
All core subsystems and external providers implement these base contracts.
"""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class PluginStatus(str, Enum):
    """Status enumeration for plugin health and state."""
    LOADED = "LOADED"
    UNLOADED = "UNLOADED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


@dataclass
class ExecutionResult:
    """Represents the output and metrics of a safely executed command.
    
    Attributes:
        command (List[str]): The executed command and its argument list.
        stdout (str): Standard output stream content.
        stderr (str): Standard error stream content.
        exit_code (int): Return code from process exit.
        execution_time_ms (float): Wall-clock execution time in milliseconds.
        timed_out (bool): True if the process exceeded its timeout limit.
        environment (Optional[Dict[str, str]]): Sanitized env vars passed during execution.
    """
    command: List[str]
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    timed_out: bool = False
    environment: Optional[Dict[str, str]] = None

    @property
    def is_success(self) -> bool:
        """Check if process completed with zero exit code without timing out."""
        return self.exit_code == 0 and not self.timed_out


class IExecutor(ABC):
    """Abstract contract for safe command execution engines."""

    @abstractmethod
    def execute(
        self,
        command: List[str],
        timeout_seconds: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute a command synchronously without shell=True.

        Args:
            command: Command and arguments list.
            timeout_seconds: Maximum allowed wall-clock execution time.
            cwd: Optional current working directory.
            env: Optional environment key-value pairs.

        Returns:
            ExecutionResult containing execution details and streams.
        """
        pass

    @abstractmethod
    async def execute_async(
        self,
        command: List[str],
        timeout_seconds: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute a command asynchronously without shell=True."""
        pass


class ILLMProvider(ABC):
    """Abstract strategy contract for LLM inference providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the friendly name of the LLM provider backend."""
        pass

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a completion prompt to the LLM backend.

        Args:
            prompt: User or contextual prompt text.
            system_prompt: Optional instruction system prompt.
            model: Model identifier override.
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.

        Returns:
            Completed text content string.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Perform API connectivity and authentication health check."""
        pass


class IPlugin(ABC):
    """Abstract lifecycle contract for Security Orchestrator Plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of the plugin."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief summary of plugin capability."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin resources with configuration payload."""
        pass

    @abstractmethod
    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute plugin capability against a target."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify plugin dependencies and runtime requirements."""
        pass
