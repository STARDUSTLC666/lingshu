# Thirteen-contribution local integration freeze

Final source: `513ce31bd2666a012a583a1b265015d9d58c4926` on `validation/global-all-20261121`.
Worktree: `${REPO_TOTAL13}`. Git status is clean. All thirteen supplied contribution
heads are ancestors of this commit; their exact IDs are in `combined-summary.json`.
The final additional commit contains only three cross-feature guards and their
boundary explanation. Production code and intake manifests are unchanged from
`234767c7d4efb8dded4c79b8a44e09d564b665ab`, where the integrity checks below ran.

## Bounded combined regression

**1,415 passed, 0 failed, 0 skipped** across 80 relevant test files, exit 0,
201.557 seconds. No source, guard or checked documentation
hash changed during execution. Exact arguments, Python version, all production
LF hashes, guard/document hashes and pre/post status are recorded in
`combined-summary.json`; every individual case is recorded in `combined-cases.json`
and `combined.xml`. `combined.log` contains the full captured pytest output.

Reproduce using the complete local Python environment:

```powershell
& '${PYTHON_RUNTIME}\Scripts\python.exe' -B -X utf8 '${EVIDENCE_ROOT}\all-integration\run_combined.py'
```

The driver refuses a changed source head, dirty checkout, missing supplied
ancestor, changed historical source or missing FFmpeg. The five required real
brain-MCP cases, four historical-physics cases and three real-FFmpeg cases all
executed and passed. None was skipped. The brain process uses pinned commit
`98d6b899533a82fb1047f952987229c62a9929fb`. Historical physics is byte-identical after LF
normalization to commit `124ea433fe9a2ad2fd66a7360df85f6d61bab793`, SHA256
`4b34d161010da4d9ca8da4563d8caa1ec952fcdf712c634baf835b1dc152c876`. Real FFmpeg decodes synthetic encoded
clips; these cases do not claim camera or arbitrary-media coverage.

## Integrity and merged surface

- Strict manifest: 64/64 MATCH, no missing, mismatch, malformed or byte mismatch.
- Time-core, silent-except, import-direction and coverage-map lints: exit 0.
- All 23 existing time-lint statements map exactly to the five-way baseline;
  no new baseline mapping or exemption was added.
- Import smoke: 95/95 modules, constructive smoke OK.
- Inventory: 95 Python files, 89 non-init modules; core 15, nn 14, gen 7,
  world 47, vision 5, plus one package-root module.

The merge retains both audio and video entrypoints/capabilities, the lazy vision
export union, the controlled discovery whitelist union, main's image/local
visual-query descriptions, shared complete quadrant evidence, and corrected
package counts. Merge logs and resolution helpers remain beside this report.

## Explicit cross-feature boundary

`bridge-dedup-final.log/xml` records three passing guards for warm-cache writes,
same-ID same-layer replacement, duplicate merging, committed cross-connection
visibility and transaction rollback. The third guard verifies the existing #127
same-ID cross-layer refusal: uncertain `context` ingestion cannot replace an
accepted `knowledge` card, and the prior row, exact cached match and factual
answer remain intact. Qualification transitions at that ID remain unsupported.

The original `bridge-dedup.log/xml` remains untouched: two passes and one failure
from the invalid expectation that the uncertain card could replace the accepted
fact. Earlier fixture-development output is also retained under
`bridge-dedup-test-development.*`. No governance bypass or production behavior
change was made to turn those expectations green. Constructive network weights
verify memory consistency, not real-image recognition accuracy or model quality.

## Remaining verification ownership

The combined run emitted 1208 warnings. They include optional component
discovery, existing #775 SQLite-lock access-count write failures under thread
stress, explicit scene follow-target warnings and source-literal SyntaxWarnings.
The thread assertions passed, but those warnings are not presented as fixed.

Full repository gates and remote CI are supervisor-owned and were not started
by this bounded integration task. No push, GitHub mutation or new bounty was
performed. Existing individual contribution/mutation evidence remains in the
sibling integration directories. This freeze contains thirteen contributions;
the later perception/controlled-benchmark dependency integration is separate.
