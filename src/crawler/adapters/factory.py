"""适配器工厂（crawler-module.md §2.3 配置驱动注册）。

按配置 source 名创建对应适配器，支持注入测试依赖。
"""

from __future__ import annotations

from src.crawler.adapters.base import BaseAdapter
from src.crawler.adapters.company import CompanyWebsiteAdapter
from src.crawler.adapters.boss import BossAdapter
from src.crawler.adapters.nowcoder import NowcoderAdapter
from src.crawler.adapters.greenhouse import GreenhouseAdapter
from src.crawler.adapters.cmb_campus import CmbCampusAdapter

# source 名 → 适配器类
_REGISTRY: dict[str, type[BaseAdapter]] = {
    "company": CompanyWebsiteAdapter,
    "boss": BossAdapter,
    "nowcoder": NowcoderAdapter,
    "greenhouse": GreenhouseAdapter,
    "cmb_campus": CmbCampusAdapter,
}


def create_adapter(
    source: str,
    config: dict | None = None,
    robots_checker=None,
    **kwargs,
) -> BaseAdapter:
    """按 source 名创建适配器。

    Args:
        source: 适配器名（company/boss/nowcoder/greenhouse/cmb_campus）
        config: 适配器配置
        robots_checker: 注入 RobotsChecker（测试用）
        **kwargs: 其他注入参数（如 company 的 html_fetcher）
    """
    cls = _REGISTRY.get(source)
    if cls is None:
        raise ValueError(f"未知 adapter source: {source}（已知: {list(_REGISTRY)}）")

    cfg = {"source_name": source, **(config or {})}
    # 各适配器构造参数不同，统一用 try 兼容
    try:
        return cls(config=cfg, robots_checker=robots_checker, **kwargs)
    except TypeError:
        # 某些适配器可能不接 robots_checker/kwargs
        return cls(config=cfg)


def register_adapter(source: str, cls: type[BaseAdapter]) -> None:
    """注册新适配器（扩展用）。"""
    _REGISTRY[source] = cls
