"""Case API routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import PaymentCase
from app.services.case_service import (
    CaseNotFoundError,
    classify_case,
    create_case,
    get_case,
    list_cases,
)

router = APIRouter(prefix="/v1/cases", tags=["cases"])


class CreateCaseRequest(BaseModel):
    order_id: str
    incident_id: str | None = None


class EvidenceItem(BaseModel):
    id: str
    source_type: str
    event_reference: str | None
    amount_paise: int | None
    status: str | None
    occurred_at: str | None


class AuditEventOut(BaseModel):
    id: str
    event_type: str
    actor: str
    prior_state: str | None
    new_state: str | None
    action: str | None
    reason_codes: list[str] | None
    customer_message: str | None
    occurred_at: str


class CaseOut(BaseModel):
    id: str
    order_id: str
    state: str
    payment_state: str | None
    action: str | None
    customer_message: str | None
    incident_id: str | None
    created_at: str
    evidence: list[EvidenceItem] = []
    audit_trail: list[AuditEventOut] = []

    @classmethod
    def from_orm(cls, case: PaymentCase) -> "CaseOut":
        return cls(
            id=case.id,
            order_id=case.order_id,
            state=case.state,
            payment_state=case.payment_state,
            action=case.action,
            customer_message=case.customer_message,
            incident_id=case.incident_id,
            created_at=case.created_at.isoformat(),
            evidence=[
                EvidenceItem(
                    id=ev.id,
                    source_type=ev.source_type,
                    event_reference=ev.event_reference,
                    amount_paise=ev.amount_paise,
                    status=ev.status,
                    occurred_at=ev.occurred_at.isoformat() if ev.occurred_at else None,
                )
                for ev in (case.evidence_items or [])
            ],
            audit_trail=[
                AuditEventOut(
                    id=ae.id,
                    event_type=ae.event_type,
                    actor=ae.actor,
                    prior_state=ae.prior_state,
                    new_state=ae.new_state,
                    action=ae.action,
                    reason_codes=ae.reason_codes,
                    customer_message=ae.customer_message,
                    occurred_at=ae.occurred_at.isoformat(),
                )
                for ae in (case.audit_events or [])
            ],
        )


@router.get("", response_model=list[CaseOut])
async def list_cases_route(db: AsyncSession = Depends(get_db)) -> list[CaseOut]:
    cases = await list_cases(db)
    return [CaseOut.from_orm(c) for c in cases]


@router.post("", response_model=CaseOut, status_code=201)
async def create_case_route(
    body: CreateCaseRequest,
    db: AsyncSession = Depends(get_db),
) -> CaseOut:
    try:
        case = await create_case(db, order_id=body.order_id, incident_id=body.incident_id)
        return CaseOut.from_orm(case)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{case_id}", response_model=CaseOut)
async def get_case_route(case_id: str, db: AsyncSession = Depends(get_db)) -> CaseOut:
    try:
        case = await get_case(db, case_id)
        return CaseOut.from_orm(case)
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{case_id}/classify", response_model=dict)
async def classify_case_route(
    case_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        decision = await classify_case(db, case_id)
        return {
            "state": decision.state.value,
            "action": decision.action.value,
            "reason_codes": decision.reason_codes,
            "customer_message": decision.customer_message,
            "policy_version": decision.policy_version,
        }
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


from app.services.reconcile_service import AmbiguousMatchError, ReconcileError, reconcile_order


@router.post("/{case_id}/reconcile")
async def reconcile_case_route(
    case_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        result = await reconcile_order(db, case_id)
        return result
    except AmbiguousMatchError as e:
        raise HTTPException(status_code=409, detail=f"Ambiguous match: {e}")
    except ReconcileError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


from pydantic import BaseModel as _BaseModel


class DuplicateReviewDecisionRequest(_BaseModel):
    decision: str  # "approve_refund_review" | "reject"
    notes: str = ""


from app.services.duplicate_review_service import (
    DuplicateReviewError,
    open_duplicate_review,
    record_review_decision,
)


@router.post("/{case_id}/duplicate-review")
async def open_duplicate_review_route(
    case_id: str, db: AsyncSession = Depends(get_db)
) -> dict:
    try:
        return await open_duplicate_review(db, case_id)
    except DuplicateReviewError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{case_id}/duplicate-review/approve")
async def record_duplicate_review_decision_route(
    case_id: str,
    body: DuplicateReviewDecisionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        return await record_review_decision(
            db, case_id, decision=body.decision, notes=body.notes
        )
    except DuplicateReviewError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
