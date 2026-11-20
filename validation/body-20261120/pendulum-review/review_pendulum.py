"""Independent, stdlib-only pendulum review; writes raw JSON and text artifacts.

Run with the exact Python interpreter named in review_results.json:
  python -X utf8 review_pendulum.py --repo <reviewed checkout> --output <this folder>
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import subprocess
import sys
import types


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout


def lf_sha(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def independent_quarter_period(theta0):
    # Complementary-modulus AGM computed locally, not by the production helper.
    a, b = 1.0, math.cos(theta0 / 2)
    for _ in range(50):
        a, b = (a + b) / 2, math.sqrt(a * b)
    return math.pi / (2 * a)


def independent_rk4_release(theta0, elapsed, dt=0.00025):
    # The physical ODE theta'' = -sin(theta), independent of elliptic identities.
    steps = max(1, math.ceil(abs(elapsed) / dt))
    step = elapsed / steps
    theta, velocity = theta0, 0.0
    for _ in range(steps):
        a1, b1 = velocity, -math.sin(theta)
        a2 = velocity + step * b1 / 2
        b2 = -math.sin(theta + step * a1 / 2)
        a3 = velocity + step * b2 / 2
        b3 = -math.sin(theta + step * a2 / 2)
        a4 = velocity + step * b3
        b4 = -math.sin(theta + step * a3)
        theta += step * (a1 + 2 * a2 + 2 * a3 + a4) / 6
        velocity += step * (b1 + 2 * b2 + 2 * b3 + b4) / 6
    return theta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_path = repo / "lingshu/world/physics.py"
    reviewed_bytes = source_path.read_bytes()
    sys.path.insert(0, str(repo))
    from lingshu.world import physics as P

    baseline_sha = git(repo, "rev-parse", "origin/main").decode().strip()
    baseline_source = git(repo, "show", baseline_sha + ":lingshu/world/physics.py")
    baseline = types.ModuleType("independent_baseline_physics")
    sys.modules[baseline.__name__] = baseline
    exec(compile(baseline_source.decode("utf-8"), "baseline_physics.py", "exec"), baseline.__dict__)

    records = {}
    checks = []

    def check(name, actual_records):
        records[name] = actual_records
        failed = [i for i, row in enumerate(actual_records) if not row["passed"]]
        checks.append({"name": name, "cases": len(actual_records), "failed_case_indices": failed,
                       "passed": not failed})

    cn_records = []
    rng = random.Random(113)
    for index in range(3000):
        k = rng.uniform(-0.9999999999, 0.9999999999)
        u = rng.uniform(-1e4, 1e4)
        actual, expected = P.jacobi_cn(u, k), baseline.jacobi_cn(u, k)
        cn_records.append({"index": index, "u": u, "k": k, "actual": actual,
                           "baseline": expected, "absolute_error": abs(actual - expected),
                           "passed": actual == expected})
    check("public_jacobi_cn_bitwise_compatibility", cn_records)

    signed_records = []
    for theta0 in (0.0, 0.3, -0.3, math.radians(120), -math.radians(179.99999),
                   math.nextafter(math.pi, 0.0)):
        for omega in (0.0, -1.0, 1.0, -3.7, 3.7):
            for elapsed in (0.0, 0.5, -0.5, 1.0, -1.0, 10.1, -10.1, 100.0, -100.0):
                actual = P.pendulum_exact_angle(theta0, omega, elapsed)
                expected = P.pendulum_exact_angle(theta0, abs(omega), abs(elapsed))
                error = abs(actual - expected)
                signed_records.append({"theta0": theta0, "omega": omega, "time": elapsed,
                                       "actual": actual, "symmetric_expected": expected,
                                       "absolute_error": error, "passed": error < 1e-14})
    check("signed_omega_and_time_symmetry", signed_records)

    phase_records = []
    initial_values = [sign * math.radians(deg)
                      for deg in (0.01, 1, 30, 120, 170, 179, 179.9, 179.99999)
                      for sign in (-1.0, 1.0)]
    initial_values.append(math.nextafter(math.pi, 0.0))
    for theta0 in initial_values:
        quarter = independent_quarter_period(theta0)
        for multiple in range(-20, 21):
            expected = (theta0, 0.0, -theta0, 0.0)[multiple % 4]
            actual = P.pendulum_exact_angle(theta0, 1.0, multiple * quarter)
            error = abs(actual - expected)
            phase_records.append({"theta0": theta0, "quarter_period": quarter,
                                  "quarter_multiple": multiple, "actual": actual,
                                  "expected": expected, "absolute_error": error,
                                  "passed": error < 5e-13})
    check("quarter_period_and_turning_point_truth", phase_records)

    rk4_records = []
    rng = random.Random(9712)
    for index in range(36):
        theta0 = rng.uniform(-math.radians(175), math.radians(175))
        elapsed = rng.uniform(-20, 20)
        expected = independent_rk4_release(theta0, elapsed)
        actual = P.pendulum_exact_angle(theta0, 1.0, elapsed)
        error = abs(actual - expected)
        rk4_records.append({"index": index, "theta0": theta0, "time": elapsed,
                             "actual": actual, "rk4_expected": expected,
                             "absolute_error": error, "passed": error < 2e-10})
    check("independent_random_rk4", rk4_records)

    invalid_records = []
    for index in range(4):
        for value_name, value in (("nan", float("nan")), ("inf", float("inf")),
                                  ("-inf", -float("inf")), ("bool", True)):
            parameters = [0.5, 1.0, 0.25, 180.0]
            parameters[index] = value
            exception_type, message = None, None
            try:
                result = P.pendulum_exact_angle(*parameters)
            except Exception as exc:
                exception_type, message = type(exc).__name__, str(exc)
            invalid_records.append({"argument_index": index, "invalid_value": value_name,
                                    "exception_type": exception_type, "message": message,
                                    "passed": exception_type == "PhysicsError"})
    for theta0 in (-2 * math.pi, -math.pi, math.pi, 2 * math.pi):
        exception_type, message = None, None
        try:
            P.pendulum_exact_angle(theta0, 1.0, 1.0)
        except Exception as exc:
            exception_type, message = type(exc).__name__, str(exc)
        invalid_records.append({"out_of_domain_theta0": theta0, "exception_type": exception_type,
                                "message": message, "passed": exception_type == "PhysicsError"})
    check("invalid_and_absolute_physical_domain", invalid_records)

    after_bytes = source_path.read_bytes()
    source_unchanged = reviewed_bytes == after_bytes
    checks.append({"name": "reviewed_source_did_not_change_during_review", "cases": 1,
                   "failed_case_indices": [] if source_unchanged else [0], "passed": source_unchanged})
    passed = all(row["passed"] for row in checks)
    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
        "reviewer": "independent read-only subagent",
        "repo": str(repo), "git_head": git(repo, "rev-parse", "HEAD").decode().strip(),
        "git_status": git(repo, "status", "--short").decode("utf-8"),
        "baseline_sha": baseline_sha,
        "baseline_physics_sha256_lf": lf_sha(baseline_source),
        "reviewed_source": "lingshu/world/physics.py",
        "reviewed_physics_sha256_lf": lf_sha(reviewed_bytes),
        "reviewed_physics_sha256_raw": hashlib.sha256(reviewed_bytes).hexdigest(),
        "review_script_sha256_lf": lf_sha(Path(__file__).read_bytes()),
        "seeds": {"cn_compatibility": 113, "rk4_random": 9712},
        "reference_parameters": {"rk4_step_max": 0.00025, "rk4_error_limit": 2e-10,
                                 "phase_error_limit": 5e-13, "symmetry_error_limit": 1e-14},
        "boundary": "Sampled and analytic-phase checks, not a uniform error guarantee for arbitrarily large floating times.",
        "checks": checks, "passed": passed,
    }
    payload = {"metadata": metadata, "records": records}
    (output / "review_results.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["Independent pendulum review", "UTC: " + metadata["generated_utc"],
             "Git HEAD: " + metadata["git_head"], "Baseline: " + baseline_sha,
             "Reviewed physics.py LF SHA256: " + metadata["reviewed_physics_sha256_lf"],
             "Script LF SHA256: " + metadata["review_script_sha256_lf"],
             "Seeds: cn=113; RK4=9712", ""]
    for check_result in checks:
        name = check_result["name"]
        lines.append("%s: %s (%d cases)" % (name, "PASS" if check_result["passed"] else "FAIL",
                                               check_result["cases"]))
        if name in records and records[name] and "absolute_error" in records[name][0]:
            lines.append("  maximum absolute error = %.17g" % max(row["absolute_error"] for row in records[name]))
    lines.extend(["", "Overall: " + ("PASS" if passed else "FAIL"), metadata["boundary"],
                  "Raw case inputs, outputs, errors, exceptions and metadata: review_results.json"])
    summary = "\n".join(lines) + "\n"
    (output / "review_results.txt").write_text(summary, encoding="utf-8")
    print(summary)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
