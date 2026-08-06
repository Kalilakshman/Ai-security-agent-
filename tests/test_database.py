"""
Unit tests for SQLite Database Persistence and SQLAlchemy 2.x Models.
"""

import pytest
import tempfile
from pathlib import Path
from memory.database import DatabaseEngine
from memory.models import ScanRecord


@pytest.fixture
def temp_db_engine():
    """Create a temporary SQLite database engine for testing."""
    with tempfile.NamedTemporaryFile("w", suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db_url = f"sqlite:///{db_path}"
    engine = DatabaseEngine(db_url=db_url)
    yield engine

    try:
        db_path.unlink(missing_ok=True)
    except Exception:
        pass


def test_database_init_and_save_scan(temp_db_engine):
    """Test saving scan record to SQLite database."""
    record = temp_db_engine.save_scan(
        target="127.0.0.1",
        plugins_used=["nmap", "whatweb"],
        execution_time_ms=1500.5,
        status="COMPLETED",
        raw_results={"target": "127.0.0.1"},
        generated_reports=["report.md", "report.html"],
        summary={"total_findings": 3}
    )

    assert record is not None
    assert record.id == 1
    assert record.target == "127.0.0.1"
    assert record.plugins_used == ["nmap", "whatweb"]
    assert record.execution_time_ms == 1500.5


def test_database_get_recent_scans(temp_db_engine):
    """Test querying recent scan records from SQLite database."""
    temp_db_engine.save_scan(
        target="scanme.nmap.org",
        plugins_used=["nmap"],
        execution_time_ms=2000.0,
        status="COMPLETED",
        raw_results={"target": "scanme.nmap.org"}
    )
    temp_db_engine.save_scan(
        target="example.com",
        plugins_used=["whatweb"],
        execution_time_ms=800.0,
        status="COMPLETED",
        raw_results={"target": "example.com"}
    )

    scans = temp_db_engine.get_recent_scans(limit=10)

    assert len(scans) == 2
    assert scans[0].target == "example.com"  # Most recent first
    assert scans[1].target == "scanme.nmap.org"
