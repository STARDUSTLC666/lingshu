"""Read-only exact-head CI audit. No dispatch, rerun, cancellation or mutation.

Polls no faster than every 180 seconds; each wait chunk is at most 45 seconds.
targets.json may be extended by the authorized caller while this process runs.
Original HTTP response bodies/logs are retained byte-for-byte with hashes.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = "FuRongJun-1999/lingshu"
LOCAL = Path(r"[workspace]/lingshu/work\lingshu-body-collision-velocity-20261120")
BRAIN = "98d6b899533a82fb1047f952987229c62a9929fb"
GATES = {"gate (py3.12)", "gate (py3.12 · 依赖下界)", "gate (py3.13)"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def command(args, timeout=120):
    return subprocess.run(args, cwd=LOCAL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def api(endpoint, path):
    result = command(["gh", "api", endpoint])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix(path.suffix + ".stderr.log").write_bytes(result.stderr)
    if result.returncode:
        raise RuntimeError("GitHub read failed " + endpoint + ": " + result.stderr.decode("utf-8", "replace")[:250])
    path.write_bytes(result.stdout)
    return json.loads(result.stdout)


def clean_lines(raw):
    lines = []
    for line in raw.decode("utf-8-sig", "replace").splitlines():
        line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line)
        stamp = re.search(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z\s?", line)
        lines.append(line[stamp.end():] if stamp else line)
    return lines


def parse_job(raw, job, expected_scripts):
    lines = clean_lines(raw)
    scripts, brain_lines = [], []
    inside_brain = False
    for line in lines:
        start = re.search(r"(?:##\[group\]|::group::)script test:\s+(tests/\S+\.py)", line)
        if start:
            scripts.append(start.group(1))
            inside_brain = start.group(1) == "tests/test_brain_store.py"
        elif inside_brain and ("##[endgroup]" in line or "::endgroup::" in line):
            inside_brain = False
        elif inside_brain:
            brain_lines.append(line)
    brain = "\n".join(brain_lines)
    summaries = [line.strip() for line in lines if re.search(r"\b\d+ passed\b", line)
                 and re.search(r"\bin [\d.]+s", line)]
    summary = summaries[-1] if summaries else None
    counts = {key: 0 for key in ("passed", "failed", "skipped", "errors", "xfailed", "xpassed")}
    for key in counts:
        match = re.search(r"\b(\d+) " + key + r"\b", summary or "")
        if match:
            counts[key] = int(match.group(1))
    subtests = re.search(r"\b(\d+) subtests? passed\b", summary or "")
    counts["subtests_passed"] = int(subtests.group(1)) if subtests else 0
    skip_lines = [line.strip() for line in lines if " SKIPPED " in line]
    skip_files = Counter(line.partition("::")[0] for line in skip_lines)
    brain_pairs = re.findall(r"SUMMARY\s+(\d+)\s*/\s*(\d+)\s+通过", brain)
    failed_steps = [{"number": s["number"], "name": s["name"], "conclusion": s.get("conclusion")}
                    for s in job.get("steps", []) if s.get("conclusion") in ("failure", "cancelled", "timed_out")]
    result = {"job_id": job["id"], "name": job["name"], "url": job["html_url"],
              "head_sha": job["head_sha"], "status": job["status"], "conclusion": job["conclusion"],
              "started_at": job.get("started_at"), "completed_at": job.get("completed_at"),
              "script_groups": len(scripts), "unique_scripts": len(set(scripts)),
              "scripts_match_workflow": scripts == expected_scripts, "scripts": scripts,
              "scripts_all_pass_marker": any(line.startswith("脚本式测试全部通过：") for line in lines),
              "brain_summary_pairs": brain_pairs, "brain_real_23_of_23": ("23", "23") in brain_pairs and "VERDICT=PASS" in brain,
              "brain_clone_actual_output": [line for line in lines if line.startswith("脑端 clone 成功")],
              "brain_clone_steps": [{"name": s["name"], "conclusion": s.get("conclusion")} for s in job.get("steps", []) if s["name"].startswith("Clone 脑端")],
              "pinned_brain_fetch_seen": any(BRAIN in line and "FETCH_HEAD" in line and not line.lstrip().startswith("git ") for line in lines),
              "pytest_summary": summary, "pytest_counts": counts, "skip_lines": skip_lines,
              "skip_count_by_file": dict(sorted(skip_files.items())), "failed_steps": failed_steps,
              "raw_log_sha256": hashlib.sha256(raw).hexdigest(), "raw_log_bytes": len(raw)}
    return result


def download_log(endpoint, path):
    if path.is_file() and path.stat().st_size:
        return path.read_bytes()
    result = command(["gh", "api", endpoint], timeout=180)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_suffix(path.suffix + ".stderr.log").write_bytes(result.stderr)
    if result.returncode or not result.stdout:
        raise RuntimeError("Log not available: " + endpoint)
    path.write_bytes(result.stdout)
    return result.stdout


def audit_target(target, stamp):
    pr, expected = target["pr"], target["head"]
    base = ROOT / ("pr" + str(pr))
    snap = base / "api" / stamp
    info = api(f"repos/{REPO}/pulls/{pr}", snap / "pull.json")
    if info["head"]["sha"] != expected:
        raise RuntimeError(f"HEAD_CHANGED PR{pr}: expected {expected}, actual {info['head']['sha']}")
    checks = api(f"repos/{REPO}/commits/{expected}/check-runs?per_page=100", snap / "checks.json")["check_runs"]
    selected = [c for c in checks if c["name"] in GATES or c["name"].startswith("PR 标题约定")]
    by_name = {}
    for check in sorted(selected, key=lambda c: c["id"]):
        assert check["head_sha"] == expected
        by_name[check["name"]] = check
    run_ids = sorted({int(re.search(r"/actions/runs/(\d+)", c["details_url"]).group(1))
                      for c in by_name.values()})
    # Freeze the exact PR workflow text, not the worktree's current branch.
    workflow_path = base / "workflow.yml"
    if not workflow_path.exists():
        wf = command(["git", "show", expected + ":.github/workflows/gate.yml"])
        if wf.returncode:
            raise RuntimeError("Exact workflow Git object missing: " + expected)
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_bytes(wf.stdout)
    workflow = workflow_path.read_text(encoding="utf-8")
    section = workflow.split("  SCRIPT_TESTS: >-", 1)[1].split("\njobs:", 1)[0]
    expected_scripts = re.findall(r"^\s+(tests/\S+\.py)\s*$", section, re.M)
    assert len(expected_scripts) == 102
    gate_jobs, title_jobs, runs = [], [], []
    for run_id in run_ids:
        run = api(f"repos/{REPO}/actions/runs/{run_id}", snap / (str(run_id) + "-run.json"))
        assert run["head_sha"] == expected, ("WRONG_RUN_HEAD", run_id, run["head_sha"], expected)
        jobs = api(f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100&filter=latest", snap / (str(run_id) + "-jobs.json"))["jobs"]
        runs.append({"id": run_id, "name": run["name"], "head": run["head_sha"], "attempt": run["run_attempt"],
                     "status": run["status"], "conclusion": run["conclusion"], "url": run["html_url"]})
        run_dir = base / (str(run_id) + "-attempt" + str(run["run_attempt"]))
        for job in jobs:
            assert job["head_sha"] == expected
            item = {"job_id": job["id"], "name": job["name"], "url": job["html_url"],
                    "head_sha": job["head_sha"], "status": job["status"], "conclusion": job["conclusion"],
                    "running_steps": [s["name"] for s in job.get("steps", []) if s["status"] == "in_progress"]}
            if job["status"] == "completed":
                raw = download_log(f"repos/{REPO}/actions/jobs/{job['id']}/logs", run_dir / (str(job["id"]) + ".log"))
                if job["name"] in GATES:
                    item = parse_job(raw, job, expected_scripts)
                else:
                    item.update(raw_log_sha256=hashlib.sha256(raw).hexdigest(), raw_log_bytes=len(raw),
                                failed_steps=[s for s in job.get("steps", []) if s.get("conclusion") in ("failure", "cancelled", "timed_out")])
                write_json(run_dir / (str(job["id"]) + "-summary.json"), item)
            if job["name"] in GATES:
                gate_jobs.append(item)
            else:
                title_jobs.append(item)
        if run["status"] == "completed":
            raw_zip = download_log(f"repos/{REPO}/actions/runs/{run_id}/logs", run_dir / "all-run-logs.zip")
            with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
                index = [{"path": n, "bytes": len(archive.read(n)), "sha256": hashlib.sha256(archive.read(n)).hexdigest()}
                         for n in archive.namelist() if not n.endswith("/")]
            write_json(run_dir / "archive-index.json", {"zip_sha256": hashlib.sha256(raw_zip).hexdigest(), "files": index})
    complete = ({j["name"] for j in gate_jobs} == GATES and len(gate_jobs) == 3 and len(title_jobs) == 1
                and all(j["status"] == "completed" for j in gate_jobs + title_jobs))
    success = complete and all(j["conclusion"] == "success" for j in gate_jobs + title_jobs)
    semantic = complete and all(j.get("scripts_match_workflow") and j.get("scripts_all_pass_marker")
                              and j.get("brain_real_23_of_23") and j.get("pinned_brain_fetch_seen")
                              and j.get("pytest_summary") and not j.get("failed_steps")
                              and j["pytest_counts"]["failed"] == 0 and j["pytest_counts"]["errors"] == 0
                              and len(j["skip_lines"]) == j["pytest_counts"]["skipped"]
                              for j in gate_jobs)
    result = {"pr": pr, "head": expected, "url": info["html_url"], "last_poll_utc": now(),
              "all_complete": complete, "all_success": success, "semantic_evidence_verified": semantic,
              "expected_scripts": len(expected_scripts), "expected_brain": BRAIN, "runs": runs,
              "gate_jobs": gate_jobs, "title_jobs": title_jobs}
    write_json(base / "summary.json", result)
    return result


def main():
    previous = {}
    while True:
        started = time.monotonic()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        results, errors = [], []
        targets = json.loads((ROOT / "targets.json").read_text(encoding="utf-8"))
        for target in targets:
            try:
                result = audit_target(target, stamp)
                results.append(result)
                compact = {"pr": result["pr"], "head": result["head"], "all_complete": result["all_complete"],
                           "all_success": result["all_success"], "semantic_evidence_verified": result["semantic_evidence_verified"],
                           "jobs": [{k: j.get(k) for k in ("job_id", "name", "status", "conclusion", "pytest_summary", "running_steps")}
                                    for j in result["gate_jobs"] + result["title_jobs"]]}
                if compact != previous.get(result["pr"]):
                    print(json.dumps({"at": now(), **compact}, ensure_ascii=False), flush=True)
                    previous[result["pr"]] = compact
            except Exception as exc:
                error = {"pr": target["pr"], "at": now(), "error": repr(exc)}
                errors.append(error)
                print(json.dumps(error, ensure_ascii=False), flush=True)
        summary = {"at": now(), "read_only": True, "minimum_poll_seconds": 180,
                   "targets": targets, "results": results, "errors": errors,
                   "all_complete": len(results) == len(targets) and all(r["all_complete"] for r in results),
                   "all_verified_success": len(results) == len(targets) and all(r["all_success"] and r["semantic_evidence_verified"] for r in results)}
        write_json(ROOT / "summary.json", summary)
        if summary["all_complete"]:
            print("AUDIT_COMPLETE " + json.dumps({"at": now(), "all_verified_success": summary["all_verified_success"]}), flush=True)
            return 0 if summary["all_verified_success"] else 1
        remaining = max(180 - (time.monotonic() - started), 0)
        while remaining:
            pause = min(45, remaining)
            time.sleep(pause)
            remaining -= pause


if __name__ == "__main__":
    raise SystemExit(main())
