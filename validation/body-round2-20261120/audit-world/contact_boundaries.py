from pathlib import Path
import json
import sys
import importlib.util

repo = Path(r"[workspace]/lingshu/work\lingshu-body-collision-velocity-20261120")
sys.path.insert(0, str(repo))

def load(path, suffix):
    name = "lingshu.world._boundary_probe_" + suffix
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

def run(m, case):
    s = m.SceneSimulator(size=128, seed=42)
    s.set_environment(gravity=.5, dt=.25)
    gap, vx, all_static = {"touch_approach": (1., 10., False),
                           "full_overlap": (0., 0., False),
                           "full_overlap_all_static": (0., 0., True),
                           "end_touch": (3.5, 10., False),
                           "overlap_away_same_endpoint": (.25, -3., False)}[case]
    a = s.add_entity("a", "wander", (10., 1000., 10.), 0.)
    b = s.add_entity("b", "wander", (10. + gap, 1000., 10.), 0.)
    s.entities[a].attrs["physics"] = m.PHYSICS_DYNAMICS
    s.set_entity_physics(a, v0=(vx, .0625, 0.))
    s.set_entity_collision_box(a, (.5, .5, .5), static=all_static)
    s.set_entity_collision_box(b, (.5, .5, .5), static=True)
    s.step()
    e = s.entities[a]
    return {"case": case, "pos": e.pos, "velocity": e.velocity,
            "state": e.attrs["physics_state"],
            "readout_vel": e.attrs["physics_readout"]["vel"],
            "contacts": [{k: v for k, v in c.items() if k not in ("i", "j")}
                         for c in s.collision_report()["contacts"]]}

out = {}
sources = {"baseline": Path(__file__).with_name("benchmark-r1") / "sources/baseline.py",
           "fixed_r1": Path(__file__).with_name("benchmark-r1") / "sources/fixed.py",
           "current": repo / "lingshu/world/scene_simulator.py"}
for key, path in sources.items():
    m = load(path, key)
    out[key] = [run(m, case) for case in ("touch_approach", "full_overlap",
                                        "full_overlap_all_static", "end_touch",
                                        "overlap_away_same_endpoint")]
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
for key, rows in out.items():
    for row in rows:
        print(key, row["case"], row["pos"], row["velocity"],
              row["state"]["t_ref"], row["contacts"][0]["hit"])
