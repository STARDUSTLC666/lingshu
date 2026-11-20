"""Frozen-source Linux A/B benchmarks and 27 semantic mutation replays.

The workflow owns dependencies and checkout; this driver records exact input
files, commands, exit codes and every stdout/stderr before validating reports.
No complete repository/brain gate is substituted by this scoped workflow.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


SPECS = {
    "core": ("tools/testing/replay_transaction_guards.py", "tests/fixtures/fresh_row_decay_mutations.json"),
    "circular": ("tools/testing/replay_save_guards.py", "tests/fixtures/circular_time_residual_mutations.json"),
    "numeric": ("tools/testing/replay_save_guards.py", "tests/fixtures/spatial_detect_complete_partition_mutations.json"),
    "world": ("tools/testing/replay_save_guards.py", "tests/fixtures/scene_collision_freeflight_velocity_mutations.json"),
}
BENCHES = ["bench/bench_fresh_row_decay.py", "bench/circular_time_residual.py",
           "bench/bench_spatial_detect_partition.py", "bench/bench_scene_collision_freeflight.py"]
CONTROL_CASES = {"kinematic_default", "kinematic_boxes_8", "dynamic_default_8", "dynamic_one_box"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_artifact_index(out):
    """Index completed outputs after the validation summary is final.

    The caller's tee can still append to driver.log when main prints its
    result. Exclude that live stream and the index itself; listed files must
    not be written after this function returns.
    """
    allowed = {".json", ".xml", ".log", ".txt", ".py", ".md"}
    inventory = []
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out)
        if (not path.is_file() or path.suffix not in allowed
                or relative.as_posix() in {"artifact-index.json", "driver.log"}
                or any(part in {"tmp", "sandbox", "__pycache__"}
                       or part.startswith("guard-") for part in relative.parts)):
            continue
        payload = path.read_bytes()
        inventory.append({"path": relative.as_posix(), "bytes": len(payload), "sha256": digest(payload)})
    result = {"files": inventory, "excludes": ["artifact-index.json (self)", "driver.log (live tee)",
              "tmp", "sandbox", "guard-*", "__pycache__", "databases"]}
    write_json(out / "artifact-index.json", result)
    return result


def validate_reports(out, source):
    checks = []
    provenance = load(out / "provenance.json")
    source_hashes = provenance["source_tracked_files_sha256"]
    baseline_hashes = provenance["baseline_archive_files_sha256"]
    core = {v: load(out / "core" / (v + ".json")) for v in ("baseline", "fixed")}
    assert core["fixed"]["source_sha256"] == source_hashes["lingshu/core/core.py"], "core fixed source mismatch"
    assert core["baseline"]["source_sha256"] == baseline_hashes["lingshu/core/core.py"], "core baseline source mismatch"
    assert len(core["fixed"]["records"]) == len(core["baseline"]["records"]) == 12
    for row in core["fixed"]["records"]:
        assert row["oracle_failures"] == 0, ("core oracle", row["nodes"], row["mode"])
        assert len(row["latency_ms_samples"]) == 9 and len(row["python_traced_peak_bytes_samples"]) == 3
    assert any(r["oracle_failures"] for r in core["baseline"]["records"]), "core baseline lost discrimination"
    checks.append("core fixed oracle has zero failures; all raw timing/memory samples present")

    circular = load(out / "circular" / "paired.json")
    assert circular["source_sha256_lf"]["fixed"] == source_hashes["lingshu/world/physics.py"], "circular fixed source mismatch"
    assert circular["source_sha256_lf"]["baseline"] == baseline_hashes["lingshu/world/physics.py"], "circular baseline source mismatch"
    fixed = circular["accuracy"]["fixed"]
    assert fixed["failures"] == fixed["fit_errors"] == 0
    assert fixed["assertions"] == fixed["planned_assertions"] == 7146
    assert circular["accuracy"]["baseline"]["failures"] > 0
    assert len(circular["performance"]) == 3
    for row in circular["performance"]:
        assert all(len(v) == 9 for v in row["samples_ns_per_call"].values())
    checks.append("circular fixed analytic oracle 7146/7146; baseline failures retained")

    numeric = {v: load(out / "numeric" / (v + ".json")) for v in ("baseline", "fixed")}
    assert numeric["fixed"]["source_lf_sha256"] == source_hashes["lingshu/nn/hex_text.py"], "numeric fixed source mismatch"
    assert numeric["baseline"]["source_lf_sha256"] == baseline_hashes["lingshu/nn/hex_text.py"], "numeric baseline source mismatch"
    pairs = {v: {r["case"]: r for r in obj["records"]} for v,obj in numeric.items()}
    assert len(pairs["baseline"]) == len(pairs["fixed"]) == 3
    assert pairs["baseline"].keys() == pairs["fixed"].keys()
    for name, row in pairs["fixed"].items():
        prior = pairs["baseline"][name]
        assert row["input_sha256"] == prior["input_sha256"]
        assert row["weights_sha256"] == prior["weights_sha256"]
        assert len(row["milliseconds"]) == 9 and len(row["traced_peak_bytes"]) == 3
        if name == "divisible_2x18x18":
            assert row["output_sha256"] == prior["output_sha256"], "divisible-grid output changed"
    checks.append("numeric A/B inputs and weights identical; divisible output SHA identical")

    world = load(out / "world" / "summary.json")
    assert world["scene_source_sha256_lf"]["fixed"] == source_hashes["lingshu/world/scene_simulator.py"], "world fixed source mismatch"
    assert world["scene_source_sha256_lf"]["baseline"] == baseline_hashes["lingshu/world/scene_simulator.py"], "world baseline source mismatch"
    assert len(world["rows"]) == 28 and len(world["comparisons"]) == 14
    for row in world["rows"]:
        if row["variant"] == "fixed":
            assert not row["oracle"]["failures"], ("world fixed oracle", row["case"], row["mode"])
        assert len(row["samples"]) == (11 if row["mode"] == "time" else 3)
    assert any(r["oracle"]["failures"] for r in world["rows"] if r["variant"] == "baseline")
    for row in world["comparisons"]:
        if row["case"] in CONTROL_CASES:
            assert row["output_equal"], ("world control changed", row["case"], row["mode"])
    checks.append("world fixed analytic oracle clear; four unchanged controls match in both modes")

    total = 0
    for label, (_, spec_path) in SPECS.items():
        spec = load(source / spec_path)
        summary = load(out / "mutations" / label / "summary.json")
        rows = summary["records"]
        assert len(rows) == len(spec["mutations"]) + 2, label
        assert all(r["ok"] for r in rows), label
        assert {r["case"] for r in rows} == {"fixed", "baseline"} | {m["name"] for m in spec["mutations"]}
        for row in rows:
            assert row["errors"] == row["skipped"] == 0, (label, row["case"])
            if row["case"] == "fixed":
                assert row["returncode"] == 0 and row["passed"] == spec["total"]
            else:
                assert row["returncode"] == 1 and row["failed_tests"]
            if row["case"] not in {"fixed", "baseline"}:
                assert len(row["failed_tests"]) == 1
        total += len(spec["mutations"])
    assert total == 27, total
    checks.append("all four fixed guards / exact baseline failures / 27 named mutants verified")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--baseline-sha", required=True)
    args = parser.parse_args()
    source, baseline, out = args.source.resolve(), args.baseline_root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True, encoding="utf-8", errors="replace").strip()
    assert actual == args.source_sha
    assert (baseline / ".source-commit").read_text().strip() == args.baseline_sha
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=source).decode().split("\0")
    tracked = [p for p in tracked if p and (source / p).is_file()]
    before = {p: digest((source / p).read_bytes()) for p in tracked}
    baseline_files = {p.relative_to(baseline).as_posix(): digest(p.read_bytes())
                      for p in sorted(baseline.rglob("*")) if p.is_file()}
    inputs = set(BENCHES)
    for runner, spec_path in SPECS.values():
        spec = load(source / spec_path)
        inputs.update([runner, spec_path, spec["guard"], *spec["sources"]])
    provenance = {"source_sha": actual, "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=source, text=True, encoding="utf-8", errors="replace").strip(),
                  "baseline_sha": args.baseline_sha, "python": sys.version, "platform": platform.platform(),
                  "cwd": str(source), "driver_sha256": digest(Path(__file__).read_bytes()),
                  "input_files_sha256": {p: before[p] for p in sorted(inputs)},
                  "source_tracked_files_sha256": before, "baseline_archive_files_sha256": baseline_files,
                  "github_run": {k: os.environ.get(k) for k in ["GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"]}}
    write_json(out / "provenance.json", provenance)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONHASHSEED": "0",
           "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    commands = []

    def run(label, argv):
        command = [sys.executable, "-X", "utf8", "-B", *map(str, argv)]
        began = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        result = subprocess.run(command, cwd=source, env=env, capture_output=True)
        for stream in ("stdout", "stderr"):
            (out / (label + "." + stream + ".log")).write_bytes(getattr(result, stream))
        row = {"label": label, "command": command, "cwd": str(source), "started_utc": began,
               "elapsed_seconds": time.perf_counter()-started, "exit_code": result.returncode,
               "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)}
        commands.append(row)
        write_json(out / "commands.json", commands)
        print(json.dumps(row), flush=True)

    run("core-baseline", [source / BENCHES[0], "--root", baseline, "--output", out / "core/baseline.json"])
    run("core-fixed", [source / BENCHES[0], "--root", source, "--output", out / "core/fixed.json"])
    run("circular-paired", [source / BENCHES[1], "--baseline", args.baseline_sha, "--output", out / "circular/paired.json"])
    run("numeric-baseline", [source / BENCHES[2], "--source-root", baseline, "--out", out / "numeric/baseline.json"])
    run("numeric-fixed", [source / BENCHES[2], "--source-root", source, "--out", out / "numeric/fixed.json"])
    run("world-paired", [source / BENCHES[3], "--baseline", args.baseline_sha, "--output", out / "world", "--ticks", 80, "--repeats", 11])
    for label, (runner, spec_path) in SPECS.items():
        run("mutations-" + label, [source / runner, "--spec", spec_path, "--baseline", args.baseline_sha,
                                   "--mutate", "--output", out / "mutations" / label])
    errors, checks = [], []
    if any(row["exit_code"] for row in commands):
        errors.append("one or more measured commands returned nonzero")
    try:
        checks = validate_reports(out, source)
    except Exception as exc:
        errors.append(type(exc).__name__ + ": " + str(exc))
    after = {p: digest((source / p).read_bytes()) for p in tracked}
    if before != after:
        errors.append("source tracked-file hashes changed during validation")
    result = {"source_sha": actual, "baseline_sha": args.baseline_sha, "checks": checks,
              "errors": errors, "commands": len(commands), "named_mutations_expected": 27,
              "all_command_exit_codes_zero": all(row["exit_code"] == 0 for row in commands),
              "source_unchanged": before == after, "ok": not errors,
              "scope": "four benchmark workloads and mutation replays; complete repository/brain gate runs separately"}
    write_json(out / "validation-summary.json", result)
    write_artifact_index(out)
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
