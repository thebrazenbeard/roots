# Roots AI Bootstrap Contract

This document defines the behavioral contract for an AI system using Roots. It is intentionally separate from the executable engine so the methodology can be integrated into different runtimes without pretending that prompt behavior and engine enforcement are the same thing.

## Trigger conditions

Roots should activate when the current task materially depends on historical provenance, origin, derivation, or semantic lineage.

Common triggers include:

- "check provenance";
- "where did this come from?";
- "what was the first use of this phrase?";
- "trace the history of this rule";
- "how did this idea change?";
- "when did we first decide this?";
- a configured sentinel/provenance flare;
- an internal uncertainty where a current claim depends on historical continuity.

Roots should not activate merely because a topic has history. The provenance question must matter to the answer.

## Precondition

The AI must distinguish:

- records currently accessible to the runtime;
- records mentioned but not accessible;
- records inferred to exist;
- records outside current authority.

Roots does not grant new access.

## Required turn behavior

When triggered, the AI should follow this sequence:

```text
ROOTS_BEGIN
  1. Capture the user's literal target and requested scope.
  2. Do not silently strengthen, broaden, or substitute the target.
  3. Search authorized records for literal candidates.
  4. Expand semantically only as needed and label the expansion.
  5. Collect source metadata and normalize event time.
  6. Order evidence oldest → newest.
  7. Begin interpretation at the oldest accessible evidence.
  8. Follow later back-references to earlier candidates.
  9. If earlier evidence is found, rebuild chronology and restart oldest-first.
 10. Distinguish:
       - earliest accessible evidence
       - first literal occurrence
       - conceptual ancestor
       - origin claim
       - proven origin
 11. Preserve correction, supersession, conflict, and current meaning as separate states.
 12. Keep source facts separate from model inference.
 13. Stop only at a supported lineage or an explicit unresolved frontier.
 14. Emit scope/completeness and evidence-backed conclusions.
ROOTS_END
```

## Forbidden shortcuts

An AI using Roots must not:

- answer from the newest relevant result merely because it summarizes older history;
- treat search rank as chronology;
- call the oldest available result the origin without qualification;
- treat semantic similarity as derivation;
- collapse conceptual ancestry into literal first use;
- skip a referenced earlier record because the later summary sounds sufficient;
- project current meaning backward;
- erase an earlier state after correction;
- convert a hypothesis into direct evidence;
- imply hidden access to unavailable records;
- stop solely because the narrative feels coherent.

## Back-reference obligation

If a later record says or implies:

> this came from X

then the AI has a retrieval obligation for X when X is within authorized accessible scope.

The later statement can be retained as an `ORIGIN_CLAIM` or `REFERENCES` edge, but it does not close the trace.

If X cannot be retrieved, the result must retain that unresolved boundary.

## Chronology restart rule

A Roots trace is not a one-pass newest-to-oldest archaeology.

When a newly discovered source predates the current chronological frontier:

```text
ADD candidate
→ NORMALIZE candidate
→ REBUILD chronology
→ RESTART interpretation from oldest accessible evidence
```

The restart is mandatory because the new source may change the interpretation of every later record.

## Semantic discipline

The AI should distinguish at least three different matching questions:

1. **Literal:** is the target itself present?
2. **Referential:** does the record refer to the same entity/event/claim under different wording?
3. **Ancestral:** did an earlier concept or event contribute to the target without being the target?

A positive answer to one does not imply a positive answer to the others.

## Confidence discipline

Suggested language mapping:

- `DIRECT_SOURCE` → "The record shows..."
- `SUPPORTED_INFERENCE` → "The evidence supports..."
- `HYPOTHESIS` → "A plausible possibility is..."
- `DISPUTED` → "The accessible sources conflict..."
- `UNRESOLVED` → "The record does not establish..."

Roots should avoid certainty language stronger than the receipt state.

## Completion discipline

A provenance answer is complete only relative to the source boundary actually checked.

Preferred completion language:

> "The earliest accessible evidence in the checked sources is..."

Stronger language such as:

> "This is the origin"

requires stronger evidence.

## Minimal bootstrap form

For constrained runtimes, the smallest useful Roots bootstrap is:

```text
Preserve the exact target. Retrieve broadly, then sort evidence by event time ascending. Review oldest-first. Follow backward references and restart if older evidence appears. Distinguish earliest accessible evidence, first literal occurrence, conceptual ancestry, and origin claims. Keep inference typed. Report gaps and source scope.
```

## Relationship to the executable engine

The bootstrap contract guides behavior. The engine should enforce what it can deterministically enforce:

- timestamp handling;
- ordering;
- source identity;
- restart state;
- receipt fields;
- explicit relation types;
- verification checks.

Neither layer should pretend to replace the other.
