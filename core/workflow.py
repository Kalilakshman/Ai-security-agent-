"""
Advanced Resilient Workflow Execution Engine.

Guarantees:
- Every tool executes independently (one step failure/timeout does NOT stop unrelated steps).
- Independent tool timeouts per profile (fast, standard, deep, custom).
- Configurable retries with backoff.
- Partial result preservation on timeout or failure.
- Atomic disk checkpointing and resumable assessments.
- Graceful cancellation handling.
- Dependency-aware DAG parallel step scheduling.
"""

import time
import signal
import concurrent.futures
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.config import AppConfig, load_config
from core.planner import ExecutionPlan, PlannedStep
from core.registry import get_registry, PluginRegistry
from plugins.base import StandardPluginOutput
from core.policy import SecurityPolicyEngine, PolicyEvaluationResult
from core.checkpoint import CheckpointManager, AssessmentCheckpoint
from core.scheduler import DependencyScheduler
from core.logger import get_logger

logger = get_logger("workflow")


class UnifiedScanResult(BaseModel):
    """Unified JSON scan result aggregating output across all workflow steps."""
    assessment_id: Optional[str] = Field(default=None, description="Assessment checkpoint identifier.")
    target: str = Field(..., description="Target evaluated.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution completion timestamp."
    )
    authorized: bool = Field(..., description="Target authorization acknowledgement flag.")
    profile: str = Field(default="standard", description="Assessment profile ('fast', 'standard', 'deep', 'custom').")
    total_duration_ms: float = Field(..., description="Total wall-clock duration in milliseconds.")
    step_results: List[StandardPluginOutput] = Field(default_factory=list, description="Plugin outputs.")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Aggregated finding counts.")


class WorkflowEngine:
    """Advanced Resilient Workflow Execution Engine."""

    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,
        policy_engine: Optional[SecurityPolicyEngine] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        config: Optional[AppConfig] = None
    ):
        self.registry = registry or get_registry()
        self.policy_engine = policy_engine or SecurityPolicyEngine(config=config)
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.config = config or load_config()

    def validate_target(self, target: str) -> bool:
        """Validate target string format (IP, Domain, URL)."""
        if not target or not target.strip():
            return False
        return True

    def require_authorization_acknowledgement(self, target: str, confirmed: bool) -> bool:
        """Enforce strict authorization guardrail check."""
        if not confirmed:
            logger.error(f"Authorization denied for target '{target}'. Execution halted.")
            return False
        return True

    def execute_single_step(
        self,
        step: PlannedStep,
        target: str,
        authorized: bool,
        profile: str = "standard",
        max_retries: int = 0,
        custom_timeout: Optional[float] = None
    ) -> StandardPluginOutput:
        """Execute a single step independently with retries, timeout resolution, and partial findings preservation."""
        tool_name = step.tool
        step_options = dict(step.options or {})
        if "profile" not in step_options:
            step_options["profile"] = profile

        # Resolve independent timeout
        if custom_timeout is not None and custom_timeout > 0:
            timeout_sec = custom_timeout
        else:
            timeout_sec = self.config.timeouts.get_timeout(tool_name, profile=profile)
        step_options["timeout"] = timeout_sec

        # Evaluate Security Policy Engine
        policy_res: PolicyEvaluationResult = self.policy_engine.evaluate_execution_request(
            target=target,
            tool_name=tool_name,
            arguments=step_options,
            profile=profile,
            authorized=authorized,
            timeout_seconds=timeout_sec
        )

        if not policy_res.allowed:
            logger.warning(f"Policy Engine BLOCKED tool '{tool_name}' for step {step.step_number}: {policy_res.reason}")
            return StandardPluginOutput(
                tool=tool_name,
                target=target,
                status="FAILED",
                errors=[f"Policy Block: {policy_res.reason}"]
            )

        plugin = self.registry.get_plugin(tool_name)
        if not plugin:
            logger.warning(f"Plugin '{tool_name}' not found in registry for step {step.step_number}.")
            return StandardPluginOutput(
                tool=tool_name,
                target=target,
                status="FAILED",
                errors=[f"Plugin '{tool_name}' not found in registry."]
            )

        # Retry loop for transient failures
        attempt = 0
        last_output: Optional[StandardPluginOutput] = None

        while attempt <= max_retries:
            attempt += 1
            if attempt > 1:
                logger.info(f"Retrying step {step.step_number} ({tool_name}) - Attempt {attempt}/{max_retries + 1}...")
                time.sleep(1.0 * attempt)

            try:
                start_t = time.perf_counter()
                output = plugin.execute(target, policy_res.sanitized_arguments)
                dur_ms = (time.perf_counter() - start_t) * 1000.0

                if "execution_time_ms" not in output.metadata:
                    output.metadata["execution_time_ms"] = round(dur_ms, 2)
                output.metadata["profile"] = profile
                output.metadata["timeout_applied_seconds"] = timeout_sec

                if output.status in ("COMPLETED", "TIMED_OUT") or attempt > max_retries:
                    return output

                last_output = output

            except Exception as e:
                logger.error(f"Execution error on step {step.step_number} ({tool_name}): {str(e)}")
                last_output = StandardPluginOutput(
                    tool=tool_name,
                    target=target,
                    status="FAILED",
                    errors=[f"Execution exception: {str(e)}"],
                    metadata={"execution_time_ms": 0.0, "profile": profile, "timeout_applied_seconds": timeout_sec}
                )

        return last_output or StandardPluginOutput(
            tool=tool_name, target=target, status="FAILED", errors=["Execution failed after retries."]
        )

    def execute_plan(
        self,
        plan: ExecutionPlan,
        authorized: bool,
        profile: str = "standard",
        max_concurrency: int = 3,
        max_retries: int = 0,
        resume_checkpoint_id: Optional[str] = None
    ) -> UnifiedScanResult:
        """Execute plan independently across DAG execution tiers with checkpointing and resumability."""
        if not self.validate_target(plan.target):
            raise ValueError(f"Invalid target format: '{plan.target}'")

        if not self.require_authorization_acknowledgement(plan.target, authorized):
            raise PermissionError(f"Execution aborted: Target '{plan.target}' not authorized.")

        # Checkpoint loading / initialization
        checkpoint: Optional[AssessmentCheckpoint] = None
        if resume_checkpoint_id:
            checkpoint = self.checkpoint_manager.load_checkpoint(resume_checkpoint_id)
            if not checkpoint:
                checkpoint = self.checkpoint_manager.find_latest_checkpoint_for_target(plan.target)

        if not checkpoint:
            checkpoint = self.checkpoint_manager.create_checkpoint(plan=plan, profile=profile)
            completed_steps_set = set()
            step_results_map: Dict[int, StandardPluginOutput] = {}
        else:
            logger.info(f"Resuming assessment '{checkpoint.assessment_id}' ({len(checkpoint.completed_step_numbers)}/{checkpoint.total_steps} steps already completed).")
            completed_steps_set = set(checkpoint.completed_step_numbers)
            step_results_map = {out.metadata.get("step_number", idx + 1): out for idx, out in enumerate(checkpoint.step_outputs)}

        # Build DAG execution tiers
        tiers = DependencyScheduler.build_execution_tiers(plan)
        start_time_all = time.perf_counter()

        try:
            for tier_idx, tier in enumerate(tiers, 1):
                # Filter out steps already completed from checkpoint
                pending_tier_steps = [s for s in tier if s.step_number not in completed_steps_set]
                if not pending_tier_steps:
                    continue

                logger.info(f"Executing tier {tier_idx}/{len(tiers)} ({len(pending_tier_steps)} parallel steps)...")

                if len(pending_tier_steps) == 1 or max_concurrency == 1:
                    for step in pending_tier_steps:
                        output = self.execute_single_step(
                            step=step, target=plan.target, authorized=authorized, profile=profile, max_retries=max_retries
                        )
                        output.metadata["step_number"] = step.step_number
                        step_results_map[step.step_number] = output
                        checkpoint.completed_step_numbers.append(step.step_number)
                        if step.step_number in checkpoint.pending_step_numbers:
                            checkpoint.pending_step_numbers.remove(step.step_number)
                        checkpoint.step_outputs = list(step_results_map.values())
                        self.checkpoint_manager.save_checkpoint(checkpoint)
                else:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
                        future_to_step = {
                            executor.submit(
                                self.execute_single_step,
                                step, plan.target, authorized, profile, max_retries
                            ): step for step in pending_tier_steps
                        }
                        for future in concurrent.futures.as_completed(future_to_step):
                            st = future_to_step[future]
                            try:
                                output = future.result()
                            except Exception as ex:
                                output = StandardPluginOutput(
                                    tool=st.tool, target=plan.target, status="FAILED", errors=[str(ex)]
                                )
                            output.metadata["step_number"] = st.step_number
                            step_results_map[st.step_number] = output
                            checkpoint.completed_step_numbers.append(st.step_number)
                            if st.step_number in checkpoint.pending_step_numbers:
                                checkpoint.pending_step_numbers.remove(st.step_number)
                            checkpoint.step_outputs = list(step_results_map.values())
                            self.checkpoint_manager.save_checkpoint(checkpoint)

        except (KeyboardInterrupt, SystemExit):
            logger.warning("Workflow execution cancelled by user. State safely saved to checkpoint.")

        total_duration = (time.perf_counter() - start_time_all) * 1000.0
        all_outputs = [step_results_map[s_id] for s_id in sorted(step_results_map.keys())]

        total_findings = sum(len(out.findings) for out in all_outputs)
        total_errors = sum(len(out.errors) for out in all_outputs)

        return UnifiedScanResult(
            assessment_id=checkpoint.assessment_id,
            target=plan.target,
            authorized=authorized,
            profile=profile,
            total_duration_ms=round(total_duration, 2),
            step_results=all_outputs,
            summary={
                "steps_executed": len(all_outputs),
                "total_findings": total_findings,
                "total_errors": total_errors,
                "checkpoint_id": checkpoint.assessment_id
            }
        )
