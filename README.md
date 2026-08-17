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

## RAG — indexation des connaissances (étape 3)

Après avoir démarré la stack, il faut indexer les articles d'ouvertures dans
Milvus (une seule fois ; à relancer si les données changent) :

```bash
docker compose exec backend python -m app.scripts.ingest_wikichess
```

Au premier lancement, le modèle d'embedding MiniLM (~80 Mo) se télécharge.
Ensuite, tester la recherche vectorielle :

```
GET http://localhost:8000/api/v1/vector-search?query=Sicilienne&k=3
```

## Interface (étape 5)

Une fois la stack lancée, l'interface est accessible sur **http://localhost:4200**.
Elle affiche un échiquier interactif (`ngx-chess-board`) : joue un coup, et le
panneau de droite se met à jour avec les coups théoriques, l'évaluation
Stockfish, le contexte Wikichess (RAG) et des vidéos explicatives.

Note technique : la mission suggérait `ngx-chessboard` (paquet Angular 8, en fin
de vie et basé sur jQuery). On lui a préféré `ngx-chess-board` (v2.2.3), maintenu
et compatible Angular 17, qui expose nativement le FEN et les événements de coup.
Le front (nginx) proxifie `/api` vers le backend : appels relatifs, pas de CORS.

## Feuille de route- [x] **Étape 1** — Socle projet, Git, Docker Compose, healthcheck FastAPI
- [x] **Étape 2** — Endpoints `moves/{fen}` (Lichess + fallback local) et `evaluate/{fen}` (Stockfish)
- [x] **Étape 3** — RAG Wikichess → embeddings MiniLM → Milvus (`/vector-search`)
- [x] **Étape 4** — Recherche de vidéos YouTube (`videos/{opening}`) + fallback
- [x] **Étape 5** — Interface Angular (ngx-chess-board + panneau : coups, éval, RAG, vidéos)
- [x] **Étape 6** — Agent LangGraph (routage conditionnel) + LLM Azure + MongoDB
- [x] **Étape 7** — Étude MCP d'analyse vidéo (docs/etude_mcp.docx)
