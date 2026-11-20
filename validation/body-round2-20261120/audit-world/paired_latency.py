"""Supplement the isolated-job benchmark with adjacent randomized pairs."""
from pathlib import Path
import gc
import hashlib
import importlib.util
import json
import random
import statistics
import sys
import time

repo = Path(r"[workspace]/lingshu/work\lingshu-body-collision-velocity-20261120")
sys.path.insert(0, str(repo))
spec = importlib.util.spec_from_file_location("scene_bench_helpers", repo / "bench/bench_scene_collision_freeflight.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
modules = {}
for key in ("baseline", "fixed"):
    path = Path(__file__).with_name("benchmark-r2") / "sources" / (key + ".py")
    name = "lingshu.world._latency_probe_" + key
    module_spec = importlib.util.spec_from_file_location(name, path)
    modules[key] = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = modules[key]
    module_spec.loader.exec_module(modules[key])
rng = random.Random(424242)
rows = []
for case in bench.CASES:
    readings = {key: [] for key in modules}
    order_log = []
    for trial in range(12):
        order = list(modules)
        rng.shuffle(order)
        order_log.append(order)
        for key in order:
            scene, expected = bench.build(modules[key], case)
            gc.collect()
            gc.disable()
            start = time.perf_counter_ns()
            scene.step(80)
            elapsed = (time.perf_counter_ns() - start) / 1e9
            gc.enable()
            if trial:
                readings[key].append(elapsed)
            result = bench.oracle(scene, expected, 80)
            if key == "fixed":
                assert not result["failures"]
    medians = {key: statistics.median(vals) for key, vals in readings.items()}
    row = {"case": case, "seconds": readings, "medians": medians,
           "fixed_over_baseline": medians["fixed"] / medians["baseline"],
           "order": order_log}
    rows.append(row)
    print(json.dumps(row), flush=True)
out = {"method": "adjacent randomized pair seed424242; same process and shared unchanged dependencies; setup excluded; 1 warmup +11 timed pairs; GC disabled equally",
       "source_sha256_lf": {key: hashlib.sha256((Path(__file__).with_name("benchmark-r2") / "sources" / (key + ".py")).read_bytes()).hexdigest() for key in modules},
       "cases": rows}
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
