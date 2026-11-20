"""Independent reviewer sweep of root's circular-fit patch; no repo writes."""
from pathlib import Path
import hashlib
import itertools
import json
import math
import subprocess
import sys

root = Path(r"[workspace]/lingshu/work\lingshu-body-circular-time-20261120")
sys.path.insert(0, str(root))
from lingshu.world import physics as p

times = (0., .125, .375, .5, .875, 1.125, 1.5, 2., 2.25, 2.5)
def oracle(t, up, radius, phase, omega, drift):
    horizontal = [i for i in range(3) if i != up]
    position = [0., 0., 0.]
    velocity = [0., 0., 0.]
    theta = phase + omega * t
    position[horizontal[0]] = 2. + radius * math.cos(theta)
    position[horizontal[1]] = -3. + radius * math.sin(theta)
    position[up] = 5. + drift * t
    velocity[horizontal[0]] = -radius * omega * math.sin(theta)
    velocity[horizontal[1]] = radius * omega * math.cos(theta)
    velocity[up] = drift
    return tuple(position), tuple(velocity)

failures = []
assertions = 0
max_error = 0.
count = 0
for up, radius, phase, omega, epoch, drift in itertools.product(
        range(3), (.5, 2., 5.), (-2.5, -.1, 1.7), (-1.25, .5, 1.75),
        (-1073741824., 0., 1073741824.), (-2., 0., 2.)):
    count += 1
    args = (up, radius, phase, omega, drift)
    samples = [(epoch + t, oracle(t, *args)[0]) for t in times]
    model = p.fit_model("circular", samples, up=up)
    for tau in (-.25, .625, 3.25):
        actual = p.predict_at(model, epoch + tau)
        expected = oracle(tau, *args)
        for field, av, ev in zip(("position", "velocity"), actual, expected):
            assertions += 1
            error = max(abs(a - b) for a, b in zip(av, ev))
            max_error = max(max_error, error)
            if error > 1e-8:
                failures.append({"args": args, "epoch": epoch, "tau": tau,
                                 "field": field, "actual": av, "expected": ev})
noisy_cases = 0
classifications = []
for up, acceleration, noise in itertools.product(range(3), (-20., -2., 0., 2., 20.), (0., .015)):
    observed = []
    for i, t in enumerate(times):
        q = list(oracle(t, up, 2., .4, 1.5, 2.)[0])
        for axis in range(3):
            q[axis] += noise * math.sin((i + 1) * (axis + 1) * .7)
        q[up] += acceleration * t * t / 2
        observed.append((t, tuple(q)))
    kinds = []
    for epoch in (-1073741824., 0., 1073741824.):
        samples = [(t + epoch, q) for t, q in observed]
        model = p.fit_circular(samples, up=up)
        expected_rms = math.sqrt(math.fsum(math.dist(p.predict_at(model, t)[0], q) ** 2
                                         for t, q in samples) / (3 * len(samples)))
        assertions += 1
        noisy_cases += 1
        if not math.isclose(model["residual_rms"], expected_rms, rel_tol=1e-9, abs_tol=1e-12):
            failures.append({"type": "rms", "up": up, "acceleration": acceleration,
                             "noise": noise, "epoch": epoch, "actual": model["residual_rms"],
                             "expected": expected_rms})
        kinds.append(p.classify(samples, up=up)["kind"])
    assertions += 1
    if len(set(kinds)) != 1:
        failures.append({"type": "classify_epoch", "up": up, "acceleration": acceleration,
                         "noise": noise, "kinds": kinds})
    classifications.append({"up": up, "acceleration": acceleration, "noise": noise, "kind": kinds[0]})
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
out = {"head": head, "physics_sha256_lf": hashlib.sha256((root / "lingshu/world/physics.py").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
       "scenes": count, "noisy_rms_cases": noisy_cases, "classifications": classifications,
       "assertions": assertions, "failures": failures,
       "max_component_error": max_error,
       "scope": "irregular binary-exact times; all up axes; radius/phase/direction/drift/time-origin sweeps; no position noise or turn aliasing"}
Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
assert not failures
