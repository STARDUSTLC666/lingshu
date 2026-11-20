"""Scoped round-three benchmarks and 22 semantic mutation replays.

Adapted from run_round2_linux_benchmarks.py. Exact inputs are bound locally;
execution stays disabled until the parent reviews/enables a separate evidence branch.
The complete repository/brain gate remains a separate workflow.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


class UnboundConfiguration(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
                    + "\n", encoding="utf-8", newline="\n")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(source, *args):
    return subprocess.check_output(["git", *args], cwd=source)


def under(source, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("binding paths must remain inside the source checkout")
    return source / path


def source_identity(source):
    return {"head": git(source, "rev-parse", "HEAD").decode("utf-8").strip(),
            "tree": git(source, "rev-parse", "HEAD^{tree}").decode("utf-8").strip(),
            "status_porcelain_all": git(source, "status", "--porcelain=v1",
                                        "--untracked-files=all").decode("utf-8")}


def archive_index(root):
    """All files, without exclusions: added/deleted paths change the hash set."""
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def final_integrity_errors(identity, config, baseline_before, baseline_after):
    errors = []
    if identity["head"] != config["source_sha"]:
        errors.append("source HEAD changed from the bound commit")
    if identity["tree"] != config["source_tree"]:
        errors.append("source HEAD tree changed from the bound tree")
    if identity["status_porcelain_all"] != "":
        errors.append("source git status is not clean (including all untracked files)")
    if baseline_before != baseline_after:
        errors.append("baseline archive all-file path/hash set changed")
    return errors


def require_bound(config):
    missing = []
    if not re.fullmatch(r"[0-9a-f]{40}", config.get("source_sha") or ""):
        missing.append("source_sha (combined measured checkout)")
    if not re.fullmatch(r"[0-9a-f]{40}", config.get("baseline_sha") or ""):
        missing.append("baseline_sha")
    if config.get("named_mutations_expected") != 22:
        missing.append("named_mutations_expected must remain 22")
    if set(config.get("cases", {})) != {"neighbors", "command"}:
        missing.append("exactly neighbors + command cases")
    for label, item in config.get("cases", {}).items():
        expected_total, expected_mutants = {"neighbors": (30, 6), "command": (61, 16)}.get(label, (None, None))
        if item.get("guard_total") != expected_total or item.get("named_mutations") != expected_mutants:
            missing.append(label + ".guard/mutant counts differ from requested scope")
        for key in ("reviewed_commit", "baseline_sha", "reviewed_files_lf_sha256",
                    "source_files_lf_sha256", "runner", "spec", "guard"):
            if not item.get(key):
                missing.append(label + "." + key)
        for key in ("path", "output", "reports", "invocations", "validator"):
            if not item.get("benchmark", {}).get(key):
                missing.append(label + ".benchmark." + key)
        if item.get("benchmark", {}).get("validator") not in {"neighbors_v1", "command_v1"}:
            missing.append(label + ".benchmark.validator implementation")
    if missing:
        raise UnboundConfiguration("unbound draft: " + "; ".join(missing))


def validate_neighbors(report, provenance, require_linux=True):
    source = report["source"]
    assert source == "lingshu/nn/hex_cnn.py"
    assert report["protocol"] == "paired-retained-six-neighbor-queries-v1"
    assert report["baseline_commit"] == provenance["baseline_sha"]
    assert report["measured_checkout_head"] == provenance["source_sha"]
    assert report["measured_checkout_status"] == ""
    assert report["fixed_source_sha256"] == provenance["source_files_sha256_lf"][source]
    assert report["baseline_source_sha256"] == provenance["baseline_files_sha256_lf"][source]
    assert report["benchmark_sha256"] == provenance["source_files_sha256_lf"][
        "bench/bench_hexgrid_neighbors.py"]
    if require_linux:
        assert report["platform"].startswith("Linux"), "report is not a Linux measurement"
    assert report["warmups_per_version_case"] == 3
    assert report["retained_timing_samples"] == 9
    assert report["separate_memory_probes"] == 3
    assert report["seed"] is None and report["clock"] == "perf_counter_ns"
    expected = {(mode, sign, n) for mode in ("axial", "odd_r_offset")
                for sign in ("positive", "negative") for n in (1000, 10000, 50000)}
    keys = [(c["mode"], c["coordinate_sign"], c["query_count"]) for c in report["cases"]]
    assert len(keys) == len(expected) and set(keys) == expected
    for case in report["cases"]:
        n = case["query_count"]
        assert case["rows_have_both_parities"] and case["returned_cells_per_version"] == 6 * n
        assert set(case["versions"]) == {"baseline", "fixed"}
        for variant, row in case["versions"].items():
            assert row["correct_ordered_queries"] == (
                0 if variant == "baseline" and case["mode"] == "odd_r_offset" else n)
            assert re.fullmatch(r"[0-9a-f]{64}", row["output_sha256"])
            assert len(row["timing_ns"]) == 9 and all(x > 0 for x in row["timing_ns"])
            assert len(row["memory_probes"]) == 3
            assert all(m["peak_bytes"] >= m["retained_bytes"] > 0 for m in row["memory_probes"])
            assert row["median_ns"] == statistics.median(row["timing_ns"])
            assert row["median_ns_per_query"] == row["median_ns"] / n
            assert row["median_peak_bytes"] == statistics.median(
                m["peak_bytes"] for m in row["memory_probes"])
        assert case["fixed_over_baseline_median_ratio"] == (
            case["versions"]["fixed"]["median_ns"] / case["versions"]["baseline"]["median_ns"])
        if case["mode"] == "axial":
            assert case["versions"]["fixed"]["output_sha256"] == (
                case["versions"]["baseline"]["output_sha256"])
    return "neighbors: 12 paired cases; raw timing/memory, hashes, correctness and axial controls"


def _finite(value):
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)
    elif isinstance(value, float):
        assert math.isfinite(value), "nonfinite measured value"


def validate_command(directory, provenance, require_linux=True):
    """Actual command script protocol: three independent process reports.

    Historical reports do not contain a measured Git HEAD. Bind their actual
    source/script/dependency hashes; do not manufacture that missing field.
    Future Linux identity is supplied independently by outer driver provenance.
    """
    reports = {mode: load(directory / (mode + ".json")) for mode in ("oracle", "timing", "memory")}
    source = "lingshu/world/scene_simulator.py"
    script = "bench/bench_dynamics_command_reanchor.py"
    dependencies = ("lingshu/world/physics.py", "lingshu/world/coord_contract.py")
    for mode, report in reports.items():
        _finite(report)
        assert report["mode"] == mode and report["baseline"] == provenance["baseline_sha"]
        assert report["ticks"] == 400 and report["repeats"] == 11
        assert report["source_sha256_lf"] == {
            "baseline": provenance["baseline_files_sha256_lf"][source],
            "fixed": provenance["source_files_sha256_lf"][source]}
        assert report["benchmark_sha256_lf"] == provenance["source_files_sha256_lf"][script]
        assert report["unchanged_dependency_sha256_lf"] == {
            p: provenance["source_files_sha256_lf"][p] for p in dependencies}
        if require_linux:
            assert report["platform"].startswith("Linux"), "report is not a Linux measurement"
    for variant, expected in (("fixed", provenance["source_files_sha256_lf"][source]),
                              ("baseline", provenance["baseline_files_sha256_lf"][source])):
        assert digest((directory / "sources" / (variant + ".py")).read_bytes().replace(
            b"\r\n", b"\n")) == expected, "command source snapshot mismatch"
    assert digest((directory / "benchmark-driver.py").read_bytes().replace(b"\r\n", b"\n")) == (
        provenance["source_files_sha256_lf"][script]), "command driver snapshot mismatch"

    oracle = reports["oracle"]["oracle"]
    raw = (directory / "oracle-cases.jsonl").read_bytes()
    assert digest(raw) == oracle["cases_sha256"], "command oracle raw-case hash mismatch"
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    assert len(cases) == 2000
    actual_summary = {v: {"cases": 0, "mismatches": 0, "max_position_error": 0.,
                          "max_velocity_error": 0.} for v in ("baseline", "fixed")}
    for index, case in enumerate(cases):
        _finite(case)
        assert case["index"] == index
        assert set(case["variants"]) == {"baseline", "fixed"}
        expected = [case["expected_position"], case["expected_velocity"]]
        for variant, outcome in case["variants"].items():
            actual = outcome["actual"]
            assert len(actual) == 2 and all(len(vector) == 3 for vector in actual)
            errors = [abs(a - b) for vector, truth in zip(actual, expected, strict=True)
                      for a, b in zip(vector, truth, strict=True)]
            matches = all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-8)
                          for vector, truth in zip(actual, expected, strict=True)
                          for a, b in zip(vector, truth, strict=True))
            assert outcome["matches"] is matches
            assert outcome["max_abs_error"] == max(errors)
            row = actual_summary[variant]
            row["cases"] += 1
            row["mismatches"] += not matches
            row["max_position_error"] = max(row["max_position_error"], *errors[:3])
            row["max_velocity_error"] = max(row["max_velocity_error"], *errors[3:])
    assert actual_summary == oracle["summary"], "command oracle raw/summary disagreement"
    assert actual_summary["fixed"]["mismatches"] == 0
    assert actual_summary["baseline"]["mismatches"] > 0

    cases_meta = {"kinematic_commands": (64, 1), "dynamics_free": (64, 0),
                  "dynamics_commands": (64, 1), "dynamics_resume_8": (8, 2),
                  "dynamics_resume_64": (64, 2), "dynamics_sparse": (64, 20),
                  "dynamics_singlebox": (1, 2)}
    controls = {"kinematic_commands", "dynamics_free", "dynamics_commands"}
    timings = reports["timing"]["timing"]
    assert len(timings) == 7 and {r["case"] for r in timings} == set(cases_meta)
    assert any(not r["oracle"]["baseline"]["matches"] for r in timings)
    for row in timings:
        name = row["case"]
        assert (row["entities"], row["command_interval_ticks"]) == cases_meta[name]
        assert row["ticks"] == 400 and row["oracle"]["fixed"]["matches"]
        assert len(row["order"]) == 12 and all(sorted(pair) == ["baseline", "fixed"] for pair in row["order"])
        assert set(row["seconds"]) == {"baseline", "fixed"}
        for variant, samples in row["seconds"].items():
            assert len(samples) == 11 and all(value > 0 for value in samples)
            assert row["median_seconds"][variant] == statistics.median(samples)
            assert re.fullmatch(r"[0-9a-f]{64}", row["result_sha256"][variant])
        medians = row["median_seconds"]
        assert row["fixed_over_baseline"] == medians["fixed"] / medians["baseline"]
        assert row["added_microseconds_per_entity_tick"] == (
            (medians["fixed"] - medians["baseline"]) * 1e6 / (row["entities"] * row["ticks"]))
        if name in controls:
            assert row["result_sha256"]["baseline"] == row["result_sha256"]["fixed"]

    memory = reports["memory"]["memory"]
    memory_cases = {"kinematic_commands", "dynamics_commands", "dynamics_resume_64", "dynamics_sparse"}
    assert len(memory) == 8
    assert {(r["case"], r["ticks"]) for r in memory} == {
        (case, ticks) for case in memory_cases for ticks in (400, 4000)}
    for row in memory:
        assert row["entities"] == 64
        assert len(row["order"]) == 3 and all(sorted(pair) == ["baseline", "fixed"] for pair in row["order"])
        assert set(row["readings"]) == {"baseline", "fixed"}
        for variant, probes in row["readings"].items():
            assert len(probes) == 3
            for probe in probes:
                assert probe["peak_bytes"] >= probe["current_bytes"] >= probe["after_drain_bytes"] > 0
                assert probe["physics_states"] == (0 if row["case"] == "kinematic_commands" else 64)
                assert probe["history_length"] >= 0 and probe["behavior_log_length"] >= 0
            for field in ("current", "peak", "after_drain"):
                assert row["median_" + field + "_bytes"][variant] == statistics.median(
                    probe[field + "_bytes"] for probe in probes)
    return "command: source/dependency snapshots; 2000 raw oracle cases; 7 timing and 8 memory/scaling cases"


def validate_mutations(directory, source, item, baseline_sha, provenance):
    spec = load(under(source, item["spec"]))
    assert spec["guard"] == item["guard"] and spec["total"] == item["guard_total"]
    assert len(spec["mutations"]) == item["named_mutations"]
    summary = load(directory / "summary.json")
    assert summary["baseline"] == baseline_sha
    assert summary["guard_sha256"] == digest(under(source, spec["guard"]).read_bytes().replace(b"\r\n", b"\n"))
    mutants = {m["name"]: m for m in spec["mutations"]}
    rows = {r["case"]: r for r in summary["records"]}
    assert len(rows) == len(summary["records"]) == len(mutants) + 2
    assert set(rows) == {"fixed", "baseline"} | set(mutants)
    for name, row in rows.items():
        expected = [] if name == "fixed" else (spec["baseline_failures"] if name == "baseline"
                                                 else [mutants[name]["test"]])
        assert row["ok"] and row["errors"] == row["skipped"] == 0
        assert sorted(row["failed_tests"]) == sorted(expected)
        assert sorted(row["expected_failures"]) == sorted(expected)
        assert row["returncode"] == (1 if expected else 0)
        tests = ET.parse(directory / (name + ".xml")).findall(".//testcase")
        assert len(tests) == (spec["total"] if name in {"fixed", "baseline"} else 1)
        assert sorted(t.get("name") for t in tests if t.find("failure") is not None) == sorted(expected)
        assert not any(t.find("error") is not None or t.find("skipped") is not None for t in tests)
        if name in {"fixed", "baseline"}:
            hashes = provenance["source_files_sha256_lf" if name == "fixed" else "baseline_files_sha256_lf"]
            assert row["source_sha256"] == {p: hashes[p] for p in spec["sources"]}
        else:
            assertion = mutants[name]["assertion"]
            assert row["expected_assertion"] == assertion
            assert assertion in (directory / (name + ".log")).read_text(encoding="utf-8")
    return len(mutants)


def write_artifact_index(out):
    # Reuses the round-two exclusion/late-index strategy; driver.log is a live tee.
    allowed = {".json", ".jsonl", ".xml", ".log", ".txt", ".py", ".md"}
    files = []
    for path in sorted(out.rglob("*")):
        relative = path.relative_to(out)
        if (not path.is_file() or path.suffix not in allowed
                or relative.as_posix() in {"artifact-index.json", "driver.log"}
                or any(part in {"tmp", "sandbox", "__pycache__"} or part.startswith("guard-")
                       for part in relative.parts)):
            continue
        payload = path.read_bytes()
        files.append({"path": relative.as_posix(), "bytes": len(payload), "sha256": digest(payload)})
    write_json(out / "artifact-index.json", {"files": files, "excludes": [
        "artifact-index.json (self)", "driver.log (live tee)", "tmp", "sandbox", "guard-*",
        "__pycache__", "databases"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    args = parser.parse_args()
    config = load(args.bindings)
    require_bound(config)
    if not config.get("execution_enabled"):
        raise UnboundConfiguration("bound local draft: execution is disabled pending parent evidence-branch review")
    source, baseline, out = args.source.resolve(), args.baseline_root.resolve(), args.output.resolve()
    identity_before = source_identity(source)
    actual = identity_before["head"]
    assert actual == config["source_sha"]
    assert identity_before["tree"] == config["source_tree"]
    assert identity_before["status_porcelain_all"] == ""
    assert (baseline / ".source-commit").read_text(encoding="utf-8").strip() == config["baseline_sha"]
    tracked = [p for p in git(source, "ls-files", "-z").decode("utf-8").split("\0") if p]
    before = {p: digest(under(source, p).read_bytes()) for p in tracked}
    source_lf = {p: digest(under(source, p).read_bytes().replace(b"\r\n", b"\n")) for p in tracked}
    baseline_raw = archive_index(baseline)
    baseline_lf = {p.relative_to(baseline).as_posix(): digest(p.read_bytes().replace(b"\r\n", b"\n"))
                   for p in baseline.rglob("*") if p.is_file()}
    for label, item in config["cases"].items():
        assert item["baseline_sha"] == config["baseline_sha"], (label, "baseline binding differs")
        for path, expected in item["source_files_lf_sha256"].items():
            assert source_lf[path] == expected, (label, path, "integration binding differs")
        assert set(item["source_files_lf_sha256"]) == set(item["reviewed_files_lf_sha256"])
        differences = sorted(p for p in item["source_files_lf_sha256"]
                             if item["source_files_lf_sha256"][p] != item["reviewed_files_lf_sha256"][p])
        assert differences == sorted(item["integration_differing_paths"])
        for path, expected in item["reviewed_files_lf_sha256"].items():
            reviewed = git(source, "show", item["reviewed_commit"] + ":" + path)
            assert digest(reviewed.replace(b"\r\n", b"\n")) == expected
    out.mkdir(parents=True, exist_ok=True)
    inputs = {p for item in config["cases"].values()
              for p in [item["runner"], item["spec"], item["guard"], item["benchmark"]["path"],
                        *item["source_files_lf_sha256"]]}
    provenance = {"source_sha": actual, "source_tree": git(source, "rev-parse", "HEAD^{tree}").decode().strip(),
                  "baseline_sha": config["baseline_sha"], "python": sys.version, "platform": platform.platform(),
                  "driver_sha256": digest(Path(__file__).read_bytes()), "bindings_sha256": digest(args.bindings.read_bytes()),
                  "source_identity_before": identity_before,
                  "input_files_sha256": {p: before[p] for p in sorted(inputs)},
                  "source_tracked_files_sha256": before, "source_files_sha256_lf": source_lf,
                  "baseline_archive_files_sha256": baseline_raw,
                  "baseline_files_sha256_lf": baseline_lf,
                  "github_run": {k: os.environ.get(k) for k in (
                      "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")}}
    write_json(out / "provenance.json", provenance)
    (out / "bindings.json").write_bytes(args.bindings.read_bytes())
    (out / "driver.py").write_bytes(Path(__file__).read_bytes())
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONHASHSEED": "0",
           "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    commands = []

    def run(label, argv):
        command = [sys.executable, "-X", "utf8", "-B", *map(str, argv)]
        began, started = datetime.now(timezone.utc).isoformat(), time.perf_counter()
        result = subprocess.run(command, cwd=source, env=env, capture_output=True)
        for stream in ("stdout", "stderr"):
            (out / (label + "." + stream + ".log")).write_bytes(getattr(result, stream))
        row = {"label": label, "command": command, "cwd": str(source), "started_utc": began,
               "elapsed_seconds": time.perf_counter() - started, "exit_code": result.returncode,
               "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)}
        commands.append(row)
        write_json(out / "commands.json", commands)
        print(json.dumps(row), flush=True)

    for label, item in config["cases"].items():
        benchmark_output = under(out, item["benchmark"]["output"])
        benchmark_output.parent.mkdir(parents=True, exist_ok=True)
        values = {"source": str(source), "baseline_root": str(baseline),
                  "baseline_sha": config["baseline_sha"], "output": str(out),
                  "benchmark_output": str(benchmark_output)}
        for invocation in item["benchmark"]["invocations"]:
            assert re.fullmatch(r"[a-z][a-z0-9_]*", invocation["label"])
            run(label + "-" + invocation["label"], [under(source, item["benchmark"]["path"]),
                *[arg.format_map(values) for arg in invocation["argv"]]])
        run("mutations-" + label, [under(source, item["runner"]), "--spec", item["spec"],
                                  "--baseline", config["baseline_sha"], "--mutate", "--output",
                                  out / "mutations" / label])
    errors, checks, total = [], [], 0
    if any(row["exit_code"] for row in commands):
        errors.append("one or more measured commands returned nonzero")
    try:
        for label, item in config["cases"].items():
            artifact = under(out, item["benchmark"]["output"])
            if item["benchmark"]["validator"] == "neighbors_v1":
                checks.append(validate_neighbors(load(artifact), provenance))
            else:
                assert item["benchmark"]["validator"] == "command_v1"
                checks.append(validate_command(artifact, provenance))
            total += validate_mutations(out / "mutations" / label, source, item,
                                        config["baseline_sha"], provenance)
        assert total == config["named_mutations_expected"] == 22
    except Exception as exc:
        errors.append(type(exc).__name__ + ": " + str(exc))
    tracked_unchanged = before == {p: (digest(under(source, p).read_bytes())
                                      if under(source, p).is_file() else None) for p in tracked}
    if not tracked_unchanged:
        errors.append("source tracked-file hashes changed during validation")
    identity_after = source_identity(source)
    baseline_after = archive_index(baseline)
    integrity_errors = final_integrity_errors(identity_after, config, baseline_raw, baseline_after)
    errors.extend(integrity_errors)
    baseline_unchanged = baseline_raw == baseline_after
    source_unchanged = tracked_unchanged and not any("source" in error for error in integrity_errors)
    write_json(out / "baseline-after-index.json", baseline_after)
    result = {"source_sha": actual, "baseline_sha": config["baseline_sha"], "checks": checks,
              "errors": errors, "commands": len(commands), "named_mutations_expected": 22,
              "all_command_exit_codes_zero": all(row["exit_code"] == 0 for row in commands),
              "named_mutations_validated": total, "source_unchanged": source_unchanged,
              "source_tracked_hashes_unchanged": tracked_unchanged,
              "source_identity_after": identity_after,
              "baseline_archive_unchanged": baseline_unchanged,
              "ok": not errors, "scope": "two benchmarks and 22 mutations; full repository/brain gate separate"}
    write_json(out / "validation-summary.json", result)
    write_artifact_index(out)
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except UnboundConfiguration as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
