import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication

from src.app import MainWindow
from src.version import app_title


def get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class MainWindowUiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = get_app()

    def test_buttons_and_status_follow_image_and_undo_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.png"
            Image.new("RGB", (64, 32), "white").save(source)

            window = MainWindow()
            self.assertEqual(window.windowTitle(), app_title())
            self.assertFalse(window.save_button.isEnabled())
            self.assertFalse(window.undo_button.isEnabled())
            self.assertFalse(window.clear_button.isEnabled())

            window.load_image(str(source), confirm=False)
            self.assertTrue(window.save_button.isEnabled())
            self.assertTrue(window.clear_button.isEnabled())
            self.assertFalse(window.undo_button.isEnabled())
            self.assertEqual(window.statusBar().currentMessage(), "読み込み完了: sample.png / 64x32 / PNG")

            window._start_stroke((20, 16))
            window._finish_stroke()
            self.assertTrue(window.undo_button.isEnabled())
            self.assertIn("編集中: モザイク / 太さ 40px / 強さ 16", window.statusBar().currentMessage())

            window.undo()
            self.assertFalse(window.undo_button.isEnabled())
            self.assertEqual(window.statusBar().currentMessage(), "1つ前の操作を取り消しました")
            window.close()


if __name__ == "__main__":
    unittest.main()
