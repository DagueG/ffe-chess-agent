# POC — Agent IA pour l'apprentissage des ouvertures aux échecs (FFE)

Proof of Concept d'un agent intelligent accompagnant les jeunes espoirs de la
Fédération Française des Échecs dans l'apprentissage des ouvertures.

L'agent, pour une position donnée (au format **FEN**), propose :
- les meilleurs coups théoriques (API **Lichess**) ;
- une évaluation de la position par **Stockfish** si la partie sort de la théorie ;
- du contexte enrichi via un **RAG** (données Wikichess indexées dans **Milvus**) ;
- des **vidéos YouTube** explicatives pertinentes.

Le tout est orchestré par un agent **LangGraph**, exposé par une API **FastAPI**,
avec une interface **Angular** (échiquier interactif `ngx-chessboard`).

## Stack technique

| Couche          | Technologie                          |
|-----------------|--------------------------------------|
| Frontend        | Angular + ngx-chessboard             |
| API             | FastAPI                              |
| Orchestration   | LangGraph                            |
| Base vectorielle| Milvus                               |
| Base documents  | MongoDB                              |
| Moteur d'échecs | Stockfish                            |
| Conteneurisation| Docker Compose                       |

## Démarrage rapide

Prérequis : **Git**, **Docker**, **Docker Compose**.

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd ffe-chess-agent

# 2. Créer le fichier d'environnement
cp .env.example .env

# 3. Lancer la stack
docker compose up --build
```

### Vérifier que l'API répond

```bash
curl http://localhost:8000/api/v1/healthcheck
# -> {"status":"ok","service":"FFE Chess Agent API","environment":"development"}
```

Documentation interactive Swagger : http://localhost:8000/docs

## Structure du projet

```
ffe-chess-agent/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── main.py       # point d'entrée
│   │   ├── core/         # configuration
│   │   ├── api/v1/routes # endpoints
│   │   └── services/     # logique métier (Lichess, Stockfish, RAG...)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # application Angular (étape 5)
├── docker-compose.yml    # orchestration des services
└── .env.example
```

## Feuille de route

- [x] **Étape 1** — Socle projet, Git, Docker Compose, healthcheck FastAPI
- [ ] **Étape 2** — Endpoints `moves/{fen}` (Lichess) et `evaluate/{fen}` (Stockfish)
- [ ] **Étape 3** — RAG Wikichess → embeddings → Milvus (`/vector-search`)
- [ ] **Étape 4** — Recherche de vidéos YouTube (`videos/{opening}`)
- [ ] **Étape 5** — Interface Angular (échiquier + panneau de recommandations)
- [ ] **Étape 6** — Conteneurisation complète + démonstration
- [ ] **Étape 7** — Étude MCP d'analyse vidéo (note + archi + faisabilité)
