"""Read-only Cartesian-center oracle for HexGrid's public neighbor method."""
from __future__ import annotations
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT=Path(r'<repo>')
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
import numpy as np
from lingshu.nn.hex_cnn import HexGrid,image_to_grid


def center(q,r,size,origin,mode):
    """Cartesian point cloud generated from the documented lattice geometry."""
    if mode=='odd_r_offset':
        return (math.sqrt(3)*size*(q+(r%2)/2)+origin[0],1.5*size*r+origin[1])
    return (math.sqrt(3)*size*(q+r/2),1.5*size*r)


def oracle(q,r,size,origin,mode):
    point=center(q,r,size,origin,mode)
    cloud=[]
    for qq,rr in itertools.product(range(q-3,q+4),range(r-3,r+4)):
        if (qq,rr)==(q,r): continue
        xy=center(qq,rr,size,origin,mode)
        cloud.append((math.dist(point,xy),qq,rr))
    cloud.sort()
    assert all(math.isclose(d,math.sqrt(3)*size,rel_tol=1e-10,abs_tol=1e-10)
               for d,_,_ in cloud[:6])
    assert cloud[6][0]>2.5*size  # independently isolate exactly six closest centers
    return {(qq,rr) for _,qq,rr in cloud[:6]}


def measure(grid,q,r):
    expected=oracle(q,r,grid.size,grid.origin,grid.mode)
    actual=set(grid.neighbors(q,r))
    point=grid.center_px(q,r)
    return {'cell':[q,r],'mode':grid.mode,'size':grid.size,'origin':grid.origin,
            'actual':sorted(actual),'nearest_six':sorted(expected),
            'missing':sorted(expected-actual),'spurious':sorted(actual-expected),
            'distance_over_size':sorted(math.dist(point,grid.center_px(*c))/grid.size for c in actual),
            'ok':actual==expected}


def main():
    status=subprocess.run(['git','status','--porcelain=v1'],cwd=ROOT,capture_output=True,
                          text=True,encoding='utf-8',check=True).stdout
    assert not status
    report={'head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,
                                 text=True,encoding='utf-8',check=True).stdout.strip(),
            'source_lf_sha256':hashlib.sha256((ROOT/'lingshu/nn/hex_cnn.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
            'seed':None,'oracle':'exhaustive Cartesian center point cloud; no HEX_DIRS or hex_conv used'}
    cases=[]
    for mode in ('axial','odd_r_offset'):
        origins=[(0.,0.)] if mode=='axial' else [(0.,0.),(-9.3,13.75),(1024.,-2048.)]
        for size,origin,q,r in itertools.product((.25,1.,2.5,10.),origins,range(-4,5),range(-4,5)):
            cases.append(measure(HexGrid(20,20,size,mode=mode,origin=origin),q,r))
    report['controls']={mode:{'cases':sum(c['mode']==mode for c in cases),
                              'failures':sum(c['mode']==mode and not c['ok'] for c in cases)}
                        for mode in ('axial','odd_r_offset')}
    report['representative_rows']=[next(c for c in cases if c['mode']==mode and c['size']==1 and c['origin']==(0.,0.) and c['cell']==[3,r])
                                    for mode in ('axial','odd_r_offset') for r in (2,3)]
    public=[]
    for shape,cols in (((64,64),8),((48,96),16),((96,48),12)):
        image=np.zeros((*shape,3),dtype=np.uint8)
        feature,grid=image_to_grid(image,cells_across=cols)
        tested=[measure(grid,q,r) for q in range(1,grid.W-1) for r in range(1,grid.H-1)]
        public.append({'image_shape':shape,'cells_across':cols,'returned_mode':grid.mode,
                       'feature_shape':feature.shape,'interior_cells':len(tested),
                       'failures':sum(not c['ok'] for c in tested),'example':tested[0]})
    report['public_image_to_grid']=public
    # Recorded only as an excluded contract question: axial's documentation
    # fixes its origin at zero, so a nonzero argument is not a new bug claim.
    axial=HexGrid(8,8,1.,origin=(10.,20.))
    p=axial.center_px(3,3)
    report['excluded_axial_origin']={'input_origin':axial.origin,'cell':[3,3],
                                     'center':p,'inverse':axial.pixel_to_cell(*p),
                                     'disposition':'exclude from claim: axial docs explicitly state origin (0,0); nonzero-origin support needs a contract decision'}
    assert report['controls']['axial']['failures']==0
    assert report['controls']['odd_r_offset']['failures']==0
    assert all(x['failures']==0 for x in public)
    assert subprocess.run(['git','status','--porcelain=v1'],cwd=ROOT,capture_output=True,
                          text=True,encoding='utf-8',check=True).stdout==status
    (OUT/'hexgrid-neighbor-oracle-fixed.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__': main()
