# JobPulse 线上部署与验收存档

**日期**：2026-07-22

**状态**：已公开部署，可用于面试展示与产品体验。

**源码基线**：`9046cc0 feat: prepare JobPulse for hosted demo`

## 访问入口

| 入口 | 地址 | 访问范围 |
|---|---|---|
| SaaS 官网 | <https://jobpulse-product-demo.tongqtang.chatgpt.site> | 公开，无需登录 |
| 产品后台 | <https://jobpulse-product-demo.tongqtang.chatgpt.site/dashboard> | 公开，共享演示数据 |
| 作品集案例 | <https://jobpulse-product-demo.tongqtang.chatgpt.site/case-study> | 公开，无需登录 |
| API 健康检查 | <https://jobpulse-api-production.up.railway.app/health> | 公开，只读健康状态 |

## 部署拓扑

```text
访客浏览器
  ├─ Codex Sites：营销页、产品后台、案例页、视频资源
  └─ Railway：FastAPI → SQLite 持久化卷 /app/data
```

- 前端：Codex Sites，vinext 构建为 Cloudflare Worker 兼容产物。
- 后端：Railway `jobpulse-demo / jobpulse-api`，Docker 部署。
- 数据：SQLite 挂载持久化卷，服务重启不丢失。
- CORS：只允许正式 Sites 域名和本地 3000/3100 调试源。

## 线上数据与功能边界

- 标准场景为 24 条确定性岗位快照、5 条投递、2 条收藏、2 条待投递和 3 条订阅。
- 岗位包含完整 JD、来源链接和官方投递链接。
- 所有访客共享同一份演示数据；访客操作可能互相影响。
- 侧栏提供二次确认的演示数据重置，验收结束后已恢复标准场景。
- 匿名在线采集触发已关闭；公开 ATS 采集保留在本地和未来受控版本中。

## 付费 API 与邮件功能

线上 Railway 环境没有以下配置：

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- SMTP、SendGrid、Resend、Mailgun、Postmark 或 AWS SES 凭据

“邮件解析”不是邮件收发服务，而是解析用户粘贴的招聘邮件或消息文本。代码保留可选 LLM 适配层，但未配置密钥时不会调用外部模型，会自动使用本地正则解析。线上实测返回 `degraded: true`、置信度 `0.5`，证明当前走免费降级路径。邮件原文不写日志，缓存只使用文本哈希。

## 成本状态

- Railway 当前为免费试用账户，没有活动付费订阅。
- 试用额度用尽时服务会停止，不会自动升级到付费计划。
- Railway 试用账户不支持自定义用量上限；后续若升级付费计划，应第一时间设置费用上限。
- Codex Sites 没有在本次部署过程中要求单独购买托管套餐。

以上是 2026-07-22 的实际账户与环境状态；平台价格和免费政策变化时需重新核对。

## 线上验收结果

| 检查项 | 结果 |
|---|---|
| Sites 首页公开访问 | HTTP 200，无登录重定向 |
| Railway 健康检查 | `status=ok` |
| 岗位数据 | 24 条 |
| JD / 投递链接 / 来源链接 | 抽检均存在 |
| 收藏流程 | 2 → 3 → 2，通过 |
| 创建投递 | 5 → 6，通过 |
| 采集保护 | `POST /crawler/trigger` 返回 403 |
| 正式域名 CORS | OPTIONS 200，返回精确允许源 |
| Demo 重置 | 恢复 24 岗位、5 投递 |
| 后端自动化测试 | 109 passed |
| 前端质量 | ESLint 通过，Next.js 与 Sites 构建通过 |

## 运维提示

1. 面试前打开首页与后台，确认 Railway 未因免费额度结束而暂停。
2. 演示前在侧栏执行“重置演示数据”，恢复标准故事线。
3. 不要向 Railway 添加 LLM 或邮件密钥，除非明确接受费用与隐私影响。
4. 若转为长期个人使用，优先补账号隔离、数据库迁移、受控采集调度和费用上限。

## 已知限制

- 公开版本没有登录和用户数据隔离，只适合作品集演示。
- Railway 免费试用不承诺长期在线，额度或试用期结束后可能暂停。
- 真实岗位自动刷新、失效下架和通知仍属于未来计划。
- 邮件解析的免费正则路径准确率有限，但不会产生模型费用。
