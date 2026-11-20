<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1475"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1475

修复身体库与纯标准库动画桥的零初速释放单摆闭式解：原式漏掉 dn 分母/四分之一周期偏移，把真实公式错误误归因于 jacobi_cn 并限制到 5°。在 theta0=120°、omega0=1、t=1、显式 tol_deg=180 的可复现输入下，基线返回 1.1387045287626738 rad，独立 RK4 为 1.645993497151551 rad，绝对误差 0.5072889683888773 rad。

现在使用正确释放解、直接互补模 cos(theta0/2)、稳定 atan2/hypot Landen 下降及周期折叠，支持 |theta0|<π，边界和非有限输入显式拒绝；保留公开 jacobi_cn 的既有数值路径。近分离点的周期真值及公开动画求值路径同步修正，桥仍不依赖 lingshu/numpy/bpy。

验证（精确 PR head e0771a810b8846676f3545542b2e70d5e0011467）：三档完整 gate（Python 3.12、3.12 依赖下界、3.13）及标题检查全部 SUCCESS。相关物理/桥侧/#455 守卫 55 passed / 4 skipped；身体新守卫 6 passed、同一基线 6 failed；桥侧 8 passed、同一基线 7 failed / 1 passed；十一项具名回退变异均命中指定断言，全部回放零 errors/skips。strict manifest 64/64；time lint 保持原有 23 项仅同步两条行号，相关 lint 测试 74 passed。

随 PR 提交可移植 80 位 mpmath 验证脚本：930 个短中期点、40 个超长时点共 6,550 项角度/相位检查通过；69 个独立周期检查通过，2,165 个公开 cn 位级比较无差异，8 项域检查通过。最多约 100.3 周期的样本最大角误差 3.67513e-13 rad；并未将此样本读数声明为任意长时间的全域误差上界。另以真实公开 eval_at(..., motions=...) 的 2,840 组输入/31,240 项断言对照 80 位四元数参考，零失败。原始读数、源码 hash、输入转换误差与性能成本均保留。

复跑命令与边界见 PR 正文及 bench/repro/pendulum_release_accuracy.py。未验证真实 Blender/bpy/GPU 渲染。额外手工物理门的 P1 仍有既有绝对/相对高度断言混比问题，基线与修复版均 10 PASS / 1 FAIL；本次没有用跳过或修改无关断言把它伪装成全绿。维护者定级、验收与合并待审。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`e0771a810b8846676f3545542b2e70d5e0011467`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1475/checks)。PR/申报仍待维护者审核、合并与验收。

- 相关物理、桥侧及 #455 编码守卫 **55 passed / 4 skipped**；身体新 guard 6/6、原始基线 6 failed；桥侧 guard 8/8、原始基线 7 failed / 1 passed；合计 11 项具名 mutation 均命中指定断言，所有回放零 errors/skips。
- 独立 80 位参考：6,550 项角度/相位检查、69 项周期比较、2,165 项公开 cn 位级兼容及 8 项域检查通过。最多约 100.3 周期的样本最大角误差 3.67513e-13 rad；不将它表述为任意大时间的全域浮点误差上界。
- 被测 physics LF SHA-256：`271d2bb9d24452e3724e3ee0375b2d4fd9e04e85bbc4b62fd5afbd39b925f904`；portable runner LF SHA-256：`f0c163e8540a052ded44efcd843d97acde20d3cdac9149520115a701b41d21bf`。
- 时延为每 16 个角度一批：1° default 中位 59.552 → 231.002 µs（3.879×）；120°、tol180 为 81.287 → 258.212 µs（3.177×）。正确释放解包含额外运算，不作免费提精度或普遍提速承诺。此标量例程本轮没有独立内存测量，不能以六套件的内存数字替代。
- [独立精度、周期、latency 与内存边界报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/pendulum/report.md)、[可移植 80 位参考脚本](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/pendulum/pendulum_release_accuracy.py)、[精确源码与 runner 指纹](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/pendulum/source_manifest.json)、[身体 guard](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/pendulum-guards/summary.json)、[桥侧 guard](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/bridge-guards/summary.json)。
- [两项桥侧修复的独立组合 oracle](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/crossfix-oracle/report.md)：784 组真实公开入口输入、10,976 项断言零失败；同时比较原始、仅数学、仅顶层 motions 与两项组合四份源。该纯位姿交互验证不等于真实 Blender 渲染或最终整仓 r2 门禁。

测量范围：合成 CPU 单摆与纯标准库位姿生成，共享主机；接近分离点时双精度 RK4 可能停滞，使用独立高精度参考。真实资产、Blender/bpy 与 GPU 渲染仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
