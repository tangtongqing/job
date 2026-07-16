# Credible Job Ingestion Research

## Understanding summary

- JobPulse 当前能演示投递管理，但采集层仍是骨架，岗位字段不完整。
- 本轮目标是“可完整演示”：有足够数量、完整 JD、官方来源页和可用投递链接。
- 真实采集只使用公开企业招聘 API 或官网结构化数据，不登录、不处理验证码、不绕过反爬。
- 确定性演示数据用于断网演示，必须显式标注为演示快照，不伪装成实时采集。
- 长期个人使用所需的账号、云同步、邮件/移动推送仍保留在后续路线图。
- 本地 Demo 预期规模为数十到数百个岗位，SQLite 与同步 FastAPI 足够。

## Approach options

1. **公开 ATS API + 完整演示快照（采用）**
   - 优点：字段完整、投递链接真实、无需登录，断网也可演示。
   - 代价：需要为 ATS 响应编写规范化和字段提取。
2. **逐家企业官网 HTML 适配**
   - 优点：国内公司覆盖更好。
   - 代价：结构不统一、大量页面需动态渲染，维护成本高。
3. **只扩充本地种子数据**
   - 优点：最稳定、开发快。
   - 代价：不能证明采集链路真正可用。

## Recommended design

- 新增通用 `GreenhouseAdapter`，调用官方 Job Board API，从同一套代码配置 Figma、Webflow、Intercom 和 Stripe 四个独立来源。
- 只保留产品、设计、研究、数据和增长相关岗位，单源限制数量，保证本地演示可控。
- 完整 JD 由 HTML 转为纯文本；要求、薪资、学历、经验、发布时间和截止时间尽可能结构化。
- `apply_url` 和 `source_url` 保留 ATS 返回的官方岗位页。
- 采集源按配置 key 运行，允许多个企业共用一个 adapter；配置解析支持标准列表。
- 演示快照保持确定性，旧的伪“采集成功”日志改为明确的演示初始化记录。

## Non-functional assumptions

- 单源单次最多保留 15 个相关岗位，超时 20 秒，最多重试 2 次。
- 公开 API 失败时记录失败日志，不删除已有岗位，不破坏 Demo。
- 不存储求职者数据，不代替用户提交申请，只跳转官方投递页。
- 字段完整度和采集来源状态需在采集管理页可见。

## Decision log

| Decision | Alternatives | Reason |
|---|---|---|
| 公开 Greenhouse API 作为第一个真实适配器 | 平台爬虫、只做种子数据 | 公开、字段完整、投递链接真实、合规风险低 |
| 四个 SaaS 公司招聘板共用适配器 | 每家单独写代码 | 能展示多源，不引入重复维护 |
| 保留演示快照 | 完全依赖网络 | 确保作品集和本地演示始终可用 |
| 登录平台继续禁用 | 处理验证码或反爬 | 不符合当前合规边界 |

## References

- Greenhouse Job Board API: https://developers.greenhouse.io/job-board.html
- Greenhouse public board endpoint: `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`
