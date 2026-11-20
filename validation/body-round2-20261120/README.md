# Round-two evidence — core/circular slice

This staged directory contains all four stable local scoped audit sets.
Combined integration and remote CI validation will be added later.
It does not assert that the full round-two batch or its release gates are complete.

See `source-status.json` for exact baseline, measured and final PR heads. Core
production measurements remain applicable after the manifest-only final commit;
the canonical production blobs were compared byte for byte. The initial stale
manifest was observed in terminal output, without a saved raw file. The final
strict JSON is retained as 64/64; there is no reconstructed initial raw result.

`audit-core` includes the fresh-decay reproduction, all raw A/B latency and
traced-memory samples, test logs/JUnit, all initial/final replay iterations,
and scoped peer-review history. Initial zero-collection output and expected
baseline/mutant failures are retained. Known activation/CSR findings were
excluded from new claims; early spatial review output is historical, not a
claim about its final later source. `audit-circular` retains both complete
benchmark rounds, independent analytic-oracle failures and fit errors, unexecuted
prediction checks, relevant test skips, mutation runs and lint iterations.

`audit-world` and `audit-numeric` retain all R1 and R2 measurements, including
intermediate failed or incomplete validations. Numeric's final guard is 70
tests with baseline 59 failed / 11 passed and six killed mutants; intermediate
43/27 results are not final. Its final replay is `r2/replay-final-verified`.
World's final R2 guard has 41 tests and six named mutants. Both raw A/B rounds
are retained. Active PR-CI captures and the complete Windows/Linux repository
gates are deliberately deferred to the subsequent integration evidence slice.

No databases, virtual environments, aggregate all-issue dumps, or complete
third-party issue/PR bodies/comments are copied. Search inputs containing bodies
are projected to identifying title/URL/state metadata, with original file hashes
for provenance. Literal nonstandard NaN JSON in historical peer-review output
is preserved with a `.json.raw.txt` suffix rather than mislabeled as strict JSON.

Local workspace and user-home prefixes become `[workspace]` and `[user-home]`;
text line endings are LF. JSON numeric leaves and XML semantic content were
compared before/after sanitization. Every published artifact digest in
`sanitization-manifest.json` is checked against the actual staged Git blob,
not an assumed working-tree newline representation. `junit-index.json` keeps
each run's original counters; its overlapping runs must not be summed.

The preparation tool is under `tools/`. Its inputs are the private output root
containing `audit-core`/`audit-circular` and this isolated evidence checkout.
It stages only this directory and does not commit or push. The manifest and
audit report exclude themselves from their digest list to avoid self-reference.

`replay-sources` contains the exact-head benchmark scripts, regression guards,
mutation specifications and scoped reports, plus the unchanged baseline replay
tool. Run the committed benchmark scripts against clean baseline/fixed source
checkouts as their command help describes. `duplicate-title-url-index.json`
consolidates identifying metadata from the body-containing search inputs.
