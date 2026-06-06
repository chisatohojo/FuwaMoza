from pathlib import Path
import sys


def resource_path(relative_path: str) -> Path:
    """Return a resource path that works both in source and PyInstaller builds."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


def app_icon_path() -> Path | None:
    """Prefer an ICO app icon, then fall back to PNG if available."""
    for relative_path in ("assets/icon.ico", "assets/icon.png"):
        icon_path = resource_path(relative_path)
        if icon_path.exists():
            return icon_path
    return None
