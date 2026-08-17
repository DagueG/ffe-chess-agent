"""Agent d'analyse d'ouvertures, orchestré avec LangGraph.

Le graphe enchaîne des noeuds de raisonnement, avec un routage conditionnel :

    validate ─▶ moves ─▶ evaluate ─▶ (enrich ?) ─▶ synthesize ─▶ persist ─▶ END
        │                               │
        └──(FEN invalide)──▶ END        └──(ouverture connue ? sinon on saute enrich)

- validate   : valide le FEN (python-chess).
- moves      : coups théoriques (Lichess + repli local) + identification de l'ouverture.
- evaluate   : évaluation Stockfish.
- enrich     : si une ouverture est identifiée -> contexte RAG (Milvus) + vidéos (YouTube).
- synthesize : synthèse pédagogique en langage naturel (Azure OpenAI + repli).
- persist    : journalisation MongoDB (effet de bord résilient).

Chaque noeud est défensif : l'échec d'un outil externe n'interrompt pas le graphe,
il laisse simplement sa portion de résultat vide.
"""
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from app.services import (
    embedding_service,
    llm_service,
    milvus_service,
    mongo_service,
    stockfish_service,
    youtube_service,
)
from app.services import lichess_service
from app.services.chess_utils import validate_fen


class AgentState(TypedDict, total=False):
    fen: str
    error: Optional[str]
    moves: list
    moves_source: str
    opening: Optional[dict]
    opening_name: Optional[str]
    is_theoretical: bool
    evaluation: Optional[dict]
    rag_results: list
    videos: list
    synthesis: str
    synthesis_source: str


# --------------------------------------------------------------------------- #
# Noeuds
# --------------------------------------------------------------------------- #
def node_validate(state: AgentState) -> dict:
    try:
        validate_fen(state["fen"])
        return {"error": None}
    except ValueError as exc:
        return {"error": str(exc)}


def node_theory(state: AgentState) -> dict:
    try:
        res = lichess_service.get_theoretical_moves_sync(state["fen"])
        opening = res.get("opening")
        return {
            "moves": res.get("moves", []),
            "moves_source": res.get("source", ""),
            "opening": opening,
            "opening_name": opening["name"] if opening else None,
            "is_theoretical": bool(res.get("moves")),
        }
    except lichess_service.LichessError:
        return {"moves": [], "is_theoretical": False, "opening": None}


def node_evaluate(state: AgentState) -> dict:
    try:
        return {"evaluation": stockfish_service.evaluate_position(state["fen"])}
    except stockfish_service.StockfishError:
        return {"evaluation": None}


def node_enrich(state: AgentState) -> dict:
    """Contexte RAG + vidéos, ciblés sur le nom de l'ouverture identifiée."""
    opening_name = state.get("opening_name") or ""
    rag_results, videos = [], []

    try:
        vector = embedding_service.embed_one(opening_name)
        rag_results = milvus_service.search(vector, k=3)
    except Exception:
        rag_results = []

    try:
        videos = youtube_service.search_videos(opening_name).get("videos", [])
    except Exception:
        videos = []

    return {"rag_results": rag_results, "videos": videos}


def node_synthesize(state: AgentState) -> dict:
    result = llm_service.synthesize(
        {
            "opening_name": state.get("opening_name"),
            "moves": state.get("moves", []),
            "evaluation": state.get("evaluation"),
            "rag_results": state.get("rag_results", []),
        }
    )
    return {"synthesis": result["text"], "synthesis_source": result["source"]}


def node_persist(state: AgentState) -> dict:
    mongo_service.log_analysis(
        {
            "fen": state.get("fen"),
            "opening_name": state.get("opening_name"),
            "is_theoretical": state.get("is_theoretical"),
            "evaluation": state.get("evaluation"),
            "synthesis": state.get("synthesis"),
        }
    )
    return {}


# --------------------------------------------------------------------------- #
# Routage conditionnel
# --------------------------------------------------------------------------- #
def route_after_validate(state: AgentState) -> str:
    return "error" if state.get("error") else "ok"


def route_after_evaluate(state: AgentState) -> str:
    # On enrichit (RAG + vidéos) seulement si une ouverture a été identifiée.
    return "enrich" if state.get("opening_name") else "skip"


# --------------------------------------------------------------------------- #
# Construction du graphe (compilé une seule fois)
# --------------------------------------------------------------------------- #
def _build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("validate", node_validate)
    builder.add_node("theory", node_theory)
    builder.add_node("evaluate", node_evaluate)
    builder.add_node("enrich", node_enrich)
    builder.add_node("synthesize", node_synthesize)
    builder.add_node("persist", node_persist)

    builder.set_entry_point("validate")
    builder.add_conditional_edges(
        "validate", route_after_validate, {"ok": "theory", "error": END}
    )
    builder.add_edge("theory", "evaluate")
    builder.add_conditional_edges(
        "evaluate", route_after_evaluate, {"enrich": "enrich", "skip": "synthesize"}
    )
    builder.add_edge("enrich", "synthesize")
    builder.add_edge("synthesize", "persist")
    builder.add_edge("persist", END)
    return builder.compile()


_graph = _build_graph()


def analyze(fen: str) -> dict:
    """Point d'entrée : exécute le graphe pour une position et renvoie l'état final."""
    final_state = _graph.invoke({"fen": fen})
    return final_state
