"""Endpoint de recherche vectorielle (RAG - Retrieval).

GET /vector-search?query=...&k=... : renvoie les passages les plus pertinents
sur une ouverture, par similarité sémantique, depuis Milvus.
"""
from fastapi import APIRouter, HTTPException, Query

from app.services import embedding_service, milvus_service

router = APIRouter(tags=["rag"])


@router.get("/vector-search")
def vector_search(
    query: str = Query(..., description="Question ou nom d'ouverture"),
    k: int = Query(3, ge=1, le=10, description="Nombre de passages à retourner"),
) -> dict:
    """Recherche sémantique dans la base de connaissances Wikichess."""
    try:
        query_vector = embedding_service.embed_one(query)
        results = milvus_service.search(query_vector, k=k)
    except Exception as exc:  # Milvus indisponible, modèle absent, etc.
        raise HTTPException(
            status_code=503,
            detail=f"Recherche vectorielle indisponible : {exc}",
        ) from exc

    return {"query": query, "count": len(results), "results": results}
