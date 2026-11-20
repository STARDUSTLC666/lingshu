"""Read-only public API evidence for spatial_detect's incomplete partition."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(r"[workspace]/lingshu/work\lingshu-audit-core-20261120")
sys.path.insert(0, str(ROOT))
from lingshu.nn.hex_cnn import image_to_grid
from lingshu.nn.hex_hier import HexHierNet, OBJ
from lingshu.nn.hex_text import spatial_detect, multimodal_check, fuse_consistency, parse_description

OUT = Path(__file__).parent


def transparent_color_net():
    net = HexHierNet(n_kernels=1, stacked=False)
    vec = net.get_vec()
    vec[:] = 0
    vec[0] = 1.0  # center-only spatial operator; no boundary leakage
    head = vec[7:].reshape(net.head.shape)
    for color, i in (("red", 0), ("green", 1), ("blue", 2)):
        head[OBJ.index("circle|" + color), 1 + i] = 100
    net.set_vec(vec)
    return net


def balanced_detect(net, lat):
    """Independent partition oracle, not a proposed source patch.

    Every index is assigned to exactly one of 3 contiguous blocks with
    boundaries floor(q*axis_size/3), including the final row and column.
    Existing production semantic model is reused for classification only.
    """
    r, c = lat.shape[1:3]
    energy, _ = net.l1(lat)
    w = np.abs(energy).sum(axis=-1)
    cells = [(q, slice((q//3)*r//3, ((q//3)+1)*r//3),
              slice((q%3)*c//3, ((q%3)+1)*c//3)) for q in range(9)]
    shares = np.array([w[0, sy, sx].sum() for _, sy, sx in cells])
    shares /= shares.sum() + 1e-9
    keep = {int(shares.argmax())} | {q for q in range(9) if shares[q] > 1/9*1.15}
    result = []
    for q, sy, sx in cells:
        if q not in keep:
            continue
        sf, cf = net.l2_features(lat[:, sy, sx])
        logits = net.l3_logits(sf, cf)[0]
        result.append({"pos": f"r{q}", "obj": OBJ[int(logits.argmax())],
                       "share": round(float(shares[q]), 3)})
    return result


def run():
    net = transparent_color_net()
    records = []
    for rows, cols, rr, cc in ((4,4,3,3), (6,7,5,6), (7,6,6,5),
                               (18,16,9,15), (18,16,9,14), (6,6,5,5)):
        lat = np.zeros((1, rows, cols, 3), dtype=np.float64)
        lat[0, rr, cc, 2] = 1
        band_r = next(q for q in range(3) if q*rows//3 <= rr < (q+1)*rows//3)
        band_c = next(q for q in range(3) if q*cols//3 <= cc < (q+1)*cols//3)
        records.append({"type":"lattice", "shape":list(lat.shape),
                        "blue_cell":[rr,cc], "balanced_zone":f"r{band_r*3+band_c}",
                        "actual":spatial_detect(net,lat)[0],
                        "balanced_partition":balanced_detect(net,lat)})
    for cells_across in (16,17,19,23):
        image = np.zeros((48,48,3), dtype=np.uint8)
        image[:, -1:, 2] = 255
        lattice, grid = image_to_grid(image, cells_across=cells_across)
        lat = lattice[None] / 255
        nonzero = np.argwhere(lattice[...,2] > 0)
        records.append({"type":"image_to_grid", "image_shape":list(image.shape),
                        "blue_pixels":"entire final image column", "cells_across":cells_across,
                        "shape":list(lat.shape), "nonzero_cells":nonzero.tolist(),
                        "actual":spatial_detect(net,lat)[0],
                        "balanced_partition":balanced_detect(net,lat),
                        "multimodal_actual":multimodal_check(net,lat,"右中有蓝色圆形"),
                        "multimodal_balanced":fuse_consistency(parse_description("右中有蓝色圆形"),balanced_detect(net,lat))})
    report = {"source_commit":"d74848fb33dbff1d719959df19d1266a1ac60f44",
              "source_sha256":hashlib.sha256((ROOT/'lingshu/nn/hex_text.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
              "numpy":np.__version__, "records":records}
    (OUT/'spatial_partition_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    run()
