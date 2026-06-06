import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

from src.image_canvas import ImageCanvas


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class ImageCanvasTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = get_app()

    def test_view_to_image_coordinates_respect_letterbox_padding(self) -> None:
        canvas = ImageCanvas()
        canvas.resize(500, 400)
        image = QImage(100, 50, QImage.Format.Format_RGBA8888)
        image.fill(QColor("white"))
        canvas.set_image(image)

        display_rect = canvas._calculate_display_rect()
        center = QPointF(
            display_rect.left() + display_rect.width() / 2,
            display_rect.top() + display_rect.height() / 2,
        )
        outside_padding = QPointF(display_rect.left() - 2, display_rect.center().y())

        self.assertEqual(canvas.image_point_from_view(center), (50, 25))
        self.assertIsNone(canvas.image_point_from_view(outside_padding))

    def test_brush_preview_uses_image_scale(self) -> None:
        canvas = ImageCanvas()
        canvas.resize(500, 400)
        image = QImage(100, 50, QImage.Format.Format_RGBA8888)
        image.fill(QColor("white"))
        canvas.set_image(image)
        canvas.set_brush_diameter(40)

        display_rect = canvas._calculate_display_rect()
        scale = display_rect.width() / image.width()
        expected_scale = (canvas.width() - 48) / image.width()

        self.assertAlmostEqual(scale, expected_scale)
        self.assertGreater(40 * scale, 0)


if __name__ == "__main__":
    unittest.main()
