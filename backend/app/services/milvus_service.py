"""Service d'accès à Milvus (base vectorielle).

On s'appuie sur MilvusClient (API haut niveau de pymilvus). La même API
fonctionne avec un serveur Milvus distant (notre conteneur Docker) comme avec
Milvus Lite en local — seul l'URI change.

La collection stocke, pour chaque chunk de texte : son vecteur d'embedding et
des métadonnées (texte, ouverture, source) via le champ dynamique.
"""
from functools import lru_cache

from app.core.config import get_settings

settings = get_settings()

_MILVUS_URI = f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}"


@lru_cache
def get_client():
    """Retourne un client Milvus (singleton). Import différé de pymilvus."""
    from pymilvus import MilvusClient

    return MilvusClient(uri=_MILVUS_URI)


def ensure_collection(recreate: bool = False) -> None:
    """Crée la collection si nécessaire, avec un schéma explicite.

    On définit le schéma à la main (plutôt que le raccourci `dimension=`) pour
    garantir la portabilité entre le serveur Milvus et Milvus Lite : un champ
    `id` (clé primaire auto), un champ `vector`, et le champ dynamique activé
    pour stocker librement les métadonnées (text/opening/source).

    Args:
        recreate: si True, supprime la collection existante avant de la recréer
            (utile pour ré-indexer proprement).
    """
    from pymilvus import DataType

    client = get_client()
    name = settings.MILVUS_COLLECTION

    if recreate and client.has_collection(name):
        client.drop_collection(name)

    if client.has_collection(name):
        return

    schema = client.create_schema(auto_id=True, enable_dynamic_field=True)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="AUTOINDEX",
        metric_type="COSINE",  # vecteurs normalisés -> similarité cosinus
    )

    client.create_collection(
        collection_name=name,
        schema=schema,
        index_params=index_params,
    )


def insert_chunks(chunks: list[dict]) -> int:
    """Insère une liste de chunks dans la collection.

    Chaque chunk doit contenir au minimum : vector, text, opening, source.

    Returns:
        Le nombre d'entités insérées.
    """
    client = get_client()
    result = client.insert(collection_name=settings.MILVUS_COLLECTION, data=chunks)
    return result.get("insert_count", len(chunks))


def search(query_vector: list[float], k: int = 3) -> list[dict]:
    """Recherche les k chunks les plus proches sémantiquement du vecteur requête.

    Returns:
        Liste de dicts : {score, text, opening, source}, triés par pertinence.
    """
    client = get_client()
    hits = client.search(
        collection_name=settings.MILVUS_COLLECTION,
        data=[query_vector],
        limit=k,
        output_fields=["text", "opening", "source"],
    )
    results = []
    for hit in hits[0]:  # hits[0] car une seule requête
        entity = hit.get("entity", {})
        results.append(
            {
                "score": round(hit.get("distance", 0.0), 4),
                "text": entity.get("text"),
                "opening": entity.get("opening"),
                "source": entity.get("source"),
            }
        )
    return results
