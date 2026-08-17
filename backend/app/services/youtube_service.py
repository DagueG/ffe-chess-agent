"""Service de recherche de vidéos YouTube (API YouTube Data v3).

Pour une ouverture donnée, on construit une requête pédagogique (nom de
l'ouverture + mots-clés "chess opening tutorial") et on interroge l'API.

Pattern résilient : si la clé API est absente, invalide, ou si le quota est
épuisé, le service renvoie un résultat de repli — un lien de recherche YouTube
préconstruit — plutôt que d'échouer. La démonstration reste ainsi toujours
fonctionnelle.

Quota : l'API YouTube Data v3 offre 10 000 unités/jour ; une recherche coûte
100 unités (~100 recherches/jour).
"""
import urllib.parse

from app.core.config import get_settings

settings = get_settings()


class YouTubeError(Exception):
    """Erreur non récupérable de la recherche YouTube."""


def _search_link_fallback(opening: str) -> dict:
    """Construit un résultat de repli : un lien de recherche YouTube."""
    query = f"{opening} chess opening tutorial"
    url = "https://www.youtube.com/results?" + urllib.parse.urlencode(
        {"search_query": query}
    )
    return {
        "source": "fallback",
        "query": query,
        "videos": [
            {
                "video_id": None,
                "title": f"Rechercher « {opening} » sur YouTube",
                "channel": None,
                "url": url,
                "thumbnail": None,
                "embed_url": None,
            }
        ],
    }


def search_videos(opening: str, max_results: int = 5) -> dict:
    """Recherche des vidéos explicatives pour une ouverture.

    Returns:
        dict : {source, query, videos[]}. `source` vaut "youtube" (API) ou
        "fallback" (lien de recherche). Chaque vidéo expose url + embed_url
        (pour un lecteur intégré côté front).
    """
    query = f"{opening} chess opening tutorial"

    # Pas de clé configurée -> repli direct, sans tenter l'appel.
    if not settings.YOUTUBE_API_KEY:
        return _search_link_fallback(opening)

    try:
        # Import différé : la lib n'est nécessaire que si une clé est présente.
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        youtube = build(
            "youtube", "v3", developerKey=settings.YOUTUBE_API_KEY, cache_discovery=False
        )
        try:
            response = (
                youtube.search()
                .list(
                    q=query,
                    part="snippet",
                    type="video",
                    maxResults=max_results,
                    relevanceLanguage="fr",
                    videoEmbeddable="true",  # ne garder que les vidéos intégrables
                    safeSearch="strict",
                )
                .execute()
            )
        except HttpError:
            # Quota épuisé (403), clé invalide, etc. -> repli.
            return _search_link_fallback(opening)

    except ImportError:
        # Lib absente -> repli.
        return _search_link_fallback(opening)

    videos = []
    for item in response.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        snippet = item.get("snippet", {})
        thumbs = snippet.get("thumbnails", {})
        videos.append(
            {
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel": snippet.get("channelTitle"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": (thumbs.get("high") or thumbs.get("default", {})).get("url"),
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
            }
        )

    # Aucun résultat exploitable -> repli plutôt qu'une liste vide.
    if not videos:
        return _search_link_fallback(opening)

    return {"source": "youtube", "query": query, "videos": videos}
