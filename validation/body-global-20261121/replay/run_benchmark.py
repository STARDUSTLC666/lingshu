"""Replay an unchanged benchmark from an explicitly supplied checkout."""
from pathlib import Path
import argparse,hashlib,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--repo",type=Path,required=True)
p.add_argument("--kind",choices=("world","world-inference"),required=True)
p.add_argument("--output",type=Path,required=True)
p.add_argument("--samples",type=int,default=None)
a=p.parse_args()
name="bench_world.py" if a.kind=="world" else "bench_world_inference.py"
expected=(Path(__file__).parent/"bench"/name).read_bytes().replace(b"\r\n",b"\n")
actual=(a.repo/"bench"/name).read_bytes().replace(b"\r\n",b"\n")
if hashlib.sha256(actual).digest()!=hashlib.sha256(expected).digest():
 raise SystemExit("benchmark source differs from the published snapshot")
cmd=[sys.executable,"-B","-X","utf8",str((a.repo/"bench"/name).resolve()),"--output",str(a.output.resolve())]
if a.samples is not None:cmd += ["--seeds" if a.kind=="world" else "--repeats",str(a.samples)]
raise SystemExit(subprocess.call(cmd,cwd=a.repo))
