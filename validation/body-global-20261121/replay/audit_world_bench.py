"""Independently compare existing benchmark artifacts, without rerunning workloads."""
from pathlib import Path
import hashlib,json,statistics,subprocess,math,argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo",type=Path,required=True)
parser.add_argument("--evidence",type=Path,required=True)
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
ROOT=args.evidence.resolve()
REPO=args.repo.resolve()
BASE="23ba01eb8dfcb1a8dfdddd030cf7a2e3c078e8e9"
FINAL="0f7427549406ad125d7efc95da5ceece052e616d"
def require(ok,msg):
 if not ok:raise AssertionError(msg)
def git(*a):return subprocess.check_output(["git","-C",str(REPO),*a])
def sha(data):return hashlib.sha256(data).hexdigest()
def load(name):return json.loads((ROOT/name).read_text(encoding="utf-8-sig"))
def identified_source(revision,filename,recorded,normalized):
 raw=git("show",revision+":lingshu/world/"+filename)
 lf=raw.replace(b"\r\n",b"\n")
 candidates={"git_blob_bytes":sha(raw),"LF":sha(lf)}
 if not normalized:candidates["CRLF_checkout"]=sha(lf.replace(b"\n",b"\r\n"))
 require(recorded in candidates.values(),("source fingerprint not attributable to exact commit",revision,filename,recorded))
 return {"file":filename,"revision":revision,"sha256_recorded":recorded,
         "matching_conventions":[k for k,v in candidates.items() if v==recorded]}
sources=[]
for name in ("bench_world.py","bench_world_inference.py"):
 require(git("show",BASE+":bench/"+name)==git("show",FINAL+":bench/"+name),"benchmark program changed "+name)
world0,world1=load("world-baseline.json"),load("world-fixed.json")
inf0,inf1=load("world_inference-baseline.json"),load("world_inference-fixed.json")
for data,head in ((world0,BASE),(world1,FINAL),(inf0,BASE),(inf1,FINAL)):
 require(data["head"]==head,("result HEAD",data["head"],head))
 require(data["python"]=="3.12.10",("python",data["python"]))
 for filename,value in data["source_sha256"].items():
  sources.append(identified_source(head,filename,value,normalized="benchmark_sha256" in data))
for key in ("schema","seeds","fixed_threshold","train_ticks","learner_eval_ticks"):
 require(world0[key]==world1[key],"world config "+key)
require(world0["seeds"]==list(range(10)) and len(world0["cases"])==9,"world workload coverage")
require(world0["contracts"]==world1["contracts"],"world contract outputs changed")
world_rows=0;world_scores=0;traces=0
for case,rows in world0["cases"].items():
 after=world1["cases"][case]
 require(rows==after,("world case raw score/result rows differ",case))
 require(len(rows)==10 and [r["seed"] for r in rows]==list(range(10)),case+" seeds")
 for before,new in zip(rows,after):
  require(before["trace_sha256"]==new["trace_sha256"],case+" trajectory fingerprint")
  traces+=1
  numeric={k:v for k,v in before.items() if k not in ("seed","trace_sha256")}
  require(all(isinstance(v,(float,int)) and math.isfinite(v) for v in numeric.values()),"nonfinite score")
  world_scores+=len(numeric)
 for label,value in world0["summary"][case].items():
  recomputed=statistics.mean(row[label] for row in rows)
  require(recomputed==value==world1["summary"][case][label],("score summary",case,label))
 world_rows+=len(rows)
require(inf0["benchmark_sha256"]==inf1["benchmark_sha256"],"inference benchmark file differs")
raw=git("show",BASE+":bench/bench_world_inference.py")
require(inf0["benchmark_sha256"] in {sha(raw),sha(raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))},"inference benchmark hash not source")
require(inf0["repeats"]==inf1["repeats"]==5 and len(inf0["cases"])==len(inf1["cases"])==14,"inference coverage")
ratios=[]
for before,after in zip(inf0["cases"],inf1["cases"]):
 for key in ("model","entities","ticks","policy","history_sha256","result_sha256","relations"):
  require(before[key]==after[key],("inference semantic mismatch",key,before,after))
 for data in (before,after):
  require(len(data["seconds"])==5 and all(t>0 and math.isfinite(t) for t in data["seconds"]),"timing samples")
  require(statistics.median(data["seconds"])==data["median_seconds"],"timing median")
 ratios.append({"model":before["model"],"entities":before["entities"],"ticks":before["ticks"],
 "policy":before["policy"],"fixed_over_baseline":after["median_seconds"]/before["median_seconds"]})
world_compare=(ROOT/"world-compare.txt").read_text(encoding="utf-8-sig")
inference_compare=(ROOT/"world_inference-compare.txt").read_text(encoding="utf-8-sig")
require("World trajectories match for every case and seed." in world_compare,"comparison trajectory result")
require(inference_compare.count("same_result=True")==14 and "same_result=False" not in inference_compare,"inference printedcomparison")
report={"baseline":BASE,"fixed":FINAL,"benchmark_source_programs_unchanged":2,
 "world_scenarios":9,"seeds_each":10,"world_result_rows_equal":world_rows,
 "world_trajectory_fingerprints_match":traces,"world_numeric_scores_equal":world_scores,
 "world_summary_metric_cells_equal":sum(len(row) for row in world0["summary"].values()),
 "world_contract_outputs_equal":True,"inference_workloads_equal":14,
 "inference_history_hashes_equal":14,"inference_result_hashes_equal":14,
 "timing_samples":140,"timing_medians_recomputed":28,
 "source_fingerprints":sources,"descriptive_inference_ratios":ratios,
 "limits":"Synthetic fixed histories and shared host timings. Equal result/trajectory hashes establish compatibility for these workloads only; no statistical performance or universal quality claim.",
 "artifacts_sha256":{path.name:sha(path.read_bytes()) for path in ROOT.iterdir() if path.is_file() and path.suffix in (".json",".txt",".log")}}
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k not in ("source_fingerprints","descriptive_inference_ratios","artifacts_sha256")},ensure_ascii=False,indent=2))
