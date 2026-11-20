## 改动说明

修复 HexGrid 的 odd_r_offset pixel_to_cell 最近格判定。旧实现先按 y 只选一行，再按该行错位换算 q；在错行边界附近，这会返回距离更远的格。例如 HexGrid(5,5,1.0, mode="odd_r_offset") 查询 (√3/2, 0.74)，改前返回 (0,0)，中心距离约 1.1391；最近格为 (0,1)，距离 0.76。现在比较 y 对应的上下相邻行，并按实际格心的欧氏距离选最近者；默认 axial 模式不变。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_hexgrid_odd_r_nearest_cell.py tests/test_issue6_grid_roundtrip_guard.py tests/test_hex_grid_extent.py tests/test_hex_cnn.py -q --no-header -p no:cacheprovider
# 10 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/hexgrid_odd_r_nearest_cell_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output [workspace]/lingshu/outputs/hexgrid-odd-r-nearest-20261120
# fixed 4 passed; baseline 4 failed; named y-only mutation hit its expected assertion

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

最近格由有限个上下候选行与各行最近列的中心距离判定；回归覆盖多 cell_size、origin 和坐标区间。未做整幅图像的最近邻性能基准。
