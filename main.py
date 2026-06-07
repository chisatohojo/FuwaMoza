import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.app import MainWindow
from src.resource_utils import app_icon_path
from src.version import APP_NAME, APP_VERSION


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("FuwaMoza")

    icon_path = app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
