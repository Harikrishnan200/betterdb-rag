from __future__ import annotations

import redis as redis_lib
from fastembed import TextEmbedding
from groq import AsyncGroq
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    groq_api_key: SecretStr
    redis_url: str = "redis://localhost:6379"
    groq_model: str = "llama-3.3-70b-versatile"
    # Local ONNX embedding model — runs on CPU, no API key, 384 dims.
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 500
    chunk_overlap: int = 50
    cache_threshold: float = 0.85
    rate_limit_minute: int = 10
    rate_limit_hour: int = 100


_settings: Settings | None = None
_redis: redis_lib.Redis | None = None
_groq: AsyncGroq | None = None
_embedder: TextEmbedding | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_redis() -> redis_lib.Redis:
    global _redis
    if _redis is None:
        _redis = redis_lib.from_url(get_settings().redis_url, decode_responses=True)
    return _redis


def get_groq() -> AsyncGroq:
    global _groq
    if _groq is None:
        _groq = AsyncGroq(api_key=get_settings().groq_api_key.get_secret_value())
    return _groq


def get_embedder() -> TextEmbedding:
    """Local embedding model. First call downloads ~130MB of ONNX weights, then caches."""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=get_settings().embedding_model)
    return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Synchronous local embedding. Returns one vector per input text."""
    return [vec.tolist() for vec in get_embedder().embed(texts)]
