"""
Comprehensive unit tests for Security Policy Engine and Authorization Layer.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.config import AppConfig, PolicyConfig
from core.policy import SecurityPolicyEngine, PolicyAuditEntry, PolicyEvaluationResult
from core.mcp.policy import MCPPolicyEngine
from core.mcp.models import MCPToolMetadata, MCPToolCapabilities
from core.workflow import WorkflowEngine
from core.planner import ExecutionPlan, PlannedStep


@pytest.fixture
def policy_config(tmp_path):
    audit_file = str(tmp_path / "test_audit.log")
    return AppConfig(
        policy=PolicyConfig(
            allowed_targets=["127.0.0.1", "localhost", "192.168.*", "10.*", "*.local"],
            denied_targets=["*.gov", "*.mil", "169.254.169.254"],
            tool_allowlist=["nmap", "whatweb", "nikto", "gobuster", "nuclei", "owasp_zap", "burp_suite", "tshark", "metasploit"],
            tool_denylist=["destructive_exploit_tool"],
            allowed_profiles=["fast", "standard", "deep"],
            max_execution_time_seconds=3600.0,
            require_explicit_auth=True,
            audit_log_file=audit_file
        )
    )


@pytest.fixture
def policy_engine(policy_config):
    return SecurityPolicyEngine(config=policy_config)


def test_authorization_acknowledgement_required(policy_engine):
    """Test that explicit authorization acknowledgement is enforced."""
    res = policy_engine.evaluate_execution_request(
        target="127.0.0.1",
        tool_name="nmap",
        arguments={},
        authorized=False
    )
    assert res.allowed is False
    assert "Explicit target authorization acknowledgement required" in res.reason


def test_target_scope_validation_allowed_and_denied(policy_engine):
    """Test target scope validation for allowed and denied targets."""
    # Allowed localhost
    res_local = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, authorized=True
    )
    assert res_local.allowed is True

    # Denied .gov target
    res_gov = policy_engine.evaluate_execution_request(
        target="subdomain.target.gov", tool_name="nmap", arguments={}, authorized=True
    )
    assert res_gov.allowed is False
    assert "explicitly denied" in res_gov.reason

    # Out of scope domain
    res_out = policy_engine.evaluate_execution_request(
        target="unauthorized-external-site.com", tool_name="nmap", arguments={}, authorized=True
    )
    assert res_out.allowed is False
    assert "not in authorized target scope" in res_out.reason


def test_tool_allowlist_and_denylist(policy_engine):
    """Test enforcement of tool allowlist and denylist."""
    # Allowed tool
    res_nmap = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, authorized=True
    )
    assert res_nmap.allowed is True

    # Tool on denylist
    res_deny = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="destructive_exploit_tool", arguments={}, authorized=True
    )
    assert res_deny.allowed is False
    assert "blocked by policy denylist" in res_deny.reason

    # Tool not on allowlist
    res_unlisted = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="random_untrusted_plugin", arguments={}, authorized=True
    )
    assert res_unlisted.allowed is False
    assert "not permitted by tool allowlist policy" in res_unlisted.reason


def test_assessment_profile_restrictions(policy_engine):
    """Test assessment profile restrictions."""
    # Permitted profile
    res_std = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, profile="deep", authorized=True
    )
    assert res_std.allowed is True

    # Prohibited profile
    res_invalid = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, profile="unlimited_aggressive", authorized=True
    )
    assert res_invalid.allowed is False
    assert "prohibited by policy" in res_invalid.reason


def test_timeout_resource_limits(policy_engine):
    """Test enforcement of timeout limits."""
    res_timeout = policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, authorized=True, timeout_seconds=99999.0
    )
    assert res_timeout.allowed is False
    assert "exceeds policy maximum limit" in res_timeout.reason


def test_shell_injection_sanitization(policy_engine):
    """Test prevention of arbitrary shell command execution."""
    res_inj = policy_engine.evaluate_execution_request(
        target="127.0.0.1",
        tool_name="nmap",
        arguments={"target": "127.0.0.1; cat /etc/passwd"},
        authorized=True
    )
    assert res_inj.allowed is False
    assert "forbidden shell operators" in res_inj.reason


def test_audit_log_writing(policy_engine, policy_config):
    """Test that audit log file receives structured decision entries."""
    policy_engine.evaluate_execution_request(
        target="127.0.0.1", tool_name="nmap", arguments={}, authorized=True
    )

    audit_file = Path(policy_config.policy.audit_log_file)
    assert audit_file.exists()

    with open(audit_file, "r") as f:
        lines = f.readlines()
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["decision"] == "PERMITTED"
        assert entry["target"] == "127.0.0.1"
        assert entry["tool_name"] == "nmap"


def test_mcp_policy_engine_delegation(policy_engine):
    """Test MCPPolicyEngine delegates scope and authorization checks to SecurityPolicyEngine."""
    mcp_policy = MCPPolicyEngine(security_policy=policy_engine)
    meta = MCPToolMetadata(
        name="nmap",
        description="Nmap tool",
        category="reconnaissance",
        server_id="mock_server"
    )

    # Authorized in-scope
    res_ok = mcp_policy.evaluate(tool_metadata=meta, target="127.0.0.1", arguments={}, authorized=True)
    assert res_ok.allowed is True

    # Unauthorized
    res_unauth = mcp_policy.evaluate(tool_metadata=meta, target="127.0.0.1", arguments={}, authorized=False)
    assert res_unauth.allowed is False


def test_workflow_engine_blocks_policy_violations(policy_engine):
    """Test WorkflowEngine blocks execution if policy engine fails."""
    workflow = WorkflowEngine(policy_engine=policy_engine)
    plan = ExecutionPlan(
        target="127.0.0.1",
        scope_summary="Localhost test",
        selected_plugins=["random_untrusted_plugin"],
        execution_order=[PlannedStep(step_number=1, tool="random_untrusted_plugin", purpose="test")],
        estimated_duration_seconds=5.0,
        reasoning="Test"
    )

    result = workflow.execute_plan(plan, authorized=True)
    assert result.step_results[0].status == "FAILED"
    assert "Policy Block" in result.step_results[0].errors[0]
