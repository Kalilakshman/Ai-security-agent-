"""
WhatWeb Web Technology Identifier Plugin wrapper.
"""

import json
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin


class WhatWebPlugin(BasePlugin):
    """Plugin wrapper for WhatWeb Web Scanner."""

    @property
    def name(self) -> str:
        return "whatweb"

    @property
    def description(self) -> str:
        return "Next generation web scanner identifying web technologies and CMS systems."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        opts = options or {}
        aggression = str(opts.get("aggression", 1))
        return ["whatweb", f"-a{aggression}", "--log-json=-", target]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        findings = []
        if not stdout.strip():
            return findings

        try:
            # Attempt parsing JSON stream output
            data = json.loads(stdout)
            if isinstance(data, list):
                for item in data:
                    target_url = item.get("target")
                    http_status = item.get("http_status")
                    plugins_detected = item.get("plugins", {})
                    findings.append({
                        "target_url": target_url,
                        "http_status": http_status,
                        "technologies": list(plugins_detected.keys()),
                        "details": plugins_detected
                    })
            elif isinstance(data, dict):
                findings.append(data)
        except json.JSONDecodeError:
            # Fallback text parsing
            for line in stdout.splitlines():
                if line.strip() and "[" in line and "]" in line:
                    findings.append({"raw": line.strip()})

        return findings
