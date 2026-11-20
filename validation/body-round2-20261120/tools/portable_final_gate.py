#!/usr/bin/env python3
"""Run the complete Lingshu integration gate and retain unmodified raw evidence.

Install the target repository in the active Python environment first, for example:
    python -m pip install -e ".[full,dev,core-sparse]"
Make OpenSSL available on the subprocess PATH to exercise the real TLS tests.

Example (all paths are supplied by the caller):
    python portable_final_gate.py --repo lingshu --output gate-output --brain-root dsh-memory --workers 4

The brain checkout must be clean and match the DSH_MEMORY_SHA pinned in gate.yml.
Workers 0 and 1 both run the full pytest leg serially. No test is deselected to
hide a failure. The controlled timing guard also runs in a separate serial leg.
The output directory must be empty and outside the source checkout. A checkout
with an applied patch is allowed: Git status and every Git-visible file's bytes
are fingerprinted before and after validation, including untracked patch files.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True,
                                   encoding="utf-8", errors="replace").strip()


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def source_snapshot(repo):
    """Fingerprint tracked files and nonignored additions, without changing Git's index."""
    listed = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z", "--cached",
                                      "--others", "--exclude-standard"])
    files = {}
    for raw_name in sorted(set(listed.split(b"\0")) - {b""}):
        name = raw_name.decode("utf-8")
        path = repo / name
        if path.is_symlink():
            payload = os.readlink(path).encode("utf-8")
            files[name] = "symlink:" + hashlib.sha256(payload).hexdigest()
        elif path.is_file():
            files[name] = "file:" + hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.exists():
            files[name] = "directory"
        else:
            files[name] = "missing"
    return {"head": git(repo, "rev-parse", "HEAD"),
            "status": git(repo, "status", "--porcelain"), "files": files}


def snapshot_description(snapshot):
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"sha256": hashlib.sha256(payload).hexdigest(), "file_count": len(snapshot["files"]),
            "convention": "Git HEAD/status plus raw bytes of tracked and nonignored untracked files"}


def junit_details(path):
    root = ET.parse(path).getroot()
    skipped_tests, failed_tests = [], []
    for test in root.iter("testcase"):
        identity = test.attrib.get("classname", "") + "::" + test.attrib.get("name", "")
        skipped = test.find("skipped")
        if skipped is not None:
            skipped_tests.append({"test": identity, "reason": skipped.attrib.get("message", "")})
        for kind in ("failure", "error"):
            detail = test.find(kind)
            if detail is not None:
                failed_tests.append({"test": identity, "kind": kind,
                                     "message": detail.attrib.get("message", ""),
                                     "detail": detail.text})
    return {"junit_totals": [dict(suite.attrib) for suite in root.iter("testsuite")],
            "skip_reasons": dict(Counter(item["reason"] for item in skipped_tests)),
            "skipped_tests": skipped_tests, "failed_tests": failed_tests}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Lingshu checkout (default: current directory)")
    parser.add_argument("--output", type=Path, required=True, help="New or empty evidence directory, outside --repo")
    parser.add_argument("--brain-root", type=Path, required=True, help="Clean dsh-memory checkout at gate.yml's pinned SHA")
    parser.add_argument("--workers", type=int, default=4, help="pytest worker count; 0 or 1 means serial (default: 4)")
    parser.add_argument("--script-timeout", type=float, default=600, help="Seconds allowed per script test (default: 600)")
    parser.add_argument("--pytest-timeout", type=float, default=3600, help="Seconds allowed for full pytest (default: 3600)")
    args = parser.parse_args()
    args.repo, args.output, args.brain_root = (value.expanduser().resolve()
                                             for value in (args.repo, args.output, args.brain_root))
    if args.workers < 0:
        parser.error("--workers must be nonnegative")
    if args.script_timeout <= 0 or args.pytest_timeout <= 0:
        parser.error("Timeouts must be positive")
    if not (args.repo / ".github/workflows/gate.yml").is_file():
        parser.error("--repo does not contain .github/workflows/gate.yml")
    if args.output.is_relative_to(args.repo):
        parser.error("--output must be outside --repo so evidence cannot change the source status")
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("--output must be a new or empty directory; previous evidence is never overwritten")
    if not (args.brain_root / "md_cg/mcp_server.py").is_file():
        parser.error("--brain-root is missing md_cg/mcp_server.py")
    return args


def main():
    args = parse_args()
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML is required: install the repository's dev dependencies in this Python environment")

    workflow_path = args.repo / ".github/workflows/gate.yml"
    workflow_bytes = workflow_path.read_bytes()
    config = yaml.safe_load(workflow_bytes)
    scripts = config["env"]["SCRIPT_TESTS"].split()
    if not scripts or len(scripts) != len(set(scripts)):
        raise SystemExit("gate.yml SCRIPT_TESTS must be a nonempty list without duplicates")
    for script in scripts:
        path = (args.repo / script).resolve()
        if not path.is_relative_to(args.repo) or not path.is_file():
            raise SystemExit("Invalid SCRIPT_TESTS entry: " + script)
    pins = {str(step.get("env", {}).get("DSH_MEMORY_SHA", ""))
            for job in config["jobs"].values() for step in job.get("steps", [])
            if step.get("env", {}).get("DSH_MEMORY_SHA")}
    if len(pins) != 1 or not re.fullmatch(r"[0-9a-fA-F]{40}", next(iter(pins), "")):
        raise SystemExit("Could not resolve one exact DSH_MEMORY_SHA from gate.yml")
    brain_expected = next(iter(pins)).lower()
    brain_head = git(args.brain_root, "rev-parse", "HEAD")
    brain_status = git(args.brain_root, "status", "--porcelain")
    if brain_head.lower() != brain_expected or brain_status:
        raise SystemExit("Brain checkout must be clean at pinned SHA " + brain_expected
                         + "; actual head=" + brain_head + "; status=" + repr(brain_status))
    source_before = source_snapshot(args.repo)
    source_status = source_before["status"]

    args.output.mkdir(parents=True, exist_ok=True)
    temp = args.output / "tmp"
    temp.mkdir()
    inherited_pytest_addopts = os.environ.get("PYTEST_ADDOPTS")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", PYTEST_ADDOPTS="",
               TEMP=str(temp), TMP=str(temp), MDCG_BRAIN_PYTHONPATH=str(args.brain_root))
    # Nested invocations must not mistake this driver for a parent xdist worker.
    for key in tuple(env):
        if key.startswith("PYTEST_XDIST_WORKER"):
            env.pop(key)
    openssl = shutil.which("openssl", path=env.get("PATH"))
    openssl_version = None
    if openssl:
        probe = subprocess.run([openssl, "version", "-a"], env=env, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30)
        openssl_version = {"returncode": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr}
    provenance = subprocess.check_output([sys.executable, "-c", "import lingshu; print(lingshu.__file__)"],
                                        cwd=args.repo, env=env, text=True, encoding="utf-8", errors="replace").strip()
    if not Path(provenance).resolve().is_relative_to(args.repo):
        raise SystemExit("This Python imports Lingshu outside --repo: " + provenance)
    summary = {
        "root": str(args.repo), "head": source_before["head"],
        "status_before": source_status, "platform": platform.platform(), "python": sys.version,
        "source_snapshot_before": snapshot_description(source_before),
        "executable": sys.executable, "workers": args.workers, "lingshu_import_path": provenance,
        "inherited_pythonpath": os.environ.get("PYTHONPATH"),
        "inherited_pytest_addopts": inherited_pytest_addopts,
        "dependencies": {name: package_version(name) for name in
                         ("numpy", "Pillow", "scipy", "pytest", "pytest-xdist", "PyYAML", "markdown-it-py")},
        "git_version": subprocess.check_output(["git", "--version"], text=True,
                                                encoding="utf-8", errors="replace").strip(),
        "brain": str(args.brain_root), "brain_expected_head": brain_expected, "brain_head": brain_head,
        "brain_status_before": brain_status, "openssl": openssl, "openssl_version": openssl_version,
        "workflow_sha256": hashlib.sha256(workflow_bytes).hexdigest(),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment_overrides": {key: env[key] for key in
                                  ("PYTHONUTF8", "PYTHONIOENCODING", "PYTHONDONTWRITEBYTECODE", "PYTEST_ADDOPTS",
                                   "TEMP", "TMP", "MDCG_BRAIN_PYTHONPATH")},
        "started_utc": utc_now(), "script_results": []
    }

    def save():
        (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    def run(arguments, name, timeout):
        log = args.output / (name + ".log")
        command = [sys.executable, "-X", "utf8", *arguments]
        started = time.perf_counter()
        with log.open("wb") as handle:
            try:
                result = subprocess.run(command, cwd=args.repo, env=env, stdout=handle,
                                        stderr=subprocess.STDOUT, timeout=timeout)
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = "timeout"
        return {"name": name, "command": command, "returncode": returncode,
                "seconds": round(time.perf_counter() - started, 3), "log": str(log)}

    save()
    (args.output / "pip_freeze.txt").write_text(subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], env=env, text=True,
        encoding="utf-8", errors="replace"), encoding="utf-8")
    for index, script in enumerate(scripts):
        result = run([script], f"script_{index:03d}_{Path(script).stem}", args.script_timeout)
        result["test"] = script
        summary["script_results"].append(result)
        save()
        print(json.dumps({"script": index + 1, "total": len(scripts), **result}), flush=True)

    pytest_args = ["-m", "pytest", "tests/", "-q"]
    if args.workers > 1:
        pytest_args += ["-n", str(args.workers), "--dist", "loadfile"]
    pytest_args += ["--tb=short", "--durations=40", "--junitxml=" + str(args.output / "pytest.xml"),
                    "--basetemp=" + str(temp / "pytest")]
    pytest_args += ["--ignore=" + script for script in scripts]
    summary["pytest"] = run(pytest_args, "pytest_full", args.pytest_timeout)
    if (args.output / "pytest.xml").exists():
        summary.update(junit_details(args.output / "pytest.xml"))
    save()
    print("PYTEST " + json.dumps(summary["pytest"]), flush=True)

    summary["controlled_timing"] = run([
        "-m", "pytest", "tests/test_issue252_self_check_cycle_enum_limit_guard.py", "-q",
        "--tb=short", "--durations=10", "--junitxml=" + str(args.output / "controlled_timing.xml"),
        "--basetemp=" + str(temp / "controlled_timing")], "controlled_timing", 300)
    if (args.output / "controlled_timing.xml").exists():
        summary["controlled_timing_details"] = junit_details(args.output / "controlled_timing.xml")
    save()
    print("CONTROLLED_TIMING " + json.dumps(summary["controlled_timing"]), flush=True)

    for name, arguments in (("strict_manifest", ["tools/verify_manifest.py", "--strict", "--quiet"]),
                            ("time_core_lint", ["tools/time_core_lint.py", "--json"])):
        summary[name] = run(arguments, name, 300)
        save()
        print(name + " " + json.dumps(summary[name]), flush=True)

    source_after = source_snapshot(args.repo)
    summary["head_after"] = source_after["head"]
    summary["status_after"] = source_after["status"]
    summary["source_snapshot_after"] = snapshot_description(source_after)
    summary["brain_head_after"] = git(args.brain_root, "rev-parse", "HEAD")
    summary["brain_status_after"] = git(args.brain_root, "status", "--porcelain")
    summary["source_unchanged"] = source_before == source_after
    summary["source_changed_files"] = [name for name in sorted(source_before["files"].keys() | source_after["files"].keys())
                                       if source_before["files"].get(name) != source_after["files"].get(name)]
    summary["brain_unchanged"] = (brain_head == summary["brain_head_after"]
                                  and brain_status == summary["brain_status_after"])
    summary["finished_utc"] = utc_now()
    ok = all(result["returncode"] == 0 for result in summary["script_results"]) and all(
        summary[key]["returncode"] == 0 for key in ("pytest", "controlled_timing", "strict_manifest", "time_core_lint"))
    summary["gate_ok"] = ok and summary["source_unchanged"] and summary["brain_unchanged"]
    save()
    print("GATE_OK=" + str(summary["gate_ok"]), flush=True)
    return 0 if summary["gate_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
