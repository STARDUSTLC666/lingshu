# Round-two body repair delivery — verified evidence

The four new PRs1477–1480 and corresponding bounty intakes2791–2794 were submitted and read back. This delivery batch is complete; the continuous contribution goal remains active. Prior eight submissions are retained, not duplicated.

Frozen combined production source: `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`; tree `529e1e150aa2c05a2f5bee3126c4678a58695e21`.

- New guards165 pass; all27 named mutants are rejected by their exact semantic assertions with no errors/skips. Baseline failures and every intermediate sample are retained.
- Each new PR's three complete Linux gate legs and title check pass at its exact head; `remote-ci/` includes full job logs and API identities.
- Complete combined Linux run44764384747: each of three environments5827 passed/40 skipped/98 subtests,102 script tests and actual pinned brain23/23.
- Complete Windows gate:5838 passed/**1 known baseline symlink-capability P1 failure**/28 skipped/98 subtests;102 scripts, serial timing4, strict manifest64/64 and time lint23registered/0new/0stale. Original `gate_ok=false` remains. Source1634 files and brain are unchanged.
- The same isolated P1 assertion fails on original d74848 baseline under actual Windows symlink capability. Historical-baseline physics supplement43 passes, original symlink bodies3/3 pass, and controlled timing4 passes; these overlap and are not added to the main counts.
- Index-clean Linux benchmark run44778606930, metadata `ff22bf03a53e422fedc029fbd0d24445aef3dbe7`, measured production source `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`: three environments each run all four A/B benchmarks and27 mutants. Source hashes, XML assertions, all timings and allocations are independently verified; all indexed lengths/hashes match after the final summary is written.
- First Linux run44766869622 is retained as intermediate: actual measurements passed; only live driver.log's old inner-index digest was stale. Original data was not rewritten.

Independent integration reconstruction confirms ten production files and29 changed functions equal the twelve PR patch union;52 paths are attributable and old camera fixes remain.

All raw timing samples, allocation peaks, negative baseline/mutant results, skipped and unexecuted checks remain visible. Shared-host numbers are descriptive, not speed claims.17 original model/pixel-asset cases remain unavailable; assets are not fabricated.

## Evidence layout

- `audit-core`, `audit-circular`, `audit-world`, `audit-numeric`: all local scoped iterations.
- `integration-independent`: independent patch/function/manifest/lint audit.
- `cross-model-box-invariance`:108 public-API scenes,648 ticks,3024 checks per source; fixed0 failures, baseline602. This metamorphic test complements independent analytic freefall checks, not exhaustive physics proof.
- `integration-windows`, `windows-supplements`: original full-gate failure and separate supplements.
- `remote-ci`: exact PR/combined source jobs and complete logs.
- `linux-benchmarks/intermediate-44766869622`, `linux-benchmarks/final-44778606930`: all original iterations and final clean inventory.
- `publication-receipts`: initial intake readbacks; final immutable-link readbacks are appended separately.

Path/home prefixes become `[workspace]` and `[user-home]`; line endings are LF. JSON numeric leaves and XML content are checked before/after. Source and public canonical Git blob digests are both recorded. Compressed convenience copies are represented by original archive digests while extracted outputs are preserved. All overlapping runs must not be summed.

The public manifest excludes only itself and detached sealing audits to avoid self-reference. Bytecode, databases, temporary environments, full third-party issue bodies and aggregate dumps are excluded.

## Current PR1478 synchronization after upstream merges

Upstream main `04e0ecb6a3669c90efbb4a1583816a8f7ca26bc7` merged our prior PRs1469/1473/1474. The PR1478 merge `41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50` imports those previously delivered fixes; conflict resolution changes only the core manifest fingerprint. Fresh-decay functions remain unchanged, and its entire core module is byte-identical to frozen combined source `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`. The original89-head measurements remain historical and are not relabeled. New exact-head gate44781318899 and title pass, each gate5638 passed/40 skipped/98subtests,102 scripts and actual brain23/23. No new bounty is claimed; intake2792 remains the single contribution. See `core-main-sync/`.
