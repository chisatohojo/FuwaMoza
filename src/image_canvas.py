from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class ImageCanvas(QWidget):
    file_dropped = Signal(str)
    stroke_started = Signal(object)
    stroke_moved = Signal(object)
    stroke_finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setMinimumSize(560, 360)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self._image = None
        self._pixmap: QPixmap | None = None
        self._display_rect = QRectF()
        self._is_drawing = False
        self._hover_pos: QPointF | None = None
        self._hover_image_point: tuple[int, int] | None = None
        self._stroke_points: list[tuple[int, int]] = []
        self._brush_diameter = 40

    def set_image(self, image) -> None:
        self._image = image
        self._pixmap = QPixmap.fromImage(image) if image is not None else None
        if not self._is_drawing:
            self._hover_image_point = None
            self._stroke_points.clear()
        self.update()

    def set_brush_diameter(self, diameter: int) -> None:
        self._brush_diameter = max(1, int(diameter))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#f5f7fb"))

        if self._pixmap is None or self._image is None:
            self._paint_empty_state(painter)
            return

        self._display_rect = self._calculate_display_rect()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(self._display_rect, self._pixmap, QRectF(self._pixmap.rect()))

        self._paint_stroke_preview(painter)

        if self._hover_image_point is not None:
            self._paint_brush_preview(painter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._first_local_file(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        path = self._first_local_file(event)
        if path:
            self.file_dropped.emit(str(path))
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._image is None:
            return

        self._hover_pos = event.position()
        point = self.image_point_from_view(event.position())
        if point is None:
            self._hover_image_point = None
            return

        self._is_drawing = True
        self._hover_image_point = point
        self._stroke_points = [point]
        self.stroke_started.emit(point)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._hover_pos = event.position()
        self._hover_image_point = self.image_point_from_view(event.position())
        if self._is_drawing and self._image is not None:
            point = self._hover_image_point
            if point is not None:
                if not self._stroke_points or self._stroke_points[-1] != point:
                    self._stroke_points.append(point)
                self.stroke_moved.emit(point)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._is_drawing:
            self._is_drawing = False
            self.stroke_finished.emit()
            self._stroke_points.clear()
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        if not self._is_drawing:
            self._hover_pos = None
            self._hover_image_point = None
            self.update()

    def cancel_stroke_preview(self) -> None:
        self._is_drawing = False
        self._stroke_points.clear()
        self.update()

    def _calculate_display_rect(self) -> QRectF:
        if self._image is None or self._image.width() <= 0 or self._image.height() <= 0:
            return QRectF()

        area = QRectF(self.rect()).adjusted(24, 24, -24, -24)
        if area.width() <= 0 or area.height() <= 0:
            return QRectF()

        scale = min(area.width() / self._image.width(), area.height() / self._image.height())
        display_width = self._image.width() * scale
        display_height = self._image.height() * scale
        left = area.left() + (area.width() - display_width) / 2
        top = area.top() + (area.height() - display_height) / 2
        return QRectF(left, top, display_width, display_height)

    def image_point_from_view(self, point: QPointF) -> tuple[int, int] | None:
        if self._image is None:
            return None

        self._display_rect = self._calculate_display_rect()

        if self._display_rect.isNull() or not self._display_rect.contains(point):
            return None

        x_ratio = (point.x() - self._display_rect.left()) / self._display_rect.width()
        y_ratio = (point.y() - self._display_rect.top()) / self._display_rect.height()
        x = min(max(int(x_ratio * self._image.width()), 0), self._image.width() - 1)
        y = min(max(int(y_ratio * self._image.height()), 0), self._image.height() - 1)
        return x, y

    def view_point_from_image(self, point: tuple[int, int]) -> QPointF:
        if self._image is None or self._display_rect.isNull():
            return QPointF()

        x_scale = self._display_rect.width() / self._image.width()
        y_scale = self._display_rect.height() / self._image.height()
        return QPointF(
            self._display_rect.left() + point[0] * x_scale,
            self._display_rect.top() + point[1] * y_scale,
        )

    def _paint_empty_state(self, painter: QPainter) -> None:
        rect = QRectF(self.rect()).adjusted(40, 40, -40, -40)
        painter.setPen(QPen(QColor("#a8b2c3"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(rect, 8, 8)

        painter.setPen(QColor("#586174"))
        font = painter.font()
        font.setPointSize(15)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "画像をここにドラッグ＆ドロップ")

    def _paint_brush_preview(self, painter: QPainter) -> None:
        if self._image is None or self._display_rect.width() <= 0 or self._hover_image_point is None:
            return

        scale = self._display_rect.width() / self._image.width()
        diameter = max(2.0, self._brush_diameter * scale)
        center = self.view_point_from_image(self._hover_image_point)
        rect = QRectF(
            center.x() - diameter / 2,
            center.y() - diameter / 2,
            diameter,
            diameter,
        )

        painter.save()
        painter.setClipRect(self._display_rect)
        painter.setPen(QPen(QColor(255, 255, 255, 210), 3))
        painter.setBrush(QColor(84, 119, 215, 32))
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor(44, 47, 58, 170), 1.5))
        painter.drawEllipse(rect)
        painter.restore()

    def _paint_stroke_preview(self, painter: QPainter) -> None:
        if self._image is None or not self._is_drawing or not self._stroke_points:
            return

        scale = self._display_rect.width() / self._image.width()
        diameter = max(2.0, self._brush_diameter * scale)

        painter.save()
        painter.setClipRect(self._display_rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(
            QPen(
                QColor(84, 119, 215, 72),
                diameter,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )

        points = [self.view_point_from_image(point) for point in self._stroke_points]
        if len(points) == 1:
            radius = diameter / 2
            painter.setBrush(QColor(84, 119, 215, 48))
            painter.drawEllipse(QRectF(points[0].x() - radius, points[0].y() - radius, diameter, diameter))
        else:
            for start, end in zip(points, points[1:]):
                painter.drawLine(start, end)
        painter.restore()

    @staticmethod
    def _first_local_file(event) -> Path | None:
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return None

        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file():
                return path
        return None
