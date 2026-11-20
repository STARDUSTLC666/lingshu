<!-- intake:v1 {"project":"lingshu","difficulty":"medium","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1471"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1471

修复 OBB SAT 对支持的非正交三维基使用边方向代替面法线，漏掉真实分离轴的问题。固定输入下 A 面法线分离间隙为 0.0321481，改前 obb_overlap=True、obb_mtv 深度 0.2119759，改后不相交、obb_mtv=None。当前 rot 行仍可非正交，但必须满秩以定义三维箱体。

验证：PR 当前头三档 Python gate 与标题检查全通过；OBB/场景守卫 28 passed，新增基线回归 2 passed，定点变异 2/2 命中预期断言；time_core_lint 74 passed，23 条既有登记无新增；严格 manifest 64/64 MATCH。因 physics.py 插入行导致的 6 条既有 lint 行号只整体后移 7 行，登记数不变。原始日志在 [workspace]\lingshu\outputs\obb-nonorthogonal-sat-20261120。
