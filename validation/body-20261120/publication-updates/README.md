# Existing PR/intake publication updates — 2026-11-20

All 14 authorized existing bodies were updated and individually read back:

- Upstream lingshu PRs 1469–1475.
- Existing dsh-bounty intakes 2783–2789.
- No new issue or PR was created by this publication pass.

The immutable evidence revision used in every new section is:
`a9fe000938a536134f4a21f83b4a633afe8413e5`, under
`validation/body-20261120` in STARDUSTLC666/lingshu.

## Preservation and scope

Each original intake:v1 header was retained byte for byte. Original narratives,
regression descriptions, external references and remaining scope limits were
preserved. Only stale performance scope, alpha replay/count wording and the
math related-suite total were surgically amended outside the added section.

Each target has exactly one idempotent block bounded by:

```text
<!-- body-validation-20261120:expanded:start -->
<!-- body-validation-20261120:expanded:end -->
```

The publication script refuses unexpected body drift and verifies each remote
body after editing it. Re-running it against the unchanged prepared target skips
the write. It does not issue claims, bounty labels, settlements, merges or source
commits.

## Content corrections

- Each suite records the supplied actual baseline/fixed assertion counts, the
  exact current head, its three successful Python CI legs and title check, and
  immutable correctness/latency/memory/portable-usage links.
- Alpha now records 25 guards, 73 vision tests and ten named mutants. The default
  committed fixture uses prior head fb8eaada (6 failed / 19 passed). The original
  d74848fb replay explicitly uses the published original-baseline variant
  (15 failed / 10 passed). The old wrong pairing and 4/52 counts were removed.
- Novelty's actual reconstruction cost is explicit: mixed 5,000-node latency
  14.247467 to 241.756767 ms (16.968x), pure append 13.859820 to 16.157400 ms,
  and mixed traced peak 1,043,015 to 12,038,190 bytes (11.542x).
- Pendulum records head e0771a810b8846676f3545542b2e70d5e0011467,
  55 related passed / 4 skipped including #455, body/bridge guards 6+8,
  eleven mutants, 6,550 angle/phase checks, 69 periods, 2,165 cn comparisons,
  eight domain checks, exact physics source 271d2bb9... and runner f0c163e8....
- The pendulum scalar report explicitly has no dedicated memory measurement;
  no six-suite memory value was misrepresented as a pendulum measurement.
- Shared-host timing, traced/native allocation limits, synthetic-only data,
  real-assets/Blender/GPU exclusions, existing local symlink/manual P1 failures,
  and absence of a final eight-fix r2 completion count remain explicit.

## Verification and backups

`publication-results.json` contains 14 verified readbacks and seven unchanged
intake headers. `final-checks-summary.json` confirms all seven PR heads unchanged,
all three Python gates successful, each latest title check successful and every
PR CLEAN after body publication.

Per target the directory preserves:

- `*-original.json/md`: inspected initial body and metadata.
- `*-submitted.md`: exact submitted text.
- `*-prewrite.json`: body drift/head check immediately before the write.
- `*-edit-result.json`: exit code, stdout and stderr.
- `*-readback.json/md`: the remote result verified immediately after the write.
- `pr-*-final-checks.json`: final source-head and CI checks.

The prepared/publication scripts, original/prepared summaries and pinned public
reports used to select the measurement values are also preserved here.
