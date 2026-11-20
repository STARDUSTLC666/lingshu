"""Prepare only the stable core/circular evidence slice, without publishing.

Usage: python -X utf8 -B prepare_round2_public_evidence.py --source-root OUT --repo EVIDENCE_WORKTREE
No database, environment, complete third-party issue body or aggregate issue
dump is copied. Staging is scoped to validation/body-round2-20261120.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


PREFIX = Path("validation/body-round2-20261120")
BASE = "d74848fb33dbff1d719959df19d1266a1ac60f44"
CORE_MEASURED = "bae2eaea9fb77e9e451f1b220d17f9096d06ee78"
CORE_FINAL = "89c005b7fdd48f64c603d34c280a4d18a93956f7"
CIRCULAR_FINAL = "e821bbb1fac57fa638640e3caf153caf7f1b1973"
NUMERIC_FINAL = "a357dbbe96905848fd81b7249814576fb2743674"
WORLD_FINAL = "13952c82874fb9ee19a4f1b660e3144134367a53"
COMBINED = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
ALLOWED = {".json", ".jsonl", ".log", ".xml", ".py", ".md", ".patch", ".txt"}
BODY_FILES = {
    "audit-core/issue176.json", "audit-core/issue280.json", "audit-core/issue327.json",
    "audit-core/issue521.json", "audit-core/issue53.json", "audit-core/issue801.json",
    "audit-core/pr830.json", "audit-circular/issue786-full.json",
    "audit-circular/circular-pr-search.json", "audit-circular/circular-bounty-search.json",
    "audit-numeric/spatial_partition_duplicate_search.json",
    "audit-numeric/spatial-bounty-hex_text-search.json",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sanitize(text):
    # Supports normal Windows/forward-slash paths and escaped path strings in logs.
    text = re.sub(r"(?i)\be:[\\/]+lingshu[\\/]*", "[workspace]/lingshu/", text)
    text = re.sub(r"(?i)\be:[\\/]+公益站[\\/]*", "[workspace]/", text)
    return re.sub(r"(?i)\bc:[\\/]+users[\\/]+[^\\/\s\"']+", "[user-home]", text)


def transform(value):
    if isinstance(value, str):
        return sanitize(value)
    if isinstance(value, list):
        return [transform(item) for item in value]
    if isinstance(value, dict):
        return {key: transform(item) for key, item in value.items()}
    return value


def numeric_leaves(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return []
    if isinstance(value, (int, float)):
        return [(type(value).__name__, repr(value))]
    if isinstance(value, list):
        return [leaf for item in value for leaf in numeric_leaves(item)]
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in numeric_leaves(item)]
    raise TypeError(type(value))


def reject_constant(value):
    raise ValueError("nonstandard JSON constant: " + value)


def dumps(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def staged_blobs(repo, paths):
    wanted = set(paths)
    selected = {}
    for entry in subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=repo).split(b"\0"):
        if not entry:
            continue
        meta, path = entry.split(b"\t", 1)
        name = path.decode("utf-8")
        if name in wanted:
            selected[name] = meta.split()[1].decode("ascii")
    assert set(selected) == wanted
    raw = subprocess.check_output(["git", "cat-file", "--batch"], cwd=repo,
                                  input=("\n".join(selected.values()) + "\n").encode("ascii"))
    stream, result = io.BytesIO(raw), {}
    for path, expected in selected.items():
        oid, kind, size = stream.readline().split()
        assert oid.decode("ascii") == expected and kind == b"blob"
        result[path] = stream.read(int(size))
        assert stream.read(1) == b"\n"
    return result


def issue_summary(data):
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        result = issue_summary(data["items"])
        for key in ("query", "total_count", "incomplete_results", "search_type"):
            if key in data:
                result[key] = data[key]
        return result
    if isinstance(data, list) and any(isinstance(item, dict) and "items" in item for item in data):
        return {"policy": "Only identifying metadata retained; bodies/comments omitted.",
                "queries": [issue_summary(item) for item in data]}
    values = data if isinstance(data, list) else [data]
    out = []
    for item in values:
        url = item.get("html_url") or item.get("url", "")
        number = item.get("number")
        if number is None and re.search(r"/(?:issues|pull)/(\d+)", url):
            number = int(re.search(r"/(?:issues|pull)/(\d+)", url).group(1))
        row = {key: item[key] for key in ("title", "url", "state") if key in item}
        if url:
            row["url"] = url
        if number is not None:
            row["number"] = number
        if isinstance(item.get("comments"), list):
            row["comment_count"] = len(item["comments"])
        out.append(row)
    return {"policy": "Only identifying title/URL/state metadata retained; third-party bodies/comments omitted.",
            "records": out}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    target = repo / PREFIX
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() != BASE:
        raise RuntimeError("evidence preparation expects the declared baseline checkout")
    target.mkdir(parents=True, exist_ok=True)
    artifacts, excluded, junit, search_index = [], [], [], []
    counts = Counter()

    def write(relative, payload, original=None, source_name=None, mode="generated"):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        artifacts.append({"artifact": relative.as_posix(), "mode": mode,
                          "source": source_name, "original_sha256": sha(original) if original is not None else None,
                          "original_bytes": len(original) if original is not None else None,
                          "published_sha256": sha(payload), "published_bytes": len(payload)})

    for folder in ("audit-core", "audit-circular", "audit-world", "audit-numeric"):
        for path in sorted((source / folder).rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            name = relative.as_posix()
            if any(p in {"ci-round2", "integration-review"} for p in relative.parts) or path.name in {"bounty-all-issues.json", "lingshu-all-issues.json"}:
                excluded.append({"source": name, "reason": "active CI capture deferred / aggregate all-issue dump excluded"})
                continue
            if path.suffix.lower() not in ALLOWED or any(p in {"__pycache__", ".venv", "venv"} for p in relative.parts):
                excluded.append({"source": name, "reason": "database/binary/environment/non-evidence extension"})
                continue
            raw = path.read_bytes()
            text = re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))
            if name in BODY_FILES:
                metadata = issue_summary(json.loads(text))
                search_index.append({"source": name, **metadata})
                out = relative.parent / "duplicate-source-metadata" / path.name
                write(out, dumps(transform(metadata)), raw, name, "third_party_metadata_projection")
                counts["third_party_body_files_not_copied"] += 1
                continue
            if path.suffix == ".json":
                try:
                    original = json.loads(text, parse_constant=reject_constant)
                except ValueError as exc:
                    # Historical peer-review output contains explicit NaN. Preserve
                    # its exact literal as raw text; never relabel it valid JSON.
                    if "nonstandard JSON constant" not in str(exc):
                        raise
                    write(relative.with_suffix(relative.suffix + ".raw.txt"), sanitize(text).encode("utf-8"), raw, name,
                          "nonstandard_json_preserved_as_raw_text")
                    counts["nonstandard_json_raw_text"] += 1
                    continue
                transformed = transform(original)
                payload = dumps(transformed)
                loaded = json.loads(payload, parse_constant=reject_constant)
                assert numeric_leaves(original) == numeric_leaves(loaded), name
                assert transformed == loaded, name
                counts["numeric_json_leaves_verified"] += len(numeric_leaves(original))
                counts["json_copied"] += 1
            else:
                payload = sanitize(text).encode("utf-8")
            if path.suffix == ".xml":
                before, after = ET.fromstring(text), ET.fromstring(payload)
                def semantic(element):
                    return (element.tag, {k: sanitize(v) for k,v in element.attrib.items()},
                            sanitize(element.text or ""), sanitize(element.tail or ""),
                            [semantic(child) for child in element])
                assert semantic(before) == semantic(after), name
                suites = [after] if after.tag == "testsuite" else after.findall(".//testsuite")
                junit.append({"artifact": relative.as_posix(), "suites": [dict(s.attrib) for s in suites]})
                counts["xml_semantics_verified"] += 1
            if path.suffix == ".jsonl":
                for before, after in zip(text.splitlines(), payload.decode("utf-8").splitlines()):
                    a, b = json.loads(before), json.loads(after)
                    assert numeric_leaves(a) == numeric_leaves(b), name
                counts["jsonl_copied"] += 1
            write(relative, payload, raw, name, "sanitized_verbatim_numeric_preserving")

    def git_blob(ref, path):
        return subprocess.check_output(["git", "show", ref + ":" + path], cwd=repo)
    source_files = {
        "core": (CORE_FINAL, ["bench/bench_fresh_row_decay.py", "tests/test_fresh_row_decay.py",
                              "tests/fixtures/fresh_row_decay_mutations.json",
                              "docs/testing/fresh-row-decay-20261120.md"]),
        "circular": (CIRCULAR_FINAL, ["bench/circular_time_residual.py", "tests/test_circular_time_residual_guard.py",
                                      "tests/fixtures/circular_time_residual_mutations.json",
                                      "docs/testing/circular-time-residual-20261120.md"]),
        "numeric": (NUMERIC_FINAL, ["bench/bench_spatial_detect_partition.py", "tests/test_spatial_detect_complete_partition.py",
                                    "tests/fixtures/spatial_detect_complete_partition_mutations.json",
                                    "docs/testing/spatial-detect-complete-partition-20261120.md"]),
        "world": (WORLD_FINAL, ["bench/bench_scene_collision_freeflight.py", "tests/test_scene_collision_freeflight_velocity.py",
                                "tests/fixtures/scene_collision_freeflight_velocity_mutations.json",
                                "docs/testing/scene-collision-freeflight-velocity-20261120.md"]),
        "shared": (BASE, ["tools/testing/replay_transaction_guards.py", "tools/testing/replay_save_guards.py"]),
    }
    for label, (ref, paths) in source_files.items():
        for path in paths:
            raw = git_blob(ref, path)
            text = re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))
            payload = sanitize(text).encode("utf-8")
            if path.endswith(".json"):
                assert numeric_leaves(json.loads(raw)) == numeric_leaves(json.loads(payload))
            write(Path("replay-sources") / label / path, payload, raw, "git:" + ref + ":" + path,
                  "source_from_exact_git_commit")
    write(Path("duplicate-title-url-index.json"), dumps({"policy": "Identifying metadata only; no third-party body/comment text.",
                                                        "sources": search_index}))
    core_old = git_blob(CORE_MEASURED, "lingshu/core/core.py")
    core_final = git_blob(CORE_FINAL, "lingshu/core/core.py")
    assert core_old == core_final
    mapping = {"baseline": BASE, "scope": "four local scoped evidence sets; combined/CI validation pending",
        "combined_source_sha": COMBINED,
        "core": {"measured_commit": CORE_MEASURED, "final_pr_head": CORE_FINAL,
                 "pr": "https://github.com/FuRongJun-1999/lingshu/pull/1478",
                 "production_canonical_sha256": sha(core_final),
                 "measurement_source_identical_to_final_head": True,
                 "final_head_delta": subprocess.check_output(["git", "diff", "--name-only", CORE_MEASURED, CORE_FINAL], cwd=repo, text=True).splitlines(),
                 "manifest_note": "Prepublication terminal inspection found the old manifest hash; no initial raw file was saved. The final recorded strict result is audit-core/manifest-final.json (64 matches / zero mismatches). No initial raw result is fabricated.",
                 "non_claims": ["Known CSR duplicate-coordinate finding is historical audit evidence, not a new discovery or bounty claim.",
                                "Spatial peer-review results describe the early reviewed tree, not the subsequent final spatial fix."]},
        "circular": {"final_pr_head": CIRCULAR_FINAL,
                     "pr": "https://github.com/FuRongJun-1999/lingshu/pull/1477",
                     "production_canonical_sha256": sha(git_blob(CIRCULAR_FINAL, "lingshu/world/physics.py"))},
        "numeric": {"final_pr_head": NUMERIC_FINAL, "pr": "https://github.com/FuRongJun-1999/lingshu/pull/1480",
                    "final_guard_tests": 70, "final_baseline_failed": 59, "final_baseline_passed": 11,
                    "named_mutations": 6,
                    "production_canonical_sha256": sha(git_blob(NUMERIC_FINAL, "lingshu/nn/hex_text.py")),
                    "history_note": "R1 and intermediate R2 results are retained; old 43/27 counts are intermediate, not final. Final R2 is replay-final-verified."},
        "world": {"final_pr_head": WORLD_FINAL, "pr": "https://github.com/FuRongJun-1999/lingshu/pull/1479",
                  "final_guard_tests": 41, "named_mutations": 6,
                  "production_canonical_sha256": sha(git_blob(WORLD_FINAL, "lingshu/world/scene_simulator.py")),
                  "history_note": "Both R1 and final R2 A/B/replay iterations are retained."},
        "preservation": {"all_available_A_B_measurement_iterations": True,
                         "failed_tests_fit_errors_unexecuted_checks_and_skips_retained": True,
                         "initial_zero_collection_and_incomplete_expected_failure_spec_retained": True,
                         "third_party_full_bodies_copied": False}}
    # Core benchmark records raw Windows checkout bytes. Prove their LF-normalized
    # identity instead of silently substituting the different canonical hashes.
    mapping["core"]["benchmark_source_alignment"] = []
    for name, ref in (("bench-baseline.json", BASE), ("bench-fixed.json", CORE_FINAL)):
        info = json.loads((source / "audit-core" / name).read_text(encoding="utf-8-sig"))
        raw = (Path(info["source_root"]) / "lingshu/core/core.py").read_bytes()
        canonical = git_blob(ref, "lingshu/core/core.py")
        assert sha(raw) == info["source_sha256"] and raw.replace(b"\r\n", b"\n") == canonical
        mapping["core"]["benchmark_source_alignment"].append({"artifact": "audit-core/"+name,
            "recorded_raw_sha256": info["source_sha256"], "canonical_lf_sha256": sha(canonical),
            "raw_source_verified": True, "LF_normalized_bytes_identical_to_declared_commit": True})
    write(Path("source-status.json"), dumps(mapping))
    write(Path("junit-index.json"), dumps({"warning": "Runs overlap and include baseline/mutant/history failures; do not sum as unique coverage.", "runs": junit}))
    write(Path("excluded-files.json"), dumps({"files": excluded, "third_party_policy": "Body-file inputs are represented only by metadata projections, with original input hashes in the artifact manifest."}))
    script = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    write(Path("tools/prepare_round2_public_evidence.py"), script)
    linux_driver = Path(__file__).with_name("run_round2_linux_benchmarks.py").read_bytes().replace(b"\r\n", b"\n")
    write(Path("tools/run_round2_linux_benchmarks.py"), linux_driver)
    readme = """# Round-two evidence — core/circular slice

This staged directory contains all four stable local scoped audit sets.
Combined integration and remote CI validation will be added later.
It does not assert that the full round-two batch or its release gates are complete.

See `source-status.json` for exact baseline, measured and final PR heads. Core
production measurements remain applicable after the manifest-only final commit;
the canonical production blobs were compared byte for byte. The initial stale
manifest was observed in terminal output, without a saved raw file. The final
strict JSON is retained as 64/64; there is no reconstructed initial raw result.

`audit-core` includes the fresh-decay reproduction, all raw A/B latency and
traced-memory samples, test logs/JUnit, all initial/final replay iterations,
and scoped peer-review history. Initial zero-collection output and expected
baseline/mutant failures are retained. Known activation/CSR findings were
excluded from new claims; early spatial review output is historical, not a
claim about its final later source. `audit-circular` retains both complete
benchmark rounds, independent analytic-oracle failures and fit errors, unexecuted
prediction checks, relevant test skips, mutation runs and lint iterations.

`audit-world` and `audit-numeric` retain all R1 and R2 measurements, including
intermediate failed or incomplete validations. Numeric's final guard is 70
tests with baseline 59 failed / 11 passed and six killed mutants; intermediate
43/27 results are not final. Its final replay is `r2/replay-final-verified`.
World's final R2 guard has 41 tests and six named mutants. Both raw A/B rounds
are retained. Active PR-CI captures and the complete Windows/Linux repository
gates are deliberately deferred to the subsequent integration evidence slice.

No databases, virtual environments, aggregate all-issue dumps, or complete
third-party issue/PR bodies/comments are copied. Search inputs containing bodies
are projected to identifying title/URL/state metadata, with original file hashes
for provenance. Literal nonstandard NaN JSON in historical peer-review output
is preserved with a `.json.raw.txt` suffix rather than mislabeled as strict JSON.

Local workspace and user-home prefixes become `[workspace]` and `[user-home]`;
text line endings are LF. JSON numeric leaves and XML semantic content were
compared before/after sanitization. Every published artifact digest in
`sanitization-manifest.json` is checked against the actual staged Git blob,
not an assumed working-tree newline representation. `junit-index.json` keeps
each run's original counters; its overlapping runs must not be summed.

The preparation tool is under `tools/`. Its inputs are the private output root
containing `audit-core`/`audit-circular` and this isolated evidence checkout.
It stages only this directory and does not commit or push. The manifest and
audit report exclude themselves from their digest list to avoid self-reference.

`replay-sources` contains the exact-head benchmark scripts, regression guards,
mutation specifications and scoped reports, plus the unchanged baseline replay
tool. Run the committed benchmark scripts against clean baseline/fixed source
checkouts as their command help describes. `duplicate-title-url-index.json`
consolidates identifying metadata from the body-containing search inputs.
"""
    write(Path("README.md"), readme.encode("utf-8"))
    subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    canonical_blobs = staged_blobs(repo, [(PREFIX / item["artifact"]).as_posix() for item in artifacts])
    for item in artifacts:
        canonical = canonical_blobs[(PREFIX / item["artifact"]).as_posix()]
        assert sha(canonical) == item["published_sha256"] and len(canonical) == item["published_bytes"], item["artifact"]
        item["git_canonical_blob_sha256"] = sha(canonical)
        item["git_canonical_blob_bytes"] = len(canonical)
    audit = {"status": "staged four local scoped evidence sets; combined/CI pending; not committed or pushed",
             "artifact_count": len(artifacts), "published_bytes": sum(a["published_bytes"] for a in artifacts),
             "checks": dict(counts), "canonical_blob_hashes_verified": len(artifacts),
             "remaining_slices": ["integration", "remote CI", "Linux benchmark/mutation workflow results"],
             "manifest_and_audit_excluded_from_own_digest_list": True}
    manifest = {"policy": "Workspace/home path prefixes replaced; LF text; all numeric samples and test outcomes retained. Hashes use staged Git canonical blobs.",
                "artifacts": artifacts}
    (target / "sanitization-manifest.json").write_bytes(dumps(manifest))
    (target / "preparation-audit.json").write_bytes(dumps(audit))
    subprocess.run(["git", "add", "-f", "--", PREFIX.as_posix()], cwd=repo, check=True, capture_output=True)
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "-z"], cwd=repo).decode().split("\0")
    staged = [p for p in staged if p]
    workflow = ".github/workflows/body-round2-benchmarks.yml"
    evidence_staged = [p for p in staged if p.startswith(PREFIX.as_posix() + "/")]
    assert all(p in evidence_staged or p == workflow for p in staged)
    assert len(evidence_staged) == len(artifacts) + 2
    secret_paths = re.compile(rb"(?i)(?:[ce]:[\\/]+(?:users|lingshu|\xe5\x85\xac\xe7\x9b\x8a\xe7\xab\x99))")
    final_blobs = staged_blobs(repo, staged)
    for path in staged:
        blob = final_blobs[path]
        if secret_paths.search(blob):
            raise AssertionError("unsanitized absolute prefix: " + path)
        if path.endswith(".json"):
            json.loads(blob, parse_constant=reject_constant)
        if path.endswith(".xml"):
            ET.fromstring(blob)
        if path.endswith((".db", ".sqlite", ".sqlite3", ".pyc")):
            raise AssertionError(path)
    audit["staged_files"] = len(evidence_staged)
    audit["additional_control_files"] = [p for p in staged if p not in evidence_staged]
    audit["final_parse_and_path_scan"] = "passed"
    (target / "preparation-audit.json").write_bytes(dumps(audit))
    subprocess.run(["git", "add", "-f", "--", (PREFIX / "preparation-audit.json").as_posix()], cwd=repo, check=True, capture_output=True)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
