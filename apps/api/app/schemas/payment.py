from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RecoveryPermit(BaseModel):
    case_id: UUID
    original_payment_id: str
    order_id: str
    amount_paise: int
    idempotency_key: str
    expires_at: datetime
    environment: Literal["test"]


class EvidenceSource(str, Enum):
    CUSTOMER_REPORT = "customer_report"
    SYNTHETIC_SCREENSHOT = "synthetic_screenshot"
    MERCHANT_ORDER = "merchant_order"
    GATEWAY_EVENT = "gateway_event"
    POLICY = "policy"


class PaymentState(str, Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    CAPTURED_UNLINKED = "CAPTURED_UNLINKED"
    DUPLICATE_SUCCESS = "DUPLICATE_SUCCESS"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    WRONG_RECIPIENT = "WRONG_RECIPIENT"
    UNAUTHORIZED = "UNAUTHORIZED"


class RecoveryAction(str, Enum):
    DO_NOT_RETRY = "DO_NOT_RETRY"
    RECONCILE_ORDER = "RECONCILE_ORDER"
    CREATE_RECOVERY_PERMIT = "CREATE_RECOVERY_PERMIT"
    OPEN_DUPLICATE_REVIEW = "OPEN_DUPLICATE_REVIEW"
    BUILD_EVIDENCE_PACKET = "BUILD_EVIDENCE_PACKET"
    OFFICIAL_ROUTE_GUIDANCE = "OFFICIAL_ROUTE_GUIDANCE"
    SECURITY_ESCALATION = "SECURITY_ESCALATION"


class MerchantOrderSchema(BaseModel):
    order_id: str
    reference: str
    amount_paise: int = Field(ge=1)
    status: str
    created_at: datetime


class GatewayPaymentEvent(BaseModel):
    provider: Literal["razorpay_test", "synthetic"]
    provider_payment_id: str
    provider_order_id: str | None = None
    amount_paise: int = Field(ge=1)
    status: Literal["created", "authorized", "captured", "failed", "pending"]
    occurred_at: datetime
    raw_event_id: str | None = None
    source: Literal["gateway_event"] = "gateway_event"


class CustomerReport(BaseModel):
    message: str
    amount_paise: int | None = Field(default=None, ge=1)
    reported_status: Literal["success", "failed", "pending", "unknown"]
    utr_like_reference: str | None = Field(default=None, max_length=64)
    occurred_at: datetime | None = None
    source: Literal["customer_report"] = "customer_report"


class RecoveryDecision(BaseModel):
    state: PaymentState
    action: RecoveryAction
    reason_codes: list[str]
    authoritative_evidence_ids: list[str]
    customer_message: str
    policy_version: str = "v0.1.0"


class SyntheticIncident(BaseModel):
    incident_id: str
    split: Literal["dev", "heldout"]
    scenario: str
    description: str
    merchant_order: MerchantOrderSchema
    gateway_events: list[GatewayPaymentEvent] = Field(default_factory=list)
    customer_report: CustomerReport | None = None
    expected_state: PaymentState
    expected_action: RecoveryAction
    simulated_gmv_paise: int = 0
    notes: str = ""
