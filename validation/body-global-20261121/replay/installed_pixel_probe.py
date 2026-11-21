"""Installed pixel->perception->World3D->persistent core memory acceptance."""
from pathlib import Path
import hashlib,importlib.metadata,json,os,sys,sysconfig,warnings
require=lambda ok,message: None if ok else (_ for _ in ()).throw(AssertionError(message))
require(sys.flags.isolated==1,"requires isolated interpreter")
require("PYTHONPATH" not in os.environ,"inherited PYTHONPATH")
root=Path(__file__).resolve().parent
import lingshu
location=Path(lingshu.__file__).resolve()
sites={Path(sysconfig.get_path(k)).resolve() for k in ("purelib","platlib")}
require(any(location.is_relative_to(s) for s in sites),"not site-packages import")
require(not "work" in location.relative_to(root).parts,"imported checkout")
distribution=importlib.metadata.distribution("lingshu")
direct=json.loads(distribution.read_text("direct_url.json"))
require(not direct.get("dir_info",{}).get("editable"),"editable import")
from lingshu.nn.hex_hier import make_scene_dataset,perceive_scene_hex
from lingshu.world.world3d import World3D
from lingshu.core.core import SpacetimeMemoryEngine,STNode,ConditionSpace
pixels,expected_labels=make_scene_dataset(4,48,seed=7)
# Only the pixels are passed to this inference call. Expected labels are used
# below for scoring after perception and have no part in memory writes.
perceived=[perceive_scene_hex(image) for image in pixels]
db=root/"installed-pixel-memory.db"
require(not db.exists(),"preserve prior memory result")
condition=ConditionSpace(observation_position="installed-wheel-world3d",
 observation_tool="perceive_scene_hex",time_window=(0,100),existence_constraint="synthetic RGB fixture")
results=[]
with warnings.catch_warnings():
 warnings.simplefilter("ignore")
 engine=SpacetimeMemoryEngine(str(db))
try:
 world=World3D()
 for index,res in enumerate(perceived):
  require(res is not None,"missing perception")
  observation=world.add_view(res["category"],res["bbox"],48,48,confidence=res["confidence"])
  require(observation["category"]==res["category"],"World3D changed perceived category")
  node=STNode(id="installed-frame-"+str(index),
   content="pixel perception "+res["category"]+" bbox="+str(res["bbox"]),
   modality="text",spatial_coordinates={"bbox":list(res["bbox"]),"image_pos":res["pos"]},
   temporal_coordinate=float(index),condition_space=condition)
  nodeid=engine.store.add_node(node)
  got=engine.store.get_node(nodeid)
  require(got is not None and res["category"] in got.content,"write/read failed")
  require(any(n.id==nodeid for n,score in engine.store.search_content(res["category"],touch=False)),"search failed")
  results.append({"frame":index,"node_id":nodeid,"perceived_category":res["category"],
    "perceived_color":res["color"],"bbox":list(res["bbox"]),"pos":res["pos"],
    "pixel_sha256":hashlib.sha256(pixels[index].tobytes()).hexdigest(),
    "world3d_category":observation["category"],"readback":True,"search":True})
finally:engine.close()
with warnings.catch_warnings():
 warnings.simplefilter("ignore")
 reopened=SpacetimeMemoryEngine(str(db))
try:
 for row in results:
  got=reopened.store.get_node(row["node_id"])
  require(got is not None and row["perceived_category"] in got.content,"reopen read failed")
  require(any(n.id==row["node_id"] for n,score in reopened.store.search_content(row["perceived_category"],touch=False)),"reopen search failed")
  row["persisted_readback"]=row["persisted_search"]=True
finally:reopened.close()
color_hits=sum(row["perceived_color"]==expected_labels["color"][row["frame"]] for row in results)
object_hits=sum(row["perceived_category"]==expected_labels["obj"][row["frame"]] for row in results)
require(color_hits==object_hits==len(results)==4,"recognition scoring failed")
report={"accepted":True,"package_file":str(location),"isolated":True,"editable":False,
 "frames":4,"color_hits":color_hits,"shape_color_hits":object_hits,"persisted_readbacks":4,"persisted_searches":4,
 "expected_labels_used_only_for_scoring":True,"world3d_input_from_perception_only":True,
 "scope":"synthetic single-object RGB fixture; no real-camera or multi-object accuracy claim",
 "results":results,"numpy":importlib.metadata.version("numpy"),"Pillow":importlib.metadata.version("Pillow")}
(root/"installed-pixel-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
print(json.dumps({k:report[k] for k in ("accepted","package_file","frames","color_hits","shape_color_hits","persisted_readbacks","persisted_searches")},ensure_ascii=False))
