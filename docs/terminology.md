# Roots Terminology

Roots depends on precise distinctions. These terms are normative for the first implementation unless a later reviewed spec supersedes them.

## Target

The exact referent being traced. A target can be a word, phrase, concept, claim, decision, event, rule, identifier, or another explicitly scoped entity.

## Candidate

A record discovered as potentially relevant to the target. A candidate is not yet accepted as lineage evidence merely because retrieval ranked it highly.

## Evidence event

A normalized record occurrence containing source identity, locator, time information, content reference, retrieval method, and epistemic metadata.

## Event time

The time the represented utterance, event, decision, or source occurrence actually happened, to the precision supported by evidence.

## Ingestion time

The time a record entered an archive, index, database, or other storage system. Ingestion time is not event time.

## Earliest accessible evidence

The oldest evidence currently available to the run after source normalization and chronological ordering.

This does not by itself establish historical origin.

## Origin

The earliest point at which the target can be established to have arisen within the scope of the provenance question.

`Origin` is a strong claim. Roots should prefer `earliest accessible evidence` when the record cannot rule out missing earlier history.

## Origin claim

A source statement asserting that something originated in a particular place, event, record, or cause. It remains a claim until supported.

## First literal occurrence

The earliest verified evidence containing the target itself or an explicitly accepted normalized form.

## Conceptual ancestor

An earlier concept, phrase, event, behavior, or pattern that contributed to the later target but is not itself the target.

A conceptual ancestor may predate the first literal occurrence.

## Derivation

An evidence-supported relationship showing that a later occurrence developed from an earlier one.

## Lineage

The evidence-supported sequence and graph of derivations, reuses, reinterpretations, corrections, supersessions, contradictions, and formalizations connecting historical occurrences of a target.

## Provenance graph

The directed graph whose nodes are evidence occurrences or assessments and whose edges are typed lineage relationships.

## Chronology

The temporal ordering of evidence by event time.

Roots uses chronology as a hard interpretive constraint while allowing the provenance graph itself to branch.

## Discovery order

The order in which a retrieval system happens to find evidence. Discovery order has no provenance authority.

## Search rank

A relevance score or ranking supplied by a retrieval system. Search rank can help discovery but cannot establish chronology or origin.

## Back-reference

A later record that refers to an earlier source, event, phrase, or state.

A back-reference creates a retrieval obligation. It does not substitute for the referenced evidence.

## Restart

The required Roots behavior when newly discovered earlier evidence changes the chronological frontier: rebuild the ordered corpus and interpret again from the oldest accessible point.

## Reuse

A later occurrence that preserves substantially the same meaning or function of an earlier occurrence.

## Reinterpretation

A later occurrence that materially changes the meaning, function, or referent of an earlier occurrence.

## Formalization

The transformation of an informal phrase, pattern, convention, or practice into an explicit definition, rule, protocol, label, schema, or documented method.

## Correction

A later record that explicitly or substantively repairs an earlier representation.

Correction does not erase the corrected record from history.

## Supersession

A later state replaces an earlier state as current while preserving the earlier state as historical evidence.

## Contradiction

Two evidence claims cannot both be accepted under the same referent, scope, and time interpretation without further reconciliation.

## Current meaning

The best-supported present interpretation of the target within the requested scope.

Current meaning is reconstructed from history; it is not projected backward onto earlier evidence.

## Direct evidence

Information directly present in an accessible source record or authoritative metadata.

## Supported inference

A conclusion not explicitly stated by one source but reasonably supported by multiple pieces of evidence.

## Hypothesis

A proposed lineage or interpretation that remains insufficiently supported.

## Evidence independence

The degree to which multiple records represent genuinely distinct sources rather than copies, paraphrases, summaries, imports, or common derivations from one source.

## Gap

A missing or unresolved interval in the lineage where a causal, semantic, or historical connection is claimed or suspected but not adequately evidenced.

## Conflict

An explicit state in which competing evidence-supported interpretations cannot yet be reconciled.

## Partial order

A chronological structure used when some records can be ordered relative to each other but exact total ordering is unsupported.

## Provenance receipt

The machine-readable result of a Roots trace containing the target, searched source scope, evidence set, lineage graph, conflicts, gaps, verification results, and completeness classification.

## Completeness

The degree to which a Roots result accounts for the authorized and technically accessible source surfaces relevant to the target.

Completeness is always relative to source access; it is not a claim that no unknown external evidence exists.

## Bootstrap contract

The AI-facing behavior that triggers and governs provenance reconstruction: preserve the target, retrieve evidence, sort oldest-first, follow back-references, distinguish evidence from inference, and report unresolved boundaries.

## Sentinel

A distinctive configured word, phrase, identifier, or pattern whose presence is intended to trigger a specific provenance lookup or regression check.

## Provenance flare

An intentionally distinctive token or phrase chosen so later systems can retrieve a specific historical lineage with low ambiguity. This is a useful informal concept; implementations may represent it as a configured sentinel.

## Roots rule of thumb

> If a later record says where something came from, Roots has found a clue—not necessarily the root.
