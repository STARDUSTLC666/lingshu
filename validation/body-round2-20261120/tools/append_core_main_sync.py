"""Append current PR1478 merge-head CI without relabeling old measurements."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

PREFIX = Path("validation/body-round2-20261120")
OLD = "89c005b7fdd48f64c603d34c280a4d18a93956f7"
NEW = "41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50"
SOURCE = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
MAIN = "04e0ecb6a3669c90efbb4a1583816a8f7ca26bc7"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    target = repo / PREFIX
    sync = source / "core-main-sync"
    ci = sync / "ci"
    result = json.loads((ci / "pr1478/summary.json").read_text(encoding="utf-8"))
    ci_summary = json.loads((ci / "summary.json").read_text(encoding="utf-8"))
    assert ci_summary["all_complete"] and ci_summary["all_verified_success"]
    assert result["head"] == NEW and result["all_complete"] and result["all_success"]
    assert result["semantic_evidence_verified"] and len(result["gate_jobs"]) == 3
    assert len(result["title_jobs"]) == 1
    assert {(run["id"], run["head"], run["status"], run["conclusion"]) for run in result["runs"]} == {
        (44781318899, NEW, "completed", "success"),
        (44781318941, NEW, "completed", "success")}
    assert all(job["head_sha"] == NEW and job["status"] == "completed" and
               job["conclusion"] == "success" for job in result["title_jobs"])
    counts = []
    for job in result["gate_jobs"]:
        assert job["head_sha"] == NEW and job["conclusion"] == "success"
        assert job["script_groups"] == job["unique_scripts"] == 102 and job["brain_real_23_of_23"]
        assert job["pytest_counts"]["failed"] == job["pytest_counts"]["errors"] == 0
        assert job["pytest_counts"]["skipped"] == 40 and job["pytest_counts"]["subtests_passed"] == 98
        counts.append(job["pytest_counts"]["passed"])
    assert len(set(counts)) == 1
    current_core = subprocess.check_output(["git", "show", NEW + ":lingshu/core/core.py"], cwd=repo)
    combined_core = subprocess.check_output(["git", "show", SOURCE + ":lingshu/core/core.py"], cwd=repo)
    assert current_core == combined_core
    old_core = subprocess.check_output(["git", "show", OLD + ":lingshu/core/core.py"], cwd=repo)
    def functions(payload):
        found = {}
        for node in ast.walk(ast.parse(payload)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.setdefault(node.name, []).append(ast.dump(node, include_attributes=False))
        return found
    old_functions, current_functions = functions(old_core), functions(current_core)
    assert old_functions.keys() == current_functions.keys()
    changed_functions = sorted(name for name in old_functions if old_functions[name] != current_functions[name])
    assert changed_functions == ["search_skills"]
    spec = importlib.util.spec_from_file_location("prep_sync", target / "tools/prepare_round2_public_evidence.py")
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    records = {r["artifact"]: r for r in manifest["artifacts"]}

    def xml_semantics(element, redact=False):
        convert = prep.sanitize if redact else (lambda value: value)
        return (element.tag,
                tuple(sorted((key, convert(value)) for key, value in element.attrib.items())),
                convert(element.text) if element.text else element.text,
                convert(element.tail) if element.tail else element.tail,
                tuple(xml_semantics(child, redact) for child in element))

    def clean(value):
        if isinstance(value, str):
            return prep.sanitize(value)
        if isinstance(value, list):
            return [clean(x) for x in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                key = prep.sanitize(key)
                assert key not in result
                result[key] = clean(item)
            return result
        return value

    def publish(name, raw, origin):
        name = Path(name).as_posix()
        if name.endswith(".json"):
            old = json.loads(raw.decode("utf-8-sig"), parse_constant=prep.reject_constant)
            value = clean(old)
            assert prep.numeric_leaves(old) == prep.numeric_leaves(value)
            payload = prep.dumps(value)
        else:
            payload = prep.sanitize(re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))).encode("utf-8")
        if name.endswith(".xml"):
            assert xml_semantics(ET.fromstring(raw), True) == xml_semantics(ET.fromstring(payload))
        p = target / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(payload)
        records[name] = {"artifact": name, "mode": "main_sync_evidence_numeric_preserving",
                         "source": origin, "original_sha256": prep.sha(raw), "original_bytes": len(raw),
                         "published_sha256": prep.sha(payload), "published_bytes": len(payload)}

    archives = []
    for p in sorted(sync.rglob("*")):
        if not p.is_file():
            continue
        relative = p.relative_to(sync)
        if any(x in {"tmp", "__pycache__"} for x in relative.parts):
            continue
        if p.suffix == ".zip":
            archives.append({"source": p.relative_to(source).as_posix(), "bytes": p.stat().st_size,
                             "sha256": prep.sha(p.read_bytes()), "policy": "complete decoded job logs published; compressed convenience copy retained privately"})
            continue
        if p.suffix not in {".json", ".xml", ".log", ".txt", ".py", ".yml"}:
            continue
        if p.name == "pull.json":
            continue  # Do not copy complete third-party/PR discussion bodies.
        if p.name.endswith(".stderr.log") and not p.stat().st_size:
            continue
        publish(Path("core-main-sync") / relative, p.read_bytes(), p.relative_to(source).as_posix())
    publish("core-main-sync/archive-digests.json", prep.dumps({"archives": archives}), "generated source archive digests")
    status = json.loads((target / "source-status.json").read_text(encoding="utf-8"))
    core = status["core"]
    assert core["final_pr_head"] in {OLD, NEW}
    core.setdefault("pre_main_sync_validated_pr_head", OLD)
    historical_core_hash = hashlib.sha256(subprocess.check_output(
        ["git", "show", OLD + ":lingshu/core/core.py"], cwd=repo)).hexdigest()
    core.setdefault("pre_main_sync_production_canonical_sha256", historical_core_hash)
    assert core["pre_main_sync_validated_pr_head"] == OLD
    assert core["pre_main_sync_production_canonical_sha256"] == historical_core_hash
    core["final_pr_head"] = NEW
    core["production_canonical_sha256"] = hashlib.sha256(current_core).hexdigest()
    core.setdefault("measurement_source_identical_to_pre_sync_pr_head", core["measurement_source_identical_to_final_head"])
    assert core["measurement_source_identical_to_pre_sync_pr_head"] is True
    core["measurement_source_identical_to_final_head"] = False
    core["final_head_delta"] = subprocess.check_output(
        ["git", "diff", "--name-only", core["measured_commit"], NEW], cwd=repo,
        text=True, encoding="utf-8", errors="replace").splitlines()
    core["main_sync"] = {"merged_main": MAIN, "head": NEW, "ci_gate_run": 44781318899,
                         "all_three_gate_legs_and_title_success": True, "pytest_passed_each_leg": counts[0],
                         "core_module_identical_to_benchmarked_combined_source": True,
                         "production_functions_changed_by_merge": changed_functions,
                         "all_fresh_decay_functions_unchanged": True,
                         "combined_source": SOURCE,
                         "reason": "Maintainer merged previous PR1474; only the core fingerprint conflicted. Fresh-decay functions unchanged. No new finding or bounty."}
    remote = status["remote_ci"]
    remote.setdefault("historical_pre_sync_core_head", remote["pull_requests"]["1478"])
    assert remote["historical_pre_sync_core_head"]["head"] == OLD
    remote["pull_requests"]["1478"] = {"head": NEW, "gate_and_title_jobs": 4, "gate_jobs": 3,
        "pytest_passed_each_gate": counts[0], "skipped_each_gate": 40, "subtests_each_gate": 98,
        "scripts_each_gate": "102/102", "real_brain_each_gate": "23/23",
        "run": 44781318899, "title_run": 44781318941, "directory": "core-main-sync/ci/pr1478"}
    status["upstream_merged_previous_contributions"] = {"main": MAIN, "merged_prs": [1469,1473,1474],
        "note": "These contributions were merged by the maintainer, not by this task; all are already present in the frozen combined patch union."}
    publish("source-status.json", prep.dumps(status), "generated verified main synchronization status")
    publish("remote-ci/summary.json", prep.dumps(remote), "generated verified current/previous head separation")
    for filename in ("README.md", "FINAL_VALIDATION.md"):
        text = (target / filename).read_text(encoding="utf-8")
        marker = "## Current PR1478 synchronization after upstream merges"
        if marker in text:
            text = text.split(marker)[0].rstrip() + "\n"
        text += f"\n{marker}\n\nUpstream main `{MAIN}` merged our prior PRs1469/1473/1474. The PR1478 merge `{NEW}` imports those previously delivered fixes; conflict resolution changes only the core manifest fingerprint. Fresh-decay functions remain unchanged, and its entire core module is byte-identical to frozen combined source `{SOURCE}`. The original89-head measurements remain historical and are not relabeled. New exact-head gate44781318899 and title pass, each gate{counts[0]} passed/40 skipped/98subtests,102 scripts and actual brain23/23. No new bounty is claimed; intake2792 remains the single contribution. See `core-main-sync/`.\n"
        publish(filename, text.encode("utf-8"), "generated current head status, preserving historic results")

    publish("tools/append_core_main_sync.py", Path(__file__).read_bytes(), "generated main synchronization append helper")
    junit = []
    for name in sorted(records):
        if name.endswith(".xml"):
            root = ET.fromstring((target / name).read_bytes())
            suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
            junit.append({"artifact": name, "suites": [dict(s.attrib) for s in suites]})
    publish("junit-index.json", prep.dumps({
        "policy": "Raw per-run counters; overlapping/supplementary runs are not summed.", "runs": junit}),
        "generated full XML inventory after current-head append")

    names = [(PREFIX / n).as_posix() for n in records]
    for start in range(0, len(names), 100):
        subprocess.run(["git", "add", "-f", "--", *names[start:start+100]], cwd=repo, check=True, capture_output=True)
    blobs = prep.staged_blobs(repo, names)
    for name, row in records.items():
        b = blobs[(PREFIX / name).as_posix()]
        assert prep.sha(b) == row["published_sha256"] and len(b) == row["published_bytes"], name
        row["git_canonical_blob_sha256"], row["git_canonical_blob_bytes"] = prep.sha(b), len(b)
    manifest["artifacts"] = list(records.values())
    (target / "sanitization-manifest.json").write_bytes(prep.dumps(manifest))
    for name in ("preparation-audit.json", "final-seal-audit.json"):
        audit = json.loads((target / name).read_text(encoding="utf-8"))
        audit["canonical_blobs_verified"] = audit["artifact_count"] = len(records)
        audit["current_core_pr_head"] = NEW
        audit["current_core_ci_gate_run"] = 44781318899
        audit["current_core_ci_verified_success"] = True
        audit["xml_files"] = len(junit)
        if "staged_evidence_files" in audit:
            audit["staged_evidence_files"] = len(records) + 3
        (target / name).write_bytes(prep.dumps(audit))
    subprocess.run(["git", "add", "-f", "--", (PREFIX / "sanitization-manifest.json").as_posix(),
                    (PREFIX / "preparation-audit.json").as_posix(), (PREFIX / "final-seal-audit.json").as_posix()],
                   cwd=repo, check=True)
    print(json.dumps({"ok": True, "current_head": NEW, "gate_run": 44781318899,
                      "passed_each_gate": counts[0], "artifacts": len(records)}))


if __name__ == "__main__":
    main()
