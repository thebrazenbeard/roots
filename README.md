> **License:** Source-visible, not open source. Original material is proprietary. Commercial use, redistribution, hosted-service use, and commercial derivative products require written permission. See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md). Separately identified third-party components retain their own licenses.

# roots

**Roots** is an AI provenance-reconstruction system: a bootstrapping behavior, methodology, and eventually executable engine for reviewing authorized records to locate the earliest accessible evidence for a word, phrase, claim, decision, event, concept, or other referent and reconstruct how it changed over time.

The repository starts from a simple observation: **search is not provenance**.

A search engine can find a relevant result. A provenance checker has to answer a harder set of questions:

- What is the target, literally and semantically?
- What is the earliest accessible evidence for it?
- Is that evidence the origin, or only the oldest thing currently available?
- What earlier conceptual ancestors are related without being the same thing?
- How did later uses derive from, reinterpret, formalize, correct, supersede, or contradict earlier ones?
- Which links are directly evidenced, which are inferred, and which remain unresolved?
- What does the target mean now, and how does the current meaning relate to its history?

Roots is intended to make those questions systematic enough that an AI can perform them reliably on its own accessible records rather than relying on vague recollection or relevance-ranked search results.

## Core idea

Roots treats provenance as a **temporally ordered evidence graph**.

Candidate evidence may be discovered by lexical search, semantic search, metadata, links, references, embeddings, or model reasoning. Discovery order does **not** determine provenance order. Once candidate evidence is collected, Roots normalizes timestamps and source identities, then reviews the evidence from **oldest to newest**.

The default provenance walk is:

```text
TARGET
  ↓
NORMALIZE LITERAL + SEMANTIC REFERENT
  ↓
DISCOVER CANDIDATE RECORDS
  ↓
NORMALIZE SOURCE / TIME / SPEAKER / LOCATOR
  ↓
SORT OLDEST → NEWEST
  ↓
REVIEW ASCENDING CHRONOLOGY
  ↓
CLASSIFY EACH OCCURRENCE
  ↓
LINK DERIVATIONS / CORRECTIONS / SUPERSESSIONS
  ↓
CHECK GAPS / CONFLICTS / BACK-REFERENCES
  ↓
RECONSTRUCT LINEAGE
  ↓
EMIT PROVENANCE RECEIPT
```

A newer record that says "this came from an earlier event" is a **lead**, not proof that the earlier event has been found. Roots follows the lead backward to candidate evidence, adds that evidence to the corpus, and then restarts the interpretive walk from the oldest accessible point.

## Non-negotiable invariants

Roots should eventually enforce these as executable contracts:

1. **Ascending chronology is mandatory for interpretation.** Candidate discovery may happen in any order. Provenance reconstruction does not.
2. **Oldest accessible evidence is not automatically the origin.** If earlier evidence may be missing, the result must say so.
3. **Literal occurrence and semantic ancestry are different relations.** A concept can inspire a phrase without being the first use of that phrase.
4. **Relevance is not lineage.** Semantic similarity can discover candidates but cannot establish derivation by itself.
5. **Later claims about earlier history are leads until corroborated.** A retrospective statement is not a time machine.
6. **Speaker, source, timestamp, and locator remain attached to evidence.** Provenance without provenance metadata is storytelling.
7. **Direct evidence and inference stay typed separately.** Roots may infer a likely derivation, but it must not rewrite inference as documented fact.
8. **Corrections and supersessions do not erase history.** The old state remains part of the lineage even when it no longer governs current meaning.
9. **Gaps remain gaps.** Roots should report unresolved intervals instead of inventing connective tissue.
10. **Current meaning is a terminal interpretation, not the starting assumption.** The system must reconstruct how the target arrived there.

## Evidence classes

An occurrence can have more than one relation, but Roots should distinguish at least:

- `EARLIEST_ACCESSIBLE_EVIDENCE` — oldest evidence currently available to the run.
- `ORIGIN_CLAIM` — a record explicitly claiming an origin; not automatically verified.
- `FIRST_LITERAL_OCCURRENCE` — earliest verified occurrence of the exact or normalized literal target.
- `CONCEPTUAL_ANCESTOR` — earlier concept, phrase, event, or pattern that materially contributed to the target without being the target itself.
- `DERIVATION` — evidence that one occurrence developed from another.
- `REUSE` — later use preserving substantially the same meaning.
- `REINTERPRETATION` — later use assigning materially different meaning.
- `FORMALIZATION` — informal material turned into an explicit rule, label, protocol, or definition.
- `CORRECTION` — later evidence correcting an earlier representation.
- `SUPERSESSION` — later state replaces earlier state as current without deleting history.
- `CONTRADICTION` — evidence cannot be reconciled without preserving a conflict.
- `CURRENT_MEANING` — best-supported present interpretation within the requested scope.

## Why not just use embeddings?

Embeddings are useful for finding semantically related evidence, especially when wording changed. They are not a provenance authority.

A semantically similar old record may be unrelated. A highly relevant recent record may describe an earlier event but not contain the origin. A later correction can embed almost identically to the statement it supersedes. Roots therefore treats vectors as an **optional discovery index**, while chronology, source metadata, explicit links, and evidence typing govern reconstruction.

## Proposed architecture

Roots is designed as a hybrid of deterministic provenance machinery and an AI-facing behavioral/bootstrap layer.

### 1. Target parser

Accepts a word, phrase, event description, claim, identifier, or semantic referent and creates a `TargetSpec` containing:

- literal forms;
- normalized forms;
- aliases supplied by evidence;
- semantic description;
- scope constraints;
- requested source surfaces;
- optional time bounds.

### 2. Source adapters

Read authorized records without assuming one storage system. Candidate adapters include:

- chat/conversation exports;
- Markdown/text archives;
- Git history;
- structured JSON/JSONL;
- database/event-ledger projections;
- API or connector search results;
- optional vector indexes.

Adapters return normalized evidence records rather than making provenance judgments.

### 3. Candidate discovery

Uses exact search first where possible, then aliases, citations/back-references, semantic expansion, and optional vector retrieval. Discovery should optimize **recall**, not decide the answer.

### 4. Evidence normalizer

Converts heterogeneous records into a common event schema with:

- record ID;
- source surface;
- source locator;
- author/speaker;
- event timestamp and timestamp quality;
- raw excerpt or content reference;
- content hash where available;
- retrieval method;
- confidence and limitations.

### 5. Chronology engine

Orders evidence using normalized event time, not search rank or ingestion time. Ties and uncertain timestamps stay explicit. Records with only approximate dates occupy bounded intervals rather than fabricated exact positions.

### 6. Lineage classifier

Classifies what each occurrence is doing relative to the target and earlier evidence. The first implementation can be rule-assisted + model-assisted, but every classification should carry evidence and confidence.

### 7. Provenance graph

Stores occurrences as nodes and typed relationships as edges, for example:

```text
conceptual ancestor ──INSPIRED──▶ phrase
phrase ──REUSED──▶ later phrase
later phrase ──FORMALIZED_AS──▶ rule
rule ──CORRECTED_BY──▶ amended rule
amended rule ──CURRENT_AS──▶ current meaning
```

The graph preserves chronology while allowing provenance to branch instead of forcing every history into one linear story.

### 8. Contradiction and gap analyzer

Checks for:

- mutually incompatible origin claims;
- back-references to evidence not yet retrieved;
- suspicious chronology inversions;
- missing source locators;
- gaps between claimed derivation steps;
- later summaries masquerading as primary evidence;
- semantic ancestors accidentally promoted to literal origins.

### 9. Receipt generator

Produces both human-readable and machine-readable output containing:

- target;
- corpus scope;
- earliest accessible evidence;
- first literal occurrence if established;
- conceptual ancestors;
- chronological lineage;
- current meaning;
- unresolved gaps/conflicts;
- evidence used;
- inference edges;
- completeness statement.

### 10. AI bootstrap contract

Roots should also define behavior for an AI using the system:

```text
WHEN provenance/origin/history/derivation matters:
  invoke Roots before asserting lineage
  collect broadly
  reconstruct oldest → newest
  distinguish accessible-oldest from proven origin
  preserve literal vs semantic identity
  cite evidence at every material transition
  stop only when lineage is supported or explicitly unresolved
```

This behavioral contract is deliberately separate from the engine. Prompt instructions alone are fallible; engine logic alone cannot decide every semantic relationship. Roots is intended to combine both.

## Potential implementation

The first executable version should be deliberately small: a local Python package and CLI that can ingest a directory of timestamped text/JSON records and reconstruct provenance for a query.

A future interface could look like:

```bash
roots trace "target phrase" --source ./records
roots trace "target phrase" --source ./records --format json
roots trace "event description" --source ./records --semantic
roots verify receipt.json
```

The initial implementation should prioritize deterministic chronology and evidence bookkeeping over sophisticated AI inference. Semantic/model-assisted classification can be added behind an interface so it never becomes the sole authority for ordering or source facts.

## Planned repository layout

```text
README.md

docs/
  methodology.md
  terminology.md
  superpowers/specs/
    2026-09-16-roots-provenance-engine-design.md

src/roots/
  model.py
  target.py
  adapters/
  discovery.py
  chronology.py
  lineage.py
  graph.py
  verification.py
  receipt.py
  cli.py

schemas/
  evidence-event.schema.json
  provenance-receipt.schema.json

tests/
  fixtures/
  test_chronology.py
  test_lineage.py
  test_receipts.py
  test_regressions.py
```

Executable source is intentionally not claimed yet. This README is the architecture target for the first implementation.

## First adversarial test family

Roots should be built against histories that deliberately tempt a model into the wrong answer. Synthetic fixtures will cover cases such as:

- search returns the newest summary first;
- the newest summary names an older source that must still be retrieved;
- an earlier concept inspires a later phrase but is not its literal origin;
- two records make conflicting origin claims;
- the oldest accessible record explicitly says it is repeating something even older that is unavailable;
- a correction supersedes a statement without deleting its historical role;
- several near-duplicate paraphrases create false confidence;
- timestamps are missing, approximate, or tied;
- ingestion order differs from event order;
- semantic similarity is high but derivation is unsupported.

A system that merely finds a convincing-looking match should fail these tests. A Roots result should survive them.

## Status

`FOUNDATION / DESIGN`

Roots currently has an approved architectural direction and is being populated as a design-first project. It does **not** yet claim an executable provenance engine, complete source adapters, model integration, provider deployment, or guaranteed access to any AI system's private/internal records.

## Design principle

> **Find broadly. Order historically. Distinguish evidence from inference. Follow the lineage all the way to the root—or say exactly why the root is still unknown.**
