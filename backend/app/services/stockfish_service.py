"""Service d'évaluation via le moteur Stockfish.

On pilote le binaire Stockfish (protocole UCI) à travers python-chess
(module chess.engine). Le binaire est installé dans l'image Docker et son
chemin est fourni par la configuration (STOCKFISH_PATH).
"""
import chess
import chess.engine

from app.core.config import get_settings

settings = get_settings()


class StockfishError(Exception):
    """Erreur levée quand le moteur Stockfish est indisponible ou échoue."""


def evaluate_position(fen: str, depth: int = 15) -> dict:
    """Évalue une position FEN avec Stockfish.

    Args:
        fen: position au format FEN (supposée déjà validée en amont).
        depth: profondeur de recherche du moteur.

    Returns:
        dict avec :
          - best_move (uci) : meilleur coup selon le moteur ;
          - eval_type : "cp" (centipawns) ou "mate" ;
          - value : score en centipawns du point de vue du trait,
                    ou nombre de coups avant mat si eval_type == "mate".

    Raises:
        StockfishError: si le binaire est introuvable ou plante.
    """
    board = chess.Board(fen)
    try:
        with chess.engine.SimpleEngine.popen_uci(settings.STOCKFISH_PATH) as engine:
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
    except FileNotFoundError as exc:
        raise StockfishError(
            f"Binaire Stockfish introuvable à '{settings.STOCKFISH_PATH}'."
        ) from exc
    except chess.engine.EngineError as exc:
        raise StockfishError(f"Erreur du moteur Stockfish : {exc}") from exc

    score = info["score"].pov(board.turn)  # score du point de vue du joueur au trait
    pv = info.get("pv", [])
    best_move = pv[0].uci() if pv else None

    if score.is_mate():
        return {"best_move": best_move, "eval_type": "mate", "value": score.mate()}
    return {"best_move": best_move, "eval_type": "cp", "value": score.score()}
