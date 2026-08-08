"""
Wireshark / Tshark Packet Capture and Protocol Analyzer Adapter implementation.
"""

import json
import shutil
import time
from typing import Dict, List, Any, Optional
from core.adapters.base import BaseToolAdapter
from core.adapters.models import ToolCapabilityMetadata, NormalizedToolEvidence, NormalizedFinding
from core.logger import get_logger

logger = get_logger("adapter_tshark")


class WiresharkTsharkAdapter(BaseToolAdapter):
    """Adapter integration for Wireshark CLI (tshark) packet analysis."""

    @property
    def name(self) -> str:
        return "tshark"

    @property
    def description(self) -> str:
        return "Tshark CLI network packet capture and protocol analysis tool."

    @property
    def category(self) -> str:
        return "packet_analysis"

    def is_installed(self) -> bool:
        return shutil.which("tshark") is not None

    def detect_version(self) -> str:
        if not self.is_installed():
            return "Not Installed"
        res = self.executor.execute(["tshark", "-v"], timeout_seconds=5.0)
        if res.is_success and res.stdout:
            lines = res.stdout.splitlines()
            return lines[0] if lines else "Unknown"
        return "Unknown"

    def health_check(self) -> bool:
        if not self.is_installed():
            return False
        res = self.executor.execute(["tshark", "-v"], timeout_seconds=5.0)
        return res.is_success

    def discover_capabilities(self) -> ToolCapabilityMetadata:
        return ToolCapabilityMetadata(
            supports_api=False,
            supports_async=True,
            supports_auth=True,
            categories=["packet_analysis", "traffic_inspection", "protocol_decoding"],
            supported_options={
                "capture_filter": "Wireshark capture filter string",
                "read_file": "Pcap file path to analyze (-r)",
                "packet_count": "Number of packets to capture (-c)",
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
                errors=["Tshark binary is not installed or available on system PATH."],
            )

        opts = options or {}
        read_file = opts.get("read_file")
        packet_count = str(opts.get("packet_count", 10))
        timeout = float(opts.get("timeout", 60.0))

        cmd = ["tshark", "-T", "json"]
        if read_file:
            cmd.extend(["-r", str(read_file)])
        else:
            cmd.extend(["-c", packet_count])

        res = self.executor.execute(cmd, timeout_seconds=timeout)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        findings = []
        parsed_json = []
        if res.stdout and res.stdout.strip():
            try:
                parsed_json = json.loads(res.stdout)
                if isinstance(parsed_json, list):
                    for idx, pkt in enumerate(parsed_json, 1):
                        layers = pkt.get("_source", {}).get("layers", {})
                        frame = layers.get("frame", {})
                        ip_layer = layers.get("ip", {})
                        findings.append(NormalizedFinding(
                            finding_id=f"tshark_frame_{idx}",
                            category="packet_frame",
                            title=f"Frame #{idx} ({ip_layer.get('ip.src', 'N/A')} -> {ip_layer.get('ip.dst', 'N/A')})",
                            severity="info",
                            details={
                                "protocols": frame.get("frame.protocols"),
                                "ip_src": ip_layer.get("ip.src"),
                                "ip_dst": ip_layer.get("ip.dst"),
                                "frame_len": frame.get("frame.len"),
                            },
                            evidence=str(layers)[:200]
                        ))
            except json.JSONDecodeError:
                pass

        status_code = 0 if res.is_success else (408 if res.timed_out else res.exit_code)
        errors = []
        if res.timed_out:
            errors.append(f"Tshark execution timed out after {timeout} seconds.")
        elif not res.is_success and res.stderr:
            errors.append(res.stderr.strip())

        return NormalizedToolEvidence(
            tool_name=self.name,
            tool_version=self.detect_version(),
            target=target,
            execution_time_ms=round(duration_ms, 2),
            success=res.is_success,
            status_code=status_code,
            raw_output=parsed_json or res.stdout,
            normalized_findings=findings,
            errors=errors,
        )
