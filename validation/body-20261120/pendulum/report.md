# Pendulum independent validation

Fixed LF-normalized source SHA-256: 271d2bb9d24452e3724e3ee0375b2d4fd9e04e85bbc4b62fd5afbd39b925f904

Baseline: d74848fb33dbff1d719959df19d1266a1ac60f44

Reference: mpmath 1.4.1 at 80 decimal digits, theta=2 asin(k sn(K-u,m)), m=k², k=sin(theta0/2), K=ellipk(m). Each binary64 input is promoted exactly before the high-precision product. This does not reuse production AGM/Landen code.

Accuracy summary:

- short_cases: 930
- long_cases: 40
- fixed_checks: 6550
- fixed_violations: 0
- short_max_abs_error_rad: 3.6751313186491484e-13
- short_3_375_period_max_abs_error_rad: 2.81987574748944e-14
- baseline_numeric_cases: 750
- baseline_exceptions: 180
- baseline_max_abs_error_rad: 3.1297763126665865

| Amplitude | Through 100.3 periods: max error rad | Through 3.375 periods: max error rad |
|---|---:|---:|
| zero | 0 | 0 |
| tiny | 2.81612e-26 | 5.71473e-28 |
| 0.001deg | 1.49894e-18 | 3.92544e-20 |
| 1deg | 9.61839e-16 | 1.16849e-17 |
| 5deg | 6.05838e-15 | 1.23441e-16 |
| 15deg | 2.12828e-15 | 9.37447e-17 |
| 30deg | 1.43829e-14 | 2.04038e-16 |
| 60deg | 3.78953e-14 | 1.16693e-15 |
| 90deg | 1.89564e-13 | 3.95283e-15 |
| 120deg | 2.52838e-13 | 6.473e-15 |
| 170deg | 1.29891e-13 | 1.0455e-15 |
| 179deg | 3.67513e-13 | 7.97059e-15 |
| 179.999deg | 1.77668e-13 | 9.05904e-15 |
| 179.99999999deg | 5.54512e-14 | 2.81988e-14 |
| pi_minus_1e-12 | 2.44917e-14 | 2.44917e-14 |
| nextafter_pi | 1.30507e-14 | 1.30507e-14 |

Long horizons: input product rounding and approximate-period reduction limit phase accuracy. The analytical speed bound |dtheta/du|<=2|k| yields |angle error|<=2|k| times circular phase error plus the sampled evaluation allowance 5e-12 rad. This is a checked sample decomposition, not a global floating-point proof.

| Target cycles | Max angle error rad | Max circular phase error u | Max intrinsic error at implemented phase rad |
|---:|---:|---:|---:|
| 1e+03 | 2.12126e-12 | 7.59682e-12 | 3.81541e-16 |
| 1e+06 | 1.55641e-09 | 6.03936e-09 | 2.94728e-16 |
| 1e+09 | 1.60454e-06 | 6.03936e-06 | 3.73948e-16 |
| 1e+12 | 0.00196035 | 0.0184778 | 5.05079e-16 |
| 1e+15 | 0.423473 | 12.3185 | 4.96483e-16 |

RK4: 70 signed-time cases, fine max error 3.01904e-10 rad; fixed max error 4.9508e-15 rad; fine errors >1e-8: 0. Energy and coarse/fine samples are retained in rk4_raw.json.

Binary64 RK4 near nextafter(pi,0): {"theta0_rad": 3.1415926535897927, "u": 37.1864010120653, "rk4_theta": 3.1415926535897927, "reference_rad": "0.000000000000001628239861799905406461040720106891064646710181017811966153685145802703951810540292036", "rk4_error_rad": 3.141592653589791, "note": "Characterization only: binary64 RK4 can stall near the turning point; the 80-digit elliptic oracle remains the accuracy reference."}

Timing (microseconds per 16-angle batch; 5 warmups, 21 retained samples, 128 batches/sample):

| Degrees / domain | Baseline median | Fixed median | Fixed p95 | Fixed / baseline |
|---|---:|---:|---:|---:|
| 1.0 / default | 59.552 | 231.002 | 250.245 | 3.879x |
| 5.0 / default | 60.529 | 228.119 | 270.234 | 3.769x |
| 30.0 / tol180 | 71.542 | 241.407 | 303.462 | 3.374x |
| 90.0 / tol180 | 89.561 | 267.030 | 313.247 | 2.982x |
| 120.0 / tol180 | 81.287 | 258.212 | 318.863 | 3.177x |
| 170.0 / tol180 | 94.498 | 303.954 | 355.520 | 3.217x |
| 179.999 / tol180 | 118.616 | 305.591 | 369.445 | 2.576x |

Limitations:

- Shared host, uncontrolled CPU affinity/power plan; descriptive medians/p95/spreads, no significance claim.
- Long-time phase errors are characterized, not hidden behind the short-horizon regression threshold.
- High-precision elliptic and RK4 checks are independent of production descent. Double RK4 cannot be the oracle at the nextafter-pi separatrix limit.
- No production source changes or database/network calls. Frozen source copies and exact hashes accompany every result.
- No dedicated memory claim: this scalar routine allocates short AGM lists, and latency/accuracy dominate this comparison.

Public jacobi_cn compatibility: 2165 deterministic inputs, 0 bitwise differences versus baseline.

Public pendulum_truth period: 69 independent high-precision comparisons, 0 failed; max relative error 2.81089e-16 and max absolute error 7.51967e-14 s. The reference uses the declared binary64 theta0_rad; exact-real degree conversion differences near the separatrix are separately retained in period_truth_raw.json.
