#!/usr/bin/env python3
"""Python 3.12+ public bridge quaternion checks against an 80-digit oracle.

Requires only mpmath beyond the standard library. Run with --repo LOCAL_CLONE
--output DIRECTORY. The baseline is archived at --baseline (default d74848f).
The fixed dependency package is archived at HEAD and overlaid with the current
working eval.py. No repository source is modified, no dependency installed and
no network request performed. All writes stay under --output.

The oracle uses DLMF 22.19.2's rest-release pendulum solution, independently
evaluated as 2 asin(k sn(K-u, m)), m=k*k, at 80 decimal digits. K-u and K+u are
equivalent by time symmetry. Each binary64 declaration and computed elapsed
time is promoted exactly before the oracle product. Desired-time -> fps ->
actual elapsed conversion and the float division/product effects are retained
separately. No body/bridge AGM or elliptic helper supplies the reference.
"""
from __future__ import annotations
import argparse,hashlib,importlib,io,json,math,os,platform,random,subprocess,sys,time,zipfile
from pathlib import Path
import mpmath as mp
DPS=80;SEED=20261120;REL=Path("bridges/blender/wm_bridge/factory/anim/eval.py")

def sha(data):return hashlib.sha256(data).hexdigest()
def lfsha(data):return sha(data.replace(b"\r\n",b"\n"))
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def git(repo,*args,binary=False):
 result=subprocess.run(["git","-C",str(repo),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 return result.stdout if binary else result.stdout.decode("utf-8","replace").strip()
def extract(data,dest):
 dest.mkdir(parents=True,exist_ok=True);root=dest.resolve()
 with zipfile.ZipFile(io.BytesIO(data)) as archive:
  if any(not (dest/item.filename).resolve().is_relative_to(root) for item in archive.infolist()):raise RuntimeError("Unsafe archive path")
  archive.extractall(dest)

def capture(repo,output,baseline,expected):
 current=(repo/REL).read_bytes()
 if expected and lfsha(current)!=expected:raise RuntimeError("Working eval.py LF SHA mismatch: "+lfsha(current))
 head=git(repo,"rev-parse","HEAD");base=git(repo,"rev-parse",baseline);snapshots={}
 for variant,commit in (("baseline",base),("fixed",head)):
  data=git(repo,"archive","--format=zip",commit,"bridges/blender/wm_bridge",binary=True);dest=output/"snapshots"/variant;extract(data,dest)
  if variant=="fixed":(dest/REL).write_bytes(current)
  snapshots[variant]={"commit":commit,"snapshot":str(dest),"archive_sha256":sha(data),"archive_bytes":len(data),"eval_lf_sha256":lfsha((dest/REL).read_bytes()),"working_eval_overlay":variant=="fixed"}
 return {"repo":str(repo),"baseline":base,"head":head,"working_eval":str(repo/REL),"fixed_eval_lf_sha256":lfsha(current),"runner_lf_sha256":lfsha(Path(__file__).read_bytes()),"snapshots":snapshots}

def full_period(theta):
 k=mp.sin(mp.mpf(theta)/2);return 4*mp.ellipk(k*k)
def ref(theta,w,t):
 k=mp.sin(mp.mpf(theta)/2);m=k*k;K=mp.ellipk(m);value=2*mp.asin(k*mp.ellipfun("sn",K-mp.mpf(w)*mp.mpf(t),m))
 if isinstance(value,mp.mpc) and abs(value.imag)>mp.mpf("1e-60"):raise RuntimeError("Nonreal reference")
 return mp.re(value)

def cases():
 amplitudes=[.1,1.,5.,30.,90.,120.,170.,179.999,math.degrees(math.pi-1e-12),math.degrees(math.nextafter(math.pi,0.))]
 for degree in amplitudes:
  for sign in (1.,-1.):
   degrees=sign*degree;theta=math.radians(degrees);p=full_period(theta)
   for w in (.25,1.,3.13):
    for fraction in (0.,.125,.25,.5,.75,1.125,3.375):
     for timesign in ((1.,) if fraction==0 else (1.,-1.)):
      desired=float(timesign*mp.mpf(fraction)*p/mp.mpf(w))
      for axis in ("x","y","z"):yield {"category":"fixed_grid","degrees":degrees,"omega0":w,"desired_time":desired,"axis":axis,"target_period_fraction":timesign*fraction}
 rng=random.Random(SEED)
 for i in range(500):
  if i<350:theta=rng.uniform(-3.1,3.1);category="seeded_random"
  else:theta=rng.choice((-1.,1.))*(math.pi-10**rng.uniform(-15.,-3.));category="seeded_near_pi"
  degrees=math.degrees(theta)
  if abs(math.radians(degrees))>=math.pi:degrees=math.copysign(math.nextafter(180.,0.),degrees)
  theta=math.radians(degrees);w=10**rng.uniform(-2.,1.);fraction=rng.uniform(-100.,100.);desired=float(mp.mpf(fraction)*full_period(theta)/mp.mpf(w))
  yield {"category":category,"degrees":degrees,"omega0":w,"desired_time":desired,"axis":rng.choice(("x","y","z")),"target_period_fraction":fraction}

class Checks:
 def __init__(self):self.counts={};self.failed={}
 def check(self,label,ok,detail):
  self.counts[label]=self.counts.get(label,0)+1
  if not ok:
   record=self.failed.setdefault(label,{"count":0,"examples":[]});record["count"]+=1
   if len(record["examples"])<10:record["examples"].append(detail)
 def result(self):return {"assertions":sum(self.counts.values()),"failed_assertions":sum(x["count"] for x in self.failed.values()),"checks":self.counts,"failures":self.failed}

def worker(args):
 mp.mp.dps=DPS;sys.path.insert(0,str(Path(args.snapshot)/"bridges/blender"));E=importlib.import_module("wm_bridge.factory.anim.eval");checks=Checks();rows=[];reference_cache={}
 for i,case in enumerate(cases()):
  desired=case["desired_time"];frame=0 if desired==0 else (1 if desired>0 else -1);fps=120. if desired==0 else 1/abs(desired);elapsed=frame/fps;theta=math.radians(case["degrees"]);w=case["omega0"];key=(theta,w,elapsed,desired)
  if key not in reference_cache:
   angle=ref(theta,w,elapsed);desired_angle=ref(theta,w,desired);reference_cache[key]=(angle,desired_angle)
  expected,desired_angle=reference_cache[key];axis=case["axis"];component={"x":1,"y":2,"z":3}[axis]
  qref=[mp.cos(expected/2),mp.mpf(0),mp.mpf(0),mp.mpf(0)];qref[component]=mp.sin(expected/2)
  spec={"schema":"wmfactory.spec/1","name":"pendulum_oracle","scene":{"fps":fps},"links":[{"name":"bob","anchor":[0,0,0],"parts":[]}],"joints":[]}
  motion={"link":"bob","kind":"pendulum","axis":axis,"exact":True,"theta0_deg":case["degrees"],"omega0":w,"zeta":0.};before=json.dumps([spec,motion],sort_keys=True)
  row=dict(case,index=i,frame=frame,fps=fps,elapsed_binary64=elapsed,declared_theta0_rad_binary64=theta,reference_angle_rad_85_digits=mp.nstr(expected,85),reference_quaternion_85_digits=[mp.nstr(x,85) for x in qref])
  row["input_conversion"]={"desired_to_actual_time_error_s":float(abs(mp.mpf(elapsed)-mp.mpf(desired))),"division_rounding_error_s":float(abs(mp.mpf(elapsed)-mp.mpf(frame)/mp.mpf(fps))),"omega_time_product_rounding_error_u":float(abs(mp.mpf(w*elapsed)-mp.mpf(w)*mp.mpf(elapsed))),"reference_angle_shift_from_time_conversion_rad":float(abs(expected-desired_angle)),"degree_to_radian_error_rad":float(abs(mp.mpf(theta)-mp.mpf(case["degrees"])*mp.pi/180))}
  try:
   result=E.eval_at(spec,frame,motions=[motion])["bob"];q=list(result["quat"]);position=list(result["pos"]);actual=2*math.atan2(q[component],q[0]);component_error=max(float(abs(mp.mpf(a)-b)) for a,b in zip(q,qref));angle_error=float(abs(mp.mpf(actual)-expected))
   row.update(quaternion=q,position=position,recovered_angle_rad=actual,angle_abs_error_rad=angle_error,max_quaternion_component_error=component_error)
   checks.check("public_call_supported",True,i);checks.check("independent_angle_error_le_1e_11",angle_error<=1e-11,{"case":i,"error_rad":angle_error});checks.check("independent_quaternion_error_le_5e_12",component_error<=5e-12,{"case":i,"error":component_error});checks.check("unit_quaternion",abs(sum(x*x for x in q)-1)<=5e-15,i);checks.check("canonical_w_nonnegative",q[0]>=0.,i);checks.check("other_axis_components_zero",all(abs(q[j])<=1e-15 for j in (1,2,3) if j!=component),i);checks.check("origin_position_preserved",position==[0.,0.,0.],i)
   again=E.eval_at(spec,frame,motions=[motion])["bob"];checks.check("repeat_pure",list(again["quat"])==q and list(again["pos"])==position,i)
   reverse=E.eval_at(spec,-frame,motions=[motion])["bob"];checks.check("time_even",list(reverse["quat"])==q,i)
   opposite=dict(motion,theta0_deg=-motion["theta0_deg"]);neg=E.eval_at(spec,frame,motions=[opposite])["bob"];neg_expected=list(q);neg_expected[component]*=-1;checks.check("initial_angle_odd",max(abs(a-b) for a,b in zip(neg["quat"],neg_expected))<=1e-15,i)
   checks.check("inputs_unchanged",before==json.dumps([spec,motion],sort_keys=True),i)
  except Exception as e:
   row.update(error_type=type(e).__name__,error=str(e));checks.check("public_call_supported",False,{"case":i,"error_type":type(e).__name__,"error":str(e)})
  rows.append(row)
 dependencies=[]
 for name,module in sorted(sys.modules.items()):
  path=getattr(module,"__file__",None)
  if name.startswith("wm_bridge") and path and str(path).endswith(".py"):
   p=Path(path).resolve();dependencies.append({"module":name,"path":str(p),"lf_sha256":lfsha(p.read_bytes())})
 actual_source=Path(E.__file__).resolve();expected_source=(Path(args.snapshot)/REL).resolve()
 if actual_source!=expected_source:raise RuntimeError("Wrong bridge source imported")
 result={"variant":args.variant,"snapshot":args.snapshot,"actual_eval_source":str(actual_source),"eval_lf_sha256":lfsha(actual_source.read_bytes()),"environment":{"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"processor":platform.processor(),"cpu_count":os.cpu_count(),"mpmath":mp.__version__,"dps":mp.mp.dps,"seed":SEED,"pythonhashseed":os.environ.get("PYTHONHASHSEED"),"wall_clock_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())},"dependencies":dependencies,"case_count":len(rows),"correctness":checks.result(),"max_angle_error_rad":max((r.get("angle_abs_error_rad",0.) for r in rows),default=0.),"max_quaternion_component_error":max((r.get("max_quaternion_component_error",0.) for r in rows),default=0.),"max_reference_angle_shift_from_time_conversion_rad":max(r["input_conversion"]["reference_angle_shift_from_time_conversion_rad"] for r in rows),"rows":rows}
 write_json(Path(args.output),result);print(json.dumps({k:v for k,v in result.items() if k in ("variant","case_count","correctness","max_angle_error_rad","max_quaternion_component_error","max_reference_angle_shift_from_time_conversion_rad")},ensure_ascii=False),flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter);p.add_argument("--repo",type=Path,default=Path.cwd());p.add_argument("--output",type=Path,required=True);p.add_argument("--baseline",default="d74848f");p.add_argument("--expected-fixed-sha");p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);p.add_argument("--variant",help=argparse.SUPPRESS);p.add_argument("--snapshot",help=argparse.SUPPRESS);args=p.parse_args()
 if args.worker:worker(args);return 0
 mp.mp.dps=DPS;repo=args.repo.resolve();output=args.output.resolve();output.mkdir(parents=True,exist_ok=True);manifest=capture(repo,output,args.baseline,args.expected_fixed_sha);write_json(output/"source_manifest.json",manifest);results={};env=os.environ.copy();env.update(PYTHONHASHSEED=str(SEED),PYTHONDONTWRITEBYTECODE="1")
 for variant in ("baseline","fixed"):
  target=output/(variant+"_raw.json");cmd=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--variant",variant,"--snapshot",manifest["snapshots"][variant]["snapshot"],"--output",str(target)];result=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",errors="replace");(output/(variant+".stdout.log")).write_text(result.stdout,encoding="utf-8");(output/(variant+".stderr.log")).write_text(result.stderr,encoding="utf-8")
  if result.returncode:raise RuntimeError("Bridge worker failed: "+variant+" "+result.stderr)
  results[variant]=json.loads(target.read_text(encoding="utf-8"));print(result.stdout.strip(),flush=True)
 summary={variant:{key:value for key,value in record.items() if key not in ("rows","dependencies","environment")} for variant,record in results.items()};summary["sources"]=manifest;write_json(output/"comparison.json",summary)
 fixed,base=results["fixed"],results["baseline"];lines=["# Independent public bridge quaternion oracle","","Fixed eval.py LF SHA-256: "+fixed["eval_lf_sha256"],"","Reference: mpmath %s, 80 decimal digits, independent sn(K-u,m), with theta promoted from the declared binary64 degree-to-radian conversion. Only the public eval_at(spec, frame, motions=[...]) API supplies actual poses."%mp.__version__,"","- Fixed: %d cases, %d assertions, %d failures."%(fixed["case_count"],fixed["correctness"]["assertions"],fixed["correctness"]["failed_assertions"]),"- Baseline: %d cases, %d assertions, %d failures (unsupported calls included)."%(base["case_count"],base["correctness"]["assertions"],base["correctness"]["failed_assertions"]),"- Fixed maximum angle error: %.9g rad."%fixed["max_angle_error_rad"],"- Fixed maximum quaternion component error: %.9g."%fixed["max_quaternion_component_error"],"- Maximum reference-angle shift from desired-time to actual frame/fps conversion: %.9g rad (recorded separately from solver error)."%fixed["max_reference_angle_shift_from_time_conversion_rad"],"","Coverage: 2,340 fixed-grid calls across all three axes; positive/negative initial angle and time; small through nextafter-pi initial amplitude; 500 extra seeded cases (350 ordinary plus 150 log-gap near-pi samples) through 100 periods. Properties cover quaternion normalization/canonical sign/axis mapping, fixed origin, repeated purity, unchanged inputs, even time and odd initial angle.","","No Blender runtime, bpy, NumPy, Pillow, production DB, environment installation or network operation is used. Pure Python pose generation is verified; exported/Blender-rendered motion is outside this evidence. Dependency sources and exact hashes, every case, oracle and conversion term are retained in JSON. Scalar performance was measured separately by pendulum_release_accuracy.py."]
 (output/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n");print("REPORT "+str(output/"report.md"),flush=True);return int(bool(fixed["correctness"]["failed_assertions"]))
if __name__=="__main__":raise SystemExit(main())
