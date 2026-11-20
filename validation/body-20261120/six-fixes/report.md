# Six-fix correctness and performance comparison

Baseline: d74848fb33dbff1d719959df19d1266a1ac60f44

Seed: 20261120

Every variant imports a separately archived package at its exact commit. Raw samples and environment metadata are in raw/*.json; snapshots retain archive SHA-256 and package tree hashes.

## Correctness

| Suite | PR | Baseline failed / assertions | Fixed failed / assertions | Fixed status |
|---|---:|---:|---:|---|
| motion_groups | 1469 | 81 / 165 | 0 / 165 | completed |
| lineart_alpha | 1470 | 22 / 69 | 0 / 85 | completed |
| obb_sat | 1471 | 8 / 2113 | 0 / 2092 | completed |
| novelty_cache | 1472 | 116 / 798 | 0 / 798 | completed |
| hexgrid_nearest | 1473 | 632 / 12205 | 0 / 12205 | completed |
| skill_limit | 1474 | 30 / 110 | 0 / 110 | completed |

## Timing medians

Units: ms per named batch or operation. Ratios >1 mean the fixed version took longer in these samples.

| Workload | Baseline median ms | Fixed median ms | Fixed / baseline |
|---|---:|---:|---:|
| detect_8_frames_8_entities | 0.204133 | 0.223400 | 1.094x |
| detect_8_frames_32_entities | 2.127500 | 2.276800 | 1.070x |
| detect_8_frames_96_entities | 17.678667 | 20.047600 | 1.134x |
| darkline_RGB_128x128 | 0.380000 | 0.836600 | 2.202x |
| darkline_RGBA_128x128 | 0.430600 | 1.137800 | 2.642x |
| darkline_RGB_512x512 | 12.088600 | 10.553200 | 0.873x |
| darkline_RGBA_512x512 | 12.081100 | 13.172700 | 1.090x |
| darkline_RGB_1536x1536 | 98.259700 | 99.097500 | 1.009x |
| darkline_RGBA_1536x1536 | 104.328500 | 123.025900 | 1.179x |
| overlap_32_pairs | 1.272300 | 1.170400 | 0.920x |
| overlap_128_pairs | 4.694300 | 4.668300 | 0.994x |
| overlap_512_pairs | 18.748800 | 18.500000 | 0.987x |
| snapshot_warm_100_nodes | 0.246120 | 0.259280 | 1.053x |
| snapshot_append_100_nodes | 0.409720 | 0.443200 | 1.082x |
| snapshot_mixed_100_nodes | 0.466500 | 4.140367 | 8.875x |
| snapshot_warm_1000_nodes | 2.380740 | 2.785060 | 1.170x |
| snapshot_append_1000_nodes | 2.639360 | 3.007040 | 1.139x |
| snapshot_mixed_1000_nodes | 3.014167 | 48.999300 | 16.256x |
| snapshot_warm_5000_nodes | 13.864620 | 15.919020 | 1.148x |
| snapshot_append_5000_nodes | 13.859820 | 16.157400 | 1.166x |
| snapshot_mixed_5000_nodes | 14.247467 | 241.756767 | 16.968x |
| nearest_odd_r_1000_points | 5.152300 | 5.727700 | 1.112x |
| nearest_odd_r_10000_points | 50.808000 | 56.799000 | 1.118x |
| nearest_odd_r_50000_points | 267.965700 | 297.301800 | 1.109x |
| search_100_skills_limit_-1 | 1.039710 | 0.877580 | 0.844x |
| search_100_skills_limit_10 | 1.052415 | 0.877940 | 0.834x |
| search_100_skills_limit_None | 1.049860 | 0.874840 | 0.833x |
| search_1000_skills_limit_-1 | 1.948105 | 1.653530 | 0.849x |
| search_1000_skills_limit_10 | 1.867495 | 1.651815 | 0.885x |
| search_1000_skills_limit_None | 1.869855 | 1.910910 | 1.022x |
| search_5000_skills_limit_-1 | 5.920730 | 5.656275 | 0.955x |
| search_5000_skills_limit_10 | 6.150480 | 5.983435 | 0.973x |
| search_5000_skills_limit_None | 5.856930 | 5.613500 | 0.958x |

## Failure detail

- motion_groups / baseline / distinct_delimiter_groups: 80 failed; examples recorded in raw JSON.
- motion_groups / baseline / structured_identifier_partitions: 1 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / alpha_matches_independent_white_composite: 8 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / hidden_rgb_invariance: 4 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / premultiplied_matches_direct_white_composite: 4 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / premultiplied_conversion_supported: 4 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / palette_transparency_visible_line: 1 failed; examples recorded in raw JSON.
- lineart_alpha / baseline / PA_matches_independent_palette_alpha_composite: 1 failed; examples recorded in raw JSON.
- obb_sat / baseline / overlap_matches_independent_corner_sat: 7 failed; examples recorded in raw JSON.
- obb_sat / baseline / singular_basis_rejected: 1 failed; examples recorded in raw JSON.
- novelty_cache / baseline / mixed_update_append_union: 9 failed; examples recorded in raw JSON.
- novelty_cache / baseline / mixed_update_append_counts: 9 failed; examples recorded in raw JSON.
- novelty_cache / baseline / mixed_update_append_per_node: 9 failed; examples recorded in raw JSON.
- novelty_cache / baseline / novelty_matches_fresh_old: 9 failed; examples recorded in raw JSON.
- novelty_cache / baseline / novelty_matches_fresh_new: 9 failed; examples recorded in raw JSON.
- novelty_cache / baseline / stateful_sequence_union: 21 failed; examples recorded in raw JSON.
- novelty_cache / baseline / stateful_sequence_counts: 25 failed; examples recorded in raw JSON.
- novelty_cache / baseline / stateful_sequence_per_node: 25 failed; examples recorded in raw JSON.
- hexgrid_nearest / baseline / euclidean_nearest_odd_r_offset: 632 failed; examples recorded in raw JSON.
- skill_limit / baseline / nonpositive_unbounded_semantics: 30 failed; examples recorded in raw JSON.

## Scope and limitations

- Synthetic deterministic CPU and in-memory SQLite workloads; no production databases, real imagery, GPU, network, or live engine tasks.
- Host concurrently runs other verification work. No CPU pinning or power-plan control. Timings are descriptive, not isolated-hardware or statistical-significance claims.
- Fixture construction is excluded from measured samples; append and mixed timings include their named database mutations. GC disabled only during timed operations; 3 warmups plus 9 retained samples.
- OBB randomized bases have abs(det)>0.15; no extremely near-singular geometry coverage.
- Skill search keeps the pre-existing 100-row candidate cap, even with negative/unbounded limit.
- Novelty warm checks still scan/hash all rows; no constant-time or memory-reduction claim.
