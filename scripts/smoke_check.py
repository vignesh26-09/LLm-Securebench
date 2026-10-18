"""Run a dependency-free application smoke check from the repository root."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.api.app import ApiApplication
if __name__ == "__main__":
    print(ApiApplication().health())
