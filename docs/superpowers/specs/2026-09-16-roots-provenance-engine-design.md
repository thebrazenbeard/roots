# Roots Provenance Engine — Design Specification

Date: 2026-09-16
Status: Design candidate for first implementation
Repository: `thebrazenbeard/roots`

## 1. Purpose

Roots is a provenance-reconstruction system for AI-assisted review of authorized historical records.

Its purpose is not merely to retrieve records that resemble a query. Its purpose is to reconstruct the evidence-supported lineage of a target: where the earliest accessible evidence appears, how later occurrences relate to earlier ones, which records claim an origin, which claims are actually supported, how meaning changes over time, and what remains unresolved.

The target may be:

- a literal word or phrase;
- a normalized phrase or label;
- a concept;
- a claim;
- a decision;
- an event;
- a rule or protocol;
- an identifier;
- another explicitly scoped referent.

Roots must preserve the difference between these target kinds rather than flattening them into one similarity search.

## 2. Problem statement

AI systems reviewing their own accessible records are vulnerable to several provenance errors:

1. Search tools often return the most relevant or recent result first, encouraging newest-first interpretation.
2. A recent summary may describe an older event and be mistaken for primary evidence.
3. A semantic ancestor may be mistaken for the first literal occurrence of a phrase.
4. A later correction can be mistaken for the original meaning.
5. Repeated paraphrases can create false confidence that a claim is historically well-supported.
6. Missing records can be silently bridged with plausible narrative.
7. A model can stop when it finds a satisfying explanation rather than when it has reconstructed the lineage.
8. Retrospective origin claims can be accepted without following the referenced trail.
9. Ingestion time, search rank, file order, and event time can be confused.
10. Current meaning can leak backward and overwrite historical meaning.

Roots exists to make these failure modes explicit and testable.

## 3. Design thesis

**Provenance is a temporally ordered evidence graph.**

Discovery and interpretation are separate phases.

Discovery may use any authorized mechanism that increases useful recall: exact search, aliases, metadata, back-references, semantic expansion, embeddings, graph links, or model reasoning.

Interpretation begins only after evidence is normalized and ordered by event chronology. The interpretive walk proceeds **oldest to newest**.

If a later record reveals a previously undiscovered earlier candidate, Roots adds the candidate to the evidence set and restarts the interpretive walk from the oldest accessible point. A later back-reference is therefore a discovery lead, not a shortcut around chronological reconstruction.

## 4. Architectural approaches considered

### 4.1 Prompt-only methodology

An AI is instructed to search broadly, sort results oldest-first, and narrate a lineage.

Advantages:

- portable;
- inexpensive;
- easy to integrate.

Weaknesses:

- relies on behavioral compliance;
- easy to stop early;
- difficult to verify deterministically;
- chronology and evidence typing remain vulnerable to model drift.

This approach is insufficient as the final architecture but useful as a bootstrap contract.

### 4.2 Deterministic provenance engine only

A conventional program ingests records, sorts timestamps, follows explicit links, and emits a lineage.

Advantages:

- testable chronology;
- deterministic evidence bookkeeping;
- strong reproducibility.

Weaknesses:

- literal systems struggle with semantic ancestry and paraphrase;
- heterogeneous historical records often lack explicit links;
- events and concepts need contextual classification.

This approach is necessary but insufficient alone.

### 4.3 Hybrid engine + AI bootstrap contract — selected

Roots combines deterministic evidence/chronology machinery with bounded model-assisted semantic classification.

Deterministic components own facts such as record identity, timestamps, ordering, source locators, hashes, explicit links, and receipt structure.

Model-assisted components may propose aliases, semantic relatives, occurrence classifications, derivation hypotheses, and missing-evidence searches. Those outputs remain typed as inference unless directly supported.

This architecture is selected because it gives semantic reach without making semantic plausibility the provenance authority.

## 5. Non-goals

Roots v0.1 does not attempt to:

- access hidden model activations or private provider internals;
- prove metaphysical or psychological origin;
- infer unrecorded events as facts;
- guarantee a true global origin when records are incomplete;
- treat embeddings as historical authority;
- rewrite or delete source history;
- create autobiographical memory by itself;
- silently promote imported records into current truth;
- solve general knowledge-graph reasoning beyond provenance needs.

Roots only reasons over records the current runtime is authorized and technically able to access.

## 6. Core invariants

### INV-001 — Ascending interpretive chronology

Once candidate evidence is normalized, provenance interpretation MUST proceed from oldest to newest event time.

Search rank, retrieval order, ingestion order, filesystem order, and display order MUST NOT substitute for event chronology.

### INV-002 — Discovery order is non-authoritative

A candidate may be discovered in any order. Discovery order MUST NOT establish lineage position.

### INV-003 — Accessible-oldest is not proven origin

The oldest available record MUST be described as `EARLIEST_ACCESSIBLE_EVIDENCE` unless additional evidence justifies a stronger origin claim.

### INV-004 — Literal and semantic lineage remain distinct

`FIRST_LITERAL_OCCURRENCE` and `CONCEPTUAL_ANCESTOR` are distinct relations.

### INV-005 — Back-reference restart

When a reviewed record points to an earlier candidate that was absent from the evidence set, Roots MUST attempt retrieval. If new evidence is added, the interpretive walk MUST restart from the earliest candidate.

### INV-006 — Evidence/inference separation

Directly observed source facts and model-generated lineage hypotheses MUST be stored with different epistemic types.

### INV-007 — History is append-preserving

Correction, supersession, and currentness MUST NOT erase the earlier record's historical role.

### INV-008 — No invented bridges

A gap between two lineage steps remains a gap unless evidence or an explicitly typed inference connects them.

### INV-009 — Current meaning does not back-propagate

Later definitions and corrections MUST NOT silently rewrite what earlier records meant in their original context.

### INV-010 — Receipts disclose scope and completeness

Every completed trace MUST disclose which sources were searched, temporal coverage where known, unresolved gaps, and whether the result is complete only relative to accessible evidence.

## 7. Domain model

### 7.1 TargetSpec

A `TargetSpec` describes what Roots is trying to trace.

Proposed fields:

```yaml
target_id: string
kind: WORD | PHRASE | CONCEPT | CLAIM | DECISION | EVENT | RULE | IDENTIFIER | OTHER
query_original: string
literal_forms: [string]
normalized_forms: [string]
semantic_description: string | null
aliases: [string]
scope:
  source_surfaces: [string]
  time_start: datetime | null
  time_end: datetime | null
  speakers: [string] | null
  projects: [string] | null
```

Aliases discovered during a run must record their evidence source and cannot silently become canonical forms.

### 7.2 EvidenceEvent

A normalized source occurrence.

```yaml
record_id: string
source_surface: string
source_locator: string
source_record_id: string | null
author: string | null
event_time:
  value: datetime | null
  precision: EXACT | SECOND | MINUTE | HOUR | DAY | MONTH | YEAR | RANGE | UNKNOWN
  start: datetime | null
  end: datetime | null
ingested_at: datetime | null
content_ref: string
content_hash: string | null
retrieval_method: EXACT | ALIAS | BACK_REFERENCE | SEMANTIC | VECTOR | GRAPH | MANUAL
raw_excerpt: string | null
metadata: object
epistemic_status: DIRECT_SOURCE | DOCUMENTED_METADATA | INFERRED | DISPUTED | UNKNOWN
limitations: [string]
```

`event_time` and `ingested_at` must remain separate.

### 7.3 OccurrenceAssessment

An interpretation of one evidence event relative to the target.

```yaml
record_id: string
relations:
  - EARLIEST_ACCESSIBLE_EVIDENCE
  - ORIGIN_CLAIM
  - FIRST_LITERAL_OCCURRENCE
  - CONCEPTUAL_ANCESTOR
  - DERIVATION
  - REUSE
  - REINTERPRETATION
  - FORMALIZATION
  - CORRECTION
  - SUPERSESSION
  - CONTRADICTION
  - CURRENT_MEANING
literal_match: EXACT | NORMALIZED | ALIAS | NONE
semantic_match: DIRECT | RELATED | WEAK | NONE
assessment_basis: [EvidenceRef]
confidence: HIGH | MEDIUM | LOW | UNRESOLVED
notes: string | null
```

### 7.4 LineageEdge

A typed relationship between records.

```yaml
edge_id: string
from_record_id: string
to_record_id: string
relation: INSPIRED | DERIVED_INTO | REUSED_AS | REINTERPRETED_AS | FORMALIZED_AS | CORRECTED_BY | SUPERSEDED_BY | CONTRADICTS | REFERENCES | CLAIMS_ORIGIN_IN
basis: [EvidenceRef]
epistemic_status: DIRECT | SUPPORTED_INFERENCE | HYPOTHESIS | DISPUTED
confidence: HIGH | MEDIUM | LOW | UNRESOLVED
```

Edges are directional and must respect chronology unless the relation is a retrospective reference.

## 8. Pipeline

### Stage 1 — Target normalization

Roots parses the request without strengthening it. If the user asks for the origin of a word, Roots must not silently broaden the task into the origin of the underlying concept. It may search conceptual ancestors as a separate lineage dimension.

Output: `TargetSpec`.

### Stage 2 — Candidate discovery

Discovery begins with literal and normalized exact search, then expands only as needed:

1. exact literal forms;
2. normalized literal forms;
3. evidence-backed aliases;
4. explicit citations/back-references;
5. semantic expansion;
6. optional vector retrieval.

Each candidate records how it was discovered.

### Stage 3 — Evidence normalization

Adapters map heterogeneous source records into `EvidenceEvent` objects.

Timestamp normalization must preserve uncertainty. A record dated only `2026-08` is not fabricated into `2026-08-01T00:00:00` for substantive ordering. It occupies a range.

### Stage 4 — Chronology construction

Events are sorted by their temporal bounds.

Where records cannot be totally ordered, Roots creates an explicit partial order / tie set rather than pretending precision.

### Stage 5 — Ascending review

The lineage analyzer starts from the earliest evidence set and proceeds forward.

At each event it asks:

- Is the target literally present?
- Is this only semantically related?
- Does the record claim an origin?
- Does it point to earlier evidence?
- Does it derive from an earlier event?
- Does it preserve or alter meaning?
- Does it correct or supersede something?
- Does it contradict the reconstructed lineage?

### Stage 6 — Back-reference expansion

If an event points backward to evidence not yet present, Roots attempts to resolve the reference.

If found, the new record is normalized, added, and the ascending review restarts.

A configurable loop guard prevents endless cycles. The receipt records expansion rounds and unresolved references.

### Stage 7 — Graph construction

Assessments become nodes and typed edges in the provenance graph.

Chronology is a constraint on the graph, not a replacement for it. A target can have multiple ancestors, competing origin claims, divergent reinterpretations, and later reconciliation.

### Stage 8 — Verification

Roots runs deterministic checks:

- chronology inversion;
- missing locators;
- duplicate records;
- hash mismatch where hashes are available;
- unsupported strong origin claims;
- semantic ancestor promoted to literal origin;
- unresolved back-reference;
- currentness without supersession evidence;
- conflicting direct evidence;
- receipt/source mismatch.

### Stage 9 — Receipt

The final trace is emitted as machine-readable data plus a concise human-readable rendering.

## 9. Receipt contract

A proposed `ProvenanceReceipt`:

```yaml
schema_version: 1
trace_id: string
target: TargetSpec
started_at: datetime
completed_at: datetime
sources:
  attempted: [SourceAttempt]
  available: [string]
  unavailable: [string]
coverage:
  earliest_event: datetime | null
  latest_event: datetime | null
  completeness: COMPLETE_RELATIVE_TO_ACCESSIBLE_SOURCES | PARTIAL | UNRESOLVED
result:
  earliest_accessible_evidence: [record_id]
  first_literal_occurrence: [record_id]
  conceptual_ancestors: [record_id]
  current_meaning: [record_id]
  origin_status: ESTABLISHED | EARLIEST_ACCESSIBLE_ONLY | MULTIPLE_CLAIMS | UNRESOLVED
lineage:
  nodes: [OccurrenceAssessment]
  edges: [LineageEdge]
conflicts: [Conflict]
gaps: [Gap]
unresolved_references: [Reference]
verification:
  checks: [CheckResult]
limitations: [string]
```

`origin_status=ESTABLISHED` should be deliberately hard to earn.

## 10. Source adapter interface

The first executable release should use a small adapter protocol:

```python
class SourceAdapter(Protocol):
    def discover(self, target: TargetSpec) -> Iterable[RawCandidate]: ...
    def resolve_reference(self, ref: Reference) -> Iterable[RawCandidate]: ...
    def normalize(self, candidate: RawCandidate) -> EvidenceEvent: ...
```

Initial adapters:

1. filesystem Markdown/text;
2. JSON/JSONL conversation/event records;
3. Git commit/history metadata where locally available.

Later adapters may include connector APIs, databases, and vector indexes.

## 11. AI bootstrap behavior

Roots is not only a library. It defines a method that an AI consumer can bootstrap when provenance matters.

Trigger examples:

- "where did this phrase come from?"
- "check provenance"
- "what is the history of this rule?"
- "when did we first decide this?"
- "trace how this idea changed"
- a configured sentinel term that explicitly requests historical reconstruction.

Behavior contract:

```text
1. Preserve the user's exact target and scope.
2. Invoke provenance retrieval before claiming origin/history.
3. Search for candidates broadly enough to expose backward references.
4. Normalize source metadata.
5. Reconstruct in ascending event chronology.
6. If later evidence points to earlier material, retrieve it and restart oldest-first.
7. Separate literal occurrence from conceptual ancestry.
8. Keep direct evidence distinct from inference.
9. Continue until the lineage is supported or the unresolved frontier is explicit.
10. Report oldest-accessible evidence as such unless origin is actually established.
```

The bootstrap contract must never claim that an AI can access hidden or unavailable records.

## 12. Failure semantics

Roots should fail visibly rather than hallucinate completion.

Suggested outcomes:

- `TRACE_COMPLETE_RELATIVE_TO_ACCESSIBLE_SOURCES`
- `TRACE_PARTIAL_SOURCE_UNAVAILABLE`
- `TRACE_PARTIAL_UNRESOLVED_BACK_REFERENCE`
- `TRACE_CONFLICTING_ORIGIN_CLAIMS`
- `TRACE_TEMPORAL_ORDER_UNRESOLVED`
- `TRACE_NO_EVIDENCE_FOUND`
- `TRACE_INVALID_SOURCE_METADATA`
- `TRACE_VERIFICATION_FAILED`

An otherwise useful lineage may still be returned with a partial outcome.

## 13. Privacy and authority

Roots can easily become a mechanism for searching personal or private history, so access boundaries are part of correctness.

- Adapters operate only on authorized sources.
- A source's presence in an index does not grant permission to expose it.
- Receipts should support redacted excerpts while preserving source locators internally where appropriate.
- Public fixtures must not be copied from private histories without explicit publication authority.
- Provenance reconstruction does not itself authorize mutation of source records.

## 14. Performance model

Correctness outranks speed, but Roots should avoid reading an entire corpus repeatedly.

The intended strategy is:

1. indexes discover candidates cheaply;
2. exact source records are loaded only for candidate verification;
3. chronology is rebuilt from normalized metadata;
4. semantic expansion occurs only when literal retrieval is insufficient or a back-reference requires it;
5. cached discovery indexes may accelerate later traces but remain rebuildable projections.

Indexes may be relevance-ranked. The lineage engine may not be.

## 15. Test strategy

### Unit tests

- timestamp normalization;
- partial-order chronology;
- literal normalization;
- source identity;
- duplicate detection;
- lineage-edge validation;
- receipt validation.

### Regression tests

Synthetic histories should prove that Roots rejects:

1. newest-first provenance;
2. search-rank-as-origin;
3. retrospective summary as primary origin;
4. conceptual ancestor as first literal occurrence;
5. unsupported derivation edge;
6. correction erasing earlier history;
7. ingestion order replacing event order;
8. duplicate paraphrases masquerading as independent support;
9. unresolved earlier reference being ignored;
10. current meaning being projected backward.

### Property tests

Useful invariants for property-based testing:

- shuffling ingestion order does not change the chronological lineage;
- adding a newer irrelevant record does not change the identified earliest evidence;
- adding an older valid candidate forces re-evaluation and can move the earliest-accessible boundary;
- removing source metadata can weaken a result but cannot strengthen it;
- duplicate copies do not increase evidentiary independence.

### End-to-end fixture

The first public fixture should be synthetic and contain:

- an early conceptual ancestor;
- a later coined phrase;
- a later summary claiming an origin;
- a back-reference to the earlier ancestor;
- a correction;
- a current formal definition;
- one missing reference.

Expected result: Roots distinguishes the conceptual ancestor, first literal occurrence, later formalization, and unresolved missing evidence without calling any one of them a stronger origin than the evidence supports.

## 16. Initial implementation boundary

Version `0.1` should intentionally remain small.

Deliverables:

- Python package;
- CLI;
- filesystem text/Markdown adapter;
- JSON/JSONL adapter;
- deterministic chronology engine;
- explicit evidence/event model;
- basic lineage graph;
- rule-based verification;
- JSON receipt;
- human-readable trace output;
- synthetic hostile fixtures;
- tests for all core invariants.

Model-assisted semantic classification should be behind an optional interface in v0.1. Roots must be useful without an LLM provider connection.

## 17. Future implementation directions

After v0.1 proves chronology and evidence integrity:

- semantic/model-assisted lineage classification;
- embedding-backed candidate discovery;
- GitHub/Drive/database/chat adapters;
- interactive provenance graph visualization;
- evidence bundle export;
- signed or hash-chained receipts;
- incremental indexing;
- cross-source identity reconciliation;
- confidence calibration against labeled fixtures;
- provider/runtime hooks that automatically invoke Roots on configured provenance triggers.

## 18. Repository structure

```text
README.md
pyproject.toml
src/roots/
  __init__.py
  model.py
  target.py
  discovery.py
  chronology.py
  lineage.py
  graph.py
  verification.py
  receipt.py
  cli.py
  adapters/
    __init__.py
    base.py
    filesystem.py
    json_records.py
schemas/
  evidence-event.schema.json
  provenance-receipt.schema.json
docs/
  methodology.md
  terminology.md
  superpowers/specs/
    2026-09-16-roots-provenance-engine-design.md
tests/
  fixtures/
  test_chronology.py
  test_lineage.py
  test_receipt.py
  test_regressions.py
```

## 19. Acceptance criteria for v0.1

A v0.1 candidate is acceptable only if all of the following are demonstrated by tests:

1. A corpus delivered newest-first is still interpreted oldest-first.
2. A late record referencing earlier evidence causes retrieval/restart rather than becoming the origin.
3. Earliest accessible evidence is not labeled proven origin without sufficient support.
4. Conceptual ancestry and first literal occurrence remain distinct.
5. Direct evidence and inferred lineage edges remain separately typed.
6. Missing source metadata weakens or blocks claims rather than being silently invented.
7. Corrections preserve the corrected historical record.
8. Conflicting origin claims survive as explicit conflict.
9. Receipt output is deterministic for a fixed normalized corpus.
10. Source order permutations do not change the result.
11. The CLI can trace a synthetic fixture end-to-end without an external model/API.
12. The final receipt reports accessible-source completeness and unresolved gaps.

## 20. Design summary

Roots should behave less like a search box and more like a careful historian with machine-enforced bookkeeping.

It searches broadly, but it does not reason from search order. It starts at the oldest accessible evidence, walks forward, follows backward references without skipping chronology, distinguishes literal origin from semantic ancestry, preserves corrections and conflicts, and reports when the actual root remains beyond the available record.

That is the foundation the first implementation should protect.
