"""Self-contained positive/negative metadata fixtures for the evidence index.

Uses only the standard library and an adjacent runner module. No production
imports or benchmark executions occur. Temporary fixture files stay below cwd.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("round2_runner", Path(__file__).with_name("run_round2_linux_benchmarks.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def mismatches(root, index):
    """Independent read-back: do not reuse the runner's digest function."""
    bad = []
    for row in index["files"]:
        path = root / row["path"]
        if not path.is_file():
            bad.append(row["path"])
            continue
        payload = path.read_bytes()
        if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
            bad.append(row["path"])
    return bad


class ArtifactIndexFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="index-metadata-fixture-", dir=Path.cwd())
        self.root = Path(self.temp.name)
        (self.root / "core").mkdir()
        (self.root / "core/fixed.json").write_text('{"oracle_failures":0}', encoding="utf-8")
        (self.root / "validation-summary.json").write_text('{"ok":true,"commands":10}', encoding="utf-8")
        (self.root / "driver.log").write_text("running\n", encoding="utf-8")
        (self.root / "artifact-index.json").write_text("stale previous index", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_final_summary_is_indexed_and_mutable_or_temporary_files_are_excluded(self):
        for relative in ("tmp/cache.json", "sandbox/copy.py", "guard-one/mutant.json", "__pycache__/cache.txt"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("temporary", encoding="utf-8")
        (self.root / "state.db").write_bytes(b"temporary database")
        index = runner.write_artifact_index(self.root)
        self.assertEqual({r["path"] for r in index["files"]}, {"core/fixed.json", "validation-summary.json"})
        self.assertEqual(index, json.loads((self.root / "artifact-index.json").read_text(encoding="utf-8")))
        self.assertEqual(mismatches(self.root, index), [])

    def test_live_driver_log_append_does_not_invalidate_listed_hashes(self):
        index = runner.write_artifact_index(self.root)
        with (self.root / "driver.log").open("a", encoding="utf-8") as stream:
            stream.write("final summary printed after indexing\n")
        self.assertEqual(mismatches(self.root, index), [])
        self.assertNotIn("driver.log", {r["path"] for r in index["files"]})

    def test_same_size_tampering_of_a_listed_file_is_detected(self):
        index = runner.write_artifact_index(self.root)
        path = self.root / "core/fixed.json"
        original_size = path.stat().st_size
        path.write_text('{"oracle_failures":9}', encoding="utf-8")
        self.assertEqual(path.stat().st_size, original_size)
        self.assertEqual(mismatches(self.root, index), ["core/fixed.json"])

    def test_final_summary_tampering_is_detected(self):
        index = runner.write_artifact_index(self.root)
        (self.root / "validation-summary.json").write_text('{"ok":false}', encoding="utf-8")
        self.assertEqual(mismatches(self.root, index), ["validation-summary.json"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactIndexFixture))
    report = {"scope": "artifact-index metadata fixtures only; no production or benchmark execution",
              "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skips": len(result.skipped), "ok": result.wasSuccessful(),
              "positive": ["final validation summary is indexed", "live driver.log append leaves listed hashes valid", "tmp/sandbox/databases/self are excluded"],
              "negative": ["same-size listed-file tampering is detected", "summary tampering is detected"]}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 1)
