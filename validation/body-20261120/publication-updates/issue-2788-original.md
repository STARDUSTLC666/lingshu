<!-- intake:v1 {"project":"lingshu","difficulty":"easy","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1474"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1474

修复 search_skills()/recall_skill() 的负数 limit 被 Python 负切片解释，导致命中静默丢尾的问题。5 张匹配技能卡中，limit=-1 原先只返回 4 张，limit=-6 返回空；现在复用仓内 _normalize_limit，None/负数返回现有候选全集，0 返回空，正数仍限制条数。100 行候选池边界保持不变。

验证：PR 当前头 fb6c9cabc939a6defcc44ef661b3048d47155d87 的三档 Python gate 与标题检查全通过。本地相关检索守卫 15 passed；同一新守卫基线 1 failed、修复后 1 passed，具名回退变异命中指定断言；strict manifest 64/64 MATCH。复跑命令见 PR 正文；原始日志和 JUnit 在 [workspace]/lingshu/outputs/search-skills-limit-20261120。维护者定级与验收待审。
