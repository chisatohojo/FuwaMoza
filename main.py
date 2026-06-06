import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.app import MainWindow
from src.resource_utils import resource_path


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("FuwaMoza")
    app.setOrganizationName("FuwaMoza")

    icon_path = resource_path("assets/icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
