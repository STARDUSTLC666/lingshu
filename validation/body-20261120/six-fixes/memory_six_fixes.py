#!/usr/bin/env python3
"""Portable separate allocation/process-memory probes for six exact-commit fixes.

Run after or independently of benchmark_six_fixes.py with --repo and --output.
Requires sibling benchmark_six_fixes.py, NumPy and Pillow. tracemalloc is the
cross-platform metric; process RSS/private commit availability is platform
dependent and explicitly recorded. Probes never supply latency conclusions.
"""
from __future__ import annotations
import argparse,ctypes,gc,hashlib,importlib,json,os,statistics,subprocess,sys,tracemalloc
from pathlib import Path
import benchmark_six_fixes as B
ROOT=None

class Counters(ctypes.Structure):
 _fields_=[("cb",ctypes.c_uint32),("PageFaultCount",ctypes.c_uint32),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]

def process_memory():
 if os.name=="nt":
  counter=Counters();counter.cb=ctypes.sizeof(Counters)
  function=ctypes.windll.psapi.GetProcessMemoryInfo;function.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_uint32];function.restype=ctypes.c_int
  if not function(ctypes.c_void_p(-1),ctypes.byref(counter),counter.cb):raise ctypes.WinError()
  return {"working_set_bytes":int(counter.WorkingSetSize),"process_peak_working_set_bytes":int(counter.PeakWorkingSetSize),"private_commit_bytes":int(counter.PagefileUsage),"source":"Windows GetProcessMemoryInfo"}
 if sys.platform.startswith("linux"):
  data={}
  for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
   key,_,value=line.partition(":")
   if key in ("VmRSS","VmHWM","VmSize"):data[key]=int(value.strip().split()[0])*1024
  return {"working_set_bytes":data.get("VmRSS"),"process_peak_working_set_bytes":data.get("VmHWM"),"private_commit_bytes":None,"virtual_size_bytes":data.get("VmSize"),"source":"Linux /proc/self/status; private commit unavailable"}
 try:
  import resource
  peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
  return {"working_set_bytes":None,"process_peak_working_set_bytes":int(peak if sys.platform=="darwin" else peak*1024),"private_commit_bytes":None,"source":"resource.getrusage; current RSS/private commit unavailable"}
 except (ImportError,AttributeError):
  return {"working_set_bytes":None,"process_peak_working_set_bytes":None,"private_commit_bytes":None,"source":"Unavailable on this platform; tracemalloc remains active"}

def measure(label,fn):
 gc.collect();before=process_memory();tracemalloc.start();before_python=tracemalloc.get_traced_memory()[0]
 try:
  result=fn();current,peak=tracemalloc.get_traced_memory();after=process_memory()
 finally:tracemalloc.stop()
 return {"label":label,"python_current_delta_bytes":current-before_python,"python_peak_new_bytes":peak-before_python,"process_before":before,"process_after":after,"result_type":type(result).__name__}

def probes(name):
 import numpy as np
 rng=np.random.default_rng(B.SEED)
 if name=="motion_groups":
  from lingshu.world import motion_groups as M
  history=[{"tick":t,"entities":{"member%d|id"%j:[j*2+t,1,0] for j in range(96)}} for t in range(8)]
  return [measure("detect_8_frames_96_entities",lambda:M.detect_motion_groups(history))]
 if name=="lineart_alpha":
  from PIL import Image
  from lingshu.vision import lineart as L
  data=rng.integers(0,256,(1536,1536,4),dtype=np.uint8);im=Image.fromarray(data,"RGBA")
  return [measure("darkline_RGBA_1536x1536",lambda:L.darkline(im))]
 if name=="obb_sat":
  from lingshu.world import physics as P
  pairs=[]
  for i in range(512):
   a={"center":(0.,0.,0.),"half":(.5,.5,.5),"rot":((1.,0.,0.),(.4,1.,0.),(.2,.3,1.))}
   b=dict(a);b["center"]=tuple(rng.uniform(-2,2,3));pairs.append((a,b))
  return [measure("overlap_512_skew_pairs",lambda:[P.obb_overlap(a,b) for a,b in pairs])]
 if name=="novelty_cache":
  from types import SimpleNamespace
  from lingshu.core.longterm_gate import LongTermMemoryGate
  store=B._make_store(5000);gate=LongTermMemoryGate(SimpleNamespace(store=store));out=[]
  try:
   out.append(measure("snapshot_cold_5000_nodes",gate._known_snapshot))
   out.append(measure("snapshot_warm_5000_nodes",gate._known_snapshot))
   store.conn.execute("UPDATE nodes SET content='改写内容 新状态5000' WHERE id='bench_0'");store.conn.commit();B._add_node(store,5000)
   out.append(measure("snapshot_after_mixed_5000_nodes",gate._known_snapshot))
   return out
  finally:store.conn.close()
 if name=="hexgrid_nearest":
  from lingshu.nn.hex_cnn import HexGrid
  grid=HexGrid(100,100,1.,mode="odd_r_offset",origin=(-2.7,4.9));points=[tuple(x) for x in rng.uniform(-100,100,(50000,2))]
  return [measure("nearest_odd_r_50000_points",lambda:[grid.pixel_to_cell(x,y) for x,y in points])]
 if name=="skill_limit":
  from lingshu.core.core import LayeredStore
  store=LayeredStore(":memory:")
  try:
   for i in range(5000):store.add_skill("needle skill %04d"%i,"needle benchmark description %04d"%i,"procedure %04d"%i,confidence=.1+.8*i/5000)
   return [measure("search_5000_skills_limit_-1",lambda:store.search_skills("needle",-1))]
  finally:store.conn.close()
 raise ValueError(name)

def worker(args):
 sys.path.insert(0,str(Path(args.snapshot).resolve()));out={"suite":args.suite,"variant":args.variant,"commit":args.commit,"snapshot":args.snapshot,"environment":B.environment(),"repetitions":[]}
 for i in range(3):out["repetitions"].append(probes(args.suite))
 out["summary"]=[]
 for i,first in enumerate(out["repetitions"][0]):
  samples=[r[i] for r in out["repetitions"]]
  out["summary"].append({"label":first["label"],"python_peak_new_bytes_samples":[s["python_peak_new_bytes"] for s in samples],"python_peak_new_bytes_median":statistics.median(s["python_peak_new_bytes"] for s in samples),"python_current_delta_bytes_samples":[s["python_current_delta_bytes"] for s in samples],"working_set_after_bytes_samples":[s["process_after"]["working_set_bytes"] for s in samples]})
 module=importlib.import_module(B.SUITES[args.suite][1][:-3].replace("/","."));source=Path(module.__file__).resolve();expected=(Path(args.snapshot)/B.SUITES[args.suite][1]).resolve()
 if source!=expected:raise RuntimeError("Imported wrong source: "+str(source))
 out["actual_source"]=str(source);out["source_lf_sha256"]=hashlib.sha256(source.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
 B.write_json(Path(args.output),out);print(json.dumps({"suite":args.suite,"variant":args.variant,"summaries":out["summary"]},ensure_ascii=False),flush=True)

def main():
 global ROOT
 p=argparse.ArgumentParser(description="Separate three-repeat allocation/process-memory probes for the six exact-commit fixes.")
 p.add_argument("--repo",type=Path,default=Path.cwd(),help="Local public Git clone; default cwd")
 p.add_argument("--output",type=Path,required=True,help="Output directory (internal worker result file)")
 p.add_argument("--only",help="Comma-separated suite names; omitted means all six")
 p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);p.add_argument("--suite",help=argparse.SUPPRESS);p.add_argument("--variant",help=argparse.SUPPRESS);p.add_argument("--commit",help=argparse.SUPPRESS);p.add_argument("--snapshot",help=argparse.SUPPRESS);args=p.parse_args()
 if args.worker:worker(args);return 0
 if args.only and any(name not in B.SUITES for name in args.only.split(",")):p.error("Unknown suite in --only")
 ROOT=args.output.resolve();ROOT.mkdir(parents=True,exist_ok=True);B.ROOT=ROOT;B.REPO=args.repo.resolve()
 raw=ROOT/"memory_raw";raw.mkdir(exist_ok=True);combined={"description":"Separate allocation probes: three repetitions, no latency conclusions from traced execution.","limitations":["tracemalloc measures traced Python/NumPy allocations and can omit native Pillow/SQLite buffers.","Process working set includes imports, allocator retention and fixtures; peak working set is lifetime-wide. Windows uses GetProcessMemoryInfo, Linux uses /proc/self/status, other platforms may expose only resource peak RSS or no process metric. Null denotes an unavailable metric.","Fixture construction excluded from traced allocation interval; result retained while sampling.","Memory probes run separately from all latency samples."],"suites":{},"runner_lf_sha256":hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n",b"\n")).hexdigest()}
 for name in (list(B.SUITES) if not args.only else args.only.split(",")):
  commit=B.SUITES[name][0]
  combined["suites"][name]={}
  for variant,sha in (("baseline",B.BASE),("fixed",commit)):
   dest,_=B.snapshot(sha);output=raw/(name+"_"+variant+".json");env=os.environ.copy();env.update(PYTHONHASHSEED=str(B.SEED),PYTHONDONTWRITEBYTECODE="1")
   cmd=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--suite",name,"--variant",variant,"--commit",sha,"--snapshot",str(dest),"--output",str(output)]
   result=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",errors="replace")
   (raw/(name+"_"+variant+".stdout.log")).write_text(result.stdout,encoding="utf-8");(raw/(name+"_"+variant+".stderr.log")).write_text(result.stderr,encoding="utf-8")
   if result.returncode:raise RuntimeError("Memory probe failed: "+name+" "+variant+" "+result.stderr)
   combined["suites"][name][variant]=json.loads(output.read_text(encoding="utf-8"));print("DONE memory "+name+" "+variant,flush=True)
 for name in B.SUITES:
  if name in combined["suites"]:continue
  if all((raw/(name+"_"+variant+".json")).exists() for variant in ("baseline","fixed")):
   combined["suites"][name]={variant:json.loads((raw/(name+"_"+variant+".json")).read_text(encoding="utf-8")) for variant in ("baseline","fixed")}
 B.write_json(ROOT/"memory_comparison.json",combined)
 lines=["# Allocation and process-memory probes","","Three repetitions per variant, independently from latency benchmarks.","","| Workload | Baseline traced peak median bytes | Fixed traced peak median bytes | Fixed / baseline |","|---|---:|---:|---:|"]
 for name,variants in combined["suites"].items():
  for b,f in zip(variants["baseline"]["summary"],variants["fixed"]["summary"]):
   lines.append("| %s | %d | %d | %.3fx |"%(b["label"],b["python_peak_new_bytes_median"],f["python_peak_new_bytes_median"],f["python_peak_new_bytes_median"]/max(1,b["python_peak_new_bytes_median"])))
 lines += ["","Scope and interpretation:",""]+["- "+s for s in combined["limitations"]]
 (ROOT/"memory_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n");print("MEMORY_REPORT "+str(ROOT/"memory_report.md"),flush=True);return 0
if __name__=="__main__":raise SystemExit(main())
