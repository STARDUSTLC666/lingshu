# Independent twelve-fix integration audit

Result: **PASS**. No integration blocker was found.

- Frozen integration head: `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`
- Frozen tree: `529e1e150aa2c05a2f5bee3126c4678a58695e21`
- Target baseline: `d74848fb33dbff1d719959df19d1266a1ac60f44`
- GitHub PRs #1469–#1480 were read back live; all twelve exact heads match
  their delivered local heads. The snapshot is `exact-pr-heads.json`.
- The integration worktree stayed clean and the frozen head/tree stayed
  unchanged. The audit only wrote files under this review output directory.

## Independent source reconstruction

For each PR, the audit computed its actual merge base with the target and
extracted the PR's net contribution. It then independently composed those
contributions with `git merge-file` in this output directory, beginning with
the target baseline. All **10 changed production Python files** match that
independent union byte for byte after LF normalization.

All **29 actually changed functions** additionally match the owning PR's
exact-head function both as a location-independent AST and as function text.
There are no changed functions with multiple owners; the shared modules hold
disjoint function changes:

- `core.py`: the old `LayeredStore.search_skills` change and the new decay
  helper/value/cycle changes are all intact.
- `physics.py`: old skew-box SAT and pendulum helpers, plus new
  `fit_circular`, are all intact. No PR overwrote another's function.
- Animation `eval.py`: old pendulum helpers and top-level-motions
  normalization/evaluation changes remain intact.

All **52 changed paths** are accounted for by the PR contribution union.
The additional **40 guard/fixture/benchmark/document/tool artifacts** match
their single exact owner or independent three-way composition exactly.
The two registration files are checked separately below.

Important merge-base distinction: PR #1469's head predates the target's
camera fix and its actual merge base is
`6e9c90bfcba1bfb7c14cdf526611501d526f6777`. A two-dot comparison against the
newer target would falsely include a `world3d.py` camera reversal. GitHub's
actual PR file list excludes that file. The integration correctly preserves
the target camera fix and contains only the motion-group net contribution.

Evidence: `audit-summary.json`, `pr-*-production.patch`,
`three-way-reconstruction/`, `artifact-union.json`.

## Registrations

- Independently flattened both manifests and recomputed every source's LF
  SHA-256 and any registered byte count: **64/64 match**. Record sets and all
  non-hash/size registration metadata match the target baseline.
- The time-lint baseline contains **23 entries before and after**. Matching
  `(path, rule, actual source-line text, comment)` as a multiset proves only
  line positions changed; no exemption was added, removed, or reassigned to
  different code. Historical baseline comments remain present.
- A read-only lint execution reports **23 registered / 0 new / 0 stale**,
  exit 0. Raw result: `time-core-lint.json`.

## Scoped execution

The four new guards were executed once on the frozen integration, with
`-B`, no pytest cache, and a separate output-directory basetemp:

**165 passed / 4.57 seconds / 0 failures / 0 errors / 0 skips.**

This did not modify source or run mutation/replay tooling concurrently with
the full gates. Raw output: `new-four-165.log` and `new-four-165.xml`.

Four additional small public-path probes passed in one integrated process:

1. The same engine retains five negative-limit skill hits while fresh-row
   decay agrees exactly with an independent post-birth closed form.
2. Epoch-shifted circular prediction has maximum coordinate error
   `2.842170943040401e-14` and residual RMS `8.266171889940315e-15`.
3. Pendulum release agrees with an independent 8,192-step RK4 solution to
   `3.1086244689504383e-15` radians for the fixed probe input.
4. An independent eight-vertex projection finds a positive skew-box gap
   `0.03214809930113154`; integrated SAT correctly returns no overlap.

Raw data: `crossfix-probe.json`; the log retains expected optional-component
discovery warnings rather than hiding them.

## Boundary

This audit verifies exact composition and the specified scoped tests/probes.
It does not substitute for the separately running complete Windows gate or
the Linux CI matrix and makes no new claim about unavailable original assets.
