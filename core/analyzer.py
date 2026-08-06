"""
AI Results Analyzer Module.

Analyzes normalized scan JSON data, extracts observed facts, formulates AI inferences,
and produces structured analysis reports while strictly avoiding hallucinating unobserved vulnerabilities.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.workflow import UnifiedScanResult
from core.llm import OpenRouterClient
from core.logger import get_logger

logger = get_logger("analyzer")


class ObservedFact(BaseModel):
    """Verifiable fact observed directly from tool output."""
    source_tool: str = Field(..., description="Tool that produced the observation.")
    finding_type: str = Field(..., description="Category of observation e.g. open_port, header, tech_stack.")
    details: Dict[str, Any] = Field(..., description="Direct raw observation details.")


class AIInference(BaseModel):
    """Contextual AI hypothesis or recommendation derived from observed facts."""
    category: str = Field(..., description="Inference category e.g. risk_hypothesis, mitigation_step.")
    fact_references: List[str] = Field(default_factory=list, description="Fact IDs or descriptions supporting this inference.")
    inference: str = Field(..., description="AI reasoning or recommendation text.")


class AnalysisReport(BaseModel):
    """Comprehensive AI Security Analysis Report structure."""
    target: str = Field(..., description="Target evaluated.")
    timestamp: str = Field(..., description="Assessment execution timestamp.")
    executive_summary: str = Field(..., description="High-level executive summary of findings.")
    observed_services: List[ObservedFact] = Field(default_factory=list, description="Explicitly observed open ports/services.")
    interesting_findings: List[ObservedFact] = Field(default_factory=list, description="Notable observed security attributes.")
    potential_risks: List[AIInference] = Field(default_factory=list, description="AI inferences regarding potential risks.")
    recommendations: List[AIInference] = Field(default_factory=list, description="Actionable remediation recommendations.")
    confidence: float = Field(..., description="AI confidence score (0.0 to 1.0) based on evidence density.")
    unknowns: List[str] = Field(default_factory=list, description="Unverified parameters, blind spots, or required follow-ups.")


class AIResultsAnalyzer:
    """Analyzes normalized scan outputs using OpenRouter LLM with strict factual grounding."""

    def __init__(self, llm_client: Optional[OpenRouterClient] = None):
        self.llm_client = llm_client or OpenRouterClient()

    def analyze(self, scan_result: UnifiedScanResult) -> AnalysisReport:
        """Analyze UnifiedScanResult object and return structured AnalysisReport."""
        return self.analyze_json(scan_result.model_dump())

    def analyze_json(self, raw_data: Dict[str, Any]) -> AnalysisReport:
        """Analyze raw normalized scan result dictionary."""
        target = str(raw_data.get("target", "Unknown Target"))
        timestamp = str(raw_data.get("timestamp", ""))

        system_prompt = """You are a Lead DevSecOps & Security Assessment Analyst.
Your task is to analyze normalized security scan JSON data and produce a structured analysis report.

CRITICAL INSTRUCTIONS & GUARDRAILS:
1. STRICTLY DISTINGUISH between Observed Facts (direct output from scanners) vs AI Inferences (hypotheses, risks, recommendations).
2. NEVER INVENT, FABRICATE, OR HALLUCINATE vulnerabilities that are not evidenced in the scan data.
3. If no significant vulnerabilities were observed, explicitly state that in the executive summary.
4. Assign a realistic confidence score between 0.0 and 1.0 based on data completeness.
5. Return your output STRICTLY as valid JSON matching this exact schema:
{
  "target": "string",
  "timestamp": "string",
  "executive_summary": "string",
  "observed_services": [
    {
      "source_tool": "string",
      "finding_type": "string",
      "details": {}
    }
  ],
  "interesting_findings": [
    {
      "source_tool": "string",
      "finding_type": "string",
      "details": {}
    }
  ],
  "potential_risks": [
    {
      "category": "risk_hypothesis",
      "fact_references": ["string"],
      "inference": "string"
    }
  ],
  "recommendations": [
    {
      "category": "mitigation_step",
      "fact_references": ["string"],
      "inference": "string"
    }
  ],
  "confidence": 0.85,
  "unknowns": ["string"]
}
"""

        user_content = f"Scan Result Data to Analyze:\n{json.dumps(raw_data, indent=2)}"

        logger.info(f"Analyzing scan results for target '{target}' using OpenRouter LLM...")

        try:
            llm_response = self.llm_client.complete(
                prompt=user_content,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=3000
            )

            clean_json = self._extract_json(llm_response.content)
            parsed_data = json.loads(clean_json)
            parsed_data["target"] = target
            parsed_data["timestamp"] = timestamp or parsed_data.get("timestamp", "")
            return AnalysisReport.model_validate(parsed_data)

        except Exception as e:
            logger.warning(f"AI analysis failed or returned invalid JSON ({str(e)}). Generating deterministic fact-based report.")
            return self._build_deterministic_fallback(raw_data)

    def _extract_json(self, text: str) -> str:
        """Extract clean JSON payload from Markdown formatting."""
        t = text.strip()
        if "```json" in t:
            return t.split("```json")[1].split("```")[0].strip()
        elif "```" in t:
            return t.split("```")[1].strip()
        return t

    def _build_deterministic_fallback(self, raw_data: Dict[str, Any]) -> AnalysisReport:
        """Create structured report directly from raw scan facts without AI synthesis."""
        target = str(raw_data.get("target", "Unknown"))
        timestamp = str(raw_data.get("timestamp", ""))
        step_results = raw_data.get("step_results", [])

        observed_services = []
        interesting_findings = []

        for step in step_results:
            tool = step.get("tool", "unknown")
            findings = step.get("findings", [])
            for f in findings:
                if "port_proto" in f or "service" in f:
                    observed_services.append(ObservedFact(
                        source_tool=tool,
                        finding_type="service_detection",
                        details=f
                    ))
                else:
                    interesting_findings.append(ObservedFact(
                        source_tool=tool,
                        finding_type="tool_observation",
                        details=f
                    ))

        return AnalysisReport(
            target=target,
            timestamp=timestamp,
            executive_summary=f"Automated factual analysis for target '{target}' completed with {len(observed_services) + len(interesting_findings)} total observations.",
            observed_services=observed_services,
            interesting_findings=interesting_findings,
            potential_risks=[
                AIInference(
                    category="risk_hypothesis",
                    fact_references=[f.source_tool for f in observed_services[:3]],
                    inference="Exposed services should be reviewed against current organization patch baselines and access control policies."
                )
            ],
            recommendations=[
                AIInference(
                    category="mitigation_step",
                    fact_references=[],
                    inference="Ensure all open administrative interfaces are protected behind VPN/MFA."
                )
            ],
            confidence=0.75,
            unknowns=["Detailed vulnerability CVE matching requires targeted authenticated assessment."]
        )
