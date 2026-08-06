"""
Unit tests for safe command executor (core/executor.py).
"""

import sys
import pytest
import asyncio
from core.executor import SafeExecutor


def test_safe_executor_success(safe_executor):
    """Test successful command execution captures output and timing."""
    cmd = [sys.executable, "-c", "print('Hello DevSecOps')"]
    res = safe_executor.execute(cmd)

    assert res.is_success is True
    assert res.exit_code == 0
    assert "Hello DevSecOps" in res.stdout
    assert res.stderr == ""
    assert res.execution_time_ms > 0
    assert res.timed_out is False


def test_safe_executor_non_zero_exit(safe_executor):
    """Test command returning non-zero exit code."""
    cmd = [sys.executable, "-c", "import sys; sys.stderr.write('Error occurred'); sys.exit(42)"]
    res = safe_executor.execute(cmd)

    assert res.is_success is False
    assert res.exit_code == 42
    assert "Error occurred" in res.stderr
    assert res.timed_out is False


def test_safe_executor_timeout():
    """Test command exceeding hard timeout limit."""
    executor = SafeExecutor(default_timeout_seconds=0.5)
    cmd = [sys.executable, "-c", "import time; time.sleep(5)"]
    res = executor.execute(cmd, timeout_seconds=0.5)

    assert res.is_success is False
    assert res.timed_out is True
    assert res.exit_code == -9


def test_safe_executor_invalid_executable(safe_executor):
    """Test handling of non-existent binary."""
    cmd = ["non_existent_binary_xyz_12345"]
    res = safe_executor.execute(cmd)

    assert res.is_success is False
    assert res.exit_code == 127
    assert "Executable not found" in res.stderr


@pytest.mark.asyncio
async def test_async_executor_success(safe_executor):
    """Test asynchronous execution workflow."""
    cmd = [sys.executable, "-c", "print('Async Hello')"]
    res = await safe_executor.execute_async(cmd)

    assert res.is_success is True
    assert res.exit_code == 0
    assert "Async Hello" in res.stdout
    assert res.execution_time_ms > 0
