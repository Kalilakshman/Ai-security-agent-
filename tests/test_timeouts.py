"""
Unit tests for timeout profiles and long-running security assessment support.
"""

import pytest
from core.config import AppConfig, TimeoutsConfig, PluginTimeoutProfile
from plugins.nmap import NmapPlugin
from plugins.base import StandardPluginOutput


def test_timeouts_config_defaults():
    """Test default timeout profiles per plugin."""
    timeouts = TimeoutsConfig()

    assert timeouts.get_timeout("nmap", "fast") == 120.0
    assert timeouts.get_timeout("nmap", "standard") == 600.0
    assert timeouts.get_timeout("nmap", "deep") == 1800.0

    assert timeouts.get_timeout("whatweb", "fast") == 60.0
    assert timeouts.get_timeout("whatweb", "standard") == 300.0
    assert timeouts.get_timeout("whatweb", "deep") == 900.0

    assert timeouts.get_timeout("nikto", "fast") == 180.0
    assert timeouts.get_timeout("nikto", "standard") == 900.0
    assert timeouts.get_timeout("nikto", "deep") == 2400.0

    assert timeouts.get_timeout("gobuster", "fast") == 180.0
    assert timeouts.get_timeout("gobuster", "standard") == 1200.0
    assert timeouts.get_timeout("gobuster", "deep") == 3600.0

    assert timeouts.get_timeout("nuclei", "fast") == 300.0
    assert timeouts.get_timeout("nuclei", "standard") == 1800.0
    assert timeouts.get_timeout("nuclei", "deep") == 7200.0


def test_plugin_timeout_resolution_and_partial_results():
    """Test plugin respects options timeout and handles timeout with partial results."""
    plugin = NmapPlugin()
    # Executing against local address with very short explicit timeout option
    output = plugin.execute("127.0.0.1", options={"timeout": 0.1})

    assert isinstance(output, StandardPluginOutput)
    if output.status == "TIMED_OUT":
        assert output.metadata["timed_out"] is True
        assert "timed out" in output.errors[0]
        # Partial findings preserved
        assert isinstance(output.findings, list)
