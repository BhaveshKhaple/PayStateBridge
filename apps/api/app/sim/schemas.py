"""Simulator event and world-state schemas for PayState World."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SimEventType(str, Enum):
    # Customer phone events
    CUSTOMER_INITIATED = "customer_initiated"       # customer taps Pay
    CUSTOMER_DEBITED = "customer_debited"           # bank SMS: debited
    CUSTOMER_PAY_AGAIN = "customer_pay_again"       # customer taps Pay again
    # Rails events (the packet moving)
    PACKET_AT_BANK = "packet_at_bank"
    PACKET_AT_SWITCH = "packet_at_switch"
    PACKET_AT_PSP = "packet_at_psp"
    PACKET_AT_MERCHANT = "packet_at_merchant"
    PACKET_STUCK = "packet_stuck"
    PACKET_LOST = "packet_lost"
    # Gateway/merchant events (consumed by the real classifier)
    GATEWAY_EVENT = "gateway_event"                 # carries a GatewayPaymentEvent
    WEBHOOK_DELIVERED = "webhook_delivered"
    ORDER_CREATED = "order_created"
    # Agent decision events (emitted after classifier runs)
    AGENT_DECISION = "agent_decision"
    # Chaos
    CHAOS_INJECTED = "chaos_injected"


class NodeId(str, Enum):
    BANK = "customer_bank"
    SWITCH = "upi_switch"
    PSP = "razorpay"
    MERCHANT = "merchant"


class SimEvent(BaseModel):
    """One event on the world timeline."""
    seq: int
    t_offset_ms: int                 # ms from story start (deterministic)
    type: SimEventType
    node: NodeId | None = None       # for packet/rails events
    label: str                       # human-readable, mono
    payload: dict = Field(default_factory=dict)  # e.g. GatewayPaymentEvent dump
    pane: Literal["customer", "rails", "merchant", "all"] = "all"


class ChaosControl(str, Enum):
    WEBHOOK_DELAY = "webhook_delay"       # slider 0-120s
    LOSE_WEBHOOK = "lose_webhook"
    MASH_PAY_AGAIN = "mash_pay_again"
    BANK_TIMEOUT = "bank_timeout"
    DOUBLE_CLICK_RACE = "double_click_race"


class SimStory(BaseModel):
    """A scripted, deterministic story."""
    story_id: str
    title: str
    subtitle: str
    seed: int
    expected_final_state: str        # PaymentState value
    expected_final_action: str       # RecoveryAction value
    events: list[SimEvent]
    narration: str = ""
