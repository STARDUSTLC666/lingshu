# Portable public evidence staging

Product source: `0f7427549406ad125d7efc95da5ceece052e616d`. Product tree: `0f33bd5642db088a459aebd6750cc1c68715f10e`.
This directory is a prepared review artifact; publication is owned by the supervisor.

The final source combines sixteen recorded contribution histories. Final targeted
acceptance is **165 passed, 0 failed, 0 skipped**. The **1,415 passed, 0 failed,
0 skipped** combined suite belongs to the earlier total13 source `513ce31bd2666a012a583a1b265015d9d58c4926`;
it is preserved separately and is not attributed to the final source.

The exact-final-source [Linux full gate](https://github.com/STARDUSTLC666/lingshu/actions/runs/44881541272) has three successful jobs.
Each records 6,415 passed, 44 skipped and 206 passed subtests. The three published
job logs are redacted derivatives of the original raw logs. The complete parsed
proof retains the skip nodes and real-brain results. The [installed acceptance](https://github.com/STARDUSTLC666/lingshu/actions/runs/44881630492)
uses workflow head `10eda1344d9df4b34c288e4236f222b3df2e79e7`, explicitly checks
out the product source above and verifies its tree. Its recorded Ubuntu/Windows
wheel checks, four authentic historical-physics guards and 48 activation guards
are distinct from the three default Linux gates and their skips.

The final installed pixel probe records four actual RGB recognition results,
World3D projections and persisted/reopened memory read/search results. Its scope
is synthetic single-object RGB. Controlled oracle-derived noise tests and
synthetic benchmark compatibility do not establish real-camera or multi-object
accuracy, production memory quality or a general performance improvement.

Windows full-gate status at staging: **terminal evidence included**.
Read `windows-status.json`. The terminal final run records **6,434 passed,
1 failed, 24 skipped and 206 passed subtests**. Its `gate_ok` remains **false**.
The sole failure is the existing #498 Windows symlink platform assertion; the
supervisor separately reproduced it on exact clean current main `23ba01eb8dfcb1a8dfdddd030cf7a2e3c078e8e9`.
Its `main-symlink.xml/log` and `main-symlink-provenance.json` preserve the failure,
return code1 and unchanged source identity. All 102 script invocations
exit zero, the real brain script records23/23, the controlled timing rerun4/4,
and manifest/time lint exit zero. Product and brain snapshots remain unchanged.
Older PR1485 Windows results in its historical receipt are separate records.

| Evidence | Source | Outcome |
| --- | --- | --- |
| Linux three full-gate jobs | final product source | each6415 passed,44 skipped,206 subtests passed |
| Windows full pytest | final product source | 6434 passed,1 failed,24 skipped,206 subtests passed |
| Windows102scripts / real brain | final product source | 102 exits0 /23of23 |
| Current-main symlink reproduction |23ba01e |1 failed; same existing POSIX assertion |

## Review map

- `final-integration/freeze.json` and `acceptance-fixed.*`: final165 source and results.
- `all-integration/combined-*`: earlier total13 suite, all case records and warnings.
- `final-integration/independent-audit/source-audit.json`: sixteen ancestors,
  unchanged guard assertions and documented constant/classification reconciliations.
- `full-gate-verified.json`, `full-gate-raw-proof.json` and the three
  `full-gate-job-*.log` files in that audit directory: exact-source Linux results.
- `artifact-audit.json`, contract JUnit/logs and per-platform installed summaries:
  wheel/blob/RECORD, isolated CLI, pip-check, PNG and installed asset evidence.
- `installed-pixel-report.json` and `replay/installed_pixel_probe.py`: installed RGB path.
- `final-integration/world-bench/`: full before/after JSON, comparisons and audit.
- `coordination/`: timestamped coordination snapshots, which may retain earlier
  running/pending wording. These historical snapshots do not override terminal
  result records elsewhere in this package.
- `intake-receipt.json` and `extended-gate/intake-receipt.json`: existing PR1485/1486
  submission readbacks, not new bounty submissions or maintainer acceptance.

## Provenance and transformation

`manifest.json` records every source locator, exact source head, public run links,
original SHA256, published SHA256, byte counts and the applied transformations.
Only entries explicitly marked `byte_identical: true` preserve original bytes.
Original evidence files were read without modification and rehashed after staging.
Hashes embedded inside copied audit reports still refer to the ORIGINAL artifacts;
use this manifest's `published_sha256` to verify the public derivative. Redacted
copies are not proof of byte-for-byte original logs or API-authenticated downloads.

Known local repository, output, runtime, user-home and temporary prefixes become
logical tokens such as `${REPO_FINAL}`, `${EVIDENCE_ROOT}`, `${CI_REPO}` and
`${CI_RUNTIME}`. Remaining host prefixes receive deterministic logical tokens.
Machine hostnames, environment blocks and JSON environment-dump fields are omitted;
package-index URLs/lines and signed or credentialed URLs are removed. JSON requiring
redaction is reserialized. Test outcomes, source IDs, timings and error/skip messages
are preserved except for those explicit path/privacy transformations.

No venv, database, temporary tree, package index, wheel, ZIP archive or environment
dump is included. Raw downloaded ZIPs and exported historical source bytes are not
part of this package. The contracts artifact itself omitted the exported historical
tree; its runtime checks, original blob identity table and logs remain the recorded
evidence. Maintainer review, merge and settlement remain pending separately.

## Replay entry points

Use a checkout with the recorded Git history and install the declared dependencies.
The unchanged benchmark source snapshots are under `replay/bench`; the wrapper
checks their LF hashes against the supplied checkout before running its source:

```text
python replay/run_benchmark.py --repo CHECKOUT --kind world --output RESULT.json
python replay/run_benchmark.py --repo CHECKOUT --kind world-inference --output RESULT.json
python replay/audit_world_bench.py --repo CHECKOUT --evidence final-integration/world-bench --output REAUDIT.json
```

For full gates and isolated installation, the tracked source provides
`tools/testing/extended_body_acceptance.py` and its `selftest`, `contracts` and
`wheel` subcommands. The original installed pixel probe is included unchanged;
create its clean wheel-installed venv inside `replay/`, remove inherited
`PYTHONPATH`, and run that venv's interpreter with `-I replay/installed_pixel_probe.py`.
It creates a new DB/report beside itself and refuses an existing DB. These are
replay instructions, not claims that the staging task reran the production suite.
