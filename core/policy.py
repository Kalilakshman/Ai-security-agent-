"""
Comprehensive Security Policy Engine and Guardrail Enforcement Subsystem.
"""

import re
import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.config import AppConfig, PolicyConfig, load_config
from core.logger import get_logger

logger = get_logger("security_policy")

# Shell injection patterns to block
SHELL_INJECTION_PATTERNS = [
    re.compile(r"[;&|`$]"),                 # Shell operators
    re.compile(r"\$\(.*\)", re.DOTALL),     # Command substitution $(...)
    re.compile(r"^\s*(?:bash|sh|zsh|cmd|powershell|pwsh)\b", re.IGNORECASE), # Shell invocation
    re.compile(r"\b(?:eval|exec|system|popen)\b", re.IGNORECASE),            # Dynamic execution functions
]


class PolicyAuditEntry(BaseModel):
    """Structured audit log entry for security policy decisions."""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Event timestamp."
    )
    action: str = Field(..., description="Action evaluated (e.g. scan_execute, tool_invoke).")
    target: str = Field(..., description="Target host/URL.")
    tool_name: Optional[str] = Field(default=None, description="Tool evaluated.")
    profile: Optional[str] = Field(default=None, description="Assessment profile.")
    decision: str = Field(..., description="PERMITTED or BLOCKED.")
    reason: str = Field(..., description="Explanation of decision.")


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation containing status, reason, and sanitized input args."""
    allowed: bool = Field(..., description="True if request is permitted by security policy.")
    reason: str = Field(default="", description="Explanation if request was blocked.")
    sanitized_arguments: Dict[str, Any] = Field(default_factory=dict, description="Sanitized input arguments.")


class SecurityPolicyEngine:
    """Enterprise Security & Guardrail Policy Engine.
    
    Architecture Layer:
    User -> Authorization Validation -> Scope Validation -> Tool Policy -> MCP Gateway -> Tool
    
    Guarantees:
    - Never silently bypass policy; BLOCKS execution safely on failure.
    - AI Planner recommendations are subject to final Policy Engine decision.
    - Enforces target scope validation (allowed & denied targets).
    - Enforces tool allowlists & denylists.
    - Enforces assessment profile restrictions.
    - Enforces hard resource limits & timeout policies.
    - Maintains structured audit logs of all policy evaluations.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.policy_cfg: PolicyConfig = self.config.policy

    def _write_audit_entry(self, entry: PolicyAuditEntry) -> None:
        """Write structured audit entry to log file."""
        log_file = self.policy_cfg.audit_log_file
        if not log_file:
            return

        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write policy audit entry: {str(e)}")

    def validate_target_scope(self, target: str) -> Tuple[bool, str]:
        """Validate if target matches allowed targets and is not in denied targets list."""
        if not target or not target.strip():
            return False, "Target string is empty."

        clean_target = target.strip().lower()
        if "://" in clean_target:
            clean_target = clean_target.split("://")[1].split("/")[0].split(":")[0]

        # 1. Denied Target Check (Denylist takes precedence)
        for pattern in self.policy_cfg.denied_targets:
            if fnmatch.fnmatch(clean_target, pattern.lower()) or re.search(pattern, clean_target):
                return False, f"Target '{target}' matches explicitly denied target pattern '{pattern}'."

        # 2. Allowed Target Check (Wildcards or explicit entries)
        if "*" in self.policy_cfg.allowed_targets or "*.*" in self.policy_cfg.allowed_targets:
            return True, "Target scope permitted by global wildcard."

        for pattern in self.policy_cfg.allowed_targets:
            if fnmatch.fnmatch(clean_target, pattern.lower()) or pattern.lower() in clean_target:
                return True, f"Target '{target}' matched allowed target pattern '{pattern}'."

        return False, f"Target '{target}' is not in authorized target scope."

    def validate_tool_policy(self, tool_name: str) -> Tuple[bool, str]:
        """Validate tool against allowlist and denylist."""
        tool_key = tool_name.lower().strip()

        # Denylist takes precedence
        if tool_key in [t.lower() for t in self.policy_cfg.tool_denylist]:
            return False, f"Tool '{tool_name}' is explicitly blocked by policy denylist."

        # Allowlist check
        if "*" in self.policy_cfg.tool_allowlist:
            return True, "Tool permitted by wildcard allowlist."

        if tool_key in [t.lower() for t in self.policy_cfg.tool_allowlist]:
            return True, f"Tool '{tool_name}' is in policy allowlist."

        return False, f"Tool '{tool_name}' is not permitted by tool allowlist policy."

    def validate_profile(self, profile: str) -> Tuple[bool, str]:
        """Validate assessment profile against permitted profiles list."""
        prof_key = profile.lower().strip()
        allowed = [p.lower() for p in self.policy_cfg.allowed_profiles]
        if prof_key in allowed:
            return True, f"Assessment profile '{profile}' is permitted."
        return False, f"Assessment profile '{profile}' is prohibited by policy. Permitted: {', '.join(allowed)}"

    def evaluate_execution_request(
        self,
        target: str,
        tool_name: str,
        arguments: Dict[str, Any],
        profile: str = "standard",
        authorized: bool = False,
        timeout_seconds: Optional[float] = None
    ) -> PolicyEvaluationResult:
        """Main Policy Engine decision gateway evaluating full execution requests.

        Returns:
            PolicyEvaluationResult (allowed=True/False, reason=..., sanitized_arguments=...)
        """
        # Step 1: Explicit Authorization Acknowledgement Check
        if self.policy_cfg.require_explicit_auth and not authorized:
            reason = "Execution Blocked: Explicit target authorization acknowledgement required before scanning."
            self._write_audit_entry(PolicyAuditEntry(
                action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
            ))
            return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)

        # Step 2: Target Scope Validation
        in_scope, scope_reason = self.validate_target_scope(target)
        if not in_scope:
            reason = f"Execution Blocked by Scope Validation: {scope_reason}"
            self._write_audit_entry(PolicyAuditEntry(
                action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
            ))
            return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)

        # Step 3: Tool Allowlist / Denylist Check
        tool_ok, tool_reason = self.validate_tool_policy(tool_name)
        if not tool_ok:
            reason = f"Execution Blocked by Tool Policy: {tool_reason}"
            self._write_audit_entry(PolicyAuditEntry(
                action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
            ))
            return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)

        # Step 4: Assessment Profile Restriction Check
        profile_ok, profile_reason = self.validate_profile(profile)
        if not profile_ok:
            reason = f"Execution Blocked by Profile Restriction: {profile_reason}"
            self._write_audit_entry(PolicyAuditEntry(
                action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
            ))
            return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)

        # Step 5: Timeout & Resource Limit Policy Check
        requested_timeout = timeout_seconds or self.config.timeouts.get_timeout(tool_name, profile=profile)
        if requested_timeout > self.policy_cfg.max_execution_time_seconds:
            reason = f"Execution Blocked: Requested timeout ({requested_timeout:.0f}s) exceeds policy maximum limit ({self.policy_cfg.max_execution_time_seconds:.0f}s)."
            self._write_audit_entry(PolicyAuditEntry(
                action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
            ))
            return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)

        # Step 6: Arbitrary Shell Execution Prevention & Argument Sanitization
        sanitized_args = {}
        for k, v in arguments.items():
            if isinstance(v, str):
                for pattern in SHELL_INJECTION_PATTERNS:
                    if pattern.search(v):
                        reason = f"Security Violation: Parameter '{k}' contains forbidden shell operators or injection syntax."
                        self._write_audit_entry(PolicyAuditEntry(
                            action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="BLOCKED", reason=reason
                        ))
                        return PolicyEvaluationResult(allowed=False, reason=reason, sanitized_arguments=arguments)
            sanitized_args[k] = v

        # Audit & Return Permitted Result
        success_reason = "Execution Permitted by Policy Engine."
        self._write_audit_entry(PolicyAuditEntry(
            action="tool_execute", target=target, tool_name=tool_name, profile=profile, decision="PERMITTED", reason=success_reason
        ))
        logger.info(f"Security Policy Engine PERMITTED execution of '{tool_name}' on '{target}'.")
        return PolicyEvaluationResult(allowed=True, reason=success_reason, sanitized_arguments=sanitized_args)
