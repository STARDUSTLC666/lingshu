## 无接触时，第二个碰撞箱改变了自由运动

`SceneSimulator._resolve_collisions` 在所有 `hit=False` 时仍把动力学瞬时末速度覆盖成 `净位移/dt`，再重播种初值。公开 API：重力 10、dt=.1、初高 100、第二碰撞箱在 30 米外；十个 tick 全程无接触，实际 y/vy=97.25/-5，而解析解应为 95/-10。减小 dt 不能收敛到正确重力。

本补丁生产代码净增 6 行：按本 tick 实际 `hit=True` 记录收集参与接触的实体；未参与任何接触的 dynamics 实体保留物理内核末速度及原初值。真实接触、static 重叠、运动学及已有接触后的近似语义保持原样。不能只根据最终位置是否变化判断接触，guard 包含“自由端点与推离端点恰好相同”的反例。

## 验证与可重放证据

- 新 guard **41 passed**；同 guard 在精确基线 `d74848fb33dbff1d719959df19d1266a1ac60f44` 上 **32 failed / 9 passed**。
- **6 个具名变异**全部由指定语义断言检出，0 errors/skips，包括错误地只看 pos 相等的伪修复。
- 扩展相邻组合 **243 passed / 0 skipped**；root 独立复跑新 guard **41 passed**。覆盖三轴、4 个 dt、2 个重力、0/1/2 箱、OBB、混合碰撞、两种插入序、初始穿透、t=0 接触、完全重叠、双方 static、末点相切及运动学。
- strict manifest **64/64**；time-core **23 既有 / 0 新 / 0 stale**。
- 真实性能和 Python traced peak：**7 场景、独立 worker、11 个时间样本、3 个内存样本**，保存基线/修复源和全部 worker 输出；默认运动学、有箱运动学、默认动力学和单箱控制的规范输出哈希完全相同。
- 修复后独立解析检查全部通过；错误基线的 8/24 箱和混合场景分别保留 16/48/2 个位置或速度错误。24 箱隔离 worker 延迟比 **1.194**，相邻随机 11 对的中位延迟之比 **1.160**、逐对比值中位数 **1.016**；共享宿主调度波动明显，成本与原样本完整公开，不宣称统一提速。该场景 traced peak 比值 **0.997**，不代表进程 RSS。

完整说明和命令：`docs/testing/scene-collision-freeflight-velocity-20261120.md`；随 PR 提供独立解析 guard、标准 mutation spec 和基准脚本。精确 head 三环境 CI 与包含上一批修复的组合回归证据见文末。

## 查重与范围

检查上游全状态 1307 项、bounty 2194 项，核对最近邻 PR #1162 / bounty #2027：旧件修复参数丢失及 static 重播种，此处是无接触情况下错误覆盖准确末速度。既有切向滑行 bounty #2362 不混入本申报。

本件不改变真实碰撞后的平均位移近似，不新建弹性冲量/摩擦/角动量模型，不声称全部碰撞动力学已符合连续物理。一个 PR 一项 intake；不自行领取、定级、结算或合并。

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
