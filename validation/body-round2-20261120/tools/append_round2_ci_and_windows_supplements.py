"""Append raw, sanitized final CI and Windows supplement evidence.

Usage: --source-root private outputs --repo clean evidence worktree at f769.
No production checkout is modified. Bodies and archive ZIP payloads are omitted;
the exact job log bytes, API job/run records and their source digests are kept.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


EXPECTED = "f769b3ac33eb5221ad66f6a4384aa6429b26e597"
PREFIX = Path("validation/body-round2-20261120")
RUNS = {
    1477: {"head": "e821bbb1fac57fa638640e3caf153caf7f1b1973", "run": 44761889152, "title_run": 44761888700, "passed": 5582},
    1478: {"head": "89c005b7fdd48f64c603d34c280a4d18a93956f7", "run": 44762844376, "title_run": 44762844234, "passed": 5624},
    1479: {"head": "13952c82874fb9ee19a4f1b660e3144134367a53", "run": 44763098857, "title_run": 44763099047, "passed": 5617},
    1480: {"head": "a357dbbe96905848fd81b7249814576fb2743674", "run": 44764764765, "title_run": 44764764805, "passed": 5646},
}
COMBINED = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
LINUX_INTERMEDIATE = 44766869622


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                   text=True, encoding="utf-8", errors="replace").strip() == EXPECTED
    prep_path = repo / PREFIX / "tools/prepare_round2_public_evidence.py"
    spec = importlib.util.spec_from_file_location("evidence_prep", prep_path)
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    target = repo / PREFIX
    manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    records = {row["artifact"]: row for row in manifest["artifacts"]}
    junit = json.loads((target / "junit-index.json").read_text(encoding="utf-8"))
    junit_records = {row["artifact"]: row for row in junit["runs"]}
    copied = 0
    numeric_leaves = 0
    source_files = []
    excluded_archives = []

    def publish(relative, raw, origin, kind):
        nonlocal copied, numeric_leaves
        relative = Path(relative)
        name = relative.as_posix()
        if kind == "json":
            original = json.loads(raw.decode("utf-8-sig"), parse_constant=prep.reject_constant)
            payload = prep.dumps(prep.transform(original))
            output = json.loads(payload, parse_constant=prep.reject_constant)
            leaves = prep.numeric_leaves(original)
            assert leaves == prep.numeric_leaves(output), name
            numeric_leaves += len(leaves)
        elif kind == "xml":
            text = re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))
            before = ET.fromstring(text)
            clean_text = prep.sanitize(text)
            payload = clean_text.encode("utf-8")
            after = ET.fromstring(payload)
            def semantic(element):
                return (element.tag, {k: prep.sanitize(v) for k, v in element.attrib.items()},
                        prep.sanitize(element.text or ""), prep.sanitize(element.tail or ""),
                        [semantic(child) for child in element])
            assert semantic(before) == semantic(after), name
            suites = [after] if after.tag == "testsuite" else after.findall(".//testsuite")
            junit_records[name] = {"artifact": name, "suites": [dict(s.attrib) for s in suites]}
        else:
            payload = prep.sanitize(re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))).encode("utf-8")
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        records[name] = {"artifact": name, "mode": "sanitized_verbatim_numeric_preserving",
                         "source": origin, "original_sha256": sha(raw), "original_bytes": len(raw),
                         "published_sha256": sha(payload), "published_bytes": len(payload)}
        source_files.append({"source": origin, "artifact": name, "sha256": sha(raw), "bytes": len(raw)})
        copied += 1

    ci_root = source / "audit-world/ci-round2"
    ci_summary_raw = (ci_root / "summary.json").read_bytes()
    ci_summary = json.loads(ci_summary_raw)
    assert ci_summary["all_complete"] and ci_summary["all_verified_success"]
    assert not ci_summary["errors"]
    verified_prs = {}
    for number, expected in RUNS.items():
        data = json.loads((ci_root / f"pr{number}/summary.json").read_text(encoding="utf-8"))
        assert data["head"] == expected["head"] and data["all_complete"] and data["all_success"]
        assert data["semantic_evidence_verified"]
        assert len(data["gate_jobs"]) == 3 and len(data["title_jobs"]) == 1
        assert all(j["head_sha"] == expected["head"] and j["status"] == "completed"
                   and j["conclusion"] == "success" for j in data["gate_jobs"] + data["title_jobs"])
        assert all(j.get("script_groups") == j.get("unique_scripts") == 102
                   and j.get("brain_real_23_of_23") is True for j in data["gate_jobs"])
        assert all(j["pytest_counts"]["passed"] == expected["passed"]
                   and j["pytest_counts"]["skipped"] == 40
                   and j["pytest_counts"]["subtests_passed"] == 98 for j in data["gate_jobs"])
        verified_prs[str(number)] = data
        pbase = ci_root / f"pr{number}"
        for name in ("summary.json", "changed-guard-evidence.json", "workflow.yml"):
            p = pbase / name
            publish(Path("remote-ci") / f"pr{number}" / name, p.read_bytes(), p.relative_to(source).as_posix(),
                    "json" if p.suffix == ".json" else "text")
        for dirname in (f"{expected['run']}-attempt1", f"{expected['title_run']}-attempt1"):
            d = pbase / dirname
            for p in sorted(d.iterdir()):
                if p.suffix == ".zip":
                    excluded_archives.append({"source": p.relative_to(source).as_posix(),
                                              "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size,
                                              "reason": "compressed convenience copy omitted; exact decoded raw job logs and per-job hashes are included"})
                    continue
                if p.name.endswith(".stderr.log") and p.stat().st_size == 0:
                    continue
                if p.suffix not in {".json", ".log"}:
                    continue
                publish(Path("remote-ci") / f"pr{number}" / dirname / p.name, p.read_bytes(),
                        p.relative_to(source).as_posix(), "json" if p.suffix == ".json" else "text")
        apis = pbase / "api"
        latest = sorted(p.name for p in apis.iterdir() if p.is_dir())[-1]
        for api_name in (f"{expected['run']}-run.json", f"{expected['run']}-jobs.json",
                         f"{expected['title_run']}-run.json", f"{expected['title_run']}-jobs.json", "checks.json"):
            p = apis / latest / api_name
            if p.exists():
                publish(Path("remote-ci") / f"pr{number}" / "api" / latest / api_name,
                        p.read_bytes(), p.relative_to(source).as_posix(), "json")

    combined = ci_root / "combined"
    combined_summary = json.loads((combined / "summary.json").read_text(encoding="utf-8"))
    expected_run = 44764384747
    assert combined_summary["run_id"] == expected_run and combined_summary["actual_run_head"] == COMBINED
    assert combined_summary["expected_head"] == COMBINED and combined_summary["all_success"]
    combined_api_latest = sorted(p for p in (combined / "api").iterdir() if p.is_dir())[-1]
    combined_run_api = json.loads((combined_api_latest / "run.json").read_text(encoding="utf-8"))
    assert combined_run_api["event"] == "workflow_dispatch" and combined_run_api["head_sha"] == COMBINED
    assert len(combined_summary["jobs"]) == 3
    for row in combined_summary["jobs"]:
        assert row["conclusion"] == "success" and row["script_groups"] == row["unique_scripts"] == 102
        assert row["brain_real_23_of_23"] is True
        assert row["pytest_counts"]["passed"] == 5827 and row["pytest_counts"]["skipped"] == 40
        assert row["pytest_counts"]["subtests_passed"] == 98
    for name in ("summary.json", "workflow.yml"):
        p = combined / name
        publish(Path("remote-ci") / "combined" / name, p.read_bytes(), p.relative_to(source).as_posix(),
                "json" if p.suffix == ".json" else "text")
    cd = combined / f"{expected_run}-attempt1"
    for p in sorted(cd.iterdir()):
        if p.suffix == ".zip":
            excluded_archives.append({"source": p.relative_to(source).as_posix(), "sha256": sha(p.read_bytes()),
                                      "bytes": p.stat().st_size,
                                      "reason": "compressed convenience copy omitted; exact decoded raw job logs and per-job hashes are included"})
            continue
        if p.name.endswith(".stderr.log") and p.stat().st_size == 0:
            continue
        if p.suffix not in {".json", ".log"}:
            continue
        publish(Path("remote-ci") / "combined" / p.name, p.read_bytes(), p.relative_to(source).as_posix(),
                "json" if p.suffix == ".json" else "text")
    apis = combined / "api"
    latest = sorted(p.name for p in apis.iterdir() if p.is_dir())[-1]
    for name in ("run.json", "jobs.json", "artifacts.json"):
        p = apis / latest / name
        if p.exists():
            publish(Path("remote-ci") / "combined" / "api" / latest / name, p.read_bytes(),
                    p.relative_to(source).as_posix(), "json")

    bench = ci_root / "linux-benchmarks"
    interim = json.loads((bench / "summary.json").read_text(encoding="utf-8"))
    assert interim["run_id"] == LINUX_INTERMEDIATE and interim["measured_source_head"] == COMBINED
    assert interim["all_complete"] and interim["all_verified_success"]
    assert interim["inner_artifact_indexes_clean"] is False
    publish(Path("linux-benchmarks/intermediate-44766869622/summary.json"),
            (bench / "summary.json").read_bytes(), (bench / "summary.json").relative_to(source).as_posix(), "json")
    readme = bench / "README.md"
    publish(Path("linux-benchmarks/intermediate-44766869622/README.md"), readme.read_bytes(),
            readme.relative_to(source).as_posix(), "text")
    interim_run = bench / f"{LINUX_INTERMEDIATE}-attempt1"
    for p in sorted(interim_run.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(interim_run)
        if p.suffix == ".zip":
            excluded_archives.append({"source": p.relative_to(source).as_posix(), "sha256": sha(p.read_bytes()),
                                      "bytes": p.stat().st_size,
                                      "reason": "uploaded artifact ZIP retained in audited private cache; extracted original outputs are published"})
            continue
        if p.suffix not in {".json", ".xml", ".log", ".txt", ".md", ".py"}:
            continue
        if p.name.endswith(".stderr.log") and p.stat().st_size == 0:
            continue
        publish(Path("linux-benchmarks/intermediate-44766869622/artifacts") / rel,
                p.read_bytes(), p.relative_to(source).as_posix(), "json" if p.suffix == ".json" else "xml" if p.suffix == ".xml" else "text")

    supplement_dir = target / "windows-supplements"
    for rel, src, kind in (
        ("frozen-physics.xml", source / "supplement-frozen-physics.xml", "xml"),
        ("frozen-physics.log", source / "supplement-frozen-physics.log", "text"),
        ("symlink-bodies/summary.json", source / "supplement-symlink/summary.json", "json"),
        ("symlink-bodies/driver.py", source / "supplement-original-symlink-bodies.py", "text"),
        ("symlink-bodies/log.log", source / "supplement-symlink.log", "text"),
        ("baseline-p1.xml", source / "baseline-symlink-p1.xml", "xml"),
        ("baseline-p1.log", source / "baseline-symlink-p1.log", "text"),
    ):
        if src.exists():
            publish(Path("windows-supplements") / rel, src.read_bytes(), src.relative_to(source).as_posix(), kind)

    remote_status = {"status": "all four exact PR heads and exact combined workflow dispatch verified success",
                     "pull_requests": {str(k): {"head": RUNS[k]["head"], "gate_and_title_jobs": 4,
                                                  "gate_jobs": 3, "pytest_passed_each_gate": RUNS[k]["passed"],
                                                  "skipped_each_gate": 40, "subtests_each_gate": 98,
                                                  "scripts_each_gate": "102/102", "real_brain_each_gate": "23/23",
                                                  "run": RUNS[k]["run"], "title_run": RUNS[k]["title_run"]}
                                        for k in RUNS},
                     "combined": {"source_head": COMBINED, "event": "workflow_dispatch",
                                  "run": expected_run, "gate_jobs": 3, "pytest_passed_each_gate": 5827,
                                  "skipped_each_gate": 40, "subtests_each_gate": 98,
                                  "scripts_each_gate": "102/102", "real_brain_each_gate": "23/23"}}
    publish(Path("remote-ci/summary.json"), prep.dumps(remote_status), "audit-world/ci-round2/summary.json", "json")
    excluded_archives.sort(key=lambda x: x["source"])
    publish(Path("remote-ci/excluded-archive-copies.json"), prep.dumps({"archives": excluded_archives,
            "note": "Original full-run/artifact ZIPs were downloaded and SHA-verified privately. To avoid duplicating extracted logs in the public tree, this tree retains their source SHA/byte count and publishes exact decoded per-job files instead."}),
            "audit-world/ci-round2/collector-index", "json")

    windows = source / "integration-windows"
    extras = ["supplement-frozen-physics.xml", "supplement-frozen-physics.log", "supplement-original-symlink-bodies.py",
              "supplement-symlink.log", "baseline-symlink-p1.xml", "baseline-symlink-p1.log"]
    for rel in extras:
        p = source / rel
        if p.exists():
            path = Path("windows-supplements") / rel
            publish(path, p.read_bytes(), rel, "xml" if p.suffix == ".xml" else "text")
    supp_json = source / "supplement-symlink/summary.json"
    if supp_json.exists():
        publish(Path("windows-supplements/supplement-symlink-summary.json"), supp_json.read_bytes(),
                "supplement-symlink/summary.json", "json")

    status = json.loads((target / "source-status.json").read_text(encoding="utf-8"))
    status["scope"] = "four scoped contributions, independent integration PASS, exact PR/combined Linux CI PASS, Windows full gate failure preserved, Linux benchmark clean rerun pending"
    status["remote_ci"] = remote_status
    status["linux_benchmark_execution"] = {"intermediate_run": LINUX_INTERMEDIATE,
        "source_sha": COMBINED, "source_workflow_head": EXPECTED,
        "actual_measurements_verified": True, "inner_index_driver_log_stale": True,
        "classification": "valid intermediate measurements; not index-clean final evidence"}
    status["windows_supplements"] = {"historical_physics_guard": "43 passed; 4 original main-suite skips covered, not added to main count",
        "original_symlink_test_bodies": "3/3 pass after actual capability probe; original skip markers unchanged and excluded from main count",
        "same_failure_on_authentic_d748_baseline": True,
        "baseline_probe": "1 original POSIX-only capability assertion failed on the same Windows-host condition; isolated, excluded from full-gate totals"}
    status["bounty_intake_receipts"] = {"directory": "publication-receipts", "issue_numbers": [2791,2792,2793,2794],
        "initial_evidence_commit": EXPECTED, "readback_verified": True,
        "note": "Original create/readback receipts retained; immutable final evidence links will be appended after the clean Linux benchmark run."}
    publish(Path("source-status.json"), prep.dumps(status), "generated from independently read-back source statuses", "json")

    readme = (target / "README.md").read_text(encoding="utf-8")
    readme += """\n## Exact PR and combined Linux CI\n\nAll four PR heads and the frozen combined source dispatch completed all three gate environments successfully. Every gate checked 102 scripts, actual pinned brain 23/23, and its separately preserved pytest count / 40 skips / 98 subtests. `remote-ci/` retains exact-head job/run API records and raw job logs; no cancelled or old head is counted. The combined run uses source5226860 explicitly.\n\n## Windows supplemental probes\n\nThe original full-gate counts remain untouched. A 43-test physics supplement with the authentic historical baseline passed; three unchanged symlink test bodies passed after an actual Windows symlink capability probe. The original P1 probe was also run alone against baseline d74848 and failed the same POSIX assertion (exit1), matching the full-gate failure. These supplemental results are separate and are not added to the main counts.\n\n## Intermediate Linux benchmark archive\n\n`linux-benchmarks/intermediate-44766869622/` preserves the first run's measured-source PASS results. Its only defect is one stale inner-index digest for live driver.log; the measurements, 27 mutation checks, outputs and uploaded archive digests were independently verified. The index-clean rerun remains pending and will be linked in a later immutable append.\n"""
    publish(Path("README.md"), prep.sanitize(readme).replace("\r\n", "\n").encode("utf-8"),
            "generated final CI/Windows supplement status", "text")
    prep.subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    blobs = prep.staged_blobs(repo, [(PREFIX / name).as_posix() for name in records])
    for name, row in records.items():
        payload = blobs[(PREFIX / name).as_posix()]
        assert sha(payload) == row["published_sha256"] and len(payload) == row["published_bytes"], name
        if name.endswith(".json"):
            json.loads(payload, parse_constant=prep.reject_constant)
        if name.endswith(".xml"):
            ET.fromstring(payload)
        row["git_canonical_blob_sha256"] = sha(payload)
        row["git_canonical_blob_bytes"] = len(payload)
    manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"] = list(records.values())
    (target / "sanitization-manifest.json").write_bytes(prep.dumps(manifest))
    audit = {"status": "Windows/CI append staged and independently blob-verified; index-clean Linux benchmark rerun pending",
             "base_commit": EXPECTED, "newly_copied_files": copied,
             "total_artifacts": len(records), "canonical_blobs_verified": len(records),
             "new_numeric_leaves_verified": numeric_leaves, "excluded_zip_convenience_copies": len(excluded_archives),
             "excluded_zip_index": excluded_archives}
    (target / "windows-ci-append-audit.json").write_bytes(prep.dumps(audit))
    # Manifest and audit are detached metadata by design and are verified by the final independent audit script.
    prep.subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
