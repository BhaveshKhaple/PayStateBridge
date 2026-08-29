# API, Data & Recovery Contracts — PayState Bridge

## 1. Core principle

**The LLM may extract an allegation. Only merchant/gateway evidence plus deterministic policy may decide a recovery action.**

A customer message such as “PhonePe shows success” is useful context. It is not authoritative proof that a merchant should issue a refund or mark an order paid.

## 2. Payment case state machine

```text
CASE_OPENED
  → EVIDENCE_COLLECTING
  → CLASSIFIED
       ├─ PENDING → WAITING_RECONCILIATION → CAPTURED_UNLINKED | FAILED | OUTCOME_UNKNOWN
       ├─ CAPTURED_UNLINKED → ORDER_RECONCILED
       ├─ FAILED → RECOVERY_PERMIT_ISSUED → RECOVERY_LINK_CREATED → RECOVERY_PAID_TEST
       ├─ DUPLICATE_SUCCESS → DUPLICATE_REVIEW_OPEN
       ├─ OUTCOME_UNKNOWN → EVIDENCE_PACKET_READY → HUMAN_ESCALATION
       ├─ WRONG_RECIPIENT → OFFICIAL_ROUTE_GUIDANCE
       └─ UNAUTHORIZED → HUMAN_SECURITY_ESCALATION
```

Terminal states: `ORDER_RECONCILED`, `RECOVERY_PAID_TEST`, `DUPLICATE_REVIEW_OPEN`, `HUMAN_ESCALATION`, `OFFICIAL_ROUTE_GUIDANCE`, `HUMAN_SECURITY_ESCALATION`, `CLOSED_NO_ACTION`.

## 3. State/action matrix

| State | May issue a new payment link? | Merchant action | Customer message principle |
|---|---|---|---|
| `PENDING` | **No** | Poll/reconcile after defined recheck window | “Please do not pay again while we verify.” |
| `OUTCOME_UNKNOWN` | **No** | Human review/evidence packet | “We cannot confirm the outcome yet; do not retry.” |
| `CAPTURED_UNLINKED` | **No** | Attach payment to order | “Your payment is confirmed; we are restoring your order.” |
| `FAILED` | **Yes, once** | Create recovery permit and one Test Mode link | “The first payment is verified failed; here is one fresh link.” |
| `DUPLICATE_SUCCESS` | **No** | Refund review | “We found two completed payments; our team is reviewing the duplicate.” |
| `WRONG_RECIPIENT` | **No** | Provide bank/NPCI evidence guidance | “A completed wrong transfer cannot be reversed automatically.” |
| `UNAUTHORIZED` | **No** | Security/human escalation | “We will not process normal recovery; use bank/security process.” |

## 4. Pydantic-style contracts

```python
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

class CustomerReport(BaseModel):
    message: str
    amount_paise: int | None = Field(default=None, ge=1)
    reported_status: Literal["success", "failed", "pending", "unknown"]
    utr_like_reference: str | None = Field(default=None, max_length=64)
    occurred_at: datetime | None
    source: Literal["customer_report"] = "customer_report"

class GatewayPaymentEvent(BaseModel):
    provider: Literal["razorpay_test", "synthetic"]
    provider_payment_id: str
    provider_order_id: str | None
    amount_paise: int = Field(ge=1)
    status: Literal["created", "authorized", "captured", "failed", "pending"]
    occurred_at: datetime
    raw_event_id: str | None
    source: Literal["gateway_event"] = "gateway_event"

class RecoveryDecision(BaseModel):
    state: PaymentState
    action: Literal[
        "DO_NOT_RETRY", "RECONCILE_ORDER", "CREATE_RECOVERY_PERMIT",
        "OPEN_DUPLICATE_REVIEW", "BUILD_EVIDENCE_PACKET",
        "OFFICIAL_ROUTE_GUIDANCE", "SECURITY_ESCALATION"
    ]
    reason_codes: list[str]
    authoritative_evidence_ids: list[str]
    customer_message: str
    policy_version: str

class RecoveryPermit(BaseModel):
    case_id: UUID
    original_payment_id: str
    order_id: str
    amount_paise: int
    idempotency_key: str
    expires_at: datetime
    environment: Literal["test"]
```

## 5. Deterministic policy rules

### Authoritative evidence order

1. verified merchant/gateway event;
2. merchant order state;
3. verified webhook/callback receipt;
4. customer report/screenshot;
5. model-extracted fields.

If sources conflict, choose `OUTCOME_UNKNOWN`, not a convenient answer.

### Create recovery permit only if all are true

```text
original payment final status == FAILED
AND merchant order is unpaid
AND no captured payment matches order/amount/reference
AND no active recovery action exists for same case
AND original case is not unauthorized/wrong-recipient
AND environment is Razorpay Test Mode
```

### Duplicate success detection rule

Open review only when two or more `captured` payment events map to the same intended merchant order / reference / amount window. A customer-reported duplicate alone is not enough.

### Captured-unlinked rule

A captured payment can be linked to an unpaid order only when order/reference/amount match under policy. If match is ambiguous, route to human review.

## 6. Minimal API

| Method / route | Purpose | Rules |
|---|---|---|
| `POST /v1/cases` | Create case from synthetic customer report/order context | No action occurs yet. |
| `POST /v1/cases/{id}/evidence` | Attach synthetic screenshot/text or merchant/gateway event | Source type is mandatory. |
| `POST /v1/cases/{id}/classify` | Run deterministic state/recovery decision | LLM output may be input only, never final state. |
| `GET /v1/cases/{id}` | Read case, evidence, decision, order/payment state | Redact secrets/raw sensitive data. |
| `POST /v1/cases/{id}/reconcile` | Attempt allowed captured-payment/order link | Requires exact deterministic match. |
| `POST /v1/cases/{id}/recovery-link` | Create one Razorpay Test Mode link | Requires current RecoveryPermit. |
| `POST /v1/cases/{id}/duplicate-review/approve` | Simulate merchant approval of refund review | No live refund API in v0. |
| `GET /v1/cases/{id}/evidence-packet` | Download redacted case timeline + official route guidance | Does not submit complaints. |
| `POST /v1/webhooks/razorpay` | Verify raw-body webhook and update case | HMAC then dedupe before parse/transition. |
| `POST /v1/evals/run` | Run local/admin synthetic evaluation suite | Never expose publicly without admin guard. |

## 7. Data entities

| Entity | Essential fields |
|---|---|
| `MerchantOrder` | ID, reference, expected amount paise, status, created/updated timestamps. |
| `PaymentCase` | ID, merchant order ID, state, action, policy version, original payment reference, created/updated. |
| `PaymentEvidence` | ID, case ID, source type, event/reference hash, amount paise, status, occurrence time, parsed JSON. |
| `GatewayPayment` | provider payment ID, order ID, amount paise, status, provider event time, linked case/order. |
| `RecoveryAction` | case ID, action kind, idempotency key, provider link ID, status, expiry. |
| `AuditEvent` | case ID, actor, prior/new status, reason code, evidence IDs, timestamp, hash of prior event optional. |
| `EvaluationCase` | split (`dev`/`heldout`), scenario, inputs, expected state/action, simulated GMV. |

Store money as integer paise. Use fake UTR-like values such as `SYN-UTR-20260830-001`; never store real UTRs in public fixtures.

## 8. Example audit event

```json
{
  "type": "RETRY_BLOCKED",
  "case_id": "case-9e2...",
  "prior_state": "EVIDENCE_COLLECTING",
  "new_state": "PENDING",
  "action": "DO_NOT_RETRY",
  "reason_codes": ["GATEWAY_STATUS_PENDING", "NO_FINAL_FAILURE_RECEIPT"],
  "evidence_ids": ["evt-synthetic-101", "order-1042"],
  "customer_message": "We are verifying your payment. Please do not pay again.",
  "occurred_at": "2026-08-30T08:30:00Z"
}
```

## 9. Provider adapter contract

```python
class PaymentProvider(Protocol):
    async def create_test_recovery_link(
        self, *, permit: RecoveryPermit
    ) -> ProviderAction: ...

    async def fetch_payment(self, payment_id: str) -> GatewayPaymentEvent: ...

    def verify_webhook(self, raw_body: bytes, signature: str) -> VerifiedWebhook: ...
```

`FakePaymentProvider` is mandatory for tests and demos without credentials. `RazorpayTestModeProvider` is optional until the deterministic recovery flow is correct.
