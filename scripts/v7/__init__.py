from pathlib import Path
import sys
# Optional local isolated installation; normal installs also work.
_dependencies = Path(__file__).resolve().parent/'data/deps'
if _dependencies.exists():
    sys.path.insert(0, str(_dependencies))
