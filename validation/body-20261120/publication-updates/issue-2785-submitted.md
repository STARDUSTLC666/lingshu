<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1471"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1471

修复 OBB SAT 对支持的非正交三维基使用边方向代替面法线，漏掉真实分离轴的问题。固定输入下 A 面法线分离间隙为 0.0321481，改前 obb_overlap=True、obb_mtv 深度 0.2119759，改后不相交、obb_mtv=None。当前 rot 行仍可非正交，但必须满秩以定义三维箱体。

验证：PR 当前头三档 Python gate 与标题检查全通过；OBB/场景守卫 28 passed，新增基线回归 2 passed，定点变异 2/2 命中预期断言；time_core_lint 74 passed，23 条既有登记无新增；严格 manifest 64/64 MATCH。因 physics.py 插入行导致的 6 条既有 lint 行号只整体后移 7 行，登记数不变。原始日志在 [workspace]\lingshu\outputs\obb-nonorthogonal-sat-20261120。

<!-- body-validation-20261120:expanded:start -->
## 2026-11-20 扩展验证（固定证据）

精确当前 head：`39d379552f34026ef46ad0515831319b1494a5d3`。该 head 的 Python 3.12、3.12 依赖下界、3.13 三档完整 gate 及标题检查均已 SUCCESS；见[固定 CI 快照](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/ci-all-eight.json)和[PR 检查页](https://github.com/FuRongJun-1999/lingshu/pull/1471/checks)。PR/申报仍待维护者审核、合并与验收。

- 独立套件 `obb_sat`：以 `d74848fb33dbff1d719959df19d1266a1ac60f44` 为基线，失败项 / 实际执行断言为 **8 / 2113 → 0 / 2092**。输入被拒绝或执行分支不同会使两个版本的断言数不同，按原始计数保留，不强行对齐分母。
- 时延与内存：512 对 overlap 批次的中位时延 18.748800 → 18.500000 ms（0.987×）；512 对斜箱的独立 tracemalloc 峰值中位数 12,320 → 8,824 B。这些样本不构成普遍提速或内存降低承诺。
- [完整正确性与 latency 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/report.md)、[独立 memory 报告](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/memory_report.md)、[可移植复跑用法](https://github.com/STARDUSTLC666/lingshu/blob/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/six-fixes/README.md)。将两个脚本放在同一目录，分别用 `--only obb_sat` 选择本套件；每次必须显式给 `--output`，不替换缺失的精确源提交。

测量范围：合成 CPU/内存 SQLite 负载，共享主机、未固定 CPU 亲和性或功耗方案；时延为描述性样本，不作统计显著性或普遍加速承诺。内存探针与时延分开，tracemalloc 可漏掉 Pillow/SQLite 原生缓冲，进程 working set 也不是单次调用的专属峰值。真实资产、生产数据库、Blender/bpy 与 GPU 范围仍未验证。
本地整体门禁不宣称全绿：既有 [Windows symlink P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/integration-six)及[手工物理门 P1](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120/manual-physics)的失败和原始基线证据保留，没有为本修复跳过或改写无关判据。本段不提供最终八项 r2 的完成计数。[固定公开证据总目录](https://github.com/STARDUSTLC666/lingshu/tree/a9fe000938a536134f4a21f83b4a633afe8413e5/validation/body-20261120)。
<!-- body-validation-20261120:expanded:end -->
