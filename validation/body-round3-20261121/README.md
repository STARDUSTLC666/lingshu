# Lingshu body fixes, round three

This branch is the public evidence seal for two independent body-library fixes.
The frozen integration source is `f81ee3a9939f3dad7c277145766508c113742ba0`
with tree `5e6e6d45fdc9ef6ea885f4e4f38d56630089a751`. It extends the previously
validated twelve-fix source with only `HexGrid.neighbors` and
`SceneSimulator._apply_command`; the method audit records the unchanged prior
production methods.

- [PR #1481](https://github.com/FuRongJun-1999/lingshu/pull/1481) uses source
  `4a352249ef6db7975353b84bc640712d46f7181b`. Its exact-source CI and title
  checks passed in three legs: **5690 passed, 40 skipped, 98 subtests, 102
  scripts, brain 23/23** per leg. Thirty new guards pass, the original
  baseline is 19 failures and 11 passes, and six named mutants are detected.
  The independent odd-r point-cloud oracle is 972/972; the axial oracle is
  324/324. The measured correction costs 1.302–1.637 times the old incorrect
  implementation on the paired local workload.
- [PR #1482](https://github.com/FuRongJun-1999/lingshu/pull/1482) uses source
  `bd208a379e44497e9f35fdc145838abb19e6d313`. Its exact-source CI and title
  checks passed in three legs: **5721 passed, 40 skipped, 98 subtests, 102
  scripts, brain 23/23** per leg. Sixty-one new guards pass, the original
  baseline is 58 failures and 3 passes, and sixteen named mutants are detected.
  The independent Decimal ballistic oracle is 2000/2000 and adjacent physics,
  collision, and environment probes are 340/340.

The combined Linux repository gate [run 44787808270](https://github.com/STARDUSTLC666/lingshu/actions/runs/44787808270)
passed **5918 tests, 40 skips, 98 subtests, 102 scripts and brain 23/23** in
each of its three environments. The completed Windows gate is retained as a
real result: **5933 passed, 1 failed, 24 skipped, 98 subtests, 102 scripts,
brain 23/23, strict manifest 64/64, time-core 23 registered / 0 new / 0
stale**. The only failure is the existing
`tests/test_issue498_atomic_write_perm_symlink_guard.py::test_p1_符号链接量具能力探测`:
Windows creates the symlink, while the test asserts the POSIX capability
result. The source is byte-identical to baseline `6b730824`; the evidence is
not marked green and the failure is not hidden.

The additional exact-source Linux benchmark and mutation workflow [run
44790156130](https://github.com/STARDUSTLC666/lingshu/actions/runs/44790156130)
completed in three environments. Its independent audit reconstructs 66
mutation executions, 36 neighbor correctness cases, 6000 command oracle
outcomes, seven timing workloads, and eight memory scenarios. The three API
artifact digests, inventories, source hashes, XML/assertion failures, and
oracle JSONL bytes are retained in this branch. Timing and `tracemalloc`
results are descriptive shared-host measurements; they do not claim general
speedup, statistical significance, RSS bounds, or native allocation bounds.

The evidence index records original, public, working-tree, and canonical Git
hashes. It contains allowlisted source slices, JSON/JSONL/XML/log outputs and
the stable CI snapshots needed to reproduce the claims. Polling snapshots,
source copies, databases, caches, bytecode, complete third-party issue bodies,
and ZIP binaries from the benchmark artifacts are excluded. Numeric JSON/XML
structure is checked after redaction; JSONL oracle files are preserved byte for
byte. A contribution maps to one PR and one original `intake:v1` bounty issue.
This branch does not self-claim, grade, label, settle, or merge upstream.
