"""Script d'ingestion : Wikichess -> chunks -> embeddings -> Milvus.

À lancer une fois la stack Docker démarrée, depuis le conteneur backend :

    docker compose exec backend python -m app.scripts.ingest_wikichess

Étapes :
  1. lit les articles (openings.json) ;
  2. découpe chaque article en chunks (découpage par phrases, fenêtre ~3 phrases) ;
  3. calcule l'embedding de chaque chunk ;
  4. (re)crée la collection Milvus et insère les chunks.
"""
import json
from pathlib import Path

from app.services import embedding_service, milvus_service

_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "services"
    / "data"
    / "wikichess"
    / "openings.json"
)


def chunk_text(text: str, sentences_per_chunk: int = 3, overlap: int = 1) -> list[str]:
    """Découpe un texte en chunks de quelques phrases, avec léger recouvrement.

    Le recouvrement (overlap) évite de couper une idée en deux entre deux chunks,
    ce qui améliore la qualité de la recherche.
    """
    # Découpage simple en phrases sur les points (suffisant pour ce POC).
    sentences = [s.strip() for s in text.replace("!", ".").split(".") if s.strip()]
    chunks = []
    step = max(1, sentences_per_chunk - overlap)
    for i in range(0, len(sentences), step):
        window = sentences[i : i + sentences_per_chunk]
        if window:
            chunks.append(". ".join(window) + ".")
    return chunks


def run() -> None:
    print(f"Lecture des articles : {_DATA_PATH}")
    with _DATA_PATH.open(encoding="utf-8") as f:
        articles = json.load(f)["articles"]

    # Construction des chunks avec leurs métadonnées.
    records = []
    for article in articles:
        for chunk in chunk_text(article["content"]):
            records.append(
                {
                    "text": chunk,
                    "opening": article["opening_fr"],
                    "source": article["source"],
                }
            )
    print(f"{len(articles)} articles -> {len(records)} chunks")

    # Embeddings (par lot).
    print("Calcul des embeddings (le modèle se télécharge au 1er lancement)...")
    vectors = embedding_service.embed([r["text"] for r in records])
    for record, vector in zip(records, vectors):
        record["vector"] = vector

    # (Re)création de la collection puis insertion.
    print("Préparation de la collection Milvus (recréation)...")
    milvus_service.ensure_collection(recreate=True)
    inserted = milvus_service.insert_chunks(records)
    print(f"OK : {inserted} chunks indexés dans Milvus.")


if __name__ == "__main__":
    run()
