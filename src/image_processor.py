from __future__ import annotations

from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFilter, UnidentifiedImageError

from .file_utils import format_from_path, is_supported_image, next_output_path


EffectType = Literal["mosaic", "blur"]


class ImageLoadError(Exception):
    """Raised when an image cannot be loaded into FuwaMoza."""


class ImageProcessor:
    def __init__(self, history_limit: int = 20) -> None:
        self.history_limit = history_limit
        self.source_path: Path | None = None
        self.source_format: str | None = None
        self.original_image: Image.Image | None = None
        self.current_image: Image.Image | None = None
        self.undo_history: list[Image.Image] = []

        self._stroke_base: Image.Image | None = None
        self._stroke_mask: Image.Image | None = None
        self._last_point: tuple[int, int] | None = None
        self._stroke_changed = False

    @property
    def has_image(self) -> bool:
        return self.current_image is not None

    @property
    def has_active_stroke(self) -> bool:
        return self._stroke_base is not None

    def load_image(self, path: str | Path) -> None:
        image_path = Path(path)
        if not is_supported_image(image_path):
            raise ImageLoadError("対応していない画像形式です。PNG, JPG, JPEG, BMP, WEBP を選択してください。")

        try:
            with Image.open(image_path) as image:
                image.load()
                normalized = self._normalize_image(image)
        except (OSError, UnidentifiedImageError) as exc:
            raise ImageLoadError("画像を読み込めませんでした。ファイルが破損していないか確認してください。") from exc

        self.source_path = image_path
        self.source_format = format_from_path(image_path)
        self.original_image = normalized.copy()
        self.current_image = normalized.copy()
        self.undo_history.clear()
        self._clear_stroke_state()

    def begin_stroke(self) -> None:
        if self.current_image is None:
            raise RuntimeError("No image loaded")

        self._stroke_base = self.current_image.copy()
        self._stroke_mask = Image.new("L", self.current_image.size, 0)
        self._last_point = None
        self._stroke_changed = False

    def stroke_to(self, point: tuple[int, int], brush_diameter: int, effect_type: EffectType, strength: int) -> None:
        if self._stroke_base is None or self._stroke_mask is None:
            self.begin_stroke()

        assert self._stroke_base is not None
        assert self._stroke_mask is not None

        point = self._clamp_point(point, self._stroke_mask.size)
        self._draw_brush_segment(self._stroke_mask, self._last_point, point, brush_diameter)
        self._last_point = point
        self._stroke_changed = True
        self.current_image = apply_effect_with_mask(self._stroke_base, self._stroke_mask, effect_type, strength)

    def end_stroke(self) -> bool:
        if self._stroke_base is None:
            return False

        changed = self._stroke_changed
        if changed:
            self._push_undo(self._stroke_base)
        self._clear_stroke_state()
        return changed

    def cancel_stroke(self) -> bool:
        if self._stroke_base is None:
            return False

        self.current_image = self._stroke_base
        self._clear_stroke_state()
        return True

    def undo(self) -> bool:
        if self.has_active_stroke:
            return self.cancel_stroke()

        if not self.undo_history:
            return False

        self.current_image = self.undo_history.pop()
        return True

    def clear(self) -> bool:
        if self.original_image is None:
            return False

        self.current_image = self.original_image.copy()
        self.undo_history.clear()
        self._clear_stroke_state()
        return True

    def save(self) -> Path:
        if self.current_image is None or self.source_path is None or self.source_format is None:
            raise RuntimeError("No image loaded")

        output_path = next_output_path(self.source_path)
        image = self._prepare_for_save(self.current_image, self.source_format)
        save_kwargs: dict[str, object] = {}
        if self.source_format == "JPEG":
            save_kwargs.update({"quality": 95, "subsampling": 0})
        elif self.source_format == "WEBP":
            save_kwargs.update({"quality": 95})

        image.save(output_path, format=self.source_format, **save_kwargs)
        return output_path

    def _push_undo(self, image: Image.Image) -> None:
        self.undo_history.append(image.copy())
        if len(self.undo_history) > self.history_limit:
            self.undo_history = self.undo_history[-self.history_limit :]

    @staticmethod
    def _normalize_image(image: Image.Image) -> Image.Image:
        has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
        if has_alpha:
            return image.convert("RGBA")
        return image.convert("RGB")

    @staticmethod
    def _prepare_for_save(image: Image.Image, image_format: str) -> Image.Image:
        if image_format in {"JPEG", "BMP"} and image.mode != "RGB":
            return image.convert("RGB")
        return image

    @staticmethod
    def _clamp_point(point: tuple[int, int], size: tuple[int, int]) -> tuple[int, int]:
        width, height = size
        x = min(max(int(round(point[0])), 0), width - 1)
        y = min(max(int(round(point[1])), 0), height - 1)
        return x, y

    @staticmethod
    def _draw_brush_segment(
        mask: Image.Image,
        previous: tuple[int, int] | None,
        current: tuple[int, int],
        brush_diameter: int,
    ) -> None:
        diameter = max(1, int(round(brush_diameter)))
        radius = diameter / 2
        draw = ImageDraw.Draw(mask)

        def ellipse_bounds(point: tuple[int, int]) -> tuple[float, float, float, float]:
            x, y = point
            return (x - radius, y - radius, x + radius, y + radius)

        if previous is not None:
            draw.line([previous, current], fill=255, width=diameter)
            draw.ellipse(ellipse_bounds(previous), fill=255)
        draw.ellipse(ellipse_bounds(current), fill=255)

    def _clear_stroke_state(self) -> None:
        self._stroke_base = None
        self._stroke_mask = None
        self._last_point = None
        self._stroke_changed = False


def apply_effect_with_mask(
    base_image: Image.Image,
    mask: Image.Image,
    effect_type: EffectType,
    strength: int,
) -> Image.Image:
    bbox = mask.getbbox()
    if bbox is None:
        return base_image.copy()

    base_crop = base_image.crop(bbox)
    mask_crop = mask.crop(bbox)
    if effect_type == "mosaic":
        effect_crop = _mosaic(base_crop, strength)
    elif effect_type == "blur":
        radius = max(1, int(round(strength)))
        effect_crop = base_crop.filter(ImageFilter.GaussianBlur(radius=radius))
    else:
        raise ValueError(f"Unknown effect type: {effect_type}")

    result = base_image.copy()
    composed = Image.composite(effect_crop, base_crop, mask_crop)
    result.paste(composed, bbox)
    return result


def _mosaic(image: Image.Image, block_size: int) -> Image.Image:
    block = max(1, int(round(block_size)))
    if block <= 1:
        return image.copy()

    width, height = image.size
    small_size = (max(1, (width + block - 1) // block), max(1, (height + block - 1) // block))
    resampling = Image.Resampling
    small = image.resize(small_size, resampling.BOX)
    return small.resize((width, height), resampling.NEAREST)
