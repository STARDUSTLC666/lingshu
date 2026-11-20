## 改动说明

修复非正交箱体的 SAT 分离轴构造错误。当前 obb_of() 明确支持归一化后的非正交边方向，但 _sat_axes() 将边方向本身当作箱体面法线；对斜平行六面体这会漏掉真实分离轴，导致相离箱体被报为重叠，并生成不应有的 MTV。修复后使用每个箱体三组边向量的叉积作为面法线，同时保留两箱九组边叉积候选轴。线性相关的 rot 行不能张成三维箱体，现在显式拒绝；非正交且满秩的基仍受支持。

固定复现中，A 的一个面法线上的间隙为 0.0321481，改前 obb_overlap=True 且 obb_mtv 深度 0.2119759，改后判定不相交且 obb_mtv=None。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_obb_nonorthogonal_sat.py tests/test_physics_collision_proxy_guard.py tests/test_issue1133_1134_scene_sim_guard.py -q --no-header -p no:cacheprovider
# 28 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/obb_nonorthogonal_sat_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output [workspace]/lingshu/outputs/obb-nonorthogonal-sat-20261120
# fixed 2 passed; baseline 2 failed; 2/2 named mutations hit their expected assertions

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

使用合成斜箱输入与仓内碰撞代理/场景守卫验证；未做物理引擎或真实资产集成测试。rot 必须是满秩三维基，不要求正交。



python -X utf8 -m pytest tests/test_time_core_lint.py tests/test_issue607_time_core_shapes_guard.py -q --no-header -p no:cacheprovider
# 74 passed; the lint baseline only shifts six pre-existing physics entries by +7 lines (23 entries remain)
