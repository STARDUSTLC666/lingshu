"""A real SevenLayerLoop actuator command survives execution but not release."""
from pathlib import Path
import copy
import json
import sys

sys.path.insert(0, r"<audit-repo>")
from lingshu.world.scene_simulator import SceneSimulator, PHYSICS_DYNAMICS
from lingshu.world.seven_layer_loop import SevenLayerLoop

s = SceneSimulator(size=128, seed=42)
s.set_environment(gravity=10., dt=.1)
a = s.add_entity("ball", "wander", (64., 1000., 64.), 0.)
s.entities[a].attrs["physics"] = PHYSICS_DYNAMICS
s.set_entity_physics(a, v0=(0., 0., 0.))
loop = SevenLayerLoop(world=s, size=128, seed=42, budget=1, policy="round_robin")
for _ in range(3):
    loop.step()
before = {"tick": s.tick_count, "pos": s.entities[a].pos}
configured = loop.configure_action(a, (90., 1000., 64.), step_size=2., policy="fixed", fixed_action="east")
action_record = copy.deepcopy(loop.step())
acted = {"tick": s.tick_count, "pos": s.entities[a].pos, "state": copy.deepcopy(s.entities[a].attrs["physics_state"])}
cleared = loop.clear_action()
resume_record = copy.deepcopy(loop.step())
resumed = {"tick": s.tick_count, "pos": s.entities[a].pos, "state": copy.deepcopy(s.entities[a].attrs["physics_state"])}
out = {"head": "04e0ecb6a3669c90efbb4a1583816a8f7ca26bc7", "before": before,
       "configured": configured, "action": action_record, "acted": acted,
       "cleared": cleared, "resumed": resumed, "resume_record": resume_record,
       "horizontal_action_undone": resumed["pos"][0] == before["pos"][0] and acted["pos"][0] != before["pos"][0]}
Path(__file__).with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: out[k] for k in ("before", "configured", "acted", "cleared", "resumed", "horizontal_action_undone")}, ensure_ascii=False, indent=2))
print(json.dumps(action_record["L7_action"].get("executed"), ensure_ascii=False, indent=2))
