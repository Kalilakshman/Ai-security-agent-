"""
Dependency-Aware DAG Scheduler for Parallel and Sequential Tool Step Execution.
"""

from typing import List, Dict, Set, Any
from core.planner import PlannedStep, ExecutionPlan
from core.logger import get_logger

logger = get_logger("scheduler")


class DependencyScheduler:
    """Schedules planned steps into concurrent execution tiers while respecting step dependencies.
    
    Guarantees:
    - Step dependencies (depends_on field) are strictly honored.
    - Independent steps in the same tier are executed concurrently.
    - Cycle detection prevents deadlocks.
    """

    @staticmethod
    def build_execution_tiers(plan: ExecutionPlan) -> List[List[PlannedStep]]:
        """Organize planned steps into ordered execution tiers (List of parallel step groups)."""
        steps = plan.execution_order
        if not steps:
            return []

        step_map: Dict[int, PlannedStep] = {s.step_number: s for s in steps}
        tool_to_step: Dict[str, int] = {s.tool.lower(): s.step_number for s in steps}

        # Build in-degree and adjacency map
        in_degree: Dict[int, int] = {s.step_number: 0 for s in steps}
        adj: Dict[int, List[int]] = {s.step_number: [] for s in steps}

        for step in steps:
            deps = getattr(step, "depends_on", []) or []
            for dep in deps:
                dep_step_id = None
                if isinstance(dep, int):
                    dep_step_id = dep
                elif isinstance(dep, str):
                    dep_step_id = tool_to_step.get(dep.lower())

                if dep_step_id and dep_step_id in step_map:
                    adj[dep_step_id].append(step.step_number)
                    in_degree[step.step_number] += 1

        # Kahn's algorithm for Tiered Topological Sort
        tiers: List[List[PlannedStep]] = []
        current_tier = [s_id for s_id, deg in in_degree.items() if deg == 0]

        visited_count = 0
        while current_tier:
            current_tier.sort()  # Deterministic ordering
            tier_steps = [step_map[s_id] for s_id in current_tier]
            tiers.append(tier_steps)
            visited_count += len(current_tier)

            next_tier: List[int] = []
            for s_id in current_tier:
                for neighbor in adj[s_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_tier.append(neighbor)
            current_tier = next_tier

        # Fallback if cyclic dependency detected
        if visited_count < len(steps):
            logger.warning("Cyclic dependency detected in execution plan. Falling back to sequential tiers.")
            return [[s] for s in steps]

        logger.debug(f"Built {len(tiers)} execution tiers across {len(steps)} planned steps.")
        return tiers
