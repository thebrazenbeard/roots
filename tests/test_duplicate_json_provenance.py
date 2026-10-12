"""Ambiguous JSON object members cannot become trusted provenance records."""
import json

import pytest

from roots.adapters.json_records import JsonRecordsAdapter, DuplicateJsonKeyError
from roots.model import TargetKind, TargetSpec


TARGET = TargetSpec(
    target_id="test", kind=TargetKind.PHRASE,
    query_original="blue lantern", literal_forms=("blue lantern",)
)


@pytest.mark.parametrize("suffix,body", [
    (".jsonl", '{"id":"first","id":"second","content":"blue lantern"}\n'),
    (".jsonl", '{"id":"first","content":"blue lantern","content":"other"}\n'),
    (".jsonl", '{"messages":[{"id":"m1","content":"blue lantern","content":"other"}]}\n'),
    (".json", '{"records":[{"id":"first","content":"blue lantern","id":"other"}]}'),
    (".json", '{"records":[],"records":[{"content":"blue lantern"}]}'),
])
def test_duplicate_object_members_reject_ambiguous_record(tmp_path,suffix,body):
    source=tmp_path/("source"+suffix)
    source.write_text(body,encoding="utf-8")
    with pytest.raises(DuplicateJsonKeyError, match="duplicate JSON object member"):
        list(JsonRecordsAdapter(source).discover(TARGET))


def test_valid_jsonl_records_still_retain_content_and_identity(tmp_path):
    source=tmp_path/"source.jsonl"
    source.write_text(
        '{"id":"first","content":"blue lantern"}\n'
        '{"id":"second","content":"blue lantern"}\n',
        encoding="utf-8",
    )
    rows=list(JsonRecordsAdapter(source).discover(TARGET))
    assert [row.source_record_id for row in rows]==["first","second"]


def test_nonambiguous_malformed_jsonl_line_preserves_existing_skip_behavior(tmp_path):
    source=tmp_path/"source.jsonl"
    source.write_text(
        '{"id":"bad", invalid-json}\n'
        '{"id":"good","content":"blue lantern"}\n',
        encoding="utf-8",
    )
    rows=list(JsonRecordsAdapter(source).discover(TARGET))
    assert [row.source_record_id for row in rows]==["good"]
