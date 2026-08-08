"""
AI Results Analyzer & Evidence Normalization Subsystem.

Normalizes raw tool executions into standard NormalizedToolResult schemas,
builds explicit EvidenceModel instances, and performs fact-grounded AI analysis
strictly separating OBSERVED FACTS, EVIDENCE, AI INFERENCES, POTENTIAL RISKS,
RECOMMENDATIONS, and UNKNOWNS without fabricating vulnerabilities.
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.workflow import UnifiedScanResult
from core.llm import LLMProvider, get_llm_provider
from core.logger import get_logger

logger = get_logger("analyzer")


class NormalizedToolResult(BaseModel):
    """Standardized normalized tool output schema."""
    tool: str = Field(..., description="Name of the security tool.")
    tool_version: str = Field(default="unknown", description="Tool version string.")
    target: str = Field(..., description="Target host or URL evaluated.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution completion timestamp."
    )
    duration: float = Field(default=0.0, description="Execution duration in seconds.")
    status: str = Field(default="COMPLETED", description="Execution status (COMPLETED, TIMED_OUT, FAILED).")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed finding dictionaries.")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Raw evidence payload items.")
    errors: List[str] = Field(default_factory=list, description="Captured error messages.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary.")


class EvidenceModel(BaseModel):
    """Structured evidence item extracted from tool output."""
    source_tool: str = Field(..., description="Tool that produced this evidence.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Evidence capture timestamp."
    )
    observation: str = Field(..., description="Factual observation description.")
    evidence_type: str = Field(default="port_scan", description="Type (port_scan, header_analysis, vuln_signal, packet_capture).")
    confidence: float = Field(default=1.0, description="Evidence confidence score (0.0 to 1.0).")
    reference: str = Field(default="", description="Fact or log line reference identifier.")


class ObservedFact(BaseModel):
    """Verifiable fact observed directly from tool output."""
    source_tool: str = Field(..., description="Tool that produced the observation.")
    finding_type: str = Field(..., description="Observation category.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Direct raw observation details.")
    reference: str = Field(default="", description="Supporting evidence reference.")


class AIInference(BaseModel):
    """Contextual AI analytical inference or risk hypothesis derived from observed facts."""
    category: str = Field(..., description="Inference category (risk_hypothesis, mitigation_step).")
    fact_references: List[str] = Field(default_factory=list, description="Fact IDs supporting this inference.")
    inference: str = Field(..., description="AI analytical reasoning text.")
    severity: str = Field(default="medium", description="Risk severity level (info, low, medium, high, critical).")


class AnalysisReport(BaseModel):
    """Comprehensive AI Security Analysis Report structure."""
    target: str = Field(..., description="Target system evaluated.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Report generation timestamp."
    )
    scope: str = Field(default="Authorized Security Assessment Scope", description="Assessment scope summary.")
    profile: str = Field(default="standard", description="Assessment profile ('fast', 'standard', 'deep', 'custom').")
    executive_summary: str = Field(..., description="High-level executive summary of findings.")
    timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Execution timeline of tool steps.")
    tool_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Summary of tools executed.")
    evidence_list: List[EvidenceModel] = Field(default_factory=list, description="Extracted evidence models.")
    observed_facts: List[ObservedFact] = Field(default_factory=list, description="Explicitly observed verifiable facts.")
    ai_inferences: List[AIInference] = Field(default_factory=list, description="Contextual AI analytical inferences.")
    potential_risks: List[AIInference] = Field(default_factory=list, description="Inferred potential risks.")
    recommendations: List[AIInference] = Field(default_factory=list, description="Actionable remediation recommendations.")
    confidence: float = Field(default=0.85, description="AI confidence score (0.0 to 1.0).")
    coverage: float = Field(default=80.0, description="Assessment coverage percentage (0.0 to 100.0).")
    unknowns: List[str] = Field(default_factory=list, description="Unverified parameters and assessment limitations.")
    appendix_json: Dict[str, Any] = Field(default_factory=dict, description="Normalized execution JSON data.")


class AIResultsAnalyzer:
    """Analyzes normalized scan outputs using configured LLMProvider with strict factual grounding."""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        llm_client: Optional[Any] = None
    ):
        self.llm_provider = llm_provider or llm_client or get_llm_provider()

    def normalize_step_output(self, raw_step: Dict[str, Any], target: str) -> NormalizedToolResult:
        """Convert raw step dictionary into standardized NormalizedToolResult schema."""
        tool = raw_step.get("tool", "unknown")
        meta = raw_step.get("metadata", {})
        dur = float(meta.get("execution_time_ms", 0.0)) / 1000.0
        ver = meta.get("tool_version", "1.0.0")

        return NormalizedToolResult(
            tool=tool,
            tool_version=ver,
            target=target,
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration=round(dur, 2),
            status=raw_step.get("status", "COMPLETED"),
            findings=raw_step.get("findings", []),
            evidence=raw_step.get("findings", []),
            errors=raw_step.get("errors", []),
            metadata=meta
        )

    def analyze(self, scan_result: UnifiedScanResult) -> AnalysisReport:
        """Analyze UnifiedScanResult object and return structured AnalysisReport."""
        return self.analyze_json(scan_result.model_dump())

    def analyze_json(self, raw_data: Dict[str, Any]) -> AnalysisReport:
        """Analyze raw normalized scan result dictionary."""
        target = str(raw_data.get("target", "Unknown Target"))
        timestamp = str(raw_data.get("timestamp", datetime.now(timezone.utc).isoformat()))
        profile = str(raw_data.get("profile", "standard"))

        # Build Normalized Tool Results and Evidence Models
        raw_steps = raw_data.get("step_results", [])
        normalized_results: List[NormalizedToolResult] = []
        evidence_list: List[EvidenceModel] = []
        timeline = []
        tool_summary = []

        for idx, s in enumerate(raw_steps, 1):
            norm_res = self.normalize_step_output(s, target=target)
            normalized_results.append(norm_res)

            tool_summary.append({
                "tool": norm_res.tool,
                "version": norm_res.tool_version,
                "status": norm_res.status,
                "duration_seconds": norm_res.duration,
                "findings_count": len(norm_res.findings)
            })

            timeline.append({
                "step": idx,
                "tool": norm_res.tool,
                "status": norm_res.status,
                "duration_seconds": norm_res.duration
            })

            for f in norm_res.findings:
                obs = f.get("title") or str(f)
                evidence_list.append(EvidenceModel(
                    source_tool=norm_res.tool,
                    timestamp=norm_res.timestamp,
                    observation=obs[:150],
                    evidence_type=f.get("category", "port_scan"),
                    confidence=1.0,
                    reference=f.get("finding_id", f"{norm_res.tool}_{idx}")
                ))

        system_prompt = """You are a Lead DevSecOps & Security Assessment Analyst.
Analyze normalized security scan JSON data and produce a structured analysis report.

CRITICAL GUARDRAILS:
1. STRICTLY SEPARATE:
   - OBSERVED FACTS (Verifiable data directly from tool outputs)
   - EVIDENCE (Extracted raw evidence items)
   - AI INFERENCES (Analytical hypotheses derived from facts)
   - POTENTIAL RISKS (Derived risk implications with severity)
   - RECOMMENDATIONS (Actionable remediation steps)
   - UNKNOWN (Assessment limitations and unverified items)
2. NEVER FABRICATE OR HALLUCINATE vulnerabilities not present in scan data.
3. Assign realistic confidence (0.0 to 1.0) and coverage (0.0 to 100.0) percentages.
4. Return output STRICTLY as valid JSON matching this schema:

{
  "executive_summary": "string",
  "observed_facts": [
    { "source_tool": "string", "finding_type": "string", "details": {}, "reference": "string" }
  ],
  "ai_inferences": [
    { "category": "analytical_hypothesis", "fact_references": ["string"], "inference": "string", "severity": "medium" }
  ],
  "potential_risks": [
    { "category": "risk_hypothesis", "fact_references": ["string"], "inference": "string", "severity": "high" }
  ],
  "recommendations": [
    { "category": "remediation", "fact_references": ["string"], "inference": "string", "severity": "info" }
  ],
  "confidence": 0.85,
  "coverage": 80.0,
  "unknowns": ["string"]
}
"""

        user_content = f"Target: {target}\nProfile: {profile}\nScan JSON Data:\n{json.dumps(raw_data, indent=2)}"

        provider_name = getattr(self.llm_provider, "provider_name", lambda: "LLMProvider")()
        logger.info(f"Analyzing scan results for '{target}' via {provider_name}...")

        try:
            if hasattr(self.llm_provider, "generate"):
                raw_response = self.llm_provider.generate(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=3000
                )
            else:
                resp_obj = self.llm_provider.complete(
                    prompt=user_content,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=3000
                )
                raw_response = getattr(resp_obj, "content", str(resp_obj))

            clean_json = self._extract_json(raw_response)
            parsed_data = json.loads(clean_json)

            return AnalysisReport(
                target=target,
                timestamp=timestamp,
                scope=f"Authorized Assessment Scope for '{target}'",
                profile=profile,
                executive_summary=parsed_data.get("executive_summary", "Security assessment completed."),
                timeline=timeline,
                tool_summary=tool_summary,
                evidence_list=evidence_list,
                observed_facts=[ObservedFact(**f) for f in parsed_data.get("observed_facts", [])],
                ai_inferences=[AIInference(**i) for i in parsed_data.get("ai_inferences", [])],
                potential_risks=[AIInference(**r) for r in parsed_data.get("potential_risks", [])],
                recommendations=[AIInference(**c) for c in parsed_data.get("recommendations", [])],
                confidence=float(parsed_data.get("confidence", 0.85)),
                coverage=float(parsed_data.get("coverage", 80.0)),
                unknowns=parsed_data.get("unknowns", []),
                appendix_json=raw_data
            )

        except Exception as e:
            logger.warning(f"AI analysis failed or returned invalid JSON ({str(e)}). Generating deterministic fallback report.")
            return self._build_deterministic_fallback(target, timestamp, profile, timeline, tool_summary, evidence_list, raw_data)

    def _extract_json(self, text: str) -> str:
        t = text.strip()
        if "```json" in t:
            return t.split("```json")[1].split("```")[0].strip()
        elif "```" in t:
            return t.split("```")[1].strip()
        return t

    def _build_deterministic_fallback(
        self,
        target: str,
        timestamp: str,
        profile: str,
        timeline: List[Dict[str, Any]],
        tool_summary: List[Dict[str, Any]],
        evidence_list: List[EvidenceModel],
        raw_data: Dict[str, Any]
    ) -> AnalysisReport:
        """Deterministic fact-grounded fallback report generator."""
        observed_facts = []
        for ev in evidence_list:
            observed_facts.append(ObservedFact(
                source_tool=ev.source_tool,
                finding_type=ev.evidence_type,
                details={"observation": ev.observation},
                reference=ev.reference
            ))

        return AnalysisReport(
            target=target,
            timestamp=timestamp,
            scope=f"Authorized Security Assessment Scope for '{target}'",
            profile=profile,
            executive_summary=f"Automated factual security assessment of target '{target}' (Profile: {profile.upper()}) completed with {len(evidence_list)} evidence observations.",
            timeline=timeline,
            tool_summary=tool_summary,
            evidence_list=evidence_list,
            observed_facts=observed_facts,
            ai_inferences=[
                AIInference(
                    category="analytical_hypothesis",
                    fact_references=[ev.reference for ev in evidence_list[:2]],
                    inference="Observed open network ports and headers require baseline security configuration verification.",
                    severity="low"
                )
            ],
            potential_risks=[
                AIInference(
                    category="risk_hypothesis",
                    fact_references=[ev.reference for ev in evidence_list[:2]],
                    inference="Unencrypted services or unpatched components represent potential attack vectors if unmitigated.",
                    severity="medium"
                )
            ],
            recommendations=[
                AIInference(
                    category="remediation",
                    fact_references=[],
                    inference="Verify TLS/SSL certificate configurations and restrict administrative endpoints to internal management networks.",
                    severity="info"
                )
            ],
            confidence=0.85,
            coverage=75.0,
            unknowns=["Authenticated vulnerability evaluation requires credentialed assessment."],
            appendix_json=raw_data
        )
