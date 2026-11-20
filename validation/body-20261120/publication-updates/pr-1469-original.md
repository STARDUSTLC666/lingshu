## 改动说明

修复 `motion_groups._group_id()` 将成员名用 `|` 拼接后再哈希造成的确定性碰撞。例如 `["a|b", "c"]` 与 `["a", "b|c"]` 是两组不同成员，却会得到同一 group ID；经 core 的 `predict_groups` 时会混淆两组预测归属。含分隔符的成员名现在使用规范 JSON 数组编码和独立的 `mg_v2_` 前缀，普通成员名保持原 group ID。新增回归守卫与定点变异夹具，并刷新已登记的源码指纹。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_motion_group_identifier_encoding.py -q --no-header -p no:cacheprovider
# 9 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/motion_group_identifier_encoding_mutations.json --baseline 6e9c90bfcba1bfb7c14cdf526611501d526f6777 --mutate --output artifacts/motion-group-id-encoding-20261120
# fixed: 9 passed; baseline: 5 failed / 4 passed; 2/2 named mutations failed at their expected assertions

python -X utf8 -m pytest tests/test_motion_group_identifier_encoding.py tests/test_motion_groups.py tests/test_motion_group_anchor_consistency.py tests/test_world_process_core.py tests/test_issue2152_2160_family_guard.py -q --no-header -p no:cacheprovider
# 74 passed, 1 skipped

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

未用生产轨迹验证。为避免改变现有消费者看到的普通成员组 ID，仅分隔符成员改用新编码；12 位截断哈希仍不承诺不存在一般哈希碰撞。
