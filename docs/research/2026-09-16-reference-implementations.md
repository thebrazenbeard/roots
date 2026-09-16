# Reference implementation notes — 2026-09-16

Roots reviewed two public MIT-licensed projects as design references before executable implementation began. These are influences and interoperability targets, not vendored code.

## `kruzovic7/ai-data-extractor`

Relevant mechanism:

- source-specific extractors discover heterogeneous local AI-assistant stores;
- source-specific details are normalized into a common JSONL conversation shape;
- malformed/corrupt inputs are isolated so one source does not destroy the entire extraction run;
- local databases are treated read-only / copied before querying;
- the common output retains source, session, message, timestamp, tool-use and project metadata where available.

Roots takeaway:

**Extraction and provenance reconstruction are different responsibilities.** Roots should not become a catalog of every product's private storage schema. It should accept canonical/normalized conversation records while preserving source/session/message provenance. A source-specific extractor can be upstream of Roots.

Roots v0.1 therefore supports both flat event JSON/JSONL and conversation-envelope JSONL with `messages[]`. Each nested message becomes its own evidence event with a deterministic record identity derived from source/session/message position or explicit message ID.

Heuristic extraction must remain marked as heuristic upstream metadata. Roots must not promote heuristic extraction confidence into direct historical certainty.

## `pomber/git-history`

Relevant mechanism:

- history is scoped to a specific file with `git log -- <path>`;
- each historical file state is read from the corresponding commit with `git show <commit>:<path>`;
- commit identity, author, date and message travel with the historical content.

Roots takeaway:

Git history is not merely another search surface; it is a high-quality temporal evidence source. A local read-only Git adapter can deterministically reconstruct versioned file states without network access or extra runtime dependencies.

Roots will implement a v0.1 `GitFileHistoryAdapter` using Python `subprocess` against the local `git` executable. It will:

1. require an explicit repository/file path;
2. enumerate commits affecting the file;
3. retain full commit SHA, author timestamp, author identity and message;
4. load the file's content at each commit;
5. emit one evidence event per historical file state containing the target;
6. preserve commit topology metadata separately from event-time chronology;
7. never treat Git's default newest-first `log` output as provenance interpretation order;
8. remain read-only.

Roots will not copy Git History's JavaScript implementation. The public Git command pattern is used as an architectural reference.

## Resulting boundary

Roots v0.1 owns:

- provenance target typing;
- normalized evidence events;
- chronological partial ordering;
- oldest-first replay;
- literal vs conceptual lineage typing;
- back-reference resolution;
- verification;
- receipts;
- local Markdown/text, flat JSON/JSONL, conversation-envelope JSONL, and local Git file-history adapters.

Roots v0.1 does not own:

- product-specific extraction from Cursor/Claude/Codex/etc. private stores;
- embeddings/vector databases;
- LLM semantic classifiers as historical authorities;
- remote GitHub/GitLab API history adapters;
- mutation of any source being inspected.
