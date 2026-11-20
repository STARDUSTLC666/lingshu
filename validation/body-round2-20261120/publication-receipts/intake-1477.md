<!-- intake:v1 {"project":"lingshu","difficulty":"hard","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1477"} -->

修复交付：[PR #1477](https://github.com/FuRongJun-1999/lingshu/pull/1477)，精确提交 `e821bbb1fac57fa638640e3caf153caf7f1b1973`。

fit_circular 对绝对时间回归后把 t=0 截距当作 t_ref 高度，平移到 t=10 后初高3变成-17，Unix时间戳下还可能拟合奇异；纵向残差遗漏则让明显错误的螺旋在 classify 中冒充近零误差。本件改为本地时间回归并按三坐标计入全部残差，保留旧世界轴序修复。

## 已验与原始证据

- 新回归：**6 passed；同一基线guard 6 failed，0 errors/skips**。
- **6个具名定点变异**全部在指定业务断言失败，0 errors/skips；不是以导入错误当检出。
- 精确head的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5582 passed /40 skipped /98 subtests**，102/102脚本及真实脑端23/23通过。[原始CI run](https://github.com/FuRongJun-1999/lingshu/actions/runs/44761889152)。40个skip没有冒充通过。
- 独立解析666场景、7146条断言0失败；基线1530失败（包括216次拟合异常），另2160条后续预测检查因异常未执行，未记为通过。
- [不可变公开证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120)；[本项完整原始工件](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120/audit-circular)。源锚/命令/原始JSON、stdout、JUnit、变异summary及全部A/B样本均随证据封存，保留失败和中间迭代。

## 基准成本

两轮共享主机、每尺寸9组交错样本：25/100/1000点修复/基线中位耗时比分别1.003–1.032/1.017–1.037/1.000–1.036；traced peak 5168→6136、10008→13384、71316→104228B。完整样本均在原始JSON。

以上性能均是共享主机上的描述性样本，不作为显著提速或通用硬件性能证明。

## 未验／不确定／不做

- 未验：长期真实部署效果；完整十二项组合Windows/Linux和额外Linux三环境基准正在另行执行，当前不以未完成任务充作通过，结束后补不可变证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：没有覆盖倾斜圆、采样角混叠或任意病态空间坐标；已存错误模型需从观测重拟合，未自动重写历史数据。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

已查上游和bounty，逐条读#786/#817评论与#829。旧件是center世界序/打包序；本件保留其修复，处理时间锚与漏算纵向残差，不重复申报旧发现。
