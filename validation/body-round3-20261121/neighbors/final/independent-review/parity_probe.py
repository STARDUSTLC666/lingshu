"""Independent integer parity table, including coordinates above float precision."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(r"<repo>")
sys.path.insert(0, str(ROOT))
from lingshu.nn.hex_cnn import HexGrid

EVEN = [(1, 0), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
ODD = [(1, 0), (1, -1), (0, -1), (-1, 0), (0, 1), (1, 1)]
AXIAL = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
rows = list(range(-1000, 1001)) + [-(2**60), -(2**60) + 1, 2**60, 2**60 + 1]
checks = 0
for mode in ("axial", "odd_r_offset"):
    grid = HexGrid(1, 1, mode=mode)
    for r in rows:
        for q in (-2**60, -17, 0, 17, 2**60):
            offsets = AXIAL if mode == "axial" else (ODD if r % 2 else EVEN)
            expected = [(q + dq, r + dr) for dq, dr in offsets]
            assert grid.neighbors(q, r) == expected, (mode, q, r)
            checks += 1
print(json.dumps({"verdict": "PASS", "cases": checks, "source_lf_sha256":
                  hashlib.sha256((ROOT / "lingshu/nn/hex_cnn.py").read_bytes().replace(
                      b"\r\n", b"\n")).hexdigest()}))
