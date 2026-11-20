"""Independent helix trajectories and prediction residuals (no fit oracle reuse)."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys


def point(tau, up, acceleration=0.0):
    horizontal = [i for i in range(3) if i != up]
    p = [0.0] * 3
    p[horizontal[0]] = 2.0 + 2.0 * math.cos(0.4 + 1.5 * tau)
    p[horizontal[1]] = -1.0 + 2.0 * math.sin(0.4 + 1.5 * tau)
    p[up] = 3.0 + 2.0 * tau + 0.5 * acceleration * tau**2
    return tuple(p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source.resolve()))
    from lingshu.world import physics as p
    records = []
    for up in range(3):
        for epoch in (0.0, -10.0, 10.0, 1024.0, 1700000000.0):
            samples = [(epoch + i * 0.125, point(i * 0.125, up))
                       for i in range(25)]
            try:
                model = p.fit_model("circular", samples, up=up)
                predictions = [(t, p.predict_at(model, t)[0]) for t, _ in samples]
                errors = [max(abs(a - b) for a, b in zip(pred, obs))
                          for (_, pred), (_, obs) in zip(predictions, samples)]
                records.append({"up": up, "epoch": epoch, "center": model["center"],
                                "omega": model["omega"], "v_up": model["v_up"],
                                "max_prediction_error": max(errors),
                                "reported_rms": model["residual_rms"]})
            except Exception as exc:
                records.append({"up": up, "epoch": epoch,
                                "error": type(exc).__name__ + ": " + str(exc)})
    residual_records = []
    for up in range(3):
        for acceleration in (0.0, 2.0, 20.0):
            samples = [(i * 0.125, point(i * 0.125, up, acceleration))
                       for i in range(25)]
            model = p.fit_circular(samples, up=up)
            sqerr = sum(sum((predicted - observed) ** 2
                           for predicted, observed in zip(p.predict_at(model, t)[0], pos))
                        for t, pos in samples)
            selected = p.classify(samples, up=up)
            residual_records.append({"up": up, "vertical_acceleration": acceleration,
                                     "reported_rms": model["residual_rms"],
                                     "independent_3d_coordinate_rms": math.sqrt(sqerr / (3 * len(samples))),
                                     "max_point_error": max(math.dist(p.predict_at(model, t)[0], pos)
                                                            for t, pos in samples),
                                     "selected_kind": selected["kind"],
                                     "classification_residuals": selected["residuals"]})
    result = {"source_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.source, text=True,
        encoding="utf-8", errors="replace").strip(),
        "imported_module": p.__file__,
        "source_sha256": hashlib.sha256(Path(p.__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "helix": records,
        "vertical_residual": residual_records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
