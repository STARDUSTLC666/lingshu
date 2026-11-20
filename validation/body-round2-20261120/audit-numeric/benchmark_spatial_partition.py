"""Real public-path A/B timings and traced allocations, with stable inputs."""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import tracemalloc

OUT=Path(__file__).parent
BASE=Path(r'[workspace]/lingshu/work\lingshu-audit-core-20261120')
FIXED=Path(r'[workspace]/lingshu/work\lingshu-body-spatial-partition-20261120')


def child(repo):
    sys.path.insert(0, str(repo))
    import numpy as np
    from lingshu.nn.hex_hier import HexHierNet
    from lingshu.nn.hex_text import spatial_detect
    rng=np.random.default_rng(20261120)
    net=HexHierNet(seed=7)
    records=[]
    for label, shape, iterations in [('divisible_2x18x18',(2,18,18,3),40),
                                     ('uneven_2x18x16',(2,18,16,3),40),
                                     ('uneven_2x65x67',(2,65,67,3),15)]:
        lat=rng.normal(size=shape)
        before=lat.copy()
        weights=net.get_vec()
        def call():
            return spatial_detect(net,lat)
        expected=call()
        for _ in range(3):
            for _ in range(iterations): call()
        timings=[]
        for _ in range(9):
            start=time.perf_counter_ns()
            for _ in range(iterations): call()
            timings.append((time.perf_counter_ns()-start)/1e6/iterations)
        memory=[]
        for _ in range(3):
            gc.collect()
            tracemalloc.start()
            result=call()
            _,peak=tracemalloc.get_traced_memory()
            tracemalloc.stop()
            assert result==expected
            memory.append(peak)
        assert np.array_equal(lat,before), 'detector changed input'
        assert np.array_equal(net.get_vec(),weights), 'detector changed weights'
        payload=json.dumps(expected,sort_keys=True,separators=(',',':')).encode()
        records.append({'case':label,'shape':shape,'seed':20261120,'iterations_per_sample':iterations,
                        'warmup_samples':3,'retained_samples':9,'milliseconds':timings,
                        'median_ms':statistics.median(timings),'traced_peak_bytes':memory,
                        'median_traced_peak_bytes':statistics.median(memory),
                        'output_sha256':hashlib.sha256(payload).hexdigest(),
                        'input_sha256':hashlib.sha256(lat.tobytes()).hexdigest(),
                        'weights_sha256':hashlib.sha256(weights.tobytes()).hexdigest(),
                        'output':expected})
    raw=(repo/'lingshu/nn/hex_text.py').read_bytes().replace(b'\r\n',b'\n')
    return {'python':sys.version,'numpy':np.__version__,'repository':str(repo),
            'source_lf_sha256':hashlib.sha256(raw).hexdigest(),
            'thread_limits':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            'records':records}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--child')
    args=parser.parse_args()
    if args.child:
        print(json.dumps(child(Path(args.child)),ensure_ascii=False,indent=2))
        return 0
    results={}
    for label,repo in [('baseline',BASE),('fixed',FIXED)]:
        env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
             'PYTHONDONTWRITEBYTECODE':'1'}
        run=subprocess.run([sys.executable,'-X','utf8','-B',str(Path(__file__)),'--child',str(repo)],
                           cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/f'benchmark-{label}.json').write_text(run.stdout,encoding='utf-8')
        (OUT/f'benchmark-{label}.stderr.log').write_text(run.stderr,encoding='utf-8')
        if run.returncode:
            raise RuntimeError(f'{label}: rc={run.returncode}: {run.stderr}')
        results[label]=json.loads(run.stdout)
    rows=[]
    for a,b in zip(results['baseline']['records'],results['fixed']['records']):
        assert a['input_sha256']==b['input_sha256'] and a['weights_sha256']==b['weights_sha256']
        if a['case'].startswith('divisible'):
            assert a['output_sha256']==b['output_sha256'], 'divisible-grid behavior changed'
        rows.append({'case':a['case'],'baseline_ms':a['median_ms'],'fixed_ms':b['median_ms'],
                     'fixed_over_baseline_time':b['median_ms']/a['median_ms'],
                     'baseline_peak_bytes':a['median_traced_peak_bytes'],
                     'fixed_peak_bytes':b['median_traced_peak_bytes'],
                     'fixed_over_baseline_peak':b['median_traced_peak_bytes']/a['median_traced_peak_bytes'],
                     'output_equal':a['output_sha256']==b['output_sha256']})
    result={'results':rows,'caveat':'Shared Windows host; descriptive timings, not statistical significance or isolated CPU guarantees. Uneven grids now classify the full input rather than a truncated subset.'}
    (OUT/'benchmark-comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
