"""Petit utilitaire de validation de position FEN, factorisé pour les endpoints."""
import chess


def validate_fen(fen: str) -> chess.Board:
    """Valide une chaîne FEN et retourne l'objet Board correspondant.

    Raises:
        ValueError: si le FEN est syntaxiquement ou logiquement invalide.
    """
    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise ValueError(f"FEN invalide : {exc}") from exc

    # chess.Board accepte certains FEN "douteux" ; on renforce un minimum.
    if not board.is_valid():
        raise ValueError("FEN invalide : la position n'est pas légale.")
    return board
