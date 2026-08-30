from app.domain.rules_kb import CITATIONS, cite_reason_codes


def test_pending_reason_codes_cited():
    cites = cite_reason_codes(["GATEWAY_STATUS_PENDING", "NO_FINAL_FAILURE_RECEIPT"])
    assert len(cites) == 2
    assert cites[0]["rule_id"] == "R-PENDING-01"


def test_unknown_reason_code_ignored():
    cites = cite_reason_codes(["NOT_A_REAL_CODE"])
    assert cites == []


def test_citations_dedup():
    cites = cite_reason_codes(["GATEWAY_STATUS_PENDING", "GATEWAY_STATUS_PENDING"])
    assert len(cites) == 1


def test_every_citation_has_source_kind():
    for c in CITATIONS.values():
        assert c.source_kind in ("razorpay", "npci", "paystate_policy")


def test_all_core_reason_codes_have_citations():
    required = [
        "GATEWAY_STATUS_PENDING", "GATEWAY_STATUS_FAILED", "CAPTURED_ORDER_NOT_LINKED",
        "MULTIPLE_CAPTURED_EVENTS", "CONFLICTING_GATEWAY_EVENTS", "NO_GATEWAY_EVENT",
        "WRONG_RECIPIENT_CLAIM", "UNAUTHORIZED_CLAIM",
    ]
    for code in required:
        assert code in CITATIONS, f"Missing citation for {code}"
