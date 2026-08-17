"""Service de synthèse en langage naturel via Azure OpenAI.

L'agent rassemble des données (ouverture, coups théoriques, évaluation, contexte)
et ce service les transforme en un conseil pédagogique clair pour un jeune joueur.

Pattern résilient : si la clé Azure est absente ou si l'appel échoue, on renvoie
une synthèse construite à partir d'un template. L'agent reste ainsi toujours
fonctionnel, même sans LLM.
"""
from app.core.config import get_settings

settings = get_settings()

_SYSTEM_PROMPT = (
    "Tu es un entraîneur d'échecs bienveillant qui accompagne de jeunes espoirs "
    "sur les ouvertures. Tu expliques simplement, en français, de manière "
    "encourageante et pédagogique. Réponds en 2 à 4 phrases maximum."
)


def _fallback_synthesis(context: dict) -> str:
    """Synthèse de repli (sans LLM), à partir des données disponibles."""
    opening = context.get("opening_name")
    moves = context.get("moves", [])
    evaluation = context.get("evaluation")

    parts = []
    if opening:
        parts.append(f"Tu joues la {opening}.")
    else:
        parts.append("Cette position sort de la théorie des ouvertures connues.")

    if moves:
        best = ", ".join(m["san"] for m in moves[:3])
        parts.append(f"Les coups les plus joués ici sont : {best}.")
    elif evaluation and evaluation.get("best_move"):
        parts.append(
            f"Aucun coup théorique de référence ; le moteur suggère "
            f"{evaluation['best_move']}."
        )

    if evaluation and evaluation.get("eval_type") == "cp":
        cp = evaluation["value"]
        if cp > 50:
            parts.append("La position est un peu meilleure pour les Blancs.")
        elif cp < -50:
            parts.append("La position est un peu meilleure pour les Noirs.")
        else:
            parts.append("La position est équilibrée.")

    return " ".join(parts)


def synthesize(context: dict) -> dict:
    """Génère une synthèse pédagogique. Retourne {text, source}.

    `source` vaut "llm" (Azure OpenAI) ou "template" (repli).
    """
    if not settings.AZURE_OPENAI_API_KEY:
        return {"text": _fallback_synthesis(context), "source": "template"}

    try:
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
        )

        # Construction d'un prompt clair à partir du contexte rassemblé par l'agent.
        opening = context.get("opening_name") or "position hors théorie"
        moves = context.get("moves", [])
        moves_str = (
            ", ".join(f"{m['san']} ({m['games']} parties)" for m in moves[:5])
            or "aucun coup théorique de référence"
        )
        evaluation = context.get("evaluation") or {}
        eval_str = (
            f"{evaluation.get('value')} ({evaluation.get('eval_type')}), "
            f"meilleur coup moteur {evaluation.get('best_move')}"
            if evaluation
            else "non disponible"
        )
        rag = context.get("rag_results", [])
        rag_str = " ".join(r["text"] for r in rag[:2]) if rag else ""

        user_prompt = (
            f"Ouverture : {opening}\n"
            f"Coups théoriques : {moves_str}\n"
            f"Évaluation moteur : {eval_str}\n"
            f"Contexte : {rag_str}\n\n"
            "Donne un conseil pédagogique au jeune joueur pour cette position."
        )

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.4,
        )
        text = response.choices[0].message.content.strip()
        return {"text": text, "source": "llm"}

    except Exception:
        # Clé invalide, quota, réseau, déploiement inconnu... -> repli.
        return {"text": _fallback_synthesis(context), "source": "template"}
