"""集中配置（pydantic-settings）。运行目录应为 backend/，或设置 DATA_DIR。"""
from pathlib import Path
from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=Path("data"), description="相对 BACKEND_ROOT 或绝对路径")

    china_geojson_url: str = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    china_geojson_local: Path = Field(default=Path("data/geo/china_100000_full.json"))

    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        validation_alias=AliasChoices("NEO4J_URI", "NEO4J_URL"),
    )
    neo4j_username: str = Field(
        default="neo4j",
        validation_alias=AliasChoices("NEO4J_USERNAME", "NEO4J_USER"),
    )
    neo4j_password: str = "12345sss"
    neo4j_database: str = "neo4j"
    neo4j_query_timeout: float = 30.0
    neo4j_refresh_schema: bool = False
    cypher_block_call: bool = Field(
        default=False,
        description="为 True 时拒绝含 CALL 的 Cypher（更严，可能误伤只读过程）",
    )

    openai_api_key: str = ""
    openai_api_base: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    admin_api_key: str = Field(default="", description="非空时 /api/admin/* 需 Header: X-Admin-Key")

    qa_cache_max_entries: int = 256
    qa_cache_ttl_seconds: int = 3600
    qa_use_simple_template: bool = True

    @model_validator(mode="after")
    def _resolve_paths(self):
        data = self.data_dir if self.data_dir.is_absolute() else (BACKEND_ROOT / self.data_dir).resolve()
        geo = (
            self.china_geojson_local
            if self.china_geojson_local.is_absolute()
            else (BACKEND_ROOT / self.china_geojson_local).resolve()
        )
        object.__setattr__(self, "data_dir", data)
        object.__setattr__(self, "china_geojson_local", geo)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
