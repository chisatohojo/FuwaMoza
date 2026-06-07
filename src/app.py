from __future__ import annotations

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon, QImage, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSlider,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .image_canvas import ImageCanvas
from .image_processor import ImageLoadError, ImageProcessor
from .resource_utils import app_icon_path
from .version import APP_DISPLAY_NAME, APP_VERSION, app_title


EFFECT_NAMES = {
    "mosaic": "モザイク",
    "blur": "ぼかし",
}
EFFECT_DESCRIPTIONS = {
    "mosaic": "選択部分を粗いドット状に隠します",
    "blur": "選択部分をふわっとぼかします",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.processor = ImageProcessor()
        self.dirty = False

        self.setWindowTitle(app_title())
        self.resize(1040, 720)
        self._set_icon()

        self.canvas = ImageCanvas()
        self.canvas.file_dropped.connect(self.load_image)
        self.canvas.stroke_started.connect(self._start_stroke)
        self.canvas.stroke_moved.connect(self._continue_stroke)
        self.canvas.stroke_finished.connect(self._finish_stroke)

        self.effect_combo = QComboBox()
        self.effect_combo.addItem("モザイク", "mosaic")
        self.effect_combo.addItem("ぼかし", "blur")
        self.effect_description_label = QLabel()
        self.effect_description_label.setObjectName("EffectDescription")
        self.effect_description_label.setMinimumWidth(0)
        self.effect_description_label.setMaximumWidth(280)
        self.effect_description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.brush_slider, self.brush_value_label = self._make_slider(5, 200, 40, "px")
        self.strength_slider, self.strength_value_label = self._make_slider(1, 50, 16, "")
        self.brush_slider.valueChanged.connect(self.canvas.set_brush_diameter)
        self.brush_slider.valueChanged.connect(self._show_current_tool_status)
        self.strength_slider.valueChanged.connect(self._show_current_tool_status)
        self.effect_combo.currentIndexChanged.connect(self._sync_effect_description)
        self.canvas.set_brush_diameter(self.brush_slider.value())

        self.file_label = QLabel("未読み込み")
        self.file_label.setObjectName("FileLabel")
        self.file_label.setMinimumWidth(80)
        self.file_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.open_button = self._make_tool_button(
            "開く",
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "画像を開く",
        )
        self.save_button = self._make_tool_button(
            "保存",
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "加工済み画像を保存",
        )
        self.undo_button = self._make_tool_button(
            "Undo",
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack),
            "直前の操作を取り消す",
        )
        self.clear_button = self._make_tool_button(
            "クリア",
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton),
            "読み込み直後に戻す",
        )
        self.about_button = self._make_tool_button(
            "情報",
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
            "このアプリについて",
        )

        self.open_button.clicked.connect(self.open_image_dialog)
        self.save_button.clicked.connect(self.save_image)
        self.undo_button.clicked.connect(self.undo)
        self.clear_button.clicked.connect(self.clear)
        self.about_button.clicked.connect(self.show_about_dialog)

        self._build_ui()
        self._setup_shortcuts()
        self._apply_style()
        self._sync_effect_description(update_status=False)
        self._update_actions()
        self.statusBar().showMessage("準備完了")

    def open_image_dialog(self) -> None:
        if not self._confirm_before_replacing_image():
            return

        filter_text = "画像ファイル (*.png *.jpg *.jpeg *.bmp *.webp)"
        path, _ = QFileDialog.getOpenFileName(self, "画像を開く", "", filter_text)
        if path:
            self.load_image(path, confirm=False)

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            f"{APP_DISPLAY_NAME} について",
            "\n".join(
                [
                    f"アプリ名: {APP_DISPLAY_NAME}",
                    f"バージョン: v{APP_VERSION}",
                    "",
                    "概要: 画像の一部にモザイクやぼかしを追加できる軽量ツール",
                    "出力仕様: 元画像と同じサイズ・同じ形式で保存",
                    "注意: 元画像は上書きせず、_fuwamoza 付きで保存します",
                ]
            ),
        )

    def load_image(self, path: str, confirm: bool = True) -> None:
        if confirm and not self._confirm_before_replacing_image():
            return

        try:
            self.processor.load_image(path)
        except ImageLoadError as exc:
            message = str(exc)
            self.statusBar().showMessage(f"エラー: {message}")
            QMessageBox.warning(self, "読み込みエラー", message)
            return
        except Exception as exc:  # pragma: no cover - defensive UI guard
            message = f"予期しないエラーが発生しました。\n{exc}"
            self.statusBar().showMessage(f"エラー: {exc}")
            QMessageBox.critical(self, "読み込みエラー", message)
            return

        self.dirty = False
        self._refresh_canvas()
        self._update_actions()
        self.statusBar().showMessage(self._image_status_text("読み込み完了"))

    def save_image(self) -> bool:
        if not self.processor.has_image:
            message = "画像が読み込まれていません。"
            self.statusBar().showMessage(f"エラー: {message}")
            QMessageBox.information(self, "保存", message)
            return False

        try:
            output_path = self.processor.save()
        except Exception as exc:  # pragma: no cover - filesystem dependent
            message = f"保存に失敗しました。\n{exc}"
            self.statusBar().showMessage(f"エラー: {exc}")
            QMessageBox.critical(self, "保存エラー", message)
            return False

        self.dirty = False
        self._update_actions()
        self.statusBar().showMessage(f"保存しました: {output_path.name}")
        QMessageBox.information(self, "保存完了", f"保存しました。\n{output_path}")
        return True

    def undo(self) -> None:
        was_active_stroke = self.processor.has_active_stroke
        if self.processor.undo():
            if not was_active_stroke:
                self.dirty = bool(self.processor.undo_history)
            self._refresh_canvas()
            self._update_actions()
            if was_active_stroke:
                self.canvas.cancel_stroke_preview()
                self.statusBar().showMessage("ドラッグ操作をキャンセルしました")
            else:
                self.statusBar().showMessage("1つ前の操作を取り消しました")

    def clear(self) -> None:
        if self.dirty and not self._confirm_continue_without_saving():
            self.statusBar().showMessage("クリアをキャンセルしました")
            return

        if self.processor.clear():
            self.dirty = False
            self._refresh_canvas()
            self._update_actions()
            self.statusBar().showMessage("編集内容をクリアしました")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._confirm_before_replacing_image():
            event.accept()
        else:
            event.ignore()

    def _start_stroke(self, point: tuple[int, int]) -> None:
        if not self.processor.has_image:
            return

        self.processor.begin_stroke()
        self._apply_stroke_point(point)

    def _continue_stroke(self, point: tuple[int, int]) -> None:
        if self.processor.has_active_stroke:
            self._apply_stroke_point(point)

    def _finish_stroke(self) -> None:
        if self.processor.end_stroke():
            self.dirty = True
            self._update_actions()
            self._show_current_tool_status()

    def _apply_stroke_point(self, point: tuple[int, int]) -> None:
        effect_type = self.effect_combo.currentData()
        self.processor.stroke_to(point, self.brush_slider.value(), effect_type, self.strength_slider.value())
        self._refresh_canvas()

    def _refresh_canvas(self) -> None:
        image = self.processor.current_image
        self.canvas.set_image(pil_to_qimage(image) if image is not None else None)
        if self.processor.source_path:
            self.file_label.setText(self.processor.source_path.name)
        else:
            self.file_label.setText("未読み込み")

    def _confirm_before_replacing_image(self) -> bool:
        if not self.dirty:
            return True

        return self._confirm_continue_without_saving()

    def _confirm_continue_without_saving(self) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("未保存の編集")
        box.setText("現在の編集内容は保存されていません。続行しますか？")
        yes_button = box.addButton("はい", QMessageBox.ButtonRole.AcceptRole)
        no_button = box.addButton("いいえ", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(no_button)
        box.exec()
        return box.clickedButton() == yes_button

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setObjectName("Toolbar")
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(8)

        command_layout = QHBoxLayout()
        command_layout.setSpacing(8)
        command_layout.addWidget(self.open_button)
        command_layout.addWidget(self.save_button)
        command_layout.addWidget(self.undo_button)
        command_layout.addWidget(self.clear_button)
        command_layout.addWidget(self.about_button)
        command_layout.addSpacing(8)
        command_layout.addWidget(QLabel("効果"))
        command_layout.addWidget(self.effect_combo)
        command_layout.addWidget(self.effect_description_label)
        command_layout.addStretch(1)

        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(8)
        slider_layout.addWidget(QLabel("太さ"))
        slider_layout.addWidget(self.brush_slider)
        slider_layout.addWidget(self.brush_value_label)
        slider_layout.addSpacing(12)
        slider_layout.addWidget(QLabel("強さ"))
        slider_layout.addWidget(self.strength_slider)
        slider_layout.addWidget(self.strength_value_label)
        slider_layout.addSpacing(12)
        slider_layout.addWidget(QLabel("ファイル"))
        slider_layout.addWidget(self.file_label)
        slider_layout.addStretch(1)

        toolbar_layout.addLayout(command_layout)
        toolbar_layout.addLayout(slider_layout)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas, 1)
        self.setCentralWidget(root)

    def _setup_shortcuts(self) -> None:
        self._shortcut_open = QShortcut(QKeySequence.StandardKey.Open, self)
        self._shortcut_save = QShortcut(QKeySequence.StandardKey.Save, self)
        self._shortcut_undo = QShortcut(QKeySequence.StandardKey.Undo, self)
        self._shortcut_escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)

        self._shortcut_open.activated.connect(self.open_image_dialog)
        self._shortcut_save.activated.connect(self.save_image)
        self._shortcut_undo.activated.connect(self.undo)
        self._shortcut_escape.activated.connect(self._cancel_active_stroke)

    def _cancel_active_stroke(self) -> None:
        if self.processor.cancel_stroke():
            self.canvas.cancel_stroke_preview()
            self._refresh_canvas()
            self._update_actions()
            self.statusBar().showMessage("ドラッグ操作をキャンセルしました")

    def _update_actions(self) -> None:
        has_image = self.processor.has_image
        self.save_button.setEnabled(has_image)
        self.clear_button.setEnabled(has_image)
        self.undo_button.setEnabled(bool(self.processor.undo_history))

    def _set_icon(self) -> None:
        icon_path = app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(QIcon(str(icon_path)))

    def _sync_effect_description(self, update_status: bool = True) -> None:
        if not isinstance(update_status, bool):
            update_status = True
        effect_type = self.effect_combo.currentData()
        self.effect_description_label.setText(EFFECT_DESCRIPTIONS.get(effect_type, ""))
        if update_status:
            self._show_current_tool_status()

    def _show_current_tool_status(self, *_args) -> None:
        if self.processor.has_image:
            self.statusBar().showMessage(self._current_tool_status_text())

    def _current_effect_name(self) -> str:
        return EFFECT_NAMES.get(self.effect_combo.currentData(), "効果")

    def _current_tool_status_text(self) -> str:
        return (
            f"編集中: {self._current_effect_name()} / "
            f"太さ {self.brush_slider.value()}px / 強さ {self.strength_slider.value()}"
        )

    def _image_status_text(self, prefix: str) -> str:
        image = self.processor.current_image
        source_path = self.processor.source_path
        image_format = self.processor.source_format
        if image is None or source_path is None or image_format is None:
            return "準備完了"

        width, height = image.size
        return f"{prefix}: {source_path.name} / {width}x{height} / {image_format}"

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                font-family: "Yu Gothic UI", "Meiryo UI", sans-serif;
            }
            QMainWindow {
                background: #f5f7fb;
                color: #1f2430;
            }
            QFrame#Toolbar {
                background: #ffffff;
                border-bottom: 1px solid #d9dfeb;
            }
            QLabel {
                color: #303747;
            }
            QLabel#FileLabel {
                color: #586174;
                padding-left: 2px;
            }
            QLabel#EffectDescription {
                color: #586174;
                padding-left: 2px;
            }
            QComboBox, QToolButton {
                min-height: 30px;
                padding: 4px 10px;
            }
            QToolButton {
                border: 1px solid #c8d0de;
                border-radius: 6px;
                background: #ffffff;
            }
            QToolButton:hover {
                background: #eef4ff;
                border-color: #8fb2f5;
            }
            QToolButton:pressed {
                background: #ddeaff;
            }
            QToolButton:disabled {
                color: #9aa3b3;
                background: #f1f3f7;
            }
            QComboBox {
                border: 1px solid #c8d0de;
                border-radius: 6px;
                background: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 5px;
                border-radius: 2px;
                background: #d9dfeb;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                background: #5477d7;
            }
            """
        )

    def _make_tool_button(self, text: str, icon: QIcon, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setIcon(icon)
        button.setToolTip(tooltip)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        return button

    @staticmethod
    def _make_slider(minimum: int, maximum: int, value: int, suffix: str) -> tuple[QSlider, QLabel]:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.setFixedWidth(180)

        label = QLabel()
        label.setFixedWidth(46)

        def update_label(next_value: int) -> None:
            label.setText(f"{next_value}{suffix}")

        slider.valueChanged.connect(update_label)
        update_label(value)
        return slider, label


def pil_to_qimage(image: Image.Image) -> QImage:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    data = rgba.tobytes("raw", "RGBA")
    return QImage(data, width, height, width * 4, QImage.Format.Format_RGBA8888).copy()
