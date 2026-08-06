"""
Safe command executor engine.

Uses subprocess safely WITHOUT shell=True to prevent command injection.
Captures stdout, stderr, exit code, timeout limits, and wall-clock execution time.
Implements IExecutor interface.
"""

import os
import sys
import time
import subprocess
import asyncio
from typing import List, Optional, Dict
from core.interfaces import IExecutor, ExecutionResult
from core.logger import get_logger

logger = get_logger("executor")


class SafeExecutor(IExecutor):
    """Subprocess execution engine designed for security assessment automation.
    
    Guarantees:
    - Never uses shell=True.
    - Captures stdout and stderr into separate streams.
    - Tracks execution duration in milliseconds using high-precision perf_counter.
    - Enforces hard execution timeout.
    - Provides environment sanitization.
    """

    def __init__(self, default_timeout_seconds: float = 60.0, safelist_env_vars: Optional[List[str]] = None):
        self.default_timeout = default_timeout_seconds
        self.safelist_env_vars = safelist_env_vars or ["PATH", "SYSTEMROOT", "TEMP", "TMP", "HOME", "USER", "LANG"]

    def _prepare_environment(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Construct sanitized environment variables dictionary."""
        sanitized_env: Dict[str, str] = {}
        for key in self.safelist_env_vars:
            val = os.getenv(key)
            if val is not None:
                sanitized_env[key] = val

        if custom_env:
            for k, v in custom_env.items():
                sanitized_env[k] = str(v)

        return sanitized_env

    def execute(
        self,
        command: List[str],
        timeout_seconds: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute a process synchronously and capture execution metrics.

        Args:
            command: Argument list [executable, arg1, arg2, ...]
            timeout_seconds: Timeout threshold in seconds.
            cwd: Optional current working directory.
            env: Optional additional environment variables.

        Returns:
            ExecutionResult containing execution metrics and captured streams.
        """
        if not command:
            raise ValueError("Command list cannot be empty.")

        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout
        exec_env = self._prepare_environment(env)

        logger.debug(f"Executing command: {command} (timeout={timeout}s, cwd={cwd})")

        start_time = time.perf_counter()
        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = -1

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=exec_env,
                shell=False  # Security Requirement: Prevent shell injection
            )

            stdout_data, stderr_data = process.communicate(timeout=timeout)
            stdout_str = stdout_data or ""
            stderr_str = stderr_data or ""
            exit_code = process.returncode

        except subprocess.TimeoutExpired:
            timed_out = True
            logger.warning(f"Command timed out after {timeout} seconds: {command}")
            process.kill()
            stdout_data, stderr_data = process.communicate()
            stdout_str = stdout_data or ""
            stderr_str = stderr_data or ""
            exit_code = -9

        except FileNotFoundError as e:
            logger.error(f"Executable not found for command {command[0]}: {str(e)}")
            stderr_str = f"Executable not found: {command[0]}"
            exit_code = 127

        except Exception as e:
            logger.exception(f"Unexpected error executing command {command}: {str(e)}")
            stderr_str = f"Execution error: {str(e)}"
            exit_code = 1

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        return ExecutionResult(
            command=command,
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=exit_code,
            execution_time_ms=round(duration_ms, 2),
            timed_out=timed_out,
            environment=exec_env
        )

    async def execute_async(
        self,
        command: List[str],
        timeout_seconds: Optional[float] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute a process asynchronously using asyncio subprocess streams."""
        if not command:
            raise ValueError("Command list cannot be empty.")

        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout
        exec_env = self._prepare_environment(env)

        logger.debug(f"Executing async command: {command} (timeout={timeout}s)")

        start_time = time.perf_counter()
        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = -1

        try:
            proc = await asyncio.create_subprocess_exec(
                command[0],
                *command[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=exec_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                stdout_str = stdout_bytes.decode(errors="replace")
                stderr_str = stderr_bytes.decode(errors="replace")
                exit_code = proc.returncode or 0

            except asyncio.TimeoutError:
                timed_out = True
                logger.warning(f"Async command timed out after {timeout} seconds: {command}")
                proc.kill()
                stdout_bytes, stderr_bytes = await proc.communicate()
                stdout_str = stdout_bytes.decode(errors="replace")
                stderr_str = stderr_bytes.decode(errors="replace")
                exit_code = -9

        except FileNotFoundError:
            logger.error(f"Executable not found: {command[0]}")
            stderr_str = f"Executable not found: {command[0]}"
            exit_code = 127

        except Exception as e:
            logger.exception(f"Unexpected async execution error: {str(e)}")
            stderr_str = f"Async execution error: {str(e)}"
            exit_code = 1

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        return ExecutionResult(
            command=command,
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=exit_code,
            execution_time_ms=round(duration_ms, 2),
            timed_out=timed_out,
            environment=exec_env
        )
