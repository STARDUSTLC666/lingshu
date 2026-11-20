## 改动说明

修复 `darkline()` / `linework()` 丢弃输入 alpha 通道的问题。RGBA 或带 palette transparency 的透明黑底线稿，隐藏的 RGB 黑色会被当作可见背景；例如透明 32×32 画布中仅有一条 16 像素黑线，修复前输出 0 个黑色线稿像素。现在先将带透明度的输入合成到白底，再做亮度和边缘检测；完全不透明输入保持原有处理路径。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_vision_lineart_alpha.py tests/test_vision_lineart.py -q --no-header -p no:cacheprovider
# 12 passed

python -X utf8 -m pytest tests/test_vision_image_stats.py tests/test_vision_lineart_alpha.py tests/test_vision_lineart.py tests/test_issue196_nonfinite_gate.py -q --no-header -p no:cacheprovider
# 66 passed, 2 subtests passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/vision_lineart_alpha_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output [workspace]/lingshu/outputs/vision-lineart-alpha-20261120
# fixed 4 passed; baseline 3 failed / 1 passed; 3/3 named mutations hit their expected assertions

python -X utf8 -m pytest tests/test_vision_image_stats.py tests/test_vision_lineart_alpha.py tests/test_vision_lineart.py -q --no-header -p no:cacheprovider
# 52 passed

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

验证使用合成 RGBA 与 palette-transparency 图片；未验证真实应用绘图数据集或大图性能。仅 alpha-bearing 输入走合成分支，普通 RGB/RGBA 不透明图仍逐点一致。
