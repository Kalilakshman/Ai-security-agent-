"""
OWASP ZAP (Zed Attack Proxy) Security Tool Adapter implementation.
"""

import os
import time
import shutil
import httpx
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding
from core.logger import get_logger

logger = get_logger("adapter_zap")


class OWASPZAPAdapter(BaseToolAdapter):
    """Adapter integration for OWASP ZAP Web Application Security Scanner via REST API."""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.api_url = (api_url or os.getenv("ZAP_API_URL") or "http://localhost:8080").rstrip("/")
        self.api_key = api_key or os.getenv("ZAP_API_KEY") or ""

    @property
    def name(self) -> str:
        return "owasp_zap"

    @property
    def description(self) -> str:
        return "OWASP Zed Attack Proxy web vulnerability scanner via REST API."

    @property
    def category(self) -> str:
        return "web_assessment"

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.api_key:
            h["X-ZAP-API-Key"] = self.api_key
        return h

    def is_installed(self) -> bool:
        # Check binary presence or API daemon availability
        if shutil.which("zap-cli") or shutil.which("zap.sh") or shutil.which("zap.bat"):
            return True
        return self.health_check()

    def detect_version(self) -> str:
        url = f"{self.api_url}/JSON/core/view/version/"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                if resp.status_code == 200:
                    return resp.json().get("version", "ZAP API Connected")
        except Exception:
            pass
        return "ZAP Daemon Offline" if not self.is_installed() else "Installed (Daemon Offline)"

    def health_check(self) -> bool:
        url = f"{self.api_url}/JSON/core/view/version/"
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(url, headers=self._headers())
                return resp.status_code == 200
        except Exception:
            return False

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=True,
            supports_async=True,
            supports_auth=True,
            categories=["web_assessment", "vulnerability_scanning", "spidering"],
            supported_options={
                "api_url": "ZAP daemon API URL (default http://localhost:8080)",
                "api_key": "ZAP API key header",
                "scan_type": "spider or active_scan",
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
                errors=[f"OWASP ZAP REST API daemon is not reachable at '{self.api_url}'."],
            )

        target_url = target if target.startswith("http") else f"http://{target}"
        url = f"{self.api_url}/JSON/core/view/alerts/"
        params = {"baseurl": target_url}

        findings = []
        errors = []
        raw_resp = {}

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(url, headers=self._headers(), params=params)
                resp.raise_for_status()
                raw_resp = resp.json()
                alerts = raw_resp.get("alerts", [])

                for idx, alert in enumerate(alerts, 1):
                    risk = alert.get("risk", "Low").lower()
                    sev_map = {"informational": "info", "low": "low", "medium": "medium", "high": "high", "critical": "critical"}
                    severity = sev_map.get(risk, "medium")

                    findings.append(NormalizedFinding(
                        finding_id=f"zap_{alert.get('id', idx)}",
                        category="web_vulnerability",
                        title=alert.get("alert", "ZAP Alert"),
                        severity=severity,
                        details={
                            "url": alert.get("url"),
                            "param": alert.get("param"),
                            "cwe_id": alert.get("cweid"),
                            "wasc_id": alert.get("wascid"),
                            "description": alert.get("description"),
                            "solution": alert.get("solution"),
                        },
                        evidence=alert.get("evidence", "")
                    ))

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version=self.detect_version(),
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=True,
                status_code=0,
                raw_output=raw_resp,
                normalized_findings=findings,
                errors=errors,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"ZAP API execution error: {str(e)}")
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version=self.detect_version(),
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                status_code=500,
                errors=[f"OWASP ZAP API error: {str(e)}"],
            )
