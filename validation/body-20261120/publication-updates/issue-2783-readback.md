<!-- intake:v1 {"project":"lingshu","difficulty":"easy","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1469"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1469

修复 `motion_groups._group_id()` 对成员名作 `|` 拼接造成的确定性别名：`["a|b", "c"]` 与 `["a", "b|c"]` 代表不同运动组，却得到同一个 `mg_c74a3276c7e3`，core 的 `predict_groups` 因而会混淆两组预测归属。含 `|` 的成员名现以规范 JSON 数组编码及独立 `mg_v2_` 命名空间计算 ID；无分隔符成员保持原 ID。

验证：PR 当前头的 Python 3.12 主门禁、3.12 依赖下界、3.13 门禁与标题检查全部通过。本地新守卫 9 passed，相关回归 74 passed / 1 skipped，strict manifest 64/64 MATCH。锚定基线 `6e9c90bfcba1bfb7c14cdf526611501d526f6777` 重放该守卫为 5 failed / 4 passed；两项具名回退变异均只触发其指定断言。原始本地日志与 JUnit 保存在 `[workspace]\lingshu\outputs\motion-group-id-encoding-20261120`。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`cc68a82baace16e92ff6ce770330b65102a530a5`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1469/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `motion_groups`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **81 / 165 → 0 / 165**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：8 帧 × 96 实体检测批次的中位时延为 17.678667 → 20.047600 ms（1.134×）；独立 tracemalloc 峰值中位数 573,832 → 574,956 B。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only motion_groups` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
