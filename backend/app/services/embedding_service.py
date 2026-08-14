"""Service d'embedding : transforme du texte en vecteurs.

On utilise sentence-transformers avec le modèle MiniLM (léger, 384 dimensions),
adapté à un POC : rapide, ~80 Mo, standard de l'industrie. Pour monter en
qualité, il suffit de changer EMBEDDING_MODEL / EMBEDDING_DIM dans la config.

Le modèle est chargé paresseusement (au premier appel) puis mis en cache, pour
ne pas ralentir le démarrage de l'API ni le télécharger inutilement.
"""
from functools import lru_cache

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def _get_model():
    """Charge le modèle une seule fois (import différé : lourd à importer)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    """Encode une liste de textes en vecteurs normalisés.

    La normalisation L2 permet d'utiliser la similarité cosinus dans Milvus.
    """
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    """Raccourci pour encoder un seul texte."""
    return embed([text])[0]
