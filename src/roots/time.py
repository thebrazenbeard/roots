from __future__ import annotations

import calendar
import re
from datetime import datetime, time, timezone
from enum import StrEnum
from typing import Iterable

from .model import EvidenceEvent, TemporalPrecision, TimeBounds

UTC = timezone.utc


class TemporalRelation(StrEnum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    OVERLAPS_OR_INCOMPARABLE = "OVERLAPS_OR_INCOMPARABLE"
    UNKNOWN = "UNKNOWN"


def compare_time_bounds(left: TimeBounds, right: TimeBounds) -> TemporalRelation:
    if (
        left.start is None
        or left.end is None
        or right.start is None
        or right.end is None
    ):
        return TemporalRelation.UNKNOWN
    if left.end < right.start:
        return TemporalRelation.BEFORE
    if right.end < left.start:
        return TemporalRelation.AFTER
    return TemporalRelation.OVERLAPS_OR_INCOMPARABLE


def earliest_events(events: Iterable[EvidenceEvent]) -> tuple[EvidenceEvent, ...]:
    items = tuple(events)
    minima: list[EvidenceEvent] = []
    for candidate in items:
        has_known_predecessor = any(
            other.record_id != candidate.record_id
            and compare_time_bounds(other.event_time, candidate.event_time)
            is TemporalRelation.BEFORE
            for other in items
        )
        if not has_known_predecessor:
            minima.append(candidate)
    return tuple(sorted(minima, key=chronology_key))



def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_time(value: object) -> TimeBounds:
    if value is None or value == "":
        return TimeBounds(None, None, TemporalPrecision.UNKNOWN)
    if isinstance(value, datetime):
        dt = _aware(value)
        return TimeBounds(dt, dt, TemporalPrecision.EXACT)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value) / 1000.0 if abs(float(value)) >= 100_000_000_000 else float(value)
        dt = datetime.fromtimestamp(seconds, tz=UTC)
        return TimeBounds(dt, dt, TemporalPrecision.EXACT)
    if not isinstance(value, str):
        return TimeBounds(None, None, TemporalPrecision.UNKNOWN)

    raw = value.strip()
    if not raw:
        return TimeBounds(None, None, TemporalPrecision.UNKNOWN)

    if re.fullmatch(r"\d{4}", raw):
        year = int(raw)
        return TimeBounds(
            datetime(year, 1, 1, tzinfo=UTC),
            datetime(year, 12, 31, 23, 59, 59, 999999, tzinfo=UTC),
            TemporalPrecision.YEAR,
        )
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        year, month = map(int, raw.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return TimeBounds(
            datetime(year, month, 1, tzinfo=UTC),
            datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC),
            TemporalPrecision.MONTH,
        )
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        year, month, day = map(int, raw.split("-"))
        return TimeBounds(
            datetime(year, month, day, tzinfo=UTC),
            datetime.combine(datetime(year, month, day).date(), time.max, tzinfo=UTC),
            TemporalPrecision.DAY,
        )

    iso = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        dt = _aware(datetime.fromisoformat(iso))
    except ValueError:
        return TimeBounds(None, None, TemporalPrecision.UNKNOWN)
    return TimeBounds(dt, dt, TemporalPrecision.EXACT)


def chronology_key(event: EvidenceEvent) -> tuple[int, datetime, datetime, str]:
    bounds = event.event_time
    if bounds.start is None or bounds.end is None:
        sentinel = datetime.max.replace(tzinfo=UTC)
        return (1, sentinel, sentinel, event.record_id)
    return (0, bounds.start, bounds.end, event.record_id)


def order_events(events: Iterable[EvidenceEvent]) -> tuple[tuple[EvidenceEvent, ...], ...]:
    """Return display-oriented overlap groups, not a provenance total order.

    Use compare_time_bounds/earliest_events for inferential chronology.
    """
    known: list[EvidenceEvent] = []
    unknown: list[EvidenceEvent] = []
    for event in events:
        if event.event_time.start is None or event.event_time.end is None:
            unknown.append(event)
        else:
            known.append(event)

    known.sort(key=chronology_key)
    groups: list[tuple[EvidenceEvent, ...]] = []
    current: list[EvidenceEvent] = []
    current_end: datetime | None = None

    for event in known:
        start = event.event_time.start
        end = event.event_time.end
        assert start is not None and end is not None
        if not current:
            current = [event]
            current_end = end
            continue
        assert current_end is not None
        if start <= current_end:
            current.append(event)
            if end > current_end:
                current_end = end
        else:
            groups.append(tuple(current))
            current = [event]
            current_end = end

    if current:
        groups.append(tuple(current))
    if unknown:
        groups.append(tuple(sorted(unknown, key=lambda e: e.record_id)))
    return tuple(groups)
