import contextlib
import json
import os
from pathlib import Path
import sys
import warnings

warnings.filterwarnings("ignore")
BASE = Path(r"[workspace]/lingshu/work\lingshu-audit-core-20261120")
OUT = Path(r"[workspace]/lingshu/outputs\body-round2-20261120\audit-core")
sys.path.insert(0, str(BASE))

import numpy as np
import scipy
from lingshu.core.core import SpacetimeMemoryEngine, ConditionSpace, EdgeType, STNode
from lingshu.core import activation

CS = ConditionSpace("same", "same", (100.0, 101.0), "same")
original_csr = activation.csr_matrix


def run(backend, cyclic=False, repeats=1):
    activation.csr_matrix = original_csr if backend == "scipy" else None
    stem = f"parallel-{backend}-{'cycle' if cyclic else 'single'}"
    db = OUT / f"{stem}.db"
    if db.exists():
        raise RuntimeError(f"refusing to overwrite {db}")
    e = SpacetimeMemoryEngine(str(db))
    try:
        for nid, content in (("source", "独有源信号"), ("target", "无关目标内容")):
            e.store.add_node(STNode(id=nid, content=content, modality="text",
                spatial_coordinates={}, temporal_coordinate=100.0, condition_space=CS))
        directions = [("source", "target")]
        if cyclic:
            directions.append(("target", "source"))
        edges = []
        for a, b in directions:
            for relation in (EdgeType.CAUSAL, EdgeType.SIMILAR):
                edge = e.add_edge(a, b, relation_type=relation, condition_space=CS)
                edges.append({"source": a, "target": b, "relation": relation.value,
                              "merged": edge.merged})
        eng = activation.ActivationEngine(store=e.store, audit_path=str(OUT / f"{stem}.jsonl"))
        states = []
        for _ in range(repeats):
            result = eng.activate("独有源信号", workset="audit", hops=2 if cyclic else 1,
                                  self_condition=0.5 if cyclic else 0.0)
            states.append({"result": result, "state": eng.carry_vector("audit")})
        return {"backend": backend, "cyclic": cyclic, "edges": edges,
                "seed_bound": 1.0, "expected_first_target": 0.85, "states": states}
    finally:
        e.close()


result = {"baseline": "d74848fb33dbff1d719959df19d1266a1ac60f44",
          "python": sys.version, "numpy": np.__version__, "scipy": scipy.__version__,
          "cases": [run("scipy"), run("edge-list"), run("scipy", True, 6),
                    run("edge-list", True, 6)]}
activation.csr_matrix = original_csr
path = OUT / "parallel-activation-results.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
