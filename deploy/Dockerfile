# Nexus Sight: one container serves the website and the API.
# Works on Render (free web service, builds from the GitHub repo) and any Docker host.
# Build context = repo root:  docker build -f deploy/Dockerfile .

# 1) Build the React website. VITE_API_URL="/" makes it call the API on the same domain.
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=/
RUN npm run build

# 2) Python runtime
FROM python:3.12-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY --chown=user requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=user backend/ ./backend/
COPY --chown=user frontend/data/ ./frontend/data/
COPY --chown=user deploy/serve.py ./backend/serve.py
COPY --from=web --chown=user /web/dist ./dist

# The database and model are not in Git. If they are not in the build context, download them from the
# GitHub release named below (attach nexus_sight.db and model_v6.pkl to it).
ARG DATA_URL=https://github.com/Zylocope/LOL-game-analyzer/releases/download/data-2026-10-26
RUN python -c "import os, urllib.request as u; \
[(u.urlretrieve(os.environ.get('DATA_URL', '$DATA_URL') + '/' + f, 'backend/' + f), print('downloaded', f)) \
 for f in ('nexus_sight.db', 'model_v6.pkl') if not os.path.exists('backend/' + f)]" \
 && chown user backend/nexus_sight.db backend/model_v6.pkl

# services.py looks for backend/data/ but the folder is backend/Data/ (only matters on Linux)
RUN if [ -d backend/Data ] && [ ! -e backend/data ]; then ln -s Data backend/data; fi
USER user
ENV FRONTEND_DIST=/app/dist PYTHONUNBUFFERED=1 PORT=7860
EXPOSE 7860
# Render and most hosts pass the port in $PORT.
CMD ["sh", "-c", "uvicorn backend.serve:app --host 0.0.0.0 --port ${PORT}"]
