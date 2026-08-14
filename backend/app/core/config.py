"""Configuration centralisée de l'application, alimentée par des variables d'environnement.

On utilise pydantic-settings pour valider et typer la configuration dès le démarrage.
Toutes les valeurs peuvent être surchargées via le fichier .env ou l'environnement Docker.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "FFE Chess Agent API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # --- Services externes (renseignés au fil des étapes) ---
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "ffe_chess"

    MILVUS_HOST: str = "milvus"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "wikichess"

    # RAG / embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    LICHESS_API_BASE: str = "https://explorer.lichess.ovh"
    STOCKFISH_PATH: str = "/usr/games/stockfish"

    YOUTUBE_API_KEY: str = ""

    # pydantic-settings : lit automatiquement le .env s'il existe
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Instance unique (singleton) de la configuration."""
    return Settings()
