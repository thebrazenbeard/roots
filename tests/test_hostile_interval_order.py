from datetime import datetime, timezone

from roots.model import TemporalPrecision, TimeBounds
from roots.time import TemporalRelation, compare_time_bounds


UTC = timezone.utc


def bounds(start_day: int, end_day: int) -> TimeBounds:
    return TimeBounds(
        datetime(2026, 1, start_day, tzinfo=UTC),
        datetime(2026, 1, end_day, tzinfo=UTC),
        TemporalPrecision.RANGE,
    )


def test_interval_order_preserves_known_nontransitive_relation():
    a = bounds(1, 3)
    b = bounds(2, 5)
    c = bounds(4, 6)

    assert compare_time_bounds(a, b) is TemporalRelation.OVERLAPS_OR_INCOMPARABLE
    assert compare_time_bounds(b, c) is TemporalRelation.OVERLAPS_OR_INCOMPARABLE
    assert compare_time_bounds(a, c) is TemporalRelation.BEFORE
    assert compare_time_bounds(c, a) is TemporalRelation.AFTER
