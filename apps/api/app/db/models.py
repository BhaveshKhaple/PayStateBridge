"""SQLAlchemy ORM models for PayState Bridge."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class MerchantOrder(Base):
    __tablename__ = "merchant_orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    reference: Mapped[str] = mapped_column(String, nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="payment_pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    cases: Mapped[list[PaymentCase]] = relationship("PaymentCase", back_populates="order")


class PaymentCase(Base):
    __tablename__ = "payment_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("merchant_orders.order_id"), nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, default="CASE_OPENED")
    payment_state: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str | None] = mapped_column(String, nullable=True)
    policy_version: Mapped[str] = mapped_column(String, nullable=False, default="v0.1.0")
    original_payment_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    order: Mapped[MerchantOrder] = relationship("MerchantOrder", back_populates="cases")
    evidence_items: Mapped[list[PaymentEvidence]] = relationship("PaymentEvidence", back_populates="case")
    recovery_actions: Mapped[list[RecoveryAction]] = relationship("RecoveryAction", back_populates="case")
    audit_events: Mapped[list[AuditEvent]] = relationship("AuditEvent", back_populates="case", order_by="AuditEvent.occurred_at")


class PaymentEvidence(Base):
    __tablename__ = "payment_evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("payment_cases.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # EvidenceSource enum value
    event_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped[PaymentCase] = relationship("PaymentCase", back_populates="evidence_items")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("payment_cases.id"), nullable=False)
    action_kind: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    provider_link_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped[PaymentCase] = relationship("PaymentCase", back_populates="recovery_actions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("payment_cases.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False, default="system")
    prior_state: Mapped[str | None] = mapped_column(String, nullable=True)
    new_state: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str | None] = mapped_column(String, nullable=True)
    reason_codes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    customer_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped[PaymentCase] = relationship("PaymentCase", back_populates="audit_events")
