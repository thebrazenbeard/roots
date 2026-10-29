# ChatGPT export provenance projection (source contract)

Status: **metadata-only candidate projection**, not a live memory service or
qualified source-verification procedure.

`roots.chat_export` accepts already-authorized ChatGPT conversation objects
supplied in manifest-declared shards. It yields `ChatExportNodeRef` pointers
without copying titles, message bodies, attachments, tool contents, or other
free-form export metadata. Its intended input is the **authenticated local
archive/index boundary**, not a public GitHub artifact.

## Contract

Each node carries:

- source SHA-256 fingerprint, numbered shard name, original conversation ID,
  mapping node ID and optional original message ID;
- optional parent mapping node and author role;
- normalized source time, with `MESSAGE`, `CONVERSATION_FALLBACK`, or `UNKNOWN`
  marking where that timestamp came from;
- whether a source mapping node actually has a message;
- fixed `historical_untrusted=true`, `admission_state=NOT_ADMITTED`, and
  `correction_status=NOT_ASSESSED` values.

The source locator encodes these identifiers without storing content. Mapping
root/null-message nodes are retained, because counts of source *mapping nodes*
must not silently become counts of authored messages.
Author roles are reduced to known structural values; unexpected free-form role
strings become `unknown` rather than being copied into the projection.

An example with **invented** records:

```python
from roots.chat_export import iter_chat_export_nodes

source_fingerprint = "a" * 64  # Synthetic placeholder, never a real archive hash.
shards = [("conversations-000.json", [{
    "id": "synthetic-conversation",
    "create_time": 1700000000,
    "mapping": {
        "synthetic-node": {
            "id": "synthetic-node", "parent": None,
            "message": {"id": "synthetic-message", "author": {"role": "user"},
                        "create_time": 1700000100, "content": {"parts": ["fixture"]}},
        }
    },
}])]

for reference in iter_chat_export_nodes(
    shards, source_fingerprint=source_fingerprint,
    expected_shards=["conversations-000.json"]
):
    assert reference.historical_untrusted
    assert reference.admission_state == "NOT_ADMITTED"
    # Pass references only to an authorized, owner-scoped local consumer.
```

## Gates and limitations

1. `validate_shard_manifest` requires an explicit expected manifest, recognizes
   one `conversations.json` or zero-based contiguous three-digit numbered
   `conversations-000.json` shards, and rejects missing/extra/duplicate names.
   It does **not** independently establish that the expected manifest is genuine.
2. Duplicate original conversation IDs or malformed mapping structures fail.
   Consumers persisting streamed results **must transact and roll back** on
   any late validation failure; a generator is not a storage transaction.
3. This module does not open ZIPs, authenticate source bytes, verify encrypted
   indexed records, reconcile their contents with the archive, or establish
   that every historical conversation is represented. Those are upstream
   source-verification obligations.
4. Parent/reply links are **not** corrections. A separate attributable basis
   can create an `UNVERIFIED_CANDIDATE` correction link, rejected if source
   timestamps prove that the proposed correction predates its target. Unknown
   and overlapping times remain unresolved. The basis is limited to a bounded
   `review://` or `receipt://` opaque identifier (1–64 ASCII letters, digits,
   underscores or hyphens); neither arbitrary prose nor remote URLs are
   accepted. This is syntax validation, not authentication of that basis.
5. No export text becomes a present fact, autobiographical memory, identity
   update, or model instruction merely by passing through this projection.
   Memory admission requires a separately authorized, reviewed write.
6. There is no network endpoint or embedded access control. Callers must enforce
   owner identity, allowed source paths, encryption and authenticated retrieval.
   Do not publish real projected IDs, source fingerprints, transcripts or
   derived sensitive tags to a public repository, CI log, issue or Blotter.

The projection is deliberately less powerful than a provenance proof. The
`roots` chronology and receipt gates still govern any later claim of earliest
accessible evidence, derivation, correction, or current meaning.
