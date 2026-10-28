"""Put this directory on sys.path so the guards can share helper modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
