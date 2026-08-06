"""
Database session management and persistence layer using SQLAlchemy 2.x and SQLite.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from memory.models import Base, ScanRecord
from core.logger import get_logger

logger = get_logger("database")


class DatabaseEngine:
    """SQLAlchemy 2.x SQLite database engine for persisting security scan records."""

    def __init__(self, db_url: str = "sqlite:///security_orchestrator.db", echo: bool = False):
        self.db_url = db_url

        # Ensure directory exists if SQLite file path is specified
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(self.db_url, echo=echo, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()

    def init_db(self) -> None:
        """Initialize database schema tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.debug("Database schema tables initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {str(e)}")

    def save_scan(
        self,
        target: str,
        plugins_used: List[str],
        execution_time_ms: float,
        status: str,
        raw_results: Dict[str, Any],
        generated_reports: Optional[List[str]] = None,
        summary: Optional[Dict[str, Any]] = None,
    ) -> Optional[ScanRecord]:
        """Save a new scan record into the database with graceful error handling."""
        session: Session = self.SessionLocal()
        try:
            record = ScanRecord(
                target=target,
                plugins_used=plugins_used,
                execution_time_ms=execution_time_ms,
                status=status,
                raw_results=raw_results,
                generated_reports=generated_reports or [],
                summary=summary or {},
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(f"Saved scan record #{record.id} for target '{target}' to database.")
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Database error saving scan record for '{target}': {str(e)}")
            return None
        finally:
            session.close()

    def get_recent_scans(self, limit: int = 10) -> List[ScanRecord]:
        """Retrieve recent scan records ordered by date descending."""
        session: Session = self.SessionLocal()
        try:
            stmt = select(ScanRecord).order_by(ScanRecord.id.desc()).limit(limit)
            results = session.scalars(stmt).all()
            return list(results)
        except Exception as e:
            logger.error(f"Database error querying recent scans: {str(e)}")
            return []
        finally:
            session.close()


# Singleton engine instance
_db_instance: Optional[DatabaseEngine] = None


def get_db_engine(db_url: Optional[str] = None) -> DatabaseEngine:
    """Retrieve global DatabaseEngine singleton instance."""
    global _db_instance
    if _db_instance is None or db_url:
        url = db_url or "sqlite:///security_orchestrator.db"
        _db_instance = DatabaseEngine(db_url=url)
    return _db_instance
