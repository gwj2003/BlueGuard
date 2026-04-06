"""Centralized application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent
DEFAULT_ALLOW_ORIGINS = ["http://localhost:5173", "http://localhost:5174"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default=Path("data"), description="Seed/static data directory.")
    runtime_dir: Path = Field(default=Path("runtime"), description="Runtime outputs and local database.")
    allow_origins: list[str] | str = Field(
        default_factory=lambda: DEFAULT_ALLOW_ORIGINS.copy(),
        validation_alias=AliasChoices("ALLOW_ORIGINS", "CORS_ALLOW_ORIGINS"),
    )

    china_geojson_url: str = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"
    china_geojson_local: Path = Field(default=Path("data/geo/china_100000_full.json"))

    neo4j_uri: str = Field(default="bolt://localhost:7687", validation_alias=AliasChoices("NEO4J_URI", "NEO4J_URL"))
    neo4j_username: str = Field(default="neo4j", validation_alias=AliasChoices("NEO4J_USERNAME", "NEO4J_USER"))
    neo4j_password: str = Field(default="", validation_alias=AliasChoices("NEO4J_PASSWORD", "NEO4J_PASS"))
    neo4j_database: str = "neo4j"
    neo4j_query_timeout: float = 30.0
    neo4j_refresh_schema: bool = False
    cypher_block_call: bool = Field(default=False, description="Reject generated Cypher with CALL.")

    openai_api_key: str = ""
    openai_api_base: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    admin_api_key: str = ""

    qa_cache_max_entries: int = 256
    qa_cache_ttl_seconds: int = 3600
    qa_use_simple_template: bool = True

    @property
    def database_path(self) -> Path:
        return self.runtime_dir / "species.db"

    @model_validator(mode="after")
    def _resolve_paths(self):
        data_dir = self.data_dir if self.data_dir.is_absolute() else (BACKEND_ROOT / self.data_dir).resolve()
        runtime_dir = self.runtime_dir if self.runtime_dir.is_absolute() else (BACKEND_ROOT / self.runtime_dir).resolve()
        geo_path = (
            self.china_geojson_local
            if self.china_geojson_local.is_absolute()
            else (BACKEND_ROOT / self.china_geojson_local).resolve()
        )
        origins = self.allow_origins
        normalized_origins = (
            [item.strip() for item in origins.split(",") if item.strip()]
            if isinstance(origins, str)
            else [str(item).strip() for item in origins if str(item).strip()]
        )

        object.__setattr__(self, "data_dir", data_dir)
        object.__setattr__(self, "runtime_dir", runtime_dir)
        object.__setattr__(self, "china_geojson_local", geo_path)
        object.__setattr__(self, "allow_origins", normalized_origins or DEFAULT_ALLOW_ORIGINS.copy())
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
