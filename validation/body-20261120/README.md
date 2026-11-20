# 身体库修复：可复跑验证证据（2026-11-20）

本分支保存测试与测量证据，不是合并实现的发布分支，不单独申请 bounty。七个实现分别在上游 PR #1469–#1475。未改动生产数据库或真实用户资产。

| PR | 问题 | 被测精确提交 |
|---|---|---|
| #1469 | Motion group 成员分隔符造成 ID 碰撞 | cc68a82baace16e92ff6ce770330b65102a530a5 |
| #1470 | 透明线稿丢失 alpha，含 RGBa/La 扩展 | 433befa7b356eebecbc457ecd8f8a123ec1540cc |
| #1471 | 斜 OBB 的 SAT 面法线错误 | 39d379552f34026ef46ad0515831319b1494a5d3 |
| #1472 | 改写旧记录同时追加时 novelty 缓存过期 | a663512dd0fbc44a9fb08a55751951009586d172 |
| #1473 | odd-r 六角网格最近格点未比较相邻行 | cff189b3438623feaebdf1a874fafdd03080acb1 |
| #1474 | 技能检索负数 limit 被当作负切片 | fb6c9cabc939a6defcc44ef661b3048d47155d87 |
| #1475 | 零初速释放单摆公式与近分离点精度 | aa18885c933dfd49d8c23a288726158de1bc7c03 |

基线均为 `d74848fb33dbff1d719959df19d1266a1ac60f44`。克隆仓库后需要先 fetch 上表提交（例如添加贡献者 fork remote 并 fetch 对应分支，或 fetch 上游 `refs/pull/<编号>/head`），不可把缺失的提交静默替换为本地主线。

## 六项正确性、性能与内存

- [可移植用法](six-fixes/README.md)
- [正确性与时延报告](six-fixes/report.md)：修复版 15,455 项断言无失败；基线共 889 项失败。各版本的检查数会因基线输入拒绝而不同，按套件原样记录。
- [独立内存报告](six-fixes/memory_report.md)
- [原始时延数据](six-fixes/raw)、[原始内存数据](six-fixes/memory_raw)、[归档来源清单](six-fixes/snapshot-manifests)

固定随机种子为 20261120。每个版本从精确提交 `git archive` 到独立目录并核验导入路径与源码哈希；包含正常输入、边界、独立几何/像素参考和缓存状态序列。时延为 3 次预热 + 9 次保留样本，内存单独运行 3 次。主机共享 CPU，没有固定亲和性或功耗方案，读数仅描述本次样本。

性能退化同样保留：混合改写+追加的 novelty 缓存现在正确全量重建，时间与峰值分配增加；纯追加仍使用增量路径。tracemalloc 不能覆盖所有 Pillow/SQLite 原生缓冲；进程 working-set 快照不能视作单次操作的专属峰值。

## 单摆与公开动画入口

- [80 位角度、周期、RK4 与性能报告](pendulum/report.md)
- [可移植精度脚本](pendulum/pendulum_release_accuracy.py)：在 Python 3.12+ 的独立环境中装 `mpmath==1.4.1`，运行 `python <脚本> --repo <PR1475工作树> --output <输出目录>`。
- [身体侧具名变异回放](pendulum-guards/summary.json)、[桥侧具名变异回放](bridge-guards/summary.json)：身体 6/6 与桥侧 8/8 通过；原基线分别 6 失败、7 失败/1 通过；十一项指定变异均触发指定断言，零 errors/skips。
- [独立标准库复核](pendulum-review/review_results.txt)：随机 RK4、周期/对称性质与公有 cn 位级兼容。
- [公开四元数入口的 80 位参考](bridge-oracle/report.md)：2,840 次真实 `eval_at(..., motions=...)` 调用、31,240 项断言无失败。输入时间转换误差单列。

930 个短中期点、40 个超长时点共 6,550 项角度/相位检查通过；不把最多约 100 周期的样本精度当作任意长时间的浮点误差上界。69 个周期样本与高精度椭圆积分比较通过。接近 π 时双精度 RK4 自身可能停滞，使用 80 位参考而非把 RK4 当作极限振幅的唯一真值。

## 完整组合门禁

[首轮六项组合的原始记录](integration-six/summary.json)覆盖 YAML 的 102 个脚本（含固定脑核真实 23/23）及全部 pytest：5,590 通过、46 跳过、98 个 subtest 通过、1 失败。唯一失败是 `test_issue498_atomic_write_perm_symlink_guard.py` 在可创建 symlink 的 Windows 上仍断言 POSIX；[未改动上游的同一失败](integration-six/baseline_symlink.log)原样保留。不以该结果声称整个 Windows suite 全绿。

## 数据完整性

公开副本仅将本地工作区/家目录路径前缀替换为占位符；测量值、输入值、源码哈希、种子与结论保留。每个公开文件及本机原始文件的校验值见 [sanitization-manifest.json](sanitization-manifest.json)。重跑时产生的路径和测量时延会随环境变化。源码归档未重复提交，可由精确 Git 提交重新生成。
