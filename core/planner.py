"""
AI Security Assessment Planner.

Understands user target intent, queries available registered tool plugins,
generates structured execution plans via OpenRouter LLM, and explains reasoning.
Strictly avoids fabricating scan findings.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.llm import OpenRouterClient
from core.registry import get_registry, PluginRegistry
from core.logger import get_logger

logger = get_logger("planner")


class PlannedStep(BaseModel):
    """Single step in an AI assessment execution plan."""
    step_number: int = Field(..., description="Sequence step index.")
    tool: str = Field(..., description="Name of plugin tool to execute.")
    options: Dict[str, Any] = Field(default_factory=dict, description="Command line options/flags for plugin.")
    purpose: str = Field(..., description="Objective of this specific scan step.")


class ExecutionPlan(BaseModel):
    """Complete AI-generated security assessment plan."""
    target: str = Field(..., description="Target host, domain, IP, or URL.")
    scope_summary: str = Field(..., description="AI assessment of target scope and classification.")
    selected_plugins: List[str] = Field(..., description="Plugins chosen for execution.")
    execution_order: List[PlannedStep] = Field(..., description="Sequential ordered scan steps.")
    estimated_duration_seconds: float = Field(..., description="Estimated total execution wall-clock time.")
    reasoning: str = Field(..., description="AI strategic reasoning for selecting these tools and ordering.")


class AIPlanner:
    """Intelligent Planner formulating security assessment plans."""

    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,
        registry: Optional[PluginRegistry] = None
    ):
        self.llm_client = llm_client or OpenRouterClient()
        self.registry = registry or get_registry()

    def generate_plan(self, target: str, prompt_override: Optional[str] = None) -> ExecutionPlan:
        """Analyze target, query registered plugins, and build an ExecutionPlan using OpenRouter LLM."""
        registered_plugins = self.registry.list_plugins()
        plugin_metadata = []

        for name, plugin in registered_plugins.items():
            plugin_metadata.append({
                "name": name,
                "description": plugin.description,
                "is_installed": plugin.is_installed()
            })

        system_prompt = """You are a Senior DevSecOps & Security Automation Architect.
Your task is to analyze a target and formulate a structured security assessment plan using ONLY the provided list of registered tools.

Rules:
1. Select ONLY tools that are installed and relevant to the target.
2. Formulate a safe, logical, non-destructive sequential execution order.
3. Provide transparent strategic reasoning explaining why each tool was selected.
4. Estimate total execution wall-clock time in seconds realistically.
5. Do NOT fabricate or invent scan findings or vulnerability results.
6. Return your output STRICTLY as valid JSON matching this exact JSON schema:
{
  "target": "string",
  "scope_summary": "string",
  "selected_plugins": ["string"],
  "execution_order": [
    {
      "step_number": 1,
      "tool": "string",
      "options": {},
      "purpose": "string"
    }
  ],
  "estimated_duration_seconds": 60.0,
  "reasoning": "string"
}
"""

        user_content = f"""Target to assess: {target}
User additional instructions: {prompt_override or 'None'}

Available Registered Security Tool Plugins:
{json.dumps(plugin_metadata, indent=2)}

Formulate a security assessment execution plan in JSON.
"""

        logger.info(f"Generating AI assessment plan for target '{target}' using {self.llm_client.model}...")

        try:
            llm_response = self.llm_client.complete(
                prompt=user_content,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2048
            )

            raw_json = self._extract_json(llm_response.content)
            data = json.loads(raw_json)
            plan = ExecutionPlan.model_validate(data)
            return plan

        except Exception as e:
            logger.warning(f"AI Plan generation failed or returned invalid JSON ({str(e)}). Generating structured fallback plan.")
            return self._build_fallback_plan(target, registered_plugins)

    def _extract_json(self, text: str) -> str:
        """Extract clean JSON string from Markdown code blocks if present."""
        text_str = text.strip()
        if "```json" in text_str:
            parts = text_str.split("```json")
            if len(parts) > 1:
                json_part = parts[1].split("```")[0]
                return json_part.strip()
        elif "```" in text_str:
            parts = text_str.split("```")
            if len(parts) > 1:
                return parts[1].strip()
        return text_str

    def _build_fallback_plan(self, target: str, plugins: Dict[str, Any]) -> ExecutionPlan:
        """Generate structured deterministic fallback plan when LLM is offline/unreachable."""
        installed = [name for name, p in plugins.items() if p.is_installed()]
        selected = installed if installed else list(plugins.keys())[:2]

        steps = []
        for idx, tool in enumerate(selected, 1):
            steps.append(PlannedStep(
                step_number=idx,
                tool=tool,
                options={},
                purpose=f"Initial discovery and assessment step using {tool}."
            ))

        return ExecutionPlan(
            target=target,
            scope_summary=f"Automated target assessment scope for '{target}'.",
            selected_plugins=selected,
            execution_order=steps,
            estimated_duration_seconds=float(len(selected) * 30),
            reasoning="Fallback deterministic planning applied based on installed plugin availability."
        )
