## 改动说明

修复 `darkline()` / `linework()` 丢弃输入 alpha 通道的问题。RGBA/RGBa/LA/La/PA 或带 palette transparency 的透明黑底线稿，隐藏的 RGB 黑色会被当作可见背景；例如透明 32×32 画布中仅有一条 16 像素黑线，修复前输出 0 个黑色线稿像素。现在先将带透明度的输入合成到白底，再做亮度和边缘检测；完全不透明输入保持原有结果。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_vision_lineart_alpha.py -q --no-header -p no:cacheprovider
# 25 passed

python -X utf8 -m pytest tests/test_vision_image_stats.py tests/test_vision_lineart_alpha.py tests/test_vision_lineart.py -q --no-header -p no:cacheprovider
# 73 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/vision_lineart_alpha_mutations.json --baseline fb8eaada60fdabcd3069e531fa498d8d784609a1 --mutate --output artifacts/lineart-expanded-previous-head
# fixed 25 passed; previous-head baseline 6 failed / 19 passed; 10/10 named mutations hit their specified assertion

# 将下方链接中的原始基线 fixture 另存为 tests/fixtures/vision_lineart_alpha_original_baseline.json，再运行：
python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/vision_lineart_alpha_original_baseline.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output artifacts/lineart-expanded-original
# fixed 25 passed; original baseline 15 failed / 10 passed; 10/10 named mutations hit their specified assertion

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

提交中的默认 fixture 对应上一 PR head `fb8eaada60fdabcd3069e531fa498d8d784609a1`；对原始 `d74848fb` 复跑时应使用固定证据内的[原始基线 fixture](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/lineart-expanded/vision_lineart_alpha_original_baseline.json)。两份 fixture 的预期基线失败清单不同；不要把原始基线 SHA 与默认 fixture 混用。[完整双基线日志、JUnit 与 summary](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/lineart-expanded)均保留，所有回放零 errors/skips。

## 未验证项 / 边界

验证覆盖合成 RGBA/RGBa/LA/La/PA 与 palette-transparency 图片、半透明、opaque parity、反相和输入不变；已补 128/512/1536 尺寸 CPU 时延与独立内存探针。真实应用绘图数据集、端到端渲染及 GPU 仍未验证。普通 RGB 结果及完全不透明输入的像素一致性由回归保留。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`433befa7b356eebecbc457ecd8f8a123ec1540cc`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1470/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `lineart_alpha`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **22 / 69 → 0 / 85**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：RGBA 128×128 的中位时延 0.430600 → 1.137800 ms（2.642×），1536×1536 为 104.328500 → 123.025900 ms（1.179×）；1536×1536 独立 tracemalloc 峰值中位数 120,325,453 → 120,326,691 B。RGB 对照及其他尺寸保留在完整报告。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only lineart_alpha` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。
- 扩展 alpha 回归：25 项 guard、73 项 vision，RGBA/RGBa/LA/La/PA/P transparency 均覆盖。默认 fixture 对应 `fb8eaada`：6 failed / 19 passed；[原始基线变体](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/lineart-expanded/vision_lineart_alpha_original_baseline.json)对应 `d74848fb`：15 failed / 10 passed；两路均保留 10 项具名 mutation 及零 errors/skips 的完整回放，详见[alpha 专项证据](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/lineart-expanded)。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
