# Combined math and top-level motions: independent 80-digit public oracle

Each variant is an exact separate Git archive. No source was changed. The reference is high-precision sn(K-u,m), with actual binary64 elapsed=frame/fps, separate input-conversion terms, and direct quaternion construction.

| Variant | Cases | Top supported | Top numeric failures | Explicit supported | Explicit numeric failures |
|---|---:|---:|---:|---:|---:|
| baseline | 784 | 0 | 0 | 180 | 96 |
| math_only | 784 | 0 | 0 | 784 | 0 |
| top_level_only | 784 | 180 | 96 | 180 | 96 |
| combined | 784 | 784 | 0 | 784 | 0 |

Combined correctness: {"assertions": 10976, "failed_assertions": 0, "checks": {"top_level_supported": 784, "top_level_angle_1e_11": 784, "top_level_quaternion_5e_12": 784, "top_level_unit": 784, "top_level_origin": 784, "explicit_parameter_supported": 784, "explicit_parameter_angle_1e_11": 784, "explicit_parameter_quaternion_5e_12": 784, "explicit_parameter_unit": 784, "explicit_parameter_origin": 784, "top_level_repeat_pure": 784, "top_level_time_even": 784, "top_level_equals_explicit": 784, "inputs_unchanged": 784}, "failures": {}}

Combined route maxima: {"top_level": {"supported": 784, "unsupported": 0, "max_angle_error_rad": 4.171278257284197e-13, "max_quaternion_component_error": 2.036977218152234e-13, "numeric_failures": 0}, "explicit_parameter": {"supported": 784, "unsupported": 0, "max_angle_error_rad": 4.171278257284197e-13, "max_quaternion_component_error": 2.036977218152234e-13, "numeric_failures": 0}}

The fixed grid includes +/-5, +/-120, +/-179.99999 degrees and +/-nextafter(pi,0), both time signs, all x/y/z axes and multiple periods, plus 64 seeded near-separatrix points. Checks include input immutability, repeated purity, time symmetry, origin and normalized quaternions. Explicit-parameter and top-level results are compared directly. This covers pure pose generation, not a live Blender render or timing claim.
