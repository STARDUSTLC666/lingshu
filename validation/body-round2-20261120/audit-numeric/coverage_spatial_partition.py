"""Run every positive-size lattice in 1..20 through the public crop protocol."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

repo=Path(sys.argv[1])
sys.path.insert(0,str(repo))
import numpy as np
from lingshu.nn.hex_text import spatial_detect


class Recorder:
    def __init__(self): self.seen=[]
    def l1(self,lat): return lat,lat.mean(axis=(1,2))
    def l2_features(self,lat):
        if 0 in lat.shape[1:3]: raise ValueError('classified empty region')
        self.seen.extend(lat.ravel().astype(int).tolist())
        return np.ones((1,1)),np.ones((1,3))
    def l3_logits(self,sf,cf): return np.arange(9)[None]


records=[]
for rows in range(1,21):
    for cols in range(1,21):
        ids=np.arange(1,rows*cols+1).reshape(1,rows,cols,1)
        net=Recorder()
        error=None
        try: spatial_detect(net,ids,exist_mult=0)
        except Exception as exc: error=f'{type(exc).__name__}: {exc}'
        missing=sorted(set(ids.ravel())-set(net.seen))
        records.append({'rows':rows,'cols':cols,'missing_count':len(missing),
                        'repeat_count':len(net.seen)-len(set(net.seen)),'error':error})
summary={'source_lf_sha256':hashlib.sha256((repo/'lingshu/nn/hex_text.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
         'cases':len(records),'input_cells':sum(r['rows']*r['cols'] for r in records),
         'perfect_cases':sum(not r['missing_count'] and not r['repeat_count'] and not r['error'] for r in records),
         'error_cases':sum(r['error'] is not None for r in records),
         'missing_cells':sum(r['missing_count'] for r in records),
         'repeated_cells':sum(r['repeat_count'] for r in records),'records':records}
print(json.dumps(summary,indent=2))
