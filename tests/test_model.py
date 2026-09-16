from datetime import datetime, timezone
from roots.model import (
    EvidenceEvent,
    EpistemicStatus,
    RetrievalMethod,
    TargetKind,
    TargetSpec,
    TemporalPrecision,
    TimeBounds,
)


def test_target_preserves_literal_scope():
    target = TargetSpec(
        target_id="t1",
        kind=TargetKind.PHRASE,
        query_original="blue lantern",
        literal_forms=("blue lantern",),
    )
    assert target.query_original == "blue lantern"
    assert target.kind is TargetKind.PHRASE


def test_event_keeps_event_time_separate_from_ingestion_time():
    event = EvidenceEvent(
        record_id="r1",
        source_surface="fixture",
        source_locator="a.md:1",
        retrieval_method=RetrievalMethod.EXACT,
        epistemic_status=EpistemicStatus.DIRECT_SOURCE,
        content="blue lantern",
        event_time=TimeBounds(
            start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end=datetime(2026, 1, 1, tzinfo=timezone.utc),
            precision=TemporalPrecision.DAY,
        ),
        ingested_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    assert event.event_time.start.year == 2026
    assert event.ingested_at.month == 9
