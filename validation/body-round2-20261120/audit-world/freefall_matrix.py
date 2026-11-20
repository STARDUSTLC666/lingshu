"""Independent analytic free-fall matrix; only public scene APIs."""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, r"[workspace]/lingshu/work\lingshu-audit-core-20261120")
from lingshu.world.scene_simulator import SceneSimulator, PHYSICS_DYNAMICS


def run(dt, g, n, n_boxes):
    s = SceneSimulator(size=64, seed=42)
    s.set_environment(gravity=g, dt=dt)
    a = s.add_entity("ball", "wander", (10., 10000., 10.), 0.)
    b = s.add_entity("wall", "wander", (40., 10000., 40.), 0.)
    s.entities[a].attrs["physics"] = PHYSICS_DYNAMICS
    s.set_entity_physics(a, p0=(10., 10000., 10.), v0=(.25, .5, 0.))
    if n_boxes >= 1:
        s.set_entity_collision_box(a, (.25, .25, .25))
    if n_boxes >= 2:
        s.set_entity_collision_box(b, (.25, .25, .25), static=True)
    bad_p = bad_v = hits = 0
    max_p = max_v = 0.
    for tick in range(1, n + 1):
        s.step()
        e = s.entities[a]
        t = tick * dt
        true_p = (10. + .25 * t, 10000. + .5 * t - g * t * t / 2., 10.)
        true_v = (.25, .5 - g * t, 0.)
        ep = max(abs(x - y) for x, y in zip(e.pos, true_p))
        ev = max(abs(x - y) for x, y in zip(e.velocity, true_v))
        max_p, max_v = max(max_p, ep), max(max_v, ev)
        bad_p += ep > 1e-7
        bad_v += ev > 1e-7
        hits += sum(c["hit"] for c in s.collision_report()["contacts"])
    return {"dt": dt, "g": g, "n": n, "boxes": n_boxes,
            "bad_position_ticks": bad_p, "bad_velocity_ticks": bad_v,
            "max_position_error": max_p, "max_velocity_error": max_v,
            "true_last_y": true_p[1], "last_y": e.pos[1],
            "true_last_vy": true_v[1], "last_vy": e.velocity[1], "hits": hits}


matrix = [run(dt, g, 10, k) for k in (0, 1, 2)
          for dt in (.01, .05, .1, .25, .5, 1.)
          for g in (.1, 1., 9.80665, 20.)]
convergence = [run(dt, 10., round(1. / dt), 2) for dt in (.1, .01, .001)]
summary = [{"boxes": k, "runs": sum(r["boxes"] == k for r in matrix),
            "bad_position_ticks": sum(r["bad_position_ticks"] for r in matrix if r["boxes"] == k),
            "bad_velocity_ticks": sum(r["bad_velocity_ticks"] for r in matrix if r["boxes"] == k),
            "collision_hits": sum(r["hits"] for r in matrix if r["boxes"] == k)} for k in (0, 1, 2)]
out = {"summary": summary, "matrix": matrix, "convergence": convergence}
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"summary": summary, "convergence": convergence}, indent=2))
