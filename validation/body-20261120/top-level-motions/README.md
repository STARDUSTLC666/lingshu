# Top-level animation motions repair

PR: https://github.com/FuRongJun-1999/lingshu/pull/1476
Bounty intake: https://github.com/FuRongJun-1999/dsh-bounty/issues/2790
Head: `1ab5cc7f295ed5748b50c7ffde26cf2a34663204`.
Baseline: `d74848fb33dbff1d719959df19d1266a1ac60f44` (latest fetched origin/main).
Checkout: `[workspace]\lingshu\work\lingshu-body-top-level-motions-20261120`.
Python: `[workspace]\lingshu\work\lingshu-body-20261120-venv\Scripts\python.exe`.

## Scope and source

The public animation API documents spec['motions']; _motions_by_link reads it,
but the frozen geometry validator rejects the unknown key. Animation normalize
now removes only the top-level extension from its already converted copy before
calling the original geometry validator. Explicit motions, including [], keep
priority. Caller inputs and nested/other unknown keys retain their contracts.
No geometry schema or physics formula changed.

The portable guard, six-mutant declaration and successful-path timing/memory
probe are committed in the PR. The isolated runner prepares declared source
parents and otherwise retains its exact failure/count/assertion/exit checks.
Its directory preparation matches the parallel pendulum PR byte for byte.

## Recorded results

- New public guard: 30 passed, zero errors/skips.
- Original source with the same guard: exactly 23 failed / 7 passed, zero errors/skips.
- Six named mutations: each killed only by the selected test/assertion.
- Related tests in fresh per-file processes: 194 passed / 4 skipped; one CI-style script succeeded.
- Strict manifest: 64/64 match. Time-core lint: 23 existing / 0 new violations.
- Source compilation and diff whitespace check passed.
- Three complete CI gates plus the title check passed on the exact head above.
  Each Python leg reports 5,606 passed / 40 skipped, plus 98 subtests passed.
  Complete job logs and extracted terminal summaries are preserved as ci-*.log
  and ci-test-summaries.json. The skips are explicit; they are not counted as passed.
- Intake 2790 was created only after all three gates passed. Its intake:v1 PR
  link and the fixed public evidence link were read back and verified. No bounty
  label, claim or settlement was self-issued.

Fixed public evidence snapshot (source/bench/regression/replay evidence):
https://github.com/STARDUSTLC666/lingshu/tree/7bf90b7d0dcdc61140e4000eccd5a159da3f39e1/validation/body-20261120/top-level-motions
Both the PR and intake link this snapshot and the exact remote CI jobs.

`related-suite.log/xml` preserve an initial custom aggregated subset with 20
old bridge-family import failures caused by lingshu._pathguard refusing the
bridges namespace under that subset's import order. The same 20 tests pass in
their isolated file (`family-isolated.log/xml`). No pathguard change was made.
The first per-file attempt also exposed the existing script-style test_issue825
having zero pytest tests (exit 5). The final harness follows SCRIPT_TESTS from
gate.yml and runs it as a script. These exploratory results are retained;
`related-final/summary.json` is the final correct-style run.

The four skips are explicit cases in test_issue427_shade_paint_guard.py and
are preserved in its JUnit. They are not counted as passed. The new guard and
all fixed/baseline/mutation replays contain zero skips.

## Timing and allocation measurements

benchmark/summary.json includes every trial and source hash. Separate Python
-S workers test baseline_parameter, fixed_parameter and fixed_top_level.
Seven trials each contain 200 successful eval_at calls after 50 warmup calls.
The baseline top-level input is probed only for the expected SpecError, not
timed as if it were successful work.

| Links/motions | Baseline parameter us | Fixed parameter us | Fixed top-level us |
| ---: | ---: | ---: | ---: |
| 1 | 14.65 | 16.83 | 19.14 |
| 16 | 173.90 | 153.90 | 181.06 |
| 64 | 576.40 | 564.31 | 653.24 |

All successful paths produce equal pose SHA-256 fingerprints at each size.
The top-level input includes copying its extension metadata. Values describe
this Windows/CPython machine and workload; no speed threshold is asserted.
At 64 links, tracemalloc retained delta after 1,000 calls and GC is 364 B for
each worker, with peak near 73.3–73.4 KB. These are sample allocation readings,
not a proof of absence of leaks for arbitrary inputs.

## Duplicate search

duplicate-search.json preserves nine GitHub CLI title/body queries across
upstream issues, upstream PRs and dsh-bounty. Exact motions/normalize_spec
queries had no results. Broader animation searches returned 43 upstream issues
and 28 PRs. Bounty bridge and top-level searches were each capped at 100;
their relevant candidates did not describe this root cause. recent-prs.json
also preserves the 100 most recently updated upstream PRs, reviewed for the
exact extension/normalization path. The source still actively documents and
implements the fallback; no deprecation or superseding fix was found.
This is a time-bounded search, not a claim that every historical comment was
exhaustively reviewed.

## Reproduction

From the checkout, use the Python runtime above:

```text
-B -X utf8 -m pytest tests/test_bridge_top_level_motions.py -q
-B -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/bridge_top_level_motions_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output <new-replay-directory>
-B -X utf8 tools/testing/bench_bridge_motions.py --repo . --output <new-benchmark-directory>
-B -X utf8 tools/verify_manifest.py --strict --quiet
-B -X utf8 tools/time_core_lint.py
```

For the local related-file run, call evidence/run_related_checks.py with --repo
set to the checkout and --output set to a new directory. All chosen commands,
stdout, JUnit and the final aggregate are preserved by the harness.
