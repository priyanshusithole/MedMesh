import sys
import os
from pathlib import Path

# Add root and backend directories to sys.path
_ROOT = Path(__file__).resolve().parent
_BACKEND = _ROOT / "backend"

for p in [str(_BACKEND), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app
