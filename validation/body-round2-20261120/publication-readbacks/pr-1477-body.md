## 问题与修复

`fit_circular` 支持水平圆周加 `up` 轴匀速漂移，但把绝对时间的线性截距当作 `t_ref` 时刻的高度。独立解析螺旋从 `t=0` 平移到 `t=10` 后，初高 3 被拟合为 -17；Unix epoch 1700000000 下角度拟合还会报矩阵奇异。

另一个同函数缺陷是残差完全漏掉 `up` 轴，并按 `2*n` 归一。水平圆周 + 纵向加速度 20 的样本实际三坐标 RMS 为 4.18563、最大位置误差 14.375，却报告 5.32e-16，`classify` 因此错选 circular。

此补丁仅将角度、高度回归改用 `t-t_ref`，并把纵向拟合误差纳入三坐标 RMS。保留模型 schema、世界轴序、圆拟合算法和 unwrap；只按净增四行移动既有 time-core 登记，不增加豁免。已有错误序列化模型需用观测重拟合。

## 验证

- 新 guard **6 组全部通过**；同一 guard 在精确基线 `d74848fb33dbff1d719959df19d1266a1ac60f44` 上 **6 组全部语义失败**。
- **6 个具名定点变异**均在指定业务断言上被检出，无导入错误、无 skip。
- 相关 physics / dynamics / collision / #786 / finite-time 测试：**145 passed, 4 existing skipped**。
- time-core 及 #607 / #455 静态守卫：**76 passed**；lint **23 既有 / 0 新 / 0 过期**。
- 独立解析基准：**666 场景，7146 条断言，0 失败**，抽样位置/速度最大误差分别低于 1.484e-13 / 2.046e-13。基线 1530 条失败，216 次拟合异常；异常后的 2160 条预测检查明确记为未执行，不冒充通过。
- 两轮共享主机性能测量各保留 9 组交错样本：25/100/1000 点的修复后/基线中位耗时范围分别 **1.003–1.032 / 1.017–1.037 / 1.000–1.036**。Python traced peak 分别 **5168→6136 / 10008→13384 / 71316→104228 B**；补回正确语义所需数组的内存成本如实保留，不据此声称提速。

命令、独立 oracle、完整成本边界见 `docs/testing/circular-time-residual-20261120.md`、`bench/circular_time_residual.py`；变异规格见 `tests/fixtures/circular_time_residual_mutations.json`。完整组合回归与远端三环境 CI 已完成，精确提交证据见文末。

## 查重与边界

核对 1307 条上游 issue/PR、2194 条 bounty issue 及 circular 精查，逐条阅读 #786 / #817 评论和 #829：旧报告是 center 的世界序/打包序错位，此处保留其修复；本件是非零时间锚及遗漏纵向残差。`circular_truth` 几何参数及 damped 符号既有件也不重复申报。

此修复不覆盖倾斜圆、采样角混叠或任意病态空间坐标。一个 PR 作为一项完整贡献申报；不把参数/守卫拆成多项 bounty，不自行定级、领取、结算或合并。

<!-- body-round2-final-evidence:v1 -->

## 最终组合验证与不可变证据（2026-11-21）

本项当前源提交 `e821bbb1fac57fa638640e3caf153caf7f1b1973`；对应 bounty 仍是原 issue #2791，没有另建或拆分申报。

[最终完整证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120)；[本项工件](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/audit-circular)；[结果与边界总表](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/FINAL_VALIDATION.md)。证据提交 `83496a7f49ede450729cb944fec36a0fbbafec6f`。

- 冻结的十二项组合源 `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`：独立重建核对十个生产文件、29 个变更函数；本轮 165 项守卫通过，27 个具名变异由指定语义断言检出。各 PR 的精确 head CI 原始记录亦保留。
- 完整组合 Linux [run 44764384747](https://github.com/STARDUSTLC666/lingshu/actions/runs/44764384747)：三个环境各 **5827 passed / 40 skipped / 98 subtests**，各 102/102 脚本及实际固定脑端 23/23。
- 完整组合 Windows 实测 **5838 passed / 1 failed / 28 skipped / 98 subtests**，102/102 脚本通过，原驱动 `gate_ok=false` 保持不变。唯一失败是既有 symlink 能力 P1 的 POSIX 断言，精确旧基线也在本机独立复现；不将它改写成全绿。另做历史物理守卫 43 passed、原 symlink 测试体 3/3 和串行计时 4 passed，均不叠加主计数。
- 额外 Linux [基准/变异 run 44778606930](https://github.com/STARDUSTLC666/lingshu/actions/runs/44778606930)：三个环境各完成四项 A/B 基准及同 27 个具名变异；实际源哈希、原始样本、stdout/stderr、JUnit 和内层工件长度/哈希已独立核对。早期 run 44766869622 的测量和旧索引问题作为中间记录保留。
- 成本按前文及原始 JSON 如实保留，包括增加的 Python traced peak；共享主机数据只描述本次测量，不主张统一提速、统计显著性或 RSS。仍缺 17 个原始模型/像素资产用例，未伪造资产；长期真实部署效果仍未验证。各环境和补充运行有重叠，不能把计数相加当独立覆盖。

<!-- /body-round2-final-evidence:v1 -->
