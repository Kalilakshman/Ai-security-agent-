"""
AI Security Assessment Planner Subsystem.

Understands:
- Target classification (web_application, network_host, domain, subnet)
- Assessment profiles (fast, standard, deep, custom)
- Installed & healthy security tool adapters
- MCP capabilities
- Previous evidence & prior assessment findings
- Security Policy Engine rules

Strictly avoids fabricating tool outputs or dumping unnecessary tools.
"""

import json
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.llm import LLMProvider, get_llm_provider
from core.registry import get_registry, PluginRegistry
from core.adapters import get_adapter_registry, ToolAdapterRegistry
from core.mcp import get_mcp_registry, MCPServerRegistry
from core.policy import SecurityPolicyEngine
from core.logger import get_logger

logger = get_logger("planner")


class PlannedStep(BaseModel):
    """Single step in a structured AI assessment execution plan."""
    step_number: int = Field(..., description="Sequence step index.")
    tool: str = Field(..., description="Name of plugin or MCP tool to execute.")
    purpose: str = Field(..., description="Objective of this specific scan step.")
    selection_reason: str = Field(default="", description="Explanation of why this tool was selected.")
    depends_on: List[int] = Field(default_factory=list, description="Step indices that must complete prior to this step.")
    estimated_duration_seconds: float = Field(default=60.0, description="Estimated step execution duration.")
    options: Dict[str, Any] = Field(default_factory=dict, description="Command line options or API payload parameters.")


class ExecutionPlan(BaseModel):
    """Complete AI-generated security assessment plan."""
    target: str = Field(..., description="Target host, domain, IP, or URL.")
    target_type: str = Field(default="network_host", description="Target classification (web_application, network_host, domain, subnet).")
    assessment_type: str = Field(default="vulnerability_assessment", description="Assessment type.")
    profile: str = Field(default="standard", description="Assessment profile (fast, standard, deep, custom).")
    scope_summary: str = Field(..., description="AI assessment of target scope and classification.")
    selected_plugins: List[str] = Field(..., description="Tools chosen for execution.")
    execution_order: List[PlannedStep] = Field(..., description="Sequential ordered scan steps.")
    estimated_duration_seconds: float = Field(..., description="Estimated total execution wall-clock time.")
    reasoning: str = Field(..., description="AI strategic reasoning for selecting tools, profile, and ordering.")


class AIPlanner:
    """Intelligent Strategic Planner formulating security assessment plans."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        llm_client: Optional[Any] = None,
        registry: Optional[PluginRegistry] = None,
        adapter_registry: Optional[ToolAdapterRegistry] = None,
        mcp_registry: Optional[MCPServerRegistry] = None,
        policy_engine: Optional[SecurityPolicyEngine] = None
    ):
        self.llm_provider = llm_provider or llm_client or get_llm_provider()
        self.registry = registry or get_registry()
        self.adapter_registry = adapter_registry or get_adapter_registry()
        self.mcp_registry = mcp_registry or get_mcp_registry()
        self.policy_engine = policy_engine or SecurityPolicyEngine()

    def classify_target_type(self, target: str) -> str:
        """Classify target format into web_application, network_host, domain, or subnet."""
        t = target.strip().lower()
        if t.startswith("http://") or t.startswith("https://") or ":" in t and not t.replace(":", "").isdigit():
            return "web_application"
        if "/" in t and t.replace("/", "").replace(".", "").isdigit():
            return "subnet"
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", t):
            return "network_host"
        return "domain"

    def discover_healthy_tools((self)) -> List[Dict[str, Any]]:
        """Query ToolAdapterRegistry, PluginRegistry, and MCPServerRegistry for installed & healthy tools."""
        available_tools = []
        seen = set()

        # 1. Tool Adapters
        adapters = self.adapter_registry.list_adapters()
        for name, adapter in adapters.items():
            if adapter.is_installed() and adapter.health_check():
                caps = adapter.discover_capabilities()
                available_tools.append({
                    "name": name,
                    "description": adapter.description,
                    "category": adapter.category,
                    "version": adapter.detect_version(),
                    "source": "tool_adapter",
                    "capabilities": caps.categories
                })
                seen.add(name.lower())

        # 2. Base Plugins
        plugins = self.registry.list_plugins()
        for name, plugin in plugins.items():
            if name.lower() not in seen and plugin.is_installed():
                available_tools.append({
                    "name": name,
                    "description": plugin.description,
                    "category": getattr(plugin, "category", "security_assessment"),
                    "source": "native_plugin",
                    "capabilities": []
                })
                seen.add(name.lower())

        # 3. MCP Tools
        mcp_tools = self.mcp_registry.list_tools()
        for m_tool in mcp_tools:
            if m_tool.enabled and m_tool.health == "HEALTHY" and m_tool.name.lower() not in seen:
                available_tools.append({
                    "name": m_tool.name,
                    "description": m_tool.description,
                    "category": m_tool.category,
                    "version": m_tool.version,
                    "source": f"mcp_server ({m_tool.server_id})",
                    "capabilities": [k for k, v in m_tool.capabilities.model_dump().items() if v]
                })
                seen.add(m_tool.name.lower())

        return available_tools

    def generate_plan(
        self,
        target: str,
        profile: str = "standard",
        previous_evidence: Optional[Dict[str, Any]] = None,
        prompt_override: Optional[str] = None
    ) -> ExecutionPlan:
        """Formulate a structured security assessment plan matching target type and profile depth."""
        target_type = self.classify_target_type(target)
        healthy_tools = self.discover_healthy_tools()

        system_prompt = """You are a Senior Principal Security Automation & Penetration Testing Architect.
Formulate a structured security assessment plan using ONLY the provided list of healthy, installed tools.

CRITICAL RULES:
1. Do NOT automatically include every available tool. Select ONLY tools that are directly relevant to the target type and assessment profile.
2. Provide explicit reasoning explaining WHY each tool was selected for this specific target.
3. Include clear step dependencies (`depends_on`: [step_numbers]) to establish execution ordering (e.g., fingerprinting before vulnerability scanning).
4. Estimate realistic wall-clock duration in seconds per step based on profile depth.
5. NEVER fabricate or invent tool outputs, execution logs, or vulnerability findings.
6. Return output STRICTLY as valid JSON matching this exact JSON schema:

{
  "target": "string",
  "target_type": "string",
  "assessment_type": "string",
  "profile": "string",
  "scope_summary": "string",
  "selected_plugins": ["string"],
  "execution_order": [
    {
      "step_number": 1,
      "tool": "string",
      "purpose": "string",
      "selection_reason": "string",
      "depends_on": [],
      "estimated_duration_seconds": 60.0,
      "options": {}
    }
  ],
  "estimated_duration_seconds": 120.0,
  "reasoning": "string"
}
"""

        user_content = f"""Target: {target}
Target Type: {target_type}
Assessment Profile: {profile.upper()}
Additional User Guidance: {prompt_override or 'None'}

Prior Evidence Context:
{json.dumps(previous_evidence, indent=2) if previous_evidence else 'No prior evidence recorded.'}

Installed & Operational Security Tools & MCP Capabilities:
{json.dumps(healthy_tools, indent=2)}

Formulate a context-aware security assessment execution plan in JSON.
"""

        provider_name = getattr(self.llm_provider, "provider_name", lambda: "LLMProvider")()
        logger.info(f"Formulating AI assessment plan for '{target}' ({target_type}, profile={profile}) via {provider_name}...")

        try:
            if hasattr(self.llm_provider, "generate"):
                raw_response = self.llm_provider.generate(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=2048
                )
            else:
                resp_obj = self.llm_provider.complete(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=2048
                )
                raw_response = getattr(resp_obj, "content", str(resp_obj))

            raw_json = self._extract_json(raw_response)
            data = json.loads(raw_json)

            # Ensure profile and target fields are set
            data["target"] = target
            data["profile"] = profile
            if "target_type" not in data:
                data["target_type"] = target_type

            plan = ExecutionPlan.model_validate(data)

            # Policy Engine Pre-Validation
            valid_steps = []
            for st in plan.execution_order:
                sec_eval = self.policy_engine.evaluate_execution_request(
                    target=target,
                    tool_name=st.tool,
                    arguments=st.options,
                    profile=profile,
                    authorized=True
                )
                if sec_eval.allowed:
                    valid_steps.append(st)
                else:
                    logger.warning(f"Planner pre-validation dropped step {st.step_number} ({st.tool}): {sec_eval.reason}")

            plan.execution_order = valid_steps
            plan.selected_plugins = list(set(s.tool for s in valid_steps))
            return plan

        except Exception as e:
            logger.warning(f"AI Plan generation failed or returned invalid JSON ({str(e)}). Building fallback plan.")
            return self._build_fallback_plan(target, target_type, profile, healthy_tools)

    def _extract_json(self, text: str) -> str:
        """Extract clean JSON string from Markdown code blocks if present."""
        text_str = text.strip()
        if "```json" in text_str:
            parts = text_str.split("```json")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()
        elif "```" in text_str:
            parts = text_str.split("```")
            if len(parts) > 1:
                return parts[1].strip()
        return text_str

    def _build_fallback_plan(
        self,
        target: str,
        target_type: str,
        profile: str,
        healthy_tools: List[Dict[str, Any]]
    ) -> ExecutionPlan:
        """Generate structured deterministic fallback plan when LLM is offline."""
        tool_names = [t["name"] for t in healthy_tools]

        if target_type == "web_application":
            relevant = [t for t in tool_names if t in ("whatweb", "owasp_zap", "nikto", "burp_suite", "gobuster", "nmap")]
        else:
            relevant = [t for t in tool_names if t in ("nmap", "tshark", "metasploit", "nuclei")]

        if not relevant:
            relevant = tool_names[:2] if tool_names else ["nmap"]

        steps = []
        for idx, t_name in enumerate(relevant[:4], 1):
            steps.append(PlannedStep(
                step_number=idx,
                tool=t_name,
                purpose=f"Security assessment using {t_name}",
                selection_reason=f"Selected based on target type '{target_type}' and tool availability.",
                depends_on=[idx - 1] if idx > 1 else [],
                estimated_duration_seconds=60.0 if profile == "fast" else 300.0,
                options={"profile": profile}
            ))

        return ExecutionPlan(
            target=target,
            target_type=target_type,
            assessment_type="vulnerability_assessment",
            profile=profile,
            scope_summary=f"Automated security assessment scope for '{target}' ({target_type}).",
            selected_plugins=[s.tool for s in steps],
            execution_order=steps,
            estimated_duration_seconds=sum(s.estimated_duration_seconds for s in steps),
            reasoning=f"Structured fallback plan generated for target type '{target_type}' using installed tools."
        )
