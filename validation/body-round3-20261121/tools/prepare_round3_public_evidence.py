"""Prepare a redacted, hash-sealed public evidence tree for round three."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile
import xml.etree.ElementTree as ET


PREFIX = Path("validation/body-round3-20261121")
DETACHED = {"sanitization-manifest.json", "seal-audit.json"}
SOURCE = "f81ee3a9939f3dad7c277145766508c113742ba0"
HEADS = {
    1481: "4a352249ef6db7975353b84bc640712d46f7181b",
    1482: "bd208a379e44497e9f35fdc145838abb19e6d313",
}
TEXT_SUFFIXES = {".json", ".jsonl", ".xml", ".log", ".txt", ".py", ".yml", ".md"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dumps(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def redact(value: str) -> str:
    value = re.sub(r"(?i)\be:[\\/]+lingshu[\\/]*", "[workspace]/lingshu/", value)
    value = re.sub(r"(?i)\be:[\\/]+公益站[\\/]*", "[workspace]/", value)
    value = re.sub(r"(?i)\bc:[\\/]+users[\\/]+[^\s\"']+", "[user-home]", value)
    runner_prefix = chr(47) + "home" + chr(47) + "runner" + chr(47)
    runner_path_pattern = re.escape(runner_prefix) + r"[^\s\"']*"
    return re.sub(runner_path_pattern, "[linux-runner-path]", value)


def clean(value: object) -> object:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            new_key = redact(key)
            assert new_key not in result
            result[new_key] = clean(item)
        return result
    return value


def numeric_shape(value: object) -> object:
    if isinstance(value, dict):
        return ("dict", tuple(numeric_shape(item) for item in value.values()))
    if isinstance(value, list):
        return ("list", tuple(numeric_shape(item) for item in value))
    if isinstance(value, str):
        return ("string",)
    return (type(value).__name__, repr(value))


def xml_shape(element: ET.Element, redacted: bool = False) -> object:
    transform = redact if redacted else (lambda value: value)
    return (
        element.tag,
        tuple(sorted((key, transform(value)) for key, value in element.attrib.items())),
        transform(element.text) if element.text else element.text,
        transform(element.tail) if element.tail else element.tail,
        tuple(xml_shape(child, redacted) for child in element),
    )


def allowed(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in TEXT_SUFFIXES


def posix_path(value: str) -> Path:
    return Path(value.replace("\\", "/"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--include-ci", action="store_true")
    parser.add_argument("--include-windows", action="store_true")
    parser.add_argument("--include-benchmarks", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    raw = args.source_root.resolve()
    target = repo / PREFIX
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "sanitization-manifest.json"
    old_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for old in old_manifest.get("artifacts", []):
        old_path = target / old["artifact"]
        if old_path.is_file():
            old_path.unlink()
    for name in DETACHED:
        path = target / name
        if path.is_file():
            path.unlink()
    subprocess.run(["git", "reset", "--quiet", "--", PREFIX.as_posix()], cwd=repo, check=True)
    records: dict[str, dict] = {}

    def publish(name: str | Path, data: bytes, origin: str, *, preverified: dict | None = None) -> None:
        name = Path(name).as_posix()
        if preverified is not None:
            assert sha(data) == preverified["public_sha256"]
            assert len(data) == preverified["public_bytes"]
            payload = data
        elif name.endswith(".json"):
            old = json.loads(data.decode("utf-8-sig"))
            new = clean(old)
            assert numeric_shape(old) == numeric_shape(new)
            payload = dumps(new)
        elif name.endswith(".jsonl"):
            text = data.decode("utf-8-sig")
            lines = []
            for line in text.splitlines():
                if line.strip():
                    old = json.loads(line)
                    new = clean(old)
                    assert numeric_shape(old) == numeric_shape(new)
                    lines.append(json.dumps(new, ensure_ascii=False, allow_nan=False))
            payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
        else:
            payload = redact(data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")).encode("utf-8")
        if name.endswith(".xml"):
            assert xml_shape(ET.fromstring(data), True) == xml_shape(ET.fromstring(payload))
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        records[name] = {
            "artifact": name,
            "source": origin,
            "original_sha256": preverified["raw_sha256"] if preverified else sha(data),
            "original_bytes": preverified["raw_bytes"] if preverified else len(data),
            "published_sha256": sha(payload),
            "published_bytes": len(payload),
            "slice_projection": preverified.get("projection", False) if preverified else False,
            "projected_input_sha256": preverified.get("projected_input_sha256") if preverified else None,
            "semantic_checks": preverified.get("checks", {}) if preverified else {},
        }

    for label in ("neighbors", "world"):
        folder = raw / ("public-slice-" + label)
        index = json.loads((folder / "public-index.json").read_text(encoding="utf-8"))
        assert index["file_count"] == len(index["entries"])
        for row in index["entries"]:
            relative = Path(row["public"])
            assert not relative.is_absolute() and ".." not in relative.parts
            publish(Path(label) / relative, (folder / relative).read_bytes(), label + " raw/" + row["source"], preverified=row)
        publish(Path(label) / "public-index.json", (folder / "public-index.json").read_bytes(), "public slice metadata")
        publish(Path(label) / "README.md", (folder / "README.md").read_bytes(), "public slice metadata")

    for name in ("audit_frozen_composition.py", "root-command-guards.xml"):
        publish(Path("integration-independent") / name, (raw / name).read_bytes(), name)
    for folder_name in ("integration-independent", "integration-scoped"):
        folder = raw / folder_name
        for path in sorted(folder.glob("*")):
            if allowed(path):
                publish(Path(folder_name) / path.name, path.read_bytes(), path.relative_to(raw).as_posix())

    previous = json.loads((target / "source-status.json").read_text(encoding="utf-8")) if (target / "source-status.json").exists() else {}
    statuses = dict(previous.get("exact_pr_ci", {}))

    def include_ci(label: str, folder: Path, pr: int | None, expected_head: str) -> None:
        summary = json.loads((folder / "verified-summary.json").read_text(encoding="utf-8"))
        completion = json.loads((folder / "verified-completion.json").read_text(encoding="utf-8"))
        assert summary["head"] == expected_head and summary["all_complete"] and summary["all_success"]
        assert summary["semantic_evidence_verified"] and len(summary["gate_jobs"]) == 3
        counts = []
        for job in summary["gate_jobs"]:
            assert job["head_sha"] == expected_head and job["conclusion"] == "success"
            assert job["script_groups"] == job["unique_scripts"] == 102 and job["brain_real_23_of_23"]
            counts.append(job["pytest_counts"])
        if pr is not None:
            assert len(summary["title_jobs"]) == 1 and summary["title_jobs"][0]["conclusion"] == "success"
        else:
            assert not summary["title_jobs"]
        statuses[str(pr) if pr is not None else "combined"] = {"head": expected_head, "gate_counts": counts, "all_verified_success": True}
        publish(Path("remote-ci") / label / "verified-summary.json", (folder / "verified-summary.json").read_bytes(), folder.relative_to(raw).as_posix())
        publish(Path("remote-ci") / label / "verified-completion.json", (folder / "verified-completion.json").read_bytes(), folder.relative_to(raw).as_posix())
        for path in sorted(folder.glob("*-workflow.yml")):
            publish(Path("remote-ci") / label / path.name, path.read_bytes(), path.relative_to(raw).as_posix())
        archives = []
        for attempt in sorted(folder.glob("*-attempt*")):
            if not attempt.is_dir():
                continue
            for path in sorted(attempt.iterdir()):
                if path.suffix.lower() == ".zip":
                    data = path.read_bytes()
                    archives.append({"path": path.relative_to(folder).as_posix(), "sha256": sha(data), "bytes": len(data)})
                elif allowed(path) and not path.name.endswith(".stderr.log"):
                    publish(Path("remote-ci") / label / path.relative_to(folder), path.read_bytes(), path.relative_to(raw).as_posix())
        identity = folder / "commit-identity"
        if identity.is_dir():
            for path in sorted(identity.glob("*")):
                if allowed(path) and not path.name.endswith(".stderr.log"):
                    publish(Path("remote-ci") / label / "commit-identity" / path.name, path.read_bytes(), path.relative_to(raw).as_posix())
        api_rel = completion.get("api_snapshot_directory")
        api_dir = folder / posix_path(api_rel) if api_rel else None
        if not api_dir or not api_dir.is_dir():
            candidates = sorted((folder / "api").iterdir()) if (folder / "api").is_dir() else []
            api_dir = candidates[-1] if candidates else None
        if api_dir and api_dir.is_dir():
            for path in sorted(api_dir.rglob("*")):
                if allowed(path) and not path.name.endswith(".stderr.log"):
                    publish(Path("remote-ci") / label / "api" / path.relative_to(api_dir), path.read_bytes(), path.relative_to(raw).as_posix())
        publish(Path("remote-ci") / label / "archive-digests.json", dumps({"archives": archives}), "stable CI archive identities")

    if args.include_ci:
        include_ci("neighbors", raw / "remote-ci/neighbors", 1481, HEADS[1481])
        include_ci("command", raw / "remote-ci/command", 1482, HEADS[1482])
        include_ci("combined-gate", raw / "remote-ci/fork/combined-gate", None, SOURCE)

    windows = previous.get("windows_complete_gate", {"status": "pending", "frozen_source": SOURCE})
    if args.include_windows:
        folder = raw / "integration-windows"
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        assert summary["head"] == SOURCE and summary["finished_utc"]
        assert summary["source_unchanged"] and summary["brain_unchanged"]
        windows = {"status": "complete", "frozen_source": SOURCE, "gate_ok": summary["gate_ok"], "pytest_exit_code": summary["pytest"]["returncode"], "failed_tests": summary["failed_tests"], "junit_totals": summary["junit_totals"], "scripts": len(summary["script_results"])}
        for path in sorted(folder.glob("*")):
            if allowed(path):
                publish(Path("integration-windows") / path.name, path.read_bytes(), path.relative_to(raw).as_posix())
        for path in (raw / "run_round3_full_windows.py", raw / "integration-windows-launch.json", raw / "integration-windows-driver.log"):
            publish(Path("integration-windows") / path.name, path.read_bytes(), path.relative_to(raw).as_posix())

    linux_benchmark = previous.get("linux_benchmark", {"status": "pending", "run_id": 44790156130, "artifact_contents_validated": False})
    if args.include_benchmarks:
        audit_dir = raw / "benchmark-independent-audit"
        audit = json.loads((audit_dir / "audit-summary.json").read_text(encoding="utf-8"))
        assert audit["ok"] and audit["run_id"] == 44790156130
        assert audit["source_head"] == SOURCE and audit["metadata_head"] == "7d898378c84bdd125ed510cc749bef119880f3a8"
        api_rows = {row["name"]: row for row in json.loads(subprocess.check_output(["gh", "api", "repos/STARDUSTLC666/lingshu/actions/runs/44790156130/artifacts"], text=True, encoding="utf-8"))["artifacts"]}
        zip_root = raw / "benchmark-artifacts/raw"
        rows = []
        allowed_inner = {".json", ".jsonl", ".xml", ".log", ".txt", ".py", ".yml"}
        excluded = {"command/sources/baseline.py", "command/sources/fixed.py", "artifact-index.json"}
        for env_name in ("py312-floor", "py312-latest", "py313-latest"):
            artifact_name = f"body-round3-{env_name}-44790156130-1"
            api = api_rows[artifact_name]
            archive = zip_root / (env_name + ".zip")
            archive_bytes = archive.read_bytes()
            expected_archive_sha = api["digest"].removeprefix("sha256:")
            assert sha(archive_bytes) == expected_archive_sha
            inner = audit["artifact_inventory"][env_name]
            with ZipFile(archive) as zf:
                infos = zf.infolist()
                assert len(infos) == inner["zip_entries"]
                names = set(zf.namelist())
                index = json.loads(zf.read("artifact-index.json"))
                indexed = {item["path"]: item for item in index["files"]}
                assert len(indexed) == inner["indexed_files"] and "driver.log" not in indexed
                for info in infos:
                    relative = Path(info.filename)
                    assert not relative.is_absolute() and ".." not in relative.parts and "\\" not in info.filename
                    assert info.file_size <= 30_000_000
                    if info.is_dir():
                        continue
                    data = zf.read(info.filename)
                    if info.filename in indexed:
                        row = indexed[info.filename]
                        assert len(data) == row["bytes"] and sha(data) == row["sha256"]
                    if info.filename == "driver.log" or info.filename in excluded or relative.suffix not in allowed_inner:
                        continue
                    if info.filename.endswith(".jsonl"):
                        lower = data.lower()
                        runner_prefix = (chr(47) + "home" + chr(47) + "runner" + chr(47)).encode()
                        assert b"[linux-runner-path]" not in lower and runner_prefix not in lower
                        record = {"raw_sha256": sha(data), "raw_bytes": len(data), "public_sha256": sha(data), "public_bytes": len(data), "projection": False}
                        publish(Path("linux-benchmarks") / env_name / relative, data, f"run44790156130/{env_name}/{info.filename}", preverified=record)
                    else:
                        publish(Path("linux-benchmarks") / env_name / relative, data, f"run44790156130/{env_name}/{info.filename}")
                assert set(indexed) | {"artifact-index.json", "driver.log"} == names
            rows.append({"environment": env_name, "artifact_id": api["id"], "artifact_name": artifact_name, "api_zip_sha256": expected_archive_sha, "api_zip_bytes": len(archive_bytes), "indexed_files": inner["indexed_files"], "zip_entries": inner["zip_entries"], "driver_log_excluded_from_inner_index": True})
        for name in ("REPORT.md", "audit-summary.json", "verify_linux_artifacts.py"):
            path = audit_dir / name
            if path.is_file():
                publish(Path("benchmark-independent-audit") / name, path.read_bytes(), path.relative_to(raw).as_posix())
        publish("benchmark-independent-audit/artifact-api-metadata.json", dumps({"run_id": 44790156130, "artifacts": rows}), "verified original GitHub artifact API identities")
        linux_benchmark = {"status": "complete and independently content-audited", "run_id": 44790156130, "metadata_head": "7d898378c84bdd125ed510cc749bef119880f3a8", "source_head": SOURCE, "source_tree": "5e6e6d45fdc9ef6ea885f4e4f38d56630089a751", "artifact_contents_validated": True, "three_environments": rows, "independent_report": "benchmark-independent-audit/REPORT.md"}

    publish("source-status.json", dumps({"scope": "two new contributions; previous twelve preserved; continuous goal active", "frozen_source": SOURCE, "pr_heads": HEADS, "new_guards": 91, "named_mutants": 22, "combined_scoped_guards": 256, "exact_pr_ci": statuses, "windows_complete_gate": windows, "linux_benchmark": linux_benchmark, "intake_publication": previous.get("intake_publication", "original intake receipts appended separately; no self-grading or settlement")}), "generated completed scope status")
    for path in sorted((target / "tools").glob("*")):
        if allowed(path):
            publish(path.relative_to(target), path.read_bytes(), "evidence control source")
    publish("workflow/body-round3-benchmarks.yml", (repo / ".github/workflows/body-round3-benchmarks.yml").read_bytes(), "exact evidence workflow source")
    publish("README.md", (target / "README.md").read_bytes(), "evidence overview snapshot")
    junit = []
    for name in sorted(records):
        if name.endswith(".xml"):
            root = ET.fromstring((target / name).read_bytes())
            junit.append({"artifact": name, "suites": [dict(s.attrib) for s in root.iter("testsuite")]})
    publish("junit-index.json", dumps({"policy": "Overlapping fixed/baseline/mutant/CI/supplementary runs are not additive.", "runs": junit}), "generated complete XML inventory")

    selected = sorted(records)
    for start in range(0, len(selected), 120):
        subprocess.run(["git", "add", "-f", "--", *[(PREFIX / name).as_posix() for name in selected[start:start + 120]]], cwd=repo, check=True, capture_output=True)
    staged = {}
    for entry in subprocess.check_output(["git", "ls-files", "--stage", "-z", "--", PREFIX.as_posix()], cwd=repo).split(b"\0"):
        if entry:
            meta, path = entry.split(b"\t", 1)
            staged[path.decode()] = meta.split()[1].decode()
    assert set(staged) == {(PREFIX / name).as_posix() for name in selected}
    batch = subprocess.check_output(["git", "cat-file", "--batch"], cwd=repo, input=("\n".join(staged.values()) + "\n").encode())
    stream = io.BytesIO(batch)
    runner_prefix = (chr(47) + "home" + chr(47) + "runner" + chr(47)).encode()
    private = re.compile(rb"(?i)(?:[ce]:[\\/]+(?:users|lingshu))|" + re.escape(runner_prefix))
    private_chinese = "公益站".encode("utf-8")
    for full, oid in staged.items():
        header = stream.readline().split()
        assert header[0].decode() == oid and header[1] == b"blob"
        data = stream.read(int(header[2]))
        assert stream.read(1) == b"\n"
        name = full[len(PREFIX.as_posix()) + 1:]
        row = records[name]
        working = (target / name).read_bytes()
        assert data == working or data == working.replace(b"\r\n", b"\n"), name
        row["working_tree_sha256"], row["working_tree_bytes"] = sha(working), len(working)
        row["git_line_ending_normalization"] = data != working
        if not name.startswith("tools/"):
            assert not private.search(data) and private_chinese not in data, name
        if name.endswith(".json"):
            json.loads(data)
        elif name.endswith(".jsonl"):
            for line in data.decode("utf-8").splitlines():
                if line.strip():
                    json.loads(line)
        elif name.endswith(".xml"):
            ET.fromstring(data)
        row["canonical_sha256"], row["canonical_bytes"] = sha(data), len(data)

    manifest = {"policy": "Original source/public and canonical Git hashes; numeric JSON/XML semantics retained; detached sealing metadata excluded.", "artifacts": [records[name] for name in selected]}
    manifest_path.write_bytes(dumps(manifest))
    (target / "seal-audit.json").write_bytes(dumps({"ok": True, "manifested_artifacts": len(records), "xml_runs": len(junit), "canonical_hashes_verified": True, "detached_metadata": sorted(DETACHED), "source_sha": SOURCE, "included_ci": args.include_ci, "included_windows": args.include_windows, "included_benchmarks": args.include_benchmarks}))
    subprocess.run(["git", "add", "-f", "--", *[(PREFIX / name).as_posix() for name in DETACHED]], cwd=repo, check=True, capture_output=True)
    print(json.dumps({"ok": True, "artifacts": len(records), "xml_runs": len(junit), "ci": args.include_ci, "windows": args.include_windows, "benchmarks": args.include_benchmarks}))


if __name__ == "__main__":
    main()
