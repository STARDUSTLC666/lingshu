## 完整空间分区及一致的均匀能量基线

`spatial_detect` 把 `r//3`、`c//3` 重复三次，导致余下的尾行/尾列既不进入能量份额，也不进入分类裁片。公开 `image_to_grid(48×48, cells_across=16)` 会生成 18×16 晶格，最右侧信号因而整列消失；合法透明权重的真实 `HexHierNet` 把仅最右像素列为蓝色的图像误报为 r0/red/share=0。

本件让每条边界按 `i*axis_length//3` 计算，能量与分类复用同一分区，覆盖每个 cell 恰好一次。完整分区面积可能不等，因此追加检测门槛同步改为 `该区面积/(r*c) * exist_mult`；share 仍是真实总能量占比，主导区仍选最高总能量的非空区。这样均匀色场不会只因区域较大而误报多个对象。可整除维度保留原切片、面积基线及字节一致的控制输出。

## 最终验证（R2）

- 新 guard **70 passed**；同一最终 guard 在 untouched 基线 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为 **59 failed / 11 passed**，非旧版草稿 guard 的读数。
- 标准 `replay_save_guards.py` 的 fixed / baseline / **6 个具名变异**共 8 态全部符合预期，变异均由指定业务断言检出，0 errors/skips；包含只修能量或只修分类、遗漏尾行/尾列、空主导区、回退固定 1/9 面积阈值。
- 独立裁片记录 oracle：**400 种尺寸（轴长1..20）、44,100个 cell** 全部恰好覆盖一次，0 遗漏、0 重复、0 异常。真实网络覆盖正常/透明权重、0/0.25/1 均匀场、小轴、4/5/8/18×16、batch 与空空间边界。
- 真公共路径 `image_to_grid→spatial_detect→multimodal_check`：右侧蓝列恢复为蓝色区域；相关 oracle 不依赖旧图像资产。
- 最终相关回归及编码/计数/manifest 守卫 **143 passed**；contracts **14/14**；root 独立复跑新 guard **70 passed**。strict manifest **64/64**；time-core **23 既有 / 0 新**。
- A/B基准每尺寸 **3 预热 + 9 时间样本 + 3 独立 traced peak**：2×18×18 基线/修复 **0.548/0.467 ms**，2×18×16 **0.362/0.350 ms**，2×65×67 **2.033/2.119 ms**；Python traced peak 各 **+40 B**。可整除控制输出 SHA 完全一致。共享主机结果是描述性成本，不声称显著提速或 RSS 结论。

第一次交叉复核发现“补完分区却仍用固定1/9阈值”会把均匀5×5/8×8误报成四个对象，已在本件内修正并新增反向变异；原R1证据保留，最终R2另存，不选择性覆盖。复跑脚本、完整成本和边界见 `docs/testing/spatial-detect-complete-partition-20261120.md`。

## 范围与查重

空空间 extent 返回每样本空清单；没有新增非有限输入或任意网络协议校验。模型训练、权重、类选择不重写；不从透明小网络的可控断言声称真实世界识别精度。

查重覆盖上游与bounty并阅读 #116/#860/#1435/#24 及 PR#1439：旧件分别是采样坐标、数量约束或桥接增量，没有处理尾部完整分区；不把其已有发现重复申报。一个 PR 一项 intake，不自行领取、定级、结算或合并。

<!-- body-round2-final-evidence:v1 -->

## 最终组合验证与不可变证据（2026-11-21）

本项当前源提交 `a357dbbe96905848fd81b7249814576fb2743674`；对应 bounty 仍是原 issue #2794，没有另建或拆分申报。

[最终完整证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120)；[本项工件](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/audit-numeric/r2)；[结果与边界总表](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/FINAL_VALIDATION.md)。证据提交 `83496a7f49ede450729cb944fec36a0fbbafec6f`。

- 冻结的十二项组合源 `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`：独立重建核对十个生产文件、29 个变更函数；本轮 165 项守卫通过，27 个具名变异由指定语义断言检出。各 PR 的精确 head CI 原始记录亦保留。
- 完整组合 Linux [run 44764384747](https://github.com/STARDUSTLC666/lingshu/actions/runs/44764384747)：三个环境各 **5827 passed / 40 skipped / 98 subtests**，各 102/102 脚本及实际固定脑端 23/23。
- 完整组合 Windows 实测 **5838 passed / 1 failed / 28 skipped / 98 subtests**，102/102 脚本通过，原驱动 `gate_ok=false` 保持不变。唯一失败是既有 symlink 能力 P1 的 POSIX 断言，精确旧基线也在本机独立复现；不将它改写成全绿。另做历史物理守卫 43 passed、原 symlink 测试体 3/3 和串行计时 4 passed，均不叠加主计数。
- 额外 Linux [基准/变异 run 44778606930](https://github.com/STARDUSTLC666/lingshu/actions/runs/44778606930)：三个环境各完成四项 A/B 基准及同 27 个具名变异；实际源哈希、原始样本、stdout/stderr、JUnit 和内层工件长度/哈希已独立核对。早期 run 44766869622 的测量和旧索引问题作为中间记录保留。
- 成本按前文及原始 JSON 如实保留，包括增加的 Python traced peak；共享主机数据只描述本次测量，不主张统一提速、统计显著性或 RSS。仍缺 17 个原始模型/像素资产用例，未伪造资产；长期真实部署效果仍未验证。各环境和补充运行有重叠，不能把计数相加当独立覆盖。

<!-- /body-round2-final-evidence:v1 -->
