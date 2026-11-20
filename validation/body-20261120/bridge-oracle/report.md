# Independent public bridge quaternion oracle

Fixed eval.py LF SHA-256: f2b24ec11fbdef01d56c7d354ef247fc1bfdda9dfc14588f8830a3cf62b01aad

Reference: mpmath 1.4.1, 80 decimal digits, independent sn(K-u,m), with theta promoted from the declared binary64 degree-to-radian conversion. Only the public eval_at(spec, frame, motions=[...]) API supplies actual poses.

- Fixed: 2840 cases, 31240 assertions, 0 failures.
- Baseline: 2840 cases, 9990 assertions, 2799 failures (unsupported calls included).
- Fixed maximum angle error: 1.0887494e-12 rad.
- Fixed maximum quaternion component error: 5.44316467e-13.
- Maximum reference-angle shift from desired-time to actual frame/fps conversion: 1.80032733e-12 rad (recorded separately from solver error).

Coverage: 2,340 fixed-grid calls across all three axes; positive/negative initial angle and time; small through nextafter-pi initial amplitude; 500 extra seeded cases (350 ordinary plus 150 log-gap near-pi samples) through 100 periods. Properties cover quaternion normalization/canonical sign/axis mapping, fixed origin, repeated purity, unchanged inputs, even time and odd initial angle.

No Blender runtime, bpy, NumPy, Pillow, production DB, environment installation or network operation is used. Pure Python pose generation is verified; exported/Blender-rendered motion is outside this evidence. Dependency sources and exact hashes, every case, oracle and conversion term are retained in JSON. Scalar performance was measured separately by pendulum_release_accuracy.py.
