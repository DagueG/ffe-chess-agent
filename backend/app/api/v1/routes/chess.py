"""Endpoints liés à l'analyse d'une position d'échecs.

- GET /moves/{fen}     -> coups théoriques via Lichess
- GET /evaluate/{fen}  -> évaluation de la position via Stockfish

Le FEN est passé en paramètre de chemin. Comme il contient des espaces et des
slashs, le client doit l'encoder (URL-encoding). FastAPI le décode automatiquement.
"""
from fastapi import APIRouter, HTTPException

from app.services import lichess_service, stockfish_service
from app.services.chess_utils import validate_fen

router = APIRouter(tags=["chess"])


@router.get("/moves/{fen:path}")
async def get_moves(fen: str) -> dict:
    """Retourne les coups théoriques jouables depuis la position `fen`."""
    try:
        validate_fen(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        result = await lichess_service.get_theoretical_moves(fen)
    except lichess_service.LichessError as exc:
        # 502 : l'API externe (Lichess) a échoué, ce n'est pas la faute du client.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result["fen"] = fen
    result["is_theoretical"] = bool(result["moves"])
    return result


@router.get("/evaluate/{fen:path}")
def evaluate(fen: str, depth: int = 15) -> dict:
    """Retourne l'évaluation Stockfish de la position `fen`."""
    try:
        validate_fen(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        result = stockfish_service.evaluate_position(fen, depth=depth)
    except stockfish_service.StockfishError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result["fen"] = fen
    result["depth"] = depth
    return result
