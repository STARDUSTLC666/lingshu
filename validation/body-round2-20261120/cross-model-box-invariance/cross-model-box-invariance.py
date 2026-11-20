"""Public box-registration invariance across the supported environment families.

This supplemental metamorphic check complements the independent analytic
freefall oracle; it does not claim that one simulator validates its own physics.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    from lingshu.world.scene_simulator import PHYSICS_DYNAMICS, SceneSimulator
    from lingshu.world import physics
    rows, errors = [], []
    families = {"projectile": {}, "drag2": {"drag_c": 0.5, "mass": 2.5},
                "slope_friction": {"slope_deg": 20.0, "mu_s": 0.15, "mu_k": 0.1},
                "rolling": {"slope_deg": 20.0, "mu_s": 0.15, "mu_k": 0.1}}
    checks, scenes, ticks = 0, 0, 0
    for family, options in families.items():
        for up in range(3):
            for dt in (0.01, 0.05, 0.2):
                controls = []
                for boxes in (0, 1, 2):
                    scenes += 1
                    sim = SceneSimulator(size=128, seed=42)
                    sim.set_environment(gravity=10.0, dt=dt, up=up,
                                        incline_axis=(up + 1) % 3, **options)
                    ball = sim.add_entity("ball", "wander", (64.0, 1000.0, 64.0), 0.0)
                    wall = sim.add_entity("wall", "wander", (115.0, 1000.0, 115.0), 0.0)
                    sim.entities[ball].attrs["physics"] = PHYSICS_DYNAMICS
                    kw = {"beta": 0.4, "radius": 0.3} if family == "rolling" else {}
                    sim.set_entity_physics(ball, v0=(0.25, 0.5, -0.1), mass=2.5, **kw)
                    if boxes:
                        sim.set_entity_collision_box(ball, (0.25, 0.25, 0.25))
                    if boxes > 1:
                        sim.set_entity_collision_box(wall, (0.25, 0.25, 0.25), static=True)
                    snapshots = []
                    for tick in range(1, 7):
                        ticks += 1
                        sim.step()
                        e = sim.entities[ball]
                        snapshots.append({"pos": e.pos, "vel": e.velocity,
                                          "state": dict(e.attrs["physics_state"]),
                                          "kind": e.attrs["physics_readout"]["kind"]})
                        checks += 2
                        if e.attrs["physics_readout"]["kind"] != family:
                            errors.append([family, up, dt, boxes, tick, "unexpected family"])
                        if any(c["hit"] for c in sim.collision_report()["contacts"]):
                            errors.append([family, up, dt, boxes, tick, "contact invalidates premise"])
                    if boxes == 0:
                        controls = snapshots
                    else:
                        for tick, (expected, actual) in enumerate(zip(controls, snapshots), 1):
                            for field in ("pos", "vel", "state", "kind"):
                                checks += 1
                                if actual[field] != expected[field]:
                                    errors.append([family, up, dt, boxes, tick, field])
                    rows.append({"family": family, "up": up, "dt": dt, "boxes": boxes,
                                 "snapshots": snapshots})
    source = args.source.resolve()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source,
                                     text=True, encoding="utf-8", errors="replace").strip()
    result = {"source_sha": commit, "imported_physics_path": physics.__file__,
              "physics_sha256_lf": hashlib.sha256(Path(physics.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
              "scenes": scenes, "ticks": ticks, "checks": checks, "failures": len(errors),
              "errors": errors, "rows": rows,
              "scope": "Metamorphic 0/1/2-box equality, complementing independent analytic tests; no claim of exhaustive physics accuracy."}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "errors")}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
