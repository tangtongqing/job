# TASK-009 执行结果

## 摘要
完成了采集模块设计文档，覆盖适配器架构（3个适配器）、调度设计、清洗与字段提取、去重策略（三层）、有效性核验、合规控制，可直接指导阶段 4 实现。核心设计包括：BaseAdapter 抽象基类 + 3 个具体适配器、APScheduler 内嵌调度、归一化 + 唯一索引 + 跨源合并的三层去重、robots.txt + 速率限制的合规控制。

## 修改/新建的文件清单
- docs/architecture/crawler-module.md（新建）

## 关键设计决策

### 适配器数量
- **3 个适配器**：CompanyWebsiteAdapter（企业官网）、BossAdapter（BOSS直聘）、NowcoderAdapter（牛客网）
- 合规风险：企业官网（低）→ 牛客网（中）→ BOSS直聘（高）

### 去重策略（三层）
1. **第一层**：采集层归一化（location/公司名）
2. **第二层**：入库时唯一索引（source+company+title+location）
3. **第三层**：跨源合并（不同 source 的同一岗位，保留信息最全版本）

### 合规方案
- **robots.txt 尊重**：RobotsChecker 类，抓取前检查
- **速率限制**：RateLimiter 类，每源每分钟 ≤1 次
- **数据合规**：仅采集公开页面、不存储个人隐私、引用来源标注

## 与前置任务对齐自查

- [x] 全同步（httpx.Client / sync_playwright）？
- [x] 批量提交事务（每批 20 条）？
- [x] location 归一化（解决 TASK-007 v2 已知限制）？
- [x] robots.py + rate_limiter.py 合规模块？
- [x] 至少 3 个适配器 + 合规评估？
- [x] 写入 CrawlLog 表？

## 未解决的问题
- BOSS 直聘反爬较强，Demo 阶段可能需要降低采集频率
- 部分企业官网结构不统一，需要配置化的选择器

## 需要 Codex 判断的风险
- 合规边界：BOSS 直聘的 ToS 禁止爬虫，Demo 阶段是否可以例外
- 反爬应对：验证码检测后如何处理（暂停 vs 切换 UA）
- 去重准确性：跨源合并的公司名匹配可能不够精确