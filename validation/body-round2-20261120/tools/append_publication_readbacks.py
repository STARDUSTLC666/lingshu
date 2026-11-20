"""Append final body readbacks and independent audits; do not publish messages."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

PREFIX = Path("validation/body-round2-20261120")
EVIDENCE = "83496a7f49ede450729cb944fec36a0fbbafec6f"
DETACHED = {"sanitization-manifest.json", "preparation-audit.json", "final-seal-audit.json"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    source, repo = args.source_root.resolve(), args.repo.resolve()
    target = repo / PREFIX
    spec = importlib.util.spec_from_file_location("prep_readbacks", target / "tools/prepare_round2_public_evidence.py")
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    latest = json.loads((source / "final-publication/latest-verified.json").read_text(encoding="utf-8"))
    assert latest["evidence_commit"] == EVIDENCE
    receipt_path = Path(latest["receipt_path"])
    receipts = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipts["all_eight_verified"] and len(receipts["targets"]) == 8
    assert {row["number"] for row in receipts["targets"]} == {1477, 1478, 1479, 1480, 2791, 2792, 2793, 2794}
    assert all(row["readback_verified"] and row["final_marker_count"] == 1 and row["evidence_commit"] == EVIDENCE
               for row in receipts["targets"])
    manifest = json.loads((target / "sanitization-manifest.json").read_text(encoding="utf-8"))
    records = {row["artifact"]: row for row in manifest["artifacts"]}

    def clean(value):
        if isinstance(value, str):
            return prep.sanitize(value)
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                key = prep.sanitize(key)
                assert key not in result
                result[key] = clean(item)
            return result
        return value

    def publish(name, raw, origin):
        name = Path(name).as_posix()
        if name.endswith(".json"):
            old = json.loads(raw.decode("utf-8-sig"), parse_constant=prep.reject_constant)
            new = clean(old)
            assert prep.numeric_leaves(old) == prep.numeric_leaves(new)
            data = prep.dumps(new)
        else:
            data = prep.sanitize(re.sub(r"\r+\n|\r", "\n", raw.decode("utf-8-sig"))).encode("utf-8")
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        records[name] = {"artifact": name, "mode": "final_publication_readback_or_independent_audit",
                         "source": origin, "original_sha256": prep.sha(raw), "original_bytes": len(raw),
                         "published_sha256": prep.sha(data), "published_bytes": len(data)}

    publish("publication-readbacks/receipts.json", receipt_path.read_bytes(), receipt_path.relative_to(source).as_posix())
    for row in receipts["targets"]:
        name = f"{row['kind']}-{row['number']}-body.md"
        raw = (receipt_path.parent / name).read_bytes()
        assert prep.sha(raw.replace(b"\r\n", b"\n")) == row["body_sha256_lf"]
        publish("publication-readbacks/" + name, raw, (receipt_path.parent / name).relative_to(source).as_posix())
    for pr in (1477, 1478, 1479, 1480):
        p = receipt_path.parent / f"pr-{pr}-checks.json"
        publish("publication-readbacks/" + p.name, p.read_bytes(), p.relative_to(source).as_posix())
    for folder, names in {
        "main-sync-publication-audit": ["REPORT.md", "audit-summary.json", "github-merge-commit.json", "audit_append.py"],
        "final-publication-audit": ["REPORT.md", "audit-summary.json", "extra-inventory-and-api.json", "audit_final_index.py"],
    }.items():
        for name in names:
            p = source / folder / name
            publish(Path(folder) / name, p.read_bytes(), p.relative_to(source).as_posix())
    p = source / "finalize_publication.py"
    publish("tools/finalize_publication.py", p.read_bytes(), p.relative_to(source).as_posix())
    publish("tools/append_publication_readbacks.py", Path(__file__).read_bytes(), "generated publication readback append helper")

    status = json.loads((target / "source-status.json").read_text(encoding="utf-8"))
    status["bounty_intake_receipts"].update({
        "final_evidence_commit": EVIDENCE, "final_body_readbacks": "publication-readbacks/receipts.json",
        "all_eight_final_bodies_verified": True,
        "note": "All four PR and four original intake bodies now contain the immutable completed evidence link. Original intake markers and historical measurements are preserved. No new intake or labels were added."})
    status["publication_observation"] = {
        "pr_states": {str(row["number"]): {"state": row["state_observed"], "merged": row["merged_observed"],
                                             "head": row["source_head"], "at": row["observed_at"]}
                      for row in receipts["targets"] if row["kind"] == "pr"},
        "maintainer_merged_previous_prs": [1469, 1473, 1474], "maintainer_also_merged_pr1480": True,
        "main_after_1480": "6b73082406d40a630a44cd68559c1f66b3652390",
        "note": "Observed maintainer actions only; this task did not merge, grade, claim or settle contributions."}
    publish("source-status.json", prep.dumps(status), "generated verified final publication status")
    for name in ("README.md", "FINAL_VALIDATION.md"):
        text = (target / name).read_text(encoding="utf-8")
        marker = "## Final publication readbacks"
        if marker in text:
            text = text.split(marker)[0].rstrip() + "\n"
        text += (f"\n{marker}\n\nAll four PR bodies1477–1480 and original intake bodies2791–2794 were updated to immutable final evidence `{EVIDENCE}` and read back exactly. Original intake markers remain. Body hashes, observed states and exact heads are in `publication-readbacks/receipts.json`; public body snapshots and current check projections are adjacent. Maintainer merged1480; no new bounty, self-grading or merge action was performed by this task.\n\n"
                 "The independent review snapshots in `final-publication-audit/` (1580 manifested artifacts) and `main-sync-publication-audit/` (1636 manifested artifacts) describe their explicitly frozen preappend inventories. They are historical audit results, not new test runs or a claim that their old inventory counts include this later receipt append. New CI's actual synthetic merge checkout has the same Git tree as current PR1478 head.\n")
        publish(name, text.encode("utf-8"), "generated final readback navigation, retaining historical outcomes")
    selected = [(PREFIX / name).as_posix() for name in records]
    for start in range(0, len(selected), 120):
        subprocess.run(["git", "add", "-f", "--", *selected[start:start+120]], cwd=repo, check=True, capture_output=True)
    blobs = prep.staged_blobs(repo, selected)
    private = re.compile(rb"(?i)(?:[ce]:[\\/]+(?:users|lingshu|\xe5\x85\xac\xe7\x9b\x8a\xe7\xab\x99))")
    xml_count = json_count = 0
    for name, row in records.items():
        data = blobs[(PREFIX / name).as_posix()]
        assert prep.sha(data) == row["published_sha256"] and len(data) == row["published_bytes"], name
        assert not private.search(data), name
        assert not name.endswith((".pyc", ".db", ".sqlite", ".sqlite3"))
        if name.endswith(".json"):
            json.loads(data, parse_constant=prep.reject_constant)
            json_count += 1
        if name.endswith(".xml"):
            ET.fromstring(data)
            xml_count += 1
        row["git_canonical_blob_sha256"], row["git_canonical_blob_bytes"] = prep.sha(data), len(data)
    manifest["artifacts"] = list(records.values())
    (target / "sanitization-manifest.json").write_bytes(prep.dumps(manifest))
    for name in ("preparation-audit.json", "final-seal-audit.json"):
        audit = json.loads((target / name).read_text(encoding="utf-8"))
        audit.update({"canonical_blobs_verified": len(records), "artifact_count": len(records), "xml_files": xml_count,
                      "final_eight_publication_readbacks_verified": True, "immutable_final_evidence_link": EVIDENCE})
        if "staged_evidence_files" in audit:
            audit["staged_evidence_files"] = len(records) + len(DETACHED)
        (target / name).write_bytes(prep.dumps(audit))
    subprocess.run(["git", "add", "-f", "--", *[(PREFIX / name).as_posix() for name in sorted(DETACHED)]], cwd=repo, check=True, capture_output=True)
    files = set(subprocess.check_output(["git", "ls-files", "-z", "--", PREFIX.as_posix()], cwd=repo).decode("utf-8").strip("\0").split("\0"))
    assert files == set(selected) | {(PREFIX / name).as_posix() for name in DETACHED}
    print(json.dumps({"ok": True, "artifacts": len(records), "indexed_files": len(files), "xml": xml_count,
                      "json": json_count, "final_body_readbacks": 8, "final_evidence_commit": EVIDENCE}))


if __name__ == "__main__":
    main()
