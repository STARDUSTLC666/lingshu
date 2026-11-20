from pathlib import Path
import hashlib
import json
import subprocess

repo = Path(r"[workspace]/lingshu/work\lingshu-body-collision-velocity-20261120")
out = Path(__file__).resolve().parent
def git(*args):
    return subprocess.check_output(["git", *args], cwd=repo)
head = git("rev-parse", "HEAD").decode().strip()
files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines()
rows = []
for name in files:
    blob = git("show", "HEAD:" + name)
    local = (repo / name).read_bytes().replace(b"\r\n", b"\n")
    assert local == blob
    rows.append({"path": name, "git_blob": git("rev-parse", "HEAD:" + name).decode().strip(),
                 "sha256_lf": hashlib.sha256(blob).hexdigest(), "bytes_lf": len(blob)})
source = next(r["sha256_lf"] for r in rows if r["path"] == "lingshu/world/scene_simulator.py")
bench = json.loads((out / "benchmark-r2/summary.json").read_text(encoding="utf-8"))
replay = json.loads((out / "replay-r2/summary.json").read_text(encoding="utf-8"))
assert bench["scene_source_sha256_lf"]["fixed"] == source
assert replay["records"][0]["source_sha256"]["lingshu/world/scene_simulator.py"] == source
assert not git("status", "--porcelain")
record = {"head": head, "base": git("rev-parse", "HEAD^").decode().strip(),
          "branch": git("branch", "--show-current").decode().strip(),
          "working_tree_clean": True, "published": False, "files": rows,
          "benchmark_source_matches_commit": True, "mutation_source_matches_commit": True}
(out / "implementation-seal.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False, indent=2))
