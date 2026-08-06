"""
Core package initialization.
"""

from core.interfaces import IExecutor, ILLMProvider, IPlugin, ExecutionResult
from core.config import load_config, AppConfig
from core.logger import setup_logger, get_logger
from core.executor import SafeExecutor
from core.llm import OpenRouterClient
from core.planner import AIPlanner, ExecutionPlan
from core.workflow import WorkflowEngine, UnifiedScanResult

__all__ = [
    "IExecutor",
    "ILLMProvider",
    "IPlugin",
    "ExecutionResult",
    "load_config",
    "AppConfig",
    "setup_logger",
    "get_logger",
    "SafeExecutor",
    "OpenRouterClient",
    "AIPlanner",
    "ExecutionPlan",
    "WorkflowEngine",
    "UnifiedScanResult",
]
