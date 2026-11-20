## 缺陷与最小修复

已有 `_last_decay_at` 可能早于本轮新增行。`decay_cycle(now=...)` 把整个全库间隔套给每一行，因而会扣除节点/边出生前的时间。纯公开 API：先在空库建立七天前的游标，正常创建 context / perception / edge，再按当前时刻衰减；毫秒级新 context 和 edge 被直接删掉，knowledge confidence 从 0.5 降至约 1.81e-89。

对已存在且有限的游标，只有 `created_at` 确证位于 `(last_tick, now]` 内时，将该行 dt 缩到 `now-created_at`；老行保留停机补偿。三条腿（context / knowledge / unverified edge）统一适用。另保证 dt=0 是恒等，包括 factor=1，避免恰在 now 出生的行被清零。写事务涵盖游标读取和更新，无每节点新增查询，不改 schema 或 stored timestamps。

## 验证

- 新 guard：**48 passed**；完全相同的 guard 对精确基线 `d74848fb33dbff1d719959df19d1266a1ac60f44`：**25 failed / 23 passed**，无 errors/skips。
- **9/9 具名变异**由指定业务断言检出，均是 1 failed、0 errors、0 skipped。
- 相关 core/decay 回归 **193 pytest + 4 脚本通过**；原 #176 时间/回拨守卫保持不变；另一独立审阅者复跑 48 新 + 11 旧 = **59 passed**。
- 独立闭式 oracle：每种源版本核对 **27,450 个值**，修复 **0 错**，基线 **4,575 错**；覆盖空/100/1000/5000 节点、新旧混合、不同层与边、重复时刻、回拨、bootstrap、离散模式、保护与事务回滚。
- 基准 **12 配置 ×（3 预热 + 9 时间样本 + 3 独立 Python allocation peak）**。5000 节点 + 2500 边的 traced peak 约 **+4.27%**；共享主机时延波动如实保留，不从更快的中位数宣称提速。
- strict manifest **64/64**；time-core lint **23 既有 / 0 新**。

重放命令、成本表和全部范围说明见 `docs/testing/fresh-row-decay-20261120.md`；bench 与 mutation spec 随 PR 提供。完整组合回归和精确 head 三环境 CI 的独立证据见文末。

## 时间域边界与查重

现有公开 API 允许自定义衰减时钟，但创建时钟仍用 `time.time()`；原 #176 的 guard 明确使用从 5000 开始的注入时钟。因此本件只对**能与本轮区间比较的出生时间**修复，不把不同 epoch 混用误当零年龄。未来/无效/缺失/非有限出生时间保持旧 global-dt 语义；首次时间模式保持一周期 bootstrap，`now=None` 保持旧离散步进。无法从现有元数据推断异轴时钟的真实行龄，未宣称全面统一时钟模型。

已检索上游与 bounty 并读取 #176 正文及评论；既有报告处理调用次数/全库连续时间/游标回拨，没有处理本轮新生行。CSR 并行边叠加等既有已报告发现不混入本件。一个 PR 一项 intake，不自行领取、定级、结算或合并。

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
