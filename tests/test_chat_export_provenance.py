"""Synthetic-only contract checks; no account export or transcript fixture."""

from dataclasses import asdict
from datetime import datetime, timezone
import unittest

from roots.chat_export import (
    AdmissionState,
    ChatExportProvenanceError,
    CorrectionStatus,
    iter_chat_export_nodes,
    propose_correction,
    validate_shard_manifest,
)


FINGERPRINT = "a" * 64  # Test-only stand-in, not a real export identifier.


def _conversation(conversation_id="synthetic-conversation", text="PRIVATE SENTINEL"):
    return {
        "id": conversation_id,
        "create_time": 1_700_000_000,
        "title": "DO NOT COPY THIS TITLE",
        "mapping": {
            "root": {"id": "root", "parent": None, "message": None},
            "user-node": {
                "id": "user-node", "parent": "root",
                "message": {"id": "synthetic-message", "author": {"role": "user"},
                            "create_time": 1_700_000_100,
                            "content": {"content_type": "text", "parts": [text]}},
            },
            "assistant-node": {
                "id": "assistant-node", "parent": "user-node",
                "message": {"id": "synthetic-assistant-message",
                            "author": {"role": "assistant"},
                            "content": {"parts": ["another private sentinel"]}},
            },
        },
    }


def _project(shards, expected):
    return tuple(iter_chat_export_nodes(shards, source_fingerprint=FINGERPRINT,
                                        expected_shards=expected))


class ChatExportProvenanceTests(unittest.TestCase):
    def test_metadata_only_projection_preserves_nodes_and_timestamps(self):
        nodes = _project([("conversations-000.json", [_conversation()])],
                         ["conversations-000.json"])
        self.assertEqual(len(nodes), 3)  # Mapping root still counts as a source node.
        by_id = {node.node_id: node for node in nodes}
        self.assertFalse(by_id["root"].message_present)
        self.assertIsNone(by_id["root"].message_id)
        self.assertEqual(by_id["user-node"].author_role, "user")
        self.assertEqual(by_id["user-node"].message_id, "synthetic-message")
        self.assertEqual(by_id["user-node"].timestamp_origin, "MESSAGE")
        self.assertEqual(by_id["user-node"].event_time.start,
                         datetime(2023, 11, 14, 22, 15, tzinfo=timezone.utc))
        self.assertEqual(by_id["assistant-node"].timestamp_origin, "CONVERSATION_FALLBACK")
        self.assertEqual(by_id["assistant-node"].parent_node_id, "user-node")
        self.assertTrue(all(n.admission_state is AdmissionState.NOT_ADMITTED for n in nodes))
        self.assertTrue(all(n.historical_untrusted for n in nodes))
        self.assertTrue(all(n.correction_status is CorrectionStatus.NOT_ASSESSED for n in nodes))
        self.assertNotIn("PRIVATE SENTINEL", repr(nodes))
        self.assertNotIn("DO NOT COPY THIS TITLE", repr(nodes))
        self.assertTrue(all("content" not in asdict(n) and "title" not in asdict(n)
                            for n in nodes))

    def test_shard_manifest_rejects_missing_duplicate_gaps_or_unsupported(self):
        cases = [
            (["conversations-000.json", "conversations-002.json"],
             ["conversations-000.json", "conversations-001.json", "conversations-002.json"]),
            (["conversations-000.json", "conversations-000.json"], ["conversations-000.json"]),
            (["conversations-001.json"], ["conversations-001.json"]),
            (["conversations-000.json", "other.json"], ["conversations-000.json", "other.json"]),
        ]
        for actual, expected in cases:
            with self.subTest(actual=actual), self.assertRaises(ChatExportProvenanceError):
                validate_shard_manifest(actual, expected)

    def test_shard_manifest_supports_single_file_and_contiguous_parts(self):
        self.assertEqual(validate_shard_manifest(["conversations.json"],
                                                 ["conversations.json"]), ("conversations.json",))
        names = ["conversations-000.json", "conversations-001.json"]
        self.assertEqual(validate_shard_manifest(names, names), tuple(names))

    def test_rejects_duplicate_conversations_across_shards(self):
        shards = [("conversations-000.json", [_conversation()]),
                  ("conversations-001.json", [_conversation()])]
        with self.assertRaisesRegex(ChatExportProvenanceError, "duplicate conversation"):
            _project(shards, ["conversations-000.json", "conversations-001.json"])

    def test_rejects_inconsistent_node_identity(self):
        conversation = _conversation()
        conversation["mapping"]["user-node"]["id"] = "different-id"
        with self.assertRaisesRegex(ChatExportProvenanceError, "node identity"):
            _project([("conversations-000.json", [conversation])], ["conversations-000.json"])

    def test_reply_chain_is_not_a_correction(self):
        nodes = _project([("conversations-000.json", [_conversation()])],
                         ["conversations-000.json"])
        by_id = {n.node_id: n for n in nodes}
        candidate = propose_correction(by_id["user-node"], by_id["assistant-node"],
                                       basis_locator="review://synthetic-annotation")
        self.assertIs(candidate.status, CorrectionStatus.UNVERIFIED_CANDIDATE)
        self.assertEqual(candidate.original_node_id, "user-node")
        self.assertEqual(candidate.later_node_id, "assistant-node")
        self.assertIs(by_id["assistant-node"].correction_status, CorrectionStatus.NOT_ASSESSED)
        with self.assertRaises(ChatExportProvenanceError):
            propose_correction(by_id["user-node"], by_id["assistant-node"], basis_locator="")
        for invalid in ("review://PRIVATE SENTINEL", "review://" + "x" * 65,
                        "https://example.invalid/private", "review://foo/bar"):
            with self.subTest(invalid=invalid), self.assertRaises(ChatExportProvenanceError):
                propose_correction(by_id["user-node"], by_id["assistant-node"],
                                   basis_locator=invalid)
        reverse = _conversation()
        reverse["mapping"]["assistant-node"]["message"]["create_time"] = 1_700_000_050
        reversed_nodes = {n.node_id: n for n in _project(
            [("conversations-000.json", [reverse])], ["conversations-000.json"])}
        with self.assertRaisesRegex(ChatExportProvenanceError, "predates"):
            propose_correction(reversed_nodes["user-node"], reversed_nodes["assistant-node"],
                               basis_locator="review://synthetic-annotation")

    def test_bad_fingerprint_and_malformed_record_fail_closed(self):
        with self.assertRaises(ChatExportProvenanceError):
            tuple(iter_chat_export_nodes([("conversations-000.json", [_conversation()])],
                                         source_fingerprint="not-a-digest",
                                         expected_shards=["conversations-000.json"]))
        malformed = _conversation()
        malformed["mapping"] = []
        with self.assertRaisesRegex(ChatExportProvenanceError, "mapping"):
            _project([("conversations-000.json", [malformed])], ["conversations-000.json"])

    def test_unexpected_role_cannot_smuggle_free_form_chat_text(self):
        conversation = _conversation()
        conversation["mapping"]["user-node"]["message"]["author"]["role"] = "PRIVATE ROLE SENTINEL"
        nodes = _project([("conversations-000.json", [conversation])],
                         ["conversations-000.json"])
        by_id = {n.node_id: n for n in nodes}
        self.assertEqual(by_id["user-node"].author_role, "unknown")
        self.assertNotIn("PRIVATE ROLE SENTINEL", repr(nodes))


if __name__ == "__main__":
    unittest.main()
