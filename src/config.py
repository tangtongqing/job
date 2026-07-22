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

    # Web / deployment
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3100,http://127.0.0.1:3100"
    )

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
    crawler_trigger_enabled: bool = True

    # 业务阈值
    no_response_days: int = 14
    demo_reset_enabled: bool = True

    # 日志
    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def allowed_cors_origins(self) -> list[str]:
        """Return normalized origins from the deployment-friendly CSV setting."""
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
