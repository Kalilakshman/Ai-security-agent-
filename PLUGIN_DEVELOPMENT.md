# Tool Adapter & Plugin Extension Guide

The **AI Security Orchestrator CLI** supports two extensible integration mechanisms:
1. **Security Tool Adapters (`core/adapters/`)**: Recommended for structured tool integrations (REST API, RPC, subprocesses).
2. **BasePlugins (`plugins/`)**: Lightweight python script wrappers in `plugins/`.

---

## 🛠️ Option 1: Writing a `BaseToolAdapter` (`core/adapters/`)

Create a new file in `core/adapters/` (e.g. `core/adapters/mytool.py`):

```python
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding

class MyToolAdapter(BaseToolAdapter):
    @property
    def name(self) -> str:
        return "mytool"

    @property
    def description(self) -> str:
        return "Custom security assessment tool adapter."

    @property
    def category(self) -> str:
        return "vulnerability_assessment"

    def is_installed(self) -> bool:
        import shutil
        return shutil.which("mytool") is not None

    def detect_version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return self.is_installed()

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=False,
            supports_async=True,
            supports_auth=True,
            categories=["vulnerability_assessment"]
        )

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> NormalizedToolEvidence:
        # Run binary or call API
        return NormalizedToolEvidence(
            tool_name=self.name,
            tool_version=self.detect_version(),
            target=target,
            execution_time_ms=120.0,
            success=True,
            normalized_findings=[
                NormalizedFinding(
                    finding_id="mytool_1",
                    category="custom_finding",
                    title="Sample Observation",
                    severity="info",
                    details={"target": target}
                )
            ]
        )
```

Register your adapter in `core/adapters/registry.py` under `_register_default_adapters()`. The `AdapterPluginBridge` will automatically expose it to `PluginRegistry`, `AIPlanner`, and `WorkflowEngine` with **zero core workflow code modifications**!

---

## 🔌 Option 2: Writing a `BasePlugin` (`plugins/`)

Create a new Python file in `plugins/` (e.g., `plugins/myplugin.py`):

```python
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin

class CustomScannerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "custom_scanner"

    @property
    def description(self) -> str:
        return "Custom security scanner plugin."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        return ["custom_scanner", "--target", target]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        return [{"raw_stdout": stdout.strip()}]
```

`PluginManager` auto-discovers all files in `plugins/` upon startup!
