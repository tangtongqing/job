# 采集模块设计

> TASK-009 产出。基于 TASK-006/007/008 的架构决策，详细设计采集模块的适配器、调度、清洗、去重、核验、合规控制。
>
> **M1 修订（2026-08-05）**：本文保留 M0 实现细节；M1 数据主干已经切换为国内校招官方来源，招聘活动/公告/岗位分层、来源注册表、模板族适配器和覆盖率以[国内校招官方信息采集架构](domestic-campus-ingestion.md)为准。本文中曾提出的随机 UA、代理规避或“平台低频少量抓取”不再有效。
>
> ---
> **版本**：v2（主智能体校准版）
> **v2 修订说明**：v1 结构完整（3 适配器 + 三层去重 + 合规模块），但存在 8 处硬伤，v2 集中修订：
> 1. **【严重·合规】robots.txt fail-open 错误**：v1 "无法读取 robots.txt 时默认允许"，这是合规硬伤（会被判定为故意绕过）。v2 改为 **fail-closed**（默认禁止 + 告警 + 人工评估）
> 2. **【严重】去重函数索引自相矛盾**：v1 写了 `CREATE UNIQUE INDEX ... normalize_company(company)`，但注释自己说 SQLite 不支持函数索引。v2 删除该 SQL，明确归一化在应用层完成后入库，唯一索引用普通字段（对齐 TASK-007 v2）
> 3. **【严重】status 又用中文 `已关闭`**：违反 TASK-007 v2 的 CHECK 约束（只允许 `displaying`/`closed`），UPDATE 会失败。v2 改为 `'closed'`
> 4. **【中】跨源 contains 误判**：v1 用 `LIKE '%xx%'` 会导致"字节"误匹配"字节其他公司"。v2 改为"归一化后完全相等"，与同源去重一致
> 5. **【中】BaseAdapter 强制创建 httpx.Client**：BOSS 用 Playwright 不需要 Client。v2 改为懒加载 property
> 6. **【中】批量提交未体现**：v1 伪代码是单条处理，与 TASK-006 v2 §4.3 批量提交（每批 20 条）不一致。v2 补充
> 7. **【小】Playwright 生命周期管理未说明**：补充 browser 启动/关闭/异常清理
> 8. **【小】指数退避重试缺失**：补充 retry_with_backoff 伪代码

---

## 一、采集模块总览

### 1.1 一句话定位

> 采集模块从已登记的国内企业官方招聘入口和可信公共发现渠道获取校招活动、公告与岗位，核验去重后入库，为订阅、投递管理和覆盖看板提供数据基础。

### 1.2 模块边界

| 做什么 | 不做什么 |
|--------|---------|
| 抓取公开招聘信息 | 不绕过反爬/付费墙 |
| 清洗、去重、入库 | 不处理投递状态 |
| 定时调度采集任务 | 不处理用户交互 |
| 核验岗位有效性 | 不做实时推送 |
| 记录采集日志 | 不做数据分析 |

### 1.3 与其他模块的关系

```
                    ┌─────────────┐
                    │   api/      │
                    │ (触发采集)  │
                    └──────┬──────┘
                           │
                           ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  crawler/   │────▶│    db/      │────▶│   core/     │
│ (采集模块)  │     │ (数据持久化)│     │ (业务逻辑)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ 国内官方源  │
│ (官网/ATS)  │
└─────────────┘
```

---

## 二、适配器架构（核心）

### 2.1 适配器基类设计

```python
# crawler/adapters/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from httpx import Client

class BaseAdapter(ABC):
    """采集适配器基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.source_name = config.get('source_name', 'unknown')
        # v2 改为懒加载：httpx.Client 和 Playwright 按需创建
        # （BOSS 用 Playwright 不需要 httpx.Client，强制创建浪费资源）
        self._client = None
    
    @property
    def client(self) -> Client:
        """httpx.Client 懒加载（仅 httpx 类适配器使用）"""
        if self._client is None:
            self._client = Client(
                timeout=self.config.get('timeout', 30),
                headers={'User-Agent': self.config.get('user_agent', 'JobPulseSourceMonitor/1.0')}
            )
        return self._client
    
    @abstractmethod
    def fetch(self, page: int = 1) -> List[Dict]:
        """
        抓取岗位列表
        返回：原始数据列表
        """
        pass
    
    @abstractmethod
    def parse(self, raw_data: Dict) -> Optional[Dict]:
        """
        解析单条岗位数据
        返回：结构化数据或 None（解析失败）
        """
        pass
    
    @abstractmethod
    def should_crawl(self) -> bool:
        """
        判断是否应该采集（合规检查）
        返回：True 表示可以采集
        """
        pass
    
    def fetch_detail(self, url: str) -> Optional[str]:
        """
        抓取详情页（可选）
        返回：HTML 内容或 None
        """
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to fetch detail {url}: {e}")
            return None
    
    def close(self):
        """释放资源（httpx.Client / Playwright browser）"""
        if self._client is not None:
            self._client.close()
            self._client = None
        # 子类如用 Playwright，override 此方法关闭 browser
    
```

### 2.2 各源适配器

#### CompanyWebsiteAdapter（企业官网）

**合规风险**：逐源评估，不能因为是企业官网就自动判定为低风险

| 项目 | 说明 |
|------|------|
| 目标 URL | 来源注册表中审核通过的国内企业招聘官网、校招专题或公开 ATS |
| 抓取方式 | httpx.Client（静态页面）或 Playwright（动态渲染） |
| 解析方式 | 优先模板族/结构化接口；少量公司差异配置 |
| 访问控制 | 声明身份的固定 UA + 逐域名限速 + fail closed |
| 合规评估 | 记录 robots、条款、检查日期和证据；无法确认允许时不采集 |

**配置示例**：

```yaml
# config/sources.yaml
company_sources:
  - company_id: "example-company"
    source_type: "official_campus_site"
    canonical_url: "https://example.com/campus"
    ats_family: "custom"
    compliance_status: "approved"
    enabled: false  # 完成来源审核和契约测试后逐源开启
```

---

#### BossAdapter（BOSS 直聘）

**决策**：未经 BOSS 书面许可、官方 API 或数据合作，不采集。

当前代码只保留明确返回空结果的合规骨架，配置永久默认关闭。低频、随机 UA、代理池、Playwright 拟人或验证码检测都不能把禁止的抓取变成合规。未来只有取得授权后才能另写授权适配器，并按授权范围、频率和保留期执行。

---

#### NowcoderAdapter（牛客网）

**合规风险**：中 ⚠️

| 项目 | 说明 |
|------|------|
| 目标 URL | https://www.nowcoder.com/jobs/school/jobs |
| 抓取方式 | 当前不抓取，仅保留安全空实现 |
| 字段选择器 | 不适用 |
| 访问控制 | 不登录、不绕过、不模拟用户 |
| 合规评估 | 完成条款与授权评估前保持禁用 |

---

### 2.3 适配器注册与配置驱动

**工厂模式**：

```python
# crawler/adapters/factory.py

from typing import Dict, Optional
from .base import BaseAdapter
from .company import CompanyWebsiteAdapter
from .boss import BossAdapter
from .nowcoder import NowcoderAdapter

ADAPTERS = {
    'company': CompanyWebsiteAdapter,
    'boss': BossAdapter,
    'nowcoder': NowcoderAdapter,
}

def get_adapter(source: str, config: Dict) -> Optional[BaseAdapter]:
    """获取适配器实例"""
    adapter_class = ADAPTERS.get(source)
    if not adapter_class:
        logger.error(f"Unknown source: {source}")
        return None
    return adapter_class(config)
```

**配置文件结构**：

```yaml
# config/sources.yaml

global:
  crawl_interval_minutes: 60
  max_concurrent: 3
  batch_size: 20
  user_agent_rotation: true

sources:
  company:
    enabled: true
    websites:
      - name: "字节跳动"
        url: "https://jobs.bytedance.com/..."
        selector: { ... }
      - name: "腾讯"
        url: "https://careers.tencent.com/..."
        selector: { ... }
  
  boss:
    enabled: true
    rate_limit_per_minute: 1
    max_pages: 5
  
  nowcoder:
    enabled: true
    rate_limit_per_minute: 2
    max_pages: 3
```

---

## 三、调度设计

### 3.1 APScheduler 集成方式

**内嵌 FastAPI**（呼应 TASK-006 §5.1）：

```python
# crawler/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """初始化调度器"""
    # 从配置读取采集间隔
    interval_minutes = config.CRAWL_INTERVAL_MINUTES
    
    # 添加采集任务
    scheduler.add_job(
        crawl_all_sources,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='crawl_all',
        name='采集所有源',
        replace_existing=True
    )
    
    # 添加核验任务
    scheduler.add_job(
        verify_all_jobs,
        trigger=IntervalTrigger(hours=24),
        id='verify_jobs',
        name='核验岗位有效性',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"[SCHEDULER] Started, crawl interval: {interval_minutes} minutes")
```

### 3.2 调度策略

| 任务 | 频率 | 说明 |
|------|------|------|
| 采集所有源 | 每小时（默认，可配置） | 按 sources.yaml 配置执行 |
| 核验岗位有效性 | 每天一次 | 检查投递链接是否有效 |
| 手动触发 | 用户点击 | 对应 API `POST /crawler/trigger` |

### 3.3 并发控制 + 批量提交（v2 补充批量提交，呼应 TASK-006 v2 §4.3）

```python
# 并发控制
MAX_CONCURRENT = config.CRAWL_MAX_CONCURRENT  # 默认 3
BATCH_SIZE = 20  # v2 补充：每批入库条数，避免 SQLite 长事务锁库

def crawl_source(source: str):
    """单源采集（v2: 批量提交，呼应 TASK-006 v2 §4.3）"""
    adapter = get_adapter(source, config)
    if not adapter or not adapter.should_crawl():
        return
    
    start_time = datetime.utcnow()
    try:
        # 1. 抓取（同步，呼应 TASK-006 v2 全同步策略）
        raw_jobs = adapter.fetch()
        
        # 2. 清洗 + 归一化（不事务化）
        parsed_jobs = []
        for raw in raw_jobs:
            job_data = adapter.parse(raw)
            if job_data:
                job_data['company'] = normalize_company(job_data['company'])
                job_data['location'] = normalize_location(job_data['location'])
                parsed_jobs.append(job_data)
        
        # 3. v2 批量入库（每批 BATCH_SIZE 条一个事务，部分失败不影响整体）
        success_count = 0
        fail_count = 0
        for i in range(0, len(parsed_jobs), BATCH_SIZE):
            batch = parsed_jobs[i:i+BATCH_SIZE]
            try:
                with db.session.begin():  # 短事务
                    for job_data in batch:
                        is_dup, existing = deduplicate(job_data)
                        if is_dup:
                            if existing:
                                merge_jobs(existing, job_data)
                        else:
                            db.session.add(Job(**job_data))
                    success_count += len(batch)
            except Exception as batch_error:
                fail_count += len(batch)
                logger.warning(f"[CRAWL] {source} batch {i//BATCH_SIZE} failed: {batch_error}")
        
        # 4. 记录采集日志
        log_crawl_result(source, success=True,
                        total=len(raw_jobs), saved=success_count, failed=fail_count,
                        start_time=start_time)
    except Exception as e:
        log_crawl_result(source, success=False, error=str(e), start_time=start_time)
        raise
    finally:
        adapter.close()  # v2: 释放 httpx.Client / Playwright browser

def crawl_all_sources():
    """采集所有启用的源（并发控制）"""
    from concurrent.futures import ThreadPoolExecutor
    
    sources = get_enabled_sources()
    
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        futures = []
        for source in sources:
            future = executor.submit(crawl_source, source)
            futures.append(future)
        
        # 等待所有完成
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"[CRAWL] Source failed: {e}")
```

**为什么批量提交**（呼应 TASK-006 v2 §4.3）：
- SQLite 长事务持有写锁，阻塞其他读写
- 批量提交（每批 20 条）让锁持有时间极短
- 部分失败时已成功的批次保留，符合采集场景"尽量多保留有效数据"

### 3.4 调度日志写入 CrawlLog 表

```python
def log_crawl_result(source: str, success: bool, 
                     total: int = 0, saved: int = 0, failed: int = 0,
                     error: str = None):
    """记录采集日志"""
    log = CrawlLog(
        source=source,
        status='success' if success else 'failed',
        count=saved,
        error=error,
        started_at=start_time,
        finished_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
```

---

## 四、清洗与字段提取

### 4.1 字段映射

| 原始字段 | Job 表字段 | 说明 |
|---------|-----------|------|
| company_name | company | 公司名 |
| job_title | title | 岗位名 |
| job_location | location | 工作地点 |
| salary_range | salary | 薪资范围 |
| job_description | jd | 岗位描述 |
| job_requirement | requirement | 岗位要求 |
| apply_link | apply_url | 投递链接 |
| source_platform | source | 来源平台 |
| original_url | source_url | 原始页面 URL |
| publish_time | published_at | 发布时间 |
| deadline | deadline | 截止时间 |

**缺失字段处理**：

| 字段 | 缺失时处理 |
|------|-----------|
| salary | 标记为"薪资面议" |
| published_at | 标记为 NULL |
| deadline | 标记为 NULL |
| requirement | 从 jd 中提取 |

### 4.2 硬条件提取（呼应 PRD F-A.2 v3）

**毕业年份提取**：

```python
import re

def extract_graduation_year(text: str) -> Optional[str]:
    """提取毕业年份要求"""
    patterns = [
        r'20(\d{2})届',           # "2025届"
        r'20(\d{2})年毕业',       # "2025年毕业"
        r'毕业年份[：:]?\s*(\d{4})', # "毕业年份：2025"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return f"20{match.group(1)}" if len(match.group(1)) == 2 else match.group(1)
    return None  # 未识别
```

**学历要求提取**：

```python
def extract_education(text: str) -> Optional[str]:
    """提取学历要求"""
    if '博士' in text:
        return '博士'
    elif '硕士' in text:
        return '硕士'
    elif '本科' in text or '学士' in text:
        return '本科'
    elif '大专' in text or '专科' in text:
        return '大专'
    return None  # 未识别
```

**经验要求提取**：

```python
def extract_experience(text: str) -> Optional[str]:
    """提取经验要求"""
    patterns = [
        r'(\d+)[-\s]*\d*年经验',    # "3年经验" 或 "3-5年经验"
        r'经验[：:]?\s*(\d+)',      # "经验：3"
        r'无经验要求',              # "无经验要求"
        r'应届生',                  # "应届生"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if '无经验' in match.group() or '应届' in match.group():
                return '无经验要求'
            return f"{match.group(1)}年经验"
    return None  # 未识别
```

### 4.3 应届/实习标签

```python
def classify_job(title: str, jd: str) -> Dict[str, bool]:
    """判断岗位类型"""
    text = f"{title} {jd}".lower()
    
    # 实习判断
    is_intern = any(kw in text for kw in ['实习', 'intern', '实习生'])
    
    # 应届判断
    is_fresh = any(kw in text for kw in ['应届', '校招', '毕业生', '2025届', '2026届'])
    
    return {'is_intern': is_intern, 'is_fresh': is_fresh}
```

---

## 五、去重设计（重点）

### 5.1 去重挑战

| 挑战 | 说明 | 解决方案 |
|------|------|---------|
| location 不一致 | "北京市" vs "北京" vs "Beijing" | 归一化 |
| 公司名不一致 | "字节跳动" vs "北京字节跳动科技有限公司" | 归一化 |
| 跨源重复 | BOSS 和牛客同一岗位 | 跨源合并 |

### 5.2 去重策略（分层）

**第一层：采集层归一化**

```python
# crawler/normalizer.py

import re

def normalize_location(location: str) -> str:
    """地点归一化"""
    if not location:
        return ''
    
    # 去除"市""省"后缀
    location = re.sub(r'[省市]', '', location)
    
    # 英文转中文
    en_to_cn = {
        'beijing': '北京', 'shanghai': '上海', 'guangzhou': '广州',
        'shenzhen': '深圳', 'hangzhou': '杭州', 'chengdu': '成都',
    }
    location_lower = location.lower().strip()
    if location_lower in en_to_cn:
        return en_to_cn[location_lower]
    
    return location.strip()

def normalize_company(company: str) -> str:
    """公司名归一化"""
    if not company:
        return ''
    
    # 去除常见后缀
    suffixes = ['有限公司', '科技有限公司', '股份有限公司', '集团', '（中国）', '(中国)']
    for suffix in suffixes:
        company = company.replace(suffix, '')
    
    return company.strip()
```

**第二层：入库时唯一索引（v2 修正：普通字段，非函数索引）**

> ⚠️ v1 用了 `CREATE UNIQUE INDEX ... normalize_company(company)`（函数索引），但 SQLite **不支持函数索引**（注释自己都说了）。v2 删除该 SQL。
> 正确做法：归一化在应用层（normalizer.py）完成后入库，**入库时 company/location 已是归一化值**，唯一索引用普通字段（对齐 TASK-007 v2 §3.1）。

```sql
-- 对齐 TASK-007 v2：普通字段唯一索引（归一化已在应用层完成）
CREATE UNIQUE INDEX idx_job_dedup ON job(source, company, title, location);
```

**第三层：跨源合并（v2 修正：归一化后完全相等，非 contains）**

> ⚠️ v1 用 `Job.company.contains(normalized_company)`（LIKE '%xx%'），会导致"字节"误匹配"字节其他公司"等无关公司。
> v2 改为**归一化后完全相等**（`==`），与同源去重逻辑一致，消除误判。

```python
# crawler/dedup.py

def find_cross_source_duplicate(job_data: Dict) -> Optional[Job]:
    """
    查找跨源重复岗位（v2: 归一化后完全相等，非 contains）
    """
    # 归一化值已在 deduplicate() 入口处理，这里直接用
    normalized_company = job_data['company']  # 已归一化
    normalized_location = job_data['location']  # 已归一化
    
    # v2: 用完全相等（==），而非 contains，避免误判
    existing = db.session.query(Job).filter(
        Job.company == normalized_company,
        Job.title == job_data['title'],
        Job.location == normalized_location,
        Job.source != job_data['source']
    ).first()
    
    return existing

def merge_jobs(existing: Job, new_data: Dict) -> Job:
    """合并岗位信息（保留信息最全版本）"""
    # 如果新数据更完整，更新
    if new_data.get('salary') and not existing.salary:
        existing.salary = new_data['salary']
    if new_data.get('requirement') and not existing.requirement:
        existing.requirement = new_data['requirement']
    if new_data.get('deadline') and not existing.deadline:
        existing.deadline = new_data['deadline']
    # v2 补充：记录合并来源，便于溯源
    if not existing.source_url and new_data.get('source_url'):
        existing.source_url = new_data['source_url']
    
    return existing
```

> **v2 已知限制（诚实标注）**：归一化后完全相等会漏掉"字节跳动"vs"字节"这种部分匹配的真实重复。
> Demo 阶段取舍：宁可漏合并（用户可在列表里手动发现），不可误合并（污染数据）。
> 未来可引入相似度算法（如 Levenshtein）做模糊匹配，但需配合"用户确认合并"交互。

### 5.3 去重伪代码（完整流程）

```python
# crawler/dedup.py

def deduplicate(job_data: Dict) -> Tuple[bool, Optional[Job]]:
    """
    去重流程
    返回：(是否重复, 现有记录)
    """
    # 1. 归一化
    job_data['company'] = normalize_company(job_data['company'])
    job_data['location'] = normalize_location(job_data['location'])
    
    # 2. 同源去重（唯一索引）
    existing = db.session.query(Job).filter_by(
        source=job_data['source'],
        company=job_data['company'],
        title=job_data['title'],
        location=job_data['location']
    ).first()
    
    if existing:
        return True, existing
    
    # 3. 跨源合并
    cross_existing = find_cross_source_duplicate(job_data)
    if cross_existing:
        merged = merge_jobs(cross_existing, job_data)
        return True, merged
    
    return False, None
```

---

## 六、有效性核验（呼应 PRD F-A.6）

### 6.1 核验方式

```python
# crawler/verifier.py

from httpx import Client

def verify_job(job: Job) -> bool:
    """核验岗位有效性"""
    if not job.apply_url:
        return False
    
    try:
        response = Client().head(job.apply_url, timeout=10, follow_redirects=True)
        
        # 404 表示失效
        if response.status_code == 404:
            return False
        
        # 5xx 表示服务器异常，暂不判定
        if response.status_code >= 500:
            return None  # 无法判定
        
        return True
        
    except Exception as e:
        logger.warning(f"[VERIFY] Failed to verify {job.id}: {e}")
        return None  # 无法判定
```

### 6.2 失效判定

| 情况 | 判定 | 处理 |
|------|------|------|
| HTTP 404 | 失效 | is_valid = False |
| HTTP 5xx | 无法判定 | 保持原状态，下次重试 |
| 超时 | 无法判定 | 保持原状态，下次重试 |
| 页面结构变更 | 无法判定 | 人工检查 |

### 6.3 核验频率

| 任务 | 频率 | 说明 |
|------|------|------|
| 自动核验 | 每天一次 | 检查所有 is_valid=True 的岗位 |
| 手动核验 | 用户触发 | 对应 API `POST /jobs/{id}/verify` |

### 6.4 last_verified_at 更新策略

```python
def update_verification(job: Job, is_valid: bool):
    """更新核验结果（v2: status 用英文 code，对齐 TASK-007 v2）"""
    job.last_verified_at = datetime.utcnow()
    job.is_valid = is_valid
    if not is_valid:
        job.status = 'closed'  # v2 修正：英文 code，非 '已关闭'（否则违反 CHECK 约束）
    db.session.commit()
```

---

## 七、合规控制（重点，TASK-011 会严查）

### 7.1 robots.txt 尊重

> ⚠️ **v2 关键修正（合规）**：v1 在"无法读取 robots.txt 时默认允许"（fail-open），这是合规硬伤——会被判定为故意绕过 robots.txt。
> v2 改为 **fail-closed**：无法读取时默认**禁止**抓取，记录告警，等待人工评估。

```python
# crawler/compliance/robots.py

from urllib.robotparser import RobotFileParser

class RobotsChecker:
    """robots.txt 检查器（fail-closed 策略）"""
    
    def __init__(self):
        self._cache = {}  # 缓存已解析的 robots.txt
        self._unreadable = set()  # 记录无法读取的站点
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """检查是否允许抓取（fail-closed）"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # 已标记为不可读的站点，直接禁止（fail-closed）
        if base_url in self._unreadable:
            return False
        
        # 获取 robots.txt
        if base_url not in self._cache:
            rp = RobotFileParser()
            rp.set_url(f"{base_url}/robots.txt")
            try:
                rp.read()
                self._cache[base_url] = rp
            except Exception as e:
                # v2 关键修正：无法读取时 FAIL-CLOSED（禁止），而非 fail-open
                # 记录告警，等待人工评估是否允许
                logger.warning(
                    f"[ROBOTS] 无法读取 {base_url}/robots.txt: {e}，"
                    f"按 fail-closed 策略禁止抓取，需人工评估"
                )
                self._unreadable.add(base_url)
                return False
        
        return self._cache[base_url].can_fetch(user_agent, url)
    
    def mark_allowed_manually(self, base_url: str):
        """人工评估后手动标记允许（覆盖 fail-closed）"""
        self._unreadable.discard(base_url)
        # 标记为"无 robots 限制"（等价于允许全部）
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.parse([])  # 空规则 = 全部允许
        self._cache[base_url] = rp
        logger.info(f"[ROBOTS] {base_url} 已被人工标记为允许抓取")
```

**为什么 fail-closed**：
- 合规审计时，"读取失败就允许"会被判定为"故意绕过 robots.txt 检查"
- 正确的保守策略是"无法确认允许时禁止"，让人工显式授权
- 这是 TASK-011 安全门禁的必查项

### 7.2 速率限制 + 指数退避重试（v2 补充重试）

```python
# crawler/compliance/rate_limiter.py

import time
from collections import defaultdict

class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self._last_request = defaultdict(float)
        self._min_interval = 60  # 每源每分钟 ≤1 次
    
    def wait_if_needed(self, source: str):
        """如果需要，等待到允许请求"""
        now = time.time()
        elapsed = now - self._last_request[source]
        
        if elapsed < self._min_interval:
            wait_time = self._min_interval - elapsed
            logger.debug(f"[RATE_LIMIT] {source}: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        self._last_request[source] = time.time()
```

**v2 补充：指数退避重试**（请求失败时使用，避免雪崩）

```python
# crawler/compliance/retry.py

import time
import random

def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError)
):
    """
    指数退避重试（v2 新增）
    - 仅对可重试异常（网络/超时）重试，其他异常立即抛出
    - 指数退避 + 抖动（jitter），避免多个客户端同时重试造成雪崩
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"[RETRY] 已达最大重试次数 {max_retries}，放弃: {e}")
                raise
            # 指数退避 + 抖动：delay = min(base * 2^attempt + random, max)
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            logger.warning(f"[RETRY] 第 {attempt+1} 次失败，{delay:.1f}s 后重试: {e}")
            time.sleep(delay)
        except Exception as e:
            # 非可重试异常（如 HTTP 404、解析错误），立即抛出
            raise
    raise last_exception
```

**使用示例**：
```python
# 在适配器的 fetch_detail 中应用
from crawler.compliance.retry import retry_with_backoff

def fetch_detail(self, url: str):
    def _do_fetch():
        response = self.client.get(url)
        response.raise_for_status()
        return response.text
    
    try:
        return retry_with_backoff(_do_fetch, max_retries=3)
    except (ConnectionError, TimeoutError):
        return None  # 重试耗尽，返回 None
```

**重试策略说明**：
- **可重试异常**：ConnectionError、TimeoutError（网络问题，重试有意义）
- **不可重试异常**：HTTP 404（资源不存在，重试无用）、解析错误（代码 bug，重试无用）
- **指数退避**：1s → 2s → 4s（+ 抖动），避免雪崩
- **最大重试 3 次**：超过则放弃，记录日志

### 7.3 数据合规

| 规则 | 说明 |
|------|------|
| 仅采集已审核公开来源 | “页面能打开”不等于允许自动收集 |
| 不存储个人隐私 | HR 联系方式等不入库 |
| 引用来源标注 | source_url 必填 |
| 固定声明身份 | 使用可配置、非伪装浏览器的固定 User-Agent |
| 逐源限速 | 按来源约定和站点能力设置，不用统一频率掩盖未授权访问 |
| 遵守 robots 与条款 | 两者都检查；任一无法确认时 fail closed |

### 7.4 合规风险评估表

| 数据源 | 风险等级 | robots.txt | ToS | 对策 |
|--------|---------|------------|-----|------|
| 已审核企业官网/ATS | 逐源 | 逐源检查 | 逐源检查 | 注册、契约测试通过后开启 |
| 政府/高校就业平台 | 逐源 | 逐源检查 | 逐源检查 | 优先做发现与核验，保留原文链接 |
| 公众号公开文章 URL | 中 ⚠️ | 不等同普通网站 | 无全网开放采集承诺 | 已知 URL + 最小必要字段 + 人工复核 |
| BOSS 直聘 | 高 ⚠️ | 非唯一依据 | 明确禁止未经许可抓取 | 禁用；只接受授权/API/合作 |
| 猎聘 | 高 ⚠️ | 非唯一依据 | 明确禁止程序抓取 | 不建批量适配器；只接受授权/API/合作 |
| 牛客等社区/平台 | 待评估 | 逐源检查 | 逐源检查 | 未完成评估前禁用 |

---

## 八、与 TASK-006/007/008 的对齐

| 任务 | 对齐点 | 本设计如何落地 |
|------|--------|---------------|
| TASK-006 | 全同步策略 | 使用 httpx.Client / sync_playwright，非 async |
| TASK-006 | 批量提交 | 每批 20 条一个事务 |
| TASK-007 | location 归一化 | normalizer.py 实现 |
| TASK-007 | 去重唯一索引 | 同源去重 + 跨源合并 |
| TASK-007 | CrawlLog 表 | 每次采集写入日志 |
| TASK-008 | POST /crawler/trigger | 手动触发采集 |
| TASK-008 | GET /crawler/logs | 查询采集日志 |

---

*文档版本：v1.0 | 创建日期：2026-06-22*
