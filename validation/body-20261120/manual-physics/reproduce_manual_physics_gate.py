#!/usr/bin/env python3
"""Python 3.12+ isolated original-vs-current complete manual physics gates.

Run with --repo LOCAL_CLONE --output DIRECTORY; --baseline defaults d74848f.
No production source is edited. Each gate executes its exact archived/copied
source with __file__ under its output sandbox. WM_LINGSHU_ROOT is scoped to
that same sandbox, so both imports and _evidence writes stay isolated.
The original complete gate's failures are retained, not patched or masked.
"""
from __future__ import annotations
import argparse,ast,concurrent.futures,hashlib,io,json,math,os,platform,runpy,subprocess,sys,time,traceback,zipfile
from pathlib import Path
PHYSICS=Path("lingshu/world/physics.py")
GATE=Path("bridges/blender/wm_bridge/factory/anim/_det/gate_physics.py")
DEPS=Path("bridges/blender/wm_bridge/factory/_deps.py")

def sha(data):return hashlib.sha256(data).hexdigest()
def lfsha(data):return sha(data.replace(b"\r\n",b"\n"))
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def git(repo,*args,binary=False):
 result=subprocess.run(["git","-C",str(repo),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 return result.stdout if binary else result.stdout.decode("utf-8","replace").strip()
def function_source(path,name):
 text=path.read_text(encoding="utf-8");tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
 return ast.get_source_segment(text,node)
def p1_source(path):
 text=path.read_text(encoding="utf-8");start=text.index("    # ---------------- P1 ");end=text.index("    # ---------------- P2 ",start);return text[start:end]

def capture(repo,out,baseline,expected):
 current_physics=(repo/PHYSICS).read_bytes();current_gate=(repo/GATE).read_bytes()
 if expected and lfsha(current_physics)!=expected:raise RuntimeError("Fixed body physics LF SHA mismatch")
 head=git(repo,"rev-parse","HEAD");base=git(repo,"rev-parse",baseline);manifest={"repo":str(repo),"baseline":base,"head":head,"runner_lf_sha256":lfsha(Path(__file__).read_bytes()),"variants":{}}
 for variant,commit in (("baseline",base),("fixed",head)):
  data=git(repo,"archive","--format=zip",commit,"lingshu","bridges/blender/wm_bridge",binary=True);sandbox=out/variant/"sandbox";sandbox.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(io.BytesIO(data)) as archive:
   if any(not (sandbox/item.filename).resolve().is_relative_to(sandbox.resolve()) for item in archive.infolist()):raise RuntimeError("Unsafe ZIP path")
   archive.extractall(sandbox)
  if variant=="fixed":(sandbox/PHYSICS).write_bytes(current_physics);(sandbox/GATE).write_bytes(current_gate)
  manifest["variants"][variant]={"commit":commit,"sandbox":str(sandbox),"archive_sha256":sha(data),"archive_bytes":len(data),"working_physics_and_gate_overlay":variant=="fixed","physics_lf_sha256":lfsha((sandbox/PHYSICS).read_bytes()),"gate_lf_sha256":lfsha((sandbox/GATE).read_bytes()),"deps_lf_sha256":lfsha((sandbox/DEPS).read_bytes()),"P1_block_sha256":sha(p1_source(sandbox/GATE).encode()),"projectile_truth_source_sha256":sha(function_source(sandbox/PHYSICS,"projectile_truth").encode())}
 return manifest

def worker(args):
 sandbox=Path(args.sandbox).resolve();gate=sandbox/GATE;os.environ["WM_LINGSHU_ROOT"]=str(sandbox);sys.path.insert(0,str(sandbox/"bridges/blender"));sys.path.insert(0,str(sandbox));started=time.perf_counter();record={"variant":args.variant,"sandbox":str(sandbox),"expected_gate_file":str(gate),"environment":{"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"cpu_count":os.cpu_count(),"pythonhashseed":os.environ.get("PYTHONHASHSEED"),"WM_LINGSHU_ROOT":os.environ.get("WM_LINGSHU_ROOT"),"wall_clock_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}}
 try:
  namespace=runpy.run_path(str(gate),run_name="isolated_manual_physics_gate");record["actual_gate_file"]=namespace["__file__"];code=namespace["main"]();P=namespace["P"];actual=Path(P.__file__).resolve()
  if actual!=(sandbox/PHYSICS).resolve():raise RuntimeError("Gate imported the wrong physics module")
  raw_path=gate.parent.parents[3]/"_evidence/factory/raw/gate-physics.json"
  if not raw_path.resolve().is_relative_to(sandbox):raise RuntimeError("Gate evidence escaped sandbox")
  raw=json.loads(raw_path.read_text(encoding="utf-8"));record.update(gate_exit_code=code,rows=raw["rows"],failed=raw["failed"],raw=raw["raw"],raw_file=str(raw_path),raw_file_sha256=sha(raw_path.read_bytes()),actual_physics_source=str(actual),physics_lf_sha256=lfsha(actual.read_bytes()),gate_lf_sha256=lfsha(gate.read_bytes()),status="completed")
  p=raw["raw"]["P1"];initial_height=1.2;vy=7.5;g=P.DEFAULT_G;relative=vy*vy/(2*g);absolute=initial_height+relative
  record["P1_independent_interpretation"]={"initial_height_m":initial_height,"initial_vertical_speed_m_s":vy,"gravity_m_s2":g,"relative_rise_m":relative,"absolute_apex_y_m":absolute,"observed_apex_height":p["apex_height"],"gate_comparison_target":p["apex_expect"]-initial_height,"gate_d_apex":p["d_apex"],"observed_matches_absolute":abs(p["apex_height"]-absolute)<1e-12,"gate_target_matches_relative":abs(p["apex_expect"]-initial_height-relative)<1e-12,"mismatch_equals_initial_height":abs(p["d_apex"]-initial_height)<1e-12}
 except BaseException as e:
  code=3;record.update(status="error",error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc());print(record["traceback"],file=sys.stderr)
 record["elapsed_seconds"]=time.perf_counter()-started;write_json(Path(args.output),record);return code

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);p.add_argument("--repo",type=Path,default=Path.cwd());p.add_argument("--output",type=Path,required=True);p.add_argument("--baseline",default="d74848f");p.add_argument("--expected-fixed-sha");p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);p.add_argument("--variant",help=argparse.SUPPRESS);p.add_argument("--sandbox",help=argparse.SUPPRESS);args=p.parse_args()
 if args.worker:return worker(args)
 repo=args.repo.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True);manifest=capture(repo,out,args.baseline,args.expected_fixed_sha);write_json(out/"source_manifest.json",manifest)
 def execute(variant):
  directory=out/variant;result_path=directory/"worker_raw.json";env=os.environ.copy();env.update(PYTHONHASHSEED="20261120",PYTHONDONTWRITEBYTECODE="1",WM_LINGSHU_ROOT=manifest["variants"][variant]["sandbox"]);cmd=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--variant",variant,"--sandbox",manifest["variants"][variant]["sandbox"],"--output",str(result_path)]
  result=subprocess.run(cmd,env=env,cwd=manifest["variants"][variant]["sandbox"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",errors="replace");(directory/"stdout.log").write_text(result.stdout,encoding="utf-8");(directory/"stderr.log").write_text(result.stderr,encoding="utf-8");record=json.loads(result_path.read_text(encoding="utf-8"));record["subprocess_exit_code"]=result.returncode;return variant,record
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=dict(pool.map(execute,("baseline","fixed")))
 comparison={"sources":manifest,"variants":results,"P1_gate_block_identical":manifest["variants"]["baseline"]["P1_block_sha256"]==manifest["variants"]["fixed"]["P1_block_sha256"],"projectile_truth_function_identical":manifest["variants"]["baseline"]["projectile_truth_source_sha256"]==manifest["variants"]["fixed"]["projectile_truth_source_sha256"]}
 baseline,fixed=results["baseline"],results["fixed"];comparison["preexisting_P1_confirmed"]=all(r.get("status")=="completed" and "P1" in r.get("failed",[]) and all(r.get("P1_independent_interpretation",{}).get(k,False) for k in ("observed_matches_absolute","gate_target_matches_relative","mismatch_equals_initial_height")) for r in (baseline,fixed)) and comparison["P1_gate_block_identical"] and comparison["projectile_truth_function_identical"]
 write_json(out/"comparison.json",comparison);lines=["# Complete manual physics gate: isolated parity","","The exact original baseline gate and current PR gate ran separately and completely under their output sandboxes. Both physics imports and gate _evidence writes stayed in those sandboxes. No gate assertion or production source was modified.","","| Variant | Gate exit | Passed rows | Failed rows | Failure tags | P4 RK4 maximum rad |","|---|---:|---:|---:|---|---:|"]
 for variant,r in results.items():lines.append("| %s | %s | %d | %d | %s | %s |"%(variant,r.get("gate_exit_code","error"),sum(bool(row["ok"]) for row in r.get("rows",[])),len(r.get("failed",[])),", ".join(r.get("failed",[])),r.get("raw",{}).get("P4",{}).get("worst_rk4_rad","n/a")))
 lines += ["","Pre-existing P1 confirmed: "+str(comparison["preexisting_P1_confirmed"]),"","The P1 gate source block is identical: "+str(comparison["P1_gate_block_identical"])+". The projectile_truth function source is identical: "+str(comparison["projectile_truth_function_identical"])+".","","P1 compares an absolute apex y against a relative rise. With initial y=1.2 m and v_y=7.5 m/s, both variants return the same absolute apex; the gate subtracts the initial height from its own expected absolute apex and therefore observes exactly the initial 1.2 m as a mismatch. Full original stdout/stderr, JSON rows and the gate's raw JSON remain available. This is a documented existing gate assertion issue, not an all-green gate result.","","Independent P1 values:",""]
 for variant,r in results.items():lines.append("- "+variant+": "+json.dumps(r.get("P1_independent_interpretation",{}),ensure_ascii=False))
 (out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n");print(json.dumps({"report":str(out/"report.md"),"preexisting_P1_confirmed":comparison["preexisting_P1_confirmed"],"variants":{v:{"status":r.get("status"),"failed":r.get("failed"),"gate_exit_code":r.get("gate_exit_code"),"elapsed_seconds":r.get("elapsed_seconds")} for v,r in results.items()}},ensure_ascii=False),flush=True)
 return 0 if comparison["preexisting_P1_confirmed"] and all(r.get("status")=="completed" for r in results.values()) else 1
if __name__=="__main__":raise SystemExit(main())
