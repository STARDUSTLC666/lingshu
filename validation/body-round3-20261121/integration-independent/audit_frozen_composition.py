"""Verify exact two-fix composition on the immutable previous twelve-fix tree."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = Path(r"[workspace]/lingshu/work\lingshu-body-round3-integration-20261121")
BEFORE = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
BASE = "6b73082406d40a630a44cd68559c1f66b3652390"
FROZEN = "f81ee3a9939f3dad7c277145766508c113742ba0"
PRS = {1481: "4a352249ef6db7975353b84bc640712d46f7181b", 1482: "bd208a379e44497e9f35fdc145838abb19e6d313"}
PRODUCTION = {"lingshu/nn/hex_cnn.py": (1481, "HexGrid.neighbors"),
              "lingshu/world/scene_simulator.py": (1482, "SceneSimulator._apply_command")}
MANIFEST = "docs/intake/body-export-v0.1/_export_manifest.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def source(ref, path):
    return git("show", ref + ":" + path)


def function_map(data):
    result = {}
    def walk(node, parent):
        for child in ast.iter_child_nodes(node):
            scope = parent
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = parent + (child.name,)
                if not isinstance(child, ast.ClassDef):
                    key = ".".join(scope)
                    assert key not in result
                    result[key] = ast.dump(child, include_attributes=False)
            walk(child, scope)
    walk(ast.parse(data), ())
    return result


assert git("rev-parse", "HEAD").decode().strip() == FROZEN
assert git("status", "--porcelain").decode().strip() == ""
paths = git("diff", "--name-only", BEFORE, FROZEN).decode().splitlines()
assert sorted(path for path in paths if path.startswith("lingshu/")) == sorted(PRODUCTION)
production = []
for path, (pr, method) in PRODUCTION.items():
    old, current, individual = (source(ref, path) for ref in (BEFORE, FROZEN, PRS[pr]))
    a, b, c = (function_map(data) for data in (old, current, individual))
    assert a.keys() == b.keys()
    changed = [name for name in a if a[name] != b[name]]
    assert changed == [method], (path, changed)
    assert b[method] == c[method]
    production.append({"path": path, "changed_method": method, "pr": pr,
                       "before_sha256": hashlib.sha256(old).hexdigest(),
                       "combined_sha256": hashlib.sha256(current).hexdigest(),
                       "individual_sha256": hashlib.sha256(individual).hexdigest(),
                       "new_method_exactly_matches_individual_pr": True,
                       "other_functions_unchanged_from_previous_twelve": True})
expected = set(PRODUCTION) | {MANIFEST}
artifacts = []
for pr, head in PRS.items():
    for path in git("diff", "--name-only", BASE, head).decode().splitlines():
        expected.add(path)
        if path in PRODUCTION or path == MANIFEST:
            continue
        data, incoming = source(FROZEN, path), source(head, path)
        assert data == incoming, path
        artifacts.append({"path": path, "pr": pr, "sha256": hashlib.sha256(data).hexdigest(), "exact_match": True})
assert set(paths) == expected
assert source(FROZEN, "lingshu/core/core.py") == source(BEFORE, "lingshu/core/core.py")
out = ROOT / "integration-independent"
out.mkdir(exist_ok=True)
summary = {"ok": True, "source_head": FROZEN, "source_tree": git("rev-parse", FROZEN + "^{tree}").decode().strip(),
           "previous_twelve": BEFORE, "merged_main": BASE, "individual_pr_heads": PRS,
           "changed_paths": paths, "production": production, "exact_nonproduction_artifacts": artifacts,
           "previous_twelve_production_preserved": True,
           "interpretation": "Only the two specified methods extend the previously validated twelve-fix production source. Original nonproduction artifacts match their PRs exactly; manifest reflects the merged module bytes. This is composition evidence, not a substitute for full gates."}
(out / "composition.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"ok": True, "production_methods": len(production), "exact_nonproduction_artifacts": len(artifacts), "changed_paths": len(paths)}))
