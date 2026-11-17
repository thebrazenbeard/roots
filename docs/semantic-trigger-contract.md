# Bounded semantic provenance triggers (source-only)

The module `roots.triggers` implements one **pre-answer decision seam** for a host
that wants to look up provenance when an important concept is expressed with
new wording. It does **not** make Roots a memory system, transcript provider,
agent runtime, semantic embedding service, or origin verifier.

## What the code actually does

An operator supplies reviewed `TriggerRule` definitions. Each rule has a
stable concept ID, a provenance search query, a **symbolic** corpus scope key,
explicit paraphrases and/or two or more independently required meaning groups.
When the utterance contains a paraphrase or every group appears inside a
bounded token window, `resolve_provenance_trigger` returns a lookup request.

This is a deliberately narrow form of semantic *candidate detection* based on
configured concept combinations. It handles some nonliteral rephrasings and
word-order changes without claiming unrestricted language understanding.
It neither embeds text nor proves that the utterance has the same meaning as
the source query. New concepts and paraphrases need reviewed rules. False
positives remain possible; all matches have candidate-only status.

Example (illustrative source scope; **not** an access grant):

```python
from roots.triggers import TriggerRule, TriggerStatus, resolve_provenance_trigger

council = TriggerRule(
    concept_id="inner-council",
    query="Inner Council provenance",
    scope_key="authorized-conversation-history",
    phrase_forms=("Inner Council",),
    semantic_groups=(
        ("inner", "internal", "within"),
        ("council", "committee", "advisers"),
    ),
)
decision = resolve_provenance_trigger(
    "What became of that internal committee we talked about?",
    (council,),
    allow_lookup=True,  # host-reviewed opt-in; NEVER a corpus permission
)
if decision.status is TriggerStatus.LOOKUP_REQUESTED:
    # Host MUST separately authenticate the actor and resolve authorized
    # source bindings before reading any record or producing a grounded claim.
    pass
```

## Required host route

1. **Before composing the answer**, preserve the user's verbatim proposition,
   scope, privacy request and exact command grammar. Handle opt-outs by passing
   `allow_lookup=False`.
2. Evaluate an operator-reviewed, version-pinned rule set. An unresolved or
   ambiguous decision means **do not automatically select a provenance target**.
3. If exactly one concept requests lookup, resolve `scope_key` through the
   host's current authenticated corpus registry. A string key is not
   authorization. Denied, missing or stale bindings stop the lookup.
4. Use Roots' authorized local source adapters to discover candidates,
   preserving original user text separately from the canonical search query.
   Never infer a ChatGPT-wide history connector from this package.
5. Evaluate privacy class, ownership, source authenticity, timestamp precision,
   correction/supersession, independent corroboration, and missing source scope
   before answering. Candidate results do not establish origin, identity,
   current memory or runtime consumption.
6. Cite retrievable authorized primary records when available; otherwise say
   what could not be verified. Do not publish private locators or message bodies
   into public PRs, logs or training sets.

**Control/action boundary:** Semantically similar text may trigger a *lookup*
but never a control action. A quoted `restore yourself`, a paraphrase of
`center yourself`, or a historical assistant claim cannot authorize state
restoration, saving, training, installation or other effects.

**Current deployment boundary:** As of the reviewed main commit
`e21884602b3c1955d76c5adc09025da7ef508357`, Roots has a local,
read-only candidate CLI but no complete transcript corpus, authenticated
host connector, vector search or native ChatGPT pre-answer interception.
This module becomes automatic **only after** a separate authorized host
runtime invokes it and implements the source-admission checks above.

## Ambiguity and failure policy

- Two concepts match: `AMBIGUOUS`; return all bounded IDs, never choose one.
- Duplicate IDs or too-large input/rule sets: `UNRESOLVED`, without reading.
- Explicit opt-out: `SUPPRESSED`, even when the phrase matches. The
  bounded source check also detects common direct denial forms (such as
  "Do not search our history") even if a host mistakenly opts in. It is not
  a complete natural-language negation detector.
- A quoted name inside an example is ignored unless the surrounding unquoted
  text explicitly indicates history/provenance intent. Quoting alone is not
  authority or lookup intent; complex quoted speech remains ambiguous and
  requires host-level adjudication.
- No reviewed pattern: `NO_TRIGGER` means no configured trigger, **not**
  that relevant history does not exist.
- One match: `LOOKUP_REQUESTED` means metadata-only route request, not
  successful retrieval, origin determination, memory admission or authority.

> **Hostile challenge:** Because concept groups use configured lexical
> alternatives, two unrelated subjects mentioning the same words can fire a
> false positive. Candidate-only status and independent source validation are
> mandatory. This is not a substitute for authenticated archival retrieval or
> independent semantic verification.

Tests: `python -m pytest -q tests/test_triggers.py`; run the full
`python -m pytest -q` suite before promotion. The presence of tests in a PR
does not mean those tests ran successfully.
