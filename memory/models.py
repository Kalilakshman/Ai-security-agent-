"""
SQLAlchemy 2.x Declarative Data Models for Comprehensive Scan & Policy Persistence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Float, DateTime, JSON, Text, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.x declarative models."""
    pass


class ScanRecord(Base):
    """ORM Model representing a comprehensive security assessment execution record."""
    __tablename__ = "scan_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assessment_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    target: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    target_scope: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile: Mapped[str] = mapped_column(String(50), default="standard", nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(50), default="openrouter", nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), default="default", nullable=False)
    mcp_servers: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    plugins_used: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    tool_executions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    retries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)
    raw_results: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    generated_reports: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    policy_decisions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM record model instance to python dictionary."""
        return {
            "id": self.id,
            "assessment_id": self.assessment_id,
            "target": self.target,
            "profile": self.profile,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "mcp_servers": self.mcp_servers,
            "date": self.date.isoformat() if self.date else "",
            "plugins_used": self.plugins_used,
            "execution_time_ms": self.execution_time_ms,
            "retries_count": self.retries_count,
            "evidence_count": self.evidence_count,
            "findings_count": self.findings_count,
            "status": self.status,
            "generated_reports": self.generated_reports,
            "summary": self.summary,
        }
