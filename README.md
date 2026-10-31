> **License:** Source-visible, **not open source**. Original material is proprietary. Private noncommercial evaluation and review are permitted under [LICENSE](LICENSE); commercial use, redistribution, hosted use, and commercial derivatives require separate written permission. See [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md). Third-party components retain their own rights.

# Roots — evidence provenance tools

Roots is an experimental Python toolkit for finding candidate source records and representing the evidence needed to investigate where a claim, term, decision, or concept came from. Its central distinction is simple: **a search result is not proof of origin**.

The current product is a **local, read-only candidate-discovery CLI and Python evidence/verification library**. It can retrieve matching records and preserve their source metadata, but it does not yet reconstruct complete semantic lineages or prove historical origins.

## What is available

| Capability | Current implementation | Boundary |
| --- | --- | --- |
| Candidate discovery | `roots candidates` scans local Markdown/text or JSON/JSONL sources for literal/normalized matches | Results follow adapter discovery order, **not** proven historical order |
| Evidence normalization | Filesystem and JSON-record adapters produce typed evidence with record IDs, locators, timestamps when present, and content hashes | Missing or ambiguous metadata remains missing or ambiguous |
| Temporal comparison | Python helpers represent bounded/uncertain event times and identify earliest *accessible* candidates | Overlapping or unknown intervals are not arbitrarily ordered |
| Claim-strength validation | Typed receipts and `validate_receipt_claims` guard against unsupported completeness/origin assertions | Validation checks consistency of supplied evidence; it does not independently obtain evidence |
| Full lineage reconstruction | Architecture and adversarial-test design in `docs/` | **Not implemented** as a `trace`, `verify`, hosted service, vector search, or model-authenticated agent |

Roots is useful for local source review, data-provenance research, and building a provenance-conscious workflow around records an application is already authorized to read.

## Quick start

Requires **Python 3.12 or newer**. From a checkout of this repository:

```bash
python -m pip install -e .
roots --version
roots candidates "provenance" --source ./docs/methodology.md --limit 5
```

That example searches a repository document and emits JSON with a candidate's locator, source metadata, event-time precision, content hash, and limitations. Its output explicitly contains:

```json
{
  "operation": "candidate_discovery",
  "origin_status": "NOT_ASSESSED",
  "source_completeness": "UNKNOWN"
}
```

The JSON fragment shows selected fields, not an entire response. A match means only that a candidate was found in the specified input.

### Source formats and output controls

```bash
roots candidates "build decision" --source ./records.jsonl --limit 20
roots candidates "design note" --source ./notes --limit 20
roots candidates "release" --source ./notes/release.md --include-content
```

- A file may be `.md`, `.txt`, `.json`, or `.jsonl`. **Directory scans currently include only `.md` and `.txt`**, recursively.
- Repeat `--source` to search multiple sources. JSON records can supply fields such as `record_id`, `timestamp`, `speaker`, and `content`; missing fields are not guessed.
- Default output omits raw matched content. `--include-content` prints it to standard output, so use it only where the output destination is authorized.
- `--limit` accepts 1–1000 and limits **emitted candidates**, not the total files examined, bytes read, or CPU spent. A successful run does not establish source completeness.
- Search is literal/normalized in this executable seam; the broader semantic/vector approach described in design documents is not available through this CLI.

## Python integration

The package is `roots-provenance`; import names are under `roots`.

| Interface | Purpose | Source |
| --- | --- | --- |
| `TargetSpec` / `EvidenceEvent` / `ProvenanceReceipt` | Typed target, evidence, and receipt structures | [`src/roots/model.py`](src/roots/model.py) |
| `FilesystemAdapter` | Discover and normalize local Markdown/text records | [`src/roots/adapters/filesystem.py`](src/roots/adapters/filesystem.py) |
| `JsonRecordsAdapter` | Discover and normalize records from JSON/JSONL files | [`src/roots/adapters/json_records.py`](src/roots/adapters/json_records.py) |
| `compare_time_bounds` / `earliest_events` | Handle ordering with uncertainty and overlapping intervals | [`src/roots/time.py`](src/roots/time.py) |
| `validate_receipt_claims` | Check that a receipt's asserted completeness/origin strength matches its stated evidence | [`src/roots/verification.py`](src/roots/verification.py) |

These are source-level Python interfaces, not a stable remote API. Downstream callers must independently authenticate their actors, enforce permitted source scopes, and gate any effects.

## Provenance principles

Roots keeps several questions separate:

1. **Discovery:** Which records matched the request in the sources actually searched?
2. **Time:** Which events demonstrably precede others, and which have unknown or overlapping time bounds?
3. **Attribution:** Who supplied each record, where is the primary locator, and what was inspected?
4. **Inference:** Does evidence show literal reuse, conceptual ancestry, correction, or merely semantic resemblance?
5. **Completeness:** What requested sources were inaccessible, unsearched, or unresolved?

An oldest *accessible* match is not automatically the original occurrence. Later retrospective accounts are leads until corroborated against earlier primary records. A valid data structure, hash, or model-generated interpretation is not an independent truth or authorization certificate.

See [methodology](docs/methodology.md), [terminology](docs/terminology.md), the [AI bootstrap contract](docs/bootstrap-contract.md), and the [hostile test matrix](docs/hostile-test-matrix.md) for the research design and proposed future engine.

## Test and security posture

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

The test suite exercises candidate discovery, metadata/receipt constraints, disputed and incomplete evidence, uncertain interval ordering, and workspace-startup safety. It does **not** establish model reasoning quality or provenance over uninspected/private corpora.

**Security:** The CLI reads local paths available to its operating-system account and can reveal locators or matched content in JSON output. It is not an authorization service, path sandbox, disclosure filter, or safe unrestricted model tool. Hosts must control filesystem access, corpus size, actor/subject boundaries, and downstream publication. Historical source contained a concealed editor auto-task and disguised executable payload that were removed from the current tree; the safety tests check the current workspace configuration, not every old checkout or user's editor/host environment. See [SECURITY.md](SECURITY.md).

## Status and licensing

Current status: **v0.1 foundation / candidate discovery**, with a larger provenance engine still in design. There is no authenticated connector, live provider binding, origin-verification service, complete lineage graph, or deployed model integration.

Read the [contribution terms](CONTRIBUTING.md), [security policy](SECURITY.md), [source license](LICENSE), and [commercial terms](COMMERCIAL_LICENSE.md) before incorporating Roots elsewhere. Public visibility does not grant unrestricted reuse or redistribution.
