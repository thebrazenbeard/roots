from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from roots.model import EvidenceEvent, EpistemicStatus, RetrievalMethod, TargetSpec
from roots.normalize import literal_match
from roots.time import parse_time

from .base import RawCandidate, Reference

RECORD_ID_KEYS = ("record_id", "id", "message_id")
TIME_KEYS = ("event_time", "timestamp", "create_time_iso", "created_at")
AUTHOR_KEYS = ("author", "speaker", "role")
CONTENT_KEYS = ("content", "text")
REFERENCE_KEYS = ("references", "source_refs", "back_references")


def _first(record: dict[str, Any], keys: tuple[str, ...]):
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def _content(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts) if parts else None
    return None


def _references(record: dict[str, Any]) -> tuple[Reference, ...]:
    raw = _first(record, REFERENCE_KEYS)
    if raw is None:
        return ()
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return ()
    refs = []
    for item in raw:
        if isinstance(item, str):
            target = item.removeprefix("record:") if item.startswith("record:") else item
            refs.append(Reference(target=target, reference_id=item))
        elif isinstance(item, dict):
            target = item.get("record_id") or item.get("target") or item.get("id")
            if target:
                refs.append(Reference(target=str(target), reference_id=item.get("reference_id")))
    return tuple(refs)


class JsonRecordsAdapter:
    name = "json_records"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _documents(self) -> Iterable[tuple[int, dict[str, Any]]]:
        if not self.path.exists() or not self.path.is_file():
            return
        if self.path.suffix.lower() == ".jsonl":
            with self.path.open("r", encoding="utf-8", errors="replace") as f:
                for line_no, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(value, dict):
                        yield line_no, value
            return
        try:
            value = json.loads(self.path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(value, list):
            for index, item in enumerate(value, start=1):
                if isinstance(item, dict):
                    yield index, item
        elif isinstance(value, dict) and isinstance(value.get("records"), list):
            for index, item in enumerate(value["records"], start=1):
                if isinstance(item, dict):
                    yield index, item
        elif isinstance(value, dict):
            yield 1, value

    def _flat_candidate(self, record: dict[str, Any], line_no: int, target: TargetSpec) -> RawCandidate | None:
        raw_content = _first(record, CONTENT_KEYS)
        if raw_content is None and isinstance(record.get("message"), dict):
            nested = record["message"]
            raw_content = _first(nested, CONTENT_KEYS)
            record = {**record, **{k: v for k, v in nested.items() if k not in record}}
        content = _content(raw_content)
        if not content:
            return None
        match = literal_match(content, target)
        relation = record.get("relation")
        if not match and not relation:
            return None
        method = RetrievalMethod.EXACT if match == "EXACT" else RetrievalMethod.NORMALIZED if match else RetrievalMethod.SEMANTIC
        return RawCandidate(
            source_name=self.name,
            source_locator=f"{self.path}:{line_no}",
            content=content,
            source_record_id=str(_first(record, RECORD_ID_KEYS)) if _first(record, RECORD_ID_KEYS) is not None else None,
            event_time=_first(record, TIME_KEYS),
            author=str(_first(record, AUTHOR_KEYS)) if _first(record, AUTHOR_KEYS) is not None else None,
            retrieval_method=method,
            metadata={k: v for k, v in record.items() if k not in CONTENT_KEYS},
            references=_references(record),
            limitations=() if _first(record, TIME_KEYS) is not None else ("missing event_time",),
        )

    def _conversation_candidates(self, envelope: dict[str, Any], line_no: int, target: TargetSpec):
        messages = envelope.get("messages")
        if not isinstance(messages, list):
            return
        source = str(envelope.get("source") or "conversation")
        session_id = str(envelope.get("session_id") or f"line-{line_no}")
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            content = _content(message.get("content") if "content" in message else message.get("text"))
            if not content:
                continue
            match = literal_match(content, target)
            relation = message.get("relation")
            if not match and not relation:
                continue
            explicit_id = _first(message, RECORD_ID_KEYS)
            record_id = str(explicit_id) if explicit_id is not None else f"{source}:{session_id}:{index}"
            event_time = _first(message, TIME_KEYS)
            if event_time is None:
                event_time = envelope.get("created_at")
            meta = {
                "source": source,
                "session_id": session_id,
                "message_index": index,
                "project_path": envelope.get("project_path"),
                "model": envelope.get("model") or message.get("model"),
                "tool_use": message.get("tool_use"),
                "extraction_confidence": envelope.get("extraction_confidence"),
                "heuristic": envelope.get("heuristic", False),
                "relation": message.get("relation"),
            }
            yield RawCandidate(
                source_name=self.name,
                source_locator=f"{self.path}:{line_no}#message[{index}]",
                content=content,
                source_record_id=record_id,
                event_time=event_time,
                author=message.get("role") or message.get("author"),
                retrieval_method=RetrievalMethod.EXACT if match == "EXACT" else RetrievalMethod.NORMALIZED if match else RetrievalMethod.SEMANTIC,
                metadata=meta,
                references=_references(message),
                limitations=() if event_time is not None else ("missing event_time",),
            )

    def discover(self, target: TargetSpec):
        for line_no, record in self._documents() or ():
            if isinstance(record.get("messages"), list):
                yield from self._conversation_candidates(record, line_no, target)
                continue
            candidate = self._flat_candidate(record, line_no, target)
            if candidate:
                yield candidate

    def resolve_reference(self, ref: Reference):
        for line_no, record in self._documents() or ():
            if isinstance(record.get("messages"), list):
                source = str(record.get("source") or "conversation")
                session_id = str(record.get("session_id") or f"line-{line_no}")
                for index, message in enumerate(record["messages"]):
                    if not isinstance(message, dict):
                        continue
                    explicit = _first(message, RECORD_ID_KEYS)
                    record_id = str(explicit) if explicit is not None else f"{source}:{session_id}:{index}"
                    if record_id != ref.target:
                        continue
                    content = _content(message.get("content") if "content" in message else message.get("text"))
                    if not content:
                        continue
                    event_time = _first(message, TIME_KEYS) or record.get("created_at")
                    yield RawCandidate(
                        source_name=self.name,
                        source_locator=f"{self.path}:{line_no}#message[{index}]",
                        content=content,
                        source_record_id=record_id,
                        event_time=event_time,
                        author=message.get("role") or message.get("author"),
                        retrieval_method=RetrievalMethod.BACK_REFERENCE,
                        metadata={"source": source, "session_id": session_id, "message_index": index},
                        references=_references(message),
                    )
                continue
            record_id = _first(record, RECORD_ID_KEYS)
            if record_id is None or str(record_id) != ref.target:
                continue
            candidate = self._flat_candidate(record, line_no, TargetSpec("_ref", target_kind_fallback(), "", literal_forms=("",)))
            if candidate:
                yield replace(candidate, retrieval_method=RetrievalMethod.BACK_REFERENCE)

    def normalize(self, candidate: RawCandidate) -> EvidenceEvent:
        content_hash = hashlib.sha256(candidate.content.encode("utf-8")).hexdigest()
        record_id = candidate.source_record_id or f"json:{hashlib.sha256((candidate.source_locator + ':' + content_hash).encode()).hexdigest()[:20]}"
        metadata = dict(candidate.metadata)
        if candidate.references:
            metadata["references"] = tuple(r.target for r in candidate.references)
        epistemic = EpistemicStatus.DIRECT_SOURCE
        if metadata.get("heuristic"):
            epistemic = EpistemicStatus.DOCUMENTED_METADATA
        return EvidenceEvent(
            record_id=record_id,
            source_surface=self.name,
            source_locator=candidate.source_locator,
            source_record_id=candidate.source_record_id,
            author=candidate.author,
            event_time=parse_time(candidate.event_time),
            content=candidate.content,
            content_hash=content_hash,
            retrieval_method=candidate.retrieval_method,
            epistemic_status=epistemic,
            metadata=metadata,
            limitations=candidate.limitations,
        )


def target_kind_fallback():
    from roots.model import TargetKind

    return TargetKind.OTHER
