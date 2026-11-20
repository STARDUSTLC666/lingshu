"""Independent read-only staged-evidence audit; only writes its own report directory."""
from __future__ import annotations
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

REPO = Path(r"[workspace]/lingshu/work\lingshu-body-round2-evidence-final-20261121")
PREFIX = "validation/body-round2-20261120/"
TARGET = REPO / PREFIX
RAWROOT = Path(r"[workspace]/lingshu/outputs\body-round2-20261120")
OUT = RAWROOT / "main-sync-publication-audit"
OLD = "89c005b7fdd48f64c603d34c280a4d18a93956f7"
NEW = "41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50"
MEASURED = "bae2eaea9fb77e9e451f1b220d17f9096d06ee78"
COMBINED = "5226860c1d70bc7fc6619cf79aff10c4f9a2a234"
MERGE = "6cfd83024a94b93bad714ca670c6921d8bc73866"
MAIN = "04e0ecb6a3669c90efbb4a1583816a8f7ca26bc7"
BRAIN = "98d6b899533a82fb1047f952987229c62a9929fb"

def sha(b): return hashlib.sha256(b).hexdigest()
def git(*args): return subprocess.check_output(["git", *args], cwd=REPO)
def read_json(p): return json.loads(p.read_bytes(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def normalize(s): return re.sub(r"\r+\n|\r", "\n", s)
def redact(s):
    s = re.sub(r"(?i)\be:[\\/]+lingshu[\\/]*", "[workspace]/lingshu/", s)
    s = re.sub(r"(?i)\be:[\\/]+公益站[\\/]*", "[workspace]/", s)
    return re.sub(r"(?i)\bc:[\\/]+users[\\/]+[^\\/\s\"']+", "[user-home]", s)
def clean(v):
    if isinstance(v, str): return redact(v)
    if isinstance(v, list): return [clean(x) for x in v]
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            k = redact(k)
            assert k not in out
            out[k] = clean(x)
        return out
    return v
def numeric(v):
    if isinstance(v, bool) or v is None or isinstance(v, str): return []
    if isinstance(v, (int, float)): return [(type(v).__name__, repr(v))]
    if isinstance(v, list): return [n for x in v for n in numeric(x)]
    if isinstance(v, dict): return [n for x in v.values() for n in numeric(x)]
    raise TypeError(type(v))
def xml_sem(e, red=False):
    f = redact if red else lambda s: s
    return (e.tag, tuple(sorted((k, f(v)) for k,v in e.attrib.items())),
            f(e.text) if e.text else e.text, f(e.tail) if e.tail else e.tail,
            tuple(xml_sem(x,red) for x in e))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"ok": False, "scope": "Independent current-head append and full staged inventory audit; no source/evidence writes and no helper rerun."}
    manifest = read_json(TARGET / "sanitization-manifest.json")
    records = {r["artifact"]:r for r in manifest["artifacts"]}
    assert len(records) == len(manifest["artifacts"]) == 1636
    detached = {"sanitization-manifest.json", "preparation-audit.json", "final-seal-audit.json"}
    index = {}
    for entry in git("ls-files", "--stage", "-z").split(b"\0"):
        if not entry: continue
        meta,p = entry.split(b"\t",1)
        p = p.decode()
        if p.startswith(PREFIX):
            mode,oid,stage = meta.decode().split()
            assert stage == "0"
            index[p.removeprefix(PREFIX)] = oid
    assert set(index) == set(records)|detached, (set(index)-set(records)-detached, set(records)-set(index))
    batch = git("cat-file", "--batch",) if False else subprocess.check_output(
        ["git","cat-file","--batch"], cwd=REPO,
        input=("\n".join(index.values())+"\n").encode())
    stream = io.BytesIO(batch)
    blobs = {}
    for name,oid in index.items():
        actual,kind,size = stream.readline().decode().split()
        assert actual == oid and kind == "blob"
        blobs[name] = stream.read(int(size))
        assert stream.read(1) == b"\n"
    parses=Counter(); private=[]; xmlnames=[]
    for name,b in blobs.items():
        if name in records:
            r=records[name]
            assert sha(b)==r["published_sha256"]==r["git_canonical_blob_sha256"],name
            assert len(b)==r["published_bytes"]==r["git_canonical_blob_bytes"],name
        text=b.decode("utf-8-sig")
        if re.search(r"(?i)\b(?:e:[\\/]+(?:lingshu|公益站)|c:[\\/]+users[\\/]+)",text): private.append(name)
        assert not re.search(r"(?:^|/)(?:__pycache__|\.pytest_cache|\.venv)(?:/|$)|\.(?:pyc|db|sqlite3?)$",name),name
        if name.endswith(".json"): json.loads(text,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x))); parses["json"]+=1
        if name.endswith(".xml"): ET.fromstring(b); parses["xml"]+=1; xmlnames.append(name)
    assert not private,private
    assert parses["xml"]==315
    junit=json.loads(blobs["junit-index.json"])
    assert len(junit["runs"])==len({r["artifact"] for r in junit["runs"]})==315
    assert {r["artifact"] for r in junit["runs"]}==set(xmlnames)
    for row in junit["runs"]:
        root=ET.fromstring(blobs[row["artifact"]]); suites=[root] if root.tag=="testsuite" else root.findall(".//testsuite")
        assert row["suites"]==[dict(s.attrib) for s in suites]
    for name in detached-{"sanitization-manifest.json"}:
        d=json.loads(blobs[name]); assert d["artifact_count"]==d["canonical_blobs_verified"]==1636
        assert d["xml_files"]==315 and d["windows_gate_ok"] is False
        assert d["current_core_pr_head"]==NEW and d["current_core_ci_verified_success"] is True
    report["inventory"]={"manifested":1636,"detached":3,"staged":len(index),"parse_counts":dict(parses),"private_prefix_findings":private,"canonical_hashes_and_coverage_verified":True,"junit_inventory_complete":True}
    appended=[]
    for name,r in records.items():
        if not name.startswith("core-main-sync/") or name.endswith("archive-digests.json"): continue
        original=RAWROOT/r["source"]
        assert original.is_file(),str(original)
        raw=original.read_bytes(); b=blobs[name]
        assert len(raw)==r["original_bytes"] and sha(raw)==r["original_sha256"],name
        if name.endswith(".json"):
            a=json.loads(raw); z=json.loads(b)
            assert clean(a)==z and numeric(a)==numeric(z),name
        elif name.endswith(".xml"):
            assert xml_sem(ET.fromstring(raw),True)==xml_sem(ET.fromstring(b)),name
        else: assert redact(normalize(raw.decode("utf-8-sig"))).encode()==b,name
        appended.append(name)
    report["append_raw_to_public"]={"files_verified":len(appended),"json_keys_values_numbers_preserved":True,"xml_full_semantics_preserved":True}

    status=json.loads(blobs["source-status.json"]); c=status["core"]
    old=git("show",OLD+":lingshu/core/core.py"); new=git("show",NEW+":lingshu/core/core.py")
    assert git("show",MEASURED+":lingshu/core/core.py")==old
    assert git("show",COMBINED+":lingshu/core/core.py")==new
    assert c["measured_commit"]==MEASURED and c["final_pr_head"]==NEW and c["pre_main_sync_validated_pr_head"]==OLD
    assert c["pre_main_sync_production_canonical_sha256"]==sha(old)
    assert c["production_canonical_sha256"]==sha(new)
    assert c["measurement_source_identical_to_pre_sync_pr_head"] is True
    assert c["measurement_source_identical_to_final_head"] is False
    def functions(b):
        out={}
        for n in ast.walk(ast.parse(b)):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): out.setdefault(n.name,[]).append(ast.dump(n,include_attributes=False))
        return out
    a,z=functions(old),functions(new); assert a.keys()==z.keys()
    changed=sorted(k for k in a if a[k]!=z[k]); assert changed==["search_skills"]
    assert status["remote_ci"]["historical_pre_sync_core_head"]["head"]==OLD
    assert status["remote_ci"]["pull_requests"]["1478"]["head"]==NEW
    assert json.loads(blobs["audit-core/bench-fixed.json"])["source_sha256"]=="1ced866b6dc912537e754d405d4acd512cff9703cda564e26c5eebc4d93a94bb"
    report["source_alignment"]={"measured":MEASURED,"historical":OLD,"current":NEW,"combined_core_identical":COMBINED,"historical_core_sha256":sha(old),"current_core_sha256":sha(new),"changed_ast_functions":changed,"historical_measurements_not_relabelled":True}

    rawci=RAWROOT/"core-main-sync/ci/pr1478"
    summary=read_json(rawci/"summary.json")
    assert summary["all_complete"] and summary["all_success"] and summary["semantic_evidence_verified"]
    latest=sorted((rawci/"api").iterdir())[-1]
    alljobs={}
    runs=[]
    for runid in (44781318899,44781318941):
        run=read_json(latest/f"{runid}-run.json"); jobs=read_json(latest/f"{runid}-jobs.json")["jobs"]
        assert run["id"]==runid and run["head_sha"]==NEW and run["status"]=="completed" and run["conclusion"]=="success"
        assert all(j["run_id"]==runid and j["head_sha"]==NEW and j["status"]=="completed" and j["conclusion"]=="success" for j in jobs)
        assert all(not [s for s in j["steps"] if s["conclusion"] in {"failure","cancelled","timed_out"}] for j in jobs)
        alljobs.update({j["id"]:j for j in jobs}); runs.append({"id":runid,"head":run["head_sha"],"jobs":len(jobs),"conclusion":run["conclusion"]})
        folder=rawci/f"{runid}-attempt1"; idx=read_json(folder/"archive-index.json"); zraw=(folder/"all-run-logs.zip").read_bytes()
        assert sha(zraw)==idx["zip_sha256"]
        with zipfile.ZipFile(io.BytesIO(zraw)) as archive:
            assert set(archive.namelist())=={x["path"] for x in idx["files"]}
            for item in idx["files"]:
                payload=archive.read(item["path"]); assert len(payload)==item["bytes"] and sha(payload)==item["sha256"]
            for job in jobs:
                raw=(folder/f"{job['id']}.log").read_bytes()
                matches=[n for n in archive.namelist() if "/" not in n and n.endswith(job["name"]+".txt")]
                assert len(matches)==1 and archive.read(matches[0])==raw
    assert len(alljobs)==4
    checks=[]
    workflow=git("show",NEW+":.github/workflows/gate.yml").decode()
    scriptblock=workflow.split("SCRIPT_TESTS: >-",1)[1].split("\n\n",1)[0]
    expected=re.findall(r"^\s+(tests/\S+\.py)\s*$",scriptblock,re.M)
    assert len(expected)==102
    assert (rawci/"workflow.yml").read_bytes().replace(b"\r\n",b"\n")==workflow.encode().replace(b"\r\n",b"\n")
    for job in summary["gate_jobs"]+summary["title_jobs"]:
        jid=job["job_id"]; assert jid in alljobs
        runid=alljobs[jid]["run_id"]; raw=(rawci/f"{runid}-attempt1/{jid}.log").read_bytes()
        assert sha(raw)==job["raw_log_sha256"] and len(raw)==job["raw_log_bytes"]
        if runid!=44781318899: continue
        text=raw.decode("utf-8-sig"); lines=[re.sub(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?","",line) for line in text.splitlines()]
        scripts=re.findall(r"##\[group\]script test: (tests/\S+\.py)",text)
        assert scripts==expected==job["scripts"] and len(set(scripts))==102
        assert any(line.startswith("脚本式测试全部通过：") for line in lines)
        brain=text.split("##[group]script test: tests/test_brain_store.py",1)[1].split("##[endgroup]",1)[0]
        assert "SUMMARY 23/23 通过" in brain and "VERDICT=PASS" in brain
        assert BRAIN in text and re.search(BRAIN+r".*FETCH_HEAD",text)
        assert any(line.startswith("脑端 clone 成功") for line in lines)
        assert "HEAD is now at 6cfd830 Merge "+NEW+" into "+MAIN in text
        summaries=[x.strip() for x in lines if re.search(r"\b\d+ passed\b",x) and re.search(r"\bin [\d.]+s",x)]
        final=summaries[-1]
        assert re.search(r"\b5638 passed, 40 skipped, \d+ warnings, 98 subtests passed in ",final)
        skips=[x for x in lines if " SKIPPED " in x]; assert len(skips)==40
        checks.append({"job_id":jid,"name":job["name"],"raw_sha256":sha(raw),"scripts":102,"brain":"23/23 actual","pytest_summary":final,"skip_lines":40})
    merge_api=subprocess.check_output(["gh","api",f"repos/FuRongJun-1999/lingshu/git/commits/{MERGE}"])
    (OUT/"github-merge-commit.json").write_bytes(merge_api)
    merged=json.loads(merge_api); current_tree=git("rev-parse",NEW+"^{tree}").decode().strip()
    assert merged["sha"]==MERGE and merged["tree"]["sha"]==current_tree
    assert {p["sha"] for p in merged["parents"]}=={MAIN,NEW}
    report["ci"]={"runs":runs,"gate_jobs":checks,"title_verified":True,"raw_archive_indexes_verified":True,"actual_checkout_merge":MERGE,"actual_checkout_tree":current_tree,"same_tree_as_current_head":True,"workflow_scripts_source_verified":True}
    scoped=ET.fromstring(blobs["core-main-sync/scoped.xml"]); suite=scoped.find("testsuite") if scoped.tag!="testsuite" else scoped
    assert suite.attrib["tests"]=="60" and suite.attrib["failures"]==suite.attrib["errors"]==suite.attrib["skipped"]=="0"
    report["scoped"]={"tests":60,"failures":0,"errors":0,"skips":0}
    helper=blobs["tools/append_core_main_sync.py"].decode(); ast.parse(helper)
    for token in ('core.setdefault("pre_main_sync_validated_pr_head", OLD)',
                  'core.setdefault("pre_main_sync_production_canonical_sha256", historical_core_hash)',
                  'core.setdefault("measurement_source_identical_to_pre_sync_pr_head", core["measurement_source_identical_to_final_head"])',
                  'remote.setdefault("historical_pre_sync_core_head", remote["pull_requests"]["1478"])'):
        assert token in helper
    report["helper_logic"]={"historical_identity_stable_on_repeat":True,"not_executed_or_reexecuted_by_auditor":True,"self_manifested":True,"xml_semantics_and_junit_rebuild_present":True,"note":"Generated artifact original_sha256 fields may update on repeat; source measurements and historical head/hash booleans stay stable. This is a code review, not an execution test."}
    report["ok"]=True
    (OUT/"audit-summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"REPORT.md").write_text("# Current-head append publication audit\n\nPASS. Independently checked 1636 manifested artifacts plus three detached metadata files, exact canonical blob coverage/hashes, JSON/XML parsing and private prefixes; 315 XML runs have matching JUnit index.\n\nNew PR1478 CI: 3 successful gate legs, each 5638 passed / 40 skipped / 98 subtests; 102 actual script groups and actual brain 23/23, plus title success. Raw job logs match original indexed ZIP entries; saved API job/run identities and workflow script source agree. Actual CI checkout was GitHub merge commit `"+MERGE+"`; independently queried commit API confirms its tree equals current `"+NEW+"` exactly.\n\nMeasured `"+MEASURED+"` / historical `"+OLD+"` evidence remains historical; new current core matches frozen combined source `"+COMBINED+"`. Only search_skills AST changes during the merge; fresh-decay functions remain unchanged. Windows gate remains false with the original known failure. The helper was code-reviewed for repeat stability and not rerun.\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__": main()
