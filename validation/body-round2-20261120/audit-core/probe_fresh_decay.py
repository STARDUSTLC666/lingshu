import json
import math
from pathlib import Path
import sys
import time
import warnings

BASE = Path(r"[workspace]/lingshu/work\lingshu-audit-core-20261120")
OUT = Path(r"[workspace]/lingshu/outputs\body-round2-20261120\audit-core")
sys.path.insert(0, str(BASE))
warnings.filterwarnings("ignore")

from lingshu.core.core import SpacetimeMemoryEngine, EdgeType

db = OUT / "fresh-decay.db"
if db.exists():
    raise RuntimeError(f"refusing to overwrite {db}")
e = SpacetimeMemoryEngine(str(db))
try:
    prior_tick = time.time() - 7 * 86400
    # Explicit time-mode maintenance on an empty context/knowledge graph.
    e.decay_cycle(now=prior_tick)
    # Normal public creation APIs at the actual present time.
    context = e.add_context("just received live context", importance=0.5)
    premise = e.add_perception("live source event", skip_dedup=True)
    conclusion = e.add_perception("unrelated fresh observation", skip_dedup=True)
    edge = e.add_edge(premise.id, conclusion.id, EdgeType.CAUSAL)
    birth = {"context": context.created_at, "premise": premise.created_at,
             "edge": edge.created_at}
    now = time.time()
    result = {"baseline": "d74848fb33dbff1d719959df19d1266a1ac60f44",
              "prior_tick": prior_tick, "now": now, "birth": birth,
              "ages_seconds": {k: now-v for k,v in birth.items()},
              "before": {"context": e.store.get_node(context.id).importance,
                         "premise": e.store.get_node(premise.id).confidence,
                         "edge": e.store.get_edge(edge.id).confidence}}
    e.decay_cycle(now=now)
    c, p, d = e.store.get_node(context.id), e.store.get_node(premise.id), e.store.get_edge(edge.id)
    result["after"] = {"context": c.importance if c else None,
                        "premise": p.confidence if p else None,
                        "edge": d.confidence if d else None}
    # Independent closed-form oracle: no state may age before it exists.
    result["oracle"] = {k: .5 * .98 ** ((now-max(prior_tick,v))/60) for k,v in birth.items()}
    result["expected_global_old_value"] = .5 * .98 ** ((now-prior_tick)/60)
    result["cursor"] = e.store.get_meta("_last_decay_at")
    (OUT / "fresh-decay-results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
finally:
    e.close()
