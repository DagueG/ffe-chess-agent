# =============================================================================
#  Frontend Angular — build multi-stage
#  Étape 1 : compilation de l'app avec Node.
#  Étape 2 : service des fichiers statiques via nginx (léger, rapide).
# =============================================================================

# ---- Étape build ----
FROM node:20-alpine AS build
WORKDIR /app

# Install des dépendances (copiées seules d'abord pour le cache Docker).
# .npmrc (legacy-peer-deps) permet d'accepter le peer dep Angular 13 de
# ngx-chess-board 2.2.3 dans une app Angular 17 (compatibilité Ivy assurée).
COPY package.json package-lock.json .npmrc ./
RUN npm ci

# Copie du code et build de production.
COPY . .
RUN npm run build -- --configuration production

# ---- Étape service ----
FROM nginx:1.27-alpine
# Fichiers compilés d'Angular 17 (application builder -> dist/frontend/browser).
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
