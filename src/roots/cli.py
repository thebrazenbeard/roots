"""Read-only candidate discovery CLI; this is not a lineage/origin verifier."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from roots import __version__
from roots.adapters.filesystem import FilesystemAdapter
from roots.adapters.json_records import JsonRecordsAdapter
from roots.model import EvidenceEvent, TargetSpec


def _positive_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("limit must be an integer") from exc
    if not 1 <= limit <= 1000:
        raise argparse.ArgumentTypeError("limit must be between 1 and 1000")
    return limit


def _adapter_for(source: Path):
    if source.is_file():
        suffix = source.suffix.lower()
        if suffix in {".md", ".txt"}:
            return FilesystemAdapter(source)
        if suffix in {".json", ".jsonl"}:
            return JsonRecordsAdapter(source)
        raise ValueError(f"unsupported source file type: {suffix or '[none]'}")
    if source.is_dir():
        # The existing filesystem adapter discovers only .md and .txt records.
        return FilesystemAdapter(source)
    raise ValueError(f"source is not a readable file or directory: {source}")


def _discover(sources: Sequence[Path], target: TargetSpec) -> Iterable[EvidenceEvent]:
    for source in sources:
        adapter = _adapter_for(source)
        for candidate in adapter.discover(target):
            yield adapter.normalize(candidate)


def _event_summary(event: EvidenceEvent, *, include_content: bool) -> dict[str, object]:
    result: dict[str, object] = {
        "record_id": event.record_id,
        "source_surface": event.source_surface,
        "source_locator": event.source_locator,
        "author": event.author,
        "retrieval_method": event.retrieval_method.value,
        "epistemic_status": event.epistemic_status.value,
        "event_time": {
            "start": event.event_time.start.isoformat() if event.event_time.start else None,
            "end": event.event_time.end.isoformat() if event.event_time.end else None,
            "precision": event.event_time.precision.value,
        },
        "content_sha256": event.content_hash,
        "limitations": list(event.limitations),
    }
    if include_content:
        result["content"] = event.content
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="roots", description="Roots evidence candidate tools")
    parser.add_argument("--version", action="version", version=f"roots {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)
    candidates = subcommands.add_parser(
        "candidates",
        help="discover candidate records only (does not reconstruct or verify origins)",
    )
    candidates.add_argument("query", help="literal or normalized phrase to discover")
    candidates.add_argument("--source", type=Path, action="append", required=True, help="local .md/.txt directory or .md/.txt/.json/.jsonl file")
    candidates.add_argument("--limit", type=_positive_limit, default=100, help="maximum returned candidates (1-1000; default: 100)")
    candidates.add_argument("--include-content", action="store_true", help="include raw matched content in local stdout JSON")

    args = parser.parse_args(argv)
    if args.command == "candidates":
        if not args.query.strip():
            parser.error("query must not be blank")
        try:
            # Validate every source, even if a match limit would be reached early.
            for source in args.source:
                _adapter_for(source)
            target = TargetSpec.from_cli(args.query)
            events: list[EvidenceEvent] = []
            truncated = False
            for event in _discover(args.source, target):
                if len(events) == args.limit:
                    truncated = True
                    break
                events.append(event)
        except (OSError, ValueError) as exc:
            print(f"roots: {exc}", file=sys.stderr)
            return 2
        result = {
            "schema_version": 1,
            "operation": "candidate_discovery",
            "target": args.query,
            "source_paths": [str(source) for source in args.source],
            "candidate_count": len(events),
            "limit_reached": truncated,
            "ordering": "adapter_discovery_order",
            "origin_status": "NOT_ASSESSED",
            "source_completeness": "UNKNOWN",
            "content_included": args.include_content,
            "candidates": [_event_summary(e, include_content=args.include_content) for e in events],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
