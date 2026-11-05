"""Bounded, candidate-only provenance triggers for host-controlled pre-answer routing.

This module does not read a corpus, authorize memory access, or execute commands.
A match requests review of provenance candidates; it is not semantic proof.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

MAX_TEXT_CHARS = 8192
MAX_TEXT_TOKENS = 512
MAX_RULES = 64
_WORDS = re.compile(r"[^\W_]+", re.UNICODE)


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(_WORDS.findall(unicodedata.normalize("NFKC", value).casefold()))


def _contains(words: tuple[str, ...], phrase: tuple[str, ...]) -> bool:
    return bool(phrase) and any(
        words[index : index + len(phrase)] == phrase
        for index in range(len(words) - len(phrase) + 1)
    )


class TriggerStatus(StrEnum):
    NO_TRIGGER = "NO_TRIGGER"
    LOOKUP_REQUESTED = "LOOKUP_REQUESTED"
    AMBIGUOUS = "AMBIGUOUS"
    SUPPRESSED = "SUPPRESSED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class TriggerRule:
    """Operator-reviewed concept hint; scope_key is not an access grant.

    phrase_forms support ordinary rewording. Every semantic_group represents
    one independent meaning axis, whose alternatives can be multiword phrases.
    Matching all axes within one bounded window makes a *candidate* only.
    """

    concept_id: str
    query: str
    scope_key: str
    phrase_forms: tuple[str, ...] = ()
    semantic_groups: tuple[tuple[str, ...], ...] = ()
    max_window_tokens: int = 24

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and 0 < len(value.strip()) <= 256
            for value in (self.concept_id, self.query, self.scope_key)
        ):
            raise ValueError("concept_id, query and scope_key must be bounded nonblank strings")
        if type(self.max_window_tokens) is not int or not 8 <= self.max_window_tokens <= 48:
            raise ValueError("max_window_tokens must be an integer between 8 and 48")
        if type(self.phrase_forms) is not tuple or type(self.semantic_groups) is not tuple:
            raise ValueError("trigger forms and concept groups must be tuples")
        if not self.phrase_forms and not self.semantic_groups:
            raise ValueError("a trigger requires phrase_forms or semantic_groups")
        if len(self.phrase_forms) > 16 or len(self.semantic_groups) > 8:
            raise ValueError("too many trigger forms or concept groups")
        if self.semantic_groups and len(self.semantic_groups) < 2:
            raise ValueError("semantic triggering requires at least two independent groups")
        forms = list(self.phrase_forms)
        for group in self.semantic_groups:
            if type(group) is not tuple or not 1 <= len(group) <= 16:
                raise ValueError("concept groups must contain 1-16 alternatives")
            forms.extend(group)
        if any(
            not isinstance(form, str)
            or len(form) > 160
            or not 1 <= len(_tokens(form)) <= 12
            for form in forms
        ):
            raise ValueError("trigger forms must have 1-12 words and at most 160 characters")


@dataclass(frozen=True, slots=True)
class TriggerHit:
    concept_id: str
    query: str
    scope_key: str
    match_method: str


@dataclass(frozen=True, slots=True)
class TriggerDecision:
    status: TriggerStatus
    hits: tuple[TriggerHit, ...] = ()
    limitations: tuple[str, ...] = ()


def _match(words: tuple[str, ...], rule: TriggerRule) -> str | None:
    if any(_contains(words, _tokens(form)) for form in rule.phrase_forms):
        return "CONFIGURED_PHRASE"
    if rule.semantic_groups:
        for start in range(len(words)):
            window = words[start : start + rule.max_window_tokens]
            if all(
                any(_contains(window, _tokens(alternative)) for alternative in group)
                for group in rule.semantic_groups
            ):
                return "CONFIGURED_CONCEPT_GROUPS"
    return None


def resolve_provenance_trigger(
    text: str,
    rules: Sequence[TriggerRule],
    *,
    allow_lookup: bool = True,
) -> TriggerDecision:
    """Resolve *whether to request* provenance lookup, without performing one.

    Hosts must independently authenticate actor/corpus scope, check privacy and
    currentness, and retrieve/cite primary evidence. Matching never installs
    memory, establishes origin, changes authority, or runs control commands.
    """

    if not allow_lookup:
        return TriggerDecision(TriggerStatus.SUPPRESSED)
    if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:
        return TriggerDecision(TriggerStatus.UNRESOLVED, limitations=("input_not_bounded",))
    if len(rules) > MAX_RULES or len({r.concept_id for r in rules}) != len(rules):
        return TriggerDecision(TriggerStatus.UNRESOLVED, limitations=("rules_not_bounded_or_unique",))
    words = _tokens(text)
    if len(words) > MAX_TEXT_TOKENS:
        return TriggerDecision(TriggerStatus.UNRESOLVED, limitations=("token_limit_exceeded",))
    hits = tuple(
        TriggerHit(rule.concept_id, rule.query, rule.scope_key, method)
        for rule in rules
        if (method := _match(words, rule)) is not None
    )
    if not hits:
        return TriggerDecision(TriggerStatus.NO_TRIGGER)
    common = ("candidate_only", "authorization_and_source_verification_required")
    if len(hits) > 1:
        return TriggerDecision(TriggerStatus.AMBIGUOUS, hits, common + ("no_automatic_disambiguation",))
    return TriggerDecision(TriggerStatus.LOOKUP_REQUESTED, hits, common)
