# Final integration publication audit — 2026-11-20

All 16 authorized existing bodies were updated successfully and individually read back. All 16 strict UTF-8 body SHA-256 values match the prepared submissions, not merely normalized text.

Fixed evidence revision: `ce40e464d256f1a53b4fb6bd4b7012cf6c4a942d`.

## Preservation and factual scope

- PRs 1469–1476 and dsh-bounty intakes 2783–2790 each contain one `body-validation-20261120:integration:start/end` block.
- All eight original `intake:v1` headers are retained byte for byte, parsed and checked against their exact corresponding PR.
- Every previous expanded-validation block is retained byte for byte.
- Only PR 1471 and intake 2785 additionally received the authorized narrow SAT-domain wording changes. The normalized determinant rejection `<=1e-9` and the oracle sampling domain `>0.15` are explicit; near-singular cases are not inferred from that oracle.
- Finite/physical-domain tightening is described explicitly. The bodies do not promise that old invalid/coercible input acceptance is unchanged.
- Linux three-leg success, Windows 5673/1/28/98 with original driver exit 1 and unchanged-upstream P1 reproduction, eight separately covered skips, and twenty remaining unavailable Windows cases are all kept distinct. Supplemental passes are not added to the main pytest passed count.
- Before preparation, seven pinned public files were fetched directly from GitHub and checked against their Git blob hashes; the local copies and verification manifest are under `public-reports/`.

## Final PR state and checks

Each head below matches both its pre-publication snapshot and its readback. Each PR has all three gate legs SUCCESS and a latest title check SUCCESS that started after its body-edit prewrite snapshot (with a five-second clock tolerance). Historical cancelled title checks were not mistaken for the latest result.

| PR | State | Merge state | Unchanged head | Three gates | Latest fresh title |
|---|---|---|---|---|---|
| #1469 | OPEN | CLEAN | `cc68a82baace16e92ff6ce770330b65102a530a5` | SUCCESS | SUCCESS |
| #1470 | OPEN | CLEAN | `433befa7b356eebecbc457ecd8f8a123ec1540cc` | SUCCESS | SUCCESS |
| #1471 | OPEN | CLEAN | `39d379552f34026ef46ad0515831319b1494a5d3` | SUCCESS | SUCCESS |
| #1472 | OPEN | CLEAN | `a663512dd0fbc44a9fb08a55751951009586d172` | SUCCESS | SUCCESS |
| #1473 | OPEN | CLEAN | `cff189b3438623feaebdf1a874fafdd03080acb1` | SUCCESS | SUCCESS |
| #1474 | OPEN | CLEAN | `fb6c9cabc939a6defcc44ef661b3048d47155d87` | SUCCESS | SUCCESS |
| #1475 | OPEN | CLEAN | `e0771a810b8846676f3545542b2e70d5e0011467` | SUCCESS | SUCCESS |
| #1476 | OPEN | CLEAN | `1ab5cc7f295ed5748b50c7ffde26cf2a34663204` | SUCCESS | SUCCESS |

## Updated bodies

| PR | Corresponding existing intake | Verified |
|---|---|---|
| [#1469](https://github.com/FuRongJun-1999/lingshu/pull/1469) | [#2783](https://github.com/FuRongJun-1999/dsh-bounty/issues/2783) | yes |
| [#1470](https://github.com/FuRongJun-1999/lingshu/pull/1470) | [#2784](https://github.com/FuRongJun-1999/dsh-bounty/issues/2784) | yes |
| [#1471](https://github.com/FuRongJun-1999/lingshu/pull/1471) | [#2785](https://github.com/FuRongJun-1999/dsh-bounty/issues/2785) | yes |
| [#1472](https://github.com/FuRongJun-1999/lingshu/pull/1472) | [#2786](https://github.com/FuRongJun-1999/dsh-bounty/issues/2786) | yes |
| [#1473](https://github.com/FuRongJun-1999/lingshu/pull/1473) | [#2787](https://github.com/FuRongJun-1999/dsh-bounty/issues/2787) | yes |
| [#1474](https://github.com/FuRongJun-1999/lingshu/pull/1474) | [#2788](https://github.com/FuRongJun-1999/dsh-bounty/issues/2788) | yes |
| [#1475](https://github.com/FuRongJun-1999/lingshu/pull/1475) | [#2789](https://github.com/FuRongJun-1999/dsh-bounty/issues/2789) | yes |
| [#1476](https://github.com/FuRongJun-1999/lingshu/pull/1476) | [#2790](https://github.com/FuRongJun-1999/dsh-bounty/issues/2790) | yes |

## Evidence files

- `audit-summary.json`: aggregate readback, preservation and source/check assertions.
- `publication-results.json`: all 16 actual edit results and verified remote body hashes.
- `final-checks-summary.json` and per-PR `*-final-checks.json`: final state, exact heads, all gate checks and latest fresh title-check details.
- Per-target `*-original.json/md`, `*-submitted.md`, `*-prewrite.json`, `*-edit-result.json`, `*-readback.json/md`: original snapshots, exact requests and post-write evidence.
- `prepare_integration_updates.py`, `publish_integration_updates.py`, `check_final_prs.py`: preparation, fail-closed publication and final check logic.

No new issue, claim, label, settlement, merge, code change or workflow change was performed in this publication pass. The integration source worktree remained clean.
