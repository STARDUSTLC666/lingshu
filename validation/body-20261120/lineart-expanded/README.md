# Lineart alpha expansion validation

Implementation commit: `433befa7b356eebecbc457ecd8f8a123ec1540cc`.
Working tree: `[workspace]\lingshu\work\lingshu-body-lineart-20261120`.
Runtime: `[workspace]\lingshu\work\lingshu-body-20261120-venv\Scripts\python.exe`.

The production change recognizes RGBA, RGBa, LA, La, PA and transparency metadata.
Premultiplied luminance is converted to LA before RGBA. The center differences,
luminance weights, threshold calculation and output inversion are unchanged.

## Final results

| Check | Result |
| --- | --- |
| Alpha regression guard | 25 passed |
| All test_vision*.py tests | 73 passed |
| Strict manifest | 64/64 match; no missing/malformed/unparseable entries |
| Expanded baseline fb8eaada | 6 expected failures, 19 passed |
| Original baseline d74848fb | 15 expected failures, 10 passed |
| Named mutants | 10/10 killed by the selected guard |
| Replay errors / skips | 0 / 0 in all fixed, baseline and mutant runs |

The 25 guard cases cover six alpha input forms, transparent and partial alpha,
opaque RGB parity, output inversion and preservation of mode, size, pixels,
metadata and palettes. The additional P-mode case preserves integer transparent
index coverage alongside per-index alpha bytes.

`replay-expanded-baseline/summary.json` is generated from the committed fixture
`tests/fixtures/vision_lineart_alpha_mutations.json`. Its baseline is the previous
PR head `fb8eaada60fdabcd3069e531fa498d8d784609a1`.

`replay-original-baseline/summary.json` uses the same final guard and mutants
against `d74848fb33dbff1d719959df19d1266a1ac60f44`. The preserved variant
`vision_lineart_alpha_original_baseline.json` differs only in its expected
baseline-failure list. It was temporarily copied into tests/fixtures for the
repository runner, then moved to this evidence directory.

Each replay folder retains the complete stdout and JUnit XML per case, plus
source SHA-256 values and the shared guard SHA-256 in summary.json. Expected
baseline and mutant failures are successful detection evidence; they are not
failures of the fixed implementation.

## Reproduction

From the working tree, run the runtime above with:

```text
-B -X utf8 -m pytest tests/test_vision_lineart_alpha.py -q
-B -X utf8 tools/verify_manifest.py --strict --quiet
-B -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/vision_lineart_alpha_mutations.json --baseline fb8eaada60fdabcd3069e531fa498d8d784609a1 --mutate --output <new-output-directory>
```

For the original baseline replay, copy the preserved variant into
`tests/fixtures/vision_lineart_alpha_original_baseline.json` and select that
relative spec path with `--baseline d74848fb33dbff1d719959df19d1266a1ac60f44`.
Use the same fixed implementation and unchanged final guard.

Independent randomized/oracle and memory probes are maintained by the parallel
benchmark agent under the parent validation directory; they are separate from
the regression/mutation evidence here.
