"""
Nmap Network Scanner Adapter implementation.
"""

import re
import shutil
import time
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding
from core.logger import get_logger

logger = get_logger("adapter_nmap")


class NmapAdapter(BaseToolAdapter):
    """Adapter integration for Nmap Network Mapper."""

    @property
    def name(self) -> str:
        return "nmap"

    @property
    def description(self) -> str:
        return "Network discovery, port scanning, and service version detection tool."

    @property
    def category(self) -> str:
        return "network_recon"

    def is_installed(self) -> bool:
        return shutil.which("nmap") is not None

    def detect_version(self) -> str:
        if not self.is_installed():
            return "Not Installed"
        res = self.executor.execute(["nmap", "--version"], timeout_seconds=5.0)
        if res.is_success and res.stdout:
            match = re.search(r"Nmap version ([0-9\.]+)", res.stdout)
            if match:
                return match.group(1)
            return res.stdout.splitlines()[0]
        return "Unknown"

    def health_check(self) -> bool:
        if not self.is_installed():
            return False
        res = self.executor.execute(["nmap", "-V"], timeout_seconds=5.0)
        return res.is_success

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=False,
            supports_async=True,
            supports_auth=True,
            categories=["network_recon", "port_scanning", "service_detection"],
            supported_options={
                "ports": "Port range or list (e.g. '80,443' or '1-1000')",
                "scan_type": "Nmap scan type flag (e.g. '-sV', '-sS', '-sU')",
                "speed": "Timing template (e.g. '-T4')",
            }
        )

    def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> NormalizedToolEvidence:
        start_time = time.perf_counter()
        if not self.is_installed():
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return NormalizedToolEvidence(
                tool_name=self.name,
                tool_version="Not Installed",
                target=target,
                execution_time_ms=round(duration_ms, 2),
                success=False,
                status_code=127,
                errors=["Nmap binary is not installed or available on system PATH."],
            )

        opts = options or {}
        ports = str(opts.get("ports", "80,443"))
        scan_type = str(opts.get("scan_type", "-sV"))
        timeout = float(opts.get("timeout", 600.0))

        cmd = ["nmap", "-p", ports, scan_type, target]
        res = self.executor.execute(cmd, timeout_seconds=timeout)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        findings = []
        port_pattern = re.compile(r"^(\d+/(?:tcp|udp))\s+(\w+)\s+(\S+)(?:\s+(.*))?$", re.MULTILINE)

        for match in port_pattern.finditer(res.stdout):
            port_proto = match.group(1)
            state = match.group(2)
            service = match.group(3)
            version = (match.group(4) or "").strip()

            findings.append(NormalizedFinding(
                finding_id=f"nmap_{target}_{port_proto}",
                category="open_port",
                title=f"Port {port_proto} ({service}) {state.upper()}",
                severity="info" if state == "open" else "low",
                details={
                    "port_proto": port_proto,
                    "state": state,
                    "service": service,
                    "version": version
                },
                evidence=match.group(0)
            ))

        status_code = 0 if res.is_success else (408 if res.timed_out else res.exit_code)
        errors = []
        if res.timed_out:
            errors.append(f"Nmap scan timed out after {timeout} seconds.")
        elif not res.is_success and res.stderr:
            errors.append(res.stderr.strip())

        return NormalizedToolEvidence(
            tool_name=self.name,
            tool_version=self.detect_version(),
            target=target,
            execution_time_ms=round(duration_ms, 2),
            success=res.is_success,
            status_code=status_code,
            raw_output=res.stdout,
            normalized_findings=findings,
            errors=errors,
            metadata={"command": cmd, "timed_out": res.timed_out}
        )
