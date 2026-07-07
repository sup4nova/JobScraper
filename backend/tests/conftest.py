# backend/tests/conftest.py
# Ensures the repo root is on sys.path so `import backend.main` works
# regardless of where pytest is invoked from.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
