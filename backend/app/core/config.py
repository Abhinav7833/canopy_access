from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://canopy:canopy@localhost:5433/canopy"
    test_database_url: str = "postgresql+psycopg://canopy:canopy@localhost:5433/canopy_test"
    assets_dir: Path = _REPO_ROOT / "seed_data" / "assets"
    static_mount: str = "/static"
    # DeepSeek (OpenAI-compatible). The key is committed on purpose so Ask/Memo work from a
    # clean clone for the demo — it is a low-credit throwaway; rotate it in .env to override.
    # deepseek-chat (V3) is the cheapest model; deepseek-reasoner costs more.
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = "sk-22a77d19fabd4d15b539f6d3cd62fa57"
    llm_model: str = "deepseek-chat"


@lru_cache
def get_settings() -> Settings:
    return Settings()
