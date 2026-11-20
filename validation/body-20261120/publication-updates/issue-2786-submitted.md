<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1472"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1472

修复 LongTermMemoryGate 的增量词表缓存遗漏「同 rowid 原地更新正文后再追加节点」的混合情况。先热缓存、改写同一 rowid 的正文并追加一行后，旧 gate 会保留旧 gram、漏掉新 gram；重建 gate 对同库的 novelty 读数不同。现将旧 rowid 摘要纳入追加判定，旧正文变化时完整重建，纯追加仍增量。该场景是 #770 已记录的未覆盖边界；本 PR 补齐该边界，未另开重复源 issue。

验证：PR 当前头的 Python 3.12 主门禁、依赖下界、3.13 与标题检查全通过。本地 novelty/cache 相邻回归 47 passed；新守卫基线 1 failed / 0 passed，修复后 1 passed；具名变异命中预期断言；strict manifest 64/64 MATCH，time_core_lint 23 条既有登记、0 新违规、0 stale。原始本地日志与 JUnit 位于 [workspace]\lingshu\outputs\longterm-gate-mixed-update-20261120。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`a663512dd0fbc44a9fb08a55751951009586d172`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1472/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `novelty_cache`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **116 / 798 → 0 / 798**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：5,000 节点混合改写+追加现在正确地完整重建，中位时延 14.247467 → 241.756767 ms（16.968×，约 16.97 倍）；纯追加仍走增量路径，13.859820 → 16.157400 ms（1.166×）。混合写后的独立 tracemalloc 峰值中位数 1,043,015 → 12,038,190 B（11.542×）；warm 为 906,876 → 1,380,332 B。正确性修复的重建及分配成本如实保留。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only novelty_cache` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
