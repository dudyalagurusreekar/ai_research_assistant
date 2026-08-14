"""Benchmark Evaluation Runs and Quality Assurance Task Results ORM models."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class BenchmarkRun(BaseORMModel):
    """Historical benchmark run record (Sprint 14 Integration)."""

    __tablename__ = "benchmark_runs"

    version_tag = Column(String(50), nullable=False, index=True)
    mode = Column(String(50), default="fast", nullable=False)
    total_tasks = Column(Integer, nullable=False)
    passed_tasks = Column(Integer, nullable=False)
    failed_tasks = Column(Integer, nullable=False)
    pass_rate = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    release_approved = Column(Boolean, default=False, nullable=False, index=True)
    metrics_summary = Column(JSON, default=dict, nullable=False)

    task_results = relationship("BenchmarkTaskResult", back_populates="benchmark_run", cascade="all, delete-orphan")


class BenchmarkTaskResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual benchmark task execution result."""

    __tablename__ = "benchmark_task_results"

    benchmark_run_id = Column(String(36), ForeignKey("benchmark_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    score = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    error_details = Column(Text, nullable=True)

    benchmark_run = relationship("BenchmarkRun", back_populates="task_results")
