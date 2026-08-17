"""Service d'accès aux coups théoriques d'ouverture.

Source primaire : l'API Lichess (Opening Explorer).
Source de repli : une base d'ouvertures embarquée (openings_fallback.json).

L'Opening Explorer de Lichess (explorer.lichess.ovh) s'est révélé instable
depuis l'incident d'infrastructure OVH de février 2026 : il renvoie par
intermittence des erreurs 401/429 au niveau de sa passerelle nginx, avant même
d'atteindre l'application. Pour qu'un POC destiné à une démonstration client ne
dépende pas de la disponibilité d'une API tierce, ce service applique le pattern
"appel externe + repli gracieux" : si Lichess echoue, on sert des données
théoriques locales pour les principales ouvertures.
"""
import json
from pathlib import Path

import httpx

from app.core.config import get_settings

settings = get_settings()

_EXPLORER_URL = f"{settings.LICHESS_API_BASE}/lichess"
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_HEADERS = {
    "User-Agent": "FFE-Chess-Agent-POC/0.1 (contact: dev@ffe.fr)",
    "Accept": "application/json",
}

# Chargement unique de la base de repli au démarrage du module.
_FALLBACK_PATH = Path(__file__).parent / "data" / "openings_fallback.json"
with _FALLBACK_PATH.open(encoding="utf-8") as f:
    _FALLBACK_DATA: dict = json.load(f)


class LichessError(Exception):
    """Erreur levée quand l'appel a Lichess echoue (reseau, timeout, statut HTTP)."""


def _normalize_lichess_response(data: dict, top_moves: int) -> dict:
    """Transforme la reponse brute de Lichess en notre format normalise."""
    total = data.get("white", 0) + data.get("draws", 0) + data.get("black", 0)
    moves = []
    for m in data.get("moves", [])[:top_moves]:
        games = m.get("white", 0) + m.get("draws", 0) + m.get("black", 0)
        moves.append(
            {
                "uci": m.get("uci"),
                "san": m.get("san"),
                "games": games,
                "white_pct": round(100 * m.get("white", 0) / games, 1) if games else 0,
                "draw_pct": round(100 * m.get("draws", 0) / games, 1) if games else 0,
                "black_pct": round(100 * m.get("black", 0) / games, 1) if games else 0,
            }
        )
    return {"opening": data.get("opening"), "total_games": total, "moves": moves}


def _fallback_lookup(fen: str, top_moves: int):
    """Cherche la position dans la base locale. On compare sur les 3 premiers
    champs du FEN (placement des pieces, trait, roques) en ignorant la prise en
    passant et les compteurs de coups. C'est indispensable car un echiquier
    genere le champ de prise en passant (ex. 'e3' apres 1.e4) alors que la base
    peut le stocker a '-' : comparer ces champs ferait echouer la correspondance."""
    def key(f: str) -> str:
        return " ".join(f.split()[:3])

    target = key(fen)
    for stored_fen, payload in _FALLBACK_DATA.items():
        if key(stored_fen) == target:
            result = dict(payload)
            result["moves"] = result["moves"][:top_moves]
            return result
    return None


async def get_theoretical_moves(fen: str, top_moves: int = 8) -> dict:
    """Retourne les coups theoriques depuis une position FEN.

    Tente d'abord Lichess ; en cas d'echec, bascule sur la base locale.
    Le champ `source` indique l'origine des donnees ("lichess" ou "fallback").

    Raises:
        LichessError: uniquement si Lichess echoue ET que la position est
            absente de la base de repli.
    """
    params = {
        "fen": fen,
        "moves": top_moves,
        "topGames": 0,
        "recentGames": 0,
        "variant": "standard",
        "speeds": "blitz,rapid,classical",
        "ratings": "1600,1800,2000,2200,2500",
    }

    # --- Tentative sur l'API Lichess ---
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as client:
            response = await client.get(_EXPLORER_URL, params=params)
            response.raise_for_status()
            data = response.json()
        result = _normalize_lichess_response(data, top_moves)
        result["source"] = "lichess"
        return result
    except (httpx.HTTPError, ValueError):
        # Reseau, timeout, statut HTTP (401/429...) ou JSON invalide :
        # on tente le repli local plutot que d'echouer.
        pass

    # --- Repli sur la base locale ---
    fallback = _fallback_lookup(fen, top_moves)
    if fallback is not None:
        fallback["source"] = "fallback"
        return fallback

    raise LichessError(
        "Lichess est indisponible et la position n'est pas dans la base locale."
    )
