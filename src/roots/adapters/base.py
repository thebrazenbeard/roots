from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol

from roots.model import EvidenceEvent, RetrievalMethod, TargetSpec


@dataclass(frozen=True, slots=True)
class Reference:
    target: str
    reference_id: str | None = None


@dataclass(frozen=True, slots=True)
class RawCandidate:
    source_name: str
    source_locator: str
    content: str
    source_record_id: str | None = None
    event_time: object = None
    author: str | None = None
    retrieval_method: RetrievalMethod = RetrievalMethod.EXACT
    metadata: dict[str, Any] = field(default_factory=dict)
    references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()


class SourceAdapter(Protocol):
    name: str

    def discover(self, target: TargetSpec) -> Iterable[RawCandidate]: ...

    def resolve_reference(self, ref: Reference) -> Iterable[RawCandidate]: ...

    def normalize(self, candidate: RawCandidate) -> EvidenceEvent: ...
