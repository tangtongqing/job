"""AI 邮件解析器（三级降级链核心）。

对应 ai-parser-module.md §4.4 + TASK-BE-AI-001 §3：
LLM（高置信度）→ 正则（低置信度）→ parsed=false

降级触发条件：
- 无 API Key → 直接正则
- 限流超限 → 直接正则
- LLM 异常/超时/认证错误 → 正则
- LLM 返回非法 JSON / 非法 status → 正则
- LLM 置信度 < 阈值 → 正则

隐私：
- 不记录邮件原文
- 缓存 key 用 hash
- Prompt 明确只提取不执行
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Protocol

from src.config import get_settings
from src.core.ai.schemas import ParsedEmailResult, SUGGESTABLE_STATUSES
from src.core.ai.regex_parser import RegexParser
from src.core.ai.cache import TTLCache, text_hash
from src.core.ai.rate_limiter import AIRateLimiter
from src.core.ai.prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_THRESHOLD = 0.7


class LLMClient(Protocol):
    """LLM 客户端接口（便于注入 fake）。"""

    async def call(self, system_prompt: str, user_text: str) -> str:
        """返回 LLM 响应文本（应为 JSON）。失败抛异常。"""
        ...


class AIParser:
    """邮件解析器（三级降级）。

    使用 openai SDK 1.0+ AsyncOpenAI。
    无 Key / 异常 / 低置信度 → 降级正则。
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        cache_ttl: int = 3600,
        max_per_minute: int = 10,
        client: LLMClient | None = None,
        clock: Callable[[], float] | None = None,
    ):
        settings = get_settings()
        self._api_key = api_key if api_key is not None else (
            settings.deepseek_api_key or settings.openai_api_key or ""
        )
        self._model = model or settings.llm_model
        self._base_url = base_url
        self._threshold = confidence_threshold
        self._regex = RegexParser()
        self._cache = TTLCache(ttl=cache_ttl)
        self._rate_limiter = AIRateLimiter(max_per_minute, clock=clock)
        self._client = client  # 注入的 fake client（测试用）

    @property
    def has_api_key(self) -> bool:
        return bool(self._api_key)

    async def parse_email(self, email_text: str) -> ParsedEmailResult:
        """解析邮件文本（三级降级）。"""
        if not email_text or not email_text.strip():
            return ParsedEmailResult(parsed=False, degraded=True)

        # 缓存命中（key=hash，不存原文）
        h = text_hash(email_text)
        cached = self._cache.get(h)
        if cached is not None:
            logger.debug(f"[AI] cache hit, hash={h}")
            return cached

        # 无 API Key → 直接正则降级
        if not self.has_api_key:
            logger.info("[AI] 无 API Key，降级正则")
            result = self._regex.parse(email_text)
            self._cache.set(h, result)
            return result

        # 限流超限 → 直接正则降级
        if not self._rate_limiter.allow():
            logger.warning("[AI] 限流超限，降级正则")
            result = self._regex.parse(email_text)
            self._cache.set(h, result)
            return result

        # 尝试 LLM
        try:
            result = await self._call_llm(email_text)
            if result is None or not result.parsed:
                # LLM 无法解析 → 正则
                logger.info("[AI] LLM 未解析，降级正则")
                result = self._regex.parse(email_text)
            elif result.confidence < self._threshold:
                # 低置信度 → 正则
                logger.info(
                    f"[AI] LLM 置信度 {result.confidence} < {self._threshold}，降级正则"
                )
                result = self._regex.parse(email_text)
            # 成功
            self._cache.set(h, result)
            return result
        except Exception as e:
            logger.warning(f"[AI] LLM 异常，降级正则: {type(e).__name__}")
            result = self._regex.parse(email_text)
            self._cache.set(h, result)
            return result

    async def _call_llm(self, email_text: str) -> ParsedEmailResult | None:
        """调用 LLM 并解析响应。失败返回 None（上层降级）。"""
        client = self._get_client()
        if client is None:
            return None

        raw = await asyncio.wait_for(
            client.call(SYSTEM_PROMPT, email_text),
            timeout=get_settings().llm_timeout,
        )
        return self._parse_llm_response(raw)

    def _get_client(self) -> LLMClient | None:
        """获取 LLM 客户端（注入或真实 AsyncOpenAI）。"""
        if self._client is not None:
            return self._client
        # 真实 AsyncOpenAI（openai SDK 1.0+）
        try:
            from openai import AsyncOpenAI
        except ImportError:
            logger.warning("[AI] openai SDK 未安装")
            return None

        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        elif self._api_key and not self._api_key.startswith("sk-"):
            # DeepSeek 等 OpenAI 兼容 API
            kwargs["base_url"] = "https://api.deepseek.com/v1"

        client = AsyncOpenAI(**kwargs)

        # 包装成 LLMClient 接口
        class _Adapter:
            def __init__(self, oai):
                self._oai = oai

            async def call(self, system_prompt: str, user_text: str) -> str:
                resp = await self._oai.chat.completions.create(
                    model=self._model if hasattr(self, "_model") else None,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
                    ],
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content or ""

        adapter = _Adapter(client)
        adapter._model = self._model  # type: ignore
        return adapter

    def _parse_llm_response(self, raw: str) -> ParsedEmailResult | None:
        """解析 LLM 的 JSON 响应。非法 JSON/字段 → None。"""
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("[AI] LLM 返回非法 JSON")
            return None

        parsed = data.get("parsed", False)
        if not parsed:
            return ParsedEmailResult(parsed=False, degraded=False)

        status = data.get("suggested_status")
        if status is not None and status not in SUGGESTABLE_STATUSES:
            logger.warning(f"[AI] LLM 返回非法 status: {status}")
            return None  # 触发降级

        confidence = data.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        return ParsedEmailResult(
            parsed=True,
            company=data.get("company"),
            title=data.get("title"),
            suggested_status=status,
            confidence=confidence,
            degraded=False,
            reasoning=data.get("reasoning"),
        )
