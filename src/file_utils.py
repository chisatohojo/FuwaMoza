from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".bmp": "BMP",
    ".webp": "WEBP",
}


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def format_from_path(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported image format: {suffix or '(none)'}. Supported: {supported}")
    return SUPPORTED_EXTENSIONS[suffix]


def next_output_path(source_path: str | Path) -> Path:
    source = Path(source_path)
    base = source.with_name(f"{source.stem}_fuwamoza{source.suffix}")
    if not base.exists():
        return base

    index = 2
    while True:
        candidate = source.with_name(f"{source.stem}_fuwamoza_{index}{source.suffix}")
        if not candidate.exists():
            return candidate
        index += 1
