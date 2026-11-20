## 改动说明

修复 LongTermMemoryGate 缓存增量更新只证明“追加”而未核对旧行正文的问题。相同 rowid 的正文原地改写后再追加新行，会导致旧 gram 留在长期记忆参考集中、改写正文的 gram 漏入，常驻 gate 与新建 gate 对同一数据库产生不同 novelty。增量分支现在保留并比较旧 rowid 的正文摘要；任一旧摘要变化就完整重建。纯追加仍保留增量路径。更新了 #770 的边界说明和登记源码指纹。

## 复跑命令与读数

```sh
python -X utf8 -m pytest tests/test_longterm_gate_mixed_in_place_update.py tests/test_issue770_snapshot_atomicity_and_signature_guard.py tests/test_issue462_longterm_gate_cache_stale_guard.py tests/test_longterm_gate_novelty.py tests/test_longterm_gate_p1_defects.py tests/test_issue587_gate_sql_clamp.py tests/test_issue2379_guard.py tests/test_issue573_novelty_template_guard.py -q --no-header -p no:cacheprovider
# 47 passed

python -X utf8 tools/testing/replay_save_guards.py --spec tests/fixtures/longterm_gate_mixed_in_place_update_mutations.json --baseline d74848fb33dbff1d719959df19d1266a1ac60f44 --mutate --output [workspace]/lingshu/outputs/longterm-gate-mixed-update-20261120
# fixed: 1 passed; baseline: 1 failed; named mutation hit its expected assertion

python -X utf8 tools/time_core_lint.py --json
# exit 0; 23 registered, 0 new, 0 stale

python -X utf8 tools/verify_manifest.py --strict --quiet
# 64/64 MATCH; exit 0
```

## 未验证项 / 边界

验证覆盖同 rowid 更新后再追加的缓存形态及相邻 novelty/删除/追加守卫；未做大库性能基准。摘要校验复用签名扫描时已计算的逐行摘要，仍需线性遍历现存正文。
