<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1475"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1475

修复身体库与纯标准库动画桥的零初速释放单摆闭式解：原式漏掉 dn 分母/四分之一周期偏移，把真实公式错误误归因于 jacobi_cn 并限制到 5°。在 theta0=120°、omega0=1、t=1、显式 tol_deg=180 的可复现输入下，基线返回 1.1387045287626738 rad，独立 RK4 为 1.645993497151551 rad，绝对误差 0.5072889683888773 rad。

现在使用正确释放解、直接互补模 cos(theta0/2)、稳定 atan2/hypot Landen 下降及周期折叠，支持 |theta0|<π，边界和非有限输入显式拒绝；保留公开 jacobi_cn 的既有数值路径。近分离点的周期真值及公开动画求值路径同步修正，桥仍不依赖 lingshu/numpy/bpy。

验证（精确 PR head e0771a810b8846676f3545542b2e70d5e0011467）：三档完整 gate（Python 3.12、3.12 依赖下界、3.13）及标题检查全部 SUCCESS。相关物理/桥侧/#455 守卫 55 passed / 4 skipped；身体新守卫 6 passed、同一基线 6 failed；桥侧 8 passed、同一基线 7 failed / 1 passed；十一项具名回退变异均命中指定断言，全部回放零 errors/skips。strict manifest 64/64；time lint 保持原有 23 项仅同步两条行号，相关 lint 测试 74 passed。

随 PR 提交可移植 80 位 mpmath 验证脚本：930 个短中期点、40 个超长时点共 6,550 项角度/相位检查通过；69 个独立周期检查通过，2,165 个公开 cn 位级比较无差异，8 项域检查通过。最多约 100.3 周期的样本最大角误差 3.67513e-13 rad；并未将此样本读数声明为任意长时间的全域误差上界。另以真实公开 eval_at(..., motions=...) 的 2,840 组输入/31,240 项断言对照 80 位四元数参考，零失败。原始读数、源码 hash、输入转换误差与性能成本均保留。

复跑命令与边界见 PR 正文及 bench/repro/pendulum_release_accuracy.py。未验证真实 Blender/bpy/GPU 渲染。额外手工物理门的 P1 仍有既有绝对/相对高度断言混比问题，基线与修复版均 10 PASS / 1 FAIL；本次没有用跳过或修改无关断言把它伪装成全绿。维护者定级、验收与合并待审。
