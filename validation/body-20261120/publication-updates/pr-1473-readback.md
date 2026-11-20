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

最近格由有限个上下候选行与各行最近列的中心距离判定；回归覆盖多 cell_size、origin 和坐标区间。已补 1,000/10,000/50,000 个合成坐标的 CPU 批量最近格时延与独立内存探针；真实整幅图像的端到端负载仍未验证。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`cff189b3438623feaebdf1a874fafdd03080acb1`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1473/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `hexgrid_nearest`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **632 / 12205 → 0 / 12205**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：50,000 个 odd-r 查询的中位批次时延 267.965700 → 297.301800 ms（1.109×）；独立 tracemalloc 峰值中位数 4,732,702 → 4,734,618 B。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only hexgrid_nearest` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
