<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img src="assets/banner-light.svg" alt="✦ Astra Harness — 纠偏模式、证据边界、研究核心" width="100%">
</picture>

# Astra Harness · 公共研究核心

中文 · [English](README.en.md)

✦EricMingle69 · MIT · 公共分发 **0.1.0**

Astra 是个人 Agent 体系，Harness 是其工程支撑，**HCD（Human Correction Distance，人类纠偏距离）**是纠偏评估模块。本仓库提供可运行且范围明确的研究核心：显式任务事件、带证据边界的接受状态、跨任务纠偏模式及其复发。源码、纯合成示例、架构、演化与具体研究方向均可复用。

本仓库不包含实际聊天、日志、记忆、反馈、上下文、任务记录、生产回执、训练数据或个人配置；即使匿名或脱敏，这些记录也不进入公开发布。示例中的 TaskA、TaskB 从零合成，不代表真实人物或任务。

## 运行合成实验

支持 Linux/macOS，要求 Python 3.11 或以上及 POSIX 文件锁；运行源码仅依赖标准库。导入模块不会发现宿主、启动观察、训练、调度或网络连接。

在源码目录执行：

```sh
PYTHONPATH=src python -B -m unittest discover -s tests -v
python -B scripts/publication_check.py check --root .
DEMO_ROOT="$(mktemp -d)"
PYTHONPATH=src python -B -m astra_harness demo --data-root "$DEMO_ROOT"
```

演示要求空白临时目录，只在其中生成**纯合成**账本：登记 TaskA/TaskB 的首次方向与纠偏，用确定性的注入 runner 找到共同的输出核验缺失模式，标记一次合成干预，再观察该模式复发。输出保留 `benefit: unknown`、`coverage: unknown`，不用模型或生产信息。

作为库使用时，调用 `hcd.record(event, data_root)` 和 `hcd.report(data_root)`，由调用方显式指定研究数据根、会话和项目身份。没有宿主会话环境变量兜底或自动安装。示例 profile 默认关闭全部集成，不能启用公共包没有提供的私有能力。

## 公开能力与边界

| 能力 | 公共 0.1.0 | 边界 |
|---|---|---|
| HCD 事件协议与 SQLite 账本 | 已实现 | 显式数据根、输入限额、幂等、owner/epoch 检查 |
| 接受状态与序数距离 | 已实现 | 方案/成品分开；需证据；后续纠偏和过期使旧状态失效 |
| 模式聚类与复发 | 已实现 | 调用方注入结构化 runner；无内置模型客户端或调度器 |
| Schema 3 报告 | 已实现 | 模式复发为主，D 为次要；任务覆盖与用户真值保持未知 |
| 学生标签一致率 | 协议已实现 | 可选外部标签；与模型聚类一致不等于用户确认的准确率 |
| 合成演示与回归测试 | 已提供 | 只用合成输入，无网络或推理 |
| 原生宿主采集、桌面捕获、长期知识服务 | 未包含 | 不分发私有集成适配器和配置 |
| 本地模型训练、自动维护、生产事务部署 | 未包含 | 本包不能安装或运行这些集成 |
| 云端维护与 MCP 服务 | 仅说明合同谱系 | 不含云端地址、凭据、认证实现或服务器 |

方案接受与成品接受分别记录；后续纠偏、自主修正、重开、放弃、目标变化或证据过期会使相关接受与评分失效。弱接受仅是观察代理信号，不能当成用户明确验收。

合成测试验证确定的工程行为，不证明降低真实纠偏、完整观察、模型优越性或因果收益。学生标签与模型聚类的一致率也不是用户真值。

## 架构、演化与参与

- [架构与证据边界](docs/architecture.md)
- [版本演化与编号含义](docs/evolution.md)
- [具体研究路线](docs/research-roadmap.md)
- [更新记录](CHANGELOG.md)
- [贡献与发布流程](CONTRIBUTING.md)
- [公开发布与持续维护](docs/PUBLICATION.md)
- [个人作者说明](PERSONAL-NOTICE.md)

[Engram](https://github.com/Ming-Sir-69/engram) 是独立的长期知识项目。Astra 的 HCD 模块研究纠偏证据和模式复发；本公共核心不内置 Engram 服务或私有连接适配器。两者职责与公开版本历史分别维护。

**0.1.0 是本研究核心的首个公共分发版本。**内部源码包 1.0.0 和 MCP 接口 1.0.3 属于实现谱系，不是本公共核心过去的正式发布。后续版本依公共实现与研究边界的真实变化递增。
