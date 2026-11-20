<!-- intake:v1 {"project":"lingshu","difficulty":"hard","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1478"} -->

修复交付：[PR #1478](https://github.com/FuRongJun-1999/lingshu/pull/1478)，原测量/验证提交 `89c005b7fdd48f64c603d34c280a4d18a93956f7`；当前同步提交 `41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50`。

decay_cycle 的全库游标早于本轮新增行，却把整个旧间隔套给context、knowledge与unverified edge。公开API复现七天游标后新增毫秒级行：context/edge被删除，knowledge 0.5降到约1.81e-89。现在仅在 created_at 可确证位于(last,now]时按该行出生后时间衰减，并保持零时长恒等。

## 已验与原始证据

- 新回归：**48 passed；同一基线guard 25 failed /23 passed，0 errors/skips**。
- **9个具名定点变异**全部在指定业务断言失败，0 errors/skips；不是以导入错误当检出。
- 历史89c005提交的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5624 passed /40 skipped /98 subtests**，102/102脚本及真实脑端23/23通过。[原始CI run](https://github.com/FuRongJun-1999/lingshu/actions/runs/44762844376)。40个skip没有冒充通过。
- 独立闭式oracle每个源版本27450个值：修复0错、基线4575错；相关193 pytest+4脚本通过，另一审阅者59项新旧守卫通过。
- [不可变公开证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120)；[本项完整原始工件](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120/audit-core)。源锚/命令/原始JSON、stdout、JUnit、变异summary及全部A/B样本均随证据封存，保留失败和中间迭代。

## 基准成本

12配置，每配置3预热、9时延样本、3独立Python allocation peak；5000节点+2500边的traced peak约+4.27%。全部A/B原始时延和峰值保留，不从调度噪声中的快中位数宣称加速。

以上性能均是共享主机上的描述性样本，不作为显著提速或通用硬件性能证明。

## 未验／不确定／不做

- 未验：长期真实部署效果和仍缺原始资产的17个用例。完整组合Windows/Linux及额外Linux基准的实际结果、失败与跳过见文末最终证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：只对能与既存区间比较的出生时间修复。自定义衰减时钟可与time.time异epoch；未来/无效/缺失/非有限出生时间保留旧global-dt。首次一周期bootstrap和无now离散语义不改。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查上游/bounty并读取#176全文及评论；既有件处理调用次数、连续核与游标回拨，没有处理本轮新生行。已知CSR叠加旧发现仅保留审计历史，没有混入新发现或申报。

<!-- body-round2-final-evidence:v1 -->

## 最终组合验证与不可变证据（2026-11-21）

本项当前源提交 `41dc5e01fd710ffeab79aa4d566d8ed5ed5baf50`；对应 bounty 仍是原 issue #2792，没有另建或拆分申报。 本地最初测量源为 `bae2eaea9fb77e9e451f1b220d17f9096d06ee78`，原已验证提交为 `89c005b7fdd48f64c603d34c280a4d18a93956f7`；这些历史数据不改标成新提交。当前 `41dc5e0` 合并维护者已采纳的旧修复，冲突解决仅更新 core 指纹；新生行衰减函数不变，整个 core 模块与已测组合源 `5226860` 字节一致。新 head 的独立三环境完整 gate 每腿 **5638 passed / 40 skipped / 98 subtests**、102/102 脚本和实际脑端 23/23，标题也通过。[新 head CI](https://github.com/FuRongJun-1999/lingshu/actions/runs/44781318899)。

[最终完整证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120)；[本项工件](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/audit-core)；[结果与边界总表](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/FINAL_VALIDATION.md)。证据提交 `83496a7f49ede450729cb944fec36a0fbbafec6f`。

- 冻结的十二项组合源 `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`：独立重建核对十个生产文件、29 个变更函数；本轮 165 项守卫通过，27 个具名变异由指定语义断言检出。各 PR 的精确 head CI 原始记录亦保留。
- 完整组合 Linux [run 44764384747](https://github.com/STARDUSTLC666/lingshu/actions/runs/44764384747)：三个环境各 **5827 passed / 40 skipped / 98 subtests**，各 102/102 脚本及实际固定脑端 23/23。
- 完整组合 Windows 实测 **5838 passed / 1 failed / 28 skipped / 98 subtests**，102/102 脚本通过，原驱动 `gate_ok=false` 保持不变。唯一失败是既有 symlink 能力 P1 的 POSIX 断言，精确旧基线也在本机独立复现；不将它改写成全绿。另做历史物理守卫 43 passed、原 symlink 测试体 3/3 和串行计时 4 passed，均不叠加主计数。
- 额外 Linux [基准/变异 run 44778606930](https://github.com/STARDUSTLC666/lingshu/actions/runs/44778606930)：三个环境各完成四项 A/B 基准及同 27 个具名变异；实际源哈希、原始样本、stdout/stderr、JUnit 和内层工件长度/哈希已独立核对。早期 run 44766869622 的测量和旧索引问题作为中间记录保留。
- 成本按前文及原始 JSON 如实保留，包括增加的 Python traced peak；共享主机数据只描述本次测量，不主张统一提速、统计显著性或 RSS。仍缺 17 个原始模型/像素资产用例，未伪造资产；长期真实部署效果仍未验证。各环境和补充运行有重叠，不能把计数相加当独立覆盖。

<!-- /body-round2-final-evidence:v1 -->
