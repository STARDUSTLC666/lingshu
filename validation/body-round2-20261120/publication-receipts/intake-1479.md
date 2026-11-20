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

- 未验：长期真实部署效果；完整十二项组合Windows/Linux和额外Linux三环境基准正在另行执行，当前不以未完成任务充作通过，结束后补不可变证据。
- 不确定：共享主机时延差异的统计显著性；最终采纳、归类及计分由维护者裁定。
- 范围边界：真实接触后的平均位移速度近似仍为已有语义；未新增弹性冲量/摩擦/角动量模型，也未声称所有接触动力学已符合连续物理。
- 不做：不自行/claim、不加bounty/intake标签、不结算、不合并。difficulty/impact仅是intake输入字段。一个完整PR申报一项贡献，不把参数组合或守卫数量拆成多项。

## 查重声明

检查1307项上游和2194项bounty，核对PR#1162/bounty#2027，其修复参数丢失及static重播种，与此无接触平均速度不同。切向滑行bounty#2362不纳入。
