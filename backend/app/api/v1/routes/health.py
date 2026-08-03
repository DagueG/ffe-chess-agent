"""Endpoint de santé (healthcheck).

Permet de vérifier rapidement que le conteneur FastAPI répond correctement.
Objectif de l'étape 1 : GET /api/v1/healthcheck -> 200 OK.
"""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/healthcheck")
def healthcheck() -> dict:
    """Retourne l'état du service. Utilisé par Docker et le monitoring."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
