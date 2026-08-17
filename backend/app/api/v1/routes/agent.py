"""Endpoint de l'agent orchestré par LangGraph.

GET /agent/analyze/{fen} : lance le graphe complet et renvoie une réponse unifiée
(coups théoriques, évaluation, contexte, vidéos, synthèse en langage naturel).
"""
from fastapi import APIRouter, HTTPException

from app.agent import graph
from app.services.chess_utils import validate_fen

router = APIRouter(tags=["agent"])


@router.get("/agent/analyze/{fen:path}")
def analyze(fen: str) -> dict:
    """Analyse complète d'une position par l'agent."""
    # Validation en amont pour renvoyer un 422 clair (le graphe la refait aussi).
    try:
        validate_fen(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    state = graph.analyze(fen)

    if state.get("error"):
        raise HTTPException(status_code=422, detail=state["error"])

    return {
        "fen": fen,
        "opening": state.get("opening"),
        "opening_name": state.get("opening_name"),
        "is_theoretical": state.get("is_theoretical", False),
        "moves": state.get("moves", []),
        "moves_source": state.get("moves_source", ""),
        "evaluation": state.get("evaluation"),
        "rag_results": state.get("rag_results", []),
        "videos": state.get("videos", []),
        "synthesis": state.get("synthesis", ""),
        "synthesis_source": state.get("synthesis_source", ""),
    }
