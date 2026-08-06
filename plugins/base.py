"""
Standardized Base Plugin contract and standard JSON output schema for security tool wrappers.
"""

import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from core.interfaces import ExecutionResult
from core.executor import SafeExecutor
from core.logger import get_logger

logger = get_logger("plugin_base")


class StandardPluginOutput(BaseModel):
    """Standard JSON output schema required for all plugin execution results.

    Schema:
    {
      "tool": "nmap",
      "target": "127.0.0.1",
      "status": "COMPLETED",
      "timestamp": "2026-08-06T10:57:49Z",
      "findings": [...],
      "errors": [...],
      "metadata": {}
    }
    """
    tool: str = Field(..., description="Tool name identifier.")
    target: str = Field(..., description="Target host, URL, or domain.")
    status: str = Field(..., description="Execution status: COMPLETED, FAILED, TIMED_OUT, NOT_INSTALLED.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp."
    )
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed structured findings.")
    errors: List[str] = Field(default_factory=list, description="Execution error messages or stderr lines.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metrics and metadata.")


class BasePlugin(ABC):
    """Abstract Base Class for all security tool plugins.

    Every concrete plugin MUST implement:
    - name()
    - description()
    - is_installed()
    - build_command()
    - execute()
    - parse()
    """

    def __init__(self, executor: Optional[SafeExecutor] = None):
        self.executor = executor or SafeExecutor()

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin / tool identifier name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short summary of tool capability."""
        pass

    def is_installed(self) -> bool:
        """Check if binary executable is installed on host system PATH."""
        return shutil.which(self.name) is not None

    @abstractmethod
    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        """Construct safe command and argument vector without shell injection risks."""
        pass

    @abstractmethod
    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse raw command output streams into structured finding dictionaries."""
        pass

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> StandardPluginOutput:
        """Execute plugin using shared SafeExecutor and return Standard JSON schema."""
        if not self.is_installed():
            return StandardPluginOutput(
                tool=self.name,
                target=target,
                status="NOT_INSTALLED",
                errors=[f"Binary for tool '{self.name}' is not installed or available on system PATH."],
                metadata={"installed": False}
            )

        command = self.build_command(target, options)
        timeout = options.get("timeout", 120.0) if options else 120.0

        logger.info(f"Executing plugin '{self.name}' against target '{target}'")
        res: ExecutionResult = self.executor.execute(command, timeout_seconds=timeout)

        status = "COMPLETED"
        errors = []

        if res.timed_out:
            status = "TIMED_OUT"
            errors.append(f"Execution timed out after {timeout} seconds.")
        elif not res.is_success:
            status = "FAILED"
            if res.stderr:
                errors.append(res.stderr.strip())
            else:
                errors.append(f"Process exited with non-zero code {res.exit_code}.")

        findings = self.parse(res.stdout, res.stderr)

        return StandardPluginOutput(
            tool=self.name,
            target=target,
            status=status,
            findings=findings,
            errors=errors,
            metadata={
                "command": command,
                "exit_code": res.exit_code,
                "execution_time_ms": res.execution_time_ms,
                "timed_out": res.timed_out,
            }
        )
