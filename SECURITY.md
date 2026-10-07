# Security reports with synthetic reproductions

Report a concrete vulnerability or boundary failure using a freshly invented synthetic reproduction and expected behavior. Use TaskA/TaskB and synthetic request/session labels. Describe the affected public version and source function, then show the smallest safe reproduction.

Never attach actual conversations, prompts, logs, databases, memory/task/context/feedback/event records, screenshots, credentials, host addresses, operational receipts, model artifacts, or real identifiers. This prohibition still applies after anonymization or redaction. Do not copy a real row into a test fixture. If an issue cannot be reproduced safely, describe the suspected mechanism without the underlying data.

The public core is a local research library. It has no authentication server, cloud endpoint, arbitrary execution gateway, native collector, or live deployment interface. Its path checks are not an OS sandbox. Use a dedicated scratch directory with suitable permissions when running experiments.

Maintainers reproduce reported failures synthetically, add a regression, and update the documented boundary and public version when needed. Scanner success does not establish provenance or rule out every possible secret encoding. No production input is needed for this process.

中文：安全问题只提交从零合成的最小复现、公共版本、受影响函数和预期行为。实际日志、记录、私密配置、凭据、主机地址和真实 ID，即使脱敏，也禁止提交。无法安全复现时只说明疑点机制。公共核心没有认证服务、云端接口、任意执行、原生采集或生产部署能力；路径检查不等于系统沙箱。
