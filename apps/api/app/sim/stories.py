"""
The 3 Judge Mode stories (deterministic).
1. The Cab Driver — DUPLICATE_SUCCESS → refund review
2. The Lost Webhook — CAPTURED_UNLINKED → reconcile → GMV recovered
3. The Portal Timeout — OUTCOME_UNKNOWN → evidence packet
"""
from __future__ import annotations

from app.sim.schemas import NodeId, SimEvent, SimEventType, SimStory

_ORDER_1241 = {
    "order_id": "ORD-1241",
    "reference": "ORD-1241",
    "amount_paise": 49900,
    "status": "payment_pending",
    "created_at": "2026-08-30T08:00:00Z",
}


def _gw(payment_id: str, status: str, amount: int = 49900, t: str = "2026-08-30T08:00:05Z") -> dict:
    return {
        "provider": "synthetic",
        "provider_payment_id": payment_id,
        "provider_order_id": "ORD-1241",
        "amount_paise": amount,
        "status": status,
        "occurred_at": t,
        "raw_event_id": f"SYN-EVT-{payment_id}",
        "source": "gateway_event",
    }


# STORY 1 — The Lost Webhook (CAPTURED_UNLINKED → reconcile)
STORY_LOST_WEBHOOK = SimStory(
    story_id="lost_webhook",
    title="The ₹43,994 Miss",
    subtitle="Captured, but the webhook never arrived",
    seed=1241,
    expected_final_state="CAPTURED_UNLINKED",
    expected_final_action="RECONCILE_ORDER",
    narration="Payment captured at the PSP, but the webhook to the merchant was lost. The order stayed unpaid. The agent reconciles it at close — GMV recovered without a second charge.",
    events=[
        SimEvent(seq=1, t_offset_ms=0, type=SimEventType.ORDER_CREATED, label="Order ORD-1241 created · ₹499.00 UNPAID", payload=_ORDER_1241, pane="merchant"),
        SimEvent(seq=2, t_offset_ms=500, type=SimEventType.CUSTOMER_INITIATED, label="Customer taps Pay · ₹499.00", pane="customer"),
        SimEvent(seq=3, t_offset_ms=1200, type=SimEventType.PACKET_AT_BANK, node=NodeId.BANK, label="Debit request → Customer Bank", pane="rails"),
        SimEvent(seq=4, t_offset_ms=2000, type=SimEventType.CUSTOMER_DEBITED, label="BH-HDFCBK · ₹499.00 debited · Ref 3124", payload={"customer_report": {"message": "₹499 debited, no confirmation", "amount_paise": 49900, "reported_status": "success", "utr_like_reference": "SYN-UTR-3124", "occurred_at": "2026-08-30T08:00:02Z", "source": "customer_report"}}, pane="customer"),
        SimEvent(seq=5, t_offset_ms=2600, type=SimEventType.PACKET_AT_SWITCH, node=NodeId.SWITCH, label="Packet → UPI Switch", pane="rails"),
        SimEvent(seq=6, t_offset_ms=3400, type=SimEventType.PACKET_AT_PSP, node=NodeId.PSP, label="Packet → Razorpay · captured", payload=_gw("SYN-PAY-1241", "captured"), pane="rails"),
        SimEvent(seq=7, t_offset_ms=4000, type=SimEventType.GATEWAY_EVENT, label="Gateway event: captured (SYN-PAY-1241)", payload=_gw("SYN-PAY-1241", "captured"), pane="rails"),
        SimEvent(seq=8, t_offset_ms=4200, type=SimEventType.PACKET_LOST, node=NodeId.MERCHANT, label="Webhook to merchant LOST", pane="rails"),
        SimEvent(seq=9, t_offset_ms=5000, type=SimEventType.AGENT_DECISION, label="Agent: CAPTURED_UNLINKED → reconcile order", pane="merchant"),
    ],
)


# STORY 2 — The Cab Driver (DUPLICATE_SUCCESS → review)
STORY_CAB_DRIVER = SimStory(
    story_id="cab_driver",
    title="The Cab Driver",
    subtitle="Pending debit, then a second payment",
    seed=1242,
    expected_final_state="DUPLICATE_SUCCESS",
    expected_final_action="OPEN_DUPLICATE_REVIEW",
    narration="A pending debit leaves the driver unpaid. The customer pays a second time. Both captures land. The agent opens a merchant-approved refund review — it never silently refunds.",
    events=[
        SimEvent(seq=1, t_offset_ms=0, type=SimEventType.ORDER_CREATED, label="Order ORD-1241 created · ₹499.00 UNPAID", payload=_ORDER_1241, pane="merchant"),
        SimEvent(seq=2, t_offset_ms=500, type=SimEventType.CUSTOMER_INITIATED, label="Customer taps Pay · ₹499.00", pane="customer"),
        SimEvent(seq=3, t_offset_ms=1500, type=SimEventType.PACKET_AT_SWITCH, node=NodeId.SWITCH, label="Packet stuck at UPI Switch", pane="rails"),
        SimEvent(seq=4, t_offset_ms=2000, type=SimEventType.CUSTOMER_DEBITED, label="BH-HDFCBK · ₹499.00 debited · Ref 3125", payload={"customer_report": {"message": "debited but pending", "amount_paise": 49900, "reported_status": "success", "utr_like_reference": "SYN-UTR-3125", "occurred_at": "2026-08-30T08:00:02Z", "source": "customer_report"}}, pane="customer"),
        SimEvent(seq=5, t_offset_ms=3000, type=SimEventType.CUSTOMER_PAY_AGAIN, label="Customer taps Pay again · second attempt", pane="customer"),
        SimEvent(seq=6, t_offset_ms=4000, type=SimEventType.GATEWAY_EVENT, label="Gateway event: captured (SYN-PAY-A)", payload=_gw("SYN-PAY-A", "captured"), pane="rails"),
        SimEvent(seq=7, t_offset_ms=4600, type=SimEventType.GATEWAY_EVENT, label="Gateway event: captured (SYN-PAY-B)", payload=_gw("SYN-PAY-B", "captured"), pane="rails"),
        SimEvent(seq=8, t_offset_ms=5200, type=SimEventType.AGENT_DECISION, label="Agent: DUPLICATE_SUCCESS → open refund review", pane="merchant"),
    ],
)


# STORY 3 — The Portal Timeout (OUTCOME_UNKNOWN → evidence packet)
STORY_PORTAL_TIMEOUT = SimStory(
    story_id="portal_timeout",
    title="The Portal Timeout",
    subtitle="UTR exists, merchant page still spinning",
    seed=1243,
    expected_final_state="OUTCOME_UNKNOWN",
    expected_final_action="BUILD_EVIDENCE_PACKET",
    narration="The customer has a UTR, but the merchant portal is still spinning and gateway evidence conflicts. The agent refuses to guess — it builds an evidence packet and tells the customer not to pay again.",
    events=[
        SimEvent(seq=1, t_offset_ms=0, type=SimEventType.ORDER_CREATED, label="Order ORD-1241 created · ₹499.00 UNPAID", payload=_ORDER_1241, pane="merchant"),
        SimEvent(seq=2, t_offset_ms=500, type=SimEventType.CUSTOMER_INITIATED, label="Customer taps Pay · ₹499.00", pane="customer"),
        SimEvent(seq=3, t_offset_ms=1500, type=SimEventType.PACKET_AT_SWITCH, node=NodeId.SWITCH, label="Packet → UPI Switch", pane="rails"),
        SimEvent(seq=4, t_offset_ms=2000, type=SimEventType.CUSTOMER_DEBITED, label="BH-HDFCBK · ₹499.00 debited · Ref 3126", payload={"customer_report": {"message": "UTR shown but order spinning", "amount_paise": 49900, "reported_status": "success", "utr_like_reference": "SYN-UTR-3126", "occurred_at": "2026-08-30T08:00:02Z", "source": "customer_report"}}, pane="customer"),
        SimEvent(seq=5, t_offset_ms=3000, type=SimEventType.GATEWAY_EVENT, label="Gateway event: captured (SYN-PAY-X)", payload=_gw("SYN-PAY-X", "captured"), pane="rails"),
        SimEvent(seq=6, t_offset_ms=3600, type=SimEventType.GATEWAY_EVENT, label="Gateway event: failed (SYN-PAY-Y) — CONFLICT", payload=_gw("SYN-PAY-Y", "failed"), pane="rails"),
        SimEvent(seq=7, t_offset_ms=4200, type=SimEventType.PACKET_STUCK, node=NodeId.MERCHANT, label="Merchant portal still spinning", pane="rails"),
        SimEvent(seq=8, t_offset_ms=5000, type=SimEventType.AGENT_DECISION, label="Agent: OUTCOME_UNKNOWN → build evidence packet", pane="merchant"),
    ],
)


STORIES: dict[str, SimStory] = {
    STORY_LOST_WEBHOOK.story_id: STORY_LOST_WEBHOOK,
    STORY_CAB_DRIVER.story_id: STORY_CAB_DRIVER,
    STORY_PORTAL_TIMEOUT.story_id: STORY_PORTAL_TIMEOUT,
}


def get_story(story_id: str) -> SimStory | None:
    return STORIES.get(story_id)


def list_stories() -> list[dict]:
    return [
        {
            "story_id": s.story_id,
            "title": s.title,
            "subtitle": s.subtitle,
            "expected_final_state": s.expected_final_state,
            "expected_final_action": s.expected_final_action,
            "narration": s.narration,
            "event_count": len(s.events),
        }
        for s in STORIES.values()
    ]
