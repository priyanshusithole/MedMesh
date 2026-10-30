import os
import sys
from pathlib import Path

# Add root and backend directories to sys.path so modules and datasets resolve
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

for path in [str(BACKEND_DIR), str(BASE_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.main import app
