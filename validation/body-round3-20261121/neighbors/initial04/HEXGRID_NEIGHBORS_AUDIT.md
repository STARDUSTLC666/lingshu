# HexGrid odd-r neighbor audit — 2026-11-21

Candidate: **reproducible public-API geometry defect** in `HexGrid.neighbors`
for `mode="odd_r_offset"`. No production edits, commits, or publication were
made. The axial nonzero-origin observation is excluded from the claim.

Source: `04e0ecb6a3669c90efbb4a1583816a8f7ca26bc7`, clean shared audit tree.
`hex_cnn.py` LF SHA-256:
`e1b21e3b7e74cbdd34627033a217520a3e272a30bcb3799f93e8d0e6d3c81081`.

## Reproduction and independent oracle

`probe_hexgrid_neighbors.py` builds a Cartesian point cloud from the published
mode/size/origin geometry. It exhaustively selects the six closest distinct
centers in a 7×7 candidate window. It never imports `HEX_DIRS`, calls
`hex_conv`, or uses `pixel_to_cell` as an oracle.

- Axial controls: **324 cases / zero failures**.
- Odd-r: **972 cases / 972 failures**, across four sizes, three origins,
  positive/negative indices and both row parities.
- Every failing set contains five points at `sqrt(3)*size` and one at
  `3*size`, omitting one of the six actual nearest centers.
- The public image path is also exercised using real `image_to_grid`:

| Image | Columns | Returned feature shape | Internal cells checked | Wrong neighbor sets |
| --- | ---: | --- | ---: | ---: |
| 64×64 | 8 | 9×8×3 | 42 | 42 |
| 48×96 | 16 | 9×16×3 | 98 | 98 |
| 96×48 | 12 | 28×12×3 | 260 | 260 |

These 400 public-path cells are strictly inside their returned grids; the
finding does not depend on out-of-bounds queries or border policy.

At unit size and origin zero:

- Even row `(3,2)` wrongly returns `(4,1)` and misses `(2,1)`.
- Odd row `(3,3)` wrongly returns `(2,4)` and misses `(4,4)`.

The current method always adds the axial direction constants and never reads
`self.mode`. With odd-r coordinates, diagonal column offsets depend on the
current row parity. Its result therefore disagrees with `center_px` on the
same returned grid object. The geometrically correct existing convolution
offset sets need no change.

## Scope and prior reports

The complete fetched issue bodies/comments are retained as `issue6.json`,
`issue18.json`, and `bounty183.json`. Additional full PR/intake snapshots are
`pr1254-full.json`, `pr1473-full.json`, their inline-comment responses, and
`bounty2787-full.json`.

- #6 and settled intake #183 report the older mismatch between image sampling
  and the returned grid's center/inverse formulas. #6's closing receipt
  explicitly narrows its delivered repair to that self-consistency surface.
- PR #1254 introduced `mode`/`origin` in `9e1bfb7` (merge `4132fbc`). Its diff
  changes construction, center and inverse handling, but leaves `neighbors`
  unchanged. Before the new mode, that method was correct for its only
  supported axial geometry.
- #18's original assertion about convolution neighbor distance was withdrawn:
  it measured odd-r convolution offsets with an axial metric. Its valid known
  remainder concerns kernel tap ordering. This audit does not repeat that
  finding, change a convolution tap, or mix those two metrics.
- #18's final disposition recognizes odd-r as the sampling-side geometry and
  axial as the historical default. A future formal document decision is not
  needed to measure six closest centers of an explicitly odd-r grid.
- PR #1473 / intake #2787 fixes nearest-cell selection at arbitrary pixel
  queries. Neither implementation nor its comments addresses the separate
  `neighbors` method. Both current PR inline-comment responses are empty.
- The broader `HexGrid` / `HEX_DIRS` search also finds #43, an architecture
  review based on `421deb4`, before the mode parameter existed. Its relevant
  section recommends unified coordinates and a true-neighborhood probe while
  warning against changing only convolution. It does not identify the later
  mode-ignorant `neighbors` method. Its complete snapshot is `issue43-full.json`.

Fresh GitHub issue/PR searches for `HexGrid.neighbors`, `neighbors
odd_r_offset`, `HexGrid origin`, and bounty `HexGrid`/`neighbors`/
`odd_r_offset` are archived in `hexgrid-duplicate-search.json`. Their matching
threads and the broader follow-up in `hexgrid-duplicate-search-broad.json`
contain no specific claim about `neighbors` ignoring the newly
introduced mode. This is a distinct concrete follow-up in the same coordinate
family, **not a claim to first discover the already reported two-formula issue**.

## Excluded axial-origin observation

`HexGrid(..., mode="axial", origin=(10,20))` has a failed center/inverse
round-trip because its center ignores that argument while its inverse
subtracts it. However the current class documentation explicitly defines
axial coordinates with origin `(0,0)` and describes origin shifts only for
odd-r mode. Nonzero axial-origin support is therefore a contract question.
It is recorded in the raw probe but **not proposed as a new bug or bounty**.

## Impact boundary

The method is a public geometry API and `image_to_grid` returns the affected
object through its ordinary default path. Current production consumers in
this checkout still generally discard the grid; the repository's direct
`neighbors` test only constructs the axial default. No downstream production
accuracy loss is claimed. The evidence establishes a deterministic API result
error, not a convolution defect or a measured training-quality regression.
