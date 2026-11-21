"""Build the exact allowlisted neighbors public slice; no Git or remote writes.

Core string-token JSON and structural XML checks are a read-only adaptation of
the world slice helper. Third-party issue/comment bodies are never published.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

import public_slice_core as core

SCALARS = {"query", "total_count", "incomplete_results", "number", "title", "state",
           "id", "node_id", "url", "html_url", "issue_url", "repository_url", "oid",
           "createdAt", "updatedAt", "closedAt", "mergedAt", "submittedAt",
           "created_at", "updated_at", "closed_at", "headRefOid", "baseRefOid",
           "path", "additions", "deletions", "changeType", "nameWithOwner"}
CONTAINERS = {"items", "comments", "files", "mergeCommit", "reviews", "repository"}
THIRD_PARTY = ["hexgrid-duplicate-search.json", "hexgrid-duplicate-search-broad.json",
               "issue6.json", "issue18.json", "issue43-full.json", "pr1254-full.json",
               "pr1254-inline-comments.json", "pr1473-full.json", "pr1473-inline-comments.json",
               "bounty183.json", "bounty2787-full.json"]


def metadata(value):
    if isinstance(value, list):
        return [metadata(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == "body":
            assert isinstance(item, str)
            raw = item.encode("utf-8")
            result["body_sha256_utf8"] = core.sha(raw)
            result["body_utf8_bytes"] = len(raw)
        elif key in SCALARS:
            assert not isinstance(item, (dict, list))
            result[key] = item
        elif key in CONTAINERS:
            result[key] = metadata(item)
    return result


def assert_no_bodies(value):
    if isinstance(value, list):
        for item in value:
            assert_no_bodies(item)
    elif isinstance(value, dict):
        assert "body" not in value and "bodyText" not in value and "diff" not in value
        for item in value.values():
            assert_no_bodies(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source, repo, output = args.source.resolve(), args.repo.resolve(), args.output.resolve()
    assert source.is_dir() and repo.is_dir() and output not in (source, repo)
    output.mkdir(parents=True, exist_ok=True)
    redact = core.redactor(source, repo)
    records, targets = [], set()

    def put(path, relative, label, status="final", projection=None):
        relative = Path(relative)
        assert not relative.is_absolute() and ".." not in relative.parts
        assert relative.suffix in core.ALLOWED
        assert not any(part in core.DENIED_PARTS for part in relative.parts)
        dest = (output / relative).resolve()
        assert dest.is_relative_to(output)
        assert relative.as_posix() not in targets
        targets.add(relative.as_posix())
        raw = path.read_bytes()
        original_stat = path.stat()
        text = raw.decode("utf-8-sig")
        projected = projection is not None
        if projected:
            expected = projection(core.parse(text))
            assert_no_bodies(expected)
            text = core.encode(expected) + "\n"
            assert core.parse(text) == expected
        if relative.suffix in (".json", ".jsonl"):
            public = core.json_redact(text, redact, lines=relative.suffix == ".jsonl")
            checks = {"json_keys_values_checked": True, "nonstring_tokens_byte_identical": True,
                      "projection_numeric_values_preserved": True if projected else None}
            if projected:
                assert_no_bodies(core.parse(public))
                checks["all_third_party_bodies_withheld"] = True
        elif relative.suffix == ".xml":
            public, numeric = core.xml_redact(text, redact)
            checks = {"xml_structure_and_text_checked": True,
                      "exact_numeric_attributes_checked": numeric}
        else:
            public, checks = redact(text), {}
        payload = public.encode("utf-8")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        assert dest.read_bytes() == payload
        current_stat = path.stat()
        assert (original_stat.st_size, original_stat.st_mtime_ns) == (
            current_stat.st_size, current_stat.st_mtime_ns)
        assert path.read_bytes() == raw
        records.append({"source": label, "public": relative.as_posix(), "status": status,
                        "raw_sha256": core.sha(raw), "raw_bytes": len(raw),
                        "projected_input_sha256": core.sha(text.encode("utf-8")) if projected else None,
                        "public_sha256": core.sha(payload), "public_bytes": len(payload),
                        "projection": projected, "checks": checks})

    def local(name, dest, status="final", projection=None):
        path = (source / name).resolve()
        assert path.is_relative_to(source) and path.is_file()
        put(path, dest, name, status, projection)

    delivery_raw = (source / "NEIGHBORS_DELIVERY.json").read_bytes()
    delivery = core.parse(delivery_raw.decode("utf-8"))
    assert len(delivery["evidence_artifacts"]) == 30
    for item in delivery["evidence_artifacts"]:
        path = source / item["file"]
        raw = path.read_bytes()
        assert len(raw) == item["bytes"] and core.sha(raw) == item["sha256"]
        local(item["file"], "final/" + item["file"])
    local("NEIGHBORS_DELIVERY.json", "provenance/NEIGHBORS_DELIVERY.json",
          "historical local delivery before publication; original status preserved")

    for name in ["HEXGRID_NEIGHBORS_AUDIT.md", "probe_hexgrid_neighbors.py",
                 "hexgrid-neighbor-oracle.json", "hexgrid-neighbor-oracle.log"]:
        local(name, "initial04/" + name, "original read-only04 audit; no production edits")
    for path in sorted((source / "neighbors-replay-original04").iterdir()):
        assert path.is_file() and path.suffix in {".json", ".xml", ".log"}
        local(path.relative_to(source).as_posix(), "original04-guard-replay/" + path.name,
              "later unchanged final30 guard applied to exact04 source; not original audit time")
    for name in ["neighbors-replay-original04-driver.log", "neighbors-original04-baseline-equivalence.json"]:
        local(name, "original04-guard-replay/" + name,
              "later original04 replay and raw-byte04/6b source equivalence")

    for name in ["tests/test_hexgrid_odd_r_neighbors.py", "tests/fixtures/hexgrid_odd_r_neighbors_mutations.json",
                 "bench/bench_hexgrid_neighbors.py", "tools/testing/replay_save_guards.py",
                 "docs/validation/hexgrid_odd_r_neighbors_20261121.md"]:
        put(repo / name, "final/repository/" + name, "<repo>/" + name)
    for name in THIRD_PARTY:
        local(name, "dedup/" + name, "metadata/body-hash projection; all issue/comment bodies withheld", metadata)
    local("public-slice-helper-origin.json", "helpers/public-slice-helper-origin.json",
          "read-only world helper reuse provenance")
    put(source / "public_slice_core.py", "helpers/public_slice_core.py", "public_slice_core.py",
        "copied reusable token/semantic validation functions")
    put(Path(__file__).resolve(), "helpers/prepare_public_neighbors_slice.py",
        "prepare_public_neighbors_slice.py", "self-authored reproducible public-slice helper")

    tests = core.self_test()
    sample = {"number": 17, "comments": [{"id": 12345678901234567890, "body": "private unique body"}],
              "body": "another private body", "author": {"login": "omitted"}}
    projected = metadata(sample)
    assert_no_bodies(projected)
    assert projected["number"] == 17 and projected["comments"][0]["id"] == 12345678901234567890
    assert "private unique body" not in core.encode(projected)
    tests["third_party_body_hash_projection"] = True
    info = {"schema": 1, "source": "path-redacted allowlist from audit-numeric",
            "head": "4a352249ef6db7975353b84bc640712d46f7181b",
            "measured_head": "df0838c2181abf5fb1dc8e1e4b0dfcb66c19a232",
            "production_sha256_lf": delivery["source_sha256"], "full_gate_included": False,
            "delivery_artifacts_verified": 30, "self_tests": tests, "file_count": len(records),
            "entries": records,
            "excluded": ["public-index.json (self)", "README.md (explanation)",
                         "all third-party issue/comment bodies", "authors/user payloads",
                         "full issue aggregates", "full production/baseline/brain trees", "ZIP/DB/pyc/cache",
                         "live collector aggregates", "unrelated world/core/raw body evidence"],
            "third_party_snapshot_inventory": [{"name": name,
                "raw_sha256": core.sha((source / name).read_bytes()),
                "raw_bytes": (source / name).stat().st_size, "full_body_included": False}
                for name in THIRD_PARTY]}
    (output / "public-index.json").write_text(core.encode(info) + "\n", encoding="utf-8", newline="\n")
    readme = """# Neighbors public evidence slice

Final local implementation head: `4a352249ef6db7975353b84bc640712d46f7181b`
(PR #1481). The paired Windows benchmark actually measured clean
`df0838c2181abf5fb1dc8e1e4b0dfcb66c19a232`; the final documentation commit did
not change source/guard/spec/benchmark. Historical delivery status remains
unchanged in its original metadata even though the parent later published.

The 30 hash-bound delivery artifacts are all retained. `initial04/` preserves
the original clean04 point-cloud probe, report and red baseline output.
`original04-guard-replay/` is explicitly a later replay of the unchanged final
guard against exact original04 source: 19 behavior failures/11 passes versus
30 fixed passes. It is not relabeled as having run during the initial audit.
The relevant source is byte-identical between04 and the accepted6b baseline.

JSON sanitization changes string tokens only, including dictionary keys;
all non-string tokens and numeric lexemes are byte-identical after any explicit
metadata projection. Projection keeps selected metadata/counts and body hashes,
using Decimal-preserving serialization, and withholds all issue/comment bodies
and author/user payloads. `initial04/HEXGRID_NEIGHBORS_AUDIT.md` is our own
historical analysis; references to full private snapshots name their original
audit storage, not files included in this public slice. The public versions of
those snapshots are metadata/body-hash projections under `dedup/`.

XML structure/text after path redaction and exact numeric attributes are
verified after serialization. Absolute workspace/user/runner paths become
placeholders. Standalone probe path placeholders need the target checkout
configured before use. Helpers are retained and accept explicit source/repo/
output arguments; reuse copied only world helper functions and did not edit
the world helper, world slice, production tree or frozen round-two evidence.

`public-index.json` lists every included artifact's raw/public byte count and
SHA256, projection state and checks. It excludes itself and this explanatory
README to avoid self-reference. No complete issue/comment body, baseline/brain
tree, database/cache, ZIP archive or full old body aggregation is included.

This slice contains adjacent Windows tests and historical probes, not a whole
Windows gate. Original `full_repo_gate_rerun=false` is preserved. Separate
remote full-gate CI and combined Linux benchmark artifacts belong to the
parent's distinct verified packets; they are not fabricated or mixed here.
Odd-r correction has measured timing cost1.302–1.637x; tracemalloc describes
Python allocations, not RSS/native memory. CNN's old image segments4–6 remain
skipped because the upstream image asset was not exported.
"""
    (output / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
    assert actual == targets | {"public-index.json", "README.md"}
    leak_pattern = r'(?i)(?<![a-z0-9])[a-z]:[\\/]+|[\\/]+users[\\/]+[0-9]+|' + re.escape('/'.join(('', 'home', 'runner')))
    leaks = [path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()
             and re.search(leak_pattern, path.read_text(encoding="utf-8"))]
    assert not leaks, leaks
    for item in records:
        raw = (output / item["public"]).read_bytes()
        assert core.sha(raw) == item["public_sha256"] and len(raw) == item["public_bytes"]
    print(json.dumps({"files": len(records), "public_bytes": sum(row["public_bytes"] for row in records),
                      "self_tests": tests, "path_leaks": leaks,
                      "public_index_sha256": core.sha((output / "public-index.json").read_bytes())}))


if __name__ == "__main__":
    main()
