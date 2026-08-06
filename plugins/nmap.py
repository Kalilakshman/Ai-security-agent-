"""
Nmap Network Scanner Plugin wrapper.
"""

import re
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin


class NmapPlugin(BasePlugin):
    """Plugin wrapper for Nmap Network Mapper."""

    @property
    def name(self) -> str:
        return "nmap"

    @property
    def description(self) -> str:
        return "Network exploration tool and security/port scanner."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        opts = options or {}
        ports = opts.get("ports", "80,443")
        scan_type = opts.get("scan_type", "-sV")

        command = ["nmap", "-p", str(ports)]
        if scan_type:
            command.append(scan_type)
        command.append(target)
        return command

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        findings = []
        # Pattern to match open ports e.g., 80/tcp open http Apache httpd 2.4.41
        port_pattern = re.compile(r"^(\d+/(?:tcp|udp))\s+(\w+)\s+(\S+)(?:\s+(.*))?$", re.MULTILINE)

        for match in port_pattern.finditer(stdout):
            port_proto = match.group(1)
            state = match.group(2)
            service = match.group(3)
            version = match.group(4) or ""

            findings.append({
                "port_proto": port_proto,
                "state": state,
                "service": service,
                "version": version.strip(),
            })

        return findings
