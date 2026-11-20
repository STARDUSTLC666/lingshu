<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1472"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1472

修复 LongTermMemoryGate 的增量词表缓存遗漏「同 rowid 原地更新正文后再追加节点」的混合情况。先热缓存、改写同一 rowid 的正文并追加一行后，旧 gate 会保留旧 gram、漏掉新 gram；重建 gate 对同库的 novelty 读数不同。现将旧 rowid 摘要纳入追加判定，旧正文变化时完整重建，纯追加仍增量。该场景是 #770 已记录的未覆盖边界；本 PR 补齐该边界，未另开重复源 issue。

验证：PR 当前头的 Python 3.12 主门禁、依赖下界、3.13 与标题检查全通过。本地 novelty/cache 相邻回归 47 passed；新守卫基线 1 failed / 0 passed，修复后 1 passed；具名变异命中预期断言；strict manifest 64/64 MATCH，time_core_lint 23 条既有登记、0 新违规、0 stale。原始本地日志与 JUnit 位于 [workspace]\lingshu\outputs\longterm-gate-mixed-update-20261120。
