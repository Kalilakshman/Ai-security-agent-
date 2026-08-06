"""
Unit tests for Phase 2 Plugin Architecture and Dynamic Registry.
"""

import pytest
from core.registry import get_registry, PluginRegistry
from plugins.base import BasePlugin, StandardPluginOutput
from plugins.nmap import NmapPlugin
from plugins.whatweb import WhatWebPlugin
from plugins.nikto import NiktoPlugin
from plugins.gobuster import GobusterPlugin
from plugins.nuclei import NucleiPlugin


def test_registry_auto_discovery():
    """Test PluginRegistry auto-discovers all tool plugins in plugins directory."""
    registry = get_registry()
    plugins = registry.list_plugins()

    expected_tools = {"nmap", "whatweb", "nikto", "gobuster", "nuclei"}
    registered_tools = set(plugins.keys())

    assert expected_tools.issubset(registered_tools)


def test_nmap_plugin_command_and_parse():
    """Test Nmap plugin command construction and output parsing."""
    plugin = NmapPlugin()
    cmd = plugin.build_command("127.0.0.1", {"ports": "80,443", "scan_type": "-sV"})
    assert cmd == ["nmap", "-p", "80,443", "-sV", "127.0.0.1"]

    sample_stdout = "80/tcp open http Apache httpd 2.4.41\n443/tcp open ssl/https OpenSSL 1.1.1"
    findings = plugin.parse(sample_stdout, "")
    assert len(findings) == 2
    assert findings[0]["port_proto"] == "80/tcp"
    assert findings[0]["service"] == "http"


def test_whatweb_plugin_command_and_parse():
    """Test WhatWeb plugin command construction and JSON parsing."""
    plugin = WhatWebPlugin()
    cmd = plugin.build_command("http://example.com")
    assert cmd == ["whatweb", "-a1", "--log-json=-", "http://example.com"]

    sample_stdout = '[{"target":"http://example.com","http_status":200,"plugins":{"Apache":{"version":["2.4.41"]}}}]'
    findings = plugin.parse(sample_stdout, "")
    assert len(findings) == 1
    assert findings[0]["target_url"] == "http://example.com"
    assert "Apache" in findings[0]["technologies"]


def test_nikto_plugin_command_and_parse():
    """Test Nikto plugin command building and stdout parsing."""
    plugin = NiktoPlugin()
    cmd = plugin.build_command("example.com", {"port": 8080})
    assert cmd == ["nikto", "-h", "example.com", "-p", "8080", "-Format", "txt"]

    sample_stdout = "+ OSVDB-3092: /admin/: Directory indexing enabled."
    findings = plugin.parse(sample_stdout, "")
    assert len(findings) == 1
    assert findings[0]["osvdb_id"] == "OSVDB-3092"


def test_gobuster_plugin_command_and_parse():
    """Test Gobuster plugin command building and stdout parsing."""
    plugin = GobusterPlugin()
    cmd = plugin.build_command("http://example.com", {"mode": "dir", "wordlist": "/tmp/wl.txt"})
    assert cmd == ["gobuster", "dir", "-u", "http://example.com", "-w", "/tmp/wl.txt", "--no-color"]

    sample_stdout = "/admin (Status: 200) [Size: 1234]\n/login (Status: 302)"
    findings = plugin.parse(sample_stdout, "")
    assert len(findings) == 2
    assert findings[0]["path"] == "/admin"
    assert findings[0]["status_code"] == 200


def test_nuclei_plugin_command_and_parse():
    """Test Nuclei plugin command building and JSONL parsing."""
    plugin = NucleiPlugin()
    cmd = plugin.build_command("http://example.com")
    assert cmd == ["nuclei", "-u", "http://example.com", "-severity", "medium,high,critical", "-jsonl", "-silent"]

    sample_stdout = '{"template-id":"cve-2021-44228","info":{"name":"Log4j RCE","severity":"critical"},"matched-at":"http://example.com"}'
    findings = plugin.parse(sample_stdout, "")
    assert len(findings) == 1
    assert findings[0]["template_id"] == "cve-2021-44228"
    assert findings[0]["severity"] == "critical"


def test_standard_json_output_schema():
    """Test plugin execution produces Standard JSON schema payload."""
    plugin = NmapPlugin()
    output = plugin.execute("127.0.0.1")

    assert isinstance(output, StandardPluginOutput)
    assert output.tool == "nmap"
    assert output.target == "127.0.0.1"
    assert output.status in ("COMPLETED", "FAILED", "TIMED_OUT", "NOT_INSTALLED")
    assert isinstance(output.findings, list)
    assert isinstance(output.errors, list)
    assert isinstance(output.metadata, dict)
