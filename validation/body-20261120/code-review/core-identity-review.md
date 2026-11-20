# Core, cache and identity final review

Reviewed range: `d74848fb33dbff1d719959df19d1266a1ac60f44` to `231aa5334c0c0f2f01eccf6c547ebd97a478a8d0`.

Result: no newly introduced material regression found in the three assigned production changes. This was a read-only code and call-path review; no tests were rerun and no production or public evidence files were changed.

## Findings checked

- `LayeredStore.search_skills`: the only executable change is applying the existing `_normalize_limit` helper before the prior query logic. Default/positive integer/zero/None results retain the existing SQL candidate selection, ranking, field dictionary and slice behavior. Negative integers deliberately adopt the established full-results sentinel semantics. “Full” still means the existing at-most-100 candidate pool; the fix does not accidentally expand or reorder the database query. `SpacetimeMemoryEngine.recall_skill` forwards to this same path and retains its feedback step.
- `LongTermMemoryGate._known_snapshot`: signature construction and its four-item return shape are unchanged; the added rowid-to-content-digest map is populated during the existing content scan. On append, the old rows must now retain their digests in addition to the previous count and surviving-ID proofs. Mixed rewrite-plus-append therefore takes the existing complete rebuild path, replacing the stale gram/count/per-node cache together. Cache hits and genuine append updates preserve their prior return/alias behavior. `_known_templates` continues to invalidate through the unchanged signature. The added retained/transient map costs O(N) memory and an O(N) comparison; it does not remove the existing O(total content bytes) signature scan or add a database scan.
- Motion-group identifiers: `_detect` supplies lexicographically sorted IDs, `_clusters` preserves that order, and `_fit_group` is the only `_group_id` caller. Names without `|` retain the exact old joined bytes, hash truncation and `mg_` identifier. Ambiguous delimiter-bearing names deliberately move to JSON-array encoding under a separate `mg_v2_` namespace, preventing both separator-partition aliases and encoded-vs-legacy aliases. Returned model/prediction dictionaries, member lookup, anchors and observed-coordinate arithmetic are unchanged. Existing stored group objects continue to pass their own identifier through prediction; the new code does not rewrite them. Repository consumer search found no production code parsing an assumed fixed `mg_` length or splitting this identifier.

## Actual files and context read

Production:

- `lingshu/core/core.py`: exact production diff; `_normalize_limit`; complete `search_skills` method and neighboring skill lookup; `recall_skill`; world-process `groups`/`predict_groups` dispatch and identifier forwarding.
- `lingshu/core/longterm_gate.py`: exact production diff; constructor; `_known_grams`, `_row_digest`, complete `_known_snapshot`; `_known_templates` and its signature consumer; `_novelty` context.
- `lingshu/world/motion_groups.py`: entire module, including input validation, sorted detection/clustering, fitting, group-ID generation, member lookup and both prediction entry points.

Supporting guards read (not executed):

- `tests/test_search_skills_limit_semantics.py`.
- `tests/test_longterm_gate_mixed_in_place_update.py`.
- `tests/test_motion_group_identifier_encoding.py`.
- Query-type guard references in `tests/test_issue_search_skills_query_type_guard.py` were inspected through targeted search.

The read-only review intentionally does not assert correctness outside the changed paths or replace the recorded full-suite, mutation and benchmark evidence.
