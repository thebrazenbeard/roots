"""Untrusted source chronology must not crash provenance reconstruction."""
import math

import pytest

from roots.model import TemporalPrecision
from roots.time import parse_time


@pytest.mark.parametrize(
    "source_value",
    [
        "0000",
        "2026-00",
        "2026-13",
        "2026-02-30",
        "2026-04-31",
        -10**30,
        10**30,
        float("nan"),
        float("inf"),
        -float("inf"),
    ],
)
def test_malformed_or_out_of_range_source_time_is_unknown(source_value):
    bounds = parse_time(source_value)
    assert bounds.precision is TemporalPrecision.UNKNOWN
    assert bounds.start is None
    assert bounds.end is None


@pytest.mark.parametrize(
    "source_value, expected_precision",
    [
        ("2026", TemporalPrecision.YEAR),
        ("2026-02", TemporalPrecision.MONTH),
        ("2024-02-29", TemporalPrecision.DAY),
        ("2026-10-10T09:00:00-04:00", TemporalPrecision.EXACT),
        (0, TemporalPrecision.EXACT),
    ],
)
def test_valid_source_time_precision_is_preserved(source_value, expected_precision):
    bounds = parse_time(source_value)
    assert bounds.precision is expected_precision
    assert bounds.start is not None
    assert bounds.end is not None
