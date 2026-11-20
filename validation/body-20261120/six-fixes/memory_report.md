# Allocation and process-memory probes

Three repetitions per variant, independently from latency benchmarks.

| Workload | Baseline traced peak median bytes | Fixed traced peak median bytes | Fixed / baseline |
|---|---:|---:|---:|
| detect_8_frames_96_entities | 573832 | 574956 | 1.002x |
| darkline_RGBA_1536x1536 | 120325453 | 120326691 | 1.000x |
| overlap_512_skew_pairs | 12320 | 8824 | 0.716x |
| snapshot_cold_5000_nodes | 11556216 | 12035488 | 1.041x |
| snapshot_warm_5000_nodes | 906876 | 1380332 | 1.522x |
| snapshot_after_mixed_5000_nodes | 1043015 | 12038190 | 11.542x |
| nearest_odd_r_50000_points | 4732702 | 4734618 | 1.000x |
| search_5000_skills_limit_-1 | 77655 | 77655 | 1.000x |

Scope and interpretation:

- tracemalloc measures traced Python/NumPy allocations and can omit native Pillow/SQLite buffers.
- Process working set includes imports, allocator retention and fixtures; peak working set is lifetime-wide. Windows uses GetProcessMemoryInfo, Linux uses /proc/self/status, other platforms may expose only resource peak RSS or no process metric. Null denotes an unavailable metric.
- Fixture construction excluded from traced allocation interval; result retained while sampling.
- Memory probes run separately from all latency samples.
