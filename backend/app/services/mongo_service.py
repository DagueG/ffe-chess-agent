"""Service MongoDB : journalise chaque analyse de l'agent.

Sert d'historique (positions analysées, ouvertures rencontrées, recommandations).
Résilient : si Mongo est indisponible, on n'échoue pas — la journalisation est
un effet de bord, pas le coeur de la réponse.
"""
from datetime import datetime, timezone
from functools import lru_cache

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def _get_collection():
    """Connexion paresseuse à la collection d'analyses."""
    from pymongo import MongoClient

    client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
    return client[settings.MONGO_DB]["analyses"]


def log_analysis(document: dict) -> bool:
    """Enregistre une analyse. Retourne True si réussi, False sinon (sans lever)."""
    try:
        doc = dict(document)
        doc["created_at"] = datetime.now(timezone.utc)
        _get_collection().insert_one(doc)
        return True
    except Exception:
        return False
