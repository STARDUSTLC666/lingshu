# 身体侧 world 审计第二轮：一条可交付候选

- 只读基线：`d74848fb33dbff1d719959df19d1266a1ac60f44`。
- 审计工作树：`[workspace]/lingshu/work\lingshu-audit-core-20261120`，开始与结束 `git status --short` 均为空。
- 解释器：`[workspace]/lingshu/work\lingshu-body-final-validation-20261120-venv\Scripts\python.exe`。
- 本轮只在本目录写探针/JSON/报告；未改生产源码、未 commit、未发 issue/PR。

## 候选：没有任何接触时，第二个碰撞箱使物理加速度永久减半

**建议优先修复**：`lingshu/world/scene_simulator.py:991-1005` 的 `_resolve_collisions`。

场景只要有至少两个登记碰撞箱，碰撞后处理会遍历所有带箱实体，即使全部 `hit=False`，也把动力学实体的 `velocity` 无条件改成 `本 tick 净位移 / dt`，随后 `_reseed_physics` 把这个平均速度作为下一 tick 的瞬时初速。平均速度不等于恒加速运动的末速度，因此自由落体每 tick 只增加半个应有的重力速度。解析物理本身给出了正确末速度；同 tick 的 `physics_readout['vel']` 与外部 `entity.velocity` 当场矛盾。

触发完全用公开 API：`SceneSimulator` → `set_environment(gravity=10, dt=.1)` → `add_entity` → 标记 `attrs['physics']='dynamics'` → `set_entity_physics(p0=(10,100,10),v0=(1,0,0))` → 给球与 30 米外静止墙登记半宽 `.25` 的碰撞箱 → `step(1)`。

解析 oracle 独立写为 `p_y(t)=y0+v0_y*t-g*t*t/2`、`v_y(t)=v0_y-g*t`，不调用本仓 `physics` 来产生预期。

| 场景 | tick 1 y / vy | tick 10 y / vy | 10 tick 接触 |
|---|---|---|---|
| 0 碰撞箱 | 99.95 / -1 | 95 / -10 | 0 |
| 1 碰撞箱 | 99.95 / -1 | 95 / -10 | 0 |
| 2 碰撞箱 | 99.95 / -0.5 | 97.25 / -5 | 0 |

tick 1 的动力学读数仍为 `vel=(1,-1,0)`，实体已被碰撞后处理改成约 `(1,-.5,0)`。

### 范围验证

`freefall_matrix.py`：碰撞箱数 0/1/2 × dt `.01,.05,.1,.25,.5,1` × g `.1,1,9.80665,20`，每场景 10 tick，共 72 场景、720 tick：

- 0 箱 24 场景：240/240 位置和速度均通过解析 oracle。
- 1 箱 24 场景：240/240 位置和速度均通过解析 oracle。
- 2 箱 24 场景：0 真实接触，但 216/240 位置错误、240/240 速度错误；第一 tick 位置尚正确。
- 所有初值、结果有限，位置远离地面及 x/z 边界，排除钳制和初始穿透。
- 总时间 1 秒、g=10 的细化试验：dt `.1/.01/.001` 的位置误差为 `2.25/2.475/2.4975` 米、末速度误差约 `5` 米/秒；缩小 dt 不收敛到原物理。这不是允许的一阶积分误差。

邻接现有守卫：`test_issue1959_reseed_physics_guard.py`、`test_scene_sim_environment_guard.py`、`test_issue1133_1134_scene_sim_guard.py`、`test_issue1135_scene_sim_readings.py`，**35 passed / 0 skipped**，日志 `neighbor-35.log`。现有守卫确实漏报本缺陷。

### 既有契约与可能争议

- `scene_simulator.py:40-43`、`:833-835` 明说动力学实体保存物理速度，避免把量化误差馈回下一 tick；`:726-733` 明说逐 tick 保留初值而不是反复伪积分。
- `_reseed_physics` 自身文档 `:939-941` 将重播种的必要性限定为**碰撞修正后**，以免旧闭式初值再穿一次。这里从未命中、从未修正，却强行覆盖速度与初值。
- 邻接旧修复 PR #1162 只解决 `beta/radius/mass` 丢失和 static 重播种，不解决平均速度。旧守卫末段写了“不比较有箱/无箱轨迹，因为重播种设计上应不同”。这句论据在**没有任何碰撞**且使用准确瞬时末速度时不成立：自由落体解析半群性保证任意时刻重播种轨迹相同。不要通过修改 oracle 迎合该旧注释。
- 最小修复方向：无碰撞修正者保留内核物理速度及原初值，仅对真实发生位置修正/拦停的实体做接触速度更新与重播种；需特别处理初始重叠、接触后滑移、多箱链路和静态物体，不能只测试自由落体。

### 查重结果

用 GitHub REST 全状态 Issues API 逐页拉取上游 **1307 项（含 PR）**、bounty **2194 项**，原始快照分别为 `lingshu-all-issues.json` / `bounty-all-issues.json`。按 `_resolve_collisions`、`_reseed_physics`、`physics_state`、无接触/无碰撞、平均速度、自由落体、half gravity、切向等在标题和正文检索。

- 最近邻：上游 PR #1162（`_reseed_physics` 保 beta/radius/mass + static），以及 bounty #2027 对该 PR 的复验。已读两者完整正文及 #1162 issue/review comments（空），#2027 全部评论（仅 diffstat 勘误/结算）；不是本条加速度/平均速度发现。
- 原 PR #697 已明确碰撞只做位移推离、不做摩擦/冲量，但没有声明无接触也要重写自由飞行物理，故本候选不依赖引入弹性碰撞等新物理。
- 未见对应的“无接触平均速度覆盖正确末速度/半重力”发现或补丁。此阴性结果覆盖已获取标题正文和上述最近邻评论；不声称读取了全仓所有评论。
- #1959 的原单链接在镜像 PR 中未给出，直接查询 `FuRongJun-1999/dsh-bounty#1959` 返回不可解析，故不编造其原始内容；以可读 PR #1162 与已结算复验 #2027 判断已知范围。

## 排除：切向滑行丢失已有 bounty 记录

`reproduce_scene_collision.py` 同时复现了斜向撞静态墙在 toi=0/.25/.5/.75 丢失后半段切向运动；两法向轴均发生。另见代码滑行公式与注释代数不一致，但当前示例先被 normal 符号门排除，实际走无条件 `toi` 回退，不能把该读数归因于尚未执行的公式。

已存在 bounty **#2362**《新发现：lingshu #1133 现象三（斜向碰撞切向滑行丢失）——main 上仍可复现（纯法向回退 dx=0）》。无论该单原始探针本身是否充分，本条症状已经报过，**不作为本轮新发现 claim**。上游 PR #1138 / bounty #2006 也明确留了现象三未覆盖。

## 不新增申报：物理预测层缺测年龄

`physics_predict.wrap_generate` 从 last observed tick 推 horizon，缺测后可能与 target_tick 不同；但 `world_model.py:2540-2548` 已显式把该层标为 opt-in，列明 long-occlusion 与 multistep target-tick 三项现有红及待办。属于源内已知面，本轮不包装成新发现。

