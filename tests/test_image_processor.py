import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.image_processor import ImageProcessor, apply_effect_with_mask


class ImageProcessorTest(unittest.TestCase):
    def test_click_stroke_can_be_undone_and_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.png"
            Image.new("RGB", (40, 40), "red").save(source)

            processor = ImageProcessor()
            processor.load_image(source)
            original_bytes = processor.current_image.tobytes()

            processor.begin_stroke()
            processor.stroke_to((20, 20), brush_diameter=20, effect_type="blur", strength=10)
            self.assertTrue(processor.end_stroke())
            self.assertTrue(processor.undo_history)

            self.assertTrue(processor.undo())
            self.assertEqual(processor.current_image.tobytes(), original_bytes)

            processor.begin_stroke()
            processor.stroke_to((20, 20), brush_diameter=20, effect_type="mosaic", strength=8)
            processor.end_stroke()
            self.assertTrue(processor.clear())
            self.assertEqual(processor.current_image.tobytes(), original_bytes)

    def test_save_preserves_size_format_and_uses_numbered_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "photo.jpg"
            Image.new("RGB", (32, 24), "blue").save(source, format="JPEG")
            (Path(tmp) / "photo_fuwamoza.jpg").write_bytes(b"existing")

            processor = ImageProcessor()
            processor.load_image(source)
            processor.begin_stroke()
            processor.stroke_to((8, 8), brush_diameter=12, effect_type="blur", strength=4)
            processor.end_stroke()
            output_path = processor.save()

            self.assertEqual(output_path.name, "photo_fuwamoza_2.jpg")
            with Image.open(output_path) as saved:
                self.assertEqual(saved.size, (32, 24))
                self.assertEqual(saved.format, "JPEG")

    def test_mask_limits_effect_area(self) -> None:
        base = Image.new("RGB", (20, 20), "black")
        for x in range(20):
            for y in range(20):
                base.putpixel((x, y), (x * 10, y * 10, 128))

        mask = Image.new("L", (20, 20), 0)
        for x in range(5, 15):
            for y in range(5, 15):
                mask.putpixel((x, y), 255)

        result = apply_effect_with_mask(base, mask, "mosaic", 5)
        self.assertEqual(result.getpixel((0, 0)), base.getpixel((0, 0)))
        self.assertNotEqual(result.getpixel((10, 10)), base.getpixel((10, 10)))


if __name__ == "__main__":
    unittest.main()
