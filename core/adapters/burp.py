"""
Burp Suite Security Tool Adapter implementation.
"""

import os
import time
import httpx
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding
from core.logger import get_logger

logger = get_logger("adapter_burp")


class BurpSuiteAdapter(BaseToolAdapter):
    """Adapter integration for Burp Suite Enterprise / REST API Extension."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.api_url = (api_url or os.getenv("BURP_API_URL") or "http://localhost:1337").rstrip("/")
        self.api_key = api_key or os.getenv("BURP_API_KEY") or ""

    @property
    def name(self) -> str:
        return "burp_suite"

    @property
    def description(self) -> str:
        return "Burp Suite vulnerability scanner via REST API extension."

    @property
    def category(self) -> str:
        return "web_assessment"

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def is_installed(self) -> bool:
        return self.health_check()

    def detect_version(self) -> str:
        url = f"{self.api_url}/v1/version"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json().get("version", "Burp REST API Connected")
        except Exception:
            pass
        return "Burp API Offline"

    def health_check(self) -> bool:
        url = f"{self.api_url}/v1/version"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                return resp.status_code in (200, 401)
        except Exception:
            return False

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=True,
            supports_async=True,
            supports_auth=True,
            categories=["web_assessment", "vulnerability_scanning"],
            supported_options={
                "api_url": "Burp REST API endpoint",
                "api_key": "Burp REST API token",
            }
        )

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> NormalizedToolEvidence:
        start_time = time.perf_counter()
        opts = options or {}
        timeout = float(opts.get("timeout", 300.0))

        if not self.health_check():
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version=self.detect_version(),
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                status_code=503,
                errors=[f"Burp Suite REST API endpoint is not reachable at '{self.api_url}'."],
            )

        target_url = target if target.startswith("http") else f"http://{target}"
        url = f"{self.api_url}/v1/scan/{target_url}"

        findings = []
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json()
                    issues = data.get("issue_events", [])
                    for idx, issue in enumerate(issues, 1):
                        sev = issue.get("severity", "medium").lower()
                        findings.append(NormalizedFinding(
                            finding_id=f"burp_{idx}",
                            category="web_vulnerability",
                            title=issue.get("type_name", "Burp Issue"),
                            severity=sev,
                            details=issue,
                            evidence=issue.get("path", "")
                        ))
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
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
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    return NormalizedToolEvidence(
                        tool_name=self.name,
                        tool_version=self.detect_version(),
                        target=target,
                        execution_time_ms=round(duration_ms, 2),
                        success=False,
                        status_code=resp.status_code,
                        errors=[f"Burp API returned status {resp.status_code}: {resp.text}"],
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
                errors=[f"Burp API execution error: {str(e)}"],
            )
