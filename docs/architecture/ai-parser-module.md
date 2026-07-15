# AI 解析模块设计

> TASK-010 产出。基于 TASK-006/007/008 的架构决策，详细设计 AI 解析模块的 LLM 调用、三级降级链、成本控制、Prompt 工程、匹配逻辑。
>
> ---
> **版本**：v2（主智能体校准版）
> **v2 修订说明**：v1 质量高（openai 1.0+ 正确、三级降级完整、成本控制齐全），但 2 处值得校准：
> 1. **【中】matcher 用 contains 误判**：呼应 TASK-009 v2 硬伤 4，改用归一化后完全相等（contains 仅作回退，标注风险）
> 2. **【小】边界澄清**：§1.2 说"解析邮件/截图"，但全文只讲文本。明确 MVP 仅文本解析，截图列未来版本

---

## 一、模块总览

### 1.1 一句话定位

> AI 解析模块是 F-C.5 低成本状态更新的"亮点 + 降级"双角色——用 LLM 智能解析邮件文本，提取公司+岗位+状态建议，降低用户手动操作成本。

### 1.2 模块边界

| 做什么 | 不做什么 |
|--------|---------|
| 解析邮件文本 | 不直接写库（用户确认后才流转） |
| 提取公司+岗位+状态建议 | 不自动执行状态流转 |
| 匹配已有投递记录 | 不创建新投递 |
| 降级到正则/快捷交互 | 不保证 100% 准确 |

> ⚠️ **v2 边界澄清**：模块边界原写"解析邮件/截图文本"，但**MVP 仅支持纯文本解析**。
> - **文本**：用户粘贴邮件/微信文字 ✅ MVP 支持
> - **截图（图片）**：需要 OCR 或多模态 vision LLM，**列为未来版本** ❌ MVP 不做
> - 当前若用户有截图，需手动转为文本后粘贴

### 1.3 与其他模块的关系

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   api/      │────▶│  core/ai/   │────▶│  外部 LLM   │
│ (调用解析)  │     │ (解析模块)  │     │ (DeepSeek)  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    db/      │
                    │ (匹配查询)  │
                    └─────────────┘
```

---

## 二、三级降级链（核心）

### 2.1 降级链总览

| 级别 | 触发条件 | 输入 | 输出 | 置信度 | 成本 |
|------|---------|------|------|--------|------|
| **L1 LLM** | LLM 可用 + 限流未触发 + 缓存未命中 | 邮件文本 | 结构化解析 | ≥0.7 | 高（~$0.002/次） |
| **L2 正则** | LLM 不可用/超时/限流/低置信度 | 邮件文本 | 简单匹配 | 0.5 | 零 |
| **L3 None** | 正则也失败 | - | null | 0 | 零 |

### 2.2 各级详细说明

#### L1 LLM 解析

**触发条件**：
- LLM API 可用（无认证错误）
- 限流未触发（每分钟 ≤10 次）
- 缓存未命中（相同文本 1 小时内未调用）

**输入**：邮件文本（string）

**输出**：
```json
{
  "parsed": true,
  "company": "字节跳动",
  "title": "产品经理实习",
  "suggested_status": "interviewing",
  "confidence": 0.92,
  "reasoning": "邮件提到'恭喜通过笔试'和'邀请参加面试'",
  "degraded": false
}
```

**降级日志**：
```python
logger.info(f"[AI] LLM parsed: company={company}, status={status}, confidence={confidence}")
```

---

#### L2 正则解析

**触发条件**：
- LLM 超时（5 秒）
- LLM 限流（每分钟 >10 次）
- LLM 认证错误（API Key 无效）
- LLM 低置信度（<0.7）
- LLM 其他异常

**输入**：邮件文本（string）

**输出**：
```json
{
  "parsed": true,
  "company": "字节跳动",
  "title": null,
  "suggested_status": "interviewing",
  "confidence": 0.5,
  "reasoning": "关键词匹配：'笔试' + '面试'",
  "degraded": true
}
```

**降级日志**：
```python
logger.warning(f"[AI] LLM unavailable: {reason}, fallback to regex")
logger.info(f"[AI] Regex parsed: company={company}, status={status}")
```

---

#### L3 None（用户手动）

**触发条件**：
- 正则解析也失败（无法提取公司或状态）

**输出**：
```json
{
  "parsed": false,
  "company": null,
  "title": null,
  "suggested_status": null,
  "confidence": 0,
  "reasoning": null,
  "degraded": true
}
```

**降级日志**：
```python
logger.info("[AI] Regex parse failed, return None (user manual)")
```

---

## 三、LLM 调用设计（核心）

### 3.1 API 选型与调用

**默认选型：DeepSeek**

| 项目 | DeepSeek | OpenAI |
|------|----------|--------|
| 模型 | deepseek-chat | gpt-3.5-turbo |
| 成本 | ~$0.001/次 | ~$0.002/次 |
| 速度 | 快 | 中 |
| 中文能力 | 强 | 中 |
| JSON 支持 | 支持 | 支持 |

**调用方式：openai SDK 1.0+（AsyncOpenAI）**

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"  # DeepSeek 兼容 OpenAI 接口
)
```

### 3.2 Prompt 工程

**System Prompt**：

```
你是一个招聘信息解析助手。你的任务是从邮件/消息文本中提取以下信息：

1. company: 公司名称
2. title: 岗位名称
3. suggested_status: 建议的投递状态
   - applied: 投递确认
   - test: 笔试/测评邀请
   - interviewing: 面试邀请
   - offer_pending: 收到 Offer
   - rejected: 被拒绝
4. confidence: 置信度（0-1）
5. reasoning: 判断依据

**输出要求**：
- 必须输出合法的 JSON 格式
- 如果某个字段无法提取，设置为 null
- 置信度低于 0.7 时，建议用户手动确认

**示例输入**：
"您好，恭喜您通过字节跳动产品经理实习的笔试，现邀请您于6月25日下午2点参加一面。"

**示例输出**：
{
  "company": "字节跳动",
  "title": "产品经理实习",
  "suggested_status": "interviewing",
  "confidence": 0.95,
  "reasoning": "邮件明确提到'通过笔试'和'邀请参加面试'"
}
```

**Few-shot 示例**（嵌入 System Prompt）：

```
**更多示例**：

输入："您的简历已收到，我们会尽快筛选。"
输出：{
  "company": null,
  "title": null,
  "suggested_status": "applied",
  "confidence": 0.6,
  "reasoning": "简历收到是投递确认的常见表述"
}

输入："很遗憾，您未能通过本轮筛选。"
输出：{
  "company": null,
  "title": null,
  "suggested_status": "rejected",
  "confidence": 0.9,
  "reasoning": "'很遗憾' + '未能通过'是拒绝的明确信号"
}
```

### 3.3 调用伪代码

```python
# core/ai/parser.py

from openai import AsyncOpenAI, APITimeoutError, RateLimitError, AuthenticationError
import asyncio
import json

class AIParser:
    def __init__(self, config):
        self.client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.LLM_BASE_URL
        )
        self.model = config.LLM_MODEL  # "deepseek-chat"
        self.timeout = config.LLM_TIMEOUT  # 5 秒
        self.rate_limiter = RateLimiter(max_per_minute=config.LLM_MAX_PER_MINUTE)
        self.cache = TTLCache(ttl=config.LLM_CACHE_TTL)  # 3600 秒
    
    async def parse_email(self, email_text: str) -> Optional[ParsedResult]:
        """
        解析邮件文本
        三级降级：LLM → 正则 → None
        """
        # 0. 缓存命中
        cache_key = hash(email_text)
        if cache_key in self.cache:
            logger.debug("[AI] Cache hit")
            return self.cache[cache_key]
        
        # 1. 限流检查
        if not self.rate_limiter.allow():
            logger.warning("[AI] Rate limited, fallback to regex")
            return self._regex_parse(email_text)
        
        # 2. 尝试 LLM 解析
        try:
            result = await self._call_llm(email_text)
            if result and result.confidence >= 0.7:
                self.cache[cache_key] = result
                return result
            # 置信度低，降级
            logger.info(f"[AI] Low confidence: {result.confidence if result else 0}, fallback to regex")
        except APITimeoutError:
            logger.warning("[AI] LLM timeout, fallback to regex")
        except RateLimitError:
            logger.warning("[AI] LLM rate limited, fallback to regex")
        except AuthenticationError as e:
            logger.error(f"[AI] LLM auth error: {e}, fallback to regex")
        except Exception as e:
            logger.error(f"[AI] LLM unexpected error: {e}", exc_info=True)
        
        # 3. 降级到正则解析
        result = self._regex_parse(email_text)
        if result:
            self.cache[cache_key] = result
            return result
        
        # 4. 最终降级：返回 None
        return None
    
    async def _call_llm(self, text: str) -> Optional[ParsedResult]:
        """调用 LLM API（openai 1.0+ 语法）"""
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},  # 强制 JSON 输出
                temperature=0.1,  # 低温度，稳定输出
            ),
            timeout=self.timeout
        )
        
        content = response.choices[0].message.content
        return self._parse_llm_response(content)
    
    def _parse_llm_response(self, content: str) -> Optional[ParsedResult]:
        """解析 LLM 返回的 JSON"""
        try:
            data = json.loads(content)
            return ParsedResult(
                company=data.get('company'),
                title=data.get('title'),
                suggested_status=data.get('suggested_status'),
                confidence=data.get('confidence', 0),
                reasoning=data.get('reasoning'),
                degraded=False
            )
        except json.JSONDecodeError:
            logger.error(f"[AI] Failed to parse LLM response: {content}")
            return None
```

---

## 四、正则降级设计（L2）

### 4.1 关键词词典

**公司名词典**（常见公司）：

```python
COMPANY_KEYWORDS = {
    '字节跳动': ['字节', '字节跳动', 'bytedance', '抖音', '飞书'],
    '腾讯': ['腾讯', 'tencent', '微信', 'WeChat'],
    '阿里巴巴': ['阿里', '阿里巴巴', 'alibaba', '淘宝', '天猫'],
    '美团': ['美团', 'meituan'],
    '京东': ['京东', 'jd', 'jd.com'],
    '百度': ['百度', 'baidu'],
    '网易': ['网易', 'netease'],
    '快手': ['快手', 'kuaishou'],
    '小红书': ['小红书', 'xiaohongshu'],
    '拼多多': ['拼多多', 'pinduoduo'],
}
```

**状态关键词**：

```python
STATUS_KEYWORDS = {
    'applied': ['简历已收到', '投递成功', '已收到您的简历', '申请已提交'],
    'test': ['笔试', '测评', '在线考试', '能力测试', '性格测试'],
    'interviewing': ['面试', '一面', '二面', '三面', '终面', '视频面试', '现场面试'],
    'offer_pending': ['offer', '录用', '入职', '薪资', '入职时间'],
    'rejected': ['很遗憾', '未能通过', '不合适', '未通过', '拒绝', '不符合'],
}
```

### 4.2 提取规则

```python
# core/ai/regex_parser.py

import re

class RegexParser:
    """正则解析器（降级方案）"""
    
    def parse(self, text: str) -> Optional[ParsedResult]:
        """正则解析邮件文本"""
        company = self._extract_company(text)
        status = self._extract_status(text)
        
        if company and status:
            return ParsedResult(
                company=company,
                title=None,  # 正则无法可靠提取岗位名
                suggested_status=status,
                confidence=0.5,  # 固定置信度
                reasoning=f"关键词匹配：company='{company}', status='{status}'",
                degraded=True
            )
        return None
    
    def _extract_company(self, text: str) -> Optional[str]:
        """提取公司名"""
        for company, keywords in COMPANY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return company
        return None
    
    def _extract_status(self, text: str) -> Optional[str]:
        """提取状态"""
        text_lower = text.lower()
        
        # 按优先级检查（拒绝 > offer > 面试 > 笔试 > 投递）
        for status in ['rejected', 'offer_pending', 'interviewing', 'test', 'applied']:
            keywords = STATUS_KEYWORDS[status]
            for keyword in keywords:
                if keyword in text_lower:
                    return status
        return None
```

---

## 五、匹配逻辑

### 5.1 匹配流程

```
解析出 company + title
         ↓
查询 Application 表（关联 Job）
         ↓
    ┌────┴────┐
    │ 匹配数 │
    └────┬────┘
    ┌────┼────┐
    ▼    ▼    ▼
   0    1    N
   │    │    │
   │    │    └→ 返回多个，让用户选
   │    └→ 返回唯一匹配
   └→ 返回 null，用户手动创建
```

### 5.2 匹配伪代码（v2: 归一化优先，呼应 TASK-009 v2）

```python
# core/ai/matcher.py

from difflib import SequenceMatcher
# 复用采集层的归一化函数（TASK-009 v2 normalizer.py）
from crawler.normalizer import normalize_company

class ApplicationMatcher:
    """投递记录匹配器（v2: 归一化优先，contains 仅作回退）"""
    
    def match(self, company: str, title: str = None) -> Optional[int]:
        """
        匹配已有投递记录
        返回：application_id 或 None
        """
        if not company:
            return None
        
        # v2 关键修正：先用归一化后的完全相等查询（与 TASK-009 v2 去重逻辑一致）
        normalized = normalize_company(company)
        applications = db.session.query(Application).join(Job).filter(
            Job.company == normalized,  # 归一化后完全相等（非 contains，避免误判）
            Application.status.notin_([
                'offer_accepted', 'offer_declined', 'rejected', 'no_response', 'withdrawn'
            ])
        ).all()
        
        # v2 回退：归一化后无匹配，尝试 contains（模糊匹配，标注风险）
        if not applications:
            applications = db.session.query(Application).join(Job).filter(
                Job.company.contains(normalized),
                Application.status.notin_([
                    'offer_accepted', 'offer_declined', 'rejected', 'no_response', 'withdrawn'
                ])
            ).all()
            if applications:
                logger.info(f"[AI] 模糊匹配命中（可能误判，依赖用户确认）: {normalized}")
        
        if not applications:
            return None
        
        if len(applications) == 1:
            return applications[0].id
        
        # 多个匹配时，尝试用岗位名筛选
        if title:
            best_match = None
            best_score = 0
            
            for app in applications:
                score = self._similarity(title, app.job.title)
                if score > best_score:
                    best_score = score
                    best_match = app
            
            if best_score >= 0.6:  # 相似度阈值
                return best_match.id
        
        # 无法确定，返回 None 让用户选
        return None
    
    def _similarity(self, a: str, b: str) -> float:
        """字符串相似度"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
```

> **v2 匹配策略说明**（呼应 TASK-009 v2 归一化）：
> 1. **优先归一化完全相等**：`normalize_company` 去除"有限公司/科技"等后缀后，用 `==` 精确匹配（消除误判）
> 2. **回退 contains 模糊匹配**：归一化后无结果时，用 `LIKE '%xx%'` 兜底（容忍"字节"→"字节跳动"），但记录日志标注"可能误判"
> 3. **用户确认是最终防线**：即使匹配误判，前端展示建议 + 用户确认按钮，用户可纠正，不会污染数据
>
> 复用 TASK-009 v2 的 `normalize_company`，保证采集去重和 AI 匹配用同一套归一化逻辑（避免口径不一致）。

### 5.3 用户确认机制（关键）

**核心原则**：AI 结果仅作**建议**，不自动流转

**流程**：

```
用户粘贴邮件文本
       ↓
AI 解析（三级降级）
       ↓
返回建议结果（company/title/status/confidence）
       ↓
前端展示建议 + 确认按钮
       ↓
用户确认 → 调用 transition API
用户修改 → 修改后调用 transition API
用户取消 → 不执行
```

**前端展示示例**：

```jsx
function ParsedResultCard({ result }) {
  return (
    <Card>
      <CardHeader>AI 解析结果</CardHeader>
      <CardContent>
        <p>公司：{result.company || '未识别'}</p>
        <p>岗位：{result.title || '未识别'}</p>
        <p>建议状态：{STATUS_LABELS[result.suggested_status]}</p>
        <p>置信度：{(result.confidence * 100).toFixed(0)}%</p>
        {result.degraded && <Badge>降级解析</Badge>}
      </CardContent>
      <CardFooter>
        <Button onClick={onConfirm}>确认</Button>
        <Button variant="outline" onClick={onEdit}>修改</Button>
        <Button variant="ghost" onClick={onCancel}>取消</Button>
      </CardFooter>
    </Card>
  );
}
```

---

## 六、成本控制

### 6.1 控制点总览

| 控制点 | 策略 | 参数 | 说明 |
|--------|------|------|------|
| **缓存** | TTLCache | ttl=3600 | 相同邮件 1 小时内不重复调用 |
| **限流** | RateLimiter | max_per_minute=10 | 每分钟最多 10 次 LLM 调用 |
| **超时** | asyncio.wait_for | timeout=5 | 单次调用 5 秒超时 |
| **模型选择** | DeepSeek 默认 | - | 成本更低（~$0.001/次） |

### 6.2 RateLimiter 实现

```python
# core/ai/rate_limiter.py

import time
from collections import deque

class RateLimiter:
    """速率限制器（滑动窗口）"""
    
    def __init__(self, max_per_minute: int = 10):
        self.max_per_minute = max_per_minute
        self.window = deque()  # 存储请求时间戳
    
    def allow(self) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期的时间戳
        while self.window and self.window[0] < now - 60:
            self.window.popleft()
        
        # 检查是否超过限制
        if len(self.window) >= self.max_per_minute:
            return False
        
        # 记录本次请求
        self.window.append(now)
        return True
```

### 6.3 TTLCache 实现

```python
# core/ai/cache.py

import time
from typing import Any, Optional

class TTLCache:
    """带过期时间的缓存"""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache = {}  # key -> (value, expire_at)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            value, expire_at = self.cache[key]
            if time.time() < expire_at:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        self.cache[key] = (value, time.time() + self.ttl)
    
    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
```

### 6.4 成本估算

| 场景 | 调用次数 | 成本 |
|------|---------|------|
| 每天 10 封邮件 | 10 次 | ~$0.01 |
| 每月 300 封邮件 | 300 次 | ~$0.30 |
| 缓存命中率 50% | 150 次 | ~$0.15 |

**结论**：成本极低，Demo 阶段可忽略。

---

## 七、测试策略

### 7.1 LLM Mock 测试

```python
# tests/test_ai/test_parser.py

import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_llm_parse_success():
    """LLM 解析成功"""
    mock_response = {
        "choices": [{
            "message": {
                "content": '{"company": "字节跳动", "title": "产品经理实习", "suggested_status": "interviewing", "confidence": 0.95}'
            }
        }]
    }
    
    with patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        parser = AIParser(config)
        result = await parser.parse_email("恭喜您通过笔试，邀请参加面试")
        
        assert result.company == "字节跳动"
        assert result.suggested_status == "interviewing"
        assert result.confidence == 0.95
        assert result.degraded == False
```

### 7.2 正则降级测试

```python
@pytest.mark.asyncio
async def test_regex_fallback():
    """LLM 不可用时降级到正则"""
    with patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = APITimeoutError()
        
        parser = AIParser(config)
        result = await parser.parse_email("字节跳动：恭喜您通过笔试")
        
        assert result.company == "字节跳动"
        assert result.suggested_status == "test"
        assert result.confidence == 0.5
        assert result.degraded == True
```

### 7.3 匹配逻辑测试

```python
def test_match_single():
    """单个匹配"""
    matcher = ApplicationMatcher()
    
    # 假设数据库中有字节跳动的投递
    app_id = matcher.match("字节跳动", "产品经理实习")
    assert app_id is not None

def test_match_none():
    """无匹配"""
    matcher = ApplicationMatcher()
    
    app_id = matcher.match("不存在的公司")
    assert app_id is None

def test_match_multiple():
    """多个匹配，返回 None 让用户选"""
    matcher = ApplicationMatcher()
    
    # 假设数据库中有多个腾讯的投递
    app_id = matcher.match("腾讯")
    assert app_id is None  # 无法确定，返回 None
```

### 7.4 降级链测试

```python
@pytest.mark.asyncio
async def test_full_degradation_chain():
    """完整降级链：LLM → 正则 → None"""
    parser = AIParser(config)
    
    # 1. LLM 成功
    with patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_llm_response
        result = await parser.parse_email("字节跳动：恭喜通过笔试")
        assert result.degraded == False
    
    # 2. LLM 超时，降级到正则
    with patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = APITimeoutError()
        result = await parser.parse_email("字节跳动：恭喜通过笔试")
        assert result.degraded == True
    
    # 3. 正则也失败，返回 None
    with patch('openai.AsyncOpenAI.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = APITimeoutError()
        result = await parser.parse_email("无法解析的文本")
        assert result is None
```

---

## 八、与前置任务的对齐

| 任务 | 对齐点 | 本设计如何落地 |
|------|--------|---------------|
| TASK-006 | openai SDK 1.0+ | 使用 AsyncOpenAI |
| TASK-006 | 三级降级链 | LLM → 正则 → None |
| TASK-006 | 强制 JSON 输出 | response_format={"type": "json_object"} |
| TASK-006 | 成本控制 | 缓存/限流/超时/模型 |
| TASK-008 | matched_application_id | ApplicationMatcher 匹配 |
| TASK-008 | 用户确认 | 前端展示建议 + 确认按钮 |
| TASK-006 | LLM 异步入库同步 | LLM 用 AsyncOpenAI，入库用同步 Session |

---

*文档版本：v1.0 | 创建日期：2026-06-22*