"""Candidate-only semantic trigger contracts; no archive or provider access."""

from __future__ import annotations

import unittest
from dataclasses import fields

from roots.triggers import (
    MAX_TEXT_CHARS,
    TriggerRule,
    TriggerStatus,
    resolve_provenance_trigger,
)


class SemanticTriggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.council = TriggerRule(
            concept_id="inner-council",
            query="Inner Council provenance",
            scope_key="authorized-conversation-history",
            phrase_forms=("Inner Council",),
            semantic_groups=(("inner", "internal", "within"), ("council", "committee", "advisers")),
        )
        self.voice = TriggerRule(
            concept_id="voice-drift",
            query="Vera behavioral voice corrections",
            scope_key="authorized-project-controls",
            phrase_forms=("you do not sound like yourself",),
            semantic_groups=(("voice", "tone", "behavior", "speaking"), ("drifted", "changed", "different")),
        )

    def test_exact_phrase_requests_candidates_not_origin(self) -> None:
        result = resolve_provenance_trigger("Where did the Inner Council come from?", (self.council,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.LOOKUP_REQUESTED)
        self.assertEqual(result.hits[0].match_method, "CONFIGURED_PHRASE")
        self.assertEqual(result.hits[0].scope_key, "authorized-conversation-history")
        self.assertIn("authorization_and_source_verification_required", result.limitations)
        self.assertFalse(any(field.name in {"content", "source_record", "origin"} for field in fields(result.hits[0])))

    def test_semantically_related_word_combination_without_exact_phrase(self) -> None:
        result = resolve_provenance_trigger(
            "Remember the internal committee of perspectives we talked about?",
            (self.council,),
            allow_lookup=True,
        )
        self.assertEqual(result.status, TriggerStatus.LOOKUP_REQUESTED)
        self.assertEqual(result.hits[0].match_method, "CONFIGURED_CONCEPT_GROUPS")

    def test_voice_correction_rephrasing(self) -> None:
        result = resolve_provenance_trigger("Your tone feels different today.", (self.voice,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.LOOKUP_REQUESTED)
        self.assertEqual(result.hits[0].query, "Vera behavioral voice corrections")

    def test_substring_collision_does_not_trigger(self) -> None:
        result = resolve_provenance_trigger("An innerness concerning county budgets.", (self.council,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.NO_TRIGGER)

    def test_one_concept_axis_does_not_trigger(self) -> None:
        result = resolve_provenance_trigger("Internal systems need repair.", (self.council,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.NO_TRIGGER)

    def test_concept_groups_must_share_a_bounded_window(self) -> None:
        distant = "internal " + ("unrelated " * 60) + "committee"
        result = resolve_provenance_trigger(distant, (self.council,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.NO_TRIGGER)

    def test_multiple_concepts_fail_closed_as_ambiguous(self) -> None:
        result = resolve_provenance_trigger("My internal committee changed its tone.", (self.council, self.voice), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.AMBIGUOUS)
        self.assertEqual({hit.concept_id for hit in result.hits}, {"inner-council", "voice-drift"})
        self.assertIn("no_automatic_disambiguation", result.limitations)

    def test_opt_out_suppresses_even_an_exact_match(self) -> None:
        result = resolve_provenance_trigger("Inner Council", (self.council,), allow_lookup=False)
        self.assertEqual(result.status, TriggerStatus.SUPPRESSED)
        self.assertEqual(result.hits, ())

    def test_lookup_requires_explicit_literal_true(self) -> None:
        omitted = resolve_provenance_trigger("Inner Council", (self.council,))
        self.assertEqual(omitted.status, TriggerStatus.SUPPRESSED)
        for value in ("false", 1, None, False, [], {}):
            with self.subTest(value=value):
                decision = resolve_provenance_trigger("Inner Council", (self.council,), allow_lookup=value)
                self.assertEqual(decision.status, TriggerStatus.SUPPRESSED)
                self.assertEqual(decision.hits, ())

    def test_duplicate_rule_ids_fail_closed(self) -> None:
        result = resolve_provenance_trigger("Inner Council", (self.council, self.council), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.UNRESOLVED)

    def test_oversized_input_fails_closed(self) -> None:
        result = resolve_provenance_trigger("Inner Council" + " " * MAX_TEXT_CHARS, (self.council,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.UNRESOLVED)
        self.assertEqual(result.hits, ())

    def test_quoted_control_text_without_request_does_not_trigger(self) -> None:
        rule = TriggerRule(
            concept_id="restore-provenance",
            query="restore yourself control grammar history",
            scope_key="authorized-project-controls",
            phrase_forms=("restore yourself",),
        )
        result = resolve_provenance_trigger('The old transcript says "restore yourself".', (rule,), allow_lookup=True)
        self.assertEqual(result.status, TriggerStatus.NO_TRIGGER)
        self.assertEqual(result.hits, ())
        self.assertFalse(hasattr(result, "execute") or hasattr(result, "restore"))

    def test_explicit_provenance_denial_dominates_matching(self) -> None:
        for text in (
            "Do not search our history for Inner Council.",
            "Do not ever search our history for Inner Council.",
            "Never look up Inner Council in the conversation archive.",
            "Please don't retrieve the Inner Council history.",
        ):
            with self.subTest(text=text):
                result = resolve_provenance_trigger(text, (self.council,), allow_lookup=True)
                self.assertEqual(result.status, TriggerStatus.SUPPRESSED)
                self.assertEqual(result.hits, ())

    def test_quoted_mention_is_not_lookup_intent(self) -> None:
        for text in (
            "'Inner Council'",
            'The UI displayed "Inner Council".',
            'I typed "What was the origin of Inner Council?" into a field.',
            'The old transcript says "restore yourself".',
        ):
            with self.subTest(text=text):
                rule = TriggerRule("restore", "restore provenance", "controls", phrase_forms=("restore yourself",))
                result = resolve_provenance_trigger(text, (self.council, rule), allow_lookup=True)
                self.assertEqual(result.status, TriggerStatus.NO_TRIGGER)
                self.assertEqual(result.hits, ())

    def test_explicit_historical_question_can_name_quoted_subject(self) -> None:
        result = resolve_provenance_trigger(
            'Where did the name "Inner Council" come from?', (self.council,), allow_lookup=True
        )
        self.assertEqual(result.status, TriggerStatus.LOOKUP_REQUESTED)

    def test_malformed_rule_rejected_before_use(self) -> None:
        with self.assertRaises(ValueError):
            TriggerRule("single-axis", "source query", "scope", semantic_groups=(("emotion",),))
        with self.assertRaises(ValueError):
            TriggerRule("no-patterns", "source query", "scope")
        with self.assertRaises(ValueError):
            TriggerRule("empty-scope", "source query", "", phrase_forms=("meaning",))
        with self.assertRaises(ValueError):
            TriggerRule("bool-window", "source query", "scope", phrase_forms=("meaning",), max_window_tokens=True)
        with self.assertRaises(ValueError):
            TriggerRule("bad-forms", "source query", "scope", phrase_forms="meaning")
        with self.assertRaises(ValueError):
            TriggerRule("bad-groups", "source query", "scope", semantic_groups=("meaning", "change"))


if __name__ == "__main__":
    unittest.main()
