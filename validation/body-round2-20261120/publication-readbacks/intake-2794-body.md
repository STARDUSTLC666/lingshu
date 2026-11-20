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

- 未验：长期真实部署效果和仍缺原始资产的17个用例。完整组合Windows/Linux及额外Linux基准的实际结果、失败与跳过见文末最终证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：空空间返回每样本空清单；没有新增非有限输入或任意网络协议验证，也不从透明小网络对照声称真实世界识别精度。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查上游/bounty并读#116/#860/#1435/#24及PR#1439：旧件是采样坐标、数量约束或桥接增量，不包含尾部完整分区；不把这些已有发现重新申报。

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
