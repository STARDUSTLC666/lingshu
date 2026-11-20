#!/usr/bin/env python3
"""Python 3.12+ / mpmath: public top-level motions plus pendulum interaction.

Archives baseline, math-only, top-level-only and combined Git refs. Calls both
eval_at(spec_with_top_level_motions, frame) and the explicit motions parameter.
The oracle is an independent 80-digit sn(K-u,m), evaluated at actual binary64
elapsed=frame/fps. Writes only under --output, never alters any source tree.
No Blender/NumPy/Pillow is used; this is pure public-pose correctness evidence.
"""
from __future__ import annotations
import argparse,concurrent.futures,hashlib,importlib,io,json,math,os,platform,random,subprocess,sys,time,zipfile
from pathlib import Path
import mpmath as mp
BASE="d74848fb33dbff1d719959df19d1266a1ac60f44"
MATH="e0771a810b8846676f3545542b2e70d5e0011467"
TOP="1ab5cc7f295ed5748b50c7ffde26cf2a34663204"
COMBINED="231aa5334c0c0f2f01eccf6c547ebd97a478a8d0"
EXPECTED="8c973edbf7768dcb891546ba24422b020a85ad4b2a987a64c0581e846773f4f8"
REL=Path("bridges/blender/wm_bridge/factory/anim/eval.py")
SEED=20261120

def sha(data):return hashlib.sha256(data).hexdigest()
def lfsha(data):return sha(data.replace(b"\r\n",b"\n"))
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def git(repo,*args,binary=False):
 result=subprocess.run(["git","-C",str(repo),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 return result.stdout if binary else result.stdout.decode("utf-8","replace").strip()
def period(theta):
 k=mp.sin(mp.mpf(theta)/2);return 4*mp.ellipk(k*k)
def reference(theta,w,elapsed):
 k=mp.sin(mp.mpf(theta)/2);value=2*mp.asin(k*mp.ellipfun("sn",mp.ellipk(k*k)-mp.mpf(w)*mp.mpf(elapsed),k*k))
 if isinstance(value,mp.mpc) and abs(value.imag)>mp.mpf("1e-60"):raise RuntimeError("Nonreal oracle")
 return mp.re(value)

def cases():
 for degrees0 in (5.,120.,179.99999,math.degrees(math.nextafter(math.pi,0.))):
  for sign in (1.,-1.):
   degrees=sign*degrees0;theta=math.radians(degrees);p=period(theta)
   for w in (.5,2.):
    for fraction in (0.,.125,.25,.375,.5,.75,1.125,3.375):
     for tsign in ((1.,) if fraction==0 else (1.,-1.)):
      desired=float(tsign*mp.mpf(fraction)*p/mp.mpf(w))
      for axis in ("x","y","z"):yield {"category":"fixed_joint_grid","degrees":degrees,"omega0":w,"desired_time":desired,"axis":axis,"target_period_fraction":tsign*fraction}
 rng=random.Random(SEED)
 for i in range(64):
  theta=rng.choice((-1.,1.))*(math.pi-10**rng.uniform(-15.,-.1));degrees=math.degrees(theta)
  if abs(math.radians(degrees))>=math.pi:degrees=math.copysign(math.nextafter(180.,0.),degrees)
  theta=math.radians(degrees);w=10**rng.uniform(-1.,1.);fraction=rng.uniform(-30.,30.)
  yield {"category":"seeded_near_pi_joint","degrees":degrees,"omega0":w,"desired_time":float(mp.mpf(fraction)*period(theta)/mp.mpf(w)),"axis":rng.choice(("x","y","z")),"target_period_fraction":fraction}

class Checks:
 def __init__(self):self.counts={};self.failures={}
 def check(self,label,ok,detail=None):
  self.counts[label]=self.counts.get(label,0)+1
  if not ok:
   entry=self.failures.setdefault(label,{"count":0,"examples":[]});entry["count"]+=1
   if len(entry["examples"])<8:entry["examples"].append(detail)
 def result(self):return {"assertions":sum(self.counts.values()),"failed_assertions":sum(x["count"] for x in self.failures.values()),"checks":self.counts,"failures":self.failures}

def worker(args):
 mp.mp.dps=80;sys.path.insert(0,str(Path(args.snapshot)/"bridges/blender"));E=importlib.import_module("wm_bridge.factory.anim.eval");rows=[];checks=Checks();cache={}
 for i,case in enumerate(cases()):
  theta=math.radians(case["degrees"]);w=case["omega0"];desired=case["desired_time"];frame=0 if desired==0 else (1 if desired>0 else -1);fps=120. if desired==0 else 1/abs(desired);elapsed=frame/fps;component={"x":1,"y":2,"z":3}[case["axis"]];key=(theta,w,elapsed,desired)
  if key not in cache:cache[key]=(reference(theta,w,elapsed),reference(theta,w,desired))
  expected,desired_ref=cache[key];qref=[mp.cos(expected/2),mp.mpf(0),mp.mpf(0),mp.mpf(0)];qref[component]=mp.sin(expected/2)
  motion={"link":"bob","kind":"pendulum","axis":case["axis"],"exact":True,"theta0_deg":case["degrees"],"omega0":w,"zeta":0.}
  spec={"schema":"wmfactory.spec/1","name":"joint_crossfix_oracle","scene":{"fps":fps},"links":[{"name":"bob","anchor":[0,0,0],"parts":[]}],"joints":[]};top_spec=dict(spec,motions=[dict(motion)]);before=json.dumps([spec,top_spec,motion],sort_keys=True)
  row=dict(case,index=i,frame=frame,fps=fps,elapsed_binary64=elapsed,theta0_rad_binary64=theta,reference_angle_rad_80dps=mp.nstr(expected,80),reference_quaternion_80dps=[mp.nstr(x,80) for x in qref]);row["input_conversion"]={"desired_to_elapsed_error_s":float(abs(mp.mpf(elapsed)-mp.mpf(desired))),"division_rounding_error_s":float(abs(mp.mpf(elapsed)-mp.mpf(frame)/mp.mpf(fps))),"product_rounding_error_u":float(abs(mp.mpf(w*elapsed)-mp.mpf(w)*mp.mpf(elapsed))),"reference_angle_shift_rad":float(abs(expected-desired_ref))}
  for route in ("top_level","explicit_parameter"):
   try:
    pose=E.eval_at(top_spec,frame)["bob"] if route=="top_level" else E.eval_at(spec,frame,motions=[motion])["bob"];q=list(pose["quat"]);actual=2*math.atan2(q[component],q[0]);error=float(abs(mp.mpf(actual)-expected));qerror=max(float(abs(mp.mpf(a)-b)) for a,b in zip(q,qref));row[route]={"quaternion":q,"position":list(pose["pos"]),"angle_rad":actual,"angle_error_rad":error,"max_component_error":qerror}
    checks.check(route+"_supported",True,i);checks.check(route+"_angle_1e_11",error<=1e-11,{"case":i,"error":error});checks.check(route+"_quaternion_5e_12",qerror<=5e-12,{"case":i,"error":qerror});checks.check(route+"_unit",abs(sum(x*x for x in q)-1)<=5e-15,i);checks.check(route+"_origin",list(pose["pos"])==[0.,0.,0.],i)
   except Exception as e:row[route]={"error_type":type(e).__name__,"error":str(e)};checks.check(route+"_supported",False,{"case":i,"error":type(e).__name__})
  if "quaternion" in row["top_level"]:
   again=E.eval_at(top_spec,frame)["bob"];checks.check("top_level_repeat_pure",list(again["quat"])==row["top_level"]["quaternion"],i)
   reverse=E.eval_at(top_spec,-frame)["bob"];checks.check("top_level_time_even",list(reverse["quat"])==row["top_level"]["quaternion"],i)
  if all("quaternion" in row[route] for route in ("top_level","explicit_parameter")):checks.check("top_level_equals_explicit",row["top_level"]==row["explicit_parameter"],i)
  checks.check("inputs_unchanged",before==json.dumps([spec,top_spec,motion],sort_keys=True),i);rows.append(row)
 actual=Path(E.__file__).resolve()
 if actual!=(Path(args.snapshot)/REL).resolve():raise RuntimeError("Wrong bridge import")
 routes={route:{"supported":sum("quaternion" in r[route] for r in rows),"unsupported":sum("error" in r[route] for r in rows),"max_angle_error_rad":max((r[route].get("angle_error_rad",0.) for r in rows),default=0.),"max_quaternion_component_error":max((r[route].get("max_component_error",0.) for r in rows),default=0.),"numeric_failures":sum(r[route].get("angle_error_rad",0.)>1e-11 or r[route].get("max_component_error",0.)>5e-12 for r in rows)} for route in ("top_level","explicit_parameter")}
 out={"variant":args.variant,"case_count":len(rows),"routes":routes,"correctness":checks.result(),"eval_source":str(actual),"eval_lf_sha256":lfsha(actual.read_bytes()),"environment":{"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"mpmath":mp.__version__,"dps":80,"seed":SEED,"pythonhashseed":os.environ.get("PYTHONHASHSEED")},"rows":rows};write_json(Path(args.output),out);print(json.dumps({k:v for k,v in out.items() if k in ("variant","case_count","routes","correctness")},ensure_ascii=False),flush=True)

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo",type=Path,default=Path.cwd());parser.add_argument("--output",type=Path,required=True);parser.add_argument("--baseline",default=BASE);parser.add_argument("--math-ref",default=MATH);parser.add_argument("--top-ref",default=TOP);parser.add_argument("--combined-ref",default=COMBINED);parser.add_argument("--expected-combined-sha",default=EXPECTED);parser.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);parser.add_argument("--snapshot",help=argparse.SUPPRESS);parser.add_argument("--variant",help=argparse.SUPPRESS);args=parser.parse_args()
 if args.worker:worker(args);return 0
 repo=args.repo.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 if lfsha((repo/REL).read_bytes())!=args.expected_combined_sha:raise RuntimeError("Live combined source changed")
 manifest={"repository":str(repo),"head":git(repo,"rev-parse","HEAD"),"runner_lf_sha256":lfsha(Path(__file__).read_bytes()),"variants":{}}
 for variant,ref in (("baseline",args.baseline),("math_only",args.math_ref),("top_level_only",args.top_ref),("combined",args.combined_ref)):
  commit=git(repo,"rev-parse",ref);data=git(repo,"archive","--format=zip",commit,"bridges/blender/wm_bridge",binary=True);snapshot=out/"snapshots"/variant;snapshot.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(io.BytesIO(data)) as archive:
   if any(not (snapshot/item.filename).resolve().is_relative_to(snapshot.resolve()) for item in archive.infolist()):raise RuntimeError("Unsafe archive path")
   archive.extractall(snapshot)
  manifest["variants"][variant]={"commit":commit,"snapshot":str(snapshot),"archive_sha256":sha(data),"eval_lf_sha256":lfsha((snapshot/REL).read_bytes())}
 if manifest["variants"]["combined"]["eval_lf_sha256"]!=args.expected_combined_sha:raise RuntimeError("Archived combined source differs")
 write_json(out/"source_manifest.json",manifest)
 def execute(variant):
  output=out/(variant+"_raw.json");env=os.environ.copy();env.update(PYTHONHASHSEED=str(SEED),PYTHONDONTWRITEBYTECODE="1");cmd=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--variant",variant,"--snapshot",manifest["variants"][variant]["snapshot"],"--output",str(output)];result=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",errors="replace");(out/(variant+".stdout.log")).write_text(result.stdout,encoding="utf-8");(out/(variant+".stderr.log")).write_text(result.stderr,encoding="utf-8")
  if result.returncode:raise RuntimeError(variant+" failed: "+result.stderr)
  return variant,json.loads(output.read_text(encoding="utf-8"))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=dict(pool.map(execute,manifest["variants"]))
 summary={v:{k:value for k,value in r.items() if k not in ("rows","environment")} for v,r in results.items()};summary["sources"]=manifest;write_json(out/"comparison.json",summary);lines=["# Combined math and top-level motions: independent 80-digit public oracle","","Each variant is an exact separate Git archive. No source was changed. The reference is high-precision sn(K-u,m), with actual binary64 elapsed=frame/fps, separate input-conversion terms, and direct quaternion construction.","","| Variant | Cases | Top supported | Top numeric failures | Explicit supported | Explicit numeric failures |","|---|---:|---:|---:|---:|---:|"]
 for variant,r in results.items():lines.append("| %s | %d | %d | %d | %d | %d |"%(variant,r["case_count"],r["routes"]["top_level"]["supported"],r["routes"]["top_level"]["numeric_failures"],r["routes"]["explicit_parameter"]["supported"],r["routes"]["explicit_parameter"]["numeric_failures"]))
 combined=results["combined"];lines += ["","Combined correctness: "+json.dumps(combined["correctness"],ensure_ascii=False),"","Combined route maxima: "+json.dumps(combined["routes"],ensure_ascii=False),"","The fixed grid includes +/-5, +/-120, +/-179.99999 degrees and +/-nextafter(pi,0), both time signs, all x/y/z axes and multiple periods, plus 64 seeded near-separatrix points. Checks include input immutability, repeated purity, time symmetry, origin and normalized quaternions. Explicit-parameter and top-level results are compared directly. This covers pure pose generation, not a live Blender render or timing claim."]
 (out/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n");print(json.dumps({"report":str(out/"report.md"),"combined_assertions":combined["correctness"]["assertions"],"combined_failures":combined["correctness"]["failed_assertions"],"combined_routes":combined["routes"]},ensure_ascii=False),flush=True);return int(bool(combined["correctness"]["failed_assertions"]))
if __name__=="__main__":raise SystemExit(main())
