# JobPulse 文档存档

这里保存仍有追溯价值、但不再指导当前实现的历史记录。

## 当前存档

| 目录 / 文件 | 内容 | 当前替代入口 |
|---|---|---|
| [STAGE-1-DECISIONS.md](STAGE-1-DECISIONS.md) | 阶段 1 的最终产品决策 | [产品文档中心](../README.md) |
| [M1-FOUNDATION-CHECKPOINT-2026-08-24.md](M1-FOUNDATION-CHECKPOINT-2026-08-24.md) | 国内校招公共数据底座、迁移安全与已知缺口的阶段收口 | [项目重构与后续修改计划](../product/PROJECT-RESTRUCTURE-PLAN.md) |
| [prd/](prd/) | PRD 历史版本、V2.1 重构审计 | [当前 PRD](../product/PRD.md) |

## 存档规则

1. 当前结论只维护在稳定入口中，存档文件不继续迭代。
2. 需要恢复历史内容时优先使用 Git；仅保留具有决策或审计价值的快照。
3. 代理过程文件、临时截图和可再生成产物不进入存档。
4. 存档文件中的旧路径可能只代表当时结构，当前入口以本页映射为准。

## 版本快照

2026-08-24 的项目收口同时使用三种载体：

- Git 标签 `archive/2026-08-24-m1-foundation`：不可变版本入口；
- GitHub 分支 `codex/credible-job-ingestion`：云端代码与文档存档；
- 本地 Git Bundle、源码 ZIP 和 SHA-256：断网时的独立恢复副本。

数据库、密钥、构建缓存和临时验收产物不进入上述源码存档。
