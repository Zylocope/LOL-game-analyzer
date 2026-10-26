"""Production entry point: the Nexus Sight API and the built website on one URL.

Run from the repo root (so the saved model can import `backend.*`):
    uvicorn backend.serve:app --host 0.0.0.0 --port 7860
The Dockerfile copies this file to backend/serve.py. backend/main.py is not modified.
"""
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from backend.main import app

DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parent.parent / "dist")).resolve()

if (DIST / "index.html").is_file():
    # The website takes over "/"; the API keeps every /api/* route.
    app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/"]

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"ok": True}

    @app.get("/{full_path:path}", include_in_schema=False)
    def website(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        target = (DIST / full_path).resolve()
        if full_path and target.is_file() and DIST in target.parents:
            return FileResponse(target)
        return FileResponse(DIST / "index.html")
