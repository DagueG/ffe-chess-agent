"""Point d'entrée de l'API FastAPI.

Étape 1 : exposer un "Hello World" + un healthcheck.
Les étapes suivantes viendront brancher ici les routeurs moves/evaluate/vector-search/videos.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import chess, health, rag
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="POC d'agent IA pour l'apprentissage des ouvertures aux échecs (FFE).",
)

# CORS ouvert en développement pour laisser le front Angular (localhost:4200) appeler l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des routeurs sous le préfixe /api/v1
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(chess.router, prefix=settings.API_V1_PREFIX)
app.include_router(rag.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root() -> dict:
    return {"message": "FFE Chess Agent API — Hello World", "docs": "/docs"}
