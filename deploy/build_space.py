"""Pack Nexus Sight into a folder ready to upload to a Hugging Face Space.

Usage (from the repo root):
    python deploy/build_space.py                 # writes ../nexus-sight-space
    python deploy/build_space.py <output-folder>

Re-run it whenever you retrain the model; it rebuilds the folder from scratch.
Never copies .env files, datasets, old models, tests or node_modules.
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO.parent / "nexus-sight-space"

# Top-level items needed to build the website and run the API
INCLUDE = ["requirements.txt", "backend", "frontend"]
# Never shipped (secrets, training data, old models, caches, tests)
SKIP_NAMES = {".env", "__pycache__", "tests", "node_modules", "dist", ".git", ".ipynb_checkpoints"}
SKIP_SUFFIXES = {".csv", ".backup", ".ipynb", ".pyc", ".log"}
SKIP_FILES = {"match_predictor.pkl", "match_predictor_v2.pkl", "match_predictor_v3.pkl",
              "match_predictor_v4.pkl", "model_v5.pkl"}


def skip(p: Path) -> bool:
    extra_db = p.suffix == ".db" and p.name != "nexus_sight.db"   # backups like nexus_sight.v6-original.db
    return (p.name in SKIP_NAMES or p.name.startswith(".env") or p.suffix in SKIP_SUFFIXES
            or p.name in SKIP_FILES or extra_db or p.name.endswith(("-journal", "-wal", "-shm")))


def copy(src: Path, dst: Path):
    if skip(src):
        return
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            copy(child, dst / child.name)
    else:
        shutil.copy2(src, dst)


def main():
    if OUT == REPO or REPO in OUT.parents:
        sys.exit("Choose an output folder outside the repo.")
    for name in ("backend/model_v6.pkl", "backend/nexus_sight.db"):
        if not (REPO / name).exists():
            sys.exit(f"Missing {name}: train the model / build the database first.")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name in INCLUDE:
        src = REPO / name
        if src.exists():
            copy(src, OUT / name)
    (OUT / "deploy").mkdir()
    shutil.copy2(REPO / "deploy/serve.py", OUT / "deploy/serve.py")
    shutil.copy2(REPO / "deploy/Dockerfile", OUT / "Dockerfile")
    shutil.copy2(REPO / "deploy/space_README.md", OUT / "README.md")
    (OUT / ".dockerignore").write_text("node_modules\ndist\n.env*\n**/__pycache__\n", encoding="utf-8")
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"Space folder ready: {OUT}  ({size:.0f} MB)")


if __name__ == "__main__":
    main()
