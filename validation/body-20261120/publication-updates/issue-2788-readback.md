<!-- intake:v1 {"project":"lingshu","difficulty":"easy","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1474"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1474

修复 search_skills()/recall_skill() 的负数 limit 被 Python 负切片解释，导致命中静默丢尾的问题。5 张匹配技能卡中，limit=-1 原先只返回 4 张，limit=-6 返回空；现在复用仓内 _normalize_limit，None/负数返回现有候选全集，0 返回空，正数仍限制条数。100 行候选池边界保持不变。

验证：PR 当前头 fb6c9cabc939a6defcc44ef661b3048d47155d87 的三档 Python gate 与标题检查全通过。本地相关检索守卫 15 passed；同一新守卫基线 1 failed、修复后 1 passed，具名回退变异命中指定断言；strict manifest 64/64 MATCH。复跑命令见 PR 正文；原始日志和 JUnit 在 [workspace]/lingshu/outputs/search-skills-limit-20261120。维护者定级与验收待审。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`fb6c9cabc939a6defcc44ef661b3048d47155d87`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1474/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `skill_limit`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **30 / 110 → 0 / 110**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：5,000 张技能卡、limit=-1 的中位查询时延 5.920730 → 5.656275 ms（0.955×）；独立 tracemalloc 峰值中位数均为 77,655 B。原有 100 行候选池上限保留，负数/None 不代表绕过候选池。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only skill_limit` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
