from pathlib import Path
import sys


def resource_path(relative_path: str) -> Path:
    """Return a resource path that works both in source and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path
