# Version Python figée pour garantir la reproductibilité (point de vigilance étape 1)
FROM python:3.12-slim

# Empêche Python de bufferiser stdout/stderr (logs visibles en direct dans Docker)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

# Installation du moteur d'échecs Stockfish (binaire système, piloté via UCI).
# Le paquet Debian installe l'exécutable dans /usr/games/stockfish (cf. STOCKFISH_PATH).
RUN apt-get update && \
    apt-get install -y --no-install-recommends stockfish && \
    rm -rf /var/lib/apt/lists/*

# Installation des dépendances (copiées seules d'abord pour profiter du cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif
COPY app ./app

EXPOSE 8000

# --reload pratique en développement ; à retirer/remplacer en production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
