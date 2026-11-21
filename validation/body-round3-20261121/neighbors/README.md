# Neighbors public evidence slice

Final local implementation head: `4a352249ef6db7975353b84bc640712d46f7181b`
(PR #1481). The paired Windows benchmark actually measured clean
`df0838c2181abf5fb1dc8e1e4b0dfcb66c19a232`; the final documentation commit did
not change source/guard/spec/benchmark. Historical delivery status remains
unchanged in its original metadata even though the parent later published.

The 30 hash-bound delivery artifacts are all retained. `initial04/` preserves
the original clean04 point-cloud probe, report and red baseline output.
`original04-guard-replay/` is explicitly a later replay of the unchanged final
guard against exact original04 source: 19 behavior failures/11 passes versus
30 fixed passes. It is not relabeled as having run during the initial audit.
The relevant source is byte-identical between04 and the accepted6b baseline.

JSON sanitization changes string tokens only, including dictionary keys;
all non-string tokens and numeric lexemes are byte-identical after any explicit
metadata projection. Projection keeps selected metadata/counts and body hashes,
using Decimal-preserving serialization, and withholds all issue/comment bodies
and author/user payloads. `initial04/HEXGRID_NEIGHBORS_AUDIT.md` is our own
historical analysis; references to full private snapshots name their original
audit storage, not files included in this public slice. The public versions of
those snapshots are metadata/body-hash projections under `dedup/`.

XML structure/text after path redaction and exact numeric attributes are
verified after serialization. Absolute workspace/user/runner paths become
placeholders. Standalone probe path placeholders need the target checkout
configured before use. Helpers are retained and accept explicit source/repo/
output arguments; reuse copied only world helper functions and did not edit
the world helper, world slice, production tree or frozen round-two evidence.

`public-index.json` lists every included artifact's raw/public byte count and
SHA256, projection state and checks. It excludes itself and this explanatory
README to avoid self-reference. No complete issue/comment body, baseline/brain
tree, database/cache, ZIP archive or full old body aggregation is included.

This slice contains adjacent Windows tests and historical probes, not a whole
Windows gate. Original `full_repo_gate_rerun=false` is preserved. Separate
remote full-gate CI and combined Linux benchmark artifacts belong to the
parent's distinct verified packets; they are not fabricated or mixed here.
Odd-r correction has measured timing cost1.302–1.637x; tracemalloc describes
Python allocations, not RSS/native memory. CNN's old image segments4–6 remain
skipped because the upstream image asset was not exported.
