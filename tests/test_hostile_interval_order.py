from datetime import datetime, timezone

from roots.model import EvidenceEvent, EpistemicStatus, RetrievalMethod, TemporalPrecision, TimeBounds
from roots.time import TemporalRelation, compare_time_bounds, earliest_events


UTC = timezone.utc


def bounds(start_day: int, end_day: int) -> TimeBounds:
    return TimeBounds(
        datetime(2026, 1, start_day, tzinfo=UTC),
        datetime(2026, 1, end_day, tzinfo=UTC),
        TemporalPrecision.RANGE,
    )


def event(record_id: str, start_day: int, end_day: int) -> EvidenceEvent:
    return EvidenceEvent(
        record_id=record_id,
        source_surface="fixture",
        source_locator=f"fixture:{record_id}",
        retrieval_method=RetrievalMethod.MANUAL,
        epistemic_status=EpistemicStatus.DIRECT_SOURCE,
        content=record_id,
        event_time=bounds(start_day, end_day),
    )


def test_interval_order_preserves_known_nontransitive_relation():
    a = bounds(1, 3)
    b = bounds(2, 5)
    c = bounds(4, 6)

    assert compare_time_bounds(a, b) is TemporalRelation.OVERLAPS_OR_INCOMPARABLE
    assert compare_time_bounds(b, c) is TemporalRelation.OVERLAPS_OR_INCOMPARABLE
    assert compare_time_bounds(a, c) is TemporalRelation.BEFORE
    assert compare_time_bounds(c, a) is TemporalRelation.AFTER


def test_earliest_accessible_is_a_minimal_set_not_overlap_component():
    a = event("a", 1, 3)
    b = event("b", 2, 5)
    c = event("c", 4, 6)

    assert {item.record_id for item in earliest_events((a, b, c))} == {"a", "b"}

def test_earliest_set_preserves_unknown_time_as_incomparable_candidate():
    a = event("a", 1, 3)
    c = event("c", 4, 6)
    unknown = EvidenceEvent(
        record_id="unknown",
        source_surface="fixture",
        source_locator="fixture:unknown",
        retrieval_method=RetrievalMethod.MANUAL,
        epistemic_status=EpistemicStatus.DIRECT_SOURCE,
        content="unknown",
        event_time=TimeBounds(None, None, TemporalPrecision.UNKNOWN),
    )

    assert {item.record_id for item in earliest_events((a, c, unknown))} == {
        "a",
        "unknown",
    }

