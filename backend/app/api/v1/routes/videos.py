"""Endpoint de recherche de vidéos explicatives YouTube.

GET /videos/{opening} : renvoie des vidéos pédagogiques pour une ouverture.
"""
from fastapi import APIRouter, HTTPException, Query

from app.services import youtube_service

router = APIRouter(tags=["videos"])


@router.get("/videos/{opening}")
def get_videos(
    opening: str,
    max_results: int = Query(5, ge=1, le=10),
) -> dict:
    """Retourne des vidéos YouTube explicatives pour l'ouverture demandée."""
    try:
        result = youtube_service.search_videos(opening, max_results=max_results)
    except youtube_service.YouTubeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result["opening"] = opening
    result["count"] = len(result["videos"])
    return result
