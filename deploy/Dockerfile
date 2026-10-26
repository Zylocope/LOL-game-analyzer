# Nexus Sight on Hugging Face Spaces (Docker SDK). One container serves the website and the API.

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
# services.py looks for backend/data/ but the folder is backend/Data/ (only matters on Linux)
RUN if [ -d backend/Data ] && [ ! -e backend/data ]; then ln -s Data backend/data; fi
USER user
ENV FRONTEND_DIST=/app/dist PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn", "backend.serve:app", "--host", "0.0.0.0", "--port", "7860"]
