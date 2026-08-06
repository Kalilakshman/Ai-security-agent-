"""
Nikto Web Server Vulnerability Scanner Plugin wrapper.
"""

import re
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin


class NiktoPlugin(BasePlugin):
    """Plugin wrapper for Nikto Web Server Scanner."""

    @property
    def name(self) -> str:
        return "nikto"

    @property
    def description(self) -> str:
        return "Web server vulnerability scanner testing for dangerous files, outdated software, and misconfigurations."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        opts = options or {}
        port = str(opts.get("port", 80))
        return ["nikto", "-h", target, "-p", port, "-Format", "txt"]

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        findings = []
        # Match Nikto stdout lines starting with '+'
        finding_pattern = re.compile(r"^\+\s+(?:(OSVDB-\d+):)?\s*(.*)$", re.MULTILINE)

        for match in finding_pattern.finditer(stdout):
            osvdb_id = match.group(1) or "N/A"
            description = match.group(2).strip()

            if "Target IP" in description or "Target Hostname" in description:
                continue

            findings.append({
                "osvdb_id": osvdb_id,
                "description": description
            })

        return findings
