"""
SQLAlchemy 2.x Declarative Data Models for Scan Persistence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Float, DateTime, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.x declarative models."""
    pass


class ScanRecord(Base):
    """ORM Model representing a single security assessment scan execution record."""
    __tablename__ = "scan_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    plugins_used: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    raw_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    generated_reports: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM record model instance to python dictionary."""
        return {
            "id": self.id,
            "target": self.target,
            "date": self.date.isoformat() if self.date else "",
            "plugins_used": self.plugins_used,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "generated_reports": self.generated_reports,
            "summary": self.summary,
        }
