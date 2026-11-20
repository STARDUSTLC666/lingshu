"""Execute unchanged original bodies after a real Windows symlink probe.

The full pytest result and its original skip markers remain unchanged. This is
a separate supplement, not a rewrite/skip of its existing POSIX-only probe.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    temp = out / "tmp"
    temp.mkdir(exist_ok=True)
    os.environ["TEMP"] = os.environ["TMP"] = str(temp)
    tempfile.tempdir = str(temp)
    sys.path.insert(0, str(source))
    test = source / "tests/test_issue498_atomic_write_perm_symlink_guard.py"
    before = test.read_bytes()
    with tempfile.TemporaryDirectory(prefix="capability-", dir=temp) as td:
        target, link = Path(td) / "target.txt", Path(td) / "link.txt"
        target.write_text("capability", encoding="utf-8")
        os.symlink(target, link)
        capability = {"symlink_created": True, "is_symlink": link.is_symlink(),
                      "target_read_verified": link.read_text(encoding="utf-8") == "capability"}
        assert all(capability.values())
    spec = importlib.util.spec_from_file_location("original_symlink_guard", test)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cases = []
    for prefix in ("test_a6_posix_", "test_b6_posix_", "test_c6_posix_"):
        names = [name for name in vars(module) if name.startswith(prefix)]
        assert len(names) == 1
        started = time.perf_counter()
        getattr(module, names[0])()
        cases.append({"test": names[0], "passed": True, "seconds": time.perf_counter() - started})
    assert test.read_bytes() == before
    result = {"source_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source,
              text=True, encoding="utf-8", errors="replace").strip(),
              "test_sha256_lf": hashlib.sha256(before.replace(b"\r\n", b"\n")).hexdigest(),
              "capability": capability, "cases": cases, "passed": True,
              "scope": "Three unchanged original test bodies; supplemental to, never added to or substituted for, the main full-gate totals/failure/skips."}
    (out / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
