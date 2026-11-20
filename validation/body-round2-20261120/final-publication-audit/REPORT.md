# Independent prepublication index audit

**PASS** for the frozen original evidence seal. The evidence tree was not
modified, and no repository tests, benchmark jobs, or CI runs were started.

- Audited metadata HEAD: `ff22bf03a53e422fedc029fbd0d24445aef3dbe7`.
- Measured production source: `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`.
- Index snapshot SHA-256:
  `0f98e75b85108d098eb9cad18e2ec7e56d15d33ba0aa3429f9a5ac8f2a6a6301`.

## Canonical blobs and coverage

All **1,580 manifested artifacts** were read directly from their immutable
Git index object IDs. Both recorded canonical SHA-256/length and published
SHA-256/length match each blob. The **1,583 evidence files** have no missing
or unexplained unmanifested files; only these three self-describing metadata
files are excluded:

- `final-seal-audit.json`
- `preparation-audit.json`
- `sanitization-manifest.json`

All **259 JSON and 314 XML** files parse. The seven control Python files parse
as ASTs, and the restricted staged control-script format check passes. No
compiled Python, database, cache/index files or actual private workspace/home
prefixes remain. The two previously exposed `skip_reasons` object keys are
explicitly checked and clean. Original patch/log whitespace was preserved
and was not treated as a global format gate.

## Independent semantic checks

- Windows original XML and log retain **5,838 passed / one existing symlink
  assertion failure / 28 skipped / 98 subtests**. `gate_ok` remains `false`.
  The XML's reported test count includes 98 subtests in addition to its actual
  `<testcase>` elements; the audit checks both representations.
- The three exact-source combined Linux raw logs retain **5,827 passed /
  40 skipped / 98 subtests each**, 102 script groups each, and successful
  exact-source `5226860` jobs.
- The four intake markers and receipts map PRs **1477/1478/1479/1480** to
  intakes **2791/2792/2793/2794** and their recorded exact measurement heads.
  These are historical receipt snapshots. In particular, old PR1478 head
  `89c005b...` is not represented as a future/current post-merge head.
- Final benchmark run **44778606930** is completed/successful in its raw API
  snapshot at metadata head `ff22bf03...`. All three provenances separately
  identify production source `5226860...`; declared measured input hashes
  match the corresponding immutable Git blobs.
- All ten outer commands per environment exited zero; their original stdout
  and stderr stream hashes match.
- All **27 named mutations per environment (81 total)** were reconstructed
  independently from the exact source and committed specs. Their source hashes
  match the captured hashes, each original XML has exactly the named failing
  assertion, and none has errors/skips. Fixed and baseline guard counts match
  their exact declared cases.

## Original artifact inventories and sanitization

The three untouched original inner indexes enumerate **137 / 136 / 136** files
(floor / py312 latest / py313 latest), **409 files total**. Every original
file's raw SHA-256 and length matches its original index and the outer
manifest's original-file metadata. There are no missing indexed files.
`driver.log` is the only additional inner file and is explicitly excluded as
a live tee by each original index; the outer canonical manifest covers it.

The audit independently compares numeric/bool/null values and JSON structural
shape for **231 original/published JSON pairs**, covering **143,695 numeric or
boolean leaves**. This includes 56 final-benchmark JSON pairs with 41,819 such
leaves. Third-party metadata projections are intentionally excluded from a
verbatim-tree comparison, while their canonical hashes remain checked.

One mutable local original, `remote-ci/summary.json`, changed after its copied
snapshot was recorded. The audit does not compare the newer mutable aggregate
against the older frozen snapshot as though they were the same capture.
The frozen snapshot's canonical blob and its underlying original CI evidence
and claimed results were checked independently and pass.

## Files

- `audit-summary.json`: all canonical blob checks and semantic evidence.
- `extra-inventory-and-api.json`: complete inner inventories and final API
  state, plus sanitization comparison counts.
- `audit_final_index.py`: independently implemented verifier.

This conclusion applies to the frozen index above. A later PR1478 head/CI
alignment append requires a separate scoped verification; it does not alter
the authenticity of these historical measurements.
