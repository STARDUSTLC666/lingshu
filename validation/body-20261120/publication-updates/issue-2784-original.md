<!-- intake:v1 {"project":"lingshu","difficulty":"easy","impact":"B","target":"FuRongJun-1999/lingshu","form":"intake","pr":"https://github.com/FuRongJun-1999/lingshu/pull/1470"} -->

PR: https://github.com/FuRongJun-1999/lingshu/pull/1470

修复 darkline() / linework() 丢弃 alpha 的问题。RGBA 与带 palette transparency 的透明黑底线稿，隐藏 RGB 值原先参与检测；透明黑底上 16 像素的可见黑线产生 0 个黑色线稿像素。修复后先将 alpha 图像合成到白底再检测，opaque RGB/RGBA 保持原结果。

验证：PR 当前头的 Python 3.12、3.12 依赖下界、3.13 全量门禁及标题检查全通过。本地相关 vision 回归 52 passed；新守卫 4 passed，基线 3 failed / 1 passed；三项具名回退变异均只触发其指定断言；strict manifest 64/64 MATCH。日志与 JUnit 位于 [workspace]\lingshu\outputs\vision-lineart-alpha-20261120。
