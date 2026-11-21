# 身体库总协调任务表

最近读取：2026-11-21T16:12:24+08:00

放眼全局，不要太注重局部优化，最好弄一个总智能体管理子智能体群

总协调负责排序、分派、组合验收和对外交付；子智能体自报须与当前源码和原始证据核对。

| 子智能体 | 职责 | 当前任务 |
| --- | --- | --- |
| ${HOST_ROOT}/integration_surface | 整合与依赖核对 | 1466, 1439, 1432, 1428 |
| ${HOST_ROOT}/open_scope | 独立核对 CI、证据与既有申报 | 1479, 1477, 1471, 1437, 1460, 1461, 1463 |
| ${HOST_ROOT}/pipeline_audit | 组合验收与安装门禁 | five-integration, extended-gate |

| PR | 内容 | 当前状态 | 当前提交 | 证据 |
| --- | --- | --- | --- | --- |
| [#1485](https://github.com/FuRongJun-1999/lingshu/pull/1485) | 统一模型替换与推演生命周期 | CI 已过，待维护者合并 | 72ee3e4c9a | [本地证据](../intake-receipt.json) |
| [#1484](https://github.com/FuRongJun-1999/lingshu/pull/1484) | 运动组有限坐标 | 已合并 | 4e919f76b3 | [本地证据](../../body-next-20261121/DELIVERY_STATUS.md) |
| [#1479](https://github.com/FuRongJun-1999/lingshu/pull/1479) | 自由飞行速度 | CI 已过，待维护者合并 | b3f2a67e71 | [本地证据](../integrate-freeflight/regressions.xml) |
| [#1477](https://github.com/FuRongJun-1999/lingshu/pull/1477) | 圆周拟合与残差 | CI 已过，待维护者合并 | b32b064eca | [本地证据](../integrate-circular/integration-summary.json) |
| [#1471](https://github.com/FuRongJun-1999/lingshu/pull/1471) | 斜盒碰撞 | CI 已过，待维护者合并 | cf69e40e78 | [本地证据](../integrate-obb/integration-proof.json) |
| [#1437](https://github.com/FuRongJun-1999/lingshu/pull/1437) | 线稿参数校验与透明通道 | CI 已过，待维护者合并 | f46ff9f29f | [本地证据](../integrate-lineart/regressions.xml) |
| [#1460](https://github.com/FuRongJun-1999/lingshu/pull/1460) | 音频 | CI 已过，待维护者合并 | 4a67a751ef | [本地证据](../integrate-media-audio/integration-summary.json) |
| [#1461](https://github.com/FuRongJun-1999/lingshu/pull/1461) | 视频 | CI 已过，待维护者合并 | 10853336a5 | [本地证据](../integrate-media-video/integration-summary.json) |
| [#1463](https://github.com/FuRongJun-1999/lingshu/pull/1463) | 掩码几何 | CI 已过，待维护者合并 | 596b5f0de6 | [本地证据](../integrate-media-mask/integration-summary.json) |
| [#1466](https://github.com/FuRongJun-1999/lingshu/pull/1466) | 深度反投影 | CI 已过，待维护者合并 | fb374bbad1 | [本地证据](../integrate-depth) |
| [#1439](https://github.com/FuRongJun-1999/lingshu/pull/1439) | 感知与知识桥分区一致性 | CI 已过，待维护者合并 | e687b4dbfe | [本地证据](../integrate-knowledge) |
| [#1432](https://github.com/FuRongJun-1999/lingshu/pull/1432) | 响应证据 | CI 已过，待维护者合并 | e77a67fcc5 | [本地证据](../integrate-response) |
| [#1428](https://github.com/FuRongJun-1999/lingshu/pull/1428) | 去重索引与当前记忆语义 | CI 已过，待维护者合并 | fedf81a6e2 | [本地证据](../integrate-dedup) |
| [#1486](https://github.com/FuRongJun-1999/lingshu/pull/1486) | 扩展历史、稀疏与安装验收 | CI 已过，待维护者合并 | 8c7abf1b2c | [本地证据](../extended-gate/intake-receipt.json) |
| [#1433](https://github.com/FuRongJun-1999/lingshu/pull/1433) | 实际像素识别到世界与记忆 | CI 已过，待维护者合并 | a721c3363b | [本地证据](../perception-dependencies/DECISION.md) |
| [#1431](https://github.com/FuRongJun-1999/lingshu/pull/1431) | 可控噪声误差传播基准 | CI 已过，待维护者合并 | e172c94f0b | [本地证据](../perception-dependencies/noise-curve-current-deps.json) |

## 组合与安装验收

- five-integration：502本机通过，三档远端与原始日志核对通过；[证据](../five-integration/combined-summary.json)。
- extended-gate：Windows 本机真实验收通过；PR1486远端CI运行中；[证据](../extended-gate)。
- all-integration：1415通过/0跳过；真实像素依赖接入另行验证；[证据](../all-integration/combined-summary.json)。
- final-integration：三档Linux各6415通过/44跳过；Windows6434通过/1既有失败/24跳过；安装归档与真实像素链通过；[证据](../final-integration)。

## 协作规则

- 按公共调用链、依赖和组合效果排序，再分派单项工作
- 隔离工作树按任务分配，不改历史工作树
- 子智能体提交精确版本、原始证据、失败、跳过和边界，总协调核对当前状态
- 推送、PR 与 bounty 更新由总协调执行；独立修复只对应一个 intake
- 不替维护者合并或结算；历史已结算项保持状态
- 读取已有 live 进程和 CI 句柄，不因观察超时重启

仅读取刷新命令：py -3 -X utf8 refresh_board.py。

尚未证明整个身体库完成验收。CI、维护者审核、合并和结算分别记录。
