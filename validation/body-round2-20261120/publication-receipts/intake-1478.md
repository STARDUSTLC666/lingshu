<!-- intake:v1 {"project":"lingshu","difficulty":"hard","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1478"} -->

修复交付：[PR #1478](https://github.com/FuRongJun-1999/lingshu/pull/1478)，精确提交 `89c005b7fdd48f64c603d34c280a4d18a93956f7`。

decay_cycle 的全库游标早于本轮新增行，却把整个旧间隔套给context、knowledge与unverified edge。公开API复现七天游标后新增毫秒级行：context/edge被删除，knowledge 0.5降到约1.81e-89。现在仅在 created_at 可确证位于(last,now]时按该行出生后时间衰减，并保持零时长恒等。

## 已验与原始证据

- 新回归：**48 passed；同一基线guard 25 failed /23 passed，0 errors/skips**。
- **9个具名定点变异**全部在指定业务断言失败，0 errors/skips；不是以导入错误当检出。
- 精确head的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5624 passed /40 skipped /98 subtests**，102/102脚本及真实脑端23/23通过。[原始CI run](https://github.com/FuRongJun-1999/lingshu/actions/runs/44762844376)。40个skip没有冒充通过。
- 独立闭式oracle每个源版本27450个值：修复0错、基线4575错；相关193 pytest+4脚本通过，另一审阅者59项新旧守卫通过。
- [不可变公开证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120)；[本项完整原始工件](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120/audit-core)。源锚/命令/原始JSON、stdout、JUnit、变异summary及全部A/B样本均随证据封存，保留失败和中间迭代。

## 基准成本

12配置，每配置3预热、9时延样本、3独立Python allocation peak；5000节点+2500边的traced peak约+4.27%。全部A/B原始时延和峰值保留，不从调度噪声中的快中位数宣称加速。

以上性能均是共享主机上的描述性样本，不作为显著提速或通用硬件性能证明。

## 未验／不确定／不做

- 未验：长期真实部署效果；完整十二项组合Windows/Linux和额外Linux三环境基准正在另行执行，当前不以未完成任务充作通过，结束后补不可变证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：只对能与既存区间比较的出生时间修复。自定义衰减时钟可与time.time异epoch；未来/无效/缺失/非有限出生时间保留旧global-dt。首次一周期bootstrap和无now离散语义不改。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查上游/bounty并读取#176全文及评论；既有件处理调用次数、连续核与游标回拨，没有处理本轮新生行。已知CSR叠加旧发现仅保留审计历史，没有混入新发现或申报。
