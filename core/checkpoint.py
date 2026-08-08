"""
Assessment Checkpointing and State Persistence Subsystem.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from plugins.base import StandardPluginOutput
from core.planner import ExecutionPlan, PlannedStep
from core.logger import get_logger

logger = get_logger("checkpoint_manager")


class AssessmentCheckpoint(BaseModel):
    """Pydantic model representing a serializable assessment execution state."""
    assessment_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique assessment execution identifier."
    )
    target: str = Field(..., description="Target evaluated.")
    profile: str = Field(default="standard", description="Assessment profile ('fast', 'standard', 'deep', 'custom').")
    total_steps: int = Field(..., description="Total number of steps in plan.")
    completed_step_numbers: List[int] = Field(default_factory=list, description="Step numbers completed.")
    pending_step_numbers: List[int] = Field(default_factory=list, description="Step numbers pending execution.")
    step_outputs: List[StandardPluginOutput] = Field(default_factory=list, description="Completed step plugin outputs.")
    plan_dict: Dict[str, Any] = Field(default_factory=dict, description="Serialized ExecutionPlan dictionary.")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Checkpoint creation timestamp."
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Last updated timestamp."
    )


class CheckpointManager:
    """Manages reading, writing, and resuming assessment execution state on disk."""

    def __init__(self, checkpoints_dir: str = "checkpoints"):
        self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    def _checkpoint_path(self, assessment_id: str) -> Path:
        return self.checkpoints_dir / f"checkpoint_{assessment_id}.json"

    def create_checkpoint(self, plan: ExecutionPlan, profile: str = "standard") -> AssessmentCheckpoint:
        """Create a new checkpoint instance from an ExecutionPlan."""
        all_steps = [s.step_number for s in plan.execution_order]
        cp = AssessmentCheckpoint(
            target=plan.target,
            profile=profile,
            total_steps=len(all_steps),
            completed_step_numbers=[],
            pending_step_numbers=all_steps,
            step_outputs=[],
            plan_dict=plan.model_dump()
        )
        self.save_checkpoint(cp)
        logger.info(f"Initialized assessment checkpoint '{cp.assessment_id}' for target '{plan.target}'.")
        return cp

    def save_checkpoint(self, checkpoint: AssessmentCheckpoint) -> None:
        """Save assessment checkpoint atomically to disk."""
        checkpoint.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._checkpoint_path(checkpoint.assessment_id)
        try:
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(checkpoint.model_dump_json(indent=2))
            temp_path.replace(path)
            logger.debug(f"Saved checkpoint state '{checkpoint.assessment_id}' ({len(checkpoint.completed_step_numbers)}/{checkpoint.total_steps} steps completed).")
        except Exception as e:
            logger.error(f"Failed to save checkpoint '{checkpoint.assessment_id}': {str(e)}")

    def load_checkpoint(self, assessment_id: str) -> Optional[AssessmentCheckpoint]:
        """Load an assessment checkpoint by ID."""
        path = self._checkpoint_path(assessment_id)
        if not path.is_file():
            logger.warning(f"Checkpoint file '{path}' not found.")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AssessmentCheckpoint.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to parse checkpoint '{assessment_id}': {str(e)}")
            return None

    def find_latest_checkpoint_for_target(self, target: str) -> Optional[AssessmentCheckpoint]:
        """Find most recent checkpoint for a specific target."""
        clean_t = target.strip().lower()
        latest_cp = None
        latest_time = ""

        for file_path in self.checkpoints_dir.glob("checkpoint_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cp = AssessmentCheckpoint.model_validate_json(f.read())
                if cp.target.strip().lower() == clean_t:
                    if cp.updated_at > latest_time:
                        latest_time = cp.updated_at
                        latest_cp = cp
            except Exception:
                continue

        return latest_cp

    def delete_checkpoint(self, assessment_id: str) -> None:
        """Remove a completed checkpoint file."""
        path = self._checkpoint_path(assessment_id)
        if path.is_file():
            path.unlink()
            logger.debug(f"Deleted completed checkpoint '{assessment_id}'.")
