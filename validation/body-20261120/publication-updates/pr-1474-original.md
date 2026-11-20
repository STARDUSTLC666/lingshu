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

验证使用公开技能写入/召回接口的合成技能卡；未对技能库规模做性能基准。
