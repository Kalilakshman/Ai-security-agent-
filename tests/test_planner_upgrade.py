"""
Unit tests for Upgraded AI Strategic Planner using mocked LLM responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from core.llm import LLMProvider
from core.planner import AIPlanner, ExecutionPlan, PlannedStep
from core.config import AppConfig, PolicyConfig
from core.policy import SecurityPolicyEngine


class MockLLMProvider(LLMProvider):
    def provider_name(self) -> str:
        return "mock_llm"

    def available_models(self) -> list[str]:
        return ["mock-model-v1"]

    def generate(self, prompt: str, system_prompt=None, model=None, temperature=None, max_tokens=None) -> str:
        if "web_application" in prompt.lower():
            return json.dumps({
                "target": "http://testapp.local",
                "target_type": "web_application",
                "assessment_type": "web_vulnerability_scan",
                "profile": "deep",
                "scope_summary": "Web Application assessment scope",
                "selected_plugins": ["whatweb", "owasp_zap"],
                "execution_order": [
                    {
                        "step_number": 1,
                        "tool": "whatweb",
                        "purpose": "HTTP Fingerprinting",
                        "selection_reason": "Identify technology stack and web server headers.",
                        "depends_on": [],
                        "estimated_duration_seconds": 60.0,
                        "options": {}
                    },
                    {
                        "step_number": 2,
                        "tool": "owasp_zap",
                        "purpose": "Web Application Vulnerability Assessment",
                        "selection_reason": "Scan web endpoints for OWASP Top 10 vulnerabilities.",
                        "depends_on": [1],
                        "estimated_duration_seconds": 900.0,
                        "options": {}
                    }
                ],
                "estimated_duration_seconds": 960.0,
                "reasoning": "Target is a web application, so HTTP fingerprinting and web vulnerability scanning are recommended."
            })
        return json.dumps({
            "target": "127.0.0.1",
            "target_type": "network_host",
            "assessment_type": "network_recon",
            "profile": "standard",
            "scope_summary": "Network host assessment scope",
            "selected_plugins": ["nmap"],
            "execution_order": [
                {
                    "step_number": 1,
                    "tool": "nmap",
                    "purpose": "Port Scanning",
                    "selection_reason": "Discover open ports and services.",
                    "depends_on": [],
                    "estimated_duration_seconds": 120.0,
                    "options": {}
                }
            ],
            "estimated_duration_seconds": 120.0,
            "reasoning": "Network host target requires port scanning."
        })

    def health_check(self) -> bool:
        return True


def test_target_type_classification():
    """Test target classification logic."""
    planner = AIPlanner()
    assert planner.classify_target_type("http://example.com") == "web_application"
    assert planner.classify_target_type("https://app.domain.com:8443/login") == "web_application"
    assert planner.classify_target_type("192.168.1.100") == "network_host"
    assert planner.classify_target_type("10.0.0.0/24") == "subnet"
    assert planner.classify_target_type("internal.corp.local") == "domain"


def test_discover_healthy_tools():
    """Test discovering healthy and installed tools across registries."""
    planner = AIPlanner()
    tools = planner.discover_healthy_tools()
    assert isinstance(tools, list)
    # Check tool entries have required keys
    for t in tools:
        assert "name" in t
        assert "description" in t
        assert "source" in t


def test_generate_plan_web_application_mock():
    """Test AIPlanner plan generation with mock LLM for web application."""
    mock_llm = MockLLMProvider()
    planner = AIPlanner(llm_provider=mock_llm)

    plan = planner.generate_plan(
        target="http://testapp.local",
        profile="deep",
        previous_evidence={"prior_scans": 1}
    )

    assert isinstance(plan, ExecutionPlan)
    assert plan.target == "http://testapp.local"
    assert plan.target_type == "web_application"
    assert plan.profile == "deep"
    assert len(plan.execution_order) == 2

    step1 = plan.execution_order[0]
    assert step1.tool == "whatweb"
    assert "Fingerprinting" in step1.purpose
    assert step1.selection_reason != ""

    step2 = plan.execution_order[1]
    assert step2.tool == "owasp_zap"
    assert step2.depends_on == [1]


def test_planner_policy_prevalidation_filtering():
    """Test that planner pre-validation drops steps blocked by Policy Engine."""
    mock_llm = MockLLMProvider()

    # Policy engine blocking owasp_zap
    cfg = AppConfig(
        policy=PolicyConfig(
            allowed_targets=["127.0.0.1", "localhost", "testapp.local"],
            tool_allowlist=["whatweb"],  # owasp_zap not in allowlist
            tool_denylist=["owasp_zap"]
        )
    )
    policy_engine = SecurityPolicyEngine(config=cfg)
    planner = AIPlanner(llm_provider=mock_llm, policy_engine=policy_engine)

    plan = planner.generate_plan("http://testapp.local", profile="deep")
    # Step 2 (owasp_zap) should be dropped by policy pre-validation
    tools_in_plan = [s.tool for s in plan.execution_order]
    assert "whatweb" in tools_in_plan
    assert "owasp_zap" not in tools_in_plan


def test_fallback_plan_generation():
    """Test fallback plan generation when LLM fails or returns invalid JSON."""
    failing_llm = MagicMock(spec=LLMProvider)
    failing_llm.generate.side_effect = RuntimeError("LLM API connection error")

    planner = AIPlanner(llm_provider=failing_llm)
    plan = planner.generate_plan("192.168.1.1", profile="fast")

    assert isinstance(plan, ExecutionPlan)
    assert plan.target == "192.168.1.1"
    assert plan.target_type == "network_host"
    assert "Fallback" in plan.reasoning
