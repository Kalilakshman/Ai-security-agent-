"""
Unit tests for Extensible Security-Tool Adapter Subsystem.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.adapters.models import NormalizedToolEvidence, NormalizedFinding, ToolCapabilityMetadata
from core.adapters.base import BaseToolAdapter
from core.adapters.nmap import NmapAdapter
from core.adapters.zap import OWASPZAPAdapter
from core.adapters.burp import BurpSuiteAdapter
from core.adapters.tshark import WiresharkTsharkAdapter
from core.adapters.metasploit import MetasploitRPCAdapter
from core.adapters.registry import ToolAdapterRegistry, get_adapter_registry
from app.cli import app


def test_nmap_adapter_installation_and_version():
    """Test NmapAdapter version detection and health check when uninstalled or mocked."""
    adapter = NmapAdapter()
    with patch("shutil.which", return_value=None):
        assert adapter.is_installed() is False
        assert adapter.detect_version() == "Not Installed"
        assert adapter.health_check() is False

    with patch("shutil.which", return_value="/usr/bin/nmap"):
        with patch.object(adapter.executor, "execute") as mock_exec:
            res = MagicMock()
            res.is_success = True
            res.stdout = "Nmap version 7.94 ( https://nmap.org )"
            mock_exec.return_value = res

            assert adapter.is_installed() is True
            assert adapter.detect_version() == "7.94"
            assert adapter.health_check() is True


def test_nmap_adapter_execute():
    """Test NmapAdapter execute produces NormalizedToolEvidence."""
    adapter = NmapAdapter()
    with patch("shutil.which", return_value="/usr/bin/nmap"):
        with patch.object(adapter.executor, "execute") as mock_exec:
            res = MagicMock()
            res.is_success = True
            res.stdout = "80/tcp open http Apache httpd 2.4.41\n443/tcp open ssl/https OpenSSL 1.1.1"
            res.stderr = ""
            res.exit_code = 0
            res.timed_out = False
            mock_exec.return_value = res

            evidence = adapter.execute("127.0.0.1", options={"ports": "80,443"})
            assert isinstance(evidence, NormalizedToolEvidence)
            assert evidence.success is True
            assert len(evidence.normalized_findings) == 2
            assert evidence.normalized_findings[0].category == "open_port"


def test_owasp_zap_adapter_api_calls(httpx_mock):
    """Test OWASPZAPAdapter health check and alert querying via REST API."""
    adapter = OWASPZAPAdapter(api_url="http://localhost:8080", api_key="testkey")
    assert adapter.name == "owasp_zap"
    assert adapter.category == "web_assessment"

    with patch("httpx.Client.get") as mock_get:
        resp_version = MagicMock()
        resp_version.status_code = 200
        resp_version.json.return_value = {"version": "2.14.0"}
        mock_get.return_value = resp_version

        assert adapter.health_check() is True
        assert adapter.detect_version() == "2.14.0"

    with patch("httpx.Client.get") as mock_get:
        resp_alerts = MagicMock()
        resp_alerts.status_code = 200
        resp_alerts.json.return_value = {
            "alerts": [
                {"id": "1", "alert": "X-Content-Type-Options Header Missing", "risk": "Low", "url": "http://example.com"}
            ]
        }
        mock_get.return_value = resp_alerts

        evidence = adapter.execute("example.com")
        assert evidence.success is True
        assert len(evidence.normalized_findings) == 1
        assert evidence.normalized_findings[0].title == "X-Content-Type-Options Header Missing"


def test_burp_suite_adapter_uninstalled_graceful():
    """Test BurpSuiteAdapter handles offline daemon gracefully."""
    adapter = BurpSuiteAdapter(api_url="http://localhost:9999")
    with patch("httpx.Client.get", side_effect=Exception("Connection refused")):
        assert adapter.is_installed() is False
        assert adapter.health_check() is False

        evidence = adapter.execute("example.com")
        assert evidence.success is False
        assert evidence.status_code == 503
        assert "not reachable" in evidence.errors[0]


def test_tshark_adapter_execute():
    """Test WiresharkTsharkAdapter execution and JSON parsing."""
    adapter = WiresharkTsharkAdapter()
    with patch("shutil.which", return_value="/usr/bin/tshark"):
        with patch.object(adapter.executor, "execute") as mock_exec:
            res = MagicMock()
            res.is_success = True
            res.stdout = '[{"_source": {"layers": {"frame": {"frame.protocols": "eth:ip:tcp"}, "ip": {"ip.src": "10.0.0.1", "ip.dst": "10.0.0.2"}}}}]'
            res.stderr = ""
            res.exit_code = 0
            res.timed_out = False
            mock_exec.return_value = res

            evidence = adapter.execute("10.0.0.1")
            assert evidence.success is True
            assert len(evidence.normalized_findings) == 1
            assert evidence.normalized_findings[0].category == "packet_frame"


def test_metasploit_adapter_rpc_execution():
    """Test MetasploitRPCAdapter REST/RPC execution."""
    adapter = MetasploitRPCAdapter(api_url="http://127.0.0.1:55553", api_key="msfkey")
    with patch("httpx.Client.get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"version": "6.3.0-dev"}
        mock_get.return_value = resp

        assert adapter.health_check() is True

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        with patch("httpx.Client.post") as mock_post:
            resp_exec = MagicMock()
            resp_exec.status_code = 200
            resp_exec.json.return_value = {"job_id": 1, "status": "running"}
            mock_post.return_value = resp_exec

            evidence = adapter.execute("127.0.0.1", options={"module": "auxiliary/scanner/http/title"})
            assert evidence.success is True
            assert len(evidence.normalized_findings) == 1


def test_tool_adapter_registry_auto_bridge():
    """Test registering adapters bridges them into core PluginRegistry."""
    registry = get_adapter_registry()
    adapters = registry.list_adapters()

    expected_tools = {"nmap", "owasp_zap", "burp_suite", "tshark", "metasploit"}
    assert expected_tools.issubset(set(adapters.keys()))

    from core.registry import get_registry
    core_plugins = get_registry().list_plugins()
    assert expected_tools.issubset(set(core_plugins.keys()))


def test_cli_tools_commands(cli_runner):
    """Test 'security-ai tools' CLI subcommands."""
    res_list = cli_runner.invoke(app, ["tools", "list"])
    assert res_list.exit_code == 0
    assert "EXTENSIBLE SECURITY TOOL MATRIX" in res_list.output
    assert "nmap" in res_list.output

    res_info = cli_runner.invoke(app, ["tools", "info", "nmap"])
    assert res_info.exit_code == 0
    assert "ADAPTER METADATA: NMAP" in res_info.output

    res_health = cli_runner.invoke(app, ["tools", "health"])
    assert res_health.exit_code == 0
    assert "SECURITY TOOL HEALTH DIAGNOSTICS" in res_health.output
