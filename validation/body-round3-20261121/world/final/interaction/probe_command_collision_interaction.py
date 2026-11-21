from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import math
import sys

ROOT=Path(r'<repo>')
OTHER=Path(r'<no-contact-repo>\lingshu\world\scene_simulator.py')
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
source=(ROOT/'lingshu/world/scene_simulator.py').read_text(encoding='utf8')
contact_source=OTHER.read_text(encoding='utf8')
def method(text,name):
    cls=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name=='SceneSimulator')
    node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return node,''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
target,old=method(source,'_resolve_collisions');_,replacement=method(contact_source,'_resolve_collisions')
assert source.count(old)==1
combined=source.replace(old,replacement,1)
path=OUT/'command-plus-no-contact-scene.py';path.write_text(combined,encoding='utf8',newline='\n')
name='lingshu.world._command_collision_interaction'
spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
rows=[];max_error=0.
for dt in (.05,.1,.25,1.):
 for action,(dx,dz) in {'east':(1,0),'west':(-1,0),'north':(0,-1),'south':(0,1),'stay':(0,0)}.items():
  for x in (64.,64.003):
   for first in (False,True):
    s=module.SceneSimulator(size=128,seed=42);s.set_environment(gravity=10.,dt=dt)
    a=s.add_entity('actor','wander',(x,1000.,64.007),0.);e=s.entities[a];e.attrs['physics']=module.PHYSICS_DYNAMICS
    b=s.add_entity('distant_static','wander',(110.,1000.,110.),0.)
    s.set_entity_collision_box(a,(.25,.25,.25));s.set_entity_collision_box(b,(.25,.25,.25),static=True)
    if not first:
     s.set_entity_physics(a,v0=(.013,.2,.017),beta=.4,radius=.3,mass=2.5);s.step(3)
    old=e.pos;s.set_command(a,action,1.5);s.step()
    p0=(round(old[0]+dx*1.5,2),old[1],round(old[2]+dz*1.5,2))
    v0=(0.,0.,0.) if action=='stay' else tuple((p0[i]-old[i])/dt for i in range(3))
    public=(round(p0[0]-old[0],2),0.,round(p0[2]-old[2],2))
    assert e.pos==p0 and e.velocity==public
    assert e.attrs['physics_state']['p0']==p0 and e.attrs['physics_state']['v0']==v0
    assert not any(c['hit'] for c in s.collision_report()['contacts'])
    errors=[]
    for n in (1,2,3):
     s.step();t=n*dt
     expected_p=tuple(p0[i]+v0[i]*t-(5*t*t if i==1 else 0.) for i in range(3))
     expected_v=tuple(v0[i]-(10*t if i==1 else 0.) for i in range(3))
     error=max(abs(a-b) for actual,truth in ((e.pos,expected_p),(e.velocity,expected_v)) for a,b in zip(actual,truth));errors.append(error)
     assert all(math.isclose(a,b,abs_tol=1e-9,rel_tol=1e-12) for actual,truth in ((e.pos,expected_p),(e.velocity,expected_v)) for a,b in zip(actual,truth))
     assert not any(c['hit'] for c in s.collision_report()['contacts'])
    max_error=max(max_error,*errors);rows.append(dict(dt=dt,action=action,initial_x=x,first_command=first,max_errors=errors))
result={'method':'combine only authorized _resolve_collisions method from no-contact fix with final command source;2noncontacting boxes; independent endpoint+ballistic equations;80cases x3resumed ticks',
 'command_source_sha256_lf':hashlib.sha256(source.encode()).hexdigest(),'no_contact_source_sha256_lf':hashlib.sha256(contact_source.encode()).hexdigest(),
 'combined_scene_sha256_lf':hashlib.sha256(combined.encode()).hexdigest(),'cases':len(rows),'resumed_states':len(rows)*3,'max_abs_error':max_error,'passed':True,'raw_cases':rows}
(OUT/'command-collision-interaction.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='raw_cases'}))
