from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from src.version import APP_NAME, APP_VERSION


ROOT = Path(__file__).resolve().parent
DIST_EXE = ROOT / "dist" / f"{APP_NAME}.exe"
RELEASE_ROOT = ROOT / "release"
PACKAGE_NAME = f"{APP_NAME}_v{APP_VERSION}"
PACKAGE_DIR = RELEASE_ROOT / PACKAGE_NAME
ZIP_PATH = RELEASE_ROOT / f"{PACKAGE_NAME}.zip"
CHECKSUMS_PATH = RELEASE_ROOT / "checksums.txt"

PACKAGE_FILES = [
    "README.txt",
    "CHANGELOG.txt",
    "LICENSE.txt",
    "BUILD.txt",
]


def main() -> int:
    if not DIST_EXE.exists():
        raise FileNotFoundError(
            f"{DIST_EXE} が見つかりません。先に PyInstaller で exe を作成してください。"
        )

    RELEASE_ROOT.mkdir(exist_ok=True)
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    PACKAGE_DIR.mkdir(parents=True)
    shutil.copy2(DIST_EXE, PACKAGE_DIR / DIST_EXE.name)

    for file_name in PACKAGE_FILES:
        source = ROOT / file_name
        if not source.exists():
            raise FileNotFoundError(f"{source} が見つかりません。")
        shutil.copy2(source, PACKAGE_DIR / file_name)

    sample_dir = ROOT / "sample"
    if sample_dir.exists():
        shutil.copytree(sample_dir, PACKAGE_DIR / "sample")

    create_zip(PACKAGE_DIR, ZIP_PATH)
    digest = sha256_file(ZIP_PATH)
    CHECKSUMS_PATH.write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="utf-8")

    print(f"Created: {ZIP_PATH}")
    print(f"SHA256:  {digest}")
    print(f"Wrote:   {CHECKSUMS_PATH}")
    return 0


def create_zip(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(RELEASE_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
