from __future__ import annotations

import hashlib

from roots.adapters.base import RawCandidate
from roots.model import EvidenceEvent, EpistemicStatus, RetrievalMethod, TargetSpec
from roots.time import parse_time


class DuplicateAdapter:
    name = "synthetic"

    def discover(self, target: TargetSpec):
        candidate = RawCandidate(
            source_name=self.name,
            source_locator="records.jsonl:1",
            source_record_id="same-record",
            event_time="2026-01-01",
            content="silver compass appears here",
            retrieval_method=RetrievalMethod.EXACT,
        )
        yield candidate
        yield candidate

    def resolve_reference(self, ref):
        return ()

    def normalize(self, candidate: RawCandidate) -> EvidenceEvent:
        digest = hashlib.sha256(candidate.content.encode("utf-8")).hexdigest()
        return EvidenceEvent(
            record_id=candidate.source_record_id or digest[:16],
            source_surface=candidate.source_name,
            source_locator=candidate.source_locator,
            source_record_id=candidate.source_record_id,
            retrieval_method=candidate.retrieval_method,
            epistemic_status=EpistemicStatus.DIRECT_SOURCE,
            content=candidate.content,
            content_hash=digest,
            event_time=parse_time(candidate.event_time),
        )


def test_discovery_deduplicates_same_source_record():
    from roots.discovery import discover

    result = discover(TargetSpec.from_cli("silver compass"), [DuplicateAdapter()])

    assert [event.record_id for event in result.events] == ["same-record"]
    assert len(result.source_attempts) == 1
    assert result.source_attempts[0].source == "synthetic"
