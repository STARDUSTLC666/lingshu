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

重放命令、成本表和全部范围说明见 `docs/testing/fresh-row-decay-20261120.md`；bench 与 mutation spec 随 PR 提供。完整组合回归和精确 head 的三环境 CI 将补独立证据链接。

## 时间域边界与查重

现有公开 API 允许自定义衰减时钟，但创建时钟仍用 `time.time()`；原 #176 的 guard 明确使用从 5000 开始的注入时钟。因此本件只对**能与本轮区间比较的出生时间**修复，不把不同 epoch 混用误当零年龄。未来/无效/缺失/非有限出生时间保持旧 global-dt 语义；首次时间模式保持一周期 bootstrap，`now=None` 保持旧离散步进。无法从现有元数据推断异轴时钟的真实行龄，未宣称全面统一时钟模型。

已检索上游与 bounty 并读取 #176 正文及评论；既有报告处理调用次数/全库连续时间/游标回拨，没有处理本轮新生行。CSR 并行边叠加等既有已报告发现不混入本件。一个 PR 一项 intake，不自行领取、定级、结算或合并。
