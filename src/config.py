import os
from pathlib import Path

HARNESS_HOME = Path(os.environ.get("XX_HARNESS_HOME", Path.home() / ".xx-harness"))
DB_PATH = HARNESS_HOME / "harness.db"
WORKSPACE_ROOT = HARNESS_HOME / "workspace"
WEB_PORT = int(os.environ.get("XX_HARNESS_PORT", "8720"))


def ensure_dirs() -> None:
    HARNESS_HOME.mkdir(parents=True, exist_ok=True)
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
