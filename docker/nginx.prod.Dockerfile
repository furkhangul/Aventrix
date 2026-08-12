# Production image: builds the frontend into a static bundle and serves it
# directly from nginx, alongside proxying /api, /t, /uploads to the backend.
# Unlike the dev topology (docker/frontend.Dockerfile running Vite's dev
# server as its own container), there is no separate frontend container in
# production — see docs/DEPLOY_VPS.md.
#
# Build context is the repo root (not frontend/), since this stage also
# needs nginx/nginx.prod.conf. See docker-compose.prod.yml.

FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/nginx.prod.conf /etc/nginx/nginx.conf
