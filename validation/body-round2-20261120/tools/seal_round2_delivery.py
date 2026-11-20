"""Seal completed round-two evidence, retaining data and its source digests.

Run only after the final benchmark collector is complete. Does not commit,
push, create issues or modify any production source checkout.
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


PREFIX = Path("validation/body-round2-20261120")
SOURCE = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
BENCH_RUN = 44778606930
BENCH_HEAD = "ff22bf03a53e422fedc029fbd0d24445aef3dbe7"
ALLOWED = {".json", ".jsonl", ".xml", ".log", ".txt", ".py", ".md", ".yml", ".patch"}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    target = repo / PREFIX
    spec = importlib.util.spec_from_file_location("seal_prep", target / "tools/prepare_round2_public_evidence.py")
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    final_dir = source / "audit-world/ci-round2/final-44778606930"
    final = json.loads((final_dir / "summary.json").read_text(encoding="utf-8"))
    assert final["run_id"] == BENCH_RUN and final["metadata_head"] == BENCH_HEAD
    assert final["measured_source_head"] == SOURCE
    assert final["all_complete"] and final["all_verified_success"] and final["inner_artifact_indexes_clean"]
    assert len(final["jobs"]) == len(final["artifact_validations"]) == 3
    assert all(row["conclusion"] == "success" for row in final["jobs"])
    windows = json.loads((source / "integration-windows/summary.json").read_text(encoding="utf-8"))
    assert windows["head"] == windows["head_after"] == SOURCE
    assert windows["source_unchanged"] and windows["brain_unchanged"]
    assert windows["source_snapshot_before"]["file_count"] == 1634
    assert windows["gate_ok"] is False and len(windows["failed_tests"]) == 1
    assert "test_p1_符号链接量具能力探测" in windows["failed_tests"][0]["test"]
    assert len(windows["script_results"]) == 102 and all(r["returncode"] == 0 for r in windows["script_results"])
    for key in ("controlled_timing", "strict_manifest", "time_core_lint"):
        assert windows[key]["returncode"] == 0
    comparison = json.loads((source / "windows-final-comparison.json").read_text(encoding="utf-8"))
    assert comparison["skip_ids_unchanged"] and comparison["skip_reasons_equal_after_checkout_path_normalization"]
    assert comparison["same_failure_ids_as_previous_batch"]
    remote = json.loads((target / "remote-ci/summary.json").read_text(encoding="utf-8"))
    assert len(remote["pull_requests"]) == 4 and remote["combined"]["source_head"] == SOURCE
    receipts = json.loads((source / "intake-receipts.json").read_text(encoding="utf-8"))
    assert all(receipts[str(n)]["verified"] and receipts[str(n)]["issue_number"] == n + 1314
               for n in range(1477, 1481))

    original_manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    records = {r["artifact"]: r for r in original_manifest["artifacts"]}
    copied = []
    archives = []
    numbers = 0

    def redact(value):
        if isinstance(value, str):
            return prep.sanitize(value)
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                clean_key = prep.sanitize(key)
                assert clean_key not in result, "path redaction collapsed distinct JSON keys"
                result[clean_key] = redact(item)
            return result
        return value

    def write_generated(relative, value):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = prep.dumps(value) if not isinstance(value, str) else value.encode("utf-8")
        path.write_bytes(payload)
        records[relative] = {"artifact": relative, "mode": "generated_verified_closure",
                             "source": "verified completed delivery records", "original_sha256": None,
                             "original_bytes": None, "published_sha256": sha(payload), "published_bytes": len(payload)}

    def copy(path, relative):
        nonlocal numbers
        raw = path.read_bytes()
        text = re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))
        if path.suffix == ".json":
            original = json.loads(text, parse_constant=prep.reject_constant)
            out = redact(original)
            payload = prep.dumps(out)
            assert prep.numeric_leaves(original) == prep.numeric_leaves(json.loads(payload))
            numbers += len(prep.numeric_leaves(original))
        else:
            payload = prep.sanitize(text).encode("utf-8")
        if path.suffix == ".xml":
            before, after = ET.fromstring(text), ET.fromstring(payload)
            def sem(e):
                return (e.tag, {k: prep.sanitize(v) for k, v in e.attrib.items()},
                        prep.sanitize(e.text or ""), prep.sanitize(e.tail or ""), [sem(x) for x in e])
            assert sem(before) == sem(after)
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        records[relative] = {"artifact": relative, "mode": "sanitized_verbatim_numeric_preserving",
                             "source": path.relative_to(source).as_posix(),
                             "original_sha256": sha(raw), "original_bytes": len(raw),
                             "published_sha256": sha(payload), "published_bytes": len(payload)}
        copied.append(relative)

    for directory, label in ((source / "audit-world/ci-round2/linux-benchmarks/artifacts", "linux-benchmarks/intermediate-44766869622/extracted"),
                             (final_dir, "linux-benchmarks/final-44778606930")):
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(directory)
            if any(p in {"tmp", "sandbox", "__pycache__"} or p.startswith("guard-") for p in rel.parts):
                continue
            if path.suffix == ".zip":
                archives.append({"source": path.relative_to(source).as_posix(), "sha256": sha(path.read_bytes()),
                                 "bytes": path.stat().st_size,
                                 "policy": "original downloaded archive retained privately; extracted original outputs and digests published"})
                continue
            if path.suffix not in ALLOWED:
                continue
            copy(path, (Path(label) / rel).as_posix())
    for name in ("fixture-final-clean.log",):
        if (source / name).exists():
            copy(source / name, "linux-index-fixture/root-final-fixture.log")

    status = json.loads((target / "source-status.json").read_text(encoding="utf-8"))
    status["scope"] = "Completed four-fix delivery batch; continuous contribution goal remains active. Linux gates and benchmark/mutation matrices PASS; Windows full-gate known baseline failure preserved."
    status["linux_benchmark_final"] = {"run_id": BENCH_RUN, "metadata_head": BENCH_HEAD,
        "measured_source_head": SOURCE, "jobs": 3, "all_verified_success": True,
        "inner_artifact_indexes_clean": True, "named_mutants_per_job": 27,
        "actual_benchmark_source_hashes_and_xml_assertions_independently_verified": True,
        "directory": "linux-benchmarks/final-44778606930"}
    status["linux_artifact_index_metadata_correction"]["new_index_clean_run_pending"] = False
    status["remaining_scope"] = {"unavailable_authentic_model_or_pixel_asset_cases": 17,
        "note": "No original assets were invented. Windows cannot express three POSIX permission modes, exercised in the complete Linux jobs. Historical/symlink/timing supplements are separate from main counts."}
    write_generated("source-status.json", status)
    write_generated("archive-source-digests.json", {"archives": archives,
        "note": "Uploaded artifact ZIP digests independently matched GitHub. Public text applies declared path/LF normalization; source and canonical digests are separate."})

    report = f"""# Round-two body repair delivery — verified evidence\n\nThe four new PRs1477–1480 and corresponding bounty intakes2791–2794 were submitted and read back. This delivery batch is complete; the continuous contribution goal remains active. Prior eight submissions are retained, not duplicated.\n\nFrozen combined production source: `{SOURCE}`; tree `529e1e150aa2c05a2f5bee3126c4678a58695e21`.\n\n- New guards165 pass; all27 named mutants are rejected by their exact semantic assertions with no errors/skips. Baseline failures and every intermediate sample are retained.\n- Each new PR's three complete Linux gate legs and title check pass at its exact head; `remote-ci/` includes full job logs and API identities.\n- Complete combined Linux run44764384747: each of three environments5827 passed/40 skipped/98 subtests,102 script tests and actual pinned brain23/23.\n- Complete Windows gate:5838 passed/**1 known baseline symlink-capability P1 failure**/28 skipped/98 subtests;102 scripts, serial timing4, strict manifest64/64 and time lint23registered/0new/0stale. Original `gate_ok=false` remains. Source1634 files and brain are unchanged.\n- The same isolated P1 assertion fails on original d74848 baseline under actual Windows symlink capability. Historical-baseline physics supplement43 passes, original symlink bodies3/3 pass, and controlled timing4 passes; these overlap and are not added to the main counts.\n- Index-clean Linux benchmark run{BENCH_RUN}, metadata `{BENCH_HEAD}`, measured production source `{SOURCE}`: three environments each run all four A/B benchmarks and27 mutants. Source hashes, XML assertions, all timings and allocations are independently verified; all indexed lengths/hashes match after the final summary is written.\n- First Linux run44766869622 is retained as intermediate: actual measurements passed; only live driver.log's old inner-index digest was stale. Original data was not rewritten.\n\nIndependent integration reconstruction confirms ten production files and29 changed functions equal the twelve PR patch union;52 paths are attributable and old camera fixes remain.\n\nAll raw timing samples, allocation peaks, negative baseline/mutant results, skipped and unexecuted checks remain visible. Shared-host numbers are descriptive, not speed claims.17 original model/pixel-asset cases remain unavailable; assets are not fabricated.\n\n## Evidence layout\n\n- `audit-core`, `audit-circular`, `audit-world`, `audit-numeric`: all local scoped iterations.\n- `integration-independent`: independent patch/function/manifest/lint audit.\n- `cross-model-box-invariance`:108 public-API scenes,648 ticks,3024 checks per source; fixed0 failures, baseline602. This metamorphic test complements independent analytic freefall checks, not exhaustive physics proof.\n- `integration-windows`, `windows-supplements`: original full-gate failure and separate supplements.\n- `remote-ci`: exact PR/combined source jobs and complete logs.\n- `linux-benchmarks/intermediate-44766869622`, `linux-benchmarks/final-44778606930`: all original iterations and final clean inventory.\n- `publication-receipts`: initial intake readbacks; final immutable-link readbacks are appended separately.\n\nPath/home prefixes become `[workspace]` and `[user-home]`; line endings are LF. JSON numeric leaves and XML content are checked before/after. Source and public canonical Git blob digests are both recorded. Compressed convenience copies are represented by original archive digests while extracted outputs are preserved. All overlapping runs must not be summed.\n\nThe public manifest excludes only itself and detached sealing audits to avoid self-reference. Bytecode, databases, temporary environments, full third-party issue bodies and aggregate dumps are excluded.\n"""
    write_generated("README.md", report)
    write_generated("FINAL_VALIDATION.md", report)

    # Add generated controls and reports not yet registered, without harvesting
    # bytecode, temporary databases or environment files created during editing.
    detached = {"sanitization-manifest.json", "preparation-audit.json", "final-seal-audit.json"}
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        name = path.relative_to(target).as_posix()
        if name in detached or any(p in {"__pycache__", "tmp", "sandbox", "pytest-tmp"}
                                   for p in path.relative_to(target).parts):
            continue
        if name in records:
            if name.endswith(".json"):
                payload_before = path.read_bytes()
                parsed = json.loads(payload_before, parse_constant=prep.reject_constant)
                redacted = redact(parsed)
                assert prep.numeric_leaves(parsed) == prep.numeric_leaves(redacted), name
                if redacted != parsed:
                    assert sha(payload_before) == records[name]["published_sha256"], name
                    payload_after = prep.dumps(redacted)
                    path.write_bytes(payload_after)
                    records[name]["pre_key_redaction_published_sha256"] = sha(payload_before)
                    records[name]["published_sha256"] = sha(payload_after)
                    records[name]["published_bytes"] = len(payload_after)
                    records[name]["json_object_keys_also_redacted"] = True
            # Only the two intentionally updated runner controls may differ from
            # the previous capture. Other measured artifacts must match first.
            if name not in {"tools/run_round2_linux_benchmarks.py", "tools/test_round2_artifact_index.py"}:
                assert sha(path.read_bytes().replace(b"\r\n", b"\n")) == records[name]["published_sha256"], name
            else:
                payload = path.read_bytes().replace(b"\r\n", b"\n")
                records[name] = {"artifact": name, "mode": "verified_index_metadata_control",
                                 "source": f"Git metadata head {BENCH_HEAD}", "original_sha256": sha(payload),
                                 "original_bytes": len(payload), "published_sha256": sha(payload), "published_bytes": len(payload)}
            continue
        if path.suffix in ALLOWED or (not path.suffix and "artifact-reconstruction" in path.parts):
            payload = path.read_bytes().replace(b"\r\n", b"\n")
            path.write_bytes(payload)
            records[name] = {"artifact": name, "mode": "generated_control_or_audit",
                             "source": "completed root evidence recovery", "original_sha256": None,
                             "original_bytes": None, "published_sha256": sha(payload), "published_bytes": len(payload)}
    junit = []
    for name in records:
        path = target / name
        if name.endswith(".xml"):
            root = ET.fromstring(path.read_bytes())
            suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
            junit.append({"artifact": name, "suites": [dict(s.attrib) for s in suites]})
        if name.endswith(".json"):
            json.loads(path.read_bytes(), parse_constant=prep.reject_constant)
    write_generated("junit-index.json", {"policy": "Raw per-run counters; overlapping/supplementary runs are not summed.", "runs": junit})

    listed = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo).decode("utf-8").split("\0")
    caches = [p for p in listed if p.startswith(PREFIX.as_posix() + "/")
              and ("/__pycache__/" in p or p.endswith((".pyc", ".db", ".sqlite", ".sqlite3")))]
    if caches:
        subprocess.run(["git", "reset", "-q", "HEAD", "--", *caches], cwd=repo, check=True)
    selected = [(PREFIX / name).as_posix() for name in records]
    for start in range(0, len(selected), 120):
        subprocess.run(["git", "add", "-f", "--", *selected[start:start+120]], cwd=repo,
                       check=True, capture_output=True)
    blobs = prep.staged_blobs(repo, selected)
    private = re.compile(rb"(?i)(?:[ce]:[\\/]+(?:users|lingshu|\xe5\x85\xac\xe7\x9b\x8a\xe7\xab\x99))")
    for name, row in records.items():
        blob = blobs[(PREFIX / name).as_posix()]
        assert sha(blob) == row["published_sha256"] and len(blob) == row["published_bytes"], name
        assert not private.search(blob), name
        assert not name.endswith((".pyc", ".db", ".sqlite", ".sqlite3"))
        row["git_canonical_blob_sha256"], row["git_canonical_blob_bytes"] = sha(blob), len(blob)
    manifest = {"policy": original_manifest["policy"], "artifacts": list(records.values())}
    (target / "sanitization-manifest.json").write_bytes(prep.dumps(manifest))
    audit = {"ok": True, "source_sha": SOURCE, "linux_benchmark_run": BENCH_RUN,
             "canonical_blobs_verified": len(records), "artifact_count": len(records),
             "new_benchmark_files_copied": len(copied), "new_numeric_leaves_preserved": numbers,
             "xml_files": len(junit), "windows_gate_ok": False,
             "windows_failure_preserved": "existing POSIX-only symlink capability assertion",
             "scope": "completed four-fix batch; continuous contribution goal remains active",
             "detached_metadata": sorted(detached)}
    (target / "final-seal-audit.json").write_bytes(prep.dumps(audit))
    (target / "preparation-audit.json").write_bytes(prep.dumps({
        **audit, "status": "verified completed four-contribution evidence seal",
        "staged_evidence_files": len(records) + len(detached),
        "manifest_and_detached_audits_excluded_from_own_digest_list": True,
        "numeric_json_object_keys_and_values_redacted_without_key_collisions": True}))
    subprocess.run(["git", "add", "-f", "--", (PREFIX / "sanitization-manifest.json").as_posix(),
                    (PREFIX / "final-seal-audit.json").as_posix(),
                    (PREFIX / "preparation-audit.json").as_posix()], cwd=repo, check=True)
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
