## 改动说明

修复技能检索 limit 语义不一致。search_skills() 原样把 limit 用在 Python 切片；负值会静默丢尾项（-1 少一项，-6 变空），而同仓检索接口已约定 None/负数表示全量、0 表示空。现在复用 _normalize_limit()，search_skills 与 recall_skill 都按同一约定返回。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_search_skills_limit_semantics.py tests/test_bounty1795_search_limit_semantics.py tests/test_issue658_limit_none_full_return_guard.py tests/test_batch121_search_skills_gate_guard.py -q --no-header -p no:cacheprovider
# 15 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/search_skills_limit_semantics_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output [workspace]/lingshu/outputs/search-skills-limit-20261120
# fixed 1 passed; baseline 1 failed; named mutation hit its expected assertion

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

验证使用公开技能写入/召回接口的合成技能卡；已补 100/1,000/5,000 张合成技能卡的 CPU 时延与独立内存探针；未验证生产技能库的真实查询分布。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`fb6c9cabc939a6defcc44ef661b3048d47155d87`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1474/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `skill_limit`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **30 / 110 → 0 / 110**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：5,000 张技能卡、limit=-1 的中位查询时延 5.920730 → 5.656275 ms（0.955×）；独立 tracemalloc 峰值中位数均为 77,655 B。原有 100 行候选池上限保留，负数/None 不代表绕过候选池。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only skill_limit` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
