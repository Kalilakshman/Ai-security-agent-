"""
Gobuster Directory/DNS Brute-forcer Plugin wrapper.
"""

import re
from typing import Dict, List, Any, Optional
from plugins.base import BasePlugin


class GobusterPlugin(BasePlugin):
    """Plugin wrapper for Gobuster Directory / Subdomain / DNS Enumerator."""

    @property
    def name(self) -> str:
        return "gobuster"

    @property
    def description(self) -> str:
        return "URIs and DNS subdomains brute-forcing tool written in Go."

    def build_command(self, target: str, options: Optional[Dict[str, Any]] = None) -> List[str]:
        opts = options or {}
        mode = opts.get("mode", "dir")
        wordlist = opts.get("wordlist", "/usr/share/wordlists/dirb/common.txt")

        command = ["gobuster", mode, "-u" if mode == "dir" else "-d", target, "-w", wordlist, "--no-color"]
        return command

    def parse(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        findings = []
        # Pattern matching Gobuster dir output e.g., /admin (Status: 200) [Size: 1234]
        dir_pattern = re.compile(r"^(\/\S+)\s+\(Status:\s*(\d+)\)(?:\s+\[Size:\s*(\d+)\])?", re.MULTILINE)

        for match in dir_pattern.finditer(stdout):
            path = match.group(1)
            status_code = int(match.group(2))
            size = int(match.group(3)) if match.group(3) else None

            findings.append({
                "path": path,
                "status_code": status_code,
                "size_bytes": size
            })

        return findings
