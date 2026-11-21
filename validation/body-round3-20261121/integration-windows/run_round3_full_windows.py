"""Run the frozen fourteen-fix source with its own installed environment."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = Path(r"[workspace]/lingshu/work\lingshu-body-round3-integration-20261121")
PYTHON = Path(r"[workspace]/lingshu/work\lingshu-body-round3-integration-20261121-venv\Scripts\python.exe")
DRIVER = Path(r"[workspace]/lingshu/work\lingshu-body-round2-evidence-final-20261121\validation\body-round2-20261120\tools\portable_final_gate.py")
BRAIN = Path(r"[workspace]/lingshu/outputs\body-validation-20261120\brain-pinned")
BASELINE = ROOT / "audit-world/frozen-baseline-124ea43"
OUTPUT = ROOT / "integration-windows"
HEAD = "f81ee3a9939f3dad7c277145766508c113742ba0"
TREE = "5e6e6d45fdc9ef6ea885f4e4f38d56630089a751"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True, encoding="utf-8").strip()


assert git("rev-parse", "HEAD") == HEAD
assert git("rev-parse", "HEAD^{tree}") == TREE
assert git("status", "--porcelain") == ""
assert not OUTPUT.exists()
assert (BASELINE / "lingshu/world/physics.py").is_file()
openssl_dir = Path(r"C:\Program Files\Git\usr\bin")
assert (openssl_dir / "openssl.exe").is_file()
env = dict(os.environ, PATH=os.environ["PATH"] + os.pathsep + str(openssl_dir),
           LINGSHU_BASE_TREE=str(BASELINE), PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
command = [str(PYTHON), "-B", "-X", "utf8", str(DRIVER), "--repo", str(REPO),
           "--output", str(OUTPUT), "--brain-root", str(BRAIN), "--workers", "4"]
provenance = {"frozen_head": HEAD, "frozen_tree": TREE, "command": command,
              "driver_sha256": hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
              "launcher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "authentic_historical_physics_baseline": "124ea433fe9a2ad2fd66a7360df85f6d61bab793",
              "historical_baseline_path": str(BASELINE), "openssl_dir": str(openssl_dir),
              "environment_policy": "Dedicated venv; pinned dependencies cloned from prior complete run. Historical source enables original comparisons; no tests deselected beyond workflow script split."}
(ROOT / "integration-windows-launch.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
with (ROOT / "integration-windows-driver.log").open("wb") as log:
    result = subprocess.run(command, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT)
provenance["exit_code"] = result.returncode
(ROOT / "integration-windows-launch.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"head": HEAD, "exit_code": result.returncode, "output": str(OUTPUT)}), flush=True)
raise SystemExit(result.returncode)
