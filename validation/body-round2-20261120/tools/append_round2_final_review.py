"""Append stable independent integration review and the cross-model probe.

Only stages evidence and its indexes. Does not commit, push or alter any
production tree. Usage: --source-root PRIVATE_OUTPUTS --repo EVIDENCE_TREE.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET


EXPECTED = "f769b3ac33eb5221ad66f6a4384aa6429b26e597"
BASE = "d74848fb33dbff1d719959df19d1266a1ac60f44"
COMBINED = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
PREFIX = Path("validation/body-round2-20261120")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo,
                                     text=True, encoding="utf-8", errors="replace").strip()
    assert actual == EXPECTED, "append must target the reviewed first evidence commit"
    spec = importlib.util.spec_from_file_location("preparer", source / "prepare_round2_public_evidence.py")
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    target = repo / PREFIX
    manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    records = {r["artifact"]: r for r in manifest["artifacts"]}
    junit = json.loads((target / "junit-index.json").read_text(encoding="utf-8"))
    junit_by_path = {r["artifact"]: r for r in junit["runs"]}
    excluded, copied = [], []
    counts = Counter()

    def publish(relative, payload, original=None, origin=None, mode="generated"):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        name = relative.as_posix()
        records[name] = {"artifact": name, "mode": mode, "source": origin,
                         "original_sha256": prep.sha(original) if original is not None else None,
                         "original_bytes": len(original) if original is not None else None,
                         "published_sha256": prep.sha(payload), "published_bytes": len(payload)}
        return name

    def copy(path, relative, origin=None):
        raw = path.read_bytes()
        text = re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))
        if path.suffix == ".json":
            original = json.loads(text, parse_constant=prep.reject_constant)
            value = prep.transform(original)
            payload = prep.dumps(value)
            assert prep.numeric_leaves(original) == prep.numeric_leaves(json.loads(payload))
            counts["numeric_json_leaves_preserved"] += len(prep.numeric_leaves(original))
        else:
            payload = prep.sanitize(text).encode("utf-8")
        name = publish(relative, payload, raw, origin or path.relative_to(source).as_posix(),
                       "sanitized_verbatim_numeric_preserving")
        copied.append(name)
        if path.suffix == ".xml":
            before, after = ET.fromstring(text), ET.fromstring(payload)
            def semantics(e):
                return (e.tag, {k: prep.sanitize(v) for k,v in e.attrib.items()},
                        prep.sanitize(e.text or ""), prep.sanitize(e.tail or ""),
                        [semantics(x) for x in e])
            assert semantics(before) == semantics(after)
            suites = [after] if after.tag == "testsuite" else after.findall(".//testsuite")
            junit_by_path[name] = {"artifact": name, "suites": [dict(s.attrib) for s in suites]}
            counts["xml_semantics_preserved"] += 1

    review = source / "audit-numeric/integration-review"
    for path in sorted(review.rglob("*")):
        if not path.is_file():
            continue
        local = path.relative_to(review)
        if "pytest-tmp" in local.parts or path.suffix in {".db", ".sqlite", ".sqlite3", ".pyc"}:
            excluded.append({"source": path.relative_to(source).as_posix(),
                             "reason": "temporary pytest database/environment data; original retained privately"})
            continue
        assert path.suffix in {".json", ".xml", ".log", ".py", ".patch", ".md"} or (
            not path.suffix and local.parts[0] == "artifact-reconstruction"), local
        copy(path, Path("integration-independent") / local)
    for name in ("cross-model-box-invariance.py", "cross-model-box-invariance.json",
                 "cross-model-box-invariance-baseline.json"):
        copy(source / name, Path("cross-model-box-invariance") / name)
    copy(source / "test_round2_artifact_index.py", Path("tools/test_round2_artifact_index.py"))
    for name in ("summary.json", "fixture.log"):
        copy(source / "linux-index-fixture" / name, Path("linux-index-fixture") / name)
    publish(Path("tools/run_round2_linux_benchmarks.py"),
            (source / "run_round2_linux_benchmarks.py").read_bytes().replace(b"\r\n", b"\n"))
    windows = source / "integration-windows"
    for path in sorted(windows.rglob("*")):
        if not path.is_file():
            continue
        local = path.relative_to(windows)
        if "tmp" in local.parts or path.suffix in {".db", ".sqlite", ".sqlite3", ".pyc"}:
            excluded.append({"source": path.relative_to(source).as_posix(),
                             "reason": "temporary full-gate data/database; original retained privately"})
            continue
        assert path.suffix in {".json", ".xml", ".log", ".txt"}, local
        copy(path, Path("integration-windows") / local)
    for name in ("integration-install.log", "integration-lint-final.json", "integration-lint-pre-numeric.json",
                 "integration-windows-console.log", "windows-final-comparison.json"):
        copy(source / name, Path("integration-windows") / name)
    legacy_driver = source.parent / "body-validation-20261120/portable_final_gate.py"
    legacy_before = prep.sha(legacy_driver.read_bytes())
    copy(legacy_driver, Path("tools/portable_final_gate.py"), "../body-validation-20261120/portable_final_gate.py")
    assert prep.sha(legacy_driver.read_bytes()) == legacy_before == "d76b23c179e4940b0798101ef196b8d6405692cf6fca6e43c4815b1fc78bec45"
    for name in ("intake-receipts.json", "intake-1477.md", "intake-1478.md", "intake-1479.md", "intake-1480.md"):
        copy(source / name, Path("publication-receipts") / name)

    fixed = json.loads((source / "cross-model-box-invariance.json").read_text(encoding="utf-8-sig"))
    baseline = json.loads((source / "cross-model-box-invariance-baseline.json").read_text(encoding="utf-8-sig"))
    assert fixed["source_sha"] == COMBINED and fixed["failures"] == 0
    assert baseline["source_sha"] == "d74848fb33dbff1d719959df19d1266a1ac60f44" and baseline["failures"] == 602
    assert all(v["scenes"] == 108 and v["ticks"] == 648 and v["checks"] == 3024 for v in (fixed, baseline))
    source_status = json.loads((target / "source-status.json").read_text(encoding="utf-8"))
    source_status["scope"] = "four local scoped sets plus independent combined-source reconstruction; complete Windows/Linux gates and Linux benchmark results pending"
    source_status["independent_combined_review"] = {
        "head": COMBINED, "tree": "529e1e150aa2c05a2f5bee3126c4678a58695e21",
        "directory": "integration-independent", "new_guard_tests": 165,
        "scope": "Exact independent contribution composition and specified scoped tests/probes; not a substitute for complete gates."}
    source_status["cross_model_box_probe"] = {
        "fixed_source": fixed["source_sha"], "baseline_source": baseline["source_sha"],
        "scenes_per_source": 108, "ticks_per_source": 648, "checks_per_source": 3024,
        "fixed_failures": fixed["failures"], "baseline_failures": baseline["failures"],
        "scope": "Public-API 0/1/2-box registration invariance across projectile/drag2/slope_friction/rolling; supplements independent free-fall analytic tests and does not prove exhaustive physics accuracy."}
    source_status["linux_benchmark_execution"] = {
        "run_id": 44766869622, "evidence_commit": EXPECTED, "source_sha": COMBINED,
        "result_imported": False, "note": "Run launched on the first evidence push; its result will be appended separately."}
    source_status["linux_artifact_index_metadata_correction"] = {
        "original_run": 44766869622,
        "scope": "Index metadata only; production source and actual benchmark/mutation measurements are not changed or reclassified as production failures.",
        "old_index_issue": "The first runner indexed live tee driver.log before its final print and before writing validation-summary.json.",
        "correction": "Write final validation-summary first, then index immutable completed outputs; explicitly exclude artifact-index.json itself, live driver.log and temporary/database files.",
        "fixture": "linux-index-fixture/summary.json", "tests": 4, "failures": 0,
        "original_run_preserved_as_intermediate": True, "new_index_clean_run_pending": True}
    win = json.loads((windows / "summary.json").read_text(encoding="utf-8-sig"))
    comparison = json.loads((source / "windows-final-comparison.json").read_text(encoding="utf-8-sig"))
    assert win["head"] == win["head_after"] == COMBINED
    assert win["gate_ok"] is False and win["source_unchanged"] and win["brain_unchanged"]
    assert len(win["script_results"]) == 102 and all(r["returncode"] == 0 for r in win["script_results"])
    assert comparison["skip_ids_unchanged"] and comparison["skip_reasons_equal_after_checkout_path_normalization"]
    assert comparison["same_failure_ids_as_previous_batch"]
    source_status["windows_complete_gate"] = {
        "source_sha": COMBINED, "gate_ok": win["gate_ok"],
        "pytest_main_passed": 5838, "known_baseline_failed": 1, "skipped": 28, "passed_subtests": 98,
        "scripts_succeeded": 102, "controlled_timing_passed": 4,
        "source_files_unchanged": win["source_snapshot_after"]["file_count"], "source_unchanged": True, "brain_unchanged": True,
        "failure_scope": "Existing Windows symlink capability P1 assertion; same failed ID as previous batch.",
        "skip_scope": "IDs unchanged; reasons equal only after checkout-path normalization. The original unnormalized false comparison flag is preserved.",
        "driver_original_sha256": legacy_before, "raw_directory": "integration-windows"}
    for name in ("baseline-symlink-p1.log", "baseline-symlink-p1.xml"):
        path = source / name
        copy(path, Path("integration-windows") / name)
    baseline_p1_xml = source / "baseline-symlink-p1.xml"
    report = ET.parse(baseline_p1_xml).getroot()
    cases, failures = report.findall(".//testcase"), report.findall(".//failure")
    assert len(cases) == 1 and cases[0].get("name") == "test_p1_符号链接量具能力探测"
    assert len(failures) == 1 and "竟成功" in failures[0].attrib.get("message", "")
    case_raw = subprocess.check_output(["git", "show", BASE+":tests/test_issue498_atomic_write_perm_symlink_guard.py"], cwd=repo)
    case_text = case_raw.decode("utf-8")
    start = case_text.index("def test_p1_符号链接量具能力探测")
    end = case_text.find("\ndef ", start+5)
    case_body = case_text[start:] if end < 0 else case_text[start:end]
    assert "assert POSIX" in case_body and "symlink" in case_body
    source_status["baseline_windows_symlink_p1"] = {
        "baseline": BASE, "raw_xml": "integration-windows/baseline-symlink-p1.xml",
        "raw_log": "integration-windows/baseline-symlink-p1.log", "tests": 1, "failed": 1, "exit_code": 1,
        "test_id": "tests.test_issue498_atomic_write_perm_symlink_guard::test_p1_符号链接量具能力探测",
        "source_test_sha256": prep.sha(case_raw), "same_test_body": True,
        "host_capability": "Windows symlink creation succeeded; baseline test expects POSIX and fails its capability assertion.",
        "excluded_from_full_gate_counts": True}
    source_status["scope"] = "four local scoped sets, independent combined reconstruction and complete Windows gate (baseline failure retained); remote CI and final index-clean Linux benchmark import pending"
    receipts = json.loads((source / "intake-receipts.json").read_text(encoding="utf-8-sig"))
    assert [receipts[str(pr)]["issue_number"] for pr in range(1477,1481)] == [2791,2792,2793,2794]
    assert all(row["verified"] for row in receipts.values())
    source_status["bounty_intake_receipts"] = {"directory": "publication-receipts", "issue_numbers": [2791,2792,2793,2794],
        "initial_evidence_commit": EXPECTED, "note": "Original create/readback receipts and posted first-body drafts retained; later evidence-link updates are separate."}
    publish(Path("source-status.json"), prep.dumps(source_status))
    junit["runs"] = list(junit_by_path.values())
    publish(Path("junit-index.json"), prep.dumps(junit))
    publish(Path("integration-independent/excluded-temporary-files.json"), prep.dumps({"files": excluded}))
    readme = (target / "README.md").read_text(encoding="utf-8")
    readme = readme.replace("Combined integration and remote CI validation will be added later.",
                            "Complete combined repository gates and remote CI results will be added later.")
    readme = readme.replace("Complete combined repository gates and remote CI results will be added later.",
                            "The complete Windows gate is retained below with its baseline failure; remote CI and final Linux benchmark evidence will be appended separately.")
    marker = "## Independent combined-source review append"
    if marker not in readme:
        readme += """\n## Independent combined-source review append

`integration-independent` contains the finalized independent reconstruction of
the twelve contribution heads onto combined source
`5226860c1d70bc7fc6619cf79aff10c4f9a2a234`, its scoped 165-test execution,
registration audits and cross-fix probes. Temporary pytest databases are
excluded. The complete Windows/Linux gates remain separate pending evidence.

`cross-model-box-invariance` preserves the public-API metamorphic comparison
of 0/1/2 registered boxes across four environment models, three up axes and
three step sizes: 108 scenes, 648 ticks and 3,024 checks per source, with zero
fixed failures and 602 baseline failures. It complements the independent
free-fall analytic oracle; simulator agreement under this transformation is
not a proof of exhaustive physical accuracy. Input/import/source hashes and
all individual rows are retained in the reports.

Linux benchmark/mutation run `44766869622` was launched from the first evidence
commit `f769b3ac33eb5221ad66f6a4384aa6429b26e597`; its results are not imported
by this append. The workflow now filters pushes to the runner file alone, so
later raw-evidence or workflow-configuration edits do not retrigger it.
"""
    if "## Linux artifact-index metadata correction" not in readme:
        readme += """\n## Linux artifact-index metadata correction

The first Linux benchmark run `44766869622` remains valid recorded execution
of its actual measurements and is retained as an intermediate run. Its runner
generated the inner index before writing `validation-summary.json` and before
the final print appended to live `driver.log`, leaving that log's inner digest
stale. This is an index-metadata defect, not a production or benchmark-oracle
failure; the original uploaded data must not be rewritten to hide it.

The runner now writes the final validation summary before generating its index.
The index explicitly excludes itself, live `driver.log` and temporary/database
files. The four standard-library fixtures in `tools/test_round2_artifact_index.py`
prove summary inclusion, stable listed hashes after live-log append, and
detection of same-size listed-file or summary tampering. Raw fixture output is
in `linux-index-fixture`. Production source `5226860` is unchanged. Changing
the runner will trigger a fresh three-matrix benchmark run; its final results
will be appended separately.
"""
    if "## Complete Windows gate and intake receipts" not in readme:
        readme += """\n## Complete Windows gate and intake receipts

`integration-windows` preserves every completed script log, pytest log/JUnit,
timing rerun, dependency list, console/install/lint output and final comparison.
The exact source is `5226860`: 5,838 ordinary pytest passes, one existing
Windows symlink P1 failure, 28 skips and 98 passed subtests. All 102 script
tests and the four controlled timing tests succeeded; source 1,634 files and
the pinned brain remained unchanged. **The original gate result is false**;
it is not relabeled as a fully green Windows gate. Failed IDs match the prior
batch. Skip IDs are unchanged and reasons agree after checkout-path
normalization; original unnormalized comparison flags remain untouched.

`tools/portable_final_gate.py` is a copied original from the earlier output
directory (SHA-256 `d76b23c179e4940b0798101ef196b8d6405692cf6fca6e43c4815b1fc78bec45`);
that original was read only. Temporary data and databases are excluded.
`publication-receipts` retains the four initial intake bodies and verified
create/readback receipts for bounty issues 2791–2794, which initially linked
the first scoped evidence commit. Later body/evidence-link updates are separate.
"""
    if "## Baseline symlink P1 isolated rerun" not in readme:
        readme += """\n## Baseline symlink P1 isolated rerun

The unchanged POSIX-only symlink capability test was rerun alone on the exact
`d74848f` baseline and Windows host. Windows symlink creation succeeded, then
the test's POSIX assertion failed (one test, exit 1). The exact test-source
blob, log and JUnit are retained. This isolated diagnostic is excluded from
the full-gate test totals; it independently reproduces the same known baseline
failure instead of adding a new defect or changing any gate count.
"""
    publish(Path("README.md"), readme.encode("utf-8"))
    tool = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    publish(Path("tools/append_round2_final_review.py"), tool)
    subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    blobs = prep.staged_blobs(repo, [(PREFIX / name).as_posix() for name in records])
    for name, item in records.items():
        blob = blobs[(PREFIX / name).as_posix()]
        assert prep.sha(blob) == item["published_sha256"] and len(blob) == item["published_bytes"], name
        item["git_canonical_blob_sha256"], item["git_canonical_blob_bytes"] = prep.sha(blob), len(blob)
        if name.endswith(".json"):
            json.loads(blob, parse_constant=prep.reject_constant)
        if name.endswith(".xml"):
            ET.fromstring(blob)
    manifest["artifacts"] = list(records.values())
    (target / "sanitization-manifest.json").write_bytes(prep.dumps(manifest))
    audit = json.loads(subprocess.check_output(["git", "show", EXPECTED+":"+(PREFIX/"preparation-audit.json").as_posix()], cwd=repo))
    audit["checks"]["numeric_json_leaves_verified"] += counts["numeric_json_leaves_preserved"]
    audit["checks"]["xml_semantics_verified"] += counts["xml_semantics_preserved"]
    audit["checks"]["json_copied"] += sum(name.endswith(".json") for name in copied)
    audit.update({"status": "review/cross-model append staged only; complete gates/CI pending",
                  "base_evidence_commit": EXPECTED, "artifact_count": len(records),
                  "published_bytes": sum(r["published_bytes"] for r in records.values()),
                  "canonical_blob_hashes_verified": len(records),
                  "staged_files": len(records)+2,
                  "remaining_slices": ["complete Linux gate/raw PR CI import", "final index-clean Linux benchmark/mutation results"],
                  "latest_append": {"copied_files": len(copied), "temporary_files_excluded": len(excluded), **counts}})
    (target / "preparation-audit.json").write_bytes(prep.dumps(audit))
    subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "--", ".github/workflows/body-round2-benchmarks.yml"], cwd=repo, check=True, capture_output=True)
    assert subprocess.check_output(["git", "diff", EXPECTED, "--", (PREFIX / "tools/run_round2_linux_benchmarks.py").as_posix()], cwd=repo), "metadata correction must update the runner"
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
