"""Small independent public-path probes sharing integrated module state."""
from __future__ import annotations
import itertools
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(r'[workspace]')
sys.path.insert(0,str(ROOT))
from lingshu.core.core import SpacetimeMemoryEngine
from lingshu.world import physics as P

results=[]
engine=SpacetimeMemoryEngine(':memory:')
try:
    engine.decay_cycle(now=time.time()-7*86400)
    for i in range(5): engine.store_skill(f'needle {i}',f'needle description {i}',f'procedure {i}')
    node=engine.add_context('fresh context created during downtime',importance=.5)
    now=time.time()+1
    engine.decay_cycle(now=now,min_confidence=0.)
    actual=engine.store.get_node(node.id).importance
    expected=.5 * .98 ** ((now-node.created_at)/60)
    assert abs(actual-expected)<1e-12,(actual,expected)
    assert len(engine.recall_skill('needle',limit=-6))==5
    assert engine.store.search_skills('needle',limit=0)==[]
    results.append({'probe':'same_engine_fresh_decay_and_old_skill_limit','actual_importance':actual,
                    'oracle_importance':expected,'negative_skill_hits':5})
finally: engine.close()

base=1_800_000_000.
samples=[]
for i in range(12):
    dt=i/8
    samples.append((base+dt,(3+5*math.cos(.2+.9*dt),4+5*math.sin(.2+.9*dt),7-.3*dt)))
model=P.fit_circular(samples,up=2)
tau=1.375
pred=P.predict_at(model,base+tau)[0]
truth=(3+5*math.cos(.2+.9*tau),4+5*math.sin(.2+.9*tau),7-.3*tau)
err=max(abs(x-y) for x,y in zip(pred,truth))
assert err<1e-9,(pred,truth)
results.append({'probe':'epoch_circular_fit','max_coordinate_error':err,'residual_rms':model['residual_rms']})

theta,velocity,omega,target=1.2,0.,2.,.37
h=target/8192
def rhs(a,b): return b,-omega*omega*math.sin(a)
for _ in range(8192):
    a,b=rhs(theta,velocity)
    c,d=rhs(theta+h*a/2,velocity+h*b/2)
    e,f=rhs(theta+h*c/2,velocity+h*d/2)
    g,j=rhs(theta+h*e,velocity+h*f)
    theta += h*(a+2*c+2*e+g)/6
    velocity += h*(b+2*d+2*f+j)/6
angle=P.pendulum_exact_angle(1.2,omega,target)
assert abs(angle-theta)<1e-11,(angle,theta)
results.append({'probe':'pendulum_release_independent_rk4','actual_angle':angle,'rk4_angle':theta,
                'absolute_error':abs(angle-theta)})

a={'center':(.5,.5,.5),'half':(.5,.5,.5),
   'rot':((-0.554749,0.360100,-0.750054),(-0.407590,-0.897262,0.169682),(-0.506776,0.320162,0.800422))}
b={'center':(-0.861919,0.556873,-0.312856),'half':(.5,.5,.5),
   'rot':((-0.515958,-0.760046,-0.395117),(-0.261757,0.593418,-0.761143),(-0.994881,0.072175,-0.070733))}
u,v=a['rot'][1:]
axis=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
def dot(x,y): return sum(i*j for i,j in zip(x,y))
axis=tuple(x/math.sqrt(dot(axis,axis)) for x in axis)
def projected_vertices(box):
    rows=[tuple(x/math.sqrt(dot(row,row)) for x in row) for row in box['rot']]
    return [dot(tuple(box['center'][i]+sum(s*hh*row[i] for s,hh,row in zip(signs,box['half'],rows))
                       for i in range(3)),axis) for signs in itertools.product((-1,1),repeat=3)]
pa,pb=projected_vertices(a),projected_vertices(b)
gap=max(min(pb)-max(pa),min(pa)-max(pb))
assert gap>0 and P.obb_overlap(a,b) is False,gap
results.append({'probe':'skew_sat_independent_vertex_projection','separation_gap':gap,'overlap':False})

report={'probes':results,'verdict':'PASS'}
(Path(__file__).parent/'crossfix-probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
