<!-- intake:v1 {"project":"lingshu","difficulty":"hard","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1480"} -->

修复交付：[PR #1480](https://github.com/FuRongJun-1999/lingshu/pull/1480)，精确提交 `a357dbbe96905848fd81b7249814576fb2743674`。

spatial_detect重复floor(n/3)宽度，非3整除晶格的尾部同时从能量和分类裁片消失。公开48×48图像→18×16晶格的最后蓝列会丢失。现在缩放每条三分边界使cell恰好覆盖一次，并按真实区域面积设置追加门槛，避免完整分区面积不等时把均匀色场误报成多个对象。

## 已验与原始证据

- 新回归：**最终70 passed；同一基线guard 59 failed /11 passed，0 errors/skips**。
- **6个具名定点变异**全部在指定业务断言失败，0 errors/skips；不是以导入错误当检出。
- 精确head的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5646 passed /40 skipped /98 subtests**，102/102脚本及真实脑端23/23通过。[原始CI run](https://github.com/FuRongJun-1999/lingshu/actions/runs/44764764765)。40个skip没有冒充通过。
- 独立裁片oracle覆盖400种尺寸、44100个cell，0遗漏/0重复/0异常；真实HexHierNet和image_to_grid→multimodal路径通过；最终相关143 passed、contracts14/14。可整除控制输出SHA完全相同。
- [不可变公开证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120)；[本项完整原始工件](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120/audit-numeric/r2)。源锚/命令/原始JSON、stdout、JUnit、变异summary及全部A/B样本均随证据封存，保留失败和中间迭代。

## 基准成本

每尺寸3预热+9时延+3独立峰值。2×18×18基线/修复0.548/0.467ms，2×18×16为0.362/0.350ms，2×65×67为2.033/2.119ms；traced peak各+40B。R1和最终R2全部保留，不选择性覆盖。

以上性能均是共享主机上的描述性样本，不作为显著提速或通用硬件性能证明。

## 未验／不确定／不做

- 未验：长期真实部署效果；完整十二项组合Windows/Linux和额外Linux三环境基准正在另行执行，当前不以未完成任务充作通过，结束后补不可变证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：空空间返回每样本空清单；没有新增非有限输入或任意网络协议验证，也不从透明小网络对照声称真实世界识别精度。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查上游/bounty并读#116/#860/#1435/#24及PR#1439：旧件是采样坐标、数量约束或桥接增量，不包含尾部完整分区；不把这些已有发现重新申报。
