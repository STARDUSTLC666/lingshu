#!/usr/bin/env python3
"""Six-fix exact-commit correctness and timing reproduction.

Run with --repo LOCAL_PUBLIC_CLONE --output DIRECTORY. Dependencies: NumPy and
Pillow; Python 3.12 is the validated interpreter. See sibling README.md for
commit-fetch instructions, complete protocol and limitations. All writes stay
under --output; package source is frozen with git archive and never installed
over the repository. No network request, package installation or checkout is
performed by this runner. --only accepts comma-separated suite names.
"""
from __future__ import annotations
import argparse,gc,hashlib,io,itertools,json,math,os,platform,random,statistics,subprocess,sys,time,warnings,zipfile
from pathlib import Path

ROOT=None
REPO=None
BASE="d74848fb33dbff1d719959df19d1266a1ac60f44"
SEED=20261120
SUITES={
 "motion_groups":("cc68a82baace16e92ff6ce770330b65102a530a5","lingshu/world/motion_groups.py"),
 "lineart_alpha":("433befa7b356eebecbc457ecd8f8a123ec1540cc","lingshu/vision/lineart.py"),
 "obb_sat":("39d379552f34026ef46ad0515831319b1494a5d3","lingshu/world/physics.py"),
 "novelty_cache":("a663512dd0fbc44a9fb08a55751951009586d172","lingshu/core/longterm_gate.py"),
 "hexgrid_nearest":("cff189b3438623feaebdf1a874fafdd03080acb1","lingshu/nn/hex_cnn.py"),
 "skill_limit":("fb6c9cabc939a6defcc44ef661b3048d47155d87","lingshu/core/core.py"),
}
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
class Checks:
 def __init__(self): self.counts={};self.failures={}
 def check(self,name,ok,detail=None):
  self.counts[name]=self.counts.get(name,0)+1
  if not bool(ok):
   v=self.failures.setdefault(name,{"count":0,"examples":[]});v["count"]+=1
   if len(v["examples"])<8:v["examples"].append(detail)
 def result(self):
  return {"assertions":sum(self.counts.values()),"checks":self.counts,"failed_assertions":sum(x["count"] for x in self.failures.values()),"failures":self.failures}
def time_calls(label,factory,*,calls=1,repeats=9,warmups=3):
 samples=[];cpus=[]
 for i in range(warmups+repeats):
  fn,cleanup=factory();gc.collect();was=gc.isenabled();gc.disable()
  try:
   t0,c0=time.perf_counter_ns(),time.process_time_ns()
   for _ in range(calls):fn()
   elapsed,cpu=time.perf_counter_ns()-t0,time.process_time_ns()-c0
  finally:
   if was:gc.enable()
   if cleanup:cleanup()
  if i>=warmups:samples.append(elapsed/calls/1e6);cpus.append(cpu/calls/1e6)
 ordered=sorted(samples)
 return {"label":label,"unit":"ms per timed operation","calls_per_sample":calls,"warmup_samples":warmups,"repeated_samples":repeats,
 "wall_ms_samples":samples,"cpu_ms_samples":cpus,"median_ms":statistics.median(samples),"min_ms":min(samples),"max_ms":max(samples),
 "p10_ms":ordered[math.floor(.1*(len(ordered)-1))],"p90_ms":ordered[math.ceil(.9*(len(ordered)-1))],"stdev_ms":statistics.stdev(samples)}
def simple_factory(fn):return lambda:(fn,None)
def motion_suite():
 from lingshu.world import motion_groups as M
 c=Checks()
 for i in range(80):
  token="字%d"%i;left=["a"+token+"|b","c"];right=["a"+token,"b|c"]
  history=[{"tick":t,"entities":{left[0]:[t,1,0],left[1]:[t+2,1,0],right[0]:[20-t,1,10],right[1]:[22-t,1,10]}} for t in range(1,6)]
  result=M.detect_motion_groups(history);ids=[g["group_id"] for g in result["groups"]]
  c.check("distinct_delimiter_groups",len(result["groups"])==2 and len(set(ids))==2,{"case":i,"ids":ids})
  rev=[{"tick":x["tick"],"entities":dict(reversed(list(x["entities"].items())))} for x in history]
  c.check("input_order_invariance",result==M.detect_motion_groups(rev),i)
 for members in (["left","right"],["甲","乙"],["","ordinary"],['["a','b","c"]']):
  expected="mg_"+hashlib.sha1("|".join(members).encode()).hexdigest()[:12]
  c.check("legacy_plain_ids_preserved",M._group_id(members)==expected,members)
 tricky=(["a|b","c"],["a","b|c"],["a|","b"],["a","|b"],["a||b","c"])
 c.check("structured_identifier_partitions",len({M._group_id(list(x)) for x in tricky})==len(tricky))
 perf=[]
 for count in (8,32,96):
  h=[{"tick":t,"entities":{"member%d|id"%j:[j*2+t,1,0] for j in range(count)}} for t in range(8)]
  perf.append(time_calls("detect_8_frames_%d_entities"%count,simple_factory(lambda h=h:M.detect_motion_groups(h)),calls=3))
 return c.result(),perf,{"source":str(Path(M.__file__).resolve()),"seed":SEED}
def lineart_suite():
 import numpy as np
 from PIL import Image
 from lingshu.vision import lineart as L
 rng=np.random.default_rng(SEED);c=Checks()
 for width,height in ((8,9),(32,32),(61,47),(128,96)):
  rgba=rng.integers(0,256,(height,width,4),dtype=np.uint8);rgba[::2,::2,3]=0;rgba[1::3,1::3,3]=255
  for mode in ("RGBA","LA"):
   im=Image.fromarray(rgba,"RGBA") if mode=="RGBA" else Image.fromarray(rgba[...,[0,3]],"LA")
   converted=np.asarray(im.convert("RGBA"),dtype=np.uint32);a=converted[...,3:4]
   visible=((converted[...,:3]*a+255*(255-a)+127)//255).astype(np.uint8)
   expected=np.asarray(L.darkline(Image.fromarray(visible,"RGB")));actual=np.asarray(L.darkline(im))
   c.check("alpha_matches_independent_white_composite",np.array_equal(actual,expected),{"size":[width,height],"mode":mode,"different_pixels":int(np.count_nonzero(actual!=expected))})
   inv=np.asarray(L.darkline(im,white_bg=False))
   c.check("inversion_preserved",np.array_equal(actual.astype(int)+inv.astype(int),np.full(actual.shape,255)))
   c.check("linework_rgb_consistent",np.array_equal(np.asarray(L.linework(im)),np.repeat(actual[...,None],3,axis=2)))
   c.check("input_unchanged",np.array_equal(np.asarray(im.convert("RGBA")),converted.astype(np.uint8)))
  changed=rgba.copy();mask=changed[...,3]==0;changed[...,:3][mask]=rng.integers(0,256,(int(mask.sum()),3),dtype=np.uint8)
  c.check("hidden_rgb_invariance",np.array_equal(np.asarray(L.darkline(Image.fromarray(rgba,"RGBA"))),np.asarray(L.darkline(Image.fromarray(changed,"RGBA")))),[width,height])
  # Exact-valued premultiplication avoids making the oracle depend on Pillow's
  # unpremultiply rounding: multiples of 51 with alpha 0/85/170/255 are exact.
  straight=rng.choice(np.asarray([0,51,102,153,204,255],dtype=np.uint8),size=(height,width,4));straight[...,3]=rng.choice(np.asarray([0,85,170,255],dtype=np.uint8),size=(height,width))
  for mode in ("RGBa","La"):
   src=Image.fromarray(straight,"RGBA") if mode=="RGBa" else Image.fromarray(straight[...,[0,3]],"LA")
   premul=src.convert(mode);before=np.array(premul);alpha=before[...,-1:].astype(np.uint16);colours=before[...,:-1].astype(np.uint16)
   if mode=="La":colours=np.repeat(colours,3,axis=2)
   visible=(colours+255-alpha).astype(np.uint8);expected=np.asarray(L.darkline(Image.fromarray(visible,"RGB")))
   detail={"size":[width,height],"mode":mode}
   try:actual=np.asarray(L.darkline(premul))
   except Exception as e:
    c.check("premultiplied_conversion_supported",False,dict(detail,error=repr(e)));continue
   c.check("premultiplied_conversion_supported",True,detail)
   c.check("premultiplied_matches_direct_white_composite",np.array_equal(actual,expected),dict(detail,different_pixels=int(np.count_nonzero(actual!=expected))))
   c.check("premultiplied_inversion_preserved",np.array_equal(actual.astype(int)+np.asarray(L.darkline(premul,white_bg=False)).astype(int),np.full(actual.shape,255)),detail)
   c.check("premultiplied_linework_rgb_consistent",np.array_equal(np.asarray(L.linework(premul)),np.repeat(actual[...,None],3,axis=2)),detail)
   c.check("premultiplied_input_unchanged",np.array_equal(np.asarray(premul),before),detail)
 p=Image.new("P",(32,32),0);p.putpalette([0,0,0]*256);p.info["transparency"]=0
 for x in range(8,24):p.putpixel((x,16),1)
 c.check("palette_transparency_visible_line",int(np.count_nonzero(np.asarray(L.darkline(p))==0))==36)
 # PA carries a per-pixel alpha channel in addition to the palette index.
 palette=np.asarray([[0,0,0],[255,0,0],[0,255,0],[0,0,255]],dtype=np.uint8);indices=rng.integers(0,4,(32,32),dtype=np.uint8);alpha=rng.choice(np.asarray([0,85,170,255],dtype=np.uint8),size=(32,32));pa=Image.fromarray(np.stack((indices,alpha),axis=2),"PA");pa.putpalette(palette.reshape(-1).tolist()+[0]*(768-12));before=np.array(pa)
 a=alpha[...,None].astype(np.uint32);visible=((palette[indices].astype(np.uint32)*a+255*(255-a)+127)//255).astype(np.uint8);expected=np.asarray(L.darkline(Image.fromarray(visible,"RGB")))
 try:
  actual=np.asarray(L.darkline(pa));c.check("PA_conversion_supported",True)
  c.check("PA_matches_independent_palette_alpha_composite",np.array_equal(actual,expected),{"different_pixels":int(np.count_nonzero(actual!=expected))})
  c.check("PA_inversion_preserved",np.array_equal(actual.astype(int)+np.asarray(L.darkline(pa,white_bg=False)).astype(int),np.full(actual.shape,255)))
  c.check("PA_linework_rgb_consistent",np.array_equal(np.asarray(L.linework(pa)),np.repeat(actual[...,None],3,axis=2)))
  c.check("PA_input_unchanged",np.array_equal(np.asarray(pa),before))
 except Exception as e:c.check("PA_conversion_supported",False,repr(e))
 for mode in ("RGB","L","RGBA"):
  im=Image.new(mode,(32,32),(124,33,65,255) if mode=="RGBA" else ((124,33,65) if mode=="RGB" else 123))
  c.check("opaque_uniform_no_edges",bool((np.asarray(L.darkline(im))==255).all()),mode)
 perf=[]
 for size in (128,512,1536):
  data=rng.integers(0,256,(size,size,4),dtype=np.uint8)
  for mode in ("RGB","RGBA"):
   im=Image.fromarray(data,"RGBA").convert("RGB") if mode=="RGB" else Image.fromarray(data,"RGBA")
   perf.append(time_calls("darkline_%s_%dx%d"%(mode,size,size),simple_factory(lambda im=im:L.darkline(im))))
 return c.result(),perf,{"source":str(Path(L.__file__).resolve()),"seed":SEED}
def corners(box):
 import numpy as np
 edges=np.asarray(box["rot"],dtype=float);edges=edges/np.linalg.norm(edges,axis=1)[:,None]
 scaled=edges*np.asarray(box["half"])[:,None];signs=np.asarray(list(itertools.product((-1,1),repeat=3)))
 return np.asarray(box["center"])+signs@scaled,edges
def oracle_overlap(a,b):
 import numpy as np
 ca,ea=corners(a);cb,eb=corners(b)
 axes=[np.cross(e[i],e[j]) for e in (ea,eb) for i,j in ((1,2),(2,0),(0,1))]
 axes.extend(np.cross(x,y) for x in ea for y in eb);max_gap=-math.inf
 for axis in axes:
  n=float(np.linalg.norm(axis))
  if n<1e-12:continue
  axis=axis/n;pa,pb=ca@axis,cb@axis
  gap=max(float(pa.min()-pb.max()),float(pb.min()-pa.max()));max_gap=max(max_gap,gap)
  if gap>=0:return False,gap
 return True,max_gap
def obb_suite():
 import numpy as np
 from lingshu.world import physics as P
 rng=np.random.default_rng(SEED);c=Checks()
 frozen=(
 {"center":(.5,.5,.5),"half":(.5,.5,.5),"rot":((-.554749,.360100,-.750054),(-.407590,-.897262,.169682),(-.506776,.320162,.800422))},
 {"center":(-.861919,.556873,-.312856),"half":(.5,.5,.5),"rot":((-.515958,-.760046,-.395117),(-.261757,.593418,-.761143),(-.994881,.072175,-.070733))})
 pairs=[frozen]
 def random_box(scale):
  while True:
   r=rng.normal(size=(3,3));r/=np.linalg.norm(r,axis=1)[:,None]
   if abs(float(np.linalg.det(r)))>.15:break
  return {"center":tuple(rng.normal(size=3)*scale),"half":tuple(rng.uniform(.1,1,size=3)),"rot":tuple(tuple(x) for x in r)}
 for i in range(600):pairs.append((random_box(.7 if i%2 else 2),random_box(.7 if i%2 else 2)))
 overlap_count=0
 for i,(a,b) in enumerate(pairs):
  expected,gap=oracle_overlap(a,b);actual=P.obb_overlap(a,b)
  c.check("overlap_matches_independent_corner_sat",actual is expected,{"case":i,"expected":expected,"actual":actual,"gap":gap})
  c.check("overlap_symmetric",actual==P.obb_overlap(b,a),i)
  mtv=P.obb_mtv(a,b);rev=P.obb_mtv(b,a)
  c.check("mtv_none_iff_no_overlap",(mtv is None)==(not actual),i)
  if actual:
   overlap_count+=1;axis,depth=mtv
   c.check("mtv_depth_symmetric",rev is not None and abs(rev[1]-depth)<1e-10,i)
   moved=dict(b);moved["center"]=tuple(b["center"][j]+axis[j]*(depth+1e-8) for j in range(3))
   c.check("mtv_separates_in_independent_oracle",not oracle_overlap(a,moved)[0],{"case":i,"depth":depth})
   da,db=P.resolve_penetration(a,b,mass_a=1,mass_b=3);ma,mb=dict(a),dict(b)
   ma["center"]=tuple(a["center"][j]+da[j] for j in range(3));mb["center"]=tuple(b["center"][j]+db[j] for j in range(3))
   c.check("resolve_separates_oracle",not oracle_overlap(ma,mb)[0],i)
 singular={"center":(0,0,0),"half":(1,1,1),"rot":((1,0,0),(0,1,0),(1,1,0))};rejected=False
 try:P.obb_of(aabb={k:singular[k] for k in ("center","half")},rot=singular["rot"])
 except P.PhysicsError:rejected=True
 c.check("singular_basis_rejected",rejected)
 perf=[]
 for count in (32,128,512):
  selected=pairs[:count]
  perf.append(time_calls("overlap_%d_pairs"%count,simple_factory(lambda selected=selected:[P.obb_overlap(a,b) for a,b in selected])))
 return c.result(),perf,{"source":str(Path(P.__file__).resolve()),"seed":SEED,"overlapping_pairs":overlap_count,"pair_count":len(pairs)}
def _add_node(store,i,content=None):
 from lingshu.core.core import STNode,ConditionSpace,MemoryLayer
 text=content if content is not None else "基准知识条目 alpha%d beta%d gamma%d"%(i,i,i)
 node=STNode(id="bench_%d"%i,content=text,modality="text",spatial_coordinates={},temporal_coordinate=1.,condition_space=ConditionSpace("benchmark","synthetic",(0.,1.),"synthetic"),layer=MemoryLayer.CONTEXT,created_at=1.,last_access=1.)
 return store.add_node(node)

def _make_store(count):
 from lingshu.core.core import LayeredStore
 store=LayeredStore(":memory:")
 for i in range(count):_add_node(store,i)
 return store

def novelty_suite():
 from types import SimpleNamespace
 from lingshu.core import longterm_gate as G
 Gate=G.LongTermMemoryGate;c=Checks()
 for count in (1,10,100):
  for mode in ("equal_length","longer","shorter"):
   store=_make_store(count)
   try:
    old="甲乙丙丁戊己庚辛壬癸旧知识";new="子丑寅卯辰巳午未申酉新知识"
    if mode=="longer":new+="天地玄黄宇宙洪荒"
    elif mode=="shorter":new="天干地支星辰"
    store.conn.execute("UPDATE nodes SET content=? WHERE id=?",(old,"bench_0"));store.conn.commit()
    gate=Gate(SimpleNamespace(store=store));gate._known_snapshot()
    rid=store.conn.execute("SELECT rowid FROM nodes WHERE id='bench_0'").fetchone()[0]
    store.conn.execute("UPDATE nodes SET content=? WHERE id=?",(new,"bench_0"));store.conn.commit()
    _add_node(store,count,"追加条目独立测试内容 青山绿水春夏秋冬山川河流")
    actual=gate._known_snapshot();fresh=Gate(SimpleNamespace(store=store));expected=fresh._known_snapshot()
    detail={"count":count,"mode":mode}
    c.check("update_preserves_rowid",store.conn.execute("SELECT rowid FROM nodes WHERE id='bench_0'").fetchone()[0]==rid,detail)
    for j,label in enumerate(("union","counts","per_node","signature")):
     c.check("mixed_update_append_"+label,actual[j]==expected[j],detail)
    for label,content in (("old",old),("new",new),("appended","追加条目独立测试内容 青山绿水春夏秋冬山川河流")):
     c.check("novelty_matches_fresh_"+label,gate._novelty(content)==fresh._novelty(content),detail)
   finally:store.conn.close()
 for count in (0,50,500):
  store=_make_store(count)
  try:
   gate=Gate(SimpleNamespace(store=store));before=gate._known_snapshot();calls=[];original=gate._core_grams
   def counted(text):calls.append(text);return original(text)
   gate._core_grams=counted;_add_node(store,count);after=gate._known_snapshot()
   c.check("append_reuses_union",before[0] is after[0],count)
   c.check("append_parses_only_new_row",len(calls)==1,{"count":count,"gram_calls":len(calls)})
  finally:store.conn.close()
 # Stateful property sequence exercises cache evolution, not only one edit.
 # The oracle is rebuilt from the same current DB after every public/SQL step.
 store=_make_store(20);gate=Gate(SimpleNamespace(store=store));gate._known_snapshot();sequence=random.Random(SEED);next_id=20
 try:
  for step in range(120):
   rows=list(store.conn.execute("SELECT id,content FROM nodes ORDER BY rowid"));action=sequence.choice(("append","update","replace","delete","mixed")) if rows else "append"
   if action in ("update","replace","delete","mixed"):
    nid,previous=sequence.choice(rows)
    if action=="delete":store.delete_node(nid)
    elif action=="replace":_add_node(store,int(nid.split("_")[1]),"覆盖序列内容 天地玄黄 宇宙洪荒%04d"%step)
    else:store.conn.execute("UPDATE nodes SET content=? WHERE id=?",("改写序列内容 日月盈昃 辰宿列张%04d"%step,nid));store.conn.commit()
   if action in ("append","mixed"):
    _add_node(store,next_id,"追加序列内容 寒来暑往 秋收冬藏 闰余成岁 律吕调阳%04d"%step);next_id+=1
   actual=gate._known_snapshot();fresh=Gate(SimpleNamespace(store=store));expected=fresh._known_snapshot();detail={"step":step,"action":action,"nodes":expected[3][0]}
   for j,label in enumerate(("union","counts","per_node","signature")):c.check("stateful_sequence_"+label,actual[j]==expected[j],detail)
   current=store.conn.execute("SELECT content FROM nodes ORDER BY rowid DESC LIMIT 1").fetchone()
   query=current[0] if current else "不存在的知识内容"
   c.check("stateful_sequence_novelty",gate._novelty(query)==fresh._novelty(query),detail)
   c.check("stateful_sequence_warm_identity",gate._known_snapshot()[0] is actual[0],detail)
 finally:store.conn.close()
 perf=[]
 for count in (100,1000,5000):
  base=_make_store(count)
  try:
   def factory(kind,count=count,base=base):
    from lingshu.core.core import LayeredStore
    store=LayeredStore(":memory:");base.conn.backup(store.conn);gate=Gate(SimpleNamespace(store=store));gate._known_snapshot();index=count
    def op():
     nonlocal index
     if kind=="mixed":store.conn.execute("UPDATE nodes SET content=? WHERE id='bench_0'",("改写内容 新状态%d"%index,));store.conn.commit()
     if kind!="warm":_add_node(store,index);index+=1
     return gate._known_snapshot()
    return op,store.conn.close
   for kind,calls in (("warm",5),("append",5),("mixed",3)):
    perf.append(time_calls("snapshot_%s_%d_nodes"%(kind,count),lambda kind=kind:factory(kind),calls=calls))
  finally:base.conn.close()
 return c.result(),perf,{"source":str(Path(G.__file__).resolve()),"seed":SEED,"store":"SQLite :memory:","mutations":"public append plus explicit same-rowid SQL update; fresh Gate oracle"}

def hexgrid_suite():
 import numpy as np
 from lingshu.nn import hex_cnn as H
 rng=np.random.default_rng(SEED);c=Checks();point_total=0
 cases=[("odd_r_offset",.125,(0.,0.)),("odd_r_offset",.5,(-2.7,4.9)),("odd_r_offset",1.,(0.,0.)),("odd_r_offset",5.,(12.3,-45.6)),("axial",1.,(0.,0.))]
 for mode,size,origin in cases:
  grid=H.HexGrid(100,100,size,mode=mode,origin=origin)
  for q,r in itertools.product(range(-10,11),repeat=2):
   c.check("center_roundtrip_"+mode,grid.pixel_to_cell(*grid.center_px(q,r))==(q,r),{"mode":mode,"size":size,"q":q,"r":r})
  for i in range(2000):
   x,y=(rng.uniform(-30,30,2)*size+np.asarray(origin));q,r=grid.pixel_to_cell(float(x),float(y));cx,cy=grid.center_px(q,r);actual=(x-cx)**2+(y-cy)**2
   # Brute-force Euclidean nearest center; candidate bounds derive from y first,
   # then x on each candidate row, independently of production cube rounding.
   r0=int(math.floor((y-origin[1])/(1.5*size)));best=math.inf;best_cell=None
   for rr in range(r0-3,r0+4):
    shift=.5*(rr%2) if mode=="odd_r_offset" else rr/2
    q0=int(math.floor((x-origin[0])/(math.sqrt(3)*size)-shift))
    for qq in range(q0-4,q0+5):
     xx,yy=grid.center_px(qq,rr);d=(x-xx)**2+(y-yy)**2
     if d<best:best=d;best_cell=(qq,rr)
   c.check("euclidean_nearest_"+mode,actual<=best+1e-10*size*size,{"mode":mode,"size":size,"origin":origin,"point":[float(x),float(y)],"actual":[q,r],"best":best_cell,"distance_sq_excess":float(actual-best)})
   point_total+=1
 perf=[];grid=H.HexGrid(100,100,1.,mode="odd_r_offset",origin=(-2.7,4.9))
 for count in (1000,10000,50000):
  points=[tuple(x) for x in rng.uniform(-100,100,(count,2))]
  perf.append(time_calls("nearest_odd_r_%d_points"%count,simple_factory(lambda points=points:[grid.pixel_to_cell(x,y) for x,y in points])))
 return c.result(),perf,{"source":str(Path(H.__file__).resolve()),"seed":SEED,"random_point_count":point_total,"oracle":"Euclidean distance over 63 nearby centers; no boundary clipping requested"}

def skills_suite():
 from lingshu.core import core as C
 c=Checks()
 def skill_store(count):
  store=C.LayeredStore(":memory:")
  for i in range(count):store.add_skill("needle skill %04d"%i,"needle benchmark description %04d"%i,"procedure %04d"%i,confidence=.1+.8*i/max(1,count))
  return store
 for count in (1,5,50,100,150):
  store=skill_store(count)
  try:
   for query in ("needle",""):
    all_ids=[s["id"] for s in store.search_skills(query,None)]
    c.check("existing_candidate_cap_preserved",len(all_ids)==min(count,100),{"count":count,"query":query})
    for limit in (None,-1,-6,-101):
     got=[s["id"] for s in store.search_skills(query,limit)]
     c.check("nonpositive_unbounded_semantics",got==all_ids,{"count":count,"query":query,"limit":limit,"actual_count":len(got),"expected_count":len(all_ids)})
    for limit in (0,1,3,10,100,101):
     c.check("positive_and_zero_prefix",[s["id"] for s in store.search_skills(query,limit)]==all_ids[:limit],{"count":count,"query":query,"limit":limit})
  finally:store.conn.close()
 perf=[]
 for count in (100,1000,5000):
  store=skill_store(count)
  try:
   for limit in (-1,10,None):
    perf.append(time_calls("search_%d_skills_limit_%s"%(count,limit),simple_factory(lambda limit=limit:store.search_skills("needle",limit)),calls=20))
  finally:store.conn.close()
 return c.result(),perf,{"source":str(Path(C.__file__).resolve()),"seed":SEED,"candidate_cap":100,"store":"SQLite :memory:"}

RUNNERS={"motion_groups":motion_suite,"lineart_alpha":lineart_suite,"obb_sat":obb_suite,"novelty_cache":novelty_suite,"hexgrid_nearest":hexgrid_suite,"skill_limit":skills_suite}

def git(*args,binary=False):
 result=subprocess.run(["git","-C",str(REPO),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 return result.stdout if binary else result.stdout.decode("utf-8","replace").strip()

def snapshot(commit):
 full=git("rev-parse",commit);dest=ROOT/"snapshots"/full[:12];marker=dest/"snapshot.json"
 if marker.exists():
  meta=json.loads(marker.read_text(encoding="utf-8"))
  if meta.get("commit")!=full:raise RuntimeError("Snapshot commit mismatch")
  return dest,meta
 archive=git("archive","--format=zip",full,"lingshu",binary=True)
 dest.mkdir(parents=True,exist_ok=True);resolved=dest.resolve()
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  for entry in z.infolist():
   target=(dest/entry.filename).resolve()
   if not target.is_relative_to(resolved):raise RuntimeError("Unsafe archive entry: "+entry.filename)
  z.extractall(dest)
 meta={"commit":full,"package_tree":git("rev-parse",full+":lingshu"),"archive_sha256":hashlib.sha256(archive).hexdigest(),"archive_bytes":len(archive),"path":str(dest),"source_repository":str(REPO)}
 write_json(marker,meta);return dest,meta

def environment():
 import sqlite3
 import numpy
 import PIL
 return {"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"processor":platform.processor(),"cpu_count":os.cpu_count(),"numpy":numpy.__version__,"pillow":PIL.__version__,"sqlite":sqlite3.sqlite_version,"pythonhashseed":os.environ.get("PYTHONHASHSEED"),"seed":SEED,"perf_counter":vars(time.get_clock_info("perf_counter")),"process_clock":vars(time.get_clock_info("process_time")),"cpu_affinity":"uncontrolled","power_plan":"uncontrolled","wall_clock_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}

def worker(args):
 import traceback
 sys.path.insert(0,str(Path(args.snapshot).resolve()));random.seed(SEED)
 result={"suite":args.suite,"variant":args.variant,"commit":args.commit,"snapshot":str(Path(args.snapshot).resolve()),"environment":environment()}
 started=time.perf_counter()
 try:
  correctness,perf,extra=RUNNERS[args.suite]();result.update(correctness=correctness,performance=perf,details=extra,status="completed")
  source=Path(extra["source"]);relative=Path(SUITES[args.suite][1]);expected=Path(args.snapshot)/relative
  if source.resolve()!=expected.resolve():raise RuntimeError("Imported incorrect source: "+str(source))
  result["source_lf_sha256"]=hashlib.sha256(source.read_bytes().replace(b"\r\n",b"\n")).hexdigest()
 except Exception as e:
  result.update(status="error",error=repr(e),traceback=traceback.format_exc())
 result["elapsed_seconds"]=time.perf_counter()-started;write_json(Path(args.output),result)
 print(json.dumps({"suite":args.suite,"variant":args.variant,"status":result["status"],"assertions":result.get("correctness",{}).get("assertions"),"failed_assertions":result.get("correctness",{}).get("failed_assertions"),"elapsed_seconds":result["elapsed_seconds"]},ensure_ascii=False),flush=True)
 return 0 if result["status"]=="completed" else 2

def make_report(results,snapshots):
 report={"baseline":BASE,"seed":SEED,"snapshots":snapshots,"suite_results":{},"runner_lf_sha256":hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n",b"\n")).hexdigest(),"limitations":["Synthetic deterministic CPU and in-memory SQLite workloads; no production databases, real imagery, GPU, network, or live engine tasks.","Host concurrently runs other verification work. No CPU pinning or power-plan control. Timings are descriptive, not isolated-hardware or statistical-significance claims.","Fixture construction is excluded from measured samples; append and mixed timings include their named database mutations. GC disabled only during timed operations; 3 warmups plus 9 retained samples.","OBB randomized bases have abs(det)>0.15; no extremely near-singular geometry coverage.","Skill search keeps the pre-existing 100-row candidate cap, even with negative/unbounded limit.","Novelty warm checks still scan/hash all rows; no constant-time or memory-reduction claim."]}
 lines=["# Six-fix correctness and performance comparison","","Baseline: "+BASE,"","Seed: "+str(SEED),"","Every variant imports a separately archived package at its exact commit. Raw samples and environment metadata are in raw/*.json; snapshots retain archive SHA-256 and package tree hashes.","","## Correctness","","| Suite | PR | Baseline failed / assertions | Fixed failed / assertions | Fixed status |","|---|---:|---:|---:|---|"]
 for name,(commit,source) in SUITES.items():
  base=results.get((name,"baseline"),{});fixed=results.get((name,"fixed"),{});bc=base.get("correctness",{});fc=fixed.get("correctness",{})
  pairs=[];bp={p["label"]:p for p in base.get("performance",[])}
  for p in fixed.get("performance",[]):
   old=bp.get(p["label"])
   if old:pairs.append({"label":p["label"],"baseline_median_ms":old["median_ms"],"fixed_median_ms":p["median_ms"],"fixed_over_baseline":p["median_ms"]/old["median_ms"]})
  report["suite_results"][name]={"commit":commit,"source":source,"baseline_status":base.get("status"),"fixed_status":fixed.get("status"),"baseline_correctness":bc,"fixed_correctness":fc,"performance_comparison":pairs}
  lines.append("| %s | %s | %s / %s | %s / %s | %s |"%(name,{"motion_groups":1469,"lineart_alpha":1470,"obb_sat":1471,"novelty_cache":1472,"hexgrid_nearest":1473,"skill_limit":1474}[name],bc.get("failed_assertions","error"),bc.get("assertions","?"),fc.get("failed_assertions","error"),fc.get("assertions","?"),fixed.get("status","missing")))
 lines += ["","## Timing medians","","Units: ms per named batch or operation. Ratios >1 mean the fixed version took longer in these samples.","","| Workload | Baseline median ms | Fixed median ms | Fixed / baseline |","|---|---:|---:|---:|"]
 for suite in report["suite_results"].values():
  for p in suite["performance_comparison"]:lines.append("| %s | %.6f | %.6f | %.3fx |"%(p["label"],p["baseline_median_ms"],p["fixed_median_ms"],p["fixed_over_baseline"]))
 lines += ["","## Failure detail",""]
 for name in SUITES:
  for variant in ("baseline","fixed"):
   r=results.get((name,variant),{})
   if r.get("error"):lines.extend(["### "+name+" / "+variant,"",r["error"],""])
   for category,failure in r.get("correctness",{}).get("failures",{}).items():lines.append("- %s / %s / %s: %d failed; examples recorded in raw JSON."%(name,variant,category,failure["count"]))
 lines += ["","## Scope and limitations",""]+["- "+x for x in report["limitations"]]
 write_json(ROOT/"comparison.json",report);(ROOT/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
 return report

def orchestrate(args):
 results={};snaps={};raw=ROOT/"raw";raw.mkdir(parents=True,exist_ok=True)
 selected=list(SUITES) if not args.only else args.only.split(",")
 for index,name in enumerate(selected):
  variants=[("baseline",BASE),("fixed",SUITES[name][0])]
  if index%2:variants.reverse()
  for variant,commit in variants:
   dest,meta=snapshot(commit);snaps[meta["commit"]]=meta;output=raw/(name+"_"+variant+".json")
   env=os.environ.copy();env.update(PYTHONHASHSEED=str(SEED),PYTHONDONTWRITEBYTECODE="1")
   cmd=[sys.executable,"-B","-X","utf8",str(Path(__file__).resolve()),"--worker","--suite",name,"--variant",variant,"--commit",commit,"--snapshot",str(dest),"--output",str(output)]
   print("RUN "+name+" "+variant+" "+commit,flush=True)
   run=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",errors="replace")
   (raw/(name+"_"+variant+".stdout.log")).write_text(run.stdout,encoding="utf-8");(raw/(name+"_"+variant+".stderr.log")).write_text(run.stderr,encoding="utf-8")
   if output.exists():results[name,variant]=json.loads(output.read_text(encoding="utf-8"))
   else:results[name,variant]={"status":"error","error":"Worker did not produce result; exit "+str(run.returncode)}
   print(run.stdout.strip() or results[name,variant].get("error",""),flush=True)
 # Include existing raw results when intentionally rerunning one repaired harness.
 for name in SUITES:
  for variant in ("baseline","fixed"):
   existing=raw/(name+"_"+variant+".json")
   if (name,variant) not in results and existing.exists():results[name,variant]=json.loads(existing.read_text(encoding="utf-8"))
 for marker in (ROOT/"snapshots").glob("*/snapshot.json"):
  meta=json.loads(marker.read_text(encoding="utf-8"));snaps[meta["commit"]]=meta
 report=make_report(results,snaps);fixed_failures=sum(r.get("fixed_correctness",{}).get("failed_assertions",0) for r in report["suite_results"].values())
 print("REPORT "+str(ROOT/"report.md"),flush=True);print("FIXED_FAILURES "+str(fixed_failures),flush=True)
 return 1 if fixed_failures or any(results.get((n,"fixed"),{}).get("status")!="completed" for n in selected) else 0

def main():
 global ROOT,REPO
 p=argparse.ArgumentParser(description="Reproduce six exact-commit fixes with isolated source snapshots, correctness properties and raw latency samples.")
 p.add_argument("--repo",type=Path,default=Path.cwd(),help="Local clone of the public Git repository (default: cwd); fetch the PR heads first")
 p.add_argument("--output",type=Path,required=True,help="Output directory (internal workers pass their result JSON path)")
 p.add_argument("--only",help="Comma-separated suite names; omitted means all six")
 p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);p.add_argument("--suite",choices=SUITES,help=argparse.SUPPRESS)
 p.add_argument("--variant",help=argparse.SUPPRESS);p.add_argument("--commit",help=argparse.SUPPRESS);p.add_argument("--snapshot",help=argparse.SUPPRESS)
 args=p.parse_args()
 if args.worker:return worker(args)
 if args.only and any(name not in SUITES for name in args.only.split(",")):p.error("--only must use suite names: "+", ".join(SUITES))
 REPO=args.repo.resolve();ROOT=args.output.resolve();ROOT.mkdir(parents=True,exist_ok=True)
 if not REPO.is_dir():p.error("--repo does not exist")
 return orchestrate(args)
if __name__=="__main__":raise SystemExit(main())

