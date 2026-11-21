# Bridge and dedup integration boundaries

The combined M5.5 bridge and M5 dedup guards exercise the production ingestion,
cache, SQLite transaction and visual-memory query paths with deterministic
constructive network weights. They cover a warmed empty index followed by a
new card, a same-ID same-layer rewrite, a public duplicate merge, an external
connection's committed rewrite, and a rolled-back tentative rewrite. Queries
must use the latest committed color and must not retain superseded cache rows.

The third guard preserves the existing #127 governance rule: an accepted
`knowledge` card cannot be overwritten as `context` using the same ID. An
uncertain ingestion at that deterministic ID raises `PermissionError`; the
accepted persisted row, exact dedup match and factual answer remain intact.
Same-ID qualification transitions are therefore unsupported by this bridge.
The integration does not delete, retract, re-ID or move the accepted fact.

The initial integration probe incorrectly expected the uncertain card to
replace the accepted fact and remove it from factual answers. That expectation
conflicted with #127 and produced two passes and one failure. Its original
`bridge-dedup.log` and `bridge-dedup.xml` remain in the integration evidence
directory. The corrected contract is verified separately in
`bridge-dedup-final.log` and `bridge-dedup-final.xml`.

These cases validate controlled network outputs and memory consistency. They
do not establish real-image recognition accuracy, model quality, or the design
of a future card qualification-transition workflow.
