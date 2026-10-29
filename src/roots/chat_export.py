"""Metadata-only provenance projection of an already authorized ChatGPT export.

This is NOT an archive reader, authenticator, private search API, or memory writer.
The caller must authenticate the source and enforce authorization independently.
No title, message text, attachment, or arbitrary export metadata is copied out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Mapping
from urllib.parse import quote

from .model import TimeBounds
from .time import TemporalRelation, compare_time_bounds, parse_time


_FINGERPRINT = re.compile(r"[0-9a-f]{64}\Z")
_NUMBERED = re.compile(r"conversations-(\d{3})\.json\Z")
_BASIS_LOCATOR = re.compile(r"(?:review|receipt)://[A-Za-z0-9_-]{1,64}\Z")
_ROLES = frozenset({"system", "developer", "user", "assistant", "tool"})


class ChatExportProvenanceError(ValueError):
    """A source contract error; details deliberately exclude private content."""


class AdmissionState(StrEnum):
    NOT_ADMITTED = "NOT_ADMITTED"


class CorrectionStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    UNVERIFIED_CANDIDATE = "UNVERIFIED_CANDIDATE"


class TimestampOrigin(StrEnum):
    MESSAGE = "MESSAGE"
    CONVERSATION_FALLBACK = "CONVERSATION_FALLBACK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ChatExportNodeRef:
    """Source pointer only; never a claim that its contents are currently true."""

    source_fingerprint: str
    shard_name: str
    conversation_id: str
    node_id: str
    message_id: str | None
    parent_node_id: str | None
    author_role: str | None
    event_time: TimeBounds
    timestamp_origin: TimestampOrigin
    message_present: bool
    historical_untrusted: bool = field(default=True, init=False)
    admission_state: AdmissionState = field(default=AdmissionState.NOT_ADMITTED, init=False)
    correction_status: CorrectionStatus = field(default=CorrectionStatus.NOT_ASSESSED, init=False)

    @property
    def source_locator(self) -> str:
        # Structured identifiers are URL-escaped so record IDs cannot supply
        # locator delimiters or an absolute path.
        return (f"chat-export:{self.source_fingerprint}/{self.shard_name}/"
                f"{quote(self.conversation_id, safe='')}/{quote(self.node_id, safe='')}")


@dataclass(frozen=True, slots=True)
class ChatCorrectionCandidate:
    original_source_locator: str
    later_source_locator: str
    original_node_id: str
    later_node_id: str
    basis_locator: str
    status: CorrectionStatus = field(default=CorrectionStatus.UNVERIFIED_CANDIDATE,
                                     init=False)


def validate_shard_manifest(actual: Iterable[str], expected: Iterable[str]) -> tuple[str, ...]:
    """Reconcile shard names against a caller-supplied, independent manifest.

    Exact name agreement is necessary but not sufficient for source integrity;
    callers must authenticate bytes and establish manifest provenance elsewhere.
    """
    names = tuple(actual)
    declared = tuple(expected)
    if not names or not declared or len(set(names)) != len(names) or len(set(declared)) != len(declared):
        raise ChatExportProvenanceError("empty or duplicate shard manifest")
    if set(names) != set(declared):
        raise ChatExportProvenanceError("observed and expected shard sets differ")
    if names == ("conversations.json",) or set(names) == {"conversations.json"}:
        return ("conversations.json",)
    numbers = []
    for name in names:
        if not isinstance(name, str):
            raise ChatExportProvenanceError("unsupported shard name")
        match = _NUMBERED.fullmatch(name)
        if match is None:
            raise ChatExportProvenanceError("unsupported shard name")
        numbers.append(int(match.group(1)))
    if sorted(numbers) != list(range(len(numbers))):
        raise ChatExportProvenanceError("numbered shards are not contiguous from zero")
    return tuple(sorted(names))


def _required_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ChatExportProvenanceError(f"missing or invalid {label}")
    return value


def _optional_identifier(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _required_identifier(value, label)


def _author_role(author: Mapping[str, Any] | None) -> str | None:
    if author is None or author.get("role") is None:
        return None
    role = author["role"]
    if not isinstance(role, str):
        raise ChatExportProvenanceError("invalid author role")
    # Chat text accidentally placed in a role field must never become an
    # emitted free-form metadata value.
    return role if role in _ROLES else "unknown"


def _event_time(message: Mapping[str, Any] | None, conversation: Mapping[str, Any]):
    if message is not None and message.get("create_time") is not None:
        value, origin = message["create_time"], TimestampOrigin.MESSAGE
    elif conversation.get("create_time") is not None:
        value, origin = conversation["create_time"], TimestampOrigin.CONVERSATION_FALLBACK
    else:
        value, origin = None, TimestampOrigin.UNKNOWN
    try:
        return parse_time(value), origin
    except (OverflowError, OSError, ValueError) as exc:
        raise ChatExportProvenanceError("invalid source timestamp") from exc


def iter_chat_export_nodes(
    shards: Iterable[tuple[str, Iterable[Mapping[str, Any]]]],
    *,
    source_fingerprint: str,
    expected_shards: Iterable[str],
) -> Iterable[ChatExportNodeRef]:
    """Yield every mapping node without copying any message content.

    The returned record count is a *node* count, not a non-empty message count.
    Duplicate conversation IDs fail closed across shards. This function makes
    no claims about encrypted-source authenticity, completeness beyond the
    supplied manifest, corrections, or memory admission.
    """
    if not isinstance(source_fingerprint, str) or not _FINGERPRINT.fullmatch(source_fingerprint):
        raise ChatExportProvenanceError("source fingerprint must be lowercase SHA-256")
    supplied = tuple(shards)  # Holds shard iterables, not conversation bodies.
    ordered_names = validate_shard_manifest((name for name, _ in supplied), expected_shards)
    by_name = {name: records for name, records in supplied}
    seen_conversations: set[str] = set()
    for shard_name in ordered_names:
        for conversation in by_name[shard_name]:
            if not isinstance(conversation, Mapping):
                raise ChatExportProvenanceError("invalid conversation record")
            conversation_id = _required_identifier(conversation.get("id"), "conversation ID")
            if conversation_id in seen_conversations:
                raise ChatExportProvenanceError("duplicate conversation ID across export shards")
            seen_conversations.add(conversation_id)
            mapping = conversation.get("mapping")
            if not isinstance(mapping, Mapping):
                raise ChatExportProvenanceError("conversation mapping must be an object")
            for node_key, node in mapping.items():
                node_id = _required_identifier(node_key, "mapping node ID")
                if not isinstance(node, Mapping):
                    raise ChatExportProvenanceError("mapping node must be an object")
                explicit_node_id = node.get("id")
                if explicit_node_id is not None and explicit_node_id != node_id:
                    raise ChatExportProvenanceError("mapping node identity mismatch")
                message = node.get("message")
                if message is not None and not isinstance(message, Mapping):
                    raise ChatExportProvenanceError("message must be an object or null")
                author = message.get("author") if message is not None else None
                if author is not None and not isinstance(author, Mapping):
                    raise ChatExportProvenanceError("message author must be an object or null")
                role = _author_role(author)
                event_time, timestamp_origin = _event_time(message, conversation)
                yield ChatExportNodeRef(
                    source_fingerprint=source_fingerprint,
                    shard_name=shard_name,
                    conversation_id=conversation_id,
                    node_id=node_id,
                    message_id=_optional_identifier(message.get("id"), "message ID") if message else None,
                    parent_node_id=_optional_identifier(node.get("parent"), "parent node ID"),
                    author_role=role,
                    event_time=event_time,
                    timestamp_origin=timestamp_origin,
                    message_present=message is not None,
                )


def propose_correction(original: ChatExportNodeRef, later: ChatExportNodeRef,
                       *, basis_locator: str) -> ChatCorrectionCandidate:
    """Stage a human/reviewer-supplied lead, never infer correction from reply order."""
    if (original.source_locator == later.source_locator
            or original.source_fingerprint != later.source_fingerprint):
        raise ChatExportProvenanceError("correction references must be distinct in one source")
    if not isinstance(basis_locator, str) or not _BASIS_LOCATOR.fullmatch(basis_locator):
        raise ChatExportProvenanceError("correction candidate requires a bounded review/receipt locator")
    # A conversation-level fallback is not evidence that a particular
    # message predates another. Only two message-authored timestamps can
    # justify this chronological rejection.
    if (original.timestamp_origin is TimestampOrigin.MESSAGE
            and later.timestamp_origin is TimestampOrigin.MESSAGE
            and compare_time_bounds(original.event_time, later.event_time) is TemporalRelation.AFTER):
        raise ChatExportProvenanceError("correction candidate predates referenced record")
    return ChatCorrectionCandidate(original.source_locator, later.source_locator,
                                   original.node_id, later.node_id, basis_locator)
