import json
import os
from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT = Path(r"[workspace]/lingshu/work\lingshu-body-fresh-decay-20261120")
OUT = Path(__file__).resolve().parent
scripts = set(yaml.safe_load((ROOT / ".github/workflows/gate.yml").read_text(encoding="utf-8"))["env"]["SCRIPT_TESTS"].split())
pattern = re.compile(r"decay|test_core_|test_issue36_|test_issue207_|test_issue205_|test_issue115_|test_extension_transaction_ownership|test_issue778_781|test_issue720_|test_fresh_row_decay")
selected = sorted("tests/" + p.name for p in (ROOT / "tests").glob("test_*.py") if pattern.search(p.name))
env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT)}
records = []
for path in selected:
    if path not in scripts:
        continue
    result = subprocess.run([sys.executable, "-X", "utf8", "-B", path], cwd=ROOT, env=env, capture_output=True, timeout=180)
    text = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    (OUT / (Path(path).stem + ".log")).write_text(text, encoding="utf-8")
    records.append({"script": path, "exit": result.returncode})
    print(json.dumps(records[-1]), flush=True)
tests = [p for p in selected if p not in scripts]
command = [sys.executable, "-X", "utf8", "-B", "-m", "pytest", *tests, "-q", "--disable-warnings", "-p", "no:cacheprovider", "--junitxml", str(OUT / "fresh-related-final.xml")]
result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=600)
text = (result.stdout + result.stderr).decode("utf-8", errors="replace")
(OUT / "fresh-related-final.log").write_text(text, encoding="utf-8")
records.append({"pytest": tests, "exit": result.returncode})
(OUT / "fresh-related-results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
print(text)
raise SystemExit(0 if all(r["exit"] == 0 for r in records) else 1)
