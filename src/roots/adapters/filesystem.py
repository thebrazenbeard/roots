from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from roots.model import EvidenceEvent, EpistemicStatus, RetrievalMethod, TargetSpec
from roots.normalize import literal_match
from roots.time import parse_time

from .base import RawCandidate, Reference


class FilesystemAdapter:
    name = "filesystem"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _files(self) -> Iterable[Path]:
        if self.path.is_file():
            if self.path.suffix.lower() in {".md", ".txt"}:
                yield self.path
            return
        if self.path.is_dir():
            for p in sorted(self.path.rglob("*")):
                if p.is_file() and p.suffix.lower() in {".md", ".txt"}:
                    yield p

    @staticmethod
    def _front_matter(text: str) -> tuple[dict[str, str], str]:
        if not text.startswith("---\n"):
            return {}, text
        marker = text.find("\n---\n", 4)
        if marker == -1:
            return {}, text
        header = text[4:marker]
        body = text[marker + 5 :]
        meta: dict[str, str] = {}
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
        return meta, body

    @staticmethod
    def _refs(meta: dict[str, str]) -> tuple[Reference, ...]:
        raw = meta.get("references") or meta.get("back_references") or meta.get("source_refs")
        if not raw:
            return ()
        refs = []
        for item in raw.split(","):
            item = item.strip()
            if item.startswith("record:"):
                refs.append(Reference(target=item.removeprefix("record:"), reference_id=item))
            elif item:
                refs.append(Reference(target=item, reference_id=item))
        return tuple(refs)

    def discover(self, target: TargetSpec):
        for path in self._files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = self._front_matter(text)
            match = literal_match(body, target)
            relation = meta.get("relation")
            if not match and not relation:
                continue
            method = RetrievalMethod.EXACT if match == "EXACT" else RetrievalMethod.NORMALIZED if match else RetrievalMethod.SEMANTIC
            limitations = () if meta.get("event_time") or meta.get("timestamp") or meta.get("created_at") else ("missing event_time",)
            yield RawCandidate(
                source_name=self.name,
                source_locator=str(path),
                content=body,
                source_record_id=meta.get("record_id") or meta.get("id"),
                event_time=meta.get("event_time") or meta.get("timestamp") or meta.get("created_at"),
                author=meta.get("author") or meta.get("speaker") or meta.get("role"),
                retrieval_method=method,
                metadata={**meta, "path": str(path)},
                references=self._refs(meta),
                limitations=limitations,
            )

    def resolve_reference(self, ref: Reference):
        for path in self._files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, body = self._front_matter(text)
            record_id = meta.get("record_id") or meta.get("id")
            if record_id != ref.target:
                continue
            yield RawCandidate(
                source_name=self.name,
                source_locator=str(path),
                content=body,
                source_record_id=record_id,
                event_time=meta.get("event_time") or meta.get("timestamp") or meta.get("created_at"),
                author=meta.get("author") or meta.get("speaker") or meta.get("role"),
                retrieval_method=RetrievalMethod.BACK_REFERENCE,
                metadata={**meta, "path": str(path)},
                references=self._refs(meta),
                limitations=() if meta.get("event_time") or meta.get("timestamp") or meta.get("created_at") else ("missing event_time",),
            )

    def normalize(self, candidate: RawCandidate) -> EvidenceEvent:
        content_hash = hashlib.sha256(candidate.content.encode("utf-8")).hexdigest()
        record_id = candidate.source_record_id or f"filesystem:{hashlib.sha256((candidate.source_locator + ':' + content_hash).encode()).hexdigest()[:20]}"
        metadata = dict(candidate.metadata)
        if candidate.references:
            metadata["references"] = tuple(r.target for r in candidate.references)
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
            epistemic_status=EpistemicStatus.DIRECT_SOURCE,
            metadata=metadata,
            limitations=candidate.limitations,
        )
