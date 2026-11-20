# 身体库修复：可复跑验证证据（2026-11-20）

本分支保存测试与测量证据，不是合并实现的发布分支，不单独申请 bounty。八个实现分别在上游 PR #1469–#1476。未改动生产数据库或真实用户资产。

| PR | 问题 | 被测精确提交 |
|---|---|---|
| #1469 | Motion group 成员分隔符造成 ID 碰撞 | cc68a82baace16e92ff6ce770330b65102a530a5 |
| #1470 | 透明线稿丢失 alpha，含 RGBa/La 扩展 | 433befa7b356eebecbc457ecd8f8a123ec1540cc |
| #1471 | 斜 OBB 的 SAT 面法线错误 | 39d379552f34026ef46ad0515831319b1494a5d3 |
| #1472 | 改写旧记录同时追加时 novelty 缓存过期 | a663512dd0fbc44a9fb08a55751951009586d172 |
| #1473 | odd-r 六角网格最近格点未比较相邻行 | cff189b3438623feaebdf1a874fafdd03080acb1 |
| #1474 | 技能检索负数 limit 被当作负切片 | fb6c9cabc939a6defcc44ef661b3048d47155d87 |
| #1475 | 零初速释放单摆公式与近分离点精度 | e0771a810b8846676f3545542b2e70d5e0011467 |
| #1476 | 顶层动画 motions 扩展被冻结几何验证器误拒 | 1ab5cc7f295ed5748b50c7ffde26cf2a34663204 |

基线均为 `d74848fb33dbff1d719959df19d1266a1ac60f44`。克隆仓库后需要先 fetch 上表提交（例如添加贡献者 fork remote 并 fetch 对应分支，或 fetch 上游 `refs/pull/<编号>/head`），不可把缺失的提交静默替换为本地主线。

[精确 PR head 的远程检查快照](ci-all-eight.json)记录八项 PR 的三档完整 gate 与标题检查；所有 PR 仍待维护者审核，不在这里视为已合并或已结算。

## 六项正确性、性能与内存

- [可移植用法](six-fixes/README.md)
- [正确性与时延报告](six-fixes/report.md)：修复版 15,455 项断言无失败；基线共 889 项失败。各版本的检查数会因基线输入拒绝而不同，按套件原样记录。
- [独立内存报告](six-fixes/memory_report.md)
- [原始时延数据](six-fixes/raw)、[原始内存数据](six-fixes/memory_raw)、[归档来源清单](six-fixes/snapshot-manifests)
- [透明格式扩展的完整回放](lineart-expanded/README.md)：25 项 guard、73 项 vision 测试、10 项具名变异；同时保留原始基线和上一 PR head 的不同预期失败清单，复跑时请选择对应 fixture。

固定随机种子为 20261120。每个版本从精确提交 `git archive` 到独立目录并核验导入路径与源码哈希；包含正常输入、边界、独立几何/像素参考和缓存状态序列。时延为 3 次预热 + 9 次保留样本，内存单独运行 3 次。主机共享 CPU，没有固定亲和性或功耗方案，读数仅描述本次样本。

性能退化同样保留：混合改写+追加的 novelty 缓存现在正确全量重建，时间与峰值分配增加；纯追加仍使用增量路径。tracemalloc 不能覆盖所有 Pillow/SQLite 原生缓冲；进程 working-set 快照不能视作单次操作的专属峰值。

支持域按数值条件表述：SAT 先逐行单位化 rot，归一化后的 `abs(det)<=1e-9` 帧会显式拒绝，不能把数学满秩等同于数值支持；随机八顶点 oracle 的抽样域为 `abs(det)>0.15`，不外推到近奇异帧。单摆的有限数和主物理域检查为有意收紧，不承诺旧非法输入仍被接受。

## 单摆与公开动画入口

- [80 位角度、周期、RK4 与性能报告](pendulum/report.md)
- [可移植精度脚本](pendulum/pendulum_release_accuracy.py)：在 Python 3.12+ 的独立环境中装 `mpmath==1.4.1`，运行 `python <脚本> --repo <PR1475工作树> --output <输出目录>`。
- [身体侧具名变异回放](pendulum-guards/summary.json)、[桥侧具名变异回放](bridge-guards/summary.json)：身体 6/6 与桥侧 8/8 通过；原基线分别 6 失败、7 失败/1 通过；十一项指定变异均触发指定断言，零 errors/skips。
- [独立标准库复核](pendulum-review/review_results.txt)：随机 RK4、周期/对称性质与公有 cn 位级兼容。
- [公开四元数入口的 80 位参考](bridge-oracle/report.md)：2,840 次真实 `eval_at(..., motions=...)` 调用、31,240 项断言无失败。输入时间转换误差单列。

930 个短中期点、40 个超长时点共 6,550 项角度/相位检查通过；不把最多约 100 周期的样本精度当作任意长时间的浮点误差上界。69 个周期样本与高精度椭圆积分比较通过。接近 π 时双精度 RK4 自身可能停滞，使用 80 位参考而非把 RK4 当作极限振幅的唯一真值。

## 顶层动画 motions

[第八项的完整验证与基准](top-level-motions/README.md)覆盖所有公开动画入口、显式参数优先级、输入不变和未知键仍拒绝：30 项新守卫通过，同一守卫在原基线 23 失败/7 通过，六项具名变异全部杀死。[成功路径时延与分配原始数据](top-level-motions/benchmark/summary.json)对照参数调用与修复后的顶层扩展，不把基线的快速异常当作成功工作进行时延比较。相关套件 194 通过、4 跳过，另有一项脚本测试成功。

[两项桥侧修复的组合交互报告](crossfix-oracle/report.md)冻结并比较原基线、单摆单独修复、顶层 motions 单独修复、最终组合四份源。组合版本 784 组输入、10,976 项断言通过；包括 120°、179.99999°、nextafterπ、正负时间和三轴。顶层字段与显式参数结果逐项一致。数学单独修复无法接受顶层字段，顶层单独修复仍有波形错误，因而这项检查直接验证了两项修复共同生效。

## 完整组合门禁

[首轮六项组合的原始记录](integration-six/summary.json)覆盖 YAML 的 102 个脚本（含固定脑核真实 23/23）及全部 pytest：5,590 通过、46 跳过、98 个 subtest 通过、1 失败。唯一失败是 `test_issue498_atomic_write_perm_symlink_guard.py` 在可创建 symlink 的 Windows 上仍断言 POSIX；[未改动上游的同一失败](integration-six/baseline_symlink.log)原样保留。不以该结果声称整个 Windows suite 全绿。

[最终八项 Windows 组合的完整记录](integration-final-windows/summary.json)使用独立 Python 3.12 / NumPy 2.5.5 / Pillow 12.3.0 / SciPy 1.18.1 环境及子进程作用域 OpenSSL。102/102 脚本成功；完整 pytest 为 **5,673 passed、1 failed、28 skipped、98 subtests passed**，耗时 1,383.07 秒。唯一失败仍是同环境、未修改主线也复现的 symlink P1；新增的编码缺口已经修复，组合没有其他失败。串行计时守卫 4 passed，strict manifest 64/64，time lint 23 既有/0 新增/0 过期。主驱动忠实返回 exit 1。

[同一八项组合的完整 Linux 矩阵](integration-final-linux/report.md)在现有 gate 工作流上仅手工触发一次，未修改工作流配置。运行 `44751075692` 的实际 head 与三份 checkout 日志均为 `231aa533...`；Python 3.12.16 / NumPy 2.5.5、3.12.16 / NumPy 2.3.5 下界、3.13.18 / NumPy 2.5.5，三腿各自 **SUCCESS**，每腿 **102/102 脚本、脑核真实 23/23、pytest 5,662 passed / 40 skipped / 98 subtests passed / 0 failed / 0 errors**。Pillow 均为 12.3.0。pytest 耗时分别 550.36、719.79、633.06 秒；下界和 3.13 的结果直接从各腿实读，不由 advisory 工作流总体状态推断。[环境与 checkout/脑核证明](integration-final-linux/job-details.json)、原始 job logs 与 API 快照均保留。

[Skip 与补测明细](integration-final-windows/skip_coverage_notes.json)保持上述主计数：28 个 skip 中，真实历史提交 `124ea433fe9a2ad2fd66a7360df85f6d61bab793` 的导出与逐文件核验使 4 个冻结基线用例得到实测（原物理预测文件 43 passed / 0 skip）；能力探测后调用原未改动的符号链接测试体，3/3 passed；串行计时覆盖并行时跳过的 1 条。补测不重复加入主 passed 数。Windows 本平台仍未执行的 20 条为 17 条缺真实模型/冻结像素资产、3 条 Windows 无法表达的 POSIX 权限语义。后三条在每个 Linux job 的原日志均明确 PASSED，共 9 条成功记录；前 17 条在每个 Linux job 也明确 SKIPPED。因此本轮跨平台共同未执行范围为这 17 个原始资产依赖用例，[逐测试 ID、原日志行号与日志 SHA 交叉核验](audit/commit-ce40e46-cross-platform-scope.json)保留。脑核固定 SHA 与全部 1,618 个 Git 可见源码文件前后完全未变。

[可移植组合门禁驱动](portable_final_gate.py)接受 `--repo <组合工作树> --output <仓外空目录> --brain-root <固定脑核> --workers 4`，从 YAML 读取全部脚本与固定脑核 SHA，校验后运行脚本、完整 pytest、串行计时量具、manifest 与 time lint。使用同一基线取入各 PR 的完整提交范围，包含 alpha、OBB 和单摆的前置/后续提交；不能只 cherry-pick 表中的最终 head。OBB 与单摆共同改变 physics 行数，lint baseline 行号应在两个改动的和上同步。保留所有错误，不使用 deselect 隐藏失败。

八项组合源已固定为 `231aa5334c0c0f2f01eccf6c547ebd97a478a8d0`，tree 为 `94c97c2e4e65d6e454416b126388eb11f02ee4f9`，公开在同一 fork 的 `validation/body-eight-integration-20261120` 分支。也可在干净基线先 `git apply --check`，再应用 [完整组合 patch](integration-eight-source/combined-fixes.patch)，其 [校验值与来源](integration-eight-source/patch_metadata.json)、[全部 33 个改动文件的 LF 源码哈希](integration-eight-source/sources_sha256.json)用于验证所得源码。patch 保留原字节，已核查无本机工作区/家目录路径；驱动支持 apply 后未提交的工作树，并在测试前后核验全部 Git 可见源码未变化。

[额外手工物理门隔离报告](manual-physics/report.md)将未改动基线与 PR #1475 分别完整运行：两版均 10 PASS / 1 FAIL，仅 P1，真实退出码均为 2。P1 的断言代码块和 `projectile_truth` 函数逐一同源，均把绝对顶点高度与相对上升高度混比，差 1.2 m。单摆 P4 的 RK4 样本最大误差由旧 5° 域的 `3.9983e-05 rad` 变为修复后六种振幅样本的 `1.1957e-13 rad`。本次没有修改无关的 P1，不声称整个额外手工门全绿。

## 数据完整性

公开副本将本地工作区/家目录路径前缀替换为占位符，文本换行统一为 LF；测量值、输入值、源码哈希、种子与结论保留。每个公开文件及本机原始文件的校验值见 [sanitization-manifest.json](sanitization-manifest.json)。重跑时产生的路径和测量时延会随环境变化。源码归档未重复提交，可由精确 Git 提交重新生成。

查重结果属于公开来源的元数据，使用最小摘录：保留查询、issue/PR 编号、标题、链接、状态和计数，去除无关第三方完整正文及其机器路径。[摘录来源与校验说明](top-level-motions/duplicate-search-provenance.json)单独记录此项处理；这不涉及测量样本的删改。

[发布回读审计](publication-updates/publication-results.json)记录原七项 PR/intake 共 14 份正文的备份、提交与逐次回读；既有 intake 头保留，旧性能范围和 alpha 双基线命令已更新，未重复新建 issues。

[最终生产差异只读终审](code-review/README.md)核对 core/缓存/ID、nn、vision、SAT/math、bridge 规范及 replay 路径边界，未发现本批新增实质回归或阻断项；支持域、数值退化阈值与有意收紧单列，不以测试样本代替全域证明。

完整实测证据提交 `ce40e464...` 的[最终独立数据审计](audit/commit-ce40e46-final.txt)为 PASS：656 项 artifact 的 Git blob 哈希/字节数全部一致，69 份 XML 结构有效，JSON 中 30,940 个整数和 220,036 个浮点值与本机原始源数据逐项一致；路径脱敏和 LF 规范化之外不改测量结果。此封存提交仅补入该审计、跨平台 skip 范围澄清及最终公开正文回读，不改变生产代码或实测样本。

[最终 16 份公开正文发布审计](publication-final-integration/audit-summary.json)确认全部 8 个 PR 与 8 个 intake 的新 integration 段逐份写入/回读一致；旧 expanded 段和 8 个 intake 头保留，PR 对应关系正确。[最后检查快照](publication-final-integration/final-checks-summary.json)记录八个源码 head 未变、全部 OPEN/CLEAN、三档 gate 与正文更新后的最新标题检查成功。没有自领、定级结算、合并或工作流配置变更。

对上一完整证据提交 `7bf90b7d...` 的 [独立审计](audit/commit-7bf90b7-r03.txt)逐 Git blob 核验了 313 项 artifact 的哈希/字节数、39 份 XML 结构语义，以及全部 JSON 的 21,689 个整数和 156,376 个浮点值（逐 hex）与本机原始数据一致；本提交在该快照基础上追加已完成的 alpha 回放、组合 oracle 和组合源。
