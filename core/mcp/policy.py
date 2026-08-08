"""
MCP Policy Engine enforcing security guardrails and shell command injection prevention.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.mcp.models import MCPToolMetadata
from core.logger import get_logger

logger = get_logger("mcp_policy")

# Dangerous command injection patterns to block
SHELL_INJECTION_PATTERNS = [
    re.compile(r"[;&|`$]"),                 # Shell operators
    re.compile(r"\$\(.*\)" , re.DOTALL),    # Command substitution $(...)
    re.compile(r"^\s*(?:bash|sh|zsh|cmd|powershell|pwsh)\b", re.IGNORECASE), # Shell invocation
    re.compile(r"\b(?:eval|exec|system|popen)\b", re.IGNORECASE),            # Dynamic execution functions
]


from core.policy import SecurityPolicyEngine, PolicyEvaluationResult
from core.mcp.models import MCPToolMetadata
from core.logger import get_logger

logger = get_logger("mcp_policy")


class PolicyCheckResult(BaseModel):
    """Result of policy evaluation for a tool invocation request."""
    allowed: bool = Field(..., description="True if request is permitted by policy.")
    reason: str = Field(default="", description="Explanation if request was blocked.")
    sanitized_arguments: Dict[str, Any] = Field(default_factory=dict, description="Sanitized input arguments.")


class MCPPolicyEngine:
    """Evaluates security guardrails before allowing MCP Gateway tool execution.
    
    Architecture Layer:
    User -> Authorization Validation -> Scope Validation -> Tool Policy -> MCP Gateway -> Tool
    
    Guarantees:
    - AI cannot execute arbitrary shell commands.
    - Input arguments are validated and sanitized.
    - Target authorization acknowledgement is enforced.
    - Target scope (allowed & denied targets) is validated.
    - Destructive tools require explicit authorization.
    """

    def __init__(self, allow_destructive: bool = False, security_policy: Optional[SecurityPolicyEngine] = None):
        self.allow_destructive = allow_destructive
        self.security_policy = security_policy or SecurityPolicyEngine()

    def evaluate(
        self,
        tool_metadata: MCPToolMetadata,
        target: Optional[str],
        arguments: Dict[str, Any],
        authorized: bool = False,
        profile: str = "standard"
    ) -> PolicyCheckResult:
        """Evaluate request against security policy rules."""
        # Rule 1: Tool enabled check
        if not tool_metadata.enabled:
            return PolicyCheckResult(
                allowed=False,
                reason=f"MCP tool '{tool_metadata.name}' is currently disabled.",
                sanitized_arguments=arguments
            )

        # Rule 2: Unhealthy tool check
        if tool_metadata.health == "UNHEALTHY":
            return PolicyCheckResult(
                allowed=False,
                reason=f"MCP tool '{tool_metadata.name}' is unhealthy and unavailable.",
                sanitized_arguments=arguments
            )

        # Rule 3: Destructive capability policy check
        if tool_metadata.capabilities.is_destructive and not self.allow_destructive:
            return PolicyCheckResult(
                allowed=False,
                reason=f"Tool '{tool_metadata.name}' has destructive capabilities which are prohibited by policy.",
                sanitized_arguments=arguments
            )

        # Rule 4: Delegate target scope, authorization, tool allowlist, and shell injection checks to SecurityPolicyEngine
        target_str = target or str(arguments.get("target", "127.0.0.1"))
        sec_res: PolicyEvaluationResult = self.security_policy.evaluate_execution_request(
            target=target_str,
            tool_name=tool_metadata.name,
            arguments=arguments,
            profile=profile,
            authorized=authorized
        )

        return PolicyCheckResult(
            allowed=sec_res.allowed,
            reason=sec_res.reason,
            sanitized_arguments=sec_res.sanitized_arguments
        )
