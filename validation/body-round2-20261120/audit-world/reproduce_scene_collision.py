"""Read-only public API reproductions on upstream d74848fb. No source mutation."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(r"[workspace]/lingshu/work\lingshu-audit-core-20261120")
sys.path.insert(0, str(ROOT))
from lingshu.world.scene_simulator import SceneSimulator, PHYSICS_DYNAMICS


def slide(fraction, axis="x", moving_wall=False):
    s = SceneSimulator(size=64, seed=11)
    p0 = (10.0, 1.5, 10.0)
    goal = s.add_entity("goal", "wander", (20.0, 1.5, 20.0), 0.0)
    a = s.add_entity("mover", "seek", p0, math.sqrt(8.0), goal)
    wallp = ((11.0 + 2 * fraction, 1.5, 11.0) if axis == "x" else
             (11.0, 1.5, 11.0 + 2 * fraction))
    b = s.add_entity("wall", "wander", wallp, 0.0)
    s.set_entity_collision_box(a, (0.5, 0.5, 0.5))
    s.set_entity_collision_box(b, ((0.5, 0.5, 6.0) if axis == "x" else
                                   (6.0, 0.5, 0.5)), static=True)
    s.step()
    out = s.entities[a]
    # Collision removes only normal motion after contact. Tangential displacement
    # is velocity*toi + velocity*(1-toi), hence remains exactly 2.
    expected = ((10 + 2 * fraction, 1.5, 12.0) if axis == "x" else
                (12.0, 1.5, 10 + 2 * fraction))
    return {"fraction": fraction, "normal_axis": axis, "actual": out.pos,
            "expected": expected, "velocity": out.velocity,
            "contacts": s.collision_report()["contacts"],
            "correct": all(math.isclose(a, b, abs_tol=1e-12)
                           for a, b in zip(out.pos, expected))}


def fall(n_boxes):
    s = SceneSimulator(size=64, ground_level=1, seed=11)
    s.set_environment(gravity=10.0, dt=0.1)
    a = s.add_entity("ball", "wander", (10.0, 100.0, 10.0), 0.0)
    b = s.add_entity("wall", "wander", (40.0, 100.0, 40.0), 0.0)
    s.entities[a].attrs["physics"] = PHYSICS_DYNAMICS
    s.set_entity_physics(a, p0=(10.0, 100.0, 10.0), v0=(1.0, 0.0, 0.0))
    if n_boxes:
        s.set_entity_collision_box(a, (0.25, 0.25, 0.25))
    if n_boxes == 2:
        s.set_entity_collision_box(b, (0.25, 0.25, 0.25), static=True)
    rows = []
    for tick in range(1, 11):
        s.step()
        t = tick * 0.1
        e = s.entities[a]
        expected_pos = (10 + t, 100 - 5 * t * t, 10.0)
        expected_vel = (1.0, -10 * t, 0.0)
        rows.append({"tick": tick, "actual_pos": e.pos, "expected_pos": expected_pos,
                     "actual_vel": e.velocity, "expected_vel": expected_vel,
                     "readout_vel": e.attrs["physics_readout"]["vel"],
                     "hit": [c["hit"] for c in s.collision_report()["contacts"]],
                     "correct_pos": all(math.isclose(x, y, abs_tol=1e-10)
                                        for x, y in zip(e.pos, expected_pos)),
                     "correct_vel": all(math.isclose(x, y, abs_tol=1e-10)
                                        for x, y in zip(e.velocity, expected_vel))})
    return {"n_boxes": n_boxes, "rows": rows,
            "state": s.entities[a].attrs["physics_state"]}


if __name__ == "__main__":
    data = {"upstream": "d74848fb33dbff1d719959df19d1266a1ac60f44",
            "sliding": [slide(t, axis) for axis in ("x", "z")
                        for t in (0.0, 0.25, 0.5, 0.75, 1.0)],
            "free_fall": [fall(k) for k in (0, 1, 2)]}
    p = Path(__file__).with_suffix(".json")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
