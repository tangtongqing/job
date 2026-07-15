"""JobPulse 配置层。

从环境变量读取配置，带默认值。pydantic-settings 自动加载 .env 文件。
对应架构文档 system-architecture.md §6 配置项清单。
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 数据库
    database_url: str = "sqlite:///data/jobpulse.db"

    # LLM
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_timeout: int = 5
    llm_max_per_minute: int = 10

    # 采集
    crawl_interval_minutes: int = 60
    crawl_max_concurrent: int = 3
    crawl_user_agent: str = "JobPulse/1.0"

    # 业务阈值
    no_response_days: int = 14
    demo_reset_enabled: bool = True

    # 日志
    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
