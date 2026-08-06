"""
Nuclei Vulnerability Scanner Plugin wrapper.
"""

import json
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin


class NucleiPlugin(BasePlugin):
    """Plugin wrapper for Nuclei Template-Based Vulnerability Scanner."""

    @property
    def name(self) -> str:
        return "nuclei"

    @property
    def description(self) -> str:
        return "Fast and customizable vulnerability scanner based on simple YAML templates."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        opts = options or {}
        severity = opts.get("severity", "medium,high,critical")
        return ["nuclei", "-u", target, "-severity", severity, "-jsonl", "-silent"]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        findings = []
        if not stdout.strip():
            return findings

        for line in stdout.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
                template_id = data.get("template-id")
                info = data.get("info", {})
                name = info.get("name")
                severity = info.get("severity")
                matched_at = data.get("matched-at")

                findings.append({
                    "template_id": template_id,
                    "name": name,
                    "severity": severity,
                    "matched_at": matched_at,
                    "type": data.get("type"),
                })
            except json.JSONDecodeError:
                findings.append({"raw": line_str})

        return findings
