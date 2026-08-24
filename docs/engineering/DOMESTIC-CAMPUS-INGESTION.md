# 国内校招官方采集工程记录

| 属性 | 内容 |
|---|---|
| 当前状态 | Phase 1 已完成；Phase 2 数据底座已完成，快照差分服务待实现 |
| 日期 | 2026-08-18 |
| 产品规则 | [国内校招数据源策略](../product/DATA-SOURCE-STRATEGY.md) |
| 架构 | [国内校招采集架构](../architecture/domestic-campus-ingestion.md) |
| 实施计划 | [M1 实施计划](../product/M1-IMPLEMENTATION-PLAN.md) |

## 1. 本轮目标与结果

本轮把“首批公司全部校招岗位”从产品表述推进为可执行的第一阶段：

- 首批 10 家公司进入版本化来源注册表；
- 每个来源记录官方入口、官方域名、自动化决定、robots/条款状态、审核日期和证据；
- 生产来源只能使用 `complete` 模式，注册表拒绝 `keywords` 和 `max_jobs`；
- 招商银行公开校招接口适配器已完成，覆盖应届生与实习生、完整分页、详情和源端总数对账；
- 运行配置和来源注册表形成双重门禁，待审核来源不能因单独修改 `sources.yaml` 而被启用；
- M1 公共数据模型与正式 Alembic 环境已建立：公司层级、招聘活动、多届别、轻量岗位引用、来源快照和公司变化事件；
- 来源快照区分抓取、完整性和比较状态，首个有效快照只建基线，失败或不完整快照不能进入差分；
- 所有来源仍保持关闭，未把一次性技术核验误写成生产许可。

## 2. 首批公司来源状态

| 公司 | 已核验官方入口 | 自动化结论 | 当前动作 |
|---|---|---|---|
| 腾讯 | [腾讯校园招聘](https://careers.tencent.com/campusrecruit.html) | 禁止 | [服务协议](https://careers.tencent.com/m/zh-cn/termsservice.html)禁止程序抓取平台相关数据；只做人工发现或等待书面授权 |
| 字节跳动 | [字节校园招聘](https://jobs.bytedance.com/campus/) | 待审核 | robots 允许 `/campus`，但岗位接口要求官网客户端签名；不逆向、不绕过 |
| 阿里巴巴 | [阿里巴巴校园招聘](https://campus-talent.alibaba.com/) | 待审核 | 官方入口已登记，继续核验 robots、条款和公开接口 |
| 美团 | [美团招聘](https://zhaopin.meituan.com/web/campus) | 待审核 | robots 地址返回应用页面，按 fail-closed 保持停用 |
| 华为 | [华为校园招聘](https://career.huawei.com/cn/campus-recruitment) | 待审核 | robots 地址返回站点页面，按 fail-closed 保持停用 |
| 大疆 | [大疆校园招聘](https://careers.dji.com/zh-CN/campus) | 待审核 | robots 地址返回应用页面，按 fail-closed 保持停用 |
| 比亚迪 | [比亚迪校园招聘](https://job.byd.com/portal/mobile/school-home) | 待审核 | 官方入口已登记；robots 文件缺失 |
| 招商银行 | [招商银行校园招聘](https://career.cmbchina.com/campus/home) | 技术通过、条款待审核 | 公开接口适配器已实现；最终审核后才能启用调度 |
| 中国移动 | [中国移动招聘](https://job.10086.cn/) | 待审核 | 继续补齐集团及省公司来源；robots 文件缺失 |
| 美的集团 | [美的校园招聘](https://careers.midea.com/) | 待审核 | robots 检查超时，按 fail-closed 保持停用 |

状态的机器可读事实源是 [`config/company_sources.json`](../../config/company_sources.json)。本表只用于工程评审，不作为第二套配置。

## 3. 招商银行适配器

### 3.1 数据范围

现有技术验证适配器同时遍历：

- 应届生招聘：`campus_full_time`；
- 实习生招聘：`internship`。

不传岗位关键词、机构、城市或岗位类型过滤，不设置最终岗位数量上限。`page_size` 只控制单次请求大小，不改变完整遍历的结束条件。

### 3.2 完整性规则

每个招聘类型分别读取源端 `total`，然后持续翻页，直到抓取数量与总数完全一致。出现下列任一情况时整次采集失败：

- 分页结束但数量未达到源端总数；
- 翻页过程中源端总数变化；
- 同一招聘类型返回重复 `publishGID`；
- 列表行缺少 `publishGID`；
- 任一岗位详情缺失或无法解析；
- API 返回非成功业务码。

该适配器仍包含详情抓取能力，用于早期解析验证；它尚未接入 M1 公共写入链路。下一故事会改为“列表轻量引用 → 完整性验证 → 快照差分”，公共表不保存完整 JD。未知分类将按 M1 规则保存为 `unknown + evidence + confidence`，不会因分类失败丢弃岗位。

### 3.3 真实官网冒烟结果

2026-08-05 使用透明 `JobPulseSourceMonitor/1.0` 标识进行低请求量核验：

| 项目 | 结果 |
|---|---:|
| robots 检查 | 允许 |
| 应届生岗位源端总数 | 13 |
| 实习生岗位源端总数 | 22 |
| 列表对账 | 35/35 |
| 抽样详情解析 | 成功 |
| 抽样毕业届别 | `2027` |

这些数字是当时的官网快照，不是固定产品数据，也不代表适配器已获准进入后台调度。

## 4. 关键工程决定

1. 来源发现不等于采集授权。`company_sources.json` 是审核事实源，`sources.yaml` 是运行开关，两者必须同时允许。
2. 腾讯保持 `prohibited + paused`，不能以“官网公开”为由覆盖服务协议。
3. 字节岗位接口的客户端签名不做逆向；需要授权或允许的浏览器渲染方案才能继续。
4. 招商银行适配器先实现、后启用。代码可测试不代表法律与运营审核已经完成。
5. 生产完整采集禁止关键词与数量截断；历史海外演示筛选只能存在于明确的 `sample_mode`。

## 5. 测试与证据

- 来源注册表：公司/来源 ID 唯一、官方域名校验、完整范围、禁止静默筛选、启用状态门禁；
- 招商银行适配器：多招聘类型、多页、详情解析、总数对账、提前空页、详情失败和工厂注册；
- 数据模型：多届别 SQL 筛选、轻量岗位身份回退、公司/来源作用域外键、基线唯一、任务幂等、失败与不完整快照禁止比较、变化事件幂等；
- 数据迁移：空库到 M0 基线、保留既有 Company 升级 M1、模型一致性检查、降级回基线、再次升级；
- 真实官网：仅做 robots、两次列表请求和一个岗位详情抽样；未登录、未投递、未绕过访问控制。

2026-08-18 本地验证结果：全套 `171 passed`；M1 模型、迁移与启动安全定向 `35 passed`。当前真实旧库的副本已完成“严格结构指纹 → 备份 → stamp → 升级”验证，M0 各表数量保持不变；同时验证了迁移失败自动恢复、既有备份拒绝覆盖、线程与 Windows 跨进程迁移串行化。真实源文件未在开发过程中被自动修改。PostgreSQL 已覆盖双向离线 DDL 生成，但真实 PostgreSQL 执行仍是 R1 集成测试门禁，不能据此宣称生产验证完成；本机 Docker daemon 未运行，因此容器本轮完成 5 项静态启动契约验证，未宣称镜像实构建通过。

## 6. 下一阶段

Phase 2 接下来按以下顺序进行：

1. 完成招商银行条款与数据保留方式的最终审核，决定是否将其设为首个 `allowed + enabled` 来源；
2. 将招商银行列表结果写入 `ObservedPositionRef` 与 `SourceSnapshot`，实现首次基线、重复运行零新增、模拟新增/缺失/重开的幂等差分；
3. 统一以 UTC 保存发生时间，并生成 Asia/Shanghai 的 `reporting_date_cn`，验证北京时间午夜边界；
4. 接入轻量分类器，再提供全站今日指标、变化流和公司下钻 API；
5. 在仍可合规自动化的公司中选择第二种站点结构，实现下一适配器；
6. 为禁止或无法自动化的来源建设公告 URL 人工录入与复核队列；
7. 10 家技术样本完成后，才扩展到首批 100 家公司池。

## 7. 文件变更

- `config/company_sources.json`
- `config/sources.yaml`
- `config/sources.example.yaml`
- `src/crawler/source_registry.py`
- `src/crawler/adapters/cmb_campus.py`
- `src/crawler/adapters/factory.py`
- `src/crawler/service.py`
- `src/db/models.py`
- `src/db/schema_migrations.py`
- `alembic.ini`
- `alembic/versions/d8cf04cfe08c_existing_schema_baseline.py`
- `alembic/versions/8418f8d1585a_add_recruitment_radar_public_models.py`
- `tests/test_source_registry.py`
- `tests/test_cmb_campus_adapter.py`
- `tests/test_recruitment_radar_models.py`
- `tests/test_alembic_migrations.py`
- `tests/test_startup_migration_contracts.py`
- `start.ps1`
- `Dockerfile`
