# Complete manual physics gate: isolated parity

The exact original baseline gate and current PR gate ran separately and completely under their output sandboxes. Both physics imports and gate _evidence writes stayed in those sandboxes. No gate assertion or production source was modified.

| Variant | Gate exit | Passed rows | Failed rows | Failure tags | P4 RK4 maximum rad |
|---|---:|---:|---:|---|---:|
| baseline | 2 | 10 | 1 | P1 | 3.9983058512535474e-05 |
| fixed | 2 | 10 | 1 | P1 | 1.1957101975212936e-13 |

Pre-existing P1 confirmed: True

The P1 gate source block is identical: True. The projectile_truth function source is identical: True.

P1 compares an absolute apex y against a relative rise. With initial y=1.2 m and v_y=7.5 m/s, both variants return the same absolute apex; the gate subtracts the initial height from its own expected absolute apex and therefore observes exactly the initial 1.2 m as a mismatch. Full original stdout/stderr, JSON rows and the gate's raw JSON remain available. This is a documented existing gate assertion issue, not an all-green gate result.

Independent P1 values:

- baseline: {"initial_height_m": 1.2, "initial_vertical_speed_m_s": 7.5, "gravity_m_s2": 9.80665, "relative_rise_m": 2.8679518490004234, "absolute_apex_y_m": 4.067951849000424, "observed_apex_height": 4.067951849000424, "gate_comparison_target": 2.8679518490004234, "gate_d_apex": 1.2000000000000002, "observed_matches_absolute": true, "gate_target_matches_relative": true, "mismatch_equals_initial_height": true}
- fixed: {"initial_height_m": 1.2, "initial_vertical_speed_m_s": 7.5, "gravity_m_s2": 9.80665, "relative_rise_m": 2.8679518490004234, "absolute_apex_y_m": 4.067951849000424, "observed_apex_height": 4.067951849000424, "gate_comparison_target": 2.8679518490004234, "gate_d_apex": 1.2000000000000002, "observed_matches_absolute": true, "gate_target_matches_relative": true, "mismatch_equals_initial_height": true}
