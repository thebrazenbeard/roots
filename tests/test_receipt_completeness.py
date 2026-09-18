from datetime import datetime, timezone

from roots.model import (
    CheckResult,
    Completeness,
    EpistemicStatus,
    EvidenceEvent,
    Gap,
    OriginStatus,
    ProvenanceReceipt,
    RetrievalMethod,
    SourceAttempt,
    TargetKind,
    TargetSpec,
    TemporalPrecision,
    TimeBounds,
    UnresolvedReference,
)
from roots.verification import validate_receipt_claims


NOW = datetime(2026, 9, 18, tzinfo=timezone.utc)


def _event(record_id: str = "r1") -> EvidenceEvent:
    return EvidenceEvent(
        record_id=record_id,
        source_surface="chat",
        source_locator="chat:1",
        retrieval_method=RetrievalMethod.EXACT,
        epistemic_status=EpistemicStatus.DIRECT_SOURCE,
        content="target phrase",
        event_time=TimeBounds(NOW, NOW, TemporalPrecision.EXACT),
    )


def _receipt(**overrides) -> ProvenanceReceipt:
    target = TargetSpec(
        target_id="t1",
        kind=TargetKind.PHRASE,
        query_original="target phrase",
        literal_forms=("target phrase",),
        source_surfaces=("chat", "git"),
    )
    values = dict(
        schema_version=1,
        trace_id="trace-1",
        target=target,
        started_at=NOW,
        completed_at=NOW,
        source_attempts=(
            SourceAttempt(source="chat", status="SEARCHED"),
            SourceAttempt(source="git", status="SEARCHED"),
        ),
        completeness=Completeness.COMPLETE_RELATIVE_TO_ACCESSIBLE_SOURCES,
        earliest_accessible_evidence=("r1",),
        first_literal_occurrence=("r1",),
        conceptual_ancestors=(),
        current_meaning=("r1",),
        origin_status=OriginStatus.EARLIEST_ACCESSIBLE_ONLY,
        events=(_event(),),
        assessments=(),
        edges=(),
        conflicts=(),
        gaps=(),
        unresolved_references=(),
        verification=(CheckResult(code="fixture", passed=True, detail="ok"),),
        limitations=(),
    )
    values.update(overrides)
    return ProvenanceReceipt(**values)


def _checks(receipt: ProvenanceReceipt) -> dict[str, bool]:
    return {check.code: check.passed for check in validate_receipt_claims(receipt)}


def test_complete_receipt_requires_attempt_coverage_for_requested_sources():
    receipt = _receipt(
        source_attempts=(SourceAttempt(source="chat", status="SEARCHED"),)
    )
    checks = _checks(receipt)
    assert checks["complete.source_scope_covered"] is False


def test_complete_receipt_rejects_unresolved_back_reference():
    receipt = _receipt(
        unresolved_references=(
            UnresolvedReference(
                reference_id="u1",
                source_record_id="r1",
                target="earlier source",
            ),
        )
    )
    checks = _checks(receipt)
    assert checks["complete.unresolved_references_clear"] is False


def test_complete_receipt_rejects_unresolved_gap():
    receipt = _receipt(
        gaps=(Gap(gap_id="g1", description="missing derivation evidence"),)
    )
    checks = _checks(receipt)
    assert checks["complete.gaps_clear"] is False


def test_complete_receipt_requires_evidence_and_earliest_candidate():
    receipt = _receipt(events=(), earliest_accessible_evidence=())
    checks = _checks(receipt)
    assert checks["complete.evidence_present"] is False
    assert checks["complete.earliest_evidence_bound"] is False


def test_complete_receipt_requires_executed_passing_verification_checks():
    no_checks = _checks(_receipt(verification=()))
    failed = _checks(
        _receipt(
            verification=(
                CheckResult(code="chronology", passed=False, detail="bad order"),
            )
        )
    )
    assert no_checks["complete.verification_passed"] is False
    assert failed["complete.verification_passed"] is False


def test_valid_complete_receipt_passes_claim_checks():
    assert all(_checks(_receipt()).values())


def test_partial_receipt_does_not_get_strengthened_into_complete_requirements():
    receipt = _receipt(
        completeness=Completeness.PARTIAL,
        source_attempts=(),
        events=(),
        earliest_accessible_evidence=(),
        gaps=(Gap(gap_id="g1", description="known gap"),),
        unresolved_references=(
            UnresolvedReference(
                reference_id="u1",
                source_record_id="r1",
                target="unavailable earlier source",
            ),
        ),
        verification=(),
    )
    checks = _checks(receipt)
    assert checks == {"receipt.claim_strength": True}
