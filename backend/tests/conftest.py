# tests/conftest.py
"""
This adds your backend root folder to sys.path so your tests can
import core.*, api.*, models.* etc. cleanly without ModuleNotFoundError.
"""

import sys
from pathlib import Path

# Resolve backend/ folder and add it to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))