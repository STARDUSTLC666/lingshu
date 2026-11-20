# Round-three body fixes — evidence in progress

This branch records two new fixes and their exact source identities. It is a
validation/evidence branch, not another upstream contribution or bounty.

- Neighbors PR1481: `4a352249ef6db7975353b84bc640712d46f7181b`.
  Thirty guards pass; original baseline19 fail/11 pass; six named mutants.
  Full exact-source three-leg CI and title passed, each5690 passed/40 skipped/
  98 subtests,102 scripts and actual brain23/23. Local paired timing/memory
  measured atdf0838c; odd-r correction costs1.302–1.637 times the wrong baseline.
- Command reanchoring PR1482: `bd208a379e44497e9f35fdc145838abb19e6d313`.
  Sixty-one guards pass; baseline58 fail/3 pass; sixteen named mutants.
  Independent Decimal2000cases pass and adjacent340 pass. Code freeze6d1048f;
  final head adds only two documentation files. Local memory completed; exact
  PR CI and full Windows results are still pending in this initial snapshot.
- Combined source `f81ee3a9939f3dad7c277145766508c113742ba0`, tree
  `5e6e6d45fdc9ef6ea885f4e4f38d56630089a751`, is frozen. It extends the previously
  validated twelve-fix source5226860 with only HexGrid.neighbors and
  SceneSimulator._apply_command production changes. All nine incoming
  nonproduction assets match their individual PRs exactly. Scoped256 pass;
  manifest64/64 and time lint23registered/0new/0stale.

The complete combined Linux gate44787808270, complete Windows gate, and
additional Linux two-benchmark/22-mutation matrix remain separate. A passing
workflow or driver self-summary alone is not an independent artifact audit.
Completed original logs/samples, immutable indexes, and readbacks will be
appended without modifying the frozen source. Nothing pending is counted as
passed.

Local performance is descriptive shared-host data, not a speedup or RSS claim.
Command-heavy64-entity timing cost1.4367x, command/resume1.1215x, with the full
control/workload table retained in the source documentation. After draining
benchmark diagnostics,64-entity resume/sparse states retain6144 additional
Python traced bytes at both400 and4000ticks; this does not claim all diagnostic
history or process memory remains bounded.

Known previous Windows POSIX/symlink baseline failure and unavailable original
model/pixel assets must remain visible. Skipped and overlapping runs are never
summed as independent coverage. A contribution is one PR and one original
intake; no self-claim, labels, grading, settlement or upstream merge is performed.
