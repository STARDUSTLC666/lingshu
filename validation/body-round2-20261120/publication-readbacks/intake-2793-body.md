<!-- intake:v1 {"project":"lingshu","difficulty":"hard","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1479"} -->

修复交付：[PR #1479](https://github.com/FuRongJun-1999/lingshu/pull/1479)，精确提交 `13952c82874fb9ee19a4f1b660e3144134367a53`。

SceneSimulator在登记至少两个碰撞箱后，即使全程hit=False也以净位移/dt覆盖真实末速度再重播种。重力10、dt=.1、初高100的自由落体十tick变成y97.25/vy-5，解析应为95/-10。补丁只让未参与任何hit的动力学实体保留物理末速度与原初值；真实接触仍走原处理。

## 已验与原始证据

- 新回归：**41 passed；同一基线guard 32 failed /9 passed，0 errors/skips**。
- **6个具名定点变异**全部在指定业务断言失败，0 errors/skips；不是以导入错误当检出。
- 精确head的三环境完整CI（3.12常规/依赖下界、3.13）与标题均SUCCESS；每腿 **5617 passed /40 skipped /98 subtests**，102/102脚本及真实脑端23/23通过。[原始CI run](https://github.com/FuRongJun-1999/lingshu/actions/runs/44763098857)。40个skip没有冒充通过。
- 三轴、4dt、2重力、0/1/2箱、OBB、混合真实接触、初始重叠、t=0、static及相切边界均覆盖；扩展243 passed。错误地只看pos相等的伪修复也被具名变异准确抓住。
- [不可变公开证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120)；[本项完整原始工件](https://github.com/STARDUSTLC666/lingshu/tree/f769b3ac33eb5221ad66f6a4384aa6429b26e597/validation/body-round2-20261120/audit-world)。源锚/命令/原始JSON、stdout、JUnit、变异summary及全部A/B样本均随证据封存，保留失败和中间迭代。

## 基准成本

7场景独立worker，11个时延和3个内存样本；24箱隔离延迟比1.194，相邻随机11对的中位延迟之比1.160、逐对比值中位数1.016，完整原始波动保留；该场景traced peak比0.997，不代表RSS。

以上性能均是共享主机上的描述性样本，不作为显著提速或通用硬件性能证明。

## 未验／不确定／不做

- 未验：长期真实部署效果和仍缺原始资产的17个用例。完整组合Windows/Linux及额外Linux基准的实际结果、失败与跳过见文末最终证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：真实接触后的平均位移速度近似仍为已有语义；未新增弹性冲量/摩擦/角动量模型，也未声称所有接触动力学已符合连续物理。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查1307项上游和2194项bounty，核对PR#1162/bounty#2027，其修复参数丢失及static重播种，与此无接触平均速度不同。切向滑行bounty#2362不纳入。

<!-- body-round2-final-evidence:v1 -->

## 最终组合验证与不可变证据（2026-11-21）

本项当前源提交 `13952c82874fb9ee19a4f1b660e3144134367a53`；对应 bounty 仍是原 issue #2793，没有另建或拆分申报。

[最终完整证据总索引](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120)；[本项工件](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/audit-world)；[结果与边界总表](https://github.com/STARDUSTLC666/lingshu/tree/83496a7f49ede450729cb944fec36a0fbbafec6f/validation/body-round2-20261120/FINAL_VALIDATION.md)。证据提交 `83496a7f49ede450729cb944fec36a0fbbafec6f`。

- 冻结的十二项组合源 `5226860c1d70bc7fc6619cf79aff10c4f9a2a234`：独立重建核对十个生产文件、29 个变更函数；本轮 165 项守卫通过，27 个具名变异由指定语义断言检出。各 PR 的精确 head CI 原始记录亦保留。
- 完整组合 Linux [run 44764384747](https://github.com/STARDUSTLC666/lingshu/actions/runs/44764384747)：三个环境各 **5827 passed / 40 skipped / 98 subtests**，各 102/102 脚本及实际固定脑端 23/23。
- 完整组合 Windows 实测 **5838 passed / 1 failed / 28 skipped / 98 subtests**，102/102 脚本通过，原驱动 `gate_ok=false` 保持不变。唯一失败是既有 symlink 能力 P1 的 POSIX 断言，精确旧基线也在本机独立复现；不将它改写成全绿。另做历史物理守卫 43 passed、原 symlink 测试体 3/3 和串行计时 4 passed，均不叠加主计数。
- 额外 Linux [基准/变异 run 44778606930](https://github.com/STARDUSTLC666/lingshu/actions/runs/44778606930)：三个环境各完成四项 A/B 基准及同 27 个具名变异；实际源哈希、原始样本、stdout/stderr、JUnit 和内层工件长度/哈希已独立核对。早期 run 44766869622 的测量和旧索引问题作为中间记录保留。
- 成本按前文及原始 JSON 如实保留，包括增加的 Python traced peak；共享主机数据只描述本次测量，不主张统一提速、统计显著性或 RSS。仍缺 17 个原始模型/像素资产用例，未伪造资产；长期真实部署效果仍未验证。各环境和补充运行有重叠，不能把计数相加当独立覆盖。

<!-- /body-round2-final-evidence:v1 -->
