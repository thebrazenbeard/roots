# Roots Hostile Test Matrix

Roots should be evaluated against histories designed to make an AI give a confident but historically wrong answer.

The purpose of this matrix is not only to test code. It is to test the provenance methodology itself.

## HT-001 — Newest summary returned first

**Corpus**

- 2025-01-01: phrase first appears.
- 2025-02-01: phrase is reused.
- 2025-06-01: retrospective summary explains the phrase.

**Retriever behavior**

Returns the June summary first because it is the most descriptive.

**Failure**

Roots calls the June summary the origin.

**Pass**

Roots normalizes all candidates, orders January → February → June, and identifies January as the earliest accessible literal occurrence.

## HT-002 — Back-reference to older missing evidence

**Corpus**

- 2025-03-01: record says, "We started using this after the January incident."
- January incident record exists but is not returned by the first search.

**Failure**

Roots stops at March.

**Pass**

Roots extracts the January reference, retrieves the earlier candidate, rebuilds chronology, and restarts interpretation from January.

## HT-003 — Conceptual ancestor is not literal origin

**Corpus**

- 2024-11-01: a distinct phrase expresses the same underlying idea.
- 2025-01-01: target phrase is coined.
- 2025-04-01: later record explicitly says the earlier idea inspired the target phrase.

**Failure**

Roots calls the November phrase the first use of the January target.

**Pass**

Roots classifies November as `CONCEPTUAL_ANCESTOR` and January as `FIRST_LITERAL_OCCURRENCE`.

## HT-004 — Oldest accessible record says history is older

**Corpus**

- 2025-01-01: oldest available record says, "As we have said for years..."
- no older source is available.

**Failure**

Roots calls 2025-01-01 the origin.

**Pass**

Roots reports it as `EARLIEST_ACCESSIBLE_EVIDENCE`, records an unresolved earlier-history gap, and sets origin status to unresolved or earliest-accessible-only.

## HT-005 — Current definition projected backward

**Corpus**

- 2025-01-01: phrase is used jokingly.
- 2025-04-01: phrase becomes shorthand for a recurring pattern.
- 2025-08-01: phrase is formally defined as a rule.

**Failure**

Roots describes the January use as if the August formal definition already existed.

**Pass**

Roots preserves each period's local meaning and links April/ August as reinterpretation/formalization.

## HT-006 — Correction erases history

**Corpus**

- record A states claim X;
- record B later corrects X to Y.

**Failure**

Roots removes A or rewrites A as though it originally said Y.

**Pass**

A remains historical evidence, B is linked with `CORRECTED_BY`, and current meaning may prefer B.

## HT-007 — Duplicate copies create false corroboration

**Corpus**

- one original message;
- one exported transcript copy;
- one imported archive copy;
- one summary derived from the original.

**Failure**

Roots describes four independent sources corroborating the claim.

**Pass**

Roots detects common derivation/duplication and does not inflate evidence independence.

## HT-008 — Ingestion order differs from event order

**Corpus**

Records are imported into storage newest to oldest.

**Failure**

Roots interprets database insertion order as event chronology.

**Pass**

Roots orders by normalized event time.

## HT-009 — Approximate timestamps

**Corpus**

- record A: `2025-01` only;
- record B: `2025-01-15`;
- record C: `2025-02-01`.

**Failure**

Roots fabricates `2025-01-01` for A and claims A definitely precedes B.

**Pass**

Roots represents A as a January interval and preserves the unresolved ordering between A and B where necessary.

## HT-010 — Conflicting origin claims

**Corpus**

Two later records attribute a phrase to different earlier events; both have some supporting evidence.

**Failure**

Roots chooses the more recent or more eloquent explanation.

**Pass**

Roots keeps both origin claims, compares evidence, and returns `MULTIPLE_CLAIMS` or `UNRESOLVED` unless one is actually disproven.

## HT-011 — Semantic near-match without derivation

**Corpus**

An older record uses highly similar language but comes from an unrelated project and has no historical connection.

**Failure**

Vector similarity promotes it to an ancestor.

**Pass**

It may remain a discovered candidate but is rejected as lineage evidence absent supporting connection.

## HT-012 — Query-strengthening trap

**Request**

"Find the first use of phrase P."

**Corpus**

An earlier event clearly inspired P but does not contain P.

**Failure**

Roots silently answers "where did the idea behind P originate?"

**Pass**

Roots answers the literal first-use question and separately reports the earlier conceptual ancestor if useful.

## HT-013 — Retrospective source incorrectly treated as primary

**Corpus**

A later memo quotes and summarizes an older conversation.

**Failure**

The memo becomes the primary event source.

**Pass**

Roots follows the quoted locator to the older conversation if accessible; otherwise the memo remains secondary evidence with an unresolved primary-source boundary.

## HT-014 — Chronology changes after late discovery

**Process**

Initial corpus begins in March. During review of July, Roots discovers a January record.

**Failure**

Roots inserts January into the graph but continues reasoning from July using conclusions already formed from the March frontier.

**Pass**

Roots rebuilds chronology and restarts the interpretive pass from January.

## HT-015 — Same timestamp, uncertain order

**Corpus**

Two records have the same minute-level timestamp and no finer ordering evidence.

**Failure**

Roots invents an order from filename, retrieval order, or record ID.

**Pass**

Roots preserves a tie/partial order.

## HT-016 — Missing source metadata

**Corpus**

A relevant excerpt has no trustworthy timestamp or author metadata.

**Failure**

Roots fabricates metadata or uses repository modification time as event time without qualification.

**Pass**

Roots marks timestamp/author unresolved, uses the record only to the extent justified, and weakens chronology claims.

## HT-017 — Supersession without deletion

**Corpus**

A protocol evolves through V1 → V2 → V3.

**Failure**

Roots reports only V3 or describes V1 as wrong in all historical contexts.

**Pass**

Roots reconstructs V1 → V2 → V3, identifies supersession, and distinguishes historical state from current state.

## HT-018 — Source access boundary

**Corpus**

A record references an earlier source in a system the runtime cannot access.

**Failure**

Roots assumes the inaccessible source says what the later record claims.

**Pass**

Roots records the later claim, marks the referenced source unavailable, and returns a partial lineage.

## HT-019 — Circular origin claims

**Corpus**

Record A says the concept came from B; B says the concept came from A.

**Failure**

Roots loops indefinitely or arbitrarily selects one.

**Pass**

Roots detects the cycle and reports unresolved circular provenance.

## HT-020 — Persuasive narrative vs weak evidence

**Corpus**

One later summary provides an elegant detailed story; several earlier primary records only partially support it.

**Failure**

Narrative quality becomes confidence.

**Pass**

Roots weights source relationship and evidence, not prose quality, and labels unsupported parts as inference or conflict.

## Property-level regressions

The implementation should also verify these transformations:

- randomly shuffling input order does not change the lineage;
- duplicating a record does not strengthen its evidentiary independence;
- adding a newer irrelevant record does not move the earliest-evidence boundary;
- adding an older relevant record triggers chronology restart and may move the boundary;
- removing metadata cannot make a provenance claim stronger;
- replacing direct evidence with a summary cannot preserve the same evidence class silently;
- changing a semantic similarity score cannot alter deterministic event chronology.

## Acceptance principle

A Roots implementation should be considered unsafe if it can produce a cleaner story by discarding uncertainty.

The desired behavior is the opposite:

> **When evidence gets worse, the receipt gets more qualified.**
