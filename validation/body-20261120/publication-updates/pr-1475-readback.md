## 改动说明

修复零初速释放单摆的闭式波形。原实现用 `2*asin(k*cn(u,k))`，但正确释放条件需要 `cn(u,k)/dn(u,k)`（等价于 `sn(K-u,k)`）。例如 `theta0=120°、omega0=1、t=1、tol_deg=180`，基线返回 `1.1387045287626738 rad`，独立 RK4 为 `1.645993497151551 rad`，误差 `0.5072889683888773 rad`。旧代码把这一误差归因于 `jacobi_cn`，并把默认域收缩到 5°。

本次使用有四分之一周期偏移的释放解，按周期折叠相位；直接保留 `cos(theta0/2)` 的互补模，避免接近 ±π 时 `sin(theta0/2)` 舍入为 1。Landen 下降中由 `a²-c²=b²` 推导等价 `atan2/hypot` 形式，避免 `asin` 的端点精度损失。默认允许 `|theta0|<π`，仍可用 `tol_deg` 显式收紧域；±π、非有限输入及溢出的相位乘积显式拒绝。公共 `jacobi_cn` 的签名和既有数值路径保持不变。

同源的 Blender bridge exact 动画入口保持纯标准库和独立部署，不引入对 lingshu 的硬依赖；同步释放解和近分离点周期计算。桥的机械门同步实际公式，并让 RK4 正好积分到每个请求时间，去除原先把终点四舍五入到整步的参考误差。

## 数学依据

- [NIST DLMF 22.19.2](https://dlmf.nist.gov/22.19.E2)：零初速释放解带 `K` 偏移；`K-u` 与 `K+u` 由时间偶对称等价。
- [NIST DLMF 22.20.1–4](https://dlmf.nist.gov/22.20.ii)：AGM 与振幅下降。`atan2` 版本是由其 AGM 定义和 `a²-c²=b²` 推导的等价稳定改写，非原文直接给出的公式。

## 复跑命令

```sh
python -X utf8 -m pytest tests/test_pendulum_release_solution.py tests/test_physics_predict.py -q
python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/pendulum_elliptic_angle_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output ../pendulum-guard-replay
python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/bridge_pendulum_release_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output ../bridge-pendulum-guard-replay
python -X utf8 tools/verify_manifest.py --strict --quiet
python -X utf8 tools/time_core_lint.py --json

# 可选独立高精度/性能验证，仅验证环境需要 mpmath，不增加产品依赖。
python -m pip install mpmath==1.4.1
python -X utf8 bench/repro/pendulum_release_accuracy.py --repo . --output ../pendulum-accuracy --baseline d74848fb33dbff1d719959df19d1266a1ac60f44
```

身体侧新守卫 6 passed、原始基线 6 failed；桥侧 8 passed、原始基线 7 failed / 1 passed；合计十一项具名回退变异均命中指定断言，零 error/skip。相关物理、桥侧及 #455 全仓 subprocess 文本编码守卫合计 55 passed / 4 skipped；strict manifest 64/64 MATCH。time-core baseline 仅同步两条原有形态的行号，23 条条目守恒，历史说明保留，相关 lint 测试 74 passed。通用回放器仅补充在 sandbox 中创建声明源文件的父目录，使桥侧 fixture 也可直接复跑，不更改断言或验收规则。

## 独立验证与性能边界

80 位 mpmath 椭圆函数参考不复用生产 AGM 代码；930 个短中期点、40 个超长时点的 6,550 项检查全部通过，最多约 100.3 周期的样本最大角度误差 `3.67513e-13 rad`。69 个独立周期比较通过，最大相对误差 `2.81089e-16`。覆盖正负振幅、正负时间/频率、`nextafter(pi,0)`、周期拐点和非拐点。另以独立 `theta''=-sin(theta)` RK4、周期/对称性质、公有 cn 的位级对照和冻结高精度点交叉验证。保留种子、精确源码哈希、原始输入输出与耗时样本。

测试和基准使用合成 CPU 输入；未验证真实 Blender/bpy 渲染或 GPU。接近分离点时双精度 RK4 自身会在释放点停滞，不能拿它代替高精度参考。`PENDULUM_EXACT_MAX_ERR` 是回归样本门槛，不是任意振幅/任意大时间的全域浮点误差上界。长时间的输入乘积及周期约减会丢失相位，基准单列这一现象。正确解比旧错误公式需要更多计算，耗时比较不作“免费提精度”宣称。

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
