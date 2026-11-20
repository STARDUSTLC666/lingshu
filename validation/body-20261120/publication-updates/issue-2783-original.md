<!-- intake:v1 {"project":"lingshu","difficulty":"easy","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1469"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1469

修复 `motion_groups._group_id()` 对成员名作 `|` 拼接造成的确定性别名：`["a|b", "c"]` 与 `["a", "b|c"]` 代表不同运动组，却得到同一个 `mg_c74a3276c7e3`，core 的 `predict_groups` 因而会混淆两组预测归属。含 `|` 的成员名现以规范 JSON 数组编码及独立 `mg_v2_` 命名空间计算 ID；无分隔符成员保持原 ID。

验证：PR 当前头的 Python 3.12 主门禁、3.12 依赖下界、3.13 门禁与标题检查全部通过。本地新守卫 9 passed，相关回归 74 passed / 1 skipped，strict manifest 64/64 MATCH。锚定基线 `6e9c90bfcba1bfb7c14cdf526611501d526f6777` 重放该守卫为 5 failed / 4 passed；两项具名回退变异均只触发其指定断言。原始本地日志与 JUnit 保存在 `[workspace]\lingshu\outputs\motion-group-id-encoding-20261120`。
