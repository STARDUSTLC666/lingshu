# Final production-code review

Reviewed source: `d74848fb33dbff1d719959df19d1266a1ac60f44` to `231aa5334c0c0f2f01eccf6c547ebd97a478a8d0`.

Conclusion: no newly introduced material regression or release-blocking issue was found in the seven production modules and the replay-path change. This was a read-only diff and call-path review. The completed full suites, mutation replays and benchmarks were not rerun or replaced by this review. Production source and the public evidence checkout were not modified.

## Compatibility and supported boundaries

- Skill search keeps its public signature, candidate query, ranking and result fields. It now uses the existing limit normalizer. Negative limits intentionally mean the existing full-result sentinel; this does not remove the pre-existing 100-candidate SQL pool.
- The novelty snapshot keeps its four-item return shape, signature and cache-hit/genuine-append alias behavior. The new per-row digest comparison sends mixed replacement-plus-append changes through the existing complete rebuild. It adds O(N) retained/transient digest-map memory and O(N) comparison during the existing full content scan; it does not add a database scan.
- Motion groups keep ordinary-name IDs byte-for-byte and propagate existing stored IDs unchanged. Separator-bearing member names intentionally use canonical JSON encoding in the separate `mg_v2_` namespace. Detection ordering and all repository consumers reviewed are consistent with that boundary.
- The default axial HexGrid branch is unchanged. The corrected odd-r branch still returns the same `(q, r)` integer tuple and makes a constant-size comparison of the two adjacent rows' nearest centers. Negative rows use the same parity convention as `center_px`; grid bounds remain a separate operation.
- Lineart keeps `darkline`/`linework` signatures and L/RGB output modes. Nontransparent input stays on the original conversion and Sobel path. Transparent and premultiplied modes deliberately use visible white-background pixels; input image state is not modified by the conversion/composite chain. The additional image buffers are a constant-factor O(width*height) cost.
- SAT keeps overlap/MTV return shapes, normalized projection radii and the existing touching-is-separated comparison. Face normals replace edge directions where necessary for skew frames. **The accepted frame domain has an explicit numerical margin:** after normalizing the three rows, `abs(dot(axis0, cross(axis1, axis2))) <= 1e-9` is rejected as numerically degenerate. This is not support for every mathematically nonzero determinant. An oracle restricted to `abs(det) > 0.15` must not be extrapolated to nearly singular frames.
- The public `jacobi_cn` path retains the original non-stable AGM descent, now extracted into a helper. The new stable descent and complementary-modulus preservation are used by the intentionally corrected release-from-rest exact pendulum path. The non-exact spring/damped pendulum branch is unchanged. Public result dictionaries and function signatures remain, while the exact-angle physical/finite input guards and body `tol_deg` range `[0, 180]` are intentional tightening. Review does not promise compatibility for old invalid/nonfinite/coercible-string inputs. Physical exact-angle amplitudes remain strictly inside `(-pi, pi)`; very large phases retain ordinary floating-point phase-reduction limits. `PENDULUM_EXACT_MAX_ERR` is a regression-sample threshold, not a proven global error bound.
- Bridge normalization builds a recursive list/dict copy, removes only the top-level animation `motions` extension, and sends every remaining field through the unchanged frozen strict geometry validator. Motion lookup still reads the original input first; explicit declarations and explicit empty lists retain their established precedence. All five public evaluation/oracle entry paths retain their output shapes and axis conversion.
- Replay source writes still pass through `under`: absolute/parent-traversal paths are rejected and resolved containment is checked. The only added operation creates parents for that already-validated destination in the newly created sandbox. It does not broaden the source-path validation or write through an unchecked spec path.

## Files actually read

The complete production diff was read for:

- `lingshu/core/core.py`
- `lingshu/core/longterm_gate.py`
- `lingshu/world/motion_groups.py`
- `lingshu/nn/hex_cnn.py`
- `lingshu/vision/lineart.py`
- `lingshu/world/physics.py`
- `bridges/blender/wm_bridge/factory/anim/eval.py`
- `tools/testing/replay_save_guards.py`

Additional context was read for the limit normalizer/search/recall and group forwarding; cache constructor/snapshot/templates/novelty consumers; the complete motion-group module; HexGrid constructor/forward mapping/axial rounding; the complete lineart module; physics vector/finite-number helpers, collision frame/SAT/MTV functions and pendulum/truth functions; bridge recursive normalization, motion lookup/dispatch, evaluation and oracle entry points; and the complete replay runner.

Supporting changed guards were inspected in `test_search_skills_limit_semantics.py`, `test_longterm_gate_mixed_in_place_update.py`, `test_motion_group_identifier_encoding.py`, `test_bridge_top_level_motions.py` and `test_obb_nonorthogonal_sat.py`. Targeted alpha-guard mode/oracle/immutability references and the changed reference gate in `bridges/blender/wm_bridge/factory/anim/_det/gate_physics.py` were also read.

The separate core/cache/identity review is retained in `core-identity-review.md`. The source worktree was checked clean after this review.
