"""
Metasploit Framework RPC Security Tool Adapter implementation.
"""

import os
import time
import shutil
import httpx
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding
from core.logger import get_logger

logger = get_logger("adapter_metasploit")


class MetasploitRPCAdapter(BaseToolAdapter):
    """Adapter integration for Metasploit Framework via MSF RPC API."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.api_url = (api_url or os.getenv("MSF_RPC_URL") or "http://127.0.0.1:55553").rstrip("/")
        self.api_key = api_key or os.getenv("MSF_RPC_KEY") or ""

    @property
    def name(self) -> str:
        return "metasploit"

    @property
    def description(self) -> str:
        return "Metasploit Framework vulnerability verification and exploit framework via RPC API."

    @property
    def category(self) -> str:
        return "exploit_verification"

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def is_installed(self) -> bool:
        if shutil.which("msfconsole") or shutil.which("msfrpcd"):
            return True
        return self.health_check()

    def detect_version(self) -> str:
        url = f"{self.api_url}/"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                if resp.status_code in (200, 401, 404, 405, 500):
                    return f"MSF RPC Daemon Online ({self.api_url})"
        except Exception:
            pass
        return "Installed (MSF Binary)" if self.is_installed() else "Not Installed"

    def health_check(self) -> bool:
        url = f"{self.api_url}/"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                if resp.status_code in (200, 401, 404, 405, 500):
                    return True
        except Exception:
            pass
        return self.is_installed()

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=True,
            supports_async=True,
            supports_auth=True,
            categories=["exploit_verification", "auxiliary_scan", "post_exploitation"],
            supported_options={
                "module": "Metasploit module path (e.g. 'auxiliary/scanner/http/title')",
                "api_url": "MSF RPC API endpoint",
            }
        )

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> NormalizedToolEvidence:
        start_time = time.perf_counter()
        opts = options or {}
        module_name = str(opts.get("module", "auxiliary/scanner/http/title"))
        timeout = float(opts.get("timeout", 180.0))

        if not self.health_check():
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version=self.detect_version(),
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                status_code=503,
                errors=[f"Metasploit MSF RPC daemon is not reachable at '{self.api_url}'."],
            )

        url = f"{self.api_url}/api/v1/modules/{module_name}/execute"
        payload = {"RHOSTS": target, "options": opts}

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=self._headers(), json=payload)
                duration_ms = (time.perf_counter() - start_time) * 1000.0

                if resp.status_code in (200, 201, 202):
                    data = resp.json()
                    findings = [
                        NormalizedFinding(
                            finding_id=f"msf_{module_name.replace('/', '_')}",
                            category="auxiliary_result",
                            title=f"Metasploit {module_name} executed against {target}",
                            severity="info",
                            details=data,
                            evidence=str(data)
                        )
                    ]
                    return NormalizedToolEvidence(
                        tool_name=self.name,
                        tool_version=self.detect_version(),
                        target=target,
                        execution_time_ms=round(duration_ms, 2),
                        success=True,
                        status_code=0,
                        raw_output=data,
                        normalized_findings=findings,
                    )
                else:
                    return NormalizedToolEvidence(
                        tool_name=self.name,
                        tool_version=self.detect_version(),
                        target=target,
                        execution_time_ms=round(duration_ms, 2),
                        success=False,
                        status_code=resp.status_code,
                        errors=[f"MSF RPC API returned status {resp.status_code}: {resp.text}"],
                    )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version=self.detect_version(),
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                status_code=500,
                errors=[f"Metasploit RPC execution error: {str(e)}"],
            )
