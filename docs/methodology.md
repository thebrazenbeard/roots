# Roots Methodology

Roots is designed to reconstruct provenance from accessible evidence without confusing search relevance, chronology, semantic similarity, and historical authority.

This document describes the method independently of any one implementation.

## 1. Preserve the target before searching

The first job is not search. It is referent control.

Roots should record exactly what is being traced:

- literal word;
- phrase;
- concept;
- event;
- claim;
- decision;
- rule;
- identifier;
- other scoped referent.

If the request is for the origin of a phrase, Roots must not silently replace that with the origin of the underlying concept. If the request is for an event, Roots must not quietly answer with the first time someone later described the event.

The target may have multiple dimensions, but they remain typed separately.

## 2. Discovery is broad; interpretation is strict

Roots permits broad discovery because historical evidence often changes wording.

Candidate discovery may include:

- exact string matching;
- normalized forms;
- known aliases;
- named entities;
- explicit references;
- source links;
- semantic search;
- embeddings;
- graph traversal;
- model-suggested related terms.

None of those methods establishes historical order or provenance by itself.

Discovery answers:

> What records might matter?

Provenance reconstruction answers:

> What happened first, what followed, and what evidence connects them?

## 3. Normalize before interpreting

Every candidate should be normalized into an evidence record with, where available:

- stable record ID;
- source type;
- source locator;
- speaker or author;
- event timestamp;
- timestamp precision;
- ingestion timestamp;
- raw content or content reference;
- retrieval method;
- source hash;
- limitations.

Event time and ingestion time are never interchangeable.

If event time is uncertain, uncertainty must be represented rather than hidden.

## 4. Build the chronological frontier

The initial evidence set is ordered by event time from oldest to newest.

If exact ordering is impossible, Roots should produce a partial order. For example, two records that can only be dated to the same month may occupy the same temporal band.

The earliest record in this ordered set becomes the initial `EARLIEST_ACCESSIBLE_EVIDENCE` candidate. It is not automatically an origin.

## 5. Review oldest first

Interpretation begins at the oldest accessible evidence and advances forward.

This direction matters because later records often contain retrospective explanations that are cleaner than the history itself. Reading newest-first encourages current meaning to contaminate earlier evidence.

For each record, Roots asks:

1. Is the target literally present?
2. Is the target only semantically related?
3. Is the record describing something earlier?
4. Is it making an origin claim?
5. Does it cite or imply an earlier source?
6. Does it preserve the prior meaning?
7. Does it change the meaning?
8. Does it formalize an informal use?
9. Does it correct an earlier statement?
10. Does it supersede an earlier current state?
11. Does it contradict the reconstructed lineage?

## 6. Follow backward references without reasoning backward

A later record may reveal earlier material that was not found during initial discovery.

When this happens:

1. extract the reference;
2. attempt to resolve it;
3. add any newly found source evidence;
4. rebuild chronology;
5. restart interpretation from the oldest accessible evidence.

This distinction is central to Roots.

A provenance investigation may *discover* backward. It should still *reason* forward.

## 7. Distinguish roots that are often conflated

Several different things can look like "the origin":

### Earliest accessible evidence
The oldest record available to the current run.

### First literal occurrence
The oldest verified record containing the literal or normalized target itself.

### Conceptual ancestor
An earlier idea, event, phrase, or pattern that plausibly contributed to the target.

### Origin claim
A record asserting where something originated.

### Proven origin
A stronger conclusion supported by sufficient evidence across the available record.

Roots should prefer the weakest claim justified by evidence.

## 8. Preserve changes in meaning

Meaning can evolve.

A phrase may begin as a joke, later become shorthand, then become a formal rule. Roots should not flatten those uses into one timeless definition.

Each occurrence should be interpreted in its own historical context, then linked forward.

Useful relations include:

- `INSPIRED`
- `DERIVED_INTO`
- `REUSED_AS`
- `REINTERPRETED_AS`
- `FORMALIZED_AS`
- `CORRECTED_BY`
- `SUPERSEDED_BY`
- `CONTRADICTS`
- `REFERENCES`

## 9. Keep evidence and inference separate

A source can directly show:

- a phrase was used;
- a timestamp;
- an author;
- a claim about origin;
- an explicit reference.

A model may infer:

- that one phrase inspired another;
- that two events refer to the same episode;
- that a later definition formalized an earlier informal pattern.

Those are useful inferences, but they must remain labeled as inferences unless corroborated.

Roots should never upgrade a plausible story into source fact because it makes the lineage cleaner.

## 10. Detect false provenance confidence

Roots should actively look for confidence traps:

- many copies of one source;
- repeated paraphrases of the same claim;
- summaries derived from each other;
- imported archives duplicating a conversation;
- current documentation citing earlier current documentation rather than primary evidence;
- semantic similarity without historical connection.

Evidence independence matters more than raw hit count.

## 11. Handle correction and supersession

Corrections do not erase earlier history.

If record B corrects record A:

- A remains part of the provenance graph;
- B receives a `CORRECTED_BY` relationship from A;
- current interpretation may prefer B;
- historical reconstruction still reports A as the earlier state.

The same rule applies to supersession.

## 12. Stop conditions

A Roots run may stop when one of these conditions is reached:

### Supported lineage
The requested lineage is reconstructed with sufficient evidence and no unresolved material back-references.

### Accessible frontier reached
The oldest accessible evidence has been found, but it itself points to earlier unavailable history. Result remains partial.

### Source boundary
Required sources are unavailable or unauthorized.

### Irreducible conflict
Two or more origin claims remain supported and cannot be reconciled.

### No evidence
The target cannot be found in the authorized corpus.

Roots should not stop merely because a result sounds convincing.

## 13. Output discipline

A useful provenance answer should usually contain:

1. target;
2. source scope;
3. earliest accessible evidence;
4. first literal occurrence, if different;
5. conceptual ancestors;
6. chronological derivation;
7. corrections / supersessions / conflicts;
8. current meaning;
9. unresolved gaps;
10. completeness statement.

The human-readable answer may be concise, but the machine-readable receipt should retain the full evidence map.

## 14. Bootstrap behavior for AI systems

An AI using Roots should follow this compact behavior:

```text
PROVENANCE TRIGGER
  preserve exact target
  search authorized records
  normalize evidence
  order oldest → newest
  review chronologically
  follow backward references
  restart if older evidence appears
  separate literal origin from conceptual ancestry
  preserve evidence/inference distinction
  expose gaps/conflicts
  report scope and completeness
```

The system should treat unusual user-supplied provenance keys, sentinel phrases, and exact-history commands as retrieval triggers when that behavior has been explicitly configured.

## 15. Methodological maxim

> **Discovery can move in any direction. Provenance interpretation moves from the oldest accessible evidence forward.**
