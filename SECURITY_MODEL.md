# Security Policy Engine & Authorization Model

The **AI Security Orchestrator CLI** operates under a strict, un-bypassable **Security Policy Engine** (`core/policy.py`).

---

## 🛡️ Policy Enforcement Chain

```
User Request -> Authorization Validation -> Scope Validation -> Tool Policy -> Profile & Resource Limits -> MCP Gateway -> Execution
```

Key Guardrails:
1. **Mandatory Authorization Acknowledgement**:
   - `require_explicit_auth: true`. Execution halts safely if authorization confirmation is rejected.
2. **Target Scope Boundaries**:
   - `allowed_targets` patterns (e.g. `127.0.0.1`, `localhost`, `192.168.*`, `10.*`, `*.local`).
   - `denied_targets` patterns (e.g. `*.gov`, `*.mil`, `169.254.169.254`). Denied target patterns take precedence.
3. **Tool Allowlist & Denylist**:
   - `tool_allowlist`: Tool must be in allowlist.
   - `tool_denylist`: Prohibits blacklisted tools.
4. **Shell Command Injection Prevention**:
   - Sanitizes input arguments against dangerous shell operators (`;&|`$`\`\n` and subshell execution syntax).
5. **No Output Fabrication**:
   - Findings are strictly grounded in observed evidence; vulnerabilities are never invented.
6. **Structured Audit Logging**:
   - All policy evaluations (`PERMITTED` or `BLOCKED`) are appended to `policy_audit.log`.
