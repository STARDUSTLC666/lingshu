# Reproduce the six submitted fixes

These scripts use immutable Git snapshots and synthetic inputs. They only write under the required --output directory and never install over, switch, or edit repository source. They do not fetch automatically. NumPy and Pillow are required; Python 3.12.10, NumPy 2.5.5, Pillow 12.3.0 and SQLite 3.49.1 were the original validation environment. Every run records its own actual versions.

Create a separate Python environment and install NumPy and Pillow there. Clone the public repository and make the submitted PR commits available before running. With the upstream repository as origin, GitHub exposes its PR heads; for example:

    git fetch origin refs/pull/1469/head refs/pull/1470/head refs/pull/1471/head refs/pull/1472/head refs/pull/1473/head refs/pull/1474/head

The exact commits below must resolve locally. If a PR is later rebased or its objects disappear from a fresh clone, fetch an evidence/fork ref retaining that exact commit; the runner intentionally never substitutes another revision.

| Suite | PR | Fixed commit |
|---|---:|---|
| motion_groups | 1469 | cc68a82baace16e92ff6ce770330b65102a530a5 |
| lineart_alpha | 1470 | 433befa7b356eebecbc457ecd8f8a123ec1540cc |
| obb_sat | 1471 | 39d379552f34026ef46ad0515831319b1494a5d3 |
| novelty_cache | 1472 | a663512dd0fbc44a9fb08a55751951009586d172 |
| hexgrid_nearest | 1473 | cff189b3438623feaebdf1a874fafdd03080acb1 |
| skill_limit | 1474 | fb6c9cabc939a6defcc44ef661b3048d47155d87 |

The common baseline is d74848fb33dbff1d719959df19d1266a1ac60f44. For a complete run from a separate artifact folder:

    python benchmark_six_fixes.py --repo /path/to/lingshu --output /path/to/evidence
    python memory_six_fixes.py --repo /path/to/lingshu --output /path/to/evidence

On Windows, replace the sample paths with quoted Windows paths. --repo defaults to the current directory. --output is always required. --only accepts one or more comma-separated suite names, and supports a fresh output directory for partial reproduction:

    python benchmark_six_fixes.py --repo /path/to/lingshu --output /path/to/alpha-evidence --only lineart_alpha
    python memory_six_fixes.py --repo /path/to/lingshu --output /path/to/alpha-evidence --only lineart_alpha

Keep the two scripts together: the memory runner imports the benchmark runner's exact commit definitions and synthetic fixtures. Run timing and memory probes sequentially. The separate portable pendulum_release_accuracy.py script needs mpmath (originally 1.4.1), accepts --repo/--output/--baseline, and does not depend on these two scripts.

Outputs include report.md, comparison.json, raw worker JSON/stdout/stderr, frozen snapshots and provenance hashes. Memory probes produce memory_report.md, memory_comparison.json and memory_raw. Source imports are checked against the intended snapshot. Baseline correctness failures are intentionally retained; only fixed failures/errors make the full timing run fail.

Coverage includes 80 motion-ID collisions; independent RGBA/LA/RGBa/La/PA white-composite oracles; 601 explicit-corner skew SAT cases; mixed cache writes and 120 seeded stateful mutation steps; 10,000 random hex-point nearest-center checks plus 2,205 center roundtrips; and skill limits at 1/5/50/100/150 cards. Existing 100-candidate skill semantics remain explicit.

Timing uses three warmup samples and nine retained samples, with fixtures constructed outside timing and named SQL mutations included. Raw wall and process CPU samples are retained. Shared-host medians and ratios are descriptive; there is no pinning, power-plan control or statistical-significance claim. Correct mixed-cache rebuilds cost more than the baseline's incorrect reuse.

Memory uses three repetitions separately from timing. tracemalloc can omit native Pillow/SQLite allocations. Windows process counters, Linux /proc and other-platform resource fallbacks have different available metrics; null means unavailable, not zero. The original run tested the Windows path; Linux/macOS process-counter fallbacks still require validation on those hosts. Process lifetime peaks also contain imports and fixtures. No production DB, real image corpus, GPU, network, full agent task, or extreme near-singular geometry coverage is claimed here.

Raw evidence includes local executable/source/output paths and machine version details for reproducibility. When publishing evidence, create an explicitly labeled sanitized copy rather than modifying the original measurement records. Inputs contain no real user memories or images.
